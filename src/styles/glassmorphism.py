# -*- coding: utf-8 -*-
"""
Glassmorphism 样式系统
PodPilot UI 现代化样式定义
"""


class Colors:
    """Glassmorphism 配色系统"""

    # 背景 - 深色专业风
    BG_GRADIENT_START = "#1a1a2e"
    BG_GRADIENT_MID = "#16213e"
    BG_GRADIENT_END = "#0f3460"

    # 表面 - 深色玻璃效果，适配深色主题
    SURFACE = "rgba(255, 255, 255, 0.08)"
    SURFACE_BORDER = "rgba(255, 255, 255, 0.12)"
    SURFACE_HOVER = "rgba(255, 255, 255, 0.15)"

    # 文字
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "rgba(255, 255, 255, 0.8)"

    TEXT_MUTED = "rgba(255, 255, 255, 0.6)"

    TEXT_LABEL = "rgba(255, 255, 255, 0.7)"

    # 状态标签
    TAG = "#34c759"

    BRANCH = "#3b82f6"

    DEV = "#f97316"

    MR = "#5856d6"

    GIT = "#8b5cf6"

    # 按钮
    BTN_PRIMARY = "rgba(255, 255, 255, 0.25)"

    BTN_PRIMARY_HOVER = "rgba(255, 255, 255, 0.35)"

    BTN_PRIMARY_PRESSED = "rgba(255, 255, 255, 0.2)"

    BTN_SECONDARY = "rgba(255, 255, 255, 0.1)"

    BTN_SECONDARY_BORDER = "rgba(255, 255, 255, 0.2)"


class Styles:
    """样式模板"""

    MAIN_WINDOW = f"""
        QMainWindow {{
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.BG_GRADIENT_START},
                stop:0.5 {Colors.BG_GRADIENT_MID},
                stop:1 {Colors.BG_GRADIENT_END}
            );
        }}
        QWidget {{
            color: {Colors.TEXT_PRIMARY};
            font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
        }}
    """

    CARD = f"""
        QFrame {{
            background-color: {Colors.SURFACE};
            border: 1px solid {Colors.SURFACE_BORDER};
            border-radius: 12px;
        }}
    """

    LIST_WIDGET = f"""
        QListWidget {{
            background-color: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 12px;
            padding: 8px;
            outline: none;
        }}
        QListWidget::item {{
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 12px 14px;
            margin: 2px 4px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QListWidget::item:hover:!selected {{
            background-color: rgba(255, 255, 255, 0.15);
        }}
        QListWidget::item:selected {{
            background-color: rgba(255, 255, 255, 0.25);
        }}
    """

    # 通用按钮样式 - 适用于所有 QPushButton
    BUTTON = f"""
        QPushButton {{
            background-color: rgba(255, 255, 255, 0.15);
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 12px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: rgba(255, 255, 255, 0.25);
        }}
        QPushButton:pressed {{
            background-color: rgba(255, 255, 255, 0.2);
        }}
        QPushButton:disabled {{
            background-color: rgba(255, 255, 255, 0.05);
            color: rgba(255, 255, 255, 0.3);
        }}
    """

    # 分段控制器样式
    SEGMENT_FIRST = f"""
        QPushButton {{
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-top-left-radius: 8px;
            border-bottom-left-radius: 8px;
            border-top-right-radius: 0;
            border-bottom-right-radius: 0;
            padding: 6px 14px;
            font-size: 12px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QPushButton:hover {{
            background-color: rgba(255, 255, 255, 0.15);
        }}
        QPushButton:checked {{
            background-color: rgba(59, 130, 246, 0.4);
            border-color: rgba(59, 130, 246, 0.6);
            color: white;
        }}
    """

    SEGMENT_MIDDLE = f"""
        QPushButton {{
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-left: none;
            border-radius: 0;
            padding: 6px 14px;
            font-size: 12px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QPushButton:hover {{
            background-color: rgba(255, 255, 255, 0.15);
        }}
        QPushButton:checked {{
            background-color: rgba(59, 130, 246, 0.4);
            border-color: rgba(59, 130, 246, 0.6);
            color: white;
        }}
    """

    SEGMENT_LAST = f"""
        QPushButton {{
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-left: none;
            border-top-left-radius: 0;
            border-bottom-left-radius: 0;
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
            padding: 6px 14px;
            font-size: 12px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QPushButton:hover {{
            background-color: rgba(255, 255, 255, 0.15);
        }}
        QPushButton:checked {{
            background-color: rgba(59, 130, 246, 0.4);
            border-color: rgba(59, 130, 246, 0.6);
            color: white;
        }}
    """

    # 标签样式
    LABEL_SECTION = f"""
        QLabel {{
            color: {Colors.TEXT_LABEL};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            background: transparent;
            border: none;
            padding: 4px 0;
        }}
    """

    LABEL_TITLE = f"""
        QLabel {{
            color: {Colors.TEXT_PRIMARY};
            font-size: 16px;
            font-weight: 700;
            background: transparent;
            border: none;
        }}
    """

    # 输入框
    LINE_EDIT = f"""
        QLineEdit {{
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 8px 12px;
            color: {Colors.TEXT_PRIMARY};
            font-size: 13px;
        }}
        QLineEdit:hover {{
            background-color: rgba(255, 255, 255, 0.15);
        }}
        QLineEdit:focus {{
            border: 2px solid rgba(102, 126, 234, 0.6);
            background-color: rgba(255, 255, 255, 0.12);
        }}
        QLineEdit::placeholder {{
            color: rgba(255, 255, 255, 0.4);
        }}
    """

    # 文本编辑框
    TEXT_EDIT = f"""
        QTextEdit {{
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 8px;
            color: {Colors.TEXT_PRIMARY};
            font-size: 12px;
        }}
    """

    # 滚动条
    SCROLL_BAR = """
        QScrollBar:vertical {
            border: none;
            background: transparent;
            width: 6px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: rgba(255, 255, 255, 0.2);
            min-height: 20px;
            border-radius: 3px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
    """

    # 状态栏
    STATUS_BAR = f"""
        QStatusBar {{
            background-color: rgba(0, 0, 0, 0.2);
            color: {Colors.TEXT_SECONDARY};
            font-size: 11px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }}
    """

    # 分隔符 - 使用 objectName 选择器，避免影响其他 QFrame 子类
    SEPARATOR = """
        QFrame[separator="true"] {
            background-color: rgba(255, 255, 255, 0.2);
            border: none;
            max-height: 1px;
        }
    """

    # QMessageBox 弹窗样式 - 使用与主界面相同的渐变背景
    MESSAGE_BOX = f"""
        QMessageBox {{
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.BG_GRADIENT_START},
                stop:0.5 {Colors.BG_GRADIENT_MID},
                stop:1 {Colors.BG_GRADIENT_END}
            );
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
        }}
        QMessageBox QLabel {{
            color: {Colors.TEXT_PRIMARY};
            font-size: 14px;
            padding: 16px;
            background: transparent;
        }}
        QMessageBox QPushButton {{
            background-color: rgba(255, 255, 255, 0.15);
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 8px;
            padding: 8px 20px;
            min-width: 80px;
            min-height: 32px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: rgba(255, 255, 255, 0.25);
        }}
        QMessageBox QPushButton:pressed {{
            background-color: rgba(255, 255, 255, 0.2);
        }}
    """

    # QDialog 透明标题栏辅助方法
    @staticmethod
    def setup_transparent_titlebar(dialog):
        """为 QDialog 设置透明标题栏（macOS）"""
        try:
            from AppKit import (
                NSWindow,
                NSFullSizeContentViewWindowMask,
                NSWindowTitleHidden,
            )
            import objc

            ns_view = dialog.winId()
            ns_window = objc.objc_object(c_void_p=ns_view).__int__()
            ns_window = NSWindow.alloc().initWithWindowRef_(ns_window)

            style_mask = ns_window.styleMask()
            ns_window.setStyleMask_(style_mask | NSFullSizeContentViewWindowMask)
            ns_window.setTitlebarAppearsTransparent_(True)
            ns_window.setTitleVisibility_(NSWindowTitleHidden)
            return True
        except Exception:
            return False


