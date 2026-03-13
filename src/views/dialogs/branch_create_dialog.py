from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QGridLayout,
    QVBoxLayout,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
    QComboBox,
    QMessageBox,
)
from PyQt5.QtCore import Qt
import re

from src.styles import Colors, Styles, GlassmorphismStyle
from src.components.bottom_sheet_dialog import BottomSheetDialog


class BranchCreateDialog(BottomSheetDialog):
    """创建或选择分支对话框 - Bottom Sheet 风格"""

    def __init__(self, pod_name, local_path, existing_branches, parent=None):
        self.pod_name = pod_name
        self.local_path = local_path
        self.existing_branches = existing_branches
        self.selected_branch = ""
        self.is_new_branch = False

        super().__init__(
            parent, title=f"{pod_name} - 选择或创建分支", max_height_ratio=0.7
        )

        self._build_content()
        self._apply_content_styles()
        self.setup_sheet_ui()

    def _build_content(self):
        mode_group = QGroupBox("选择模式")
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(8)

        self.mode_radio_group = QButtonGroup()

        self.select_existing_radio = QRadioButton("选择现有分支")
        self.select_existing_radio.setChecked(True)
        self.mode_radio_group.addButton(self.select_existing_radio, 1)
        self.select_existing_radio.toggled.connect(self.on_mode_changed)

        self.create_new_radio = QRadioButton("创建新分支")
        self.mode_radio_group.addButton(self.create_new_radio, 2)
        self.create_new_radio.toggled.connect(self.on_mode_changed)

        mode_layout.addWidget(self.select_existing_radio)
        mode_layout.addWidget(self.create_new_radio)
        mode_group.setLayout(mode_layout)
        self.content_layout.addWidget(mode_group)

        self.existing_branch_group = QGroupBox("现有分支")
        existing_layout = QVBoxLayout()
        existing_layout.setSpacing(8)
        self.branch_combo = QComboBox()
        self.branch_combo.addItems(self.existing_branches)
        self.branch_combo.currentTextChanged.connect(self.on_branch_selected)
        existing_layout.addWidget(self.branch_combo)
        self.existing_branch_group.setLayout(existing_layout)
        self.content_layout.addWidget(self.existing_branch_group)

        self.new_branch_group = QGroupBox("新分支名称")
        new_branch_layout = QVBoxLayout()
        new_branch_layout.setSpacing(8)

        new_branch_layout.addWidget(QLabel("分支名称:"))
        self.new_branch_edit = QLineEdit()
        self.new_branch_edit.setPlaceholderText("例如: feature/new-feature")
        new_branch_layout.addWidget(self.new_branch_edit)

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
        self.new_branch_group.setEnabled(False)
        self.content_layout.addWidget(self.new_branch_group)

        self.confirm_btn.clicked.disconnect()
        self.confirm_btn.clicked.connect(self.validate_and_accept)
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.reject)

    def _apply_content_styles(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.15);
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 500;
                min-height: 26px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.25);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            QPushButton:disabled {{
                background-color: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.3);
            }}
            QLabel {{
                color: {Colors.TEXT_LABEL};
                font-size: 12px;
                font-weight: 600;
                background: transparent;
            }}
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 13px;
                min-height: 32px;
            }}
            QLineEdit:hover {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
            QLineEdit:focus {{
                border: 2px solid rgba(102, 126, 234, 0.6);
                background-color: rgba(255, 255, 255, 0.12);
            }}
            QLineEdit::placeholder {{
                color: rgba(255, 255, 255, 0.4);
            }}
            QComboBox {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 6px 12px;
                color: {Colors.TEXT_PRIMARY};
                min-height: 26px;
            }}
            QComboBox:hover {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
            QComboBox:focus {{
                border: 2px solid rgba(102, 126, 234, 0.6);
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid rgba(255, 255, 255, 0.6);
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #1a1a2e;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 4px;
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: rgba(102, 126, 234, 0.4);
            }}
            QGroupBox {{
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                margin-top: 16px;
                padding: 16px;
                padding-top: 24px;
                font-weight: 600;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 13px;
            }}
            QGroupBox:disabled {{
                background-color: rgba(255, 255, 255, 0.03);
                border-color: rgba(255, 255, 255, 0.06);
            }}
            QGroupBox:disabled::title {{
                color: rgba(255, 255, 255, 0.3);
            }}
            QRadioButton {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 12px;
                padding: 6px 0;
                spacing: 8px;
            }}
            QRadioButton:disabled {{
                color: rgba(255, 255, 255, 0.3);
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 9px;
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QRadioButton::indicator:hover {{
                border-color: rgba(102, 126, 234, 0.6);
                background-color: rgba(255, 255, 255, 0.15);
            }}
            QRadioButton::indicator:checked {{
                background-color: rgba(102, 126, 234, 0.8);
                border: 2px solid rgba(102, 126, 234, 1);
            }}
            QRadioButton::indicator:disabled {{
                background-color: rgba(255, 255, 255, 0.05);
                border-color: rgba(255, 255, 255, 0.15);
            }}
        """)

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
                ModernDialog.warning(self, "警告", "请选择一个分支")
                return
            self.selected_branch = branch
            self.is_new_branch = False
        else:
            branch = self.new_branch_edit.text().strip()
            if not branch:
                ModernDialog.warning(self, "警告", "请输入新分支名称")
                return

            if re.search(r"[\s~^:?*\[\]\\]", branch):
                ModernDialog.warning(self, "警告", "分支名称包含非法字符")
                return

            if branch in self.existing_branches:
                reply = ModernDialog.question(
                    self, "确认", f"分支 '{branch}' 已存在，是否覆盖？"
                )
                if reply != ModernDialog.Yes:
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
