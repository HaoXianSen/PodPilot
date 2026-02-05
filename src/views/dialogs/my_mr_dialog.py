"""
我的全部 MR 对话框
显示用户在 GitLab 上创建的所有待合并 MR
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
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QCursor


class MyMRLoader(QThread):
    """异步加载用户的所有 MR"""

    finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, gitlab_host, gitlab_token):
        super().__init__()
        self.gitlab_host = gitlab_host
        self.gitlab_token = gitlab_token

    def run(self):
        try:
            # GitLab API: 获取当前用户创建的所有待合并 MR
            api_url = f"https://{self.gitlab_host}/api/v4/merge_requests?scope=created_by_me&state=opened&per_page=100"

            req = urllib.request.Request(
                api_url,
                headers={
                    "PRIVATE-TOKEN": self.gitlab_token,
                },
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                self.finished.emit(result)

        except urllib.error.HTTPError as e:
            self.error_occurred.emit(f"HTTP 错误 {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            self.error_occurred.emit(f"网络错误: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"加载失败: {str(e)}")


class MRCardWidget(QFrame):
    """MR 卡片组件"""

    def __init__(self, mr_data, parent=None):
        super().__init__(parent)
        self.mr_data = mr_data
        self.mr_url = mr_data.get("web_url", "")
        self.initUI()

    def initUI(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                padding: 12px;
            }
            QFrame:hover {
                background-color: #f8f9fa;
                border-color: #007aff;
            }
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 项目名称
        project_path = self.mr_data.get("references", {}).get("full", "")
        if not project_path:
            # 从 web_url 提取项目路径
            web_url = self.mr_data.get("web_url", "")
            if "/-/merge_requests/" in web_url:
                project_path = web_url.split("/-/merge_requests/")[0].split("//")[-1]

        project_label = QLabel(f"📁 {project_path}")
        project_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
                border: none;
                background: transparent;
            }
        """)
        layout.addWidget(project_label)

        # MR 标题
        title = self.mr_data.get("title", "无标题")
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                border: none;
                background: transparent;
            }
        """)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # 分支信息
        source_branch = self.mr_data.get("source_branch", "")
        target_branch = self.mr_data.get("target_branch", "")
        branch_label = QLabel(f"🔀 {source_branch} → {target_branch}")
        branch_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #007aff;
                border: none;
                background: transparent;
            }
        """)
        layout.addWidget(branch_label)

        # 创建时间
        created_at = self.mr_data.get("created_at", "")
        if created_at:
            # 格式化时间
            created_at = created_at.replace("T", " ").split(".")[0]
        time_label = QLabel(f"🕐 {created_at}")
        time_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #999;
                border: none;
                background: transparent;
            }
        """)
        layout.addWidget(time_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.mr_url:
            webbrowser.open(self.mr_url)
        super().mousePressEvent(event)


class MyMRDialog(QDialog):
    """我的全部 MR 对话框"""

    def __init__(self, gitlab_token, gitlab_host="gitlab.corp.youdao.com", parent=None):
        super().__init__(parent)
        self.gitlab_token = gitlab_token
        self.gitlab_host = gitlab_host
        self.mr_loader = None
        self.initUI()
        self.load_mrs()

    def initUI(self):
        self.setWindowTitle("我的 Merge Requests")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        title_bar = QFrame()
        title_bar.setFixedHeight(56)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e5e5e5;
            }
        """)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)

        title_label = QLabel("我的 Merge Requests")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                border: none;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004494;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.refresh_btn.clicked.connect(self.load_mrs)
        title_layout.addWidget(self.refresh_btn)

        layout.addWidget(title_bar)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #f5f5f7;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 0, 0, 0.3);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #f5f5f7;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(20, 20, 20, 20)
        self.scroll_layout.setSpacing(12)

        # 加载提示
        self.loading_label = QLabel("正在加载...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666;
                padding: 40px;
            }
        """)
        self.scroll_layout.addWidget(self.loading_label)
        self.scroll_layout.addStretch()

        scroll_area.setWidget(self.scroll_content)
        layout.addWidget(scroll_area)

        # 底部按钮栏
        button_bar = QFrame()
        button_bar.setFixedHeight(60)
        button_bar.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-top: 1px solid #e5e5e5;
            }
        """)

        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(20, 0, 20, 0)
        button_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 1px solid #e5e5e5;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.02);
            }
        """)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addWidget(button_bar)

    def load_mrs(self):
        """加载 MR 列表"""
        if not self.gitlab_token:
            self._show_error("请先在个人中心配置 GitLab Token")
            return

        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("加载中...")

        # 清空现有内容
        self._clear_mr_list()
        self.loading_label.setText("正在加载...")
        self.loading_label.show()

        # 启动异步加载
        self.mr_loader = MyMRLoader(self.gitlab_host, self.gitlab_token)
        self.mr_loader.finished.connect(self._on_mrs_loaded)
        self.mr_loader.error_occurred.connect(self._on_load_error)
        self.mr_loader.start()

    def _clear_mr_list(self):
        """清空 MR 列表"""
        while self.scroll_layout.count() > 0:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_mrs_loaded(self, mrs):
        """MR 列表加载完成"""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("刷新")

        self._clear_mr_list()

        if not mrs:
            empty_label = QLabel("暂无待合并的 MR")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #999;
                    padding: 40px;
                }
            """)
            self.scroll_layout.addWidget(empty_label)
        else:
            # 显示 MR 数量
            count_label = QLabel(f"共 {len(mrs)} 个待合并的 MR")
            count_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #666;
                    padding-bottom: 8px;
                }
            """)
            self.scroll_layout.addWidget(count_label)

            # 添加 MR 卡片
            for mr in mrs:
                card = MRCardWidget(mr)
                self.scroll_layout.addWidget(card)

        self.scroll_layout.addStretch()

    def _on_load_error(self, error_msg):
        """加载出错"""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("刷新")

        self._clear_mr_list()
        self._show_error(error_msg)

    def _show_error(self, message):
        """显示错误信息"""
        error_label = QLabel(f"❌ {message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #ff3b30;
                padding: 40px;
            }
        """)
        self.scroll_layout.addWidget(error_label)
        self.scroll_layout.addStretch()
