from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QLabel,
    QLineEdit,
    QGridLayout,
    QDialog,
    QFrame,
    QVBoxLayout,
)
from PyQt5.QtCore import Qt

from src.styles import Colors, Styles, GlassmorphismStyle


class PodConfigDialog(QDialog):
    def __init__(self, pod_name, local_path="", parent=None):
        super().__init__(parent)
        self._titlebar_setup = False
        self.pod_name = pod_name
        self.local_path = local_path
        self.initUI()
        if local_path:
            self.path_edit.setText(local_path)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._titlebar_setup:
            GlassmorphismStyle.setup_transparent_titlebar(self)
            self._titlebar_setup = True

    def initUI(self):
        self.setWindowTitle(f"配置 {self.pod_name}")
        self.setFixedSize(520, 200)
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.BG_GRADIENT_START},
                    stop:0.5 {Colors.BG_GRADIENT_MID},
                    stop:1 {Colors.BG_GRADIENT_END}
                );
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        title = QLabel(f"配置 {self.pod_name}")
        title.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 18px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        main_layout.addWidget(title)

        card = QFrame()
        card.setObjectName("configCard")
        card.setStyleSheet(f"""
            QFrame#configCard {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.SURFACE_BORDER};
                border-radius: 12px;
            }}
        """)

        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)
        card_layout.setColumnStretch(1, 1)

        name_label = QLabel("Pod名称:")
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_MUTED};
                font-size: 13px;
                background: transparent;
                border: none;
            }}
        """)
        card_layout.addWidget(name_label, 0, 0)

        name_value = QLabel(self.pod_name)
        name_value.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 13px;
                font-weight: 500;
                background: transparent;
                border: none;
            }}
        """)
        card_layout.addWidget(name_value, 0, 1)

        path_label = QLabel("本地路径:")
        path_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_MUTED};
                font-size: 13px;
                background: transparent;
                border: none;
            }}
        """)
        card_layout.addWidget(path_label, 1, 0)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)

        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setFixedHeight(36)
        self.path_edit.setStyleSheet(Styles.LINE_EDIT)
        path_row.addWidget(self.path_edit, 1)

        browse_btn = QPushButton("浏览")
        browse_btn.setFixedSize(70, 36)
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.15);
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 8px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.25);
            }}
        """)
        browse_btn.clicked.connect(self.browse_path)
        path_row.addWidget(browse_btn)

        card_layout.addLayout(path_row, 1, 1)

        main_layout.addWidget(card)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 36)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setFixedSize(80, 36)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(59, 130, 246, 0.3);
                color: {Colors.BRANCH};
                border: 1px solid rgba(59, 130, 246, 0.5);
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(59, 130, 246, 0.4);
            }}
        """)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        main_layout.addLayout(btn_layout)

    def browse_path(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择Pod本地开发目录")
        if dir_path:
            self.local_path = dir_path
            self.path_edit.setText(dir_path)

    def get_local_path(self):
        return self.local_path
