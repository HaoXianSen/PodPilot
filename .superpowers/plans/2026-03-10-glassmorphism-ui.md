# PodPilot UI 现代化重构实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 PodPilot 主界面从传统 PyQt5 样式升级为 Glassmorphism 风格

**Architecture:** 创建独立的样式模块和图标模块，通过渐变背景 + 半透明卡片实现毛玻璃效果，替换 emoji 为 SVG 矢量图标

**Tech Stack:** PyQt5, Python 3.6+

---

## 文件结构

```
src/
├── resources/
│   ├── __init__.py           # 新建
│   └── icons.py              # 新建: SVG 图标模块
├── styles/
│   ├── __init__.py           # 新建
│   └── glassmorphism.py      # 新建: 样式定义
└── views/
    ├── main_window.py        # 修改: 主窗口样式重构
    └── dialogs/
        └── personal_center_drawer.py  # 修改: 样式更新
```

---

## Chunk 1: 基础设施 - 样式模块

### Task 1.1: 创建 styles 包初始化文件

**Files:**
- Create: `src/styles/__init__.py`

- [ ] **Step 1: 创建 styles 目录和 __init__.py**

```python
# src/styles/__init__.py
from .glassmorphism import Colors, Styles, GlassmorphismStyle

__all__ = ["Colors", "Styles", "GlassmorphismStyle"]
```

- [ ] **Step 2: 提交**

```bash
git add src/styles/__init__.py
git commit -m "feat: add styles package init"
```

### Task 1.2: 创建 Glassmorphism 样式定义

**Files:**
- Create: `src/styles/glassmorphism.py`

- [ ] **Step 1: 创建配色系统**

```python
# src/styles/glassmorphism.py
# -*- coding: utf-8 -*-
"""
Glassmorphism 样式系统
PodPilot UI 现代化样式定义
"""


class Colors:
    """Glassmorphism 配色系统"""

    # 背景
    BG_GRADIENT_START = "#667eea"
    BG_GRADIENT_END = "#764ba2"

    # 表面
    SURFACE = "rgba(255, 255, 255, 0.15)"
    SURFACE_BORDER = "rgba(255, 255, 255, 0.2)"
    SURFACE_HOVER = "rgba(255, 255, 255, 0.25)"

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
```

- [ ] **Step 2: 添加样式模板类**

```python
class Styles:
    """样式模板"""

    MAIN_WINDOW = f"""
        QMainWindow {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 {Colors.BG_GRADIENT_START},
                stop:1 {Colors.BG_GRADIENT_END}
            );
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
            background-color: {Colors.SURFACE};
            border: 1px solid {Colors.SURFACE_BORDER};
            border-radius: 12px;
            padding: 8px;
            outline: none;
        }}
        QListWidget::item {{
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 10px 14px;
            margin: 2px 4px;
            color: {Colors.TEXT_PRIMARY};
        }}
        QListWidget::item:hover:!selected {{
            background-color: rgba(255, 255, 255, 0.2);
        }}
        QListWidget::item:selected {{
            background-color: {Colors.SURFACE_HOVER};
            border: 1px solid {Colors.SURFACE_BORDER};
        }}
    """

    BUTTON_PRIMARY = f"""
        QPushButton {{
            background-color: {Colors.BTN_PRIMARY};
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid {Colors.BTN_SECONDARY_BORDER};
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {Colors.BTN_PRIMARY_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {Colors.BTN_PRIMARY_PRESSED};
        }}
        QPushButton:disabled {{
            background-color: rgba(255, 255, 255, 0.05);
            color: rgba(255, 255, 255, 0.3);
        }}
    """

    BUTTON_SECONDARY = f"""
        QPushButton {{
            background-color: {Colors.BTN_SECONDARY};
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid {Colors.BTN_SECONDARY_BORDER};
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: rgba(255, 255, 255, 0.15);
        }}
        QPushButton:pressed {{
            background-color: rgba(255, 255, 255, 0.08);
        }}
        QPushButton:disabled {{
            background-color: rgba(255, 255, 255, 0.02);
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
            text-transform: uppercase;
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

    # 分隔符
    SEPARATOR = """
        QFrame[frameRole="separator"] {
            background-color: rgba(255, 255, 255, 0.2);
            border: none;
            max-height: 1px;
        }
    """
```

