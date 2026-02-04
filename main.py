# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication
from src.views.main_window import PodPilot


def main():
    app = QApplication(sys.argv)
    # 设置应用样式为 macOS 风格
    # 可用的样式包括: "windows", "fusion", "macos" 等
    # 当前使用的样式是: macos
    app.setStyle("macos")
    window = PodPilot()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
