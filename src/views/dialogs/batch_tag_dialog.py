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
    QStyle,
    QApplication,
)
from PyQt5.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal
from src.widgets.loading_widget import LoadingWidget
import subprocess
import os
import re


class TagCreationWorker(QThread):
    """异步创建Tag的工作线程"""

    finished = pyqtSignal(
        dict
    )  # 发送结果：{'success_count': int, 'fail_count': int, 'error_messages': list}

    def __init__(self, pods_info, pod_configs, branch_selections):
        super().__init__()
        self.pods_info = pods_info
        self.pod_configs = pod_configs
        self.branch_selections = branch_selections  # {row: selected_branch}

    def _clean_tag_name(self, tag_name):
        """清理Tag名称，移除(推荐)后缀"""
        if not tag_name:
            return tag_name
        return tag_name.replace(" (推荐)", "").strip()

    def run(self):
        success_count = 0
        fail_count = 0
        error_messages = []

        for row in range(len(self.pods_info)):
            pod_info = self.pods_info[row]
            pod_name = pod_info["name"]
            local_path = pod_info["path"]

            # 获取Tag名称
            tag_name = self._clean_tag_name(
                self.pod_configs.get(row, {}).get("tag_name", "").strip()
            )
            if not tag_name:
                continue

            # 获取Tag消息
            tag_message = self.pod_configs.get(row, {}).get("tag_message", "").strip()
            if not tag_message:
                tag_message = f"Release {tag_name}"

            # 获取选中的分支
            selected_branch = self.branch_selections.get(row, "")

            try:
                if selected_branch and selected_branch != "无分支":
                    # 先fetch远程仓库，确保远程分支信息最新
                    subprocess.run(
                        ["git", "fetch", "origin"],
                        capture_output=True,
                        cwd=local_path,
                        check=True,
                    )

                    # 直接基于远程分支创建tag
                    remote_branch = (
                        f"origin/{selected_branch}"
                        if not selected_branch.startswith("origin/")
                        else selected_branch
                    )
                    subprocess.run(
                        [
                            "git",
                            "tag",
                            "-a",
                            tag_name,
                            "-m",
                            tag_message,
                            remote_branch,
                        ],
                        cwd=local_path,
                        check=True,
                    )
                else:
                    # 如果没有选择分支，基于当前HEAD创建tag
                    subprocess.run(
                        ["git", "tag", "-a", tag_name, "-m", tag_message],
                        cwd=local_path,
                        check=True,
                    )

                # 推送tag到远程
                subprocess.run(
                    ["git", "push", "origin", tag_name],
                    capture_output=True,
                    cwd=local_path,
                    check=True,
                )

                success_count += 1

            except subprocess.CalledProcessError as e:
                error_messages.append(f"{pod_name}: {str(e)}")
                fail_count += 1

        self.finished.emit(
            {
                "success_count": success_count,
                "fail_count": fail_count,
                "error_messages": error_messages,
            }
        )


