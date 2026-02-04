from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QLabel,
    QLineEdit,
    QGridLayout,
    QDialog,
)


class PodConfigDialog(QDialog):
    def __init__(self, pod_name, local_path="", parent=None):
        super().__init__(parent)
        self.pod_name = pod_name
        self.local_path = local_path
        self.initUI()
        if local_path:
            self.path_edit.setText(local_path)

    def initUI(self):
        self.setWindowTitle(f"配置 {self.pod_name}")
        self.setGeometry(300, 300, 600, 150)
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
        """)

        layout = QGridLayout()

        # Pod名称显示
        layout.addWidget(QLabel("Pod名称:"), 0, 0)
        name_label = QLabel(self.pod_name)
        name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(name_label, 0, 1)

        # 本地路径选择
        layout.addWidget(QLabel("本地开发路径:"), 1, 0)

        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        path_layout.addWidget(self.path_edit)

        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout, 1, 1)

        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.setProperty("type", "cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout, 2, 1)

        self.setLayout(layout)

    def browse_path(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择Pod本地开发目录")
        if dir_path:
            self.local_path = dir_path
            self.path_edit.setText(dir_path)

    def get_local_path(self):
        return self.local_path
