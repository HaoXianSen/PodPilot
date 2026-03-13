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

from src.styles import Colors, Styles, GlassmorphismStyle


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

    CARD_STYLE = f"""
        QFrame {{
            background-color: {Colors.SURFACE};
            border: 1px solid {Colors.SURFACE_BORDER};
            border-radius: 12px;
            padding: 12px;
        }}
        QFrame:hover {{
            background-color: {Colors.SURFACE_HOVER};
            border: 1px solid rgba(255, 255, 255, 0.3);
        }}
    """

    PROJECT_LABEL_STYLE = f"""
        QLabel {{
            font-size: 12px;
            color: {Colors.TEXT_MUTED};
            border: none;
            background: transparent;
        }}
    """

    TITLE_LABEL_STYLE = f"""
        QLabel {{
            font-size: 14px;
            font-weight: bold;
            color: {Colors.TEXT_PRIMARY};
            border: none;
            background: transparent;
        }}
    """

    BRANCH_LABEL_STYLE = f"""
        QLabel {{
            font-size: 12px;
            color: {Colors.BRANCH};
            border: none;
            background: transparent;
        }}
    """

    TIME_LABEL_STYLE = f"""
        QLabel {{
            font-size: 11px;
            color: {Colors.TEXT_MUTED};
            border: none;
            background: transparent;
        }}
    """

    def __init__(self, mr_data, parent=None):
        super().__init__(parent)
        self.mr_data = mr_data
        self.mr_url = mr_data.get("web_url", "")
        self.initUI()

    def initUI(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(self.CARD_STYLE)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        project_path = self.mr_data.get("references", {}).get("full", "")
        if not project_path:
            web_url = self.mr_data.get("web_url", "")
            if "/-/merge_requests/" in web_url:
                project_path = web_url.split("/-/merge_requests/")[0].split("//")[-1]

        project_label = QLabel(f"📁 {project_path}")
        project_label.setStyleSheet(self.PROJECT_LABEL_STYLE)
        layout.addWidget(project_label)

        title = self.mr_data.get("title", "无标题")
        title_label = QLabel(title)
        title_label.setStyleSheet(self.TITLE_LABEL_STYLE)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        source_branch = self.mr_data.get("source_branch", "")
        target_branch = self.mr_data.get("target_branch", "")
        branch_label = QLabel(f"🔀 {source_branch} → {target_branch}")
        branch_label.setStyleSheet(self.BRANCH_LABEL_STYLE)
        layout.addWidget(branch_label)

        created_at = self.mr_data.get("created_at", "")
        if created_at:
            created_at = created_at.replace("T", " ").split(".")[0]
        time_label = QLabel(f"🕐 {created_at}")
        time_label.setStyleSheet(self.TIME_LABEL_STYLE)
        layout.addWidget(time_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.mr_url:
            webbrowser.open(self.mr_url)
        super().mousePressEvent(event)


class MyMRDialog(QDialog):
    """我的全部 MR 对话框"""

    DIALOG_BG = f"""
        QDialog {{
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.BG_GRADIENT_START},
                stop:0.5 {Colors.BG_GRADIENT_MID},
                stop:1 {Colors.BG_GRADIENT_END}
            );
        }}
    """

    TITLE_BAR_STYLE = f"""
        QFrame {{
            background-color: rgba(0, 0, 0, 0.2);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
    """

    TITLE_LABEL_STYLE = f"""
        QLabel {{
            font-size: 18px;
            font-weight: bold;
            color: {Colors.TEXT_PRIMARY};
            border: none;
        }}
    """

    REFRESH_BTN_STYLE = f"""
        QPushButton {{
            background-color: {Colors.BTN_PRIMARY};
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 13px;
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

    SCROLL_AREA_STYLE = f"""
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 6px;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: rgba(255, 255, 255, 0.3);
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """

    BUTTON_BAR_STYLE = f"""
        QFrame {{
            background-color: rgba(0, 0, 0, 0.15);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }}
    """

    CLOSE_BTN_STYLE = f"""
        QPushButton {{
            background-color: {Colors.BTN_SECONDARY};
            color: {Colors.TEXT_SECONDARY};
            border: 1px solid {Colors.BTN_SECONDARY_BORDER};
            border-radius: 8px;
            padding: 8px 24px;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: rgba(255, 255, 255, 0.2);
        }}
    """

    LOADING_LABEL_STYLE = f"""
        QLabel {{
            font-size: 14px;
            color: {Colors.TEXT_SECONDARY};
            padding: 40px;
        }}
    """

    EMPTY_LABEL_STYLE = f"""
        QLabel {{
            font-size: 14px;
            color: {Colors.TEXT_MUTED};
            padding: 40px;
        }}
    """

    COUNT_LABEL_STYLE = f"""
        QLabel {{
            font-size: 12px;
            color: {Colors.TEXT_MUTED};
            padding-bottom: 8px;
        }}
    """

    ERROR_LABEL_STYLE = f"""
        QLabel {{
            font-size: 14px;
            color: #ff6b6b;
            padding: 40px;
        }}
    """

    def __init__(self, gitlab_token, gitlab_host="gitlab.corp.youdao.com", parent=None):
        super().__init__(parent)
        self._titlebar_setup = False
        self.gitlab_token = gitlab_token
        self.gitlab_host = gitlab_host
        self.mr_loader = None
        self.initUI()
        self.load_mrs()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._titlebar_setup:
            GlassmorphismStyle.setup_transparent_titlebar(self)
            self._titlebar_setup = True

    def initUI(self):
        self.setWindowTitle("我的 Merge Requests")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        self.setStyleSheet(self.DIALOG_BG)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title_bar = QFrame()
        title_bar.setFixedHeight(56)
        title_bar.setStyleSheet(self.TITLE_BAR_STYLE)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)

        title_label = QLabel("我的 Merge Requests")
        title_label.setStyleSheet(self.TITLE_LABEL_STYLE)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setStyleSheet(self.REFRESH_BTN_STYLE)
        self.refresh_btn.clicked.connect(self.load_mrs)
        title_layout.addWidget(self.refresh_btn)

        layout.addWidget(title_bar)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(self.SCROLL_AREA_STYLE)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(20, 20, 20, 20)
        self.scroll_layout.setSpacing(12)

        self.loading_label = QLabel("正在加载...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet(self.LOADING_LABEL_STYLE)
        self.scroll_layout.addWidget(self.loading_label)
        self.scroll_layout.addStretch()

        scroll_area.setWidget(self.scroll_content)
        layout.addWidget(scroll_area)

        button_bar = QFrame()
        button_bar.setFixedHeight(60)
        button_bar.setStyleSheet(self.BUTTON_BAR_STYLE)

        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(20, 0, 20, 0)
        button_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(self.CLOSE_BTN_STYLE)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addWidget(button_bar)

    def load_mrs(self):
        if not self.gitlab_token:
            self._show_error("请先在个人中心配置 GitLab Token")
            return

        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("加载中...")

        self._clear_mr_list()
        self.loading_label.setText("正在加载...")
        self.loading_label.show()

        self.mr_loader = MyMRLoader(self.gitlab_host, self.gitlab_token)
        self.mr_loader.finished.connect(self._on_mrs_loaded)
        self.mr_loader.error_occurred.connect(self._on_load_error)
        self.mr_loader.start()

    def _clear_mr_list(self):
        while self.scroll_layout.count() > 0:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_mrs_loaded(self, mrs):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("刷新")

        self._clear_mr_list()

        if not mrs:
            empty_label = QLabel("暂无待合并的 MR")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet(self.EMPTY_LABEL_STYLE)
            self.scroll_layout.addWidget(empty_label)
        else:
            count_label = QLabel(f"共 {len(mrs)} 个待合并的 MR")
            count_label.setStyleSheet(self.COUNT_LABEL_STYLE)
            self.scroll_layout.addWidget(count_label)

            for mr in mrs:
                card = MRCardWidget(mr)
                self.scroll_layout.addWidget(card)

        self.scroll_layout.addStretch()

    def _on_load_error(self, error_msg):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("刷新")

        self._clear_mr_list()
        self._show_error(error_msg)

    def _show_error(self, message):
        error_label = QLabel(f"❌ {message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet(self.ERROR_LABEL_STYLE)
        self.scroll_layout.addWidget(error_label)
        self.scroll_layout.addStretch()