class BatchTagDialog(QDialog):
    def __init__(self, pods_info, parent=None):
        """
        pods_info: list of dict, each dict contains:
        {
            'name': pod_name,
            'path': local_path,
            'branches': list of branches,
            'current_branch': current branch name
        }
        """
        super().__init__(parent)
        self.pods_info = pods_info
        self.current_row = 0
        self.initUI()
        self.load_pods_info()

    def initUI(self):
        self.setWindowTitle("批量创建Tag")
        self.setGeometry(200, 200, 1400, 700)
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
            QLineEdit {
                border: 1px solid #d1d1d6;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: white;
                min-height: 32px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #007aff;
            }
            QTextEdit {
                border: 1px solid #d1d1d6;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
                font-size: 13px;
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
        table_group = QGroupBox("Pod列表（点击选择行查看/编辑Tag消息）")
        table_layout = QVBoxLayout()

        self.pod_table = QTableWidget()
        self.pod_table.setColumnCount(5)
        self.pod_table.setHorizontalHeaderLabels(
            ["Pod名称", "当前分支", "选择分支", "已有Tag", "Tag名称"]
        )
        self.pod_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.pod_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.pod_table.horizontalHeader().setStretchLastSection(True)
        self.pod_table.verticalHeader().setVisible(False)
        self.pod_table.setAlternatingRowColors(True)
        self.pod_table.currentCellChanged.connect(self.on_row_changed)

        # 设置列宽
        self.pod_table.setColumnWidth(0, 160)  # Pod名称
        self.pod_table.setColumnWidth(1, 110)  # 当前分支
        self.pod_table.setColumnWidth(2, 140)  # 选择分支
        self.pod_table.setColumnWidth(3, 280)  # 已有Tag
        self.pod_table.setColumnWidth(4, 200)  # Tag名称

        table_layout.addWidget(self.pod_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # Tag消息编辑区域
        self.msg_group = QGroupBox("Tag消息")
        msg_layout = QGridLayout()

        # 当前编辑的Pod
        msg_layout.addWidget(QLabel("当前编辑Pod:"), 0, 0)
        self.current_pod_label = QLabel("")
        self.current_pod_label.setStyleSheet(
            "font-weight: bold; color: #007aff; font-size: 14px;"
        )
        msg_layout.addWidget(self.current_pod_label, 0, 1)

        # Tag消息输入
        msg_layout.addWidget(QLabel("Tag消息:"), 1, 0)
        self.msg_edit = QTextEdit()
        self.msg_edit.setPlaceholderText("输入Tag消息...")
        self.msg_edit.setMinimumHeight(80)
        msg_layout.addWidget(self.msg_edit, 1, 1)

        # 消息模板
        msg_layout.addWidget(QLabel("消息模板:"), 2, 0)
        self.template_combo = QComboBox()
        self.template_combo.addItems(
            [
                "-- 选择模板 --",
                "Release {tag_name}",
                "Hotfix修复",
                "功能更新",
                "版本发布",
            ]
        )
        self.template_combo.currentIndexChanged.connect(self.apply_template)
        msg_layout.addWidget(self.template_combo, 2, 1)

        # 保存配置按钮
        self.save_btn = QPushButton("保存当前Pod配置")
        self.save_btn.setProperty("buttonType", "info")
        self.save_btn.clicked.connect(self.save_current_config)
        msg_layout.addWidget(self.save_btn, 3, 1, Qt.AlignRight)

        self.msg_group.setLayout(msg_layout)
        layout.addWidget(self.msg_group)

        # 按钮区域
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.setProperty("type", "cancel")
        cancel_btn.clicked.connect(self.reject)

        create_all_btn = QPushButton("批量创建所有Tag")
        create_all_btn.setProperty("buttonType", "success")
        create_all_btn.clicked.connect(self.create_all_tags)

        btn_layout.addWidget(create_all_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def load_pods_info(self):
        """加载Pod信息到表格"""
        self.pod_table.setRowCount(len(self.pods_info))
        self.pod_configs = {}  # {row: {'tag_name': '', 'tag_message': ''}}

        for row, pod_info in enumerate(self.pods_info):
            # Pod名称
            name_item = QTableWidgetItem(pod_info["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.pod_table.setItem(row, 0, name_item)

            # 当前分支
            branch_item = QTableWidgetItem(pod_info.get("current_branch", "获取中..."))
            branch_item.setFlags(branch_item.flags() & ~Qt.ItemIsEditable)
            self.pod_table.setItem(row, 1, branch_item)

            # 选择分支（ComboBox）
            branch_combo = QComboBox()
            branch_combo.setFixedHeight(24)
            branches = pod_info.get("branches", [])
            if branches:
                branch_combo.addItems(branches)
                # 默认优先选择包含"master"的分支（如 master, origin/master, feature/master-fix 等）
                master_branches = [b for b in branches if "master" in b.lower()]
                if master_branches:
                    # 优先选择精确匹配 "master" 或 "origin/master"，其次是其他包含master的分支
                    if "master" in master_branches:
                        branch_combo.setCurrentText("master")
                    elif "origin/master" in master_branches:
                        branch_combo.setCurrentText("origin/master")
                    else:
                        branch_combo.setCurrentText(master_branches[0])
                elif len(branches) > 0:
                    branch_combo.setCurrentIndex(0)
            else:
                branch_combo.addItem("无分支")
            self.pod_table.setCellWidget(row, 2, branch_combo)

            # 已有Tag（只读，按时间排序）
            tags = self.get_sorted_tags(pod_info["path"])
            tags_text = ", ".join(tags[:4]) if tags else "无"
            tags_item = QTableWidgetItem(tags_text)
            tags_item.setFlags(tags_item.flags() & ~Qt.ItemIsEditable)
            tags_item.setToolTip("\n".join(tags) if tags else "无Tag")
            self.pod_table.setItem(row, 3, tags_item)

            # 生成推荐Tag名称
            recommended_tag = self.generate_recommended_tag(tags)
            tag_name_item = QTableWidgetItem(f"{recommended_tag} (推荐)")
            tag_name_item.setFlags(tag_name_item.flags() | Qt.ItemIsEditable)
            tag_name_item.setToolTip("建议使用语义化版本号，如 v1.0.0")
            self.pod_table.setItem(row, 4, tag_name_item)

            # 初始化配置
            self.pod_configs[row] = {
                "tag_name": recommended_tag,
                "tag_message": f"Release {recommended_tag}",
            }

        # 设置固定行高
        for i in range(self.pod_table.rowCount()):
            self.pod_table.setRowHeight(i, 48)

        # 默认选中第一行
        if len(self.pods_info) > 0:
            self.pod_table.selectRow(0)
            self.load_pod_config(0)

    def on_row_changed(
        self, current_row, current_column, previous_row, previous_column
    ):
        """当前行改变时保存上一行的配置并加载新行的配置"""
        if previous_row >= 0 and previous_row < len(self.pods_info):
            self.save_current_config()

        if current_row >= 0 and current_row < len(self.pods_info):
            self.load_pod_config(current_row)

    def load_pod_config(self, row):
        """加载指定行的配置到编辑区域"""
        if row >= len(self.pods_info):
            return

        pod_info = self.pods_info[row]
        self.current_row = row

        # 更新Pod名称标签
        self.current_pod_label.setText(pod_info["name"])

        # 加载配置
        config = self.pod_configs.get(row, {"tag_name": "", "tag_message": ""})

        # 表格中Tag名称可能已被用户修改，优先使用表格中的值
        tag_name_item = self.pod_table.item(row, 4)
        if tag_name_item:
            config["tag_name"] = self._clean_tag_name(tag_name_item.text().strip())
            self.pod_configs[row]["tag_name"] = config["tag_name"]

        # 更新Tag消息编辑框
        self.msg_edit.setText(config.get("tag_message", ""))

    def save_current_config(self):
        """保存当前行的配置"""
        if self.current_row < 0 or self.current_row >= len(self.pods_info):
            return

        # 保存Tag名称到表格
        tag_name = self.pod_table.item(self.current_row, 4).text().strip()
        tag_message = self.msg_edit.toPlainText().strip()

        # 保存配置
        self.pod_configs[self.current_row] = {
            "tag_name": tag_name,
            "tag_message": tag_message,
        }

    def apply_template(self, index):
        """应用消息模板"""
        if index == 0:
            return

        template = self.template_combo.currentText()
        tag_name = self.pod_table.item(self.current_row, 4).text().strip()

        message = template.replace("{tag_name}", tag_name)
        self.msg_edit.setText(message)

    def get_sorted_tags(self, local_path):
        """获取按时间排序的Tag列表（最新的在前）"""
        try:
            result = subprocess.run(
                ["git", "tag", "--sort=-creatordate"],
                capture_output=True,
                text=True,
                cwd=local_path,
                check=True,
            )
            output = result.stdout.strip()
            return output.split("\n") if output else []
        except subprocess.CalledProcessError:
            return []

    def generate_recommended_tag(self, existing_tags):
        """生成推荐Tag名称"""
        if not existing_tags:
            return "v1.0.0"

        # 尝试解析最新tag
        latest_tag = existing_tags[0]
        version_match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", latest_tag)

        if version_match:
            major, minor, patch = map(int, version_match.groups())
            # 推荐补丁版本递增
            return f"v{major}.{minor}.{patch + 1}"
        else:
            return "v1.0.0"

    def _clean_tag_name(self, tag_name):
        """清理Tag名称，移除(推荐)后缀"""
        if not tag_name:
            return tag_name
        return tag_name.replace(" (推荐)", "").strip()

    def create_all_tags(self):
        """批量创建所有Tag"""
        # 先保存当前行的配置
        self.save_current_config()

        reply = QMessageBox.question(
            self,
            "确认",
            "确定要为所有Pod创建Tag吗？",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        # 收集分支选择信息
        branch_selections = {}
        for row in range(self.pod_table.rowCount()):
            branch_combo = self.pod_table.cellWidget(row, 2)
            selected_branch = ""
            if branch_combo and branch_combo.currentIndex() >= 0:
                selected_branch = branch_combo.currentText()
            branch_selections[row] = selected_branch

        # 创建loading对话框
        loading_dialog = QDialog(self)
        loading_dialog.setWindowTitle("创建Tag")
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
        self.loading_widget = LoadingWidget("创建中...")
        loading_layout.addWidget(self.loading_widget)

        loading_dialog.setLayout(loading_layout)
        loading_dialog.show()

        # 开始动画
        self.loading_widget.start_animation()
        QApplication.processEvents()

        # 创建工作线程
        self.worker = TagCreationWorker(
            self.pods_info, self.pod_configs, branch_selections
        )
        self.worker.finished.connect(
            lambda result: self._on_tag_creation_finished(result, loading_dialog)
        )
        # 设置父对象为None，避免对话框关闭时线程被强制销毁
        self.worker.setParent(None)
        # 线程完成后自动删除
        self.worker.finished.connect(self.worker.deleteLater)

        # 启动工作线程
        self.worker.start()

    def _on_tag_creation_finished(self, result, loading_dialog):
        """处理Tag创建完成"""
        try:
            # 停止动画
            if hasattr(self, "loading_widget") and self.loading_widget:
                self.loading_widget.stop_animation()

            if loading_dialog:
                loading_dialog.close()

            success_count = result["success_count"]
            fail_count = result["fail_count"]
            error_messages = result["error_messages"]

            # 刷新UI显示（Tag列表和推荐值）
            for row in range(self.pod_table.rowCount()):
                pod_info = self.pods_info[row]
                local_path = pod_info["path"]

                try:
                    # 刷新Tag列表
                    new_tags = self.get_sorted_tags(local_path)
                    tags_text = ", ".join(new_tags[:4]) if new_tags else "无"
                    self.pod_table.item(row, 3).setText(tags_text)

                    # 更新推荐Tag
                    new_recommended = self.generate_recommended_tag(new_tags)
                    self.pod_table.item(row, 4).setText(new_recommended + " (推荐)")

                    # 更新配置
                    self.pod_configs[row] = {
                        "tag_name": new_recommended,
                        "tag_message": f"Release {new_recommended}",
                    }
                except Exception:
                    pass

            # 显示结果
            result_msg = f"✅ 成功: {success_count}\n❌ 失败: {fail_count}"
            if error_messages:
                result_msg += "\n\n错误信息:\n" + "\n".join(error_messages[:5])
                if len(error_messages) > 5:
                    result_msg += f"\n... 还有 {len(error_messages) - 5} 个错误"

            if fail_count == 0:
                QMessageBox.information(self, "成功", result_msg)
                self.accept()
            else:
                QMessageBox.warning(self, "警告", result_msg)
        except Exception as e:
            if loading_dialog:
                loading_dialog.close()
            QMessageBox.critical(self, "错误", f"处理Tag创建结果时出错: {str(e)}")

    def closeEvent(self, event):
        """处理对话框关闭事件，确保线程安全退出"""
        if hasattr(self, "worker") and self.worker:
            try:
                if self.worker.isRunning():
                    self.worker.quit()
                    self.worker.wait(2000)  # 等待最多2秒
            except RuntimeError:
                # 线程对象可能已被删除
                pass
        event.accept()

    def reject(self):
        """处理取消/关闭操作，确保线程安全退出"""
        if hasattr(self, "worker") and self.worker:
            try:
                if self.worker.isRunning():
                    reply = QMessageBox.question(
                        self,
                        "确认",
                        "Tag创建正在进行中，确定要取消吗？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    if reply == QMessageBox.No:
                        return
                    self.worker.quit()
                    self.worker.wait(2000)
            except RuntimeError:
                # 线程对象可能已被删除
                pass
        super().reject()
