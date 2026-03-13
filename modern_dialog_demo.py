#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ModernDialog 演示程序
展示五种对话框类型的视觉效果
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel
from PyQt5.QtCore import Qt
from src.components.modern_dialog import ModernDialog


class DialogDemo(QMainWindow):
    """ModernDialog 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ModernDialog 演示")
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QLabel("ModernDialog 五种类型演示")
        title.setStyleSheet("""
            QLabel {
                color: #1d1d1f;
                font-size: 24px;
                font-weight: 600;
            }
        """)
        layout.addWidget(title)

        # 信息对话框
        info_btn = QPushButton("1. Information（信息提示）")
        info_btn.clicked.connect(self.show_info)
        layout.addWidget(info_btn)

        # 成功对话框
        success_btn = QPushButton("2. Success（成功提示）")
        success_btn.clicked.connect(self.show_success)
        layout.addWidget(success_btn)

        # 警告对话框
        warning_btn = QPushButton("3. Warning（警告）")
        warning_btn.clicked.connect(self.show_warning)
        layout.addWidget(warning_btn)

        # 错误对话框
        error_btn = QPushButton("4. Error（错误）")
        error_btn.clicked.connect(self.show_error)
        layout.addWidget(error_btn)

        # 确认对话框
        question_btn = QPushButton("5. Question（确认对话框）")
        question_btn.clicked.connect(self.show_question)
        layout.addWidget(question_btn)

        layout.addStretch()

        # 设置背景
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea,
                    stop:1 #764ba2
                );
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                color: #1d1d1f;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 1);
            }
        """)

    def show_info(self):
        ModernDialog.information(
            self,
            "提示",
            "当前项目中没有发现使用tag引用的Pod"
        )

    def show_success(self):
        ModernDialog.success(
            self,
            "成功",
            "切换完成：成功 3 个，失败 0 个"
        )

    def show_warning(self):
        ModernDialog.warning(
            self,
            "警告",
            "以下Pod未选择Tag:\n• PodA\n• PodB\n\n请为所有Pod选择Tag后再切换。"
        )

    def show_error(self):
        ModernDialog.error(
            self,
            "错误",
            "处理MR信息时发生错误:\n网络连接超时"
        )

    def show_question(self):
        reply = ModernDialog.question(
            self,
            "确认",
            "确定要为 3 个Pod切换Tag吗？\n\n这将修改Podfile中的Pod引用。"
        )
        if reply == ModernDialog.Yes:
            ModernDialog.success(self, "确认", "您点击了"确定"按钮")
        else:
            ModernDialog.information(self, "取消", "您点击了"取消"按钮")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DialogDemo()
    window.show()
    sys.exit(app.exec_())
