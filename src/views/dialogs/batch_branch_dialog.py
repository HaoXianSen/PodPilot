from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QFrame,
    QMessageBox,
    QComboBox,
    QCheckBox,
    QWidget,
    QScrollArea,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QPalette
import os

from src.services.git_service import GitService
from src.widgets.loading_widget import LoadingWidget
from src.widgets.custom_dropdown import CustomDropdown
from src.styles import Colors, Styles, GlassmorphismStyle
from src.components.modern_dialog import ModernDialog
from src.components.bottom_sheet_dialog import BottomSheetDialog


class BranchSwitchWorker(QThread):
    """异步切换到Branch模式的工作线程"""

    finished = pyqtSignal(dict)

    def __init__(
        self,
        pods_info,
        branch_configs,
        git_urls,
        podfile_path,
        podfile_lines,
    ):
        super().__init__()
        self.pods_info = pods_info
        self.branch_configs = branch_configs
        self.git_urls = git_urls
        self.podfile_path = podfile_path
        self.podfile_lines = podfile_lines

    def run(self):
        success_count = 0
        fail_count = 0
        error_messages = []

        new_lines = self.podfile_lines.copy()

        for row, pod_info in enumerate(self.pods_info):
            pod_name = pod_info["name"]
            local_path = pod_info["path"]
            git_url = self.git_urls.get(pod_name, "")

            if not git_url or git_url == "获取失败":
                error_messages.append(f"{pod_name}: 无法获取Git URL")
                fail_count += 1
                continue

            config = self.branch_configs.get(row, {})
            selected_branch = config.get("branch", "")
            is_new_branch = config.get("is_new", False)
            base_branch = config.get("base_branch", "origin/master")

            if not selected_branch:
                error_messages.append(f"{pod_name}: 未选择分支")
                fail_count += 1
                continue

            try:
                if is_new_branch:
                    if not GitService.create_branch(
                        local_path, selected_branch, base_branch
                    ):
                        raise Exception("创建分支失败")
                    if not GitService.push_branch(local_path, selected_branch):
                        raise Exception("推送分支失败")

                branch_for_podfile = selected_branch
                if branch_for_podfile.startswith("origin/"):
                    branch_for_podfile = branch_for_podfile[7:]

                modified = self._update_podfile_for_branch(
                    new_lines, pod_name, git_url, branch_for_podfile
                )

                if not modified:
                    error_messages.append(f"{pod_name}: 未找到Pod引用")
                    fail_count += 1
                else:
                    success_count += 1

            except Exception as e:
                error_messages.append(f"{pod_name}: {str(e)}")
                fail_count += 1

        try:
            with open(self.podfile_path, "w", encoding="utf-8") as f:
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

    def _get_full_pod_declaration(self, lines, start_idx, pod_name):
        if start_idx >= len(lines):
            return None, None, None

        line = lines[start_idx]
        pod_pattern = f"pod '{pod_name}'"
        pod_with_subspec_pattern = f"pod '{pod_name}/"
        if (
            pod_pattern not in line
            and pod_with_subspec_pattern not in line
            and f'pod "{pod_name}"' not in line
            and f'pod "{pod_name}/' not in line
        ):
            return None, None, None

        full_lines = [line.rstrip("\n")]
        end_idx = start_idx

        i = start_idx
        while i < len(lines):
            current_line = lines[i]
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

    def _extract_version_constant(self, declaration):
        import re

        patterns = [
            r":tag\s*=>\s*([A-Z]\w*)",
            r":branch\s*=>\s*([A-Z]\w*)",
        ]

        for pattern in patterns:
            match = re.search(pattern, declaration)
            if match:
                return match.group(1)

        return None

    def _update_constant_value(self, lines, constant_name, new_value):
        import re

        pattern = rf"^({re.escape(constant_name)}\s*=\s*['\"])[^'\"]*(['\"])"

        for i, line in enumerate(lines):
            if re.match(pattern, line.strip()):
                lines[i] = re.sub(pattern, rf"\g<1>{new_value}\g<2>", line)
                return True

        return False

    def _update_podfile_for_branch(self, lines, pod_name, git_url, branch_name):
        for i, line in enumerate(lines):
            pod_pattern = f"pod '{pod_name}'"
            pod_with_subspec_pattern = f"pod '{pod_name}/"

            matches = (
                pod_pattern in line
                or pod_with_subspec_pattern in line
                or f'pod "{pod_name}"' in line
                or f'pod "{pod_name}/' in line
            )

            if not matches:
                continue

            start_idx, end_idx, full_declaration = self._get_full_pod_declaration(
                lines, i, pod_name
            )

            if full_declaration is None:
                continue

            constant_name = self._extract_version_constant(full_declaration)

            if constant_name:
                if self._update_constant_value(lines, constant_name, branch_name):
                    updated_declaration = full_declaration.replace(
                        f":tag => {constant_name}", f":branch => {constant_name}"
                    )
                    if start_idx == end_idx:
                        lines[start_idx] = updated_declaration + "\n"
                    else:
                        lines[start_idx] = updated_declaration + "\n"
                        for j in range(start_idx + 1, end_idx + 1):
                            lines[j] = ""
                    return True
            else:
                updated_declaration = full_declaration

                import re

                updated_declaration = re.sub(
                    r":tag\s*=>\s*['\"][^'\"]*['\"]",
                    f":branch => '{branch_name}'",
                    updated_declaration,
                )

                updated_declaration = re.sub(
                    r":branch\s*=>\s*['\"][^'\"]*['\"]",
                    f":branch => '{branch_name}'",
                    updated_declaration,
                )

                if start_idx == end_idx:
                    lines[start_idx] = updated_declaration + "\n"
                else:
                    lines[start_idx] = updated_declaration + "\n"
                    for j in range(start_idx + 1, end_idx + 1):
                        lines[j] = ""
                return True

        return False


