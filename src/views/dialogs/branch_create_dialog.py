from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QGridLayout,
    QDialog,
    QVBoxLayout,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
    QComboBox,
    QMessageBox,
)
from PyQt5.QtCore import Qt
import re


class BranchCreateDialog(QDialog):
    """创建或选择分支对话框"""

    def __init__(self, pod_name, local_path, existing_branches, parent=None):
        super().__init__(parent)
        self.pod_name = pod_name
        self.local_path = local_path
        self.existing_branches = existing_branches
        self.selected_branch = ""
        self.is_new_branch = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"{self.pod_name} - 选择或创建分支")
        self.setGeometry(300, 300, 500, 350)
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
            QComboBox {
                border: 1px solid #d1d1d6;
                border-radius: 6px;
                padding: 6px 12px;
                background-color: white;
                min-height: 26px;
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
            QRadioButton {
                color: #1d1d1f;
                font-size: 12px;
                padding: 4px 0;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #d1d1d6;
                border-radius: 8px;
                background-color: white;
            }
            QRadioButton::indicator:checked {
                background-color: #007aff;
                border: 2px solid #007aff;
            }
        """)

        layout = QVBoxLayout()

        # 模式选择
        mode_group = QGroupBox("选择模式")
        mode_layout = QVBoxLayout()

        self.mode_radio_group = QButtonGroup()

        # 单选按钮1：选择现有分支
        self.select_existing_radio = QRadioButton("选择现有分支")
        self.select_existing_radio.setChecked(True)
        self.mode_radio_group.addButton(self.select_existing_radio, 1)
        self.select_existing_radio.toggled.connect(self.on_mode_changed)

        # 单选按钮2：创建新分支
        self.create_new_radio = QRadioButton("创建新分支")
        self.mode_radio_group.addButton(self.create_new_radio, 2)
        self.create_new_radio.toggled.connect(self.on_mode_changed)

        mode_layout.addWidget(self.select_existing_radio)
        mode_layout.addWidget(self.create_new_radio)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # 现有分支选择
        self.existing_branch_group = QGroupBox("现有分支")
        existing_layout = QVBoxLayout()
        self.branch_combo = QComboBox()
        self.branch_combo.addItems(self.existing_branches)
        self.branch_combo.currentTextChanged.connect(self.on_branch_selected)
        existing_layout.addWidget(self.branch_combo)
        self.existing_branch_group.setLayout(existing_layout)
        layout.addWidget(self.existing_branch_group)

        # 新分支输入
        self.new_branch_group = QGroupBox("新分支名称")
        new_branch_layout = QVBoxLayout()

        # 分支名称输入
        new_branch_layout.addWidget(QLabel("分支名称:"))
        self.new_branch_edit = QLineEdit()
        self.new_branch_edit.setPlaceholderText("例如: feature/new-feature")
        new_branch_layout.addWidget(self.new_branch_edit)

        # 基础分支选择
        new_branch_layout.addWidget(QLabel("基于:"))
        self.base_branch_combo = QComboBox()
        self.base_branch_combo.setEditable(True)
        self.base_branch_combo.addItems(self.existing_branches)
        if "master" in self.existing_branches:
            self.base_branch_combo.setCurrentText("master")
        elif "main" in self.existing_branches:
            self.base_branch_combo.setCurrentText("main")
        new_branch_layout.addWidget(self.base_branch_combo)

        self.new_branch_group.setLayout(new_branch_layout)
        self.new_branch_group.setEnabled(False)  # 默认禁用
        layout.addWidget(self.new_branch_group)

        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.validate_and_accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.setProperty("type", "cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def on_mode_changed(self):
        """模式切换"""
        is_select = self.select_existing_radio.isChecked()
        self.existing_branch_group.setEnabled(is_select)
        self.new_branch_group.setEnabled(not is_select)

    def on_branch_selected(self, branch_name):
        """分支选择"""
        self.selected_branch = branch_name
        self.is_new_branch = False

    def validate_and_accept(self):
        """验证并接受"""
        if self.select_existing_radio.isChecked():
            branch = self.branch_combo.currentText()
            if not branch:
                QMessageBox.warning(self, "警告", "请选择一个分支")
                return
            self.selected_branch = branch
            self.is_new_branch = False
        else:
            branch = self.new_branch_edit.text().strip()
            if not branch:
                QMessageBox.warning(self, "警告", "请输入新分支名称")
                return

            # 验证分支名称
            if re.search(r"[\s~^:?*\[\]\\]", branch):
                QMessageBox.warning(self, "警告", "分支名称包含非法字符")
                return

            if branch in self.existing_branches:
                reply = QMessageBox.question(
                    self, "确认", f"分支 '{branch}' 已存在，是否覆盖？"
                )
                if reply != QMessageBox.Yes:
                    return

            self.selected_branch = branch
            self.is_new_branch = True

        self.accept()

    def get_result(self):
        """返回结果"""
        base_branch = self.base_branch_combo.currentText()
        return {
            "branch": self.selected_branch,
            "is_new": self.is_new_branch,
            "base_branch": base_branch if self.is_new_branch else None,
        }
