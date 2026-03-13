from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QGridLayout,
    QVBoxLayout,
    QFrame,
    QTextEdit,
    QMessageBox,
    QListWidget,
    QComboBox,
    QScrollArea,
    QWidget,
)
from PyQt5.QtCore import Qt
import subprocess
import os
import re

from src.styles import Colors, Styles
from src.resources.icons import IconManager
from src.components.bottom_sheet_dialog import BottomSheetDialog


class TagDialog(BottomSheetDialog):
    def __init__(self, pod_name, local_path, parent=None):
        self.pod_name = pod_name
        self.local_path = local_path
        self.tag_message = ""
        self.existing_tags = []

        super().__init__(parent, title=f"为 {pod_name} 打Tag", max_height_ratio=0.85)

        self._build_content()
        self._apply_content_styles()
        self.setup_sheet_ui()
        self.load_existing_tags()
        self.load_tag_templates()

    def _build_content(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            {Styles.SCROLL_BAR}
        """)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(16)

        info_card = self._build_info_card()
        content_layout.addWidget(info_card)

        tag_card = self._build_tag_card()
        content_layout.addWidget(tag_card)

        scroll.setWidget(scroll_content)
        self.content_layout.addWidget(scroll, 1)

        self.confirm_btn.setText("创建Tag")
        self.confirm_btn.clicked.disconnect()
        self.confirm_btn.clicked.connect(self.create_tag)
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.reject)

        self.load_current_branch()

    def _apply_content_styles(self):
        pass

    def _build_info_card(self):
        card = QFrame()
        card.setObjectName("infoCard")
        card.setStyleSheet(f"""
            QFrame#infoCard {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.SURFACE_BORDER};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        section_title = QLabel("Pod 信息")
        section_title.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_LABEL};
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(section_title)

        info_grid = QGridLayout()
        info_grid.setSpacing(8)
        info_grid.setColumnStretch(1, 1)

        labels = [
            ("Pod名称:", self.pod_name),
            ("本地路径:", self.local_path),
        ]

        for row, (label_text, value) in enumerate(labels):
            label = QLabel(label_text)
            label.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_MUTED};
                    font-size: 12px;
                    background: transparent;
                    border: none;
                }}
            """)
            info_grid.addWidget(label, row, 0)

            value_label = QLabel(value)
            value_label.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_PRIMARY};
                    font-size: 12px;
                    background: transparent;
                    border: none;
                }}
            """)
            info_grid.addWidget(value_label, row, 1)

        branch_label = QLabel("当前分支:")
        branch_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_MUTED};
                font-size: 12px;
                background: transparent;
                border: none;
            }}
        """)
        info_grid.addWidget(branch_label, 2, 0)

        branch_row = QHBoxLayout()
        branch_row.setSpacing(8)

        self.current_branch_label = QLabel("加载中...")
        self.current_branch_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.BRANCH};
                font-size: 12px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        branch_row.addWidget(self.current_branch_label)
        branch_row.addStretch()

        switch_btn = QPushButton("切换分支")
        switch_btn.setFixedHeight(28)
        switch_btn.setCursor(Qt.PointingHandCursor)
        switch_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 0 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
        """)
        switch_btn.clicked.connect(self.switch_branch)
        branch_row.addWidget(switch_btn)

        branch_widget = QWidget()
        branch_widget.setStyleSheet("background: transparent; border: none;")
        branch_widget.setLayout(branch_row)
        info_grid.addWidget(branch_widget, 2, 1)

        layout.addLayout(info_grid)
        return card

    def _build_tag_card(self):
        card = QFrame()
        card.setObjectName("tagCard")
        card.setStyleSheet(f"""
            QFrame#tagCard {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.SURFACE_BORDER};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        section_title = QLabel("Tag 信息")
        section_title.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_LABEL};
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(section_title)

        tag_name_row = QHBoxLayout()
        tag_name_row.setSpacing(8)

        tag_name_label = QLabel("Tag名称:")
        tag_name_label.setFixedWidth(70)
        tag_name_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 13px;
                font-weight: 500;
                background: transparent;
                border: none;
            }}
        """)
        tag_name_row.addWidget(tag_name_label)

        self.tag_name_edit = QLineEdit()
        self.tag_name_edit.setPlaceholderText("例如: v1.0.0")
        self.tag_name_edit.setFixedHeight(36)
        self.tag_name_edit.setStyleSheet(Styles.LINE_EDIT)
        self.tag_name_edit.textChanged.connect(self.validate_tag_name)
        tag_name_row.addWidget(self.tag_name_edit)

        layout.addLayout(tag_name_row)

        self.tag_name_hint = QLabel()
        self.tag_name_hint.setStyleSheet(f"""
            QLabel {{
                color: #ff3b30;
                font-size: 11px;
                background: transparent;
                border: none;
                margin-left: 78px;
            }}
        """)
        layout.addWidget(self.tag_name_hint)

        version_row = QHBoxLayout()
        version_row.setSpacing(8)

        version_label = QLabel("版本建议:")
        version_label.setFixedWidth(70)
        version_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_MUTED};
                font-size: 12px;
                background: transparent;
                border: none;
            }}
        """)
        version_row.addWidget(version_label)

        self.version_combo = QComboBox()
        self.version_combo.setFixedHeight(32)
        self.version_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 0 10px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 12px;
            }}
            QComboBox:hover {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {Colors.TEXT_MUTED};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: rgba(30, 30, 40, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                selection-background-color: rgba(59, 130, 246, 0.4);
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        self.version_combo.currentTextChanged.connect(self.use_suggested_version)
        version_row.addWidget(self.version_combo)
        version_row.addStretch()

        layout.addLayout(version_row)

        existing_label = QLabel("已有Tag (点击使用):")
        existing_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_MUTED};
                font-size: 12px;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(existing_label)

        self.existing_tags_list = QListWidget()
        self.existing_tags_list.setMaximumHeight(100)
        self.existing_tags_list.setStyleSheet(f"""
            QListWidget {{
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 4px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 12px;
            }}
            QListWidget::item {{
                background-color: transparent;
                border-radius: 4px;
                padding: 6px 10px;
            }}
            QListWidget::item:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QListWidget::item:selected {{
                background-color: rgba(59, 130, 246, 0.3);
            }}
        """)
        self.existing_tags_list.itemClicked.connect(self.use_existing_tag)
        layout.addWidget(self.existing_tags_list)

        template_row = QHBoxLayout()
        template_row.setSpacing(8)

        template_label = QLabel("消息模板:")
        template_label.setFixedWidth(70)
        template_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_MUTED};
                font-size: 12px;
                background: transparent;
                border: none;
            }}
        """)
        template_row.addWidget(template_label)

        self.template_combo = QComboBox()
        self.template_combo.setFixedHeight(32)
        self.template_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 0 10px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 12px;
            }}
            QComboBox:hover {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {Colors.TEXT_MUTED};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: rgba(30, 30, 40, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                selection-background-color: rgba(59, 130, 246, 0.4);
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        self.template_combo.currentIndexChanged.connect(self.apply_template)
        template_row.addWidget(self.template_combo)
        template_row.addStretch()

        layout.addLayout(template_row)

        msg_label = QLabel("Tag消息:")
        msg_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_MUTED};
                font-size: 12px;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(msg_label)

        self.tag_message_edit = QTextEdit()
        self.tag_message_edit.setMaximumHeight(80)
        self.tag_message_edit.setStyleSheet(Styles.TEXT_EDIT)
        layout.addWidget(self.tag_message_edit)

        return card

    def load_existing_tags(self):
        """加载已有tag列表"""
        try:
            result = subprocess.run(
                ["git", "tag", "--sort=-creatordate"],
                capture_output=True,
                text=True,
                cwd=self.local_path,
            )

            if result.returncode == 0:
                self.existing_tags = result.stdout.strip().split("\n")
                self.existing_tags = [tag for tag in self.existing_tags if tag]

                self.existing_tags_list.clear()
                for tag in self.existing_tags:
                    self.existing_tags_list.addItem(tag)

                self.suggest_versions()

        except Exception as e:
            print(f"加载已有Tag失败: {str(e)}")

    def load_tag_templates(self):
        """加载tag消息模板"""
        templates = [
            "Release version {version}",
            "Hotfix for issue #{issue}",
            "Feature: {feature}",
            "Bugfix: {bug}",
            "Performance improvement",
            "Documentation update",
        ]
        self.template_combo.addItems(["-- 选择模板 --"] + templates)

    def suggest_versions(self):
        """根据已有tag建议下一个版本号"""
        self.version_combo.clear()

        if not self.existing_tags:
            self.version_combo.addItem("v1.0.0")
            return

        latest_tag = self.existing_tags[0]
        version_match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", latest_tag)

        if version_match:
            major, minor, patch = map(int, version_match.groups())

            suggestions = [
                f"v{major}.{minor}.{patch + 1}",
                f"v{major}.{minor + 1}.0",
                f"v{major + 1}.0.0",
            ]

            suggestions.extend(
                [
                    f"{major}.{minor}.{patch + 1}",
                    f"{major}.{minor + 1}.0",
                    f"{major + 1}.0.0",
                ]
            )

            for suggestion in suggestions[:6]:
                self.version_combo.addItem(suggestion)
        else:
            self.version_combo.addItem("v1.0.0")

    def validate_tag_name(self, tag_name):
        """验证tag名称格式"""
        if not tag_name:
            self.tag_name_hint.setText("")
            return

        errors = []

        if re.search(r"[\s~^:?*\[\]\\]", tag_name):
            errors.append("不能包含空格、~^:?*[]\\等特殊字符")

        if tag_name.startswith("."):
            errors.append("不能以.开头")

        if ".." in tag_name:
            errors.append("不能包含连续的..")

        if tag_name in self.existing_tags:
            errors.append(f"Tag '{tag_name}' 已存在，将覆盖")

        if errors:
            self.tag_name_hint.setText("; ".join(errors))
            self.tag_name_hint.setStyleSheet(f"""
                QLabel {{
                    color: #ff3b30;
                    font-size: 11px;
                    background: transparent;
                    border: none;
                    margin-left: 78px;
                }}
            """)
        else:
            self.tag_name_hint.setText("✓ 格式正确")
            self.tag_name_hint.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TAG};
                    font-size: 11px;
                    background: transparent;
                    border: none;
                    margin-left: 78px;
                }}
            """)

    def use_suggested_version(self, version):
        """使用建议的版本号"""
        if version and version != "v1.0.0":
            self.tag_name_edit.setText(version)

    def use_existing_tag(self, item):
        """使用已有的tag"""
        tag_name = item.text()
        self.tag_name_edit.setText(tag_name)

        try:
            result = subprocess.run(
                ["git", "tag", "-l", tag_name, "-n999"],
                capture_output=True,
                text=True,
                cwd=self.local_path,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    message = "\n".join(lines[1:])
                    self.tag_message_edit.setText(message)

        except Exception as e:
            print(f"获取tag消息失败: {str(e)}")

    def apply_template(self, index):
        """应用消息模板"""
        if index == 0:
            return

        template = self.template_combo.currentText()
        tag_name = self.tag_name_edit.text().strip()

        message = template
        if tag_name:
            message = message.replace("{version}", tag_name)

        self.tag_message_edit.setText(message)

    def create_tag(self):
        tag_name = self.tag_name_edit.text().strip()
        tag_message = self.tag_message_edit.toPlainText().strip()

        if not tag_name:
            ModernDialog.warning(self, "警告", "请输入Tag名称")
            return

        if re.search(r"[\s~^:?*\[\]\\]", tag_name):
            ModernDialog.warning(self, "警告", "Tag名称包含非法字符，请检查红色提示信息")
            return

        if tag_name in self.existing_tags:
            reply = ModernDialog.question(
                self,
                "确认",
                f"Tag '{tag_name}' 已存在，是否删除后重新创建？",
                ModernDialog.Yes | ModernDialog.No,
            )
            if reply == ModernDialog.Yes:
                try:
                    subprocess.run(
                        ["git", "tag", "-d", tag_name],
                        capture_output=True,
                        cwd=self.local_path,
                    )
                except Exception as e:
                    ModernDialog.warning(self, "警告", f"删除已有tag失败: {str(e)}")
                    return
            else:
                return

        self.tag_name = tag_name
        self.tag_message = tag_message
        self.accept()

    def get_tag_name(self):
        return self.tag_name

    def get_tag_message(self):
        return self.tag_message

    def load_current_branch(self):
        """加载当前Git分支"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=self.local_path,
                check=True,
            )
            current_branch = result.stdout.strip()
            self.current_branch_label.setText(current_branch)
        except subprocess.CalledProcessError as e:
            self.current_branch_label.setText("获取失败")
            print(f"获取当前分支失败: {str(e)}")

    def switch_branch(self):
        """切换Git分支"""
        try:
            result = subprocess.run(
                ["git", "branch", "-a"],
                capture_output=True,
                text=True,
                cwd=self.local_path,
                check=True,
            )
            branches = result.stdout.strip().split("\n")
            branches = [b.replace("*", "").strip() for b in branches if b.strip()]
            branches = [b for b in branches if not b.startswith("HEAD ->")]

            if not branches:
                ModernDialog.information(self, "提示", "没有可用的分支")
                return

            from PyQt5.QtWidgets import QInputDialog

            current_branch = self.current_branch_label.text()
            if current_branch == "加载中..." or current_branch == "获取失败":
                current_branch = ""

            branch_name, ok = QInputDialog.getItem(
                self,
                "切换分支",
                "选择要切换的分支:",
                branches,
                branches.index(current_branch) if current_branch in branches else 0,
                False,
            )

            if ok and branch_name:
                result = subprocess.run(
                    ["git", "checkout", branch_name],
                    capture_output=True,
                    text=True,
                    cwd=self.local_path,
                    check=True,
                )

                ModernDialog.information(self, "成功", f"已切换到分支: {branch_name}")

                self.load_current_branch()
                self.load_existing_tags()

        except subprocess.CalledProcessError as e:
            ModernDialog.warning(self, "警告", f"切换分支失败: {str(e)}")
        except Exception as e:
            ModernDialog.error(self, "错误", f"切换分支错误: {str(e)}")