class GlassmorphismStyle:
    """样式管理器"""

    @staticmethod
    def get_full_stylesheet():
        """获取完整样式表"""
        return "\n".join(
            [
                Styles.MAIN_WINDOW,
                Styles.LIST_WIDGET,
                Styles.BUTTON,
                Styles.LABEL_SECTION,
                Styles.LABEL_TITLE,
                Styles.LINE_EDIT,
                Styles.TEXT_EDIT,
                Styles.SCROLL_BAR,
                Styles.STATUS_BAR,
                Styles.MESSAGE_BOX,
            ]
        )

    @staticmethod
    def get_tag_style(tag_type: str) -> str:
        """获取状态标签样式"""
        colors = {
            "tag": Colors.TAG,
            "branch": Colors.BRANCH,
            "dev": Colors.DEV,
            "mr": Colors.MR,
            "git": Colors.GIT,
        }
        color = colors.get(tag_type.lower(), Colors.TEXT_MUTED)
        return f"""
            background-color: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.3);
            color: {color};
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
        """

    @staticmethod
    def setup_transparent_titlebar(widget):
        """为窗口/对话框设置透明标题栏（macOS）"""
        try:
            from AppKit import (
                NSWindow,
                NSFullSizeContentViewWindowMask,
                NSWindowTitleHidden,
            )
            import objc

            ns_view = widget.winId()
            ns_window_ptr = objc.objc_object(c_void_p=ns_view).__int__()
            ns_window = NSWindow.alloc().initWithWindowRef_(ns_window_ptr)

            style_mask = ns_window.styleMask()
            ns_window.setStyleMask_(style_mask | NSFullSizeContentViewWindowMask)
            ns_window.setTitlebarAppearsTransparent_(True)
            ns_window.setTitleVisibility_(NSWindowTitleHidden)
            return True
        except Exception as e:
            print(f"透明标题栏设置失败: {e}")
            return False
