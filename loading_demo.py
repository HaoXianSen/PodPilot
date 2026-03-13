#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LoadingWidget 使用示例和演示

展示四种现代化的 Loading 动画样式：
1. STYLE_SPINNER - 旋转圆环（默认，推荐）
2. STYLE_DOTS - 跳动圆点
3. STYLE_PULSE - 脉冲圆环
4. STYLE_BARS - 竖条动画
"""

import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QWidget,
    QLabel,
)
from PyQt5.QtCore import Qt
from src.widgets.loading_widget import LoadingWidget


class LoadingDemo(QMainWindow):
    """Loading 样式演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("现代化 Loading Widget 演示")
        self.setGeometry(100, 100, 900, 600)

        # 主容器
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)

        # 标题
        title = QLabel("现代化 Loading Widget 样式")
        title.setStyleSheet("""
            QLabel {
                color: #1d1d1f;
                font-size: 24px;
                font-weight: 600;
            }
        """)
        main_layout.addWidget(title)

        # 创建网格布局展示四种样式
        grid_layout = QHBoxLayout()
        grid_layout.setSpacing(20)

        # 样式1：旋转圆环
        spinner_container = self._create_demo_box(
            "旋转圆环", "推荐使用，流畅平滑", LoadingWidget.STYLE_SPINNER
        )
        grid_layout.addWidget(spinner_container)

        # 样式2：跳动圆点
        dots_container = self._create_demo_box(
            "跳动圆点", "简洁轻快", LoadingWidget.STYLE_DOTS
        )
        grid_layout.addWidget(dots_container)

        # 样式3：脉冲圆环
        pulse_container = self._create_demo_box(
            "脉冲圆环", "呼吸动感", LoadingWidget.STYLE_PULSE
        )
        grid_layout.addWidget(pulse_container)

        # 样式4：竖条动画
        bars_container = self._create_demo_box(
            "竖条动画", "音乐可视化风格", LoadingWidget.STYLE_BARS
        )
        grid_layout.addWidget(bars_container)

        main_layout.addLayout(grid_layout)

        # 使用说明
        usage_text = """
使用方法：

# 方式1：直接使用 LoadingWidget
from src.widgets.loading_widget import LoadingWidget

loading = LoadingWidget("加载中...", LoadingWidget.STYLE_SPINNER)
loading.start_animation()

# 方式2：使用 ModernLoadingDialog（带半透明背景）
from src.widgets.loading_widget import ModernLoadingDialog

dialog = ModernLoadingDialog("处理中...", LoadingWidget.STYLE_SPINNER, self)
dialog.start()
# ... 执行操作 ...
dialog.stop()

# 方式3：在已有对话框中使用
loading_widget = LoadingWidget("加载中...")
layout.addWidget(loading_widget)
loading_widget.start_animation()
        """

        usage_label = QLabel(usage_text)
        usage_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f7;
                color: #1d1d1f;
                font-size: 12px;
                font-family: 'Monaco', 'Courier New', monospace;
                padding: 20px;
                border-radius: 8px;
            }
        """)
        main_layout.addWidget(usage_label)

        # 设置背景
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea,
                    stop:1 #764ba2
                );
            }
        """)

    def _create_demo_box(self, title, description, style):
        """创建单个演示盒子"""
        container = QWidget()
        container.setFixedSize(200, 280)
        container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 标题
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #1d1d1f;
                font-size: 14px;
                font-weight: 600;
            }
        """)
        layout.addWidget(title_label)

        # 描述
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 11px;
            }
        """)
        layout.addWidget(desc_label)

        # Loading Widget
        loading = LoadingWidget("加载中...", style)
        loading.start_animation()
        layout.addWidget(loading)

        return container


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoadingDemo()
    window.show()
    sys.exit(app.exec_())
