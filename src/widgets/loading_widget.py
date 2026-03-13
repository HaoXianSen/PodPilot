from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient
import math


class LoadingWidget(QWidget):
    """现代化的loading动画组件，支持多种样式"""

    # Loading样式枚举
    STYLE_SPINNER = "spinner"  # 旋转圆环（默认）
    STYLE_DOTS = "dots"  # 跳动圆点
    STYLE_PULSE = "pulse"  # 脉冲圆环
    STYLE_BARS = "bars"  # 竖条动画

    def __init__(self, text="加载中...", style=STYLE_SPINNER, parent=None):
        super().__init__(parent)
        self._text = text
        self._style = style
        self._timer = None
        self._is_animating = False
        self._rotation = 0  # 旋转角度
        self._pulse_scale = 1.0  # 脉冲缩放
        self._pulse_direction = 1  # 脉冲方向
        self._dots_offset = [0, 0, 0]  # 圆点偏移
        self._bars_heights = [0, 0, 0, 0, 0]  # 竖条高度

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 设置固定大小的画布区域
        self.setMinimumSize(200, 120)

        # 文字标签
        self._text_label = QLabel(self._text)
        self._text_label.setAlignment(Qt.AlignCenter)
        self._text_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
                font-weight: 500;
                background: transparent;
            }
        """)

        layout.addStretch()
        layout.addWidget(self._text_label)

        self.setLayout(layout)

    def set_text(self, text):
        """设置显示文本"""
        self._text = text
        self._text_label.setText(text)

    def set_style(self, style):
        """设置loading样式"""
        self._style = style
        self.update()

    def start_animation(self):
        """开始动画"""
        if self._is_animating:
            return

        self._is_animating = True
        self._rotation = 0
        self._pulse_scale = 1.0
        self._dots_offset = [0, 0, 0]
        self._bars_heights = [0, 0, 0, 0, 0]

        # 根据不同样式设置不同的刷新频率
        interval = 16 if self._style == self.STYLE_SPINNER else 50

        self._timer = QTimer()
        self._timer.timeout.connect(self._animate)
        self._timer.start(interval)

    def stop_animation(self):
        """停止动画"""
        self._is_animating = False
        if self._timer and self._timer.isActive():
            self._timer.stop()
            self._timer = None
        self.update()

    def is_animating(self):
        """检查是否正在动画"""
        return self._is_animating

    def _animate(self):
        """动画更新"""
        if not self._is_animating:
            return

        if self._style == self.STYLE_SPINNER:
            self._rotation = (self._rotation + 6) % 360

        elif self._style == self.STYLE_PULSE:
            self._pulse_scale += 0.02 * self._pulse_direction
            if self._pulse_scale >= 1.3:
                self._pulse_direction = -1
            elif self._pulse_scale <= 0.8:
                self._pulse_direction = 1

        elif self._style == self.STYLE_DOTS:
            for i in range(3):
                phase = (self._rotation + i * 120) % 360
                self._dots_offset[i] = abs(math.sin(math.radians(phase)) * 10)
            self._rotation = (self._rotation + 10) % 360

        elif self._style == self.STYLE_BARS:
            for i in range(5):
                phase = (self._rotation + i * 72) % 360
                self._bars_heights[i] = abs(math.sin(math.radians(phase)) * 20) + 10
            self._rotation = (self._rotation + 8) % 360

        self.update()

    def paintEvent(self, event):
        """绘制loading动画"""
        super().paintEvent(event)

        if not self._is_animating:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 计算中心位置
        center_x = self.width() // 2
        center_y = (self.height() - 40) // 2  # 留出底部空间给文字

        if self._style == self.STYLE_SPINNER:
            self._draw_spinner(painter, center_x, center_y)
        elif self._style == self.STYLE_PULSE:
            self._draw_pulse(painter, center_x, center_y)
        elif self._style == self.STYLE_DOTS:
            self._draw_dots(painter, center_x, center_y)
        elif self._style == self.STYLE_BARS:
            self._draw_bars(painter, center_x, center_y)

    def _draw_spinner(self, painter, cx, cy):
        """绘制旋转圆环"""
        radius = 20
        pen_width = 3

        # 绘制背景圆环（灰色）
        painter.setPen(
            QPen(QColor(255, 255, 255, 30), pen_width, Qt.SolidLine, Qt.RoundCap)
        )
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPoint(cx, cy), radius, radius)

        # 绘制渐变圆弧（彩色）
        gradient = QLinearGradient(cx - radius, cy, cx + radius, cy)
        gradient.setColorAt(0, QColor(102, 126, 234, 255))  # 主题蓝色
        gradient.setColorAt(0.5, QColor(139, 92, 246, 255))  # 紫色
        gradient.setColorAt(1, QColor(236, 72, 153, 255))  # 粉色

        pen = QPen(QBrush(gradient), pen_width, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)

        # 绘制270度的圆弧，并旋转
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._rotation)
        painter.drawArc(-radius, -radius, radius * 2, radius * 2, 0 * 16, 270 * 16)
        painter.restore()

    def _draw_pulse(self, painter, cx, cy):
        """绘制脉冲圆环"""
        base_radius = 15
        radius = int(base_radius * self._pulse_scale)

        # 外圆环（半透明）
        opacity = int(255 * (1.5 - self._pulse_scale) / 0.5)
        painter.setPen(QPen(QColor(102, 126, 234, opacity), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPoint(cx, cy), radius + 5, radius + 5)

        # 内圆环（实心）
        gradient = QLinearGradient(cx - radius, cy, cx + radius, cy)
        gradient.setColorAt(0, QColor(102, 126, 234, 200))
        gradient.setColorAt(1, QColor(139, 92, 246, 200))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPoint(cx, cy), radius, radius)

    def _draw_dots(self, painter, cx, cy):
        """绘制跳动圆点"""
        dot_radius = 5
        spacing = 18
        colors = [
            QColor(102, 126, 234, 255),
            QColor(139, 92, 246, 255),
            QColor(236, 72, 153, 255),
        ]

        painter.setPen(Qt.NoPen)

        for i in range(3):
            x = cx + (i - 1) * spacing
            y = cy - self._dots_offset[i]
            painter.setBrush(QBrush(colors[i]))
            painter.drawEllipse(QPoint(int(x), int(y)), dot_radius, dot_radius)

    def _draw_bars(self, painter, cx, cy):
        """绘制竖条动画"""
        bar_width = 4
        spacing = 10
        colors = [
            QColor(102, 126, 234, 255),
            QColor(124, 104, 238, 255),
            QColor(139, 92, 246, 255),
            QColor(168, 85, 247, 255),
            QColor(236, 72, 153, 255),
        ]

        painter.setPen(Qt.NoPen)

        for i in range(5):
            x = cx + (i - 2) * (bar_width + spacing)
            height = self._bars_heights[i]
            y = cy - height / 2

            painter.setBrush(QBrush(colors[i]))
            painter.drawRoundedRect(
                int(x - bar_width / 2), int(y), bar_width, int(height), 2, 2
            )


class ModernLoadingDialog(QWidget):
    """现代化的Loading对话框（支持全屏遮罩模式）"""

    def __init__(
        self, text="加载中...", style=LoadingWidget.STYLE_SPINNER, parent=None, fullscreen=False
    ):
        super().__init__(parent)
        self._loading_widget = LoadingWidget(text, style)
        self._fullscreen = fullscreen

        if fullscreen:
            # 全屏遮罩模式 - 只有动画和文字，无卡片背景
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addStretch()
            layout.addWidget(self._loading_widget, 0, Qt.AlignCenter)
            layout.addStretch()
        else:
            # 普通小窗口模式
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setFixedSize(200, 120)

            self.setStyleSheet("""
                QWidget {
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(30, 30, 40, 0.95),
                        stop:1 rgba(20, 20, 30, 0.95)
                    );
                    border-radius: 16px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
            """)

            layout = QVBoxLayout()
            layout.setContentsMargins(20, 20, 20, 20)
            layout.addWidget(self._loading_widget)
            self.setLayout(layout)

    def showEvent(self, event):
        """显示时处理"""
        super().showEvent(event)
        if self._fullscreen and self.parent():
            self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        self._loading_widget.start_animation()

    def hideEvent(self, event):
        """隐藏时停止动画"""
        self._loading_widget.stop_animation()
        super().hideEvent(event)

    def paintEvent(self, event):
        """绘制背景"""
        if self._fullscreen:
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

    def start(self):
        """显示并开始动画"""
        self._loading_widget.start_animation()
        self.show()
        self.raise_()

    def stop(self):
        """停止动画并隐藏"""
        self._loading_widget.stop_animation()
        self.hide()

    def set_text(self, text):
        """设置文字"""
        self._loading_widget.set_text(text)

    def set_style(self, style):
        """设置样式"""
        self._loading_widget.set_style(style)

    def mousePressEvent(self, event):
        """阻止鼠标事件穿透（全屏模式）"""
        if self._fullscreen:
            event.accept()
        else:
            super().mousePressEvent(event)

    def keyPressEvent(self, event):
        """阻止键盘事件（全屏模式）"""
        if self._fullscreen:
            event.accept()
        else:
            super().keyPressEvent(event)
