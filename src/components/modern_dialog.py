# -*- coding: utf-8 -*-
"""
ModernDialog - 现代化对话框组件
macOS 原生风格 - 左对齐布局 + 方形圆角图标
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
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QFont
from src.styles import Colors


class ModernDialog(QDialog):
    """现代化对话框 - macOS 原生风格"""

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
        base_height = 160
        message_lines = len(self._message.split("\n"))
        if message_lines > 2:
            base_height += (message_lines - 2) * 20
        # 根据消息长度估算行数
        estimated_lines = len(self._message) // 40 + 1
        if estimated_lines > message_lines:
            base_height += (estimated_lines - message_lines) * 18
        return min(base_height, 350)

    def _get_icon_colors(self):
        """获取图标背景色和前景色"""
        colors = {
            self.TYPE_INFO: ("rgba(59, 130, 246, 0.2)", "#3b82f6"),
            self.TYPE_SUCCESS: ("rgba(52, 199, 89, 0.2)", "#34c759"),
            self.TYPE_WARNING: ("rgba(251, 191, 36, 0.2)", "#fbbf24"),
            self.TYPE_ERROR: ("rgba(248, 113, 113, 0.2)", "#f87171"),
            self.TYPE_QUESTION: ("rgba(139, 92, 246, 0.2)", "#8b5cf6"),
        }
        return colors.get(self._dialog_type, ("rgba(59, 130, 246, 0.2)", "#3b82f6"))

    def _get_button_color(self):
        """获取主按钮颜色"""
        colors = {
            self.TYPE_INFO: "#3b82f6",
            self.TYPE_SUCCESS: "#34c759",
            self.TYPE_WARNING: "#f59e0b",
            self.TYPE_ERROR: "#ef4444",
            self.TYPE_QUESTION: "#3b82f6",
        }
        return colors.get(self._dialog_type, "#3b82f6")

    def _get_icon_symbol(self):
        """获取图标符号"""
        symbols = {
            self.TYPE_INFO: "i",
            self.TYPE_SUCCESS: "✓",
            self.TYPE_WARNING: "!",
            self.TYPE_ERROR: "✕",
            self.TYPE_QUESTION: "?",
        }
        return symbols.get(self._dialog_type, "i")

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 对话框容器
        container = QFrame()
        container.setObjectName("dialogContainer")
        container.setStyleSheet(f"""
            QFrame#dialogContainer {{
                background-color: rgba(40, 40, 50, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
            }}
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(20)

        # 头部区域（图标 + 内容）
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        header_layout.setAlignment(Qt.AlignTop)

        # 方形圆角图标
        icon_bg, icon_color = self._get_icon_colors()
        icon_widget = IconWidget(self._dialog_type)
        icon_widget.setFixedSize(48, 48)
        header_layout.addWidget(icon_widget, 0, Qt.AlignTop)

        # 内容区域
        content_layout = QVBoxLayout()
        content_layout.setSpacing(6)

        # 标题
        title_label = QLabel(self._title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 15px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        content_layout.addWidget(title_label)

        # 消息
        message_label = QLabel(self._message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.6);
                font-size: 13px;
                line-height: 1.5;
                background: transparent;
                border: none;
            }}
        """)
        content_layout.addWidget(message_label)

        header_layout.addLayout(content_layout, 1)
        container_layout.addLayout(header_layout)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()

        for i, btn_text in enumerate(self._buttons):
            is_primary = i == len(self._buttons) - 1
            btn = self._create_button(btn_text, is_primary)
            button_layout.addWidget(btn)

        container_layout.addLayout(button_layout)
        main_layout.addWidget(container)

    def _create_button(self, text, is_primary=False):
        """创建按钮"""
        btn = QPushButton(text)
        btn.setFixedHeight(32)
        btn.setMinimumWidth(72)
        btn.setCursor(Qt.PointingHandCursor)

        if is_primary:
            color = self._get_button_color()
            # 警告类型使用深色文字
            text_color = "#000" if self._dialog_type == self.TYPE_WARNING else "#fff"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: {text_color};
                    border: none;
                    border-radius: 8px;
                    padding: 6px 18px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    opacity: 0.9;
                }}
                QPushButton:pressed {{
                    background-color: {color};
                    opacity: 0.8;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(255, 255, 255, 0.08);
                    color: rgba(255, 255, 255, 0.8);
                    border: none;
                    border-radius: 8px;
                    padding: 6px 18px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.12);
                }}
                QPushButton:pressed {{
                    background-color: rgba(255, 255, 255, 0.06);
                }}
            """)

        # 连接信号
        if text in ["确定", "完成", "是", "继续", "好"]:
            btn.clicked.connect(lambda: self._on_button_clicked(self.Yes))
        else:
            btn.clicked.connect(lambda: self._on_button_clicked(self.No))

        return btn

    def _setup_animations(self):
        """设置动画"""
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(150)
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
        fade_out.setDuration(100)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.InCubic)
        fade_out.finished.connect(self.accept)
        fade_out.start()
        self._fade_out_animation = fade_out

    # ============ 静态方法（兼容 QMessageBox API） ============

    @staticmethod
    def information(parent, title, message):
        """信息提示对话框"""
        dialog = ModernDialog(
            parent, title, message,
            dialog_type=ModernDialog.TYPE_INFO,
            buttons=["确定"],
        )
        dialog.exec_()

    @staticmethod
    def success(parent, title, message):
        """成功提示对话框"""
        dialog = ModernDialog(
            parent, title, message,
            dialog_type=ModernDialog.TYPE_SUCCESS,
            buttons=["完成"],
        )
        dialog.exec_()

    @staticmethod
    def warning(parent, title, message):
        """警告对话框"""
        dialog = ModernDialog(
            parent, title, message,
            dialog_type=ModernDialog.TYPE_WARNING,
            buttons=["确定"],
        )
        dialog.exec_()

    @staticmethod
    def error(parent, title, message):
        """错误对话框"""
        dialog = ModernDialog(
            parent, title, message,
            dialog_type=ModernDialog.TYPE_ERROR,
            buttons=["确定"],
        )
        dialog.exec_()

    @staticmethod
    def question(parent, title, message, buttons=None, default_button=None):
        """确认对话框（返回 Yes 或 No）"""
        dialog = ModernDialog(
            parent, title, message,
            dialog_type=ModernDialog.TYPE_QUESTION,
            buttons=["取消", "确定"],
        )
        dialog.exec_()
        return dialog.result_value

    @staticmethod
    def critical(parent, title, message):
        """错误对话框（兼容 QMessageBox.critical）"""
        ModernDialog.error(parent, title, message)


