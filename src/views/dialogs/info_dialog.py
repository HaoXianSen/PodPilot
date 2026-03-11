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
from src.styles import Colors, Styles
from src.resources.icons import IconManager


class InfoDialog(QDialog):
    """美化信息对话框 - Glassmorphism 风格"""

    def __init__(self, title, message, details=None, dialog_type="info", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setMaximumWidth(600)
        self._dialog_type = dialog_type
        self.initUI(message, details, dialog_type)

    def initUI(self, message, details, dialog_type):
        layout = QVBoxLayout()
        layout.setSpacing(16)

        # 根据类型设置图标和颜色
        icons = {
            "info": ("info", Colors.BRANCH),
            "warning": ("info", Colors.DEV),
            "error": ("x", "#ff3b30"),
            "success": ("tag", Colors.TAG),
        }

        icon_name, icon_color = icons.get(dialog_type, icons["info"])

        # 消息区域
        message_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(IconManager.get_pixmap(icon_name, 32, icon_color))
        icon_label.setFixedSize(50, 50)

        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 500;
            color: {Colors.TEXT_PRIMARY};
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
            details_text.setStyleSheet(f"""
                QTextEdit {{
                    background-color: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 6px;
                    padding: 8px;
                    font-family: monospace;
                    font-size: 12px;
                    color: {Colors.TEXT_PRIMARY};
                }}
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

        # 应用样式 - Glassmorphism 风格
        self.setStyleSheet(f"""
            QDialog {{
                background-color: rgba(30, 30, 40, 0.9);
                border-radius: 12px;
            }}
            QGroupBox {{
                border: 1px solid {Colors.SURFACE_BORDER};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                font-weight: 600;
                background-color: {Colors.SURFACE};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QPushButton {{
                background-color: rgba(59, 130, 246, 0.5);
                color: {Colors.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: 500;
                min-height: 32px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: rgba(59, 130, 246, 0.6);
            }}
            QPushButton[type="primary"] {{
                background-color: rgba(59, 130, 246, 0.5);
            }}
            QPushButton[type="primary"]:hover {{
                background-color: rgba(59, 130, 246, 0.6);
            }}
            QPushButton[type="cancel"] {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            QPushButton[type="cancel"]:hover {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
        """)
