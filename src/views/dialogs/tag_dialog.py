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
    QListWidget,
    QComboBox,
)
import subprocess
import os
import re


class TagDialog(QDialog):
    def __init__(self, pod_name, local_path, parent=None):
        super().__init__(parent)
        self.pod_name = pod_name
        self.local_path = local_path
        self.tag_message = ""
        self.existing_tags = []
        self.initUI()
        self.load_existing_tags()
        self.load_tag_templates()

    def initUI(self):
        self.setWindowTitle(f"为 {self.pod_name} 打Tag")
        self.setGeometry(300, 300, 700, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f7;
            }
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 400;
                min-height: 26px;
                max-height: 26px;
                min-width: 70px;
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
            }
            QLineEdit:focus {
                border: 2px solid #007aff;
            }
            QTextEdit {
                border: 1px solid #d1d1d6;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
            }
            QComboBox {
                border: 1px solid #d1d1d6;
                border-radius: 6px;
                padding: 6px 12px;
                background-color: white;
                min-height: 26px;
            }
            QListWidget {
                border: 1px solid #d1d1d6;
                border-radius: 4px;
                padding: 4px;
                background-color: white;
                max-height: 120px;
            }
            QListWidget::item {
                padding: 4px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: 600;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                color: #1d1d1f;
            }
        """)

        layout = QVBoxLayout()

        # 显示Pod信息
        info_group = QGroupBox("Pod信息")
        info_layout = QGridLayout()
        info_layout.addWidget(QLabel("Pod名称:"), 0, 0)
        info_layout.addWidget(QLabel(self.pod_name), 0, 1)
        info_layout.addWidget(QLabel("本地路径:"), 1, 0)
        info_layout.addWidget(QLabel(self.local_path), 1, 1)

        # 当前分支
        info_layout.addWidget(QLabel("当前分支:"), 2, 0)
        self.current_branch_label = QLabel("加载中...")
        self.current_branch_label.setStyleSheet("color: #007aff; font-weight: bold;")
        info_layout.addWidget(self.current_branch_label, 2, 1)

        # 分支切换按钮
        switch_branch_btn = QPushButton("切换分支")
        switch_branch_btn.setProperty("buttonType", "info")
        switch_branch_btn.clicked.connect(self.switch_branch)
        info_layout.addWidget(switch_branch_btn, 2, 2)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 加载当前分支
        self.load_current_branch()

        # Tag信息输入
        tag_group = QGroupBox("Tag信息")
        tag_layout = QVBoxLayout()

        # Tag名称输入
        tag_name_layout = QHBoxLayout()
        tag_name_layout.addWidget(QLabel("Tag名称:"))
        self.tag_name_edit = QLineEdit()
        self.tag_name_edit.setPlaceholderText("例如: v1.0.0")
        self.tag_name_edit.textChanged.connect(self.validate_tag_name)
        tag_name_layout.addWidget(self.tag_name_edit)
        tag_layout.addLayout(tag_name_layout)

        # Tag名称验证提示
        self.tag_name_hint = QLabel()
        self.tag_name_hint.setStyleSheet("color: #ff3b30; font-size: 11px;")
        tag_layout.addWidget(self.tag_name_hint)

        # 版本建议
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("版本建议:"))
        self.version_combo = QComboBox()
        self.version_combo.currentTextChanged.connect(self.use_suggested_version)
        version_layout.addWidget(self.version_combo)
        tag_layout.addLayout(version_layout)

        # 已有Tag列表
        tag_layout.addWidget(QLabel("已有Tag (点击使用):"))
        self.existing_tags_list = QListWidget()
        self.existing_tags_list.itemClicked.connect(self.use_existing_tag)
        tag_layout.addWidget(self.existing_tags_list)

        # Tag消息模板选择
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("消息模板:"))
        self.template_combo = QComboBox()
        self.template_combo.currentIndexChanged.connect(self.apply_template)
        template_layout.addWidget(self.template_combo)
        tag_layout.addLayout(template_layout)

        # Tag消息输入
        tag_layout.addWidget(QLabel("Tag消息:"))
        self.tag_message_edit = QTextEdit()
        self.tag_message_edit.setMaximumHeight(80)
        tag_layout.addWidget(self.tag_message_edit)

        tag_group.setLayout(tag_layout)
        layout.addWidget(tag_group)

        # 按钮
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("创建Tag")
        create_btn.clicked.connect(self.create_tag)
        cancel_btn = QPushButton("取消")
        cancel_btn.setProperty("type", "cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

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

                # 显示到列表
                self.existing_tags_list.clear()
                for tag in self.existing_tags:
                    self.existing_tags_list.addItem(tag)

                # 生成版本建议
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
            # 如果没有tag，建议v1.0.0
            self.version_combo.addItem("v1.0.0")
            return

        # 尝试从最新tag解析版本号
        latest_tag = self.existing_tags[0]
        version_match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", latest_tag)

        if version_match:
            major, minor, patch = map(int, version_match.groups())

            # 建议补丁版本递增
            suggestions = [
                f"v{major}.{minor}.{patch + 1}",  # 补丁版本
                f"v{major}.{minor + 1}.0",  # 次版本
                f"v{major + 1}.0.0",  # 主版本
            ]

            # 也添加主版本号前缀的版本
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
            # 无法解析版本号，建议v1.0.0
            self.version_combo.addItem("v1.0.0")

    def validate_tag_name(self, tag_name):
        """验证tag名称格式"""
        if not tag_name:
            self.tag_name_hint.setText("")
            return

        # Git tag命名规则：不能包含空格、~^:等特殊字符
        # 不允许以.开头，不能连续..等
        errors = []

        # 检查非法字符
        if re.search(r"[\s~^:?*\[\]\\]", tag_name):
            errors.append("不能包含空格、~^:?*[]\\等特殊字符")

        # 检查是否以.开头
        if tag_name.startswith("."):
            errors.append("不能以.开头")

        # 检查连续的点
        if ".." in tag_name:
            errors.append("不能包含连续的..")

        # 检查是否已存在
        if tag_name in self.existing_tags:
            errors.append(f"Tag '{tag_name}' 已存在，将覆盖")

        if errors:
            self.tag_name_hint.setText("; ".join(errors))
        else:
            self.tag_name_hint.setText("✓ 格式正确")
            self.tag_name_hint.setStyleSheet("color: #34c759; font-size: 11px;")

    def use_suggested_version(self, version):
        """使用建议的版本号"""
        if version and version != "v1.0.0":
            self.tag_name_edit.setText(version)

    def use_existing_tag(self, item):
        """使用已有的tag"""
        tag_name = item.text()
        self.tag_name_edit.setText(tag_name)

        # 获取tag消息
        try:
            result = subprocess.run(
                ["git", "tag", "-l", tag_name, "-n999"],
                capture_output=True,
                text=True,
                cwd=self.local_path,
            )

            if result.returncode == 0:
                # 提取tag消息（跳过第一行的tag名称）
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    message = "\n".join(lines[1:])
                    self.tag_message_edit.setText(message)

        except Exception as e:
            print(f"获取tag消息失败: {str(e)}")

    def apply_template(self, index):
        """应用消息模板"""
        if index == 0:  # "选择模板"
            return

        template = self.template_combo.currentText()
        tag_name = self.tag_name_edit.text().strip()

        # 替换模板变量
        message = template
        if tag_name:
            message = message.replace("{version}", tag_name)

        self.tag_message_edit.setText(message)

    def create_tag(self):
        tag_name = self.tag_name_edit.text().strip()
        tag_message = self.tag_message_edit.toPlainText().strip()

        if not tag_name:
            QMessageBox.warning(self, "警告", "请输入Tag名称")
            return

        # 再次验证tag名称
        if re.search(r"[\s~^:?*\[\]\\]", tag_name):
            QMessageBox.warning(self, "警告", "Tag名称包含非法字符，请检查红色提示信息")
            return

        # 检查tag是否已存在
        if tag_name in self.existing_tags:
            reply = QMessageBox.question(
                self,
                "确认",
                f"Tag '{tag_name}' 已存在，是否删除后重新创建？",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                # 删除已存在的tag
                try:
                    subprocess.run(
                        ["git", "tag", "-d", tag_name],
                        capture_output=True,
                        cwd=self.local_path,
                    )
                except Exception as e:
                    QMessageBox.warning(self, "警告", f"删除已有tag失败: {str(e)}")
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
            # 获取所有分支
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
                QMessageBox.information(self, "提示", "没有可用的分支")
                return

            # 显示分支选择对话框
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
                # 切换分支
                result = subprocess.run(
                    ["git", "checkout", branch_name],
                    capture_output=True,
                    text=True,
                    cwd=self.local_path,
                    check=True,
                )

                QMessageBox.information(self, "成功", f"已切换到分支: {branch_name}")

                # 重新加载当前分支
                self.load_current_branch()
                # 重新加载标签列表
                self.load_existing_tags()

        except subprocess.CalledProcessError as e:
            QMessageBox.warning(self, "警告", f"切换分支失败: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"切换分支错误: {str(e)}")