- [ ] **Step 3: 添加辅助方法**

```python
def get_status_tag_style(tag_type: str) -> str:
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


def get_full_stylesheet() -> str:
    """获取完整样式表"""
    return "\n".join([
        Styles.MAIN_WINDOW,
        Styles.LIST_WIDGET,
        Styles.BUTTON_PRIMARY,
        Styles.BUTTON_SECONDARY,
        Styles.LABEL_SECTION,
        Styles.LABEL_TITLE,
        Styles.LINE_EDIT,
        Styles.TEXT_EDIT,
        Styles.SCROLL_BAR,
        Styles.STATUS_BAR,
        Styles.SEPARATOR,
    ])
```

- [ ] **Step 4: 提交**

```bash
git add src/styles/glassmorphism.py
git commit -m "feat: add glassmorphism style system"
```

---

## Chunk 2: 基础设施 - 图标模块

### Task 2.1: 创建 resources 包初始化文件

**Files:**
- Create: `src/resources/__init__.py`

- [ ] **Step 1: 创建 __init__.py**

```python
# src/resources/__init__.py
from .icons import IconManager, get_icon, get_pixmap

__all__ = ["IconManager", "get_icon", "get_pixmap"]
```

- [ ] **Step 2: 提交**

```bash
git add src/resources/__init__.py
git commit -m "feat: add resources package init"
```

### Task 2.2: 创建 SVG 图标模块

**Files:**
- Create: `src/resources/icons.py`

- [ ] **Step 1: 创建图标路径定义**

```python
# src/resources/icons.py
# -*- coding: utf-8 -*-
"""
SVG 图标资源模块
使用 Lucide 风格的矢量图标
"""

from PyQt5.QtGui import QIcon, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import Qt, QSize
import io


# Lucide 风格 SVG 图标路径
SVG_PATHS = {
    "tag": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2H2v10l9.29 9.29c.94.94 2.48.94 3.42 0l6.58-6.58c.94-.94.94-2.48 0-3.42L12 2Z"/><path d="M7 7h.01"/></svg>""",

    "git-branch": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="6" x2="6" y1="3" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>""",

    "git-merge": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/></svg>""",

    "clipboard-list": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/></svg>""",

    "plus": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>""",

    "minus": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/></svg>""",

    "user": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>""",

    "folder": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"/></svg>""",

    "package": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>""",

    "search": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>""",

    "settings": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>""",

    "x": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>""",

    "chevron-right": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>""",

    "eye": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>""",

    "eye-off": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" x2="22" y1="2" y2="22"/></svg>""",

    "code": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>""",

    "terminal": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/></svg>""",

    "refresh-cw": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>""",
}
```

- [ ] **Step 2: 添加图标获取函数**

