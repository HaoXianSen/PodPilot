"""
工程相关 MR 对话框
显示当前主工程及其关联的已配置私有库 Pod 的待合并 MR
"""

import json
import urllib.request
import urllib.error
import urllib.parse
import webbrowser
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QFrame,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QCursor

from src.styles import Colors, Styles, GlassmorphismStyle


class ProjectMRLoader(QThread):
    """异步加载项目的 MR 列表"""

    finished = pyqtSignal(str, list)
    error_occurred = pyqtSignal(str, str)

    def __init__(self, project_name, git_url, gitlab_token):
        super().__init__()
        self.project_name = project_name
        self.git_url = git_url
        self.gitlab_token = gitlab_token

    def run(self):
        try:
            host, path_part = self._parse_git_url(self.git_url)

            if not host or not path_part:
                self.error_occurred.emit(self.project_name, "无法解析 Git URL")
                return

            encoded_path = urllib.parse.quote(path_part, safe="")

            api_url = f"https://{host}/api/v4/projects/{encoded_path}/merge_requests?state=opened&per_page=100"

            req = urllib.request.Request(
                api_url,
                headers={
                    "PRIVATE-TOKEN": self.gitlab_token,
                },
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                self.finished.emit(self.project_name, result)

        except urllib.error.HTTPError as e:
            self.error_occurred.emit(self.project_name, f"HTTP 错误 {e.code}")
        except urllib.error.URLError as e:
            self.error_occurred.emit(self.project_name, f"网络错误")
        except Exception as e:
            self.error_occurred.emit(self.project_name, f"加载失败: {str(e)}")

    def _parse_git_url(self, git_url):
        """解析 Git URL，返回 (host, path)"""
        if not git_url:
            return None, None

        if git_url.startswith("git@"):
            parts = git_url.replace("git@", "").split(":")
            host = parts[0]
            path_part = parts[1] if len(parts) > 1 else ""
            path_part = path_part.replace(".git", "")
        else:
            from urllib.parse import urlparse

            parsed = urlparse(git_url)
            host = parsed.hostname
            path_part = parsed.path.lstrip("/").replace(".git", "")

        return host, path_part


class MRCardWidget(QFrame):
    """MR 卡片组件"""

    def __init__(self, mr_data, parent=None):
        super().__init__(parent)
        self.mr_data = mr_data
        self.mr_url = mr_data.get("web_url", "")
        self.initUI()

    def initUI(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.SURFACE_BORDER};
                border-radius: 12px;
                padding: 10px;
            }}
            QFrame:hover {{
                background-color: {Colors.SURFACE_HOVER};
                border-color: rgba(88, 86, 214, 0.5);
            }}
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = self.mr_data.get("title", "无标题")
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: bold;
                color: {Colors.TEXT_PRIMARY};
                border: none;
                background: transparent;
            }}
        """)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        source_branch = self.mr_data.get("source_branch", "")
        target_branch = self.mr_data.get("target_branch", "")
        branch_label = QLabel(f"{source_branch} → {target_branch}")
        branch_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {Colors.MR};
                border: none;
                background: transparent;
            }}
        """)
        layout.addWidget(branch_label)

        author = self.mr_data.get("author", {}).get("name", "未知")
        created_at = self.mr_data.get("created_at", "")
        if created_at:
            created_at = created_at.replace("T", " ").split(".")[0]

        info_label = QLabel(f"{author}  |  {created_at}")
        info_label.setStyleSheet(f"""
            QLabel {{
                font-size: 10px;
                color: {Colors.TEXT_MUTED};
                border: none;
                background: transparent;
            }}
        """)
        layout.addWidget(info_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.mr_url:
            webbrowser.open(self.mr_url)
        super().mousePressEvent(event)


class ProjectMRDialog(QDialog):
    """工程相关 MR 对话框"""

    def __init__(self, project_info, pods_info, gitlab_token, parent=None):
        super().__init__(parent)
        self._titlebar_setup = False
        self.project_info = project_info or {}
        self.pods_info = pods_info or {}
        self.gitlab_token = gitlab_token
        self.mr_loaders = []
        self.project_mrs = {}
        self.project_errors = {}
        self.initUI()
        self.load_all_mrs()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._titlebar_setup:
            GlassmorphismStyle.setup_transparent_titlebar(self)
            self._titlebar_setup = True

    def initUI(self):
        self.setWindowTitle("当前工程 Merge Requests")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)

        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.BG_GRADIENT_START},
                    stop:0.5 {Colors.BG_GRADIENT_MID},
                    stop:1 {Colors.BG_GRADIENT_END}
                );
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title_bar = QFrame()
        title_bar.setFixedHeight(56)
        title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 0, 0, 0.2);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)

        title_label = QLabel("当前工程 Merge Requests")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {Colors.TEXT_PRIMARY};
                border: none;
            }}
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setStyleSheet(Styles.BUTTON)
        self.refresh_btn.clicked.connect(self.load_all_mrs)
        title_layout.addWidget(self.refresh_btn)

        layout.addWidget(title_bar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter {{
                background: transparent;
            }}
            QSplitter::handle {{
                background-color: rgba(255, 255, 255, 0.1);
                width: 1px;
            }}
        """)

        left_panel = QFrame()
        left_panel.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 0, 0, 0.15);
                border: none;
            }}
        """)
        left_panel.setMinimumWidth(250)
        left_panel.setMaximumWidth(350)

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        left_header = QLabel("项目列表")
        left_header.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {Colors.TEXT_PRIMARY};
                padding: 12px 16px;
                background-color: rgba(0, 0, 0, 0.2);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)
        left_layout.addWidget(left_header)

        self.project_list = QListWidget()
        self.project_list.setStyleSheet(f"""
            QListWidget {{
                border: none;
                background-color: transparent;
                outline: none;
            }}
            QListWidget::item {{
                padding: 12px 16px;
                color: {Colors.TEXT_PRIMARY};
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }}
            QListWidget::item:selected {{
                background-color: rgba(255, 255, 255, 0.25);
                color: {Colors.TEXT_PRIMARY};
            }}
            QListWidget::item:hover:!selected {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
        """)
        self.project_list.currentItemChanged.connect(self._on_project_selected)
        left_layout.addWidget(self.project_list)

        splitter.addWidget(left_panel)

        right_panel = QFrame()
        right_panel.setStyleSheet("background: transparent;")

        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.right_header = QLabel("请选择左侧项目")
        self.right_header.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {Colors.TEXT_PRIMARY};
                padding: 12px 16px;
                background-color: rgba(0, 0, 0, 0.2);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)
        right_layout.addWidget(self.right_header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            {Styles.SCROLL_BAR}
        """)

        self.mr_content = QWidget()
        self.mr_content.setStyleSheet("background: transparent;")
        self.mr_layout = QVBoxLayout(self.mr_content)
        self.mr_layout.setContentsMargins(16, 16, 16, 16)
        self.mr_layout.setSpacing(10)

        self.placeholder_label = QLabel("请选择左侧项目查看 MR")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {Colors.TEXT_MUTED};
                padding: 40px;
            }}
        """)
        self.mr_layout.addWidget(self.placeholder_label)
        self.mr_layout.addStretch()

        scroll_area.setWidget(self.mr_content)
        right_layout.addWidget(scroll_area)

        splitter.addWidget(right_panel)
        splitter.setSizes([280, 620])

        layout.addWidget(splitter)

        button_bar = QFrame()
        button_bar.setFixedHeight(60)
        button_bar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 0, 0, 0.2);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)

        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(20, 0, 20, 0)
        button_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(Styles.BUTTON)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addWidget(button_bar)

    def load_all_mrs(self):
        """加载所有项目的 MR"""
        if not self.gitlab_token:
            ModernDialog.warning(self, "提示", "请先在个人中心配置 GitLab Token")
            return

        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("加载中...")

        self.project_mrs.clear()
        self.project_errors.clear()
        self.project_list.clear()
        self._clear_mr_list()

        all_projects = {}

        if self.project_info and self.project_info.get("git_url"):
            project_name = self.project_info.get("name", "主工程")
            all_projects[project_name] = {
                "git_url": self.project_info.get("git_url"),
                "is_main": True,
            }

        for pod_name, pod_info in self.pods_info.items():
            git_url = pod_info.get("git_url", "")
            if git_url and "gitlab" in git_url.lower():
                all_projects[pod_name] = {"git_url": git_url, "is_main": False}

        if not all_projects:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("刷新")
            self._show_placeholder("暂无可用的项目")
            return

        for project_name in all_projects:
            item = QListWidgetItem(f"⏳ {project_name} (加载中...)")
            item.setData(Qt.UserRole, project_name)
            self.project_list.addItem(item)

        self.pending_count = len(all_projects)
        self.mr_loaders = []

        for project_name, info in all_projects.items():
            loader = ProjectMRLoader(project_name, info["git_url"], self.gitlab_token)
            loader.finished.connect(self._on_project_mrs_loaded)
            loader.error_occurred.connect(self._on_project_load_error)
            self.mr_loaders.append(loader)
            loader.start()

    def _on_project_mrs_loaded(self, project_name, mrs):
        """单个项目 MR 加载完成"""
        self.project_mrs[project_name] = mrs
        self._update_project_item(project_name, len(mrs))
        self._check_all_loaded()

    def _on_project_load_error(self, project_name, error_msg):
        """单个项目加载出错"""
        self.project_errors[project_name] = error_msg
        self._update_project_item(project_name, -1, error_msg)
        self._check_all_loaded()

    def _update_project_item(self, project_name, mr_count, error=None):
        """更新项目列表项"""
        for i in range(self.project_list.count()):
            item = self.project_list.item(i)
            if item.data(Qt.UserRole) == project_name:
                if error:
                    item.setText(f"❌ {project_name} (错误)")
                elif mr_count == 0:
                    item.setText(f"📁 {project_name} (0)")
                else:
                    item.setText(f"📁 {project_name} ({mr_count})")
                break

    def _check_all_loaded(self):
        """检查是否所有项目都加载完成"""
        total = len(self.project_mrs) + len(self.project_errors)
        if total >= self.pending_count:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("刷新")

            for i in range(self.project_list.count()):
                item = self.project_list.item(i)
                project_name = item.data(Qt.UserRole)
                if project_name in self.project_mrs and self.project_mrs[project_name]:
                    self.project_list.setCurrentItem(item)
                    return

            if self.project_list.count() > 0:
                self.project_list.setCurrentRow(0)

    def _on_project_selected(self, current, previous):
        """项目选中事件"""
        if not current:
            return

        project_name = current.data(Qt.UserRole)
        self._clear_mr_list()

        if project_name in self.project_errors:
            self.right_header.setText(f"{project_name} - 加载失败")
            self._show_placeholder(f"❌ {self.project_errors[project_name]}")
        elif project_name in self.project_mrs:
            mrs = self.project_mrs[project_name]
            self.right_header.setText(f"{project_name} ({len(mrs)} 个 MR)")

            if not mrs:
                self._show_placeholder("暂无待合并的 MR")
            else:
                for mr in mrs:
                    card = MRCardWidget(mr)
                    self.mr_layout.addWidget(card)
                self.mr_layout.addStretch()
        else:
            self.right_header.setText(project_name)
            self._show_placeholder("正在加载...")

    def _clear_mr_list(self):
        """清空 MR 列表"""
        while self.mr_layout.count() > 0:
            item = self.mr_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_placeholder(self, message):
        """显示占位信息"""
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {Colors.TEXT_MUTED};
                padding: 40px;
            }}
        """)
        self.mr_layout.addWidget(label)
        self.mr_layout.addStretch()
