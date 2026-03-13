from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QFrame,
    QWidget,
    QScrollArea,
    QSizePolicy,
    QApplication,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from src.widgets.loading_widget import LoadingWidget
from src.widgets.custom_dropdown import CustomDropdown
from src.styles import Colors, Styles
from src.components.modern_dialog import ModernDialog
from src.components.bottom_sheet_dialog import BottomSheetDialog
import subprocess
import os
import re


class TagCreationWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, pods_info, pod_configs, branch_selections):
        super().__init__()
        self.pods_info = pods_info
        self.pod_configs = pod_configs
        self.branch_selections = branch_selections

    def _clean_tag_name(self, tag_name):
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

            tag_name = self._clean_tag_name(
                self.pod_configs.get(row, {}).get("tag_name", "").strip()
            )
            if not tag_name:
                continue

            tag_message = self.pod_configs.get(row, {}).get("tag_message", "").strip()
            if not tag_message:
                tag_message = f"Release {tag_name}"

            selected_branch = self.branch_selections.get(row, "")

            try:
                if selected_branch and selected_branch != "无分支":
                    subprocess.run(
                        ["git", "fetch", "origin"],
                        capture_output=True,
                        cwd=local_path,
                        check=True,
                    )

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
                    subprocess.run(
                        ["git", "tag", "-a", tag_name, "-m", tag_message],
                        cwd=local_path,
                        check=True,
                    )

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