```python
def get_icon(icon_name: str, size: int = 16, color: str = "#FFFFFF") -> QIcon:
    """
    获取 SVG 图标

    Args:
        icon_name: 图标名称 (tag, git-branch, git-merge 等)
        size: 图标大小 (像素)
        color: 图标颜色 (十六进制)

    Returns:
        QIcon 对象
    """
    if icon_name not in SVG_PATHS:
        return QIcon()

    svg_content = SVG_PATHS[icon_name].replace("currentColor", color)

    renderer = QSvgRenderer()
    renderer.load(io.BytesIO(svg_content.encode('utf-8')).read())

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


def get_pixmap(icon_name: str, size: int = 16, color: str = "#FFFFFF") -> QPixmap:
    """
    获取 SVG QPixmap

    Args:
        icon_name: 图标名称
        size: 图标大小
        color: 图标颜色

    Returns:
        QPixmap 对象
    """
    if icon_name not in SVG_PATHS:
        return QPixmap()

    svg_content = SVG_PATHS[icon_name].replace("currentColor", color)
    renderer = QSvgRenderer()
    renderer.load(io.BytesIO(svg_content.encode('utf-8')).read())

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()

    return pixmap


class IconManager:
    """图标管理器 - 提供缓存功能"""

    _instance = None
    _cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_icon(cls, icon_name: str, size: int = 16, color: str = "#FFFFFF") -> QIcon:
        """获取图标（带缓存）"""
        cache_key = f"{icon_name}_{size}_{color}"
        if cache_key not in cls._cache:
            cls._cache[cache_key] = get_icon(icon_name, size, color)
        return cls._cache[cache_key]

    @classmethod
    def get_pixmap(cls, icon_name: str, size: int = 16, color: str = "#FFFFFF") -> QPixmap:
        """获取 QPixmap（带缓存）"""
        cache_key = f"pixmap_{icon_name}_{size}_{color}"
        if cache_key not in cls._cache:
            cls._cache[cache_key] = get_pixmap(icon_name, size, color)
        return cls._cache[cache_key]

    @classmethod
    def clear_cache(cls):
        """清除缓存"""
        cls._cache.clear()
```

- [ ] **Step 3: 提交**

```bash
git add src/resources/icons.py
git commit -m "feat: add SVG icon module with Lucide style icons"
```

---

## Chunk 3: 主窗口样式重构

### Task 3.1: 更新主窗口样式系统

**Files:**
- Modify: `src/views/main_window.py`

- [ ] **Step 1: 添加样式模块导入**

在文件顶部导入区域添加:

```python
# 在现有导入后添加
from src.styles import Colors, Styles, get_full_stylesheet
from src.resources.icons import IconManager
```

- [ ] **Step 2: 重构 set_modern_style 方法**

找到 `set_modern_style` 方法（约第668行），替换为:

```python
def set_modern_style(self):
    """设置 Glassmorphism UI 样式"""
    self.setStyleSheet(get_full_stylesheet())
```

- [ ] **Step 3: 提交**

```bash
git add src/views/main_window.py
git commit -m "refactor: update main window to use glassmorphism style"
```

### Task 3.2: 替换按钮 emoji 为 SVG 图标

**Files:**
- Modify: `src/views/main_window.py`

- [ ] **Step 1: 更新一键 Tag 按钮**

找到 `self.one_click_tag_btn` 的创建代码，修改为:

```python
self.one_click_tag_btn = QPushButton(" Tag", left_widget)
self.one_click_tag_btn.setIcon(IconManager.get_icon("tag", 14, "#FFFFFF"))
self.one_click_tag_btn.setToolTip(
    "自动筛选branch/git引用的Pod，批量切换到Tag引用"
)
self.one_click_tag_btn.setFixedSize(one_click_btn_w, left_btn_h)
self.one_click_tag_btn.setStyleSheet(Styles.BUTTON_SECONDARY)
```

- [ ] **Step 2: 更新一键 Branch 按钮**

```python
self.one_click_branch_btn = QPushButton(" Branch", left_widget)
self.one_click_branch_btn.setIcon(IconManager.get_icon("git-branch", 14, "#FFFFFF"))
self.one_click_branch_btn.setToolTip(
    "自动筛选tag引用的Pod，批量切换到Branch模式"
)
self.one_click_branch_btn.setFixedSize(one_click_btn_w, left_btn_h)
self.one_click_branch_btn.setStyleSheet(Styles.BUTTON_SECONDARY)
```

- [ ] **Step 3: 更新一键 MR 按钮**

```python
self.one_click_mr_btn = QPushButton(" MR", left_widget)
self.one_click_mr_btn.setIcon(IconManager.get_icon("git-merge", 14, "#FFFFFF"))
self.one_click_mr_btn.setToolTip(
    "自动筛选branch/git引用的Pod，批量创建Merge Request"
)
self.one_click_mr_btn.setFixedSize(one_click_btn_w, left_btn_h)
self.one_click_mr_btn.setStyleSheet(Styles.BUTTON_SECONDARY)
```

- [ ] **Step 4: 更新查看工程 MR 按钮**

