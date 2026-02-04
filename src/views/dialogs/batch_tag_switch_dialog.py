from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QGridLayout,
    QDialog,
    QVBoxLayout,
    QGroupBox,
    QTextEdit,
    QMessageBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QWidget,
    QApplication,
)
from PyQt5.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal
from src.widgets.loading_widget import LoadingWidget
import subprocess
import os
import re


class TagSwitchWorker(QThread):
    """异步切换Tag的工作线程"""

    finished = pyqtSignal(
        dict
    )  # 发送结果：{'success_count': int, 'fail_count': int, 'error_messages': list}

    def __init__(self, pods_info, tag_selections, podfile_path, podfile_lines):
        super().__init__()
        self.pods_info = pods_info
        self.tag_selections = tag_selections  # {row: selected_tag}
        self.podfile_path = podfile_path
        self.podfile_lines = podfile_lines

    def _parse_tag_reference(self, pod_line):
        """解析pod行中的tag引用，返回(tag_type, tag_value)
        tag_type: 'literal', 'variable', 或 None
        tag_value: tag的值或变量名
        """
        # 匹配 :tag => 'value' 或 :tag => "value" 或 :tag => VARIABLE
        tag_match = re.search(r":tag\s*=>\s*([^,\s\n]+)", pod_line)
        if not tag_match:
            return None, None

        tag_value = tag_match.group(1).strip()

        # 检查是否是字符串字面量
        if (tag_value.startswith("'") and tag_value.endswith("'")) or (
            tag_value.startswith('"') and tag_value.endswith('"')
        ):
            return "literal", tag_value[1:-1]  # 去掉引号
        else:
            # 可能是变量引用
            return "variable", tag_value

    def _find_variable_definition(self, var_name):
        """查找变量定义，返回(行号, 当前值)"""
        for i, line in enumerate(self.podfile_lines):
            # 匹配 VARIABLE = 'value' 或 VARIABLE = "value"
            match = re.match(
                rf'^\s*{re.escape(var_name)}\s*=\s*[\'"]([^\'"]*)[\'"]', line
            )
            if match:
                return i, match.group(1)
        return None, None

    def _get_full_pod_declaration(self, start_idx, pod_name):
        """获取完整的pod声明（可能跨越多行）
        返回: (start_idx, end_idx, full_declaration)
        """
        if start_idx >= len(self.podfile_lines):
            return None, None, None

        line = self.podfile_lines[start_idx]
        if f"pod '{pod_name}'" not in line and f'pod "{pod_name}"' not in line:
            return None, None, None

        full_lines = [line.rstrip("\n")]
        end_idx = start_idx

        i = start_idx
        while i < len(self.podfile_lines):
            current_line = self.podfile_lines[i]
            stripped = current_line.rstrip()

            if stripped.endswith("\\"):
                full_lines.append(stripped[:-1])
                i += 1
                end_idx = i
            else:
                if i > start_idx:
                    full_lines.append(stripped)
                break

        full_declaration = "\n".join(full_lines)
        return start_idx, end_idx, full_declaration

    def run(self):
        success_count = 0
        fail_count = 0
        error_messages = []

        new_lines = self.podfile_lines.copy()

        for row in range(len(self.pods_info)):
            pod_info = self.pods_info[row]
            pod_name = pod_info["name"]
            selected_tag = self.tag_selections.get(row, "")

            if not selected_tag:
                continue

            try:
                modified = False
                for i, line in enumerate(new_lines):
                    if f"pod '{pod_name}'" in line or f'pod "{pod_name}"' in line:
                        start_idx, end_idx, full_declaration = (
                            self._get_full_pod_declaration(i, pod_name)
                        )
                        if full_declaration is None:
                            continue

                        tag_type, tag_value = self._parse_tag_reference(
                            full_declaration
                        )

                        if tag_type == "variable":
                            if tag_value:
                                var_line_idx, current_value = (
                                    self._find_variable_definition(tag_value)
                                )
                                if var_line_idx is not None:
                                    escaped_var = re.escape(tag_value)
                                    new_lines[var_line_idx] = re.sub(
                                        rf"({escaped_var}\s*=\s*['\"])[^'\"]*(['\"])",
                                        rf"\1{selected_tag}\2",
                                        new_lines[var_line_idx],
                                    )
                                    modified = True
                                else:
                                    error_messages.append(
                                        f"{pod_name}: 找不到变量 {tag_value} 的定义"
                                    )
                        else:
                            if ":tag =>" in full_declaration:
                                new_declaration = re.sub(
                                    r"(:tag\s*=>\s*)['\"][^'\"]*['\"]",
                                    f":tag => '{selected_tag}'",
                                    full_declaration,
                                )
                            else:
                                if full_declaration.strip().endswith(","):
                                    new_declaration = (
                                        full_declaration.rstrip()
                                        + f" :tag => '{selected_tag}'\n"
                                    )
                                else:
                                    if "," in full_declaration:
                                        parts = full_declaration.rsplit(",", 1)
                                        new_declaration = (
                                            parts[0]
                                            + ","
                                            + parts[1].rstrip()
                                            + f", :tag => '{selected_tag}'\n"
                                        )
                                    else:
                                        new_declaration = (
                                            full_declaration.rstrip()
                                            + f", :tag => '{selected_tag}'\n"
                                        )

                            if start_idx == end_idx:
                                new_lines[start_idx] = new_declaration
                            else:
                                new_lines[start_idx:end_idx] = [
                                    new_declaration + "\n"
                                ] + [""] * (end_idx - start_idx - 1)
                            modified = True
                        break

                if modified:
                    success_count += 1
                else:
                    error_messages.append(f"{pod_name}: 未找到Pod引用")

            except Exception as e:
                error_messages.append(f"{pod_name}: {str(e)}")
                fail_count += 1

        # 写回Podfile
        try:
            with open(self.podfile_path, "w") as f:
                f.writelines(new_lines)
        except Exception as e:
            error_messages.append(f"写入Podfile失败: {str(e)}")
            fail_count += success_count  # 所有修改都失败了
            success_count = 0

        self.finished.emit(
            {
                "success_count": success_count,
                "fail_count": fail_count,
                "error_messages": error_messages,
            }
        )


