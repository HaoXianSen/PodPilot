# -*- coding: utf-8 -*-
"""
ModernDialog - 现代化对话框组件
替代 QMessageBox，提供 Glassmorphism 风格的对话框
"""

from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGraphicsOpacityEffect,
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient, QFont
from src.styles import Colors


class ModernDialog(QDialog):
    """现代化对话框 - Glassmorphism 风格"""

    # 对话框类型
    TYPE_INFO = "info"
    TYPE_SUCCESS = "success"
    TYPE_WARNING = "warning"
    TYPE_ERROR = "error"
    TYPE_QUESTION = "question"

    # 返回值（兼容 QMessageBox）
    Yes = 1
    No = 0
    Ok = 1
    Cancel = 0

    def __init__(
        self,
        parent,
        title,
        message,
        dialog_type=TYPE_INFO,
        buttons=None,
    ):
        super().__init__(parent)
        self.result_value = self.Cancel
        self._dialog_type = dialog_type
        self._title = title
        self._message = message
        self._buttons = buttons or ["确定"]

        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)

        self._init_ui()
        self._setup_animations()

        # 居中显示
        if parent:
            parent_rect = parent.geometry()
            dialog_width = 400
            dialog_height = self._calculate_height()
            x = parent_rect.x() + (parent_rect.width() - dialog_width) // 2
            y = parent_rect.y() + (parent_rect.height() - dialog_height) // 2
            self.setGeometry(x, y, dialog_width, dialog_height)
        else:
            self.resize(400, self._calculate_height())

    def _calculate_height(self):
        """计算对话框高度"""
        base_height = 240
        # 根据消息长度调整
        message_lines = len(self._message.split("\n"))
        if message_lines > 3:
            base_height += (message_lines - 3) * 20
        return min(base_height, 600)

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 对话框容器
        container = QFrame()
        container.setObjectName("dialogContainer")
        container.setStyleSheet(f"""
            QFrame#dialogContainer {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 30, 46, 0.95),
                    stop:1 rgba(20, 20, 35, 0.95)
                );
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 16px;
            }}
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(24, 24, 24, 24)
        container_layout.setSpacing(16)

        # 图标
        icon_widget = self._create_icon()
        icon_layout = QHBoxLayout()
        icon_layout.addStretch()
        icon_layout.addWidget(icon_widget)
        icon_layout.addStretch()
        container_layout.addLayout(icon_layout)

        # 标题
        title_label = QLabel(self._title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 18px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        container_layout.addWidget(title_label)

        # 消息
        message_label = QLabel(self._message)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.85);
                font-size: 13px;
                line-height: 1.6;
                background: transparent;
                border: none;
            }}
        """)
        container_layout.addWidget(message_label)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()

        for i, btn_text in enumerate(self._buttons):
            is_primary = i == len(self._buttons) - 1  # 最后一个按钮是主按钮
            btn = self._create_button(btn_text, is_primary)
            button_layout.addWidget(btn)

        container_layout.addLayout(button_layout)

        main_layout.addWidget(container)

    def _create_icon(self):
        """创建图标"""
        icon_widget = IconWidget(self._dialog_type)
        icon_widget.setFixedSize(60, 60)
        return icon_widget

    def _create_button(self, text, is_primary=False):
        """创建按钮"""
        btn = QPushButton(text)
        btn.setFixedHeight(40)
        btn.setMinimumWidth(100)
        btn.setCursor(Qt.PointingHandCursor)

        if is_primary:
            # 主按钮样式（根据对话框类型调整颜色）
            color = self._get_type_color()
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color}40;
                    color: {Colors.TEXT_PRIMARY};
                    border: 1px solid {color}99;
                    border-radius: 8px;
                    padding: 10px 24px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {color}55;
                    border-color: {color}cc;
                }}
                QPushButton:pressed {{
                    background-color: {color}35;
                }}
            """)
        else:
            # 次按钮样式
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(255, 255, 255, 0.1);
                    color: rgba(255, 255, 255, 0.8);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    padding: 10px 24px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.18);
                    border-color: rgba(255, 255, 255, 0.3);
                }}
                QPushButton:pressed {{
                    background-color: rgba(255, 255, 255, 0.12);
                }}
            """)

        # 连接信号
        if text in ["确定", "完成", "是", "继续"]:
            btn.clicked.connect(lambda: self._on_button_clicked(self.Yes))
        else:
            btn.clicked.connect(lambda: self._on_button_clicked(self.No))

        return btn

    def _get_type_color(self):
        """根据类型获取颜色"""
        colors = {
            self.TYPE_INFO: "#3b82f6",
            self.TYPE_SUCCESS: "#34c759",
            self.TYPE_WARNING: "#fbbf24",
            self.TYPE_ERROR: "#f87171",
            self.TYPE_QUESTION: "#8b5cf6",
        }
        return colors.get(self._dialog_type, "#3b82f6")

    def _setup_animations(self):
        """设置动画"""
        # 淡入动画
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)

    def showEvent(self, event):
        """显示事件 - 播放淡入动画"""
        super().showEvent(event)
        self.fade_animation.start()

    def _on_button_clicked(self, value):
        """按钮点击"""
        self.result_value = value
        self._fade_out_and_close()

    def _fade_out_and_close(self):
        """淡出动画并关闭"""
        fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_out.setDuration(150)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.InCubic)
        fade_out.finished.connect(self.accept)
        fade_out.start()

        # 保存动画引用防止被垃圾回收
        self._fade_out_animation = fade_out

    # ============ 静态方法（兼容 QMessageBox API） ============

    @staticmethod
    def information(parent, title, message):
        """信息提示对话框"""
        dialog = ModernDialog(
            parent,
            title,
            message,
            dialog_type=ModernDialog.TYPE_INFO,
            buttons=["确定"],
        )
        dialog.exec_()

    @staticmethod
    def success(parent, title, message):
        """成功提示对话框"""
        dialog = ModernDialog(
            parent,
            title,
            message,
            dialog_type=ModernDialog.TYPE_SUCCESS,
            buttons=["完成"],
        )
        dialog.exec_()

    @staticmethod
    def warning(parent, title, message):
        """警告对话框"""
        dialog = ModernDialog(
            parent,
            title,
            message,
            dialog_type=ModernDialog.TYPE_WARNING,
            buttons=["确定"],
        )
        dialog.exec_()

    @staticmethod
    def error(parent, title, message):
        """错误对话框"""
        dialog = ModernDialog(
            parent,
            title,
            message,
            dialog_type=ModernDialog.TYPE_ERROR,
            buttons=["确定"],
        )
        dialog.exec_()

    @staticmethod
    def question(parent, title, message):
        """确认对话框（返回 Yes 或 No）"""
        dialog = ModernDialog(
            parent,
            title,
            message,
            dialog_type=ModernDialog.TYPE_QUESTION,
            buttons=["取消", "确定"],
        )
        dialog.exec_()
        return dialog.result_value

    # 兼容 QMessageBox.critical
    @staticmethod
    def critical(parent, title, message):
        """错误对话框（兼容 QMessageBox.critical）"""
        ModernDialog.error(parent, title, message)