class BatchBranchDialog(BottomSheetDialog):
    """批量切换到Branch模式的对话框 - 卡片列表式"""

    def __init__(self, pods_info, podfile_path=None, podfile_lines=None, parent=None):
        self.pods_info = pods_info
        self.podfile_path = podfile_path
        self.podfile_lines = podfile_lines or []
        self.branch_configs = {}
        self.git_urls = {}
        self.worker = None
        self.loading_widget = None
        self.pod_cards = []

        super().__init__(parent, title="批量切换到Branch模式", max_height_ratio=0.85)

        self._build_content()
        self._apply_content_styles()
        self.load_pods_info()
        self.setup_sheet_ui()

    def _build_content(self):
        desc_label = QLabel(
            '为每个 Pod 选择目标分支，勾选"创建新分支"可基于现有分支创建'
        )
        desc_label.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 12px; background: transparent; border: none;"
        )
        self.content_layout.addWidget(desc_label)

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

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent; border: none;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 12, 0)
        self.cards_layout.setSpacing(12)

        self.scroll_area.setWidget(self.cards_container)
        self.content_layout.addWidget(self.scroll_area, 1)

        self.confirm_btn.setText("切换")
        self.confirm_btn.clicked.disconnect()
        self.confirm_btn.clicked.connect(self.switch_all_to_branch)

    def _apply_content_styles(self):
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

        current_branch = pod_info.get("current_branch", "")
        if current_branch:
            branch_badge = QLabel(current_branch)
            branch_badge.setStyleSheet(f"""
                QLabel {{
                    color: #a5b4fc;
                    font-size: 11px;
                    background-color: rgba(99, 102, 241, 0.15);
                    border: 1px solid rgba(99, 102, 241, 0.25);
                    border-radius: 4px;
                    padding: 2px 8px;
                }}
            """)
            header_layout.addWidget(branch_badge)

        header_layout.addStretch()
        card_layout.addLayout(header_layout)

        path_label = QLabel(pod_info["path"])
        path_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_MUTED};
                font-size: 11px;
                background: transparent;
                border: none;
            }}
        """)
        card_layout.addWidget(path_label)

        branch_row = QHBoxLayout()
        branch_row.setSpacing(12)

        branch_label = QLabel("目标分支:")
        branch_label.setFixedWidth(65)
        branch_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        branch_row.addWidget(branch_label)

        branches = pod_info.get("branches", [])
        branch_combo = CustomDropdown()
        branch_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        branch_combo.addItems(branches)

        if "origin/master" in branches:
            branch_combo.setCurrentText("origin/master")
        elif "origin/main" in branches:
            branch_combo.setCurrentText("origin/main")
        elif branches:
            branch_combo.setCurrentText(branches[0])

        branch_combo.currentTextChanged.connect(
            lambda text, r=row: self.on_branch_changed(r, text)
        )
        branch_row.addWidget(branch_combo)
        card_layout.addLayout(branch_row)

        create_row = QHBoxLayout()
        create_row.setSpacing(12)

        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        checked_icon = os.path.join(
            base_dir, "resources", "icons", "check_box.svg"
        ).replace("\\", "/")
        unchecked_icon = os.path.join(
            base_dir, "resources", "icons", "uncheck_box.svg"
        ).replace("\\", "/")

        create_checkbox = QCheckBox("创建新分支")
        create_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {Colors.TEXT_SECONDARY};
                font-size: 12px;
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: none;
                image: url({unchecked_icon});
            }}
            QCheckBox::indicator:checked {{
                image: url({checked_icon});
            }}
            QCheckBox::indicator:hover {{
                opacity: 0.8;
            }}
        """)
        create_checkbox.stateChanged.connect(
            lambda state, r=row: self.on_create_new_changed(r, state)
        )
        create_row.addWidget(create_checkbox)
        create_row.addStretch()
        card_layout.addLayout(create_row)

        base_row = QHBoxLayout()
        base_row.setSpacing(12)

        base_label = QLabel("基于分支:")
        base_label.setFixedWidth(65)
        base_label.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 12px; background: transparent;"
        )
        base_row.addWidget(base_label)

        base_combo = CustomDropdown()
        base_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        base_combo.addItems(branches)
        base_combo.setEnabled(False)

        if "origin/master" in branches:
            base_combo.setCurrentText("origin/master")
        elif "origin/main" in branches:
            base_combo.setCurrentText("origin/main")
        elif branches:
            base_combo.setCurrentText(branches[0])

        base_combo.currentTextChanged.connect(
            lambda text, r=row: self.on_base_branch_changed(r, text)
        )
        base_row.addWidget(base_combo)
        card_layout.addLayout(base_row)

        self.pod_cards.append(
            {
                "card": card,
                "branch_combo": branch_combo,
                "create_checkbox": create_checkbox,
                "base_combo": base_combo,
            }
        )

        return card

    def load_pods_info(self):
        for row, pod_info in enumerate(self.pods_info):
            pod_name = pod_info["name"]
            local_path = pod_info["path"]

            git_url = GitService.get_remote_url(local_path)
            self.git_urls[pod_name] = git_url if git_url else "获取失败"

            card = self._create_pod_card(row, pod_info)
            self.cards_layout.addWidget(card)

            branches = pod_info.get("branches", [])
            self.branch_configs[row] = {
                "branch": self.pod_cards[row]["branch_combo"].currentText()
                if branches
                else "",
                "is_new": False,
                "base_branch": self.pod_cards[row]["base_combo"].currentText()
                if branches
                else "origin/master",
            }

        self.cards_layout.addStretch()

    def on_branch_changed(self, row, text):
        if row in self.branch_configs:
            self.branch_configs[row]["branch"] = text

    def on_create_new_changed(self, row, state):
        if row in self.branch_configs:
            is_checked = state == 2
            self.branch_configs[row]["is_new"] = is_checked

            card_data = self.pod_cards[row]
            base_combo = card_data["base_combo"]
            branch_combo = card_data["branch_combo"]

            base_combo.setEnabled(is_checked)

            if is_checked:
                branch_combo.setEditable(True)
                branch_combo.lineEdit().setReadOnly(False)
                branch_combo.lineEdit().setPlaceholderText("输入新分支名...")
                branch_combo.lineEdit().setText("")
            else:
                branch_combo.setEditable(False)
                branches = self.pods_info[row].get("branches", [])
                if "origin/master" in branches:
                    branch_combo.setCurrentText("origin/master")
                elif "origin/main" in branches:
                    branch_combo.setCurrentText("origin/main")
                elif branches:
                    branch_combo.setCurrentText(branches[0])

    def on_base_branch_changed(self, row, text):
        if row in self.branch_configs:
            self.branch_configs[row]["base_branch"] = text

    def switch_all_to_branch(self):
        for row, pod_info in enumerate(self.pods_info):
            config = self.branch_configs.get(row, {})
            if not config.get("branch", ""):
                ModernDialog.warning(self, "警告", f"请为 {pod_info['name']} 选择分支")
                return

        reply = ModernDialog.question(
            self,
            "确认",
            f"确定要将 {len(self.branch_configs)} 个Pod切换到Branch模式吗？",
            ModernDialog.Yes | ModernDialog.No,
        )
        if reply != ModernDialog.Yes:
            return

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
        self.loading_widget = LoadingWidget("切换中...")
        loading_layout = QVBoxLayout()
        loading_layout.addWidget(self.loading_widget)
        loading_dialog.setLayout(loading_layout)
        loading_dialog.show()
        self.loading_widget.start_animation()

        if not self.podfile_lines:
            try:
                with open(self.podfile_path, "r", encoding="utf-8") as f:
                    self.podfile_lines = f.readlines()
            except Exception as e:
                self.loading_widget.stop_animation()
                loading_dialog.close()
                ModernDialog.error(self, "错误", f"读取Podfile失败: {str(e)}")
                return

        self.worker = BranchSwitchWorker(
            self.pods_info,
            self.branch_configs,
            self.git_urls,
            self.podfile_path,
            self.podfile_lines,
        )
        self.worker.setParent(None)
        self.worker.finished.connect(
            lambda result: self._on_branch_switch_finished(result, loading_dialog)
        )
        self.worker.start()

    def _on_branch_switch_finished(self, result, loading_dialog):
        if self.loading_widget:
            self.loading_widget.stop_animation()

        loading_dialog.close()

        success_count = result["success_count"]
        fail_count = result["fail_count"]
        error_messages = result["error_messages"]

        result_msg = f"切换完成：成功 {success_count} 个，失败 {fail_count} 个"
        if error_messages:
            result_msg += "\n\n失败详情:\n" + "\n".join(error_messages[:10])

        if fail_count == 0:
            ModernDialog.information(self, "成功", result_msg)
            self.accept()
        else:
            ModernDialog.warning(self, "警告", result_msg)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            reply = ModernDialog.question(
                self,
                "确认",
                "分支切换正在进行中，确定要取消吗？",
                ModernDialog.Yes | ModernDialog.No,
                ModernDialog.No,
            )
            if reply == ModernDialog.No:
                return
            self.worker.quit()
            self.worker.wait(2000)
        event.accept()
