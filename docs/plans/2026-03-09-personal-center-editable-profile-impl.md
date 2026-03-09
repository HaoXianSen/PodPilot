# 个人中心可编辑头像和名称功能实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现个人中心的头像和名称可编辑，头像仅本地管理，名称同步到 Git 本地配置

**Architecture:** 
- 扩展 ConfigService 支持头像配置存储
- 扩展 GitService 支持设置用户名
- 修改 PersonalCenterDrawer 实现可编辑 UI

**Tech Stack:** Python 3, PyQt5

---

## Task 1: 扩展 ConfigService 支持头像配置

**Files:**
- Modify: `src/services/config_service.py`

**Step 1: 在 __init__ 中添加头像相关字段**

在 `ConfigService.__init__` 方法中添加：

```python
def __init__(self, config_path: Union[str, None] = None):
    self.config_path = config_path or os.path.join(
        os.path.expanduser("~"), ".podpilot_config.json"
    )
    self.projects = []
    self.pods_config = {}
    self.original_pod_references = {}
    self.last_pod_modes = {}
    self.current_project = None
    self.gitlab_token = ""
    self.github_token = ""
    # 新增：头像相关配置
    self.custom_avatar_path = ""  # 用户自定义头像路径
```

**Step 2: 在 load_config 中加载头像配置**

在 `load_config` 方法中，在 `if "github_token" in config:` 之后添加：

```python
if "custom_avatar_path" in config:
    self.custom_avatar_path = config["custom_avatar_path"]
```

**Step 3: 在 save_config 中保存头像配置**

在 `save_config` 方法中，在 `config` 字典中添加：

```python
config = {
    "projects": self.projects,
    "pods_config": self.pods_config,
    "original_pod_references": self.original_pod_references,
    "last_pod_modes": self.last_pod_modes,
    "gitlab_token": self.gitlab_token,
    "github_token": self.github_token,
    # 新增：头像配置
    "custom_avatar_path": self.custom_avatar_path,
}
```

**Step 4: 提交**

```bash
git add src/services/config_service.py
git commit -m "feat: add avatar config fields to ConfigService"
```

---

## Task 2: 扩展 GitService 支持设置用户名

**Files:**
- Modify: `src/services/git_service.py`

**Step 1: 添加设置用户名方法**

在 `GitService` 类中添加：

```python
@staticmethod
def set_username(username: str) -> bool:
    """设置 Git 全局用户名
    
    Args:
        username: 新的用户名
        
    Returns:
        成功返回 True，失败返回 False
    """
    try:
        result = subprocess.run(
            ["git", "config", "--global", "user.name", username],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"设置 Git 用户名失败: {str(e)}")
        return False
```

**Step 2: 提交**

```bash
git add src/services/git_service.py
git commit -m "feat: add set_username method to GitService"
```

---

## Task 3: 创建可编辑头像组件

**Files:**
- Modify: `src/views/dialogs/personal_center_drawer.py`

**Step 1: 修改导入**

在文件顶部添加导入：

```python
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QMessageBox,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QFileDialog,  # 新增
)
from PyQt5.QtCore import (
    Qt,
    QPropertyAnimation,
    QPoint,
    QEasingCurve,
    QEvent,
    pyqtSignal,  # 新增
)
```

**Step 2: 添加 QPainterPath 和 QBrush 导入**

修改 QtGui 导入：

```python
from PyQt5.QtGui import QPixmap, QPainter, QColor, QTextCursor, QPen, QPainterPath, QBrush
```

**Step 3: 创建可点击头像组件**

替换原来的 `AvatarWidget` 类：

```python
class ClickableAvatar(QWidget):
    """可点击的头像组件"""
    
    clicked = pyqtSignal()
    
    def __init__(self, size=64, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        self._avatar_path = None
        self._pixmap = None
        self._hover = False
        self.setCursor(Qt.PointingHandCursor)
    
    def set_avatar_path(self, path):
        """设置头像图片路径"""
        self._avatar_path = path
        if path:
            self._pixmap = QPixmap(path)
        else:
            self._pixmap = None
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self._size
        h = self._size
        
        if self._pixmap and not self._pixmap.isNull():
            # 绘制图片
            scaled = self._pixmap.scaled(
                w, h, 
                Qt.KeepAspectRatioByExpanding, 
                Qt.SmoothTransformation
            )
            
            clip_path = QPainterPath()
            clip_path.addEllipse(0, 0, w, h)
            painter.setClipPath(clip_path)
            painter.drawPixmap(0, 0, scaled)
        else:
            # 绘制默认头像
            painter.setBrush(QBrush(QColor("#007aff")))
            painter.setPen(QPen(QColor("transparent")))
            painter.drawEllipse(0, 0, w, h)
            
            painter.setBrush(QBrush(QColor("white")))
            
            head_w = int(w * 0.3)
            head_h = int(h * 0.3)
            head_x = (w - head_w) // 2
            head_y = int(h * 0.12)
            
            body_w = int(w * 0.5)
            body_h = int(h * 0.4)
            body_x = (w - body_w) // 2
            body_y = int(h * 0.5)
            
            painter.drawEllipse(head_x, head_y, head_w, head_h)
            painter.drawEllipse(body_x, body_y, body_w, body_h)
        
        # Hover 效果
        if self._hover:
            painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
            painter.setPen(QPen(QColor("transparent")))
            painter.drawEllipse(0, 0, w, h)
            
            # 绘制编辑图标或文字
            painter.setPen(QPen(QColor("white")))
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            painter.drawText(0, 0, w, h, Qt.AlignCenter, "编辑")
    
    def enterEvent(self, event):
        self._hover = True
        self.update()
    
    def leaveEvent(self, event):
        self._hover = False
        self.update()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
```