```python
self.view_project_mr_btn = QPushButton(" 工程MR", left_widget)
self.view_project_mr_btn.setIcon(IconManager.get_icon("clipboard-list", 14, "#FFFFFF"))
self.view_project_mr_btn.setToolTip("查看当前工程及其关联Pod的待合并MR")
self.view_project_mr_btn.setFixedHeight(left_btn_h)
self.view_project_mr_btn.setStyleSheet(Styles.BUTTON_SECONDARY)
```

- [ ] **Step 5: 更新添加/移除项目按钮**

```python
self.add_btn = QPushButton(" 项目")
self.add_btn.setIcon(IconManager.get_icon("plus", 14, "#FFFFFF"))
self.add_btn.setFixedHeight(left_btn_h)
self.add_btn.setStyleSheet(Styles.BUTTON_SECONDARY)

self.remove_btn = QPushButton(" 项目")
self.remove_btn.setIcon(IconManager.get_icon("minus", 14, "#FFFFFF"))
self.remove_btn.setFixedHeight(left_btn_h)
self.remove_btn.setStyleSheet(Styles.BUTTON_SECONDARY)
```

- [ ] **Step 6: 提交**

```bash
git add src/views/main_window.py
git commit -m "refactor: replace emoji icons with SVG icons in main window"
```

### Task 3.3: 更新分段控制器样式

**Files:**
- Modify: `src/views/main_window.py`

- [ ] **Step 1: 替换分段控制器样式定义**

找到 `segment_first_style`, `segment_middle_style`, `segment_last_style` 的定义，替换为使用 `Styles.SEGMENT_FIRST` 等。

- [ ] **Step 2: 提交**

```bash
git add src/views/main_window.py
git commit -m "refactor: use glassmorphism segment control styles"
```

---

## Chunk 4: 个人中心抽屉样式更新

### Task 4.1: 更新个人中心抽屉样式

**Files:**
- Modify: `src/views/dialogs/personal_center_drawer.py`

- [ ] **Step 1: 添加样式模块导入**

```python
from src.styles import Colors, Styles
from src.resources.icons import IconManager
```

- [ ] **Step 2: 更新容器样式**

找到 `container.setStyleSheet` 调用，替换为:

```python
container.setStyleSheet(Styles.CARD)
```

- [ ] **Step 3: 更新标题栏样式**

使用 `Styles.LABEL_TITLE` 和 `Styles.BUTTON_SECONDARY`

- [ ] **Step 4: 更新卡片样式**

为头像卡片、Token卡片、MR卡片应用 `Styles.CARD`

- [ ] **Step 5: 更新关闭按钮**

```python
close_btn.setIcon(IconManager.get_icon("x", 12, Colors.TEXT_MUTED))
```

- [ ] **Step 6: 提交**

```bash
git add src/views/dialogs/personal_center_drawer.py
git commit -m "refactor: update personal center drawer with glassmorphism style"
```

---

## Chunk 5: 测试和清理

### Task 5.1: 功能测试

- [ ] **Step 1: 运行应用验证基础功能**

```bash
cd /Users/haoyh02/Desktop/iPM
python3 main.py
```

Expected: 应用启动，显示 Glassmorphism 风格界面

- [ ] **Step 2: 验证按钮交互**

检查所有按钮是否:
- 显示 SVG 图标
- 悬停有反馈效果
- 点击功能正常

- [ ] **Step 3: 验证列表显示**

检查项目列表和 Pod 列表是否:
- 显示 Glassmorphism 风格
- 选中状态正确
- 滚动条样式正确

### Task 5.2: 最终提交

- [ ] **Step 1: 确保所有更改已提交**

```bash
git status
git add -A
git commit -m "feat: complete glassmorphism UI modernization"
```

---

## 完成标志

- [ ] 所有样式模块创建完成
- [ ] SVG 图标模块创建完成
- [ ] 主窗口样式重构完成
- [ ] 个人中心抽屉样式更新完成
- [ ] 功能测试通过
- [ ] 所有更改已提交
