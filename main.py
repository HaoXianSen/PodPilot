# -*- coding: utf-8 -*-
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from src.views.main_window import PodPilot


def main():
    app = QApplication(sys.argv)
    # 设置应用图标 - 使用不同尺寸的图标以适应不同场景
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # 使用 32px 作为窗口图标（macOS 标准标题栏图标尺寸）
    icon_path = os.path.join(base_dir, "resources", "icons", "app_icon_32.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    # 设置应用样式为 macOS 风格
    # 可用的样式包括: "windows", "fusion", "macos" 等
    # 当前使用的样式是: macos
    app.setStyle("macos")
    window = PodPilot()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