**Step 4: 提交**

```bash
git add src/views/dialogs/personal_center_drawer.py
git commit -m "feat: add clickable avatar widget"
```

---

## Task 4: 修改 PersonalCenterDrawer UI 布局

**Files:**
- Modify: `src/views/dialogs/personal_center_drawer.py`

**Step 1: 修改 initUI 中的头像区域**

将原来的头像部分：

```python
avatar_label = AvatarWidget(size=64)
info_layout.addWidget(avatar_label)
```

替换为：

```python
# 头像（可点击）
self.avatar_widget = ClickableAvatar(size=64)
self.avatar_widget.clicked.connect(self._on_avatar_clicked)

# 加载自定义头像
custom_avatar = self.config.get("custom_avatar_path", "")
if custom_avatar and os.path.exists(custom_avatar):
    self.avatar_widget.set_avatar_path(custom_avatar)

info_layout.addWidget(self.avatar_widget)
```

**Step 2: 修改名称显示为可编辑输入框**

将原来的名称显示：

```python
username = self.get_git_username()
self.name_label = QLabel(username)
self.name_label.setContentsMargins(10, 0, 0, 0)
self.name_label.setStyleSheet("""
    QLabel {
        font-size: 16px;
        font-weight: bold;
        color: #333;
    }
""")
name_layout.addWidget(self.name_label)
```

替换为：

```python
username = self.get_git_username()
self.name_input = QLineEdit(username)
self.name_input.setContentsMargins(10, 0, 0, 0)
self.name_input.setStyleSheet("""
    QLineEdit {
        font-size: 16px;
        font-weight: bold;
        color: #333;
        border: 1px solid transparent;
        padding: 4px 8px;
        border-radius: 4px;
        background: transparent;
    }
    QLineEdit:hover {
        border: 1px solid #e5e5e5;
        background: white;
    }
    QLineEdit:focus {
        border: 1px solid #007aff;
        background: white;
    }
""")
name_layout.addWidget(self.name_input)
```

**Step 3: 添加头像点击处理方法**

在 `save_tokens` 方法之前添加：

```python
def _on_avatar_clicked(self):
    """头像点击处理"""
    file_path, _ = QFileDialog.getOpenFileName(
        self,
        "选择头像",
        "",
        "图片文件 (*.jpg *.jpeg *.png);;所有文件 (*)"
    )
    
    if file_path:
        # 立即显示预览
        self.avatar_widget.set_avatar_path(file_path)
        
        # 保存到配置
        self.config["custom_avatar_path"] = file_path
```

**Step 4: 修改 save_tokens 方法**

修改 `save_tokens` 方法以支持名称同步：

```python
def save_tokens(self):
    """保存配置（包括头像和名称）"""
    gitlab_token = self.gitlab_token_input.text().strip()
    github_token = self.github_token_input.text().strip()
    
    self.config["gitlab_token"] = gitlab_token
    self.config["github_token"] = github_token
    
    # 保存名称到 Git 配置
    new_name = self.name_input.text().strip()
    if new_name:
        from src.services.git_service import GitService
        if not GitService.set_username(new_name):
            QMessageBox.warning(self, "警告", "名称保存到 Git 配置失败")
    
    # 保存配置
    self._save_config_and_close()

def _save_config_and_close(self):
    """保存配置并关闭"""
    self.save_config()
    
    # 同步更新主窗口的 personal_config
    if self.parent_manager and hasattr(self.parent_manager, "personal_config"):
        self.parent_manager.personal_config["gitlab_token"] = self.config.get("gitlab_token", "")
        self.parent_manager.personal_config["github_token"] = self.config.get("github_token", "")
    
    if self.parent_manager:
        self.parent_manager.log_message("个人中心配置已保存")
    
    QMessageBox.information(self, "成功", "配置已保存")
    self.slide_out()
```

**Step 5: 修改 save_config 方法**

修改 `save_config` 方法以保存新字段：

```python
def save_config(self):
    """保存配置"""
    try:
        existing_config = {}
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                existing_config = json.load(f)
        
        existing_config["gitlab_token"] = self.config.get("gitlab_token", "")
        existing_config["github_token"] = self.config.get("github_token", "")
        # 新增：保存头像配置
        existing_config["custom_avatar_path"] = self.config.get("custom_avatar_path", "")
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(existing_config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
```

**Step 6: 提交**

```bash
git add src/views/dialogs/personal_center_drawer.py
git commit -m "feat: implement editable avatar and username in personal center"
```

---

## Task 5: 验证和测试

**Files:**
- None (manual testing)

**Step 1: 运行应用**

```bash
cd /Users/haoyh02/Desktop/iPM
python3 main.py
```

**Step 2: 测试功能**

测试清单：
- [ ] 打开个人中心，检查头像默认显示
- [ ] 点击头像，选择本地图片，检查预览显示
- [ ] 修改名称，点击保存，检查是否更新
- [ ] 验证名称是否同步到 `git config user.name`
- [ ] 关闭并重新打开个人中心，检查配置是否持久化

**Step 3: 提交最终代码（如有修复）**

```bash
git add .
git commit -m "fix: resolve issues from testing"
```

---

## 完成标志

所有任务完成后：
1. 头像可点击选择本地图片
2. 头像保存在本地配置，仅本应用使用
3. 名称可编辑
4. 名称同步到 Git 本地配置
5. 所有配置持久化保存
