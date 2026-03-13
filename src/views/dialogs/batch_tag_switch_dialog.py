from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QMessageBox,
    QWidget,
    QApplication,
    QScrollArea,
    QFrame,
    QSizePolicy,
)
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from src.widgets.loading_widget import LoadingWidget
from src.widgets.custom_dropdown import CustomDropdown
from src.styles import Colors, Styles, GlassmorphismStyle
from src.components.modern_dialog import ModernDialog
from src.components.bottom_sheet_dialog import BottomSheetDialog
import subprocess
import os
import re


class TagSwitchWorker(QThread):
    """异步切换Tag的工作线程"""

    finished = pyqtSignal(dict)

    def __init__(self, pods_info, tag_selections, podfile_path, podfile_lines):
        super().__init__()
        self.pods_info = pods_info
        self.tag_selections = tag_selections
        self.podfile_path = podfile_path
        self.podfile_lines = podfile_lines

    def _parse_tag_reference(self, pod_line):
        """解析pod行中的tag引用，返回(tag_type, tag_value)"""
        tag_match = re.search(r":tag\s*=>\s*([^,\s\n]+)", pod_line)
        if not tag_match:
            return None, None

        tag_value = tag_match.group(1).strip()

        if (tag_value.startswith("'") and tag_value.endswith("'")) or (
            tag_value.startswith('"') and tag_value.endswith('"')
        ):
            return "literal", tag_value[1:-1]
        else:
            return "variable", tag_value

    def _parse_branch_reference(self, pod_line):
        """解析pod行中的branch引用"""
        branch_pattern = r":branch\s*=>\s*([^,\s\n]+)"
        matches = re.finditer(branch_pattern, pod_line)

        references = []
        for match in matches:
            branch_value = match.group(1).strip()
            match_text = match.group(0)

            if (branch_value.startswith("'") and branch_value.endswith("'")) or (
                branch_value.startswith('"') and branch_value.endswith('"')
            ):
                branch_type = "literal"
                actual_value = branch_value[1:-1]
            else:
                branch_type = "variable"
                actual_value = branch_value

            references.append(
                {"type": branch_type, "value": actual_value, "match_text": match_text}
            )

        if references:
            return references[0]["type"], references[0]["value"], references
        return None, None, []

    def _convert_branch_to_tag(self, pod_declaration):
        """将Pod声明中的:branch =>转换为:tag =>"""
        new_declaration = re.sub(r":branch\s*=>", ":tag =>", pod_declaration)
        return new_declaration

    def _find_variable_definition(self, var_name):
        """查找变量定义，返回(行号, 当前值)"""
        for i, line in enumerate(self.podfile_lines):
            match = re.match(
                rf'^\s*{re.escape(var_name)}\s*=\s*[\'"]([^\'"]*)[\'"]', line
            )
            if match:
                return i, match.group(1)
        return None, None

    def _get_full_pod_declaration(self, start_idx, pod_name):
        """获取完整的pod声明（可能跨越多行）"""
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

                        if ":branch =>" in full_declaration:
                            branch_type, branch_value, branch_refs = (
                                self._parse_branch_reference(full_declaration)
                            )
                            if branch_refs:
                                new_declaration = self._convert_branch_to_tag(
                                    full_declaration
                                )

                                for ref in branch_refs:
                                    if ref["type"] == "variable":
                                        var_line_idx, current_value = (
                                            self._find_variable_definition(ref["value"])
                                        )
                                        if var_line_idx is not None:
                                            escaped_var = re.escape(ref["value"])
                                            new_lines[var_line_idx] = re.sub(
                                                rf"({escaped_var}\s*=\s*['\"])[^'\"]*(['\"])",
                                                rf"\1{selected_tag}\2",
                                                new_lines[var_line_idx],
                                            )
                                            modified = True
                                    elif ref["type"] == "literal":
                                        new_declaration = re.sub(
                                            r":tag\s*=>\s*['\"][^'\"]*['\"]",
                                            f":tag => '{selected_tag}'",
                                            new_declaration,
                                        )
                                        modified = True

                                if start_idx == end_idx:
                                    if new_lines[start_idx].endswith("\n"):
                                        new_lines[start_idx] = new_declaration + "\n"
                                    else:
                                        new_lines[start_idx] = new_declaration
                                else:
                                    new_lines[start_idx:end_idx] = [
                                        new_declaration + "\n"
                                    ] + [""] * (end_idx - start_idx - 1)
                                modified = True
                            else:
                                error_messages.append(
                                    f"{pod_name}: 未找到 :branch => 引用"
                                )
                        elif ":tag =>" in full_declaration:
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
                                    if new_lines[start_idx].endswith("\n"):
                                        new_lines[start_idx] = new_declaration + "\n"
                                    else:
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
                    error_messages.append(
                        f"{pod_name}: 未找到Pod引用或未检测到Tag/Branch引用"
                    )

            except Exception as e:
                error_messages.append(f"{pod_name}: {str(e)}")
                fail_count += 1

        try:
            with open(self.podfile_path, "w") as f:
                f.writelines(new_lines)
        except Exception as e:
            error_messages.append(f"写入Podfile失败: {str(e)}")
            fail_count += success_count
            success_count = 0

        self.finished.emit(
            {
                "success_count": success_count,
                "fail_count": fail_count,
                "error_messages": error_messages,
            }
        )


