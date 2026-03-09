from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QPainter, QColor, QPixmap, QPen
from PyQt5.QtCore import Qt, pyqtSignal


class AvatarButton(QPushButton):
    """自定义头像按钮"""

    avatar_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(36, 36)
        self._avatar_path = None
        self._pixmap = None
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

    def set_avatar_path(self, path):
        """设置头像图片路径"""
        self._avatar_path = path
        if path:
            self._pixmap = QPixmap(path)
        else:
            self._pixmap = None
        self.update()
        self.avatar_changed.emit()

    def paintEvent(self, a0):
        w = self.width()
        h = self.height()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )

            from PyQt5.QtGui import QPainterPath

            clip_path = QPainterPath()
            clip_path.addEllipse(0, 0, w, h)
            painter.setClipPath(clip_path)
            painter.drawPixmap(0, 0, scaled)
        else:
            painter.setBrush(QColor("#007aff"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 36, 36)

            painter.setBrush(QColor("white"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(14, 10, 8, 8)
            painter.drawEllipse(13, 19, 10, 6)
