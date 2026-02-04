from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt


class AvatarButton(QPushButton):
    """自定义头像按钮"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(36, 36)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 4px;
                margin: 0;
                min-height: 36px;
                min-width: 36px;
            }
            QPushButton:hover {
                background-color: #e0e5ff;
            }
        """)

    def paintEvent(self, a0):
        w = self.width()
        h = self.height()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(QColor("#007aff"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 36, 36)

        painter.setBrush(QColor("white"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(14, 10, 8, 8)
        painter.drawEllipse(13, 19, 10, 6)