class IconWidget(QWidget):
    """方形圆角图标组件"""

    def __init__(self, dialog_type, parent=None):
        super().__init__(parent)
        self._type = dialog_type
        self.setFixedSize(48, 48)

    def paintEvent(self, event):
        """绘制图标"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 获取类型颜色
        colors = {
            ModernDialog.TYPE_INFO: ("#3b82f6", "rgba(59, 130, 246, 0.2)"),
            ModernDialog.TYPE_SUCCESS: ("#34c759", "rgba(52, 199, 89, 0.2)"),
            ModernDialog.TYPE_WARNING: ("#fbbf24", "rgba(251, 191, 36, 0.2)"),
            ModernDialog.TYPE_ERROR: ("#f87171", "rgba(248, 113, 113, 0.2)"),
            ModernDialog.TYPE_QUESTION: ("#8b5cf6", "rgba(139, 92, 246, 0.2)"),
        }
        fg_color, bg_color = colors.get(self._type, ("#3b82f6", "rgba(59, 130, 246, 0.2)"))

        # 绘制圆角矩形背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(fg_color))
        painter.setOpacity(0.2)
        painter.drawRoundedRect(0, 0, 48, 48, 12, 12)

        # 绘制图标符号
        painter.setOpacity(1.0)
        painter.setPen(QColor(fg_color))

        symbols = {
            ModernDialog.TYPE_INFO: "i",
            ModernDialog.TYPE_SUCCESS: "✓",
            ModernDialog.TYPE_WARNING: "!",
            ModernDialog.TYPE_ERROR: "✕",
            ModernDialog.TYPE_QUESTION: "?",
        }
        symbol = symbols.get(self._type, "i")

        font = QFont("SF Pro", 22)
        font.setWeight(QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, symbol)
