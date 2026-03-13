# -*- coding: utf-8 -*-
"""
底部弹出 Sheet 组件
类似 iOS ActionSheet 风格
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QGraphicsOpacityEffect,
    QScrollArea,
)
from PyQt5.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QPoint,
    pyqtSignal,
    QSize,
)
from PyQt5.QtGui import QColor

from src.styles import Colors


class BottomSheet(QWidget):
    """底部弹出 Sheet 组件"""

    confirmed = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(
        self, parent=None, title="", message="", confirm_text="确认", cancel_text="取消"
    ):
        super().__init__(parent)
        self._parent = parent
        self._title = title
        self._message = message
        self._confirm_text = confirm_text
        self._cancel_text = cancel_text
        self._is_showing = False

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.overlay = QWidget()
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.4);")
        self.overlay.mousePressEvent = (
            lambda e: self.slide_out() if e.button() == Qt.LeftButton else None
        )
        layout.addWidget(self.overlay, 1)

        self.sheet = QFrame()
        self.sheet.setObjectName("bottomSheet")
        self.sheet.setStyleSheet(f"""
            QFrame#bottomSheet {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.BG_GRADIENT_MID},
                    stop:1 {Colors.BG_GRADIENT_END}
                );
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-bottom: none;
            }}
        """)

        sheet_layout = QVBoxLayout(self.sheet)
        sheet_layout.setContentsMargins(24, 20, 24, 24)
        sheet_layout.setSpacing(16)

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
        sheet_layout.addLayout(handle_layout)

        if self._title:
            title_label = QLabel(self._title)
            title_label.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_PRIMARY};
                    font-size: 18px;
                    font-weight: 600;
                    background: transparent;
                    border: none;
                }}
            """)
            title_label.setAlignment(Qt.AlignCenter)
            sheet_layout.addWidget(title_label)

        if self._message:
            msg_label = QLabel(self._message)
            msg_label.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_SECONDARY};
                    font-size: 14px;
                    background: transparent;
                    border: none;
                }}
            """)
            msg_label.setAlignment(Qt.AlignCenter)
            msg_label.setWordWrap(True)
            sheet_layout.addWidget(msg_label)

        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)

        self.confirm_btn = QPushButton(self._confirm_text)
        self.confirm_btn.setFixedHeight(48)
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(59, 130, 246, 0.3);
                color: {Colors.BRANCH};
                border: 1px solid rgba(59, 130, 246, 0.4);
                border-radius: 12px;
                font-size: 15px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: rgba(59, 130, 246, 0.4);
            }}
            QPushButton:pressed {{
                background-color: rgba(59, 130, 246, 0.35);
            }}
        """)
        self.confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.confirm_btn)

        self.cancel_btn = QPushButton(self._cancel_text)
        self.cancel_btn.setFixedHeight(48)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                font-size: 15px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.12);
            }}
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.cancel_btn)

        sheet_layout.addLayout(btn_layout)

        sheet_widget = QWidget()
        sheet_widget.setStyleSheet("background: transparent;")
        sheet_widget.setLayout(sheet_layout)

        sheet_container = QVBoxLayout()
        sheet_container.setContentsMargins(0, 0, 0, 0)
        sheet_container.addWidget(self.sheet)
        sheet_container.addStretch()

        layout.addLayout(sheet_container, 0)

        self.sheet.setMaximumHeight(0)

    def _on_confirm(self):
        self.slide_out()
        self.confirmed.emit()

    def _on_cancel(self):
        self.slide_out()
        self.cancelled.emit()

    def slide_in(self):
        if self._is_showing:
            return
        self._is_showing = True

        if self._parent:
            self.setGeometry(self._parent.geometry())

        self.show()

        sheet_height = self.sheet.sizeHint().height() + 48

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

    def slide_out(self):
        if not self._is_showing:
            return

        self.anim_out = QPropertyAnimation(self.sheet, b"maximumHeight")
        self.anim_out.setDuration(200)
        self.anim_out.setStartValue(self.sheet.maximumHeight())
        self.anim_out.setEndValue(0)
        self.anim_out.setEasingCurve(QEasingCurve.InCubic)
        self.anim_out.finished.connect(self.hide)
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
        if self._parent:
            self.setGeometry(self._parent.geometry())


