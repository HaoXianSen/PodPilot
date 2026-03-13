from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QPushButton,
    QLineEdit,
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QPainter, QColor, QPen
from src.styles import Colors


class CustomDropdown(QWidget):
    """自定义下拉选择控件"""

    currentTextChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.current_text = ""
        self.is_expanded = False
        self._editable = False
        self.placeholder = ""
        self.enabled = True
        self._is_hovering = False

        self.setFixedHeight(32)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)  # 启用鼠标追踪以检测hover

        # 设置背景属性
        self.setAttribute(Qt.WA_StyledBackground, True)

        # 创建编辑框（用于可编辑模式）
        self._line_edit = QLineEdit(self)
        self._line_edit.setGeometry(10, 6, self.width() - 40, 20)
        self._line_edit.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {Colors.TEXT_PRIMARY};
                font-size: 12px;
                padding: 0;
            }}
        """)
        self._line_edit.hide()
        self._line_edit.textChanged.connect(self._on_edit_text_changed)

        # 创建下拉面板
        self.dropdown_panel = QFrame(self)
        self.dropdown_panel.setObjectName("dropdownPanel")
        self.dropdown_panel.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.dropdown_panel.setAttribute(Qt.WA_TranslucentBackground, False)
        self.dropdown_panel.setAutoFillBackground(True)
        self.dropdown_panel.setStyleSheet(f"""
            QFrame#dropdownPanel {{
                background-color: #1a1a2e;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
            }}
        """)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
                margin: 4px;
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

        # 选项容器
        self.options_container = QWidget()
        self.options_container.setStyleSheet("background: transparent; border: none;")
        self.options_layout = QVBoxLayout(self.options_container)
        self.options_layout.setContentsMargins(4, 4, 4, 4)
        self.options_layout.setSpacing(2)

        scroll.setWidget(self.options_container)

        panel_layout = QVBoxLayout(self.dropdown_panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.addWidget(scroll)

        self.dropdown_panel.hide()

        # 为下拉面板安装事件过滤器，监听其隐藏事件
        self.dropdown_panel.installEventFilter(self)

    def lineEdit(self):
        """返回内部 QLineEdit（兼容 QComboBox 接口）"""
        return self._line_edit

    def _on_edit_text_changed(self, text):
        """编辑框文本变化"""
        self.current_text = text
        self.currentTextChanged.emit(text)

    def addItems(self, items):
        """添加多个选项"""
        self.items = items
        self._rebuild_options()

    def addItem(self, item):
        """添加单个选项"""
        self.items.append(item)
        self._rebuild_options()

    def clear(self):
        """清空所有选项"""
        self.items = []
        self.current_text = ""
        self._rebuild_options()

    def currentText(self):
        """获取当前选中文本"""
        if self._editable:
            return self._line_edit.text()
        return self.current_text

    def setCurrentText(self, text):
        """设置当前选中文本"""
        if text in self.items or text == "":
            self.current_text = text
            if self._editable:
                self._line_edit.setText(text)
            self.update()

    def setEditable(self, editable):
        """设置是否可编辑"""
        self._editable = editable
        if editable:
            # 切换到可编辑模式时，收起下拉面板
            self._collapse()
            self._line_edit.show()
            self._line_edit.setFocus()
        else:
            self._line_edit.hide()
        self.update()

    def setEnabled(self, enabled):
        """设置是否启用"""
        self.enabled = enabled
        self.setCursor(Qt.PointingHandCursor if enabled else Qt.ForbiddenCursor)
        self._line_edit.setEnabled(enabled)
        self.update()

    def resizeEvent(self, event):
        """调整大小事件"""
        super().resizeEvent(event)
        self._line_edit.setGeometry(10, 6, self.width() - 40, 20)

    def _rebuild_options(self):
        """重建选项列表"""
        # 清空现有选项
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 添加新选项
        for item_text in self.items:
            option = self._create_option(item_text)
            self.options_layout.addWidget(option)

        self.options_layout.addStretch()

    def _create_option(self, text):
        """创建单个选项按钮"""
        option_btn = QPushButton(text)
        option_btn.setCursor(Qt.PointingHandCursor)
        option_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                text-align: left;
                color: {Colors.TEXT_PRIMARY};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: rgba(102, 126, 234, 0.3);
            }}
            QPushButton:pressed {{
                background-color: rgba(102, 126, 234, 0.5);
            }}
        """)
        option_btn.clicked.connect(lambda: self._on_option_clicked(text))
        return option_btn

    def _on_option_clicked(self, text):
        """选项点击事件"""
        if self._editable:
            self._line_edit.setText(text)
        else:
            self.current_text = text
            self.currentTextChanged.emit(text)
        self._collapse()
        self.update()

    def _expand(self):
        """展开下拉面板"""
        if not self.enabled or not self.items:
            return

        self.is_expanded = True

        # 计算下拉面板位置和大小
        global_pos = self.mapToGlobal(self.rect().bottomLeft())
        panel_width = self.width()
        panel_height = min(200, len(self.items) * 36 + 8)

        self.dropdown_panel.setGeometry(
            global_pos.x(), global_pos.y() + 4, panel_width, panel_height
        )
        self.dropdown_panel.show()
        self.dropdown_panel.raise_()
        self.update()

    def _collapse(self):
        """收起下拉面板"""
        self.is_expanded = False
        self.dropdown_panel.hide()
        self.update()

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if not self.enabled:
            return

        # 如果是可编辑模式，不展开/收起下拉面板
        if self._editable:
            return

        if self.is_expanded:
            self._collapse()
        else:
            self._expand()

    def enterEvent(self, event):
        """鼠标进入事件"""
        self._is_hovering = True
        self.update()

    def leaveEvent(self, event):
        """鼠标离开事件"""
        self._is_hovering = False
        self.update()

    def paintEvent(self, event):
        """绘制控件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()

        # 背景色
        if not self.enabled:
            bg_color = QColor(255, 255, 255, int(0.05 * 255))
            border_color = QColor(255, 255, 255, int(0.1 * 255))
            text_color = QColor(255, 255, 255, int(0.5 * 255))
        elif self.is_expanded:
            bg_color = QColor(255, 255, 255, int(0.15 * 255))
            border_color = QColor(102, 126, 234, int(0.5 * 255))
            text_color = QColor(Colors.TEXT_PRIMARY)
        elif self._is_hovering:
            bg_color = QColor(255, 255, 255, int(0.15 * 255))
            border_color = QColor(102, 126, 234, int(0.5 * 255))
            text_color = QColor(Colors.TEXT_PRIMARY)
        else:
            bg_color = QColor(255, 255, 255, int(0.1 * 255))
            border_color = QColor(255, 255, 255, int(0.2 * 255))
            text_color = QColor(Colors.TEXT_PRIMARY)

        # 绘制背景
        painter.setBrush(bg_color)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), 6, 6)

        # 如果不是可编辑模式，绘制文本
        if not self._editable:
            painter.setPen(text_color)
            text_rect = rect.adjusted(10, 0, -30, 0)
            display_text = self.current_text if self.current_text else self.placeholder
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, display_text)

        # 绘制箭头（仅在非可编辑模式下）
        if not self._editable:
            arrow_rect = QRect(rect.width() - 25, rect.height() // 2 - 3, 10, 6)
            painter.setBrush(text_color)
            painter.setPen(Qt.NoPen)

            if self.is_expanded:
                # 向上箭头
                points = [
                    arrow_rect.bottomLeft(),
                    arrow_rect.bottomRight(),
                    QRect(arrow_rect.center().x(), arrow_rect.top(), 1, 1).topLeft(),
                ]
            else:
                # 向下箭头
                points = [
                    arrow_rect.topLeft(),
                    arrow_rect.topRight(),
                    QRect(
                        arrow_rect.center().x(), arrow_rect.bottom(), 1, 1
                    ).bottomLeft(),
                ]

            painter.drawPolygon(*points)

    def eventFilter(self, obj, event):
        """事件过滤器：监听下拉面板的隐藏事件"""
        if obj == self.dropdown_panel:
            if event.type() == event.Hide:
                # 下拉面板被隐藏时，更新状态
                if self.is_expanded:
                    self.is_expanded = False
                    self.update()
        return super().eventFilter(obj, event)

    def hideEvent(self, event):
        """隐藏事件"""
        self._collapse()
        super().hideEvent(event)
