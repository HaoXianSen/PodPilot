# -*- coding: utf-8 -*-
"""
自定义复选框组件 - 带对勾标记
"""

from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient
from src.styles import Colors


class CustomCheckBox(QWidget):
    """自定义复选框 - Glassmorphism 风格，带对勾"""

    stateChanged = pyqtSignal(int)

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._checked = False
        self._text = text
        self._is_hovering = False

        self.setFixedHeight(30)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

        # 布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 复选框区域（自定义绘制）
        self.checkbox_area = QWidget()
        self.checkbox_area.setFixedSize(20, 20)
        layout.addWidget(self.checkbox_area)

        # 文本标签
        self.text_label = QLabel(text)
        self.text_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 13px;
                background: transparent;
            }}
        """)
        layout.addWidget(self.text_label)
        layout.addStretch()

    def isChecked(self):
        """返回选中状态"""
        return self._checked

    def setChecked(self, checked):
        """设置选中状态"""
        if self._checked != checked:
            self._checked = checked
            self.update()
            self.stateChanged.emit(Qt.Checked if checked else Qt.Unchecked)

    def mousePressEvent(self, event):
        """鼠标点击切换状态"""
        self.setChecked(not self._checked)

    def enterEvent(self, event):
        """鼠标进入"""
        self._is_hovering = True
        self.update()

    def leaveEvent(self, event):
        """鼠标离开"""
        self._is_hovering = False
        self.update()

    def paintEvent(self, event):
        """绘制复选框"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 复选框位置
        checkbox_x = 0
        checkbox_y = (self.height() - 20) // 2

        if self._checked:
            # 选中状态：绿色渐变背景 + 白色对勾
            gradient = QLinearGradient(
                checkbox_x, checkbox_y, checkbox_x, checkbox_y + 20
            )
            gradient.setColorAt(0, QColor("#34c759"))
            gradient.setColorAt(1, QColor("#22c55e"))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(checkbox_x, checkbox_y, 20, 20, 5, 5)

            # 绘制白色对勾
            painter.setPen(
                QPen(
                    QColor(255, 255, 255), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin
                )
            )
            # 对勾的两条线段
            painter.drawLine(
                checkbox_x + 5, checkbox_y + 10, checkbox_x + 8, checkbox_y + 14
            )
            painter.drawLine(
                checkbox_x + 8, checkbox_y + 14, checkbox_x + 15, checkbox_y + 6
            )
        else:
            # 未选中状态：半透明背景 + 边框
            if self._is_hovering:
                painter.setBrush(QBrush(QColor(255, 255, 255, 20)))
                painter.setPen(QPen(QColor(255, 255, 255, 102), 2))
            else:
                painter.setBrush(QBrush(QColor(255, 255, 255, 13)))
                painter.setPen(QPen(QColor(255, 255, 255, 76), 2))

            painter.drawRoundedRect(checkbox_x, checkbox_y, 20, 20, 5, 5)
