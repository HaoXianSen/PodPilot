from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt, QTimer


class LoadingWidget(QWidget):
    """可复用的loading动画组件"""

    def __init__(self, text="加载中...", parent=None):
        super().__init__(parent)
        self._current_dot = 0
        self._dots = []
        self._timer = None
        self._is_animating = False

        self.init_ui(text)

    def init_ui(self, text):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 创建三个圆点动画
        dots_widget = QWidget()
        dots_layout = QHBoxLayout()
        dots_layout.setSpacing(8)
        dots_layout.setContentsMargins(0, 0, 0, 0)

        self._dots = []
        for i in range(3):
            dot = QLabel()
            dot.setFixedSize(8, 8)  # 稍微小一点的圆点
            dot.setStyleSheet("""
                QLabel {
                    background-color: #e0e0e0;
                    border-radius: 50%;
                }
            """)
            dots_layout.addWidget(dot)
            self._dots.append(dot)

        dots_widget.setLayout(dots_layout)
        layout.addWidget(dots_widget, 0, Qt.AlignCenter)

        # 添加文字标签
        self._text_label = QLabel(text)
        self._text_label.setAlignment(Qt.AlignCenter)
        self._text_label.setStyleSheet("""
            QLabel {
                color: #1d1d1f;
                font-size: 13px;
                font-weight: 500;
                background: transparent;
            }
        """)
        layout.addWidget(self._text_label)

        self.setLayout(layout)

    def set_text(self, text):
        """设置显示文本"""
        self._text_label.setText(text)

    def start_animation(self):
        """开始动画"""
        if self._is_animating:
            return

        self._is_animating = True
        self._current_dot = 0

        def animate_dots():
            if not self._is_animating:
                return

            # 重置所有圆点
            for i, dot in enumerate(self._dots):
                if i == self._current_dot:
                    dot.setStyleSheet("""
                        QLabel {
                            background-color: #007aff;
                            border-radius: 50%;
                        }
                    """)
                else:
                    dot.setStyleSheet("""
                        QLabel {
                            background-color: #e0e0e0;
                            border-radius: 50%;
                        }
                    """)
            self._current_dot = (self._current_dot + 1) % 3

        # 立即执行一次
        animate_dots()

        # 启动定时器
        self._timer = QTimer()
        self._timer.timeout.connect(animate_dots)
        self._timer.start(200)

    def stop_animation(self):
        """停止动画"""
        self._is_animating = False
        if self._timer and self._timer.isActive():
            self._timer.stop()
            self._timer = None

        # 重置所有圆点为灰色
        for dot in self._dots:
            dot.setStyleSheet("""
                QLabel {
                    background-color: #e0e0e0;
                    border-radius: 50%;
                }
            """)

    def is_animating(self):
        """检查是否正在动画"""
        return self._is_animating
