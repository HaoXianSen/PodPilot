# -*- coding: utf-8 -*-
"""
清理缓存对话框 - Bottom Sheet 风格
"""

from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QCheckBox,
    QFrame,
    QWidget,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtSvg import QSvgWidget
from src.styles import Colors
from src.components.bottom_sheet_dialog import BottomSheetDialog
from src.widgets.custom_checkbox import CustomCheckBox
import os


class CleanCacheDialog(BottomSheetDialog):
    """清理Pod缓存对话框 - Bottom Sheet 风格"""

    def __init__(self, parent=None):
        self.clean_options = {
            "pods": True,
            "lock": True,
            "cache": True,
        }

        # 增加最大高度比例，让内容有足够空间
        super().__init__(parent, title="清理Pod缓存", max_height_ratio=0.65)

        self._build_content()
        self.setup_sheet_ui()

    def _build_content(self):
        """构建内容区域"""
        # 描述
        self.desc_label = QLabel("选择要清理的内容")
        self.desc_label.setStyleSheet(
            "color: white; font-size: 13px; background: transparent;"
        )
        self.content_layout.addWidget(self.desc_label)

        # 警告提示（黄色文字 + 淡黄色背景）
        warning_container = QFrame()
        warning_container.setObjectName("warningContainer")
        warning_container.setFixedHeight(36)
        warning_container.setStyleSheet("""
            QFrame#warningContainer {
                background-color: #3d3520;
                border: 1px solid #fbbf24;
                border-radius: 6px;
            }
        """)
        warning_layout = QHBoxLayout(warning_container)
        warning_layout.setContentsMargins(12, 0, 12, 0)
        warning_layout.setSpacing(8)

        # 使用 SVG 警告图标
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        icon_path = os.path.join(base_dir, "resources", "icons", "warning.svg")
        warning_icon = QSvgWidget(icon_path)
        warning_icon.setFixedSize(18, 18)
        warning_layout.addWidget(warning_icon)

        # 警告文字
        self.warning_text = QLabel("此操作不可逆，请谨慎选择")
        self.warning_text.setStyleSheet("color: #fbbf24; font-size: 13px;")
        warning_layout.addWidget(self.warning_text)

        warning_layout.addStretch()
        self.content_layout.addWidget(warning_container)

        # 选项区域
        options_container = QFrame()
        options_container.setObjectName("optionsContainer")
        options_container.setStyleSheet(f"""
            QFrame#optionsContainer {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }}
        """)

        options_layout = QVBoxLayout(options_container)
        options_layout.setContentsMargins(16, 16, 16, 16)
        options_layout.setSpacing(16)

        # 选项1：删除 Pods 目录
        pods_option = QWidget()
        pods_option.setMinimumHeight(60)
        pods_option_layout = QVBoxLayout(pods_option)
        pods_option_layout.setContentsMargins(0, 0, 0, 0)
        pods_option_layout.setSpacing(6)

        self.clean_pods_cb = CustomCheckBox("删除 Pods 目录")
        self.clean_pods_cb.setChecked(True)
        self.clean_pods_cb.stateChanged.connect(
            lambda state: self._update_option("pods", state == Qt.Checked)
        )
        pods_option_layout.addWidget(self.clean_pods_cb)

        pods_desc = QLabel("移除所有已安装的 Pod 库文件")
        pods_desc.setStyleSheet(
            "color: rgba(255, 255, 255, 0.6); font-size: 11px; background: transparent; margin-left: 30px;"
        )
        pods_option_layout.addWidget(pods_desc)

        options_layout.addWidget(pods_option)

        # 选项2：删除 Podfile.lock
        lock_option = QWidget()
        lock_option.setMinimumHeight(60)
        lock_option_layout = QVBoxLayout(lock_option)
        lock_option_layout.setContentsMargins(0, 0, 0, 0)
        lock_option_layout.setSpacing(6)

        self.clean_lock_cb = CustomCheckBox("删除 Podfile.lock 文件")
        self.clean_lock_cb.setChecked(True)
        self.clean_lock_cb.stateChanged.connect(
            lambda state: self._update_option("lock", state == Qt.Checked)
        )
        lock_option_layout.addWidget(self.clean_lock_cb)

        lock_desc = QLabel("移除依赖版本锁定文件")
        lock_desc.setStyleSheet(
            "color: rgba(255, 255, 255, 0.6); font-size: 11px; background: transparent; margin-left: 30px;"
        )
        lock_option_layout.addWidget(lock_desc)

        options_layout.addWidget(lock_option)

        # 选项3：清理 CocoaPods 缓存
        cache_option = QWidget()
        cache_option.setMinimumHeight(60)
        cache_option_layout = QVBoxLayout(cache_option)
        cache_option_layout.setContentsMargins(0, 0, 0, 0)
        cache_option_layout.setSpacing(6)

        self.clean_cache_cb = CustomCheckBox("清理 CocoaPods 缓存")
        self.clean_cache_cb.setChecked(True)
        self.clean_cache_cb.stateChanged.connect(
            lambda state: self._update_option("cache", state == Qt.Checked)
        )
        cache_option_layout.addWidget(self.clean_cache_cb)

        cache_desc = QLabel("清除 CocoaPods 全局缓存目录")
        cache_desc.setStyleSheet(
            "color: rgba(255, 255, 255, 0.6); font-size: 11px; background: transparent; margin-left: 30px;"
        )
        cache_option_layout.addWidget(cache_desc)

        options_layout.addWidget(cache_option)

        self.content_layout.addWidget(options_container)

        # 添加弹性空间，防止内容被压缩
        self.content_layout.addStretch()

        # 修改按钮文本和样式
        self.confirm_btn.setText("开始清理")
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(248, 113, 113, 0.4);
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid rgba(248, 113, 113, 0.6);
                border-radius: 8px;
                padding: 10px 28px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: rgba(248, 113, 113, 0.55);
                border-color: rgba(248, 113, 113, 0.8);
            }}
            QPushButton:pressed {{
                background-color: rgba(248, 113, 113, 0.35);
            }}
        """)

        self.confirm_btn.clicked.disconnect()
        self.confirm_btn.clicked.connect(self.accept)

    def _update_option(self, option, checked):
        """更新清理选项"""
        self.clean_options[option] = checked

    def get_options(self):
        """获取清理选项"""
        return self.clean_options