class ConfirmSheet(BottomSheet):
    """确认类 Sheet - 只有确认和取消按钮"""

    def __init__(
        self,
        parent=None,
        message="",
        confirm_text="确认",
        cancel_text="取消",
        destructive=False,
    ):
        self._destructive = destructive
        super().__init__(
            parent,
            title="",
            message=message,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
        )

        if destructive:
            self.confirm_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(255, 59, 48, 0.3);
                    color: #ff3b30;
                    border: 1px solid rgba(255, 59, 48, 0.4);
                    border-radius: 12px;
                    font-size: 15px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 59, 48, 0.4);
                }}
            """)


class ContentSheet(QWidget):
    """
    内容型 Bottom Sheet
    支持嵌入复杂内容（如表格、表单等）
    """

    confirmed = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(
        self,
        parent=None,
        title="",
        confirm_text="确认",
        cancel_text="取消",
        max_height_ratio=0.85,
    ):
        super().__init__(parent)
        self._parent = parent
        self._title = title
        self._confirm_text = confirm_text
        self._cancel_text = cancel_text
        self._max_height_ratio = max_height_ratio
        self._is_showing = False
        self._content_widget = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self._init_base_ui()

    def _init_base_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.overlay = QWidget()
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.4);")
        self.overlay.mousePressEvent = (
            lambda e: self.slide_out() if e.button() == Qt.LeftButton else None
        )
        layout.addWidget(self.overlay, 1)

        self.sheet = QFrame()
        self.sheet.setObjectName("contentSheet")
        self.sheet.setStyleSheet(f"""
            QFrame#contentSheet {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.BG_GRADIENT_MID},
                    stop:1 {Colors.BG_GRADIENT_END}
                );
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-bottom: none;
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

        self.content_area = QScrollArea()
        self.content_area.setWidgetResizable(True)
        self.content_area.setFrameShape(QFrame.NoFrame)
        self.content_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content_area.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.2);
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 0.3);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        self.sheet_layout.addWidget(self.content_area, 1)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.cancel_btn = QPushButton(self._cancel_text)
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
        self.cancel_btn.clicked.connect(self._on_cancel)

        self.confirm_btn = QPushButton(self._confirm_text)
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
        self.confirm_btn.clicked.connect(self._on_confirm)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.confirm_btn)
        self.sheet_layout.addLayout(btn_layout)

        layout.addWidget(self.sheet, 0)

        self.sheet.setMaximumHeight(0)

    def set_content(self, widget):
        self._content_widget = widget
        self.content_area.setWidget(widget)

    def set_confirm_style(self, style_type="primary"):
        if style_type == "destructive":
            self.confirm_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(255, 59, 48, 0.3);
                    color: #ff3b30;
                    border: 1px solid rgba(255, 59, 48, 0.4);
                    border-radius: 10px;
                    font-size: 14px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 59, 48, 0.4);
                }}
            """)
        elif style_type == "success":
            self.confirm_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(52, 199, 89, 0.3);
                    color: #34c759;
                    border: 1px solid rgba(52, 199, 89, 0.4);
                    border-radius: 10px;
                    font-size: 14px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: rgba(52, 199, 89, 0.4);
                }}
            """)

    def _on_confirm(self):
        self.slide_out()
        self.confirmed.emit()

    def _on_cancel(self):
        self.slide_out()
        self.cancelled.emit()

    def slide_in(self):
        if self._is_showing:
            return
        self._is_showing = True

        if self._parent:
            self.setGeometry(self._parent.geometry())

        self.show()

        if self._parent:
            max_height = int(self._parent.height() * self._max_height_ratio)
        else:
            max_height = 600
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

    def slide_out(self):
        if not self._is_showing:
            return

        self.anim_out = QPropertyAnimation(self.sheet, b"maximumHeight")
        self.anim_out.setDuration(200)
        self.anim_out.setStartValue(self.sheet.maximumHeight())
        self.anim_out.setEndValue(0)
        self.anim_out.setEasingCurve(QEasingCurve.InCubic)
        self.anim_out.finished.connect(self.hide)
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
        if self._parent:
            self.setGeometry(self._parent.geometry())