class BatchTagSwitchDialog(BottomSheetDialog):
    """批量切换Tag对话框 - Bottom Sheet 风格（卡片式布局）"""

    def __init__(self, pods_info, podfile_path=None, podfile_lines=None, parent=None):
        self.pods_info = pods_info
        self.podfile_path = podfile_path
        self.podfile_lines = podfile_lines
        self.tag_selections = {}
        self.worker = None
        self.loading_widget = None
        self.pod_cards = []

        super().__init__(parent, title="批量切换Tag", max_height_ratio=0.85)

        self._build_content()
        self._apply_content_styles()
        self.load_pods_info()
        self.setup_sheet_ui()

    def _build_content(self):
        """构建内容区域"""
        desc_label = QLabel("为每个 Pod 选择要切换的远程 Tag")
        desc_label.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 12px; background: transparent; border: none;"
        )
        self.content_layout.addWidget(desc_label)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.2);
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 0.3);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

        # 卡片容器
        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent; border: none;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 12, 0)
        self.cards_layout.setSpacing(12)

        self.scroll_area.setWidget(self.cards_container)
        self.content_layout.addWidget(self.scroll_area, 1)

        # 修改按钮文本和连接
        self.confirm_btn.setText("切换")
        self.confirm_btn.clicked.disconnect()
        self.confirm_btn.clicked.connect(self.switch_all_tags)

    def _apply_content_styles(self):
        """应用样式"""
        self.setStyleSheet(f"""
            QComboBox QAbstractItemView {{
                background-color: #1a1a2e;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 10px;
                min-height: 24px;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: rgba(102, 126, 234, 0.4);
                color: {Colors.TEXT_PRIMARY};
            }}
        """)

    def _create_pod_card(self, row, pod_info):
        """创建单个 Pod 卡片"""
        card = QFrame()
        card.setObjectName("podCard")
        card.setStyleSheet(f"""
            QFrame#podCard {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(10)

        # Header: Pod名称 + 当前模式标签
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        name_label = QLabel(pod_info["name"])
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        header_layout.addWidget(name_label)

        # 检测当前模式
        mode = self._detect_pod_mode(pod_info["name"])
        if mode == "branch":
            mode_badge = QLabel("Branch")
            mode_badge.setStyleSheet(f"""
                QLabel {{
                    color: #fbbf24;
                    font-size: 11px;
                    background-color: rgba(251, 191, 36, 0.15);
                    border: 1px solid rgba(251, 191, 36, 0.25);
                    border-radius: 4px;
                    padding: 2px 8px;
                }}
            """)
            header_layout.addWidget(mode_badge)
        elif mode == "tag":
            mode_badge = QLabel("Tag")
            mode_badge.setStyleSheet(f"""
                QLabel {{
                    color: #60a5fa;
                    font-size: 11px;
                    background-color: rgba(96, 165, 250, 0.15);
                    border: 1px solid rgba(96, 165, 250, 0.25);
                    border-radius: 4px;
                    padding: 2px 8px;
                }}
            """)
            header_layout.addWidget(mode_badge)

        header_layout.addStretch()
        card_layout.addLayout(header_layout)

        # 本地路径
        path_label = QLabel(pod_info.get("path", ""))
        path_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_MUTED};
                font-size: 11px;
                background: transparent;
                border: none;
            }}
        """)
        card_layout.addWidget(path_label)

        # Tag选择行
        tag_row = QHBoxLayout()
        tag_row.setSpacing(12)

        tag_label = QLabel("选择Tag:")
        tag_label.setFixedWidth(65)
        tag_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        tag_row.addWidget(tag_label)

        # 使用CustomDropdown组件
        remote_tags = pod_info.get("remote_tags", [])
        tag_combo = CustomDropdown()
        tag_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if remote_tags:
            tag_combo.addItems(remote_tags)
            # 默认选择第一个tag
            if len(remote_tags) > 0:
                tag_combo.setCurrentText(remote_tags[0])
                self.tag_selections[row] = remote_tags[0]
            tag_combo.currentTextChanged.connect(
                lambda text, r=row: self.on_tag_selected(r, text)
            )
        else:
            tag_combo.addItem("无远程Tag")
            tag_combo.setEnabled(False)

        tag_row.addWidget(tag_combo)
        card_layout.addLayout(tag_row)

        # 远程Tag提示（显示前3个）
        if remote_tags and len(remote_tags) > 1:
            tags_hint = ", ".join(remote_tags[:3])
            if len(remote_tags) > 3:
                tags_hint += f" ... (共{len(remote_tags)}个)"
            hint_label = QLabel(f"可用: {tags_hint}")
            hint_label.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_MUTED};
                    font-size: 10px;
                    background: transparent;
                    border: none;
                    margin-left: 77px;
                }}
            """)
            card_layout.addWidget(hint_label)

        # 保存卡片组件引用
        self.pod_cards.append(
            {
                "card": card,
                "tag_combo": tag_combo,
            }
        )

        return card

    def _detect_pod_mode(self, pod_name):
        """检测Pod的模式：返回 'branch', 'tag', 或 'unknown'"""
        if not self.podfile_lines:
            return "unknown"
        for i, line in enumerate(self.podfile_lines):
            if f"pod '{pod_name}'" in line or f'pod "{pod_name}"' in line:
                full_line = line
                j = i
                while full_line.rstrip().endswith("\\") and j + 1 < len(
                    self.podfile_lines
                ):
                    j += 1
                    full_line += self.podfile_lines[j]
                if ":branch =>" in full_line:
                    return "branch"
                elif ":tag =>" in full_line:
                    return "tag"
        return "unknown"

    def load_pods_info(self):
        """加载Pod信息，创建卡片"""
        for row, pod_info in enumerate(self.pods_info):
            card = self._create_pod_card(row, pod_info)
            self.cards_layout.addWidget(card)

        # 添加弹性空间
        self.cards_layout.addStretch()

    def on_tag_selected(self, row, tag_name):
        """当用户选择Tag时"""
        if tag_name and tag_name != "无远程Tag":
            self.tag_selections[row] = tag_name
        else:
            self.tag_selections.pop(row, None)

    def switch_all_tags(self):
        """批量切换所有Tag"""
        # 检查是否所有Pod都选择了Tag
        unselected_pods = []
        for row in range(len(self.pods_info)):
            if row not in self.tag_selections:
                pod_name = self.pods_info[row]["name"]
                unselected_pods.append(pod_name)

        if unselected_pods:
            ModernDialog.warning(
                self,
                "警告",
                f"以下Pod未选择Tag:\n{', '.join(unselected_pods)}\n\n请为所有Pod选择Tag后再切换。",
            )
            return

        # 确认对话框
        reply = ModernDialog.question(
            self,
            "确认",
            f"确定要为 {len(self.pods_info)} 个Pod切换Tag吗？\n\n这将修改Podfile中的Pod引用。",
            ModernDialog.Yes | ModernDialog.No,
        )

        if reply != ModernDialog.Yes:
            return

        # 显示加载对话框
        loading_dialog = QWidget(self)
        loading_dialog.setFixedSize(200, 100)
        loading_dialog.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.BG_GRADIENT_START},
                    stop:0.5 {Colors.BG_GRADIENT_MID},
                    stop:1 {Colors.BG_GRADIENT_END}
                );
                border-radius: 12px;
            }}
        """)

        loading_layout = QVBoxLayout()
        loading_layout.setContentsMargins(20, 20, 20, 20)

        self.loading_widget = LoadingWidget("切换中...")
        loading_layout.addWidget(self.loading_widget)

        loading_dialog.setLayout(loading_layout)
        loading_dialog.show()

        self.loading_widget.start_animation()
        QApplication.processEvents()

        # 启动工作线程
        self.worker = TagSwitchWorker(
            self.pods_info, self.tag_selections, self.podfile_path, self.podfile_lines
        )
        self.worker.finished.connect(
            lambda result: self._on_tag_switch_finished(result, loading_dialog)
        )

        self.worker.start()

    def _on_tag_switch_finished(self, result, loading_dialog):
        """处理Tag切换完成"""
        # 清理线程引用
        if hasattr(self, "worker") and self.worker:
            try:
                self.worker.wait()
            except RuntimeError:
                pass
            finally:
                self.worker = None

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
            ModernDialog.information(self, "成功", result_msg)
            self.accept()
        else:
            ModernDialog.warning(self, "警告", result_msg)

    def closeEvent(self, event):
        """当对话框关闭时清理线程"""
        if hasattr(self, "worker") and self.worker:
            try:
                if self.worker.isRunning():
                    self.worker.quit()
                    self.worker.wait(2000)
            except RuntimeError:
                pass
        super().closeEvent(event)