class BatchTagSwitchDialog(QDialog):
    def __init__(self, pods_info, podfile_path=None, podfile_lines=None, parent=None):
        """
        pods_info: list of dict, each dict contains:
        {
            'name': pod_name,
            'path': local_path,
            'remote_tags': list of remote tags
        }
        """
        super().__init__(parent)
        self.pods_info = pods_info
        self.podfile_path = podfile_path
        self.podfile_lines = podfile_lines
        self.current_row = 0
        self.initUI()
        self.load_pods_info()

    def initUI(self):
        self.setWindowTitle("批量切换Tag")
        self.setGeometry(200, 200, 1200, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f7;
            }
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #0051d5;
            }
            QPushButton[type="cancel"] {
                background-color: #e8e8ed;
                color: #1d1d1f;
            }
            QPushButton[type="cancel"]:hover {
                background-color: #d1d1d6;
            }
            QLabel {
                color: #86868b;
                font-size: 12px;
                font-weight: 600;
            }
            QComboBox {
                border: 1px solid #d1d1d6;
                border-radius: 6px;
                padding: 2px 10px;
                background-color: white;
                min-height: 20px;
                font-size: 12px;
                color: #1d1d1f;
            }
            QComboBox:hover {
                border-color: #007aff;
            }
            QComboBox:focus {
                border-color: #007aff;
                border-width: 2px;
                padding: 1px 9px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4IiBoZWlnaHQ9IjgiPjxwYXRoIGZpbGw9IiM4Njg2OGIiIGQ9Ik0yIDJsMyAzaDNsLTItMi0yIDItMyAzeiIgLz48L3N2Zz4=);
                width: 10px;
                height: 10px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #d1d1d6;
                border-radius: 6px;
                background-color: white;
                selection-background-color: #007aff;
                selection-color: white;
                font-size: 12px;
                padding: 4px;
            }
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                font-weight: 600;
            }
            QTableWidget {
                border: 1px solid #d1d1d6;
                border-radius: 8px;
                background-color: white;
                gridline-color: #e0e0e0;
                alternate-background-color: #fafafa;
            }
            QTableWidget::item {
                padding: 4px 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f7;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout()

        # 表格区域
        table_group = QGroupBox("Pod Tag切换列表")
        table_layout = QVBoxLayout()

        self.pod_table = QTableWidget()
        self.pod_table.setColumnCount(4)
        self.pod_table.setHorizontalHeaderLabels(
            ["Pod名称", "当前状态", "远程Tag", "选择Tag"]
        )
        self.pod_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.pod_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.pod_table.horizontalHeader().setStretchLastSection(True)
        self.pod_table.verticalHeader().setVisible(False)
        self.pod_table.setAlternatingRowColors(True)

        # 设置列宽
        self.pod_table.setColumnWidth(0, 200)  # Pod名称
        self.pod_table.setColumnWidth(1, 150)  # 当前状态
        self.pod_table.setColumnWidth(2, 300)  # 远程Tag
        self.pod_table.setColumnWidth(3, 200)  # 选择Tag

        table_layout.addWidget(self.pod_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # 按钮区域
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.setProperty("type", "cancel")
        cancel_btn.clicked.connect(self.reject)

        switch_all_btn = QPushButton("批量切换所有Tag")
        switch_all_btn.setProperty("buttonType", "success")
        switch_all_btn.clicked.connect(self.switch_all_tags)

        btn_layout.addWidget(switch_all_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def load_pods_info(self):
        """加载Pod信息到表格"""
        self.pod_table.setRowCount(len(self.pods_info))
        self.tag_selections = {}  # {row: selected_tag}

        for row, pod_info in enumerate(self.pods_info):
            print(
                f"BatchTagSwitchDialog: 加载Pod {pod_info['name']}, remote_tags: {len(pod_info.get('remote_tags', []))}"
            )
            # Pod名称
            name_item = QTableWidgetItem(pod_info["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.pod_table.setItem(row, 0, name_item)

            # 当前状态（暂时显示为"准备切换"）
            status_item = QTableWidgetItem("准备切换")
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            self.pod_table.setItem(row, 1, status_item)

            # 远程Tag列表
            remote_tags = pod_info.get("remote_tags", [])
            tags_text = ", ".join(remote_tags[:3]) if remote_tags else "无远程Tag"
            if len(remote_tags) > 3:
                tags_text += "..."
            tags_item = QTableWidgetItem(tags_text)
            tags_item.setFlags(tags_item.flags() & ~Qt.ItemIsEditable)
            tags_item.setToolTip("\n".join(remote_tags) if remote_tags else "无远程Tag")
            self.pod_table.setItem(row, 2, tags_item)

            # 选择Tag（ComboBox）
            tag_combo = QComboBox()
            tag_combo.setFixedHeight(24)
            if remote_tags:
                tag_combo.addItem("-- 选择Tag --")
                tag_combo.addItems(remote_tags)
                # 默认选择最新版本
                if len(remote_tags) > 0:
                    tag_combo.setCurrentIndex(1)  # 选择第一个远程Tag
                    self.tag_selections[row] = remote_tags[0]
                tag_combo.currentTextChanged.connect(
                    lambda text, r=row: self.on_tag_selected(r, text)
                )
            else:
                tag_combo.addItem("无远程Tag")
            self.pod_table.setCellWidget(row, 3, tag_combo)

        # 设置行高
        for i in range(self.pod_table.rowCount()):
            self.pod_table.setRowHeight(i, 40)

    def on_tag_selected(self, row, tag_name):
        """当用户选择Tag时"""
        if tag_name and tag_name != "-- 选择Tag --":
            self.tag_selections[row] = tag_name
        else:
            self.tag_selections.pop(row, None)

    def switch_all_tags(self):
        """批量切换所有Tag"""
        # 检查是否有未选择的Tag
        unselected_pods = []
        for row in range(self.pod_table.rowCount()):
            if row not in self.tag_selections:
                pod_name = self.pods_info[row]["name"]
                unselected_pods.append(pod_name)

        if unselected_pods:
            QMessageBox.warning(
                self,
                "警告",
                f"以下Pod未选择Tag:\n{', '.join(unselected_pods)}\n\n请为所有Pod选择Tag后再切换。",
            )
            return

        reply = QMessageBox.question(
            self,
            "确认",
            f"确定要为 {len(self.pods_info)} 个Pod切换Tag吗？\n\n这将修改Podfile中的Pod引用。",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        # 创建loading对话框
        loading_dialog = QDialog(self)
        loading_dialog.setWindowTitle("切换Tag")
        loading_dialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint)
        loading_dialog.setFixedSize(200, 100)
        loading_dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f5f7;
                border-radius: 12px;
            }
        """)

        loading_layout = QVBoxLayout()
        loading_layout.setContentsMargins(20, 20, 20, 20)

        # 使用LoadingWidget
        self.loading_widget = LoadingWidget("切换中...")
        loading_layout.addWidget(self.loading_widget)

        loading_dialog.setLayout(loading_layout)
        loading_dialog.show()

        # 开始动画
        self.loading_widget.start_animation()
        QApplication.processEvents()

        # 创建工作线程执行切换
        self.worker = TagSwitchWorker(
            self.pods_info, self.tag_selections, self.podfile_path, self.podfile_lines
        )
        self.worker.finished.connect(
            lambda result: self._on_tag_switch_finished(result, loading_dialog)
        )

        # 启动工作线程
        self.worker.start()

    def _on_tag_switch_finished(self, result, loading_dialog):
        """处理Tag切换完成"""
        # 停止动画
        if hasattr(self, "loading_widget"):
            self.loading_widget.stop_animation()

        loading_dialog.close()

        success_count = result["success_count"]
        fail_count = result["fail_count"]
        error_messages = result["error_messages"]

        result_msg = f"切换完成：成功 {success_count} 个，失败 {fail_count} 个"
        if fail_count > 0:
            result_msg += "\n\n失败详情:\n" + "\n".join(error_messages[:10])

        if fail_count == 0:
            QMessageBox.information(self, "成功", result_msg)
            self.accept()
        else:
            QMessageBox.warning(self, "警告", result_msg)