class IconWidget(QWidget):
    """对话框图标组件 - 渐变圆形背景 + 符号"""

    def __init__(self, dialog_type, parent=None):
        super().__init__(parent)
        self._type = dialog_type
        self.setFixedSize(60, 60)

    def paintEvent(self, event):
        """绘制图标"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 获取类型颜色
        colors = {
            ModernDialog.TYPE_INFO: ("#3b82f6", "#2563eb"),
            ModernDialog.TYPE_SUCCESS: ("#34c759", "#22c55e"),
            ModernDialog.TYPE_WARNING: ("#fbbf24", "#f59e0b"),
            ModernDialog.TYPE_ERROR: ("#f87171", "#ef4444"),
            ModernDialog.TYPE_QUESTION: ("#8b5cf6", "#7c3aed"),
        }
        color_light, color_dark = colors.get(self._type, ("#3b82f6", "#2563eb"))

        # 绘制渐变圆形背景
        gradient = QLinearGradient(0, 0, 0, 60)
        gradient.setColorAt(0, QColor(color_light))
        gradient.setColorAt(1, QColor(color_dark))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(0, 0, 60, 60)

        # 绘制图标符号
        painter.setPen(QPen(QColor(255, 255, 255), 3, Qt.SolidLine, Qt.RoundCap))
        center_x, center_y = 30, 30

        if self._type == ModernDialog.TYPE_INFO:
            # 绘制 i 符号
            painter.drawEllipse(center_x - 2, center_y - 15, 4, 4)
            painter.drawLine(center_x, center_y - 7, center_x, center_y + 12)

        elif self._type == ModernDialog.TYPE_SUCCESS:
            # 绘制 ✓ 符号
            painter.drawLine(center_x - 10, center_y, center_x - 3, center_y + 8)
            painter.drawLine(center_x - 3, center_y + 8, center_x + 12, center_y - 8)

        elif self._type == ModernDialog.TYPE_WARNING:
            # 绘制 ! 符号
            painter.drawLine(center_x, center_y - 12, center_x, center_y + 2)
            painter.drawEllipse(center_x - 2, center_y + 8, 4, 4)

        elif self._type == ModernDialog.TYPE_ERROR:
            # 绘制 × 符号
            painter.drawLine(center_x - 8, center_y - 8, center_x + 8, center_y + 8)
            painter.drawLine(center_x + 8, center_y - 8, center_x - 8, center_y + 8)

        elif self._type == ModernDialog.TYPE_QUESTION:
            # 绘制 ? 符号
            painter.setFont(QFont("Arial", 24, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, "?")

    # ============ 静态便捷方法 ============

    @staticmethod
    def information(parent, title, message):
        """信息提示对话框"""
        dialog = ModernDialog(
            parent,
            title,
            message,
            dialog_type=ModernDialog.TYPE_INFO,
            buttons=["确定"],
        )
        dialog.exec_()

    @staticmethod
    def success(parent, title, message):
        """成功提示对话框"""
        dialog = ModernDialog(
            parent,
            title,
            message,
            dialog_type=ModernDialog.TYPE_SUCCESS,
            buttons=["完成"],
        )
        dialog.exec_()

    @staticmethod
    def warning(parent, title, message):
        """警告对话框"""
        dialog = ModernDialog(
            parent,
            title,
            message,
            dialog_type=ModernDialog.TYPE_WARNING,
            buttons=["确定"],
        )
        dialog.exec_()

    @staticmethod
    def error(parent, title, message):
        """错误对话框"""
        dialog = ModernDialog(
            parent,
            title,
            message,
            dialog_type=ModernDialog.TYPE_ERROR,
            buttons=["确定"],
        )
        dialog.exec_()

    @staticmethod
    def question(parent, title, message):
        """确认对话框（返回 Yes 或 No）"""
        dialog = ModernDialog(
            parent,
            title,
            message,
            dialog_type=ModernDialog.TYPE_QUESTION,
            buttons=["取消", "确定"],
        )
        dialog.exec_()
        return dialog.result_value

    @staticmethod
    def critical(parent, title, message):
        """错误对话框（兼容 QMessageBox.critical）"""
        ModernDialog.error(parent, title, message)
