from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QGroupBox,
)
from PyQt5.QtCore import Qt


class InfoDialog(QDialog):
    """美化信息对话框"""

    def __init__(self, title, message, details=None, dialog_type="info", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setMaximumWidth(600)
        self.initUI(message, details, dialog_type)

    def initUI(self, message, details, dialog_type):
        layout = QVBoxLayout()
        layout.setSpacing(16)

        # 根据类型设置图标和颜色
        icons = {
            "info": ("ℹ️", "#007aff"),
            "warning": ("⚠️", "#ff9500"),
            "error": ("❌", "#ff3b30"),
            "success": ("✅", "#34c759"),
        }

        icon_emoji, icon_color = icons.get(dialog_type, icons["info"])

        # 消息区域
        message_layout = QHBoxLayout()
        icon_label = QLabel(icon_emoji)
        icon_label.setStyleSheet(f"font-size: 32px;")
        icon_label.setFixedSize(50, 50)

        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 500;
            color: #1d1d1f;
            padding: 5px 0;
        """)

        message_layout.addWidget(icon_label)
        message_layout.addWidget(message_label)
        message_layout.setAlignment(Qt.AlignLeft)
        layout.addLayout(message_layout)

        # 详细信息区域（如果有）
        if details:
            details_group = QGroupBox("详细信息")
            details_layout = QVBoxLayout()

            details_text = QTextEdit()
            details_text.setReadOnly(True)
            details_text.setMaximumHeight(150)
            details_text.setText(str(details))
            details_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f5f5f7;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    padding: 8px;
                    font-family: monospace;
                    font-size: 12px;
                }
            """)

            details_layout.addWidget(details_text)
            details_group.setLayout(details_layout)
            layout.addWidget(details_group)

        # 按钮区域
        btn_layout = QHBoxLayout()

        if dialog_type == "info":
            ok_btn = QPushButton("知道了")
            ok_btn.clicked.connect(self.accept)
            btn_layout.addWidget(ok_btn)
        else:
            ok_btn = QPushButton("确定")
            ok_btn.clicked.connect(self.accept)
            ok_btn.setProperty("type", "primary")

            cancel_btn = QPushButton("取消")
            cancel_btn.clicked.connect(self.reject)
            cancel_btn.setProperty("type", "cancel")

            btn_layout.addWidget(ok_btn)
            btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # 应用样式
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f5f5f7;
            }}
            QGroupBox {{
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                font-weight: 600;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                color: #1d1d1f;
            }}
            QPushButton {{
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: 500;
                min-height: 32px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #0051d5;
            }}
            QPushButton[type="primary"] {{
                background-color: #007aff;
            }}
            QPushButton[type="primary"]:hover {{
                background-color: #0051d5;
            }}
            QPushButton[type="cancel"] {{
                background-color: #e8e8ed;
                color: #1d1d1f;
            }}
            QPushButton[type="cancel"]:hover {{
                background-color: #d1d1d6;
            }}
        """)
