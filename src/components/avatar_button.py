# -*- coding: utf-8 -*-
import os
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import (
    QPixmap,
    QPainter,
    QBitmap,
    QIcon,
    QColor,
    QRadialGradient,
    QBrush,
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtSvg import QSvgRenderer


class AvatarButton(QPushButton):
    """自定义头像按钮 - 使用 SVG 默认头像"""

    avatar_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(36, 36)
        self._avatar_path = None
        self.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 0;
                margin: 0;
                border-radius: 18px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self._set_default_avatar()

    def _set_default_avatar(self):
        """设置默认头像 - 使用 SVG 图标"""
        svg_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "resources",
            "icons",
            "avatar_default.svg",
        )

        if os.path.exists(svg_path):
            # 使用 SVG 渲染
            renderer = QSvgRenderer(svg_path)
            pixmap = QPixmap(72, 72)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
        else:
            # 后备方案：手动绘制
            pixmap = QPixmap(72, 72)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # 渐变背景
            from PyQt5.QtGui import QRadialGradient, QBrush

            gradient = QRadialGradient(36, 36, 36)
            gradient.setColorAt(0, QColor("#667eea"))
            gradient.setColorAt(1, QColor("#764ba2"))
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 72, 72)

            # 白色人形
            painter.setBrush(QColor("white"))
            painter.drawEllipse(26, 16, 20, 20)  # 头
            painter.drawEllipse(20, 40, 32, 24)  # 身体
            painter.end()

        # 缩放到按钮大小
        scaled = pixmap.scaled(
            36, 36, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )

        # 创建圆形遮罩
        mask = QBitmap(36, 36)
        mask.fill(Qt.color0)
        mask_painter = QPainter(mask)
        mask_painter.setRenderHint(QPainter.Antialiasing)
        mask_painter.setBrush(Qt.color1)
        mask_painter.setPen(Qt.NoPen)
        mask_painter.drawEllipse(0, 0, 36, 36)
        mask_painter.end()
        scaled.setMask(mask)

        self.setIcon(QIcon(scaled))
        self.setIconSize(QSize(36, 36))

    def set_avatar_path(self, path):
        """设置头像图片路径"""
        self._avatar_path = path
        if path:
            self._set_custom_avatar(path)
        else:
            self._set_default_avatar()
        self.update()
        self.avatar_changed.emit()

    def _set_custom_avatar(self, path):
        """设置自定义头像"""
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._set_default_avatar()
            return

        # 缩放到合适大小
        scaled = pixmap.scaled(
            36, 36, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )

        # 居中裁剪
        x = (scaled.width() - 36) // 2
        y = (scaled.height() - 36) // 2
        cropped = scaled.copy(x, y, 36, 36)

        # 创建圆形遮罩
        mask = QBitmap(36, 36)
        mask.fill(Qt.color0)
        mask_painter = QPainter(mask)
        mask_painter.setRenderHint(QPainter.Antialiasing)
        mask_painter.setBrush(Qt.color1)
        mask_painter.setPen(Qt.NoPen)
        mask_painter.drawEllipse(0, 0, 36, 36)
        mask_painter.end()
        cropped.setMask(mask)

        self.setIcon(QIcon(cropped))
        self.setIconSize(QSize(36, 36))
