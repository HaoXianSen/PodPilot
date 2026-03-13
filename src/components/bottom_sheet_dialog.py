# -*- coding: utf-8 -*-
"""
Bottom Sheet 风格的 Dialog 基类
让现有的 Dialog 可以快速转换为 Bottom Sheet 风格
"""

from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QGraphicsOpacityEffect,
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QColor

from src.styles import Colors


class BottomSheetDialog(QDialog):
    """
    Bottom Sheet 风格的 Dialog 基类

    使用方法:
    1. 继承此类而非 QDialog
    2. 在 initUI() 中使用 self.content_layout 添加内容
    3. 调用 self.setup_sheet_ui() 完成初始化
    """

    confirmed = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, parent=None, title="", max_height_ratio=0.85):
        super().__init__(parent)
        self._title = title
        self._max_height_ratio = max_height_ratio
        self._is_showing = False
        self._content_built = False

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._init_base_ui()

    def _init_base_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.overlay = QWidget()
        self.overlay.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.4);
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        """)
        self.main_layout.addWidget(self.overlay, 1)

        self.sheet = QFrame()
        self.sheet.setObjectName("bottomSheetDialog")
        self.sheet.setStyleSheet(f"""
            QFrame#bottomSheetDialog {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.BG_GRADIENT_MID},
                    stop:1 {Colors.BG_GRADIENT_END}
                );
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)

        self.sheet_layout = QVBoxLayout(self.sheet)
        self.sheet_layout.setContentsMargins(24, 12, 24, 24)
        self.sheet_layout.setSpacing(12)

        handle = QFrame()
        handle.setFixedSize(36, 4)
        handle.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.3);
                border-radius: 2px;
            }
        """)
        handle_layout = QHBoxLayout()
        handle_layout.addStretch()
        handle_layout.addWidget(handle)
        handle_layout.addStretch()
        self.sheet_layout.addLayout(handle_layout)

        if self._title:
            self.title_label = QLabel(self._title)
            self.title_label.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_PRIMARY};
                    font-size: 18px;
                    font-weight: 600;
                    background: transparent;
                    border: none;
                }}
            """)
            self.title_label.setAlignment(Qt.AlignCenter)
            self.sheet_layout.addWidget(self.title_label)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent; border: none;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)
        self.sheet_layout.addWidget(self.content_widget, 1)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedHeight(44)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 10px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
        """)
        self.cancel_btn.clicked.connect(self.reject)

        self.confirm_btn = QPushButton("确认")
        self.confirm_btn.setFixedHeight(44)
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(102, 126, 234, 0.4);
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid rgba(102, 126, 234, 0.5);
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: rgba(102, 126, 234, 0.5);
            }}
        """)
        self.confirm_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.confirm_btn)
        self.sheet_layout.addLayout(btn_layout)

        self.main_layout.addWidget(self.sheet, 0)

        self.sheet.setMaximumHeight(0)

    def setup_sheet_ui(self):
        """在子类完成内容构建后调用此方法"""
        self._content_built = True

    def exec_(self):
        """重写 exec_ 以添加动画效果"""
        self._slide_in()
        return super().exec_()

    def open(self):
        """重写 open 以添加动画效果"""
        self._slide_in()
        super().open()

    def show(self):
        """重写 show 以添加动画效果"""
        self._slide_in()
        super().show()

    def _slide_in(self):
        if self._is_showing:
            return
        self._is_showing = True

        if self.parentWidget():
            self.setGeometry(self.parentWidget().geometry())

        if self.parentWidget():
            max_height = int(self.parentWidget().height() * self._max_height_ratio)
        else:
            max_height = 700

        sheet_height = min(self.sheet.sizeHint().height(), max_height)

        self.overlay_opacity = QGraphicsOpacityEffect(self.overlay)
        self.overlay.setGraphicsEffect(self.overlay_opacity)
        self.overlay_opacity.setOpacity(0)

        self.anim_overlay = QPropertyAnimation(self.overlay_opacity, b"opacity")
        self.anim_overlay.setDuration(200)
        self.anim_overlay.setStartValue(0)
        self.anim_overlay.setEndValue(1)
        self.anim_overlay.setEasingCurve(QEasingCurve.OutCubic)
        self.anim_overlay.start()

        self.anim_sheet = QPropertyAnimation(self.sheet, b"maximumHeight")
        self.anim_sheet.setDuration(300)
        self.anim_sheet.setStartValue(0)
        self.anim_sheet.setEndValue(sheet_height)
        self.anim_sheet.setEasingCurve(QEasingCurve.OutCubic)
        self.anim_sheet.start()

    def done(self, result):
        """重写 done 以添加退出动画"""
        if not hasattr(self, "_is_closing") or not self._is_closing:
            self._is_closing = True
            self._slide_out()
            # 延迟关闭，等待动画完成
            from PyQt5.QtCore import QTimer

            QTimer.singleShot(250, lambda: super(BottomSheetDialog, self).done(result))
        else:
            super().done(result)

    def reject(self):
        """重写 reject"""
        if not hasattr(self, "_is_closing") or not self._is_closing:
            self._is_closing = True
            self._slide_out()
            # 延迟关闭，等待动画完成
            from PyQt5.QtCore import QTimer

            QTimer.singleShot(250, lambda: super(BottomSheetDialog, self).reject())
        else:
            super().reject()

    def accept(self):
        """重写 accept"""
        if not hasattr(self, "_is_closing") or not self._is_closing:
            self._is_closing = True
            self._slide_out()
            # 延迟关闭，等待动画完成
            from PyQt5.QtCore import QTimer

            QTimer.singleShot(250, lambda: super(BottomSheetDialog, self).accept())
        else:
            super().accept()

    def _slide_out(self):
        if not self._is_showing:
            return

        self.anim_out = QPropertyAnimation(self.sheet, b"maximumHeight")
        self.anim_out.setDuration(200)
        self.anim_out.setStartValue(self.sheet.maximumHeight())
        self.anim_out.setEndValue(0)
        self.anim_out.setEasingCurve(QEasingCurve.InCubic)
        self.anim_out.start()

        if hasattr(self, "overlay_opacity"):
            self.anim_overlay_out = QPropertyAnimation(self.overlay_opacity, b"opacity")
            self.anim_overlay_out.setDuration(200)
            self.anim_overlay_out.setStartValue(1)
            self.anim_overlay_out.setEndValue(0)
            self.anim_overlay_out.setEasingCurve(QEasingCurve.InCubic)
            self.anim_overlay_out.start()

        self._is_showing = False

    def showEvent(self, event):
        super().showEvent(event)
        if self.parentWidget():
            self.setGeometry(self.parentWidget().geometry())