class BatchTagDialog(BottomSheetDialog):
    """批量创建Tag对话框 - 卡片列表式"""

    def __init__(self, pods_info, parent=None):
        self.pods_info = pods_info
        self.pod_configs = {}
        self.pod_cards = []
        self.worker = None
        self.loading_widget = None

        super().__init__(parent, title="批量创建Tag", max_height_ratio=0.85)

        self._build_content()
        self._apply_content_styles()
        self.load_pods_info()
        self.setup_sheet_ui()

    def _build_content(self):
        desc_label = QLabel(
            '为每个 Pod 设置 Tag 名称和消息，基于选择的分支创建'
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

        self.confirm_btn.setText("批量创建Tag")
        self.confirm_btn.clicked.disconnect()
        self.confirm_btn.clicked.connect(self.create_all_tags)

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

        # 头部：Pod名称 + 当前分支
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

        # 已有Tag徽章
        tags = self.get_sorted_tags(pod_info["path"])
        if tags:
            latest_tag_badge = QLabel(tags[0])
            latest_tag_badge.setStyleSheet(f"""
                QLabel {{
                    color: #fbbf24;
                    font-size: 11px;
                    background-color: rgba(251, 191, 36, 0.15);
                    border: 1px solid rgba(251, 191, 36, 0.25);
                    border-radius: 4px;
                    padding: 2px 8px;
                }}
            """)
            latest_tag_badge.setToolTip("最新Tag: " + "\n".join(tags[:5]))
            header_layout.addWidget(latest_tag_badge)

        header_layout.addStretch()
        card_layout.addLayout(header_layout)

        # 路径
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

        # 选择分支
        branch_row = QHBoxLayout()
        branch_row.setSpacing(12)

        branch_label = QLabel("基于分支:")
        branch_label.setFixedWidth(65)
        branch_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        branch_row.addWidget(branch_label)

        branches = pod_info.get("branches", [])
        branch_combo = CustomDropdown()
        branch_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if branches:
            branch_combo.addItems(branches)
            master_branches = [b for b in branches if "master" in b.lower()]
            if master_branches:
                if "master" in master_branches:
                    branch_combo.setCurrentText("master")
                elif "origin/master" in master_branches:
                    branch_combo.setCurrentText("origin/master")
                else:
                    branch_combo.setCurrentText(master_branches[0])
        else:
            branch_combo.addItem("无分支")

        branch_row.addWidget(branch_combo)
        card_layout.addLayout(branch_row)

        # Tag名称
        tag_row = QHBoxLayout()
        tag_row.setSpacing(12)

        tag_label = QLabel("Tag名称:")
        tag_label.setFixedWidth(65)
        tag_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        tag_row.addWidget(tag_label)

        recommended_tag = self.generate_recommended_tag(tags)
        tag_input = QLineEdit(recommended_tag)
        tag_input.setPlaceholderText("输入Tag名称...")
        tag_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tag_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 6px 10px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-color: rgba(102, 126, 234, 0.6);
                background-color: rgba(255, 255, 255, 0.1);
            }}
        """)
        tag_input.textChanged.connect(
            lambda text, r=row: self.on_tag_changed(r, text)
        )
        tag_row.addWidget(tag_input)
        card_layout.addLayout(tag_row)

        # Tag消息
        msg_row = QHBoxLayout()
        msg_row.setSpacing(12)

        msg_label = QLabel("消息:")
        msg_label.setFixedWidth(65)
        msg_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        msg_row.addWidget(msg_label)

        msg_input = QLineEdit(f"Release {recommended_tag}")
        msg_input.setPlaceholderText("输入Tag消息...")
        msg_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        msg_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 6px 10px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-color: rgba(102, 126, 234, 0.6);
                background-color: rgba(255, 255, 255, 0.1);
            }}
        """)
        msg_input.textChanged.connect(
            lambda text, r=row: self.on_message_changed(r, text)
        )
        msg_row.addWidget(msg_input)
        card_layout.addLayout(msg_row)

        self.pod_cards.append(
            {
                "card": card,
                "branch_combo": branch_combo,
                "tag_input": tag_input,
                "msg_input": msg_input,
            }
        )

        return card

    def load_pods_info(self):
        for row, pod_info in enumerate(self.pods_info):
            tags = self.get_sorted_tags(pod_info["path"])
            recommended_tag = self.generate_recommended_tag(tags)

            self.pod_configs[row] = {
                "tag_name": recommended_tag,
                "tag_message": f"Release {recommended_tag}",
            }

            card = self._create_pod_card(row, pod_info)
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def on_tag_changed(self, row, text):
        if row in self.pod_configs:
            self.pod_configs[row]["tag_name"] = text
            # 自动更新消息
            card_data = self.pod_cards[row]
            current_msg = card_data["msg_input"].text()
            if current_msg.startswith("Release "):
                card_data["msg_input"].setText(f"Release {text}")
                self.pod_configs[row]["tag_message"] = f"Release {text}"

    def on_message_changed(self, row, text):
        if row in self.pod_configs:
            self.pod_configs[row]["tag_message"] = text

    def get_sorted_tags(self, local_path):
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
        if not existing_tags:
            return "v1.0.0"

        latest_tag = existing_tags[0]
        version_match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", latest_tag)

        if version_match:
            major, minor, patch = map(int, version_match.groups())
            return f"v{major}.{minor}.{patch + 1}"
        else:
            return "v1.0.0"

    def create_all_tags(self):
        # 验证所有Tag名称
        for row, pod_info in enumerate(self.pods_info):
            config = self.pod_configs.get(row, {})
            if not config.get("tag_name", "").strip():
                ModernDialog.warning(self, "警告", f"请为 {pod_info['name']} 输入Tag名称")
                return

        reply = ModernDialog.question(
            self,
            "确认",
            f"确定要为 {len(self.pods_info)} 个Pod创建Tag吗？",
            ModernDialog.Yes | ModernDialog.No,
        )

        if reply != ModernDialog.Yes:
            return

        # 收集分支选择
        branch_selections = {}
        for row in range(len(self.pod_cards)):
            branch_combo = self.pod_cards[row]["branch_combo"]
            selected_branch = branch_combo.currentText() if branch_combo.currentIndex() >= 0 else ""
            branch_selections[row] = selected_branch

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
        self.loading_widget = LoadingWidget("创建中...")
        loading_layout = QVBoxLayout()
        loading_layout.addWidget(self.loading_widget)
        loading_dialog.setLayout(loading_layout)
        loading_dialog.show()
        self.loading_widget.start_animation()

        self.worker = TagCreationWorker(
            self.pods_info, self.pod_configs, branch_selections
        )
        self.worker.finished.connect(
            lambda result: self._on_tag_creation_finished(result, loading_dialog)
        )
        self.worker.setParent(None)
        self.worker.start()

    def _on_tag_creation_finished(self, result, loading_dialog):
        if self.loading_widget:
            self.loading_widget.stop_animation()

        loading_dialog.close()

        success_count = result["success_count"]
        fail_count = result["fail_count"]
        error_messages = result["error_messages"]

        result_msg = f"创建完成：成功 {success_count} 个，失败 {fail_count} 个"
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
                "Tag创建正在进行中，确定要取消吗？",
                ModernDialog.Yes | ModernDialog.No,
                ModernDialog.No,
            )
            if reply == ModernDialog.No:
                event.ignore()
                return
            self.worker.quit()
            self.worker.wait(2000)
        event.accept()
