import re
import json
import subprocess
import os
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
    QFileDialog,
)
from PyQt5.QtGui import (
    QPixmap,
    QPainter,
    QColor,
    QTextCursor,
    QPen,
    QPainterPath,
    QBrush,
)
from PyQt5.QtCore import (
    Qt,
    QPropertyAnimation,
    QPoint,
    QEasingCurve,
    QEvent,
    pyqtSignal,
)
from src.views.dialogs.my_mr_dialog import MyMRDialog


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
                w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
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


class PersonalCenterDrawer(QWidget):
    """个人中心抽屉（右侧滑出）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_manager = parent
        self.config_path = os.path.expanduser("~/.podpilot_config.json")
        self.config = self.load_config()
        self.initUI()
        self.setup_animations()

    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def save_config(self):
        """保存配置"""
        try:
            # 先加载现有的完整配置
            existing_config = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    existing_config = json.load(f)

            # 只更新token字段，保留其他配置
            existing_config["gitlab_token"] = self.config.get("gitlab_token", "")
            existing_config["github_token"] = self.config.get("github_token", "")
            existing_config["custom_avatar_path"] = self.config.get(
                "custom_avatar_path", ""
            )

            # 保存完整配置
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(existing_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")

    def get_git_username(self):
        """获取Git用户名"""
        try:
            result = subprocess.run(
                ["git", "config", "user.name"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "未设置"

    def initUI(self):
        self.setFixedWidth(480)

        if self.parent_manager:
            parent_geo = self.parent_manager.geometry()
            target_height = parent_geo.height() - parent_geo.top()
            self.setFixedHeight(target_height)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top-left-radius: 12px;
                border-bottom-left-radius: 12px;
                border: 1px solid #e5e5e5;
            }
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        title_bar = QFrame()
        title_bar.setFixedHeight(64)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
            }
        """)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)
        title_layout.setSpacing(12)

        title_label = QLabel("个人中心")
        title_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        container_layout.addWidget(title_bar)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.2);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 0, 0, 0.3);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        user_group = QGroupBox("用户信息")
        user_layout = QVBoxLayout()
        user_layout.setContentsMargins(15, 15, 15, 15)

        # 头像和名字
        info_layout = QHBoxLayout()

        # 头像（可点击）
        self.avatar_widget = ClickableAvatar(size=64)
        self.avatar_widget.clicked.connect(self._on_avatar_clicked)

        # 加载自定义头像
        custom_avatar = self.config.get("custom_avatar_path", "")
        if custom_avatar and os.path.exists(custom_avatar):
            self.avatar_widget.set_avatar_path(custom_avatar)

        info_layout.addWidget(self.avatar_widget)

        # 名字
        name_layout = QVBoxLayout()
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

        email_label = QLabel("Git用户")
        email_label.setContentsMargins(10, 0, 0, 0)
        email_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #999;
            }
        """)
        name_layout.addWidget(email_label)
        name_layout.addStretch()

        info_layout.addLayout(name_layout)
        user_layout.addLayout(info_layout)
        user_group.setLayout(user_layout)
        layout.addWidget(user_group)

        # Token配置区域
        token_group = QGroupBox("访问令牌配置")
        token_layout = QVBoxLayout()
        token_layout.setContentsMargins(15, 15, 15, 15)

        # GitLab Token
        gitlab_label = QLabel("GitLab Personal Access Token:")
        gitlab_label.setStyleSheet("""
                    QLabel {
                        border: none;
                    }
                """)
        gitlab_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.gitlab_token_input = QLineEdit()
        self.gitlab_token_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.gitlab_token_input.setPlaceholderText("输入GitLab Personal Access Token")
        self.gitlab_token_input.setEchoMode(QLineEdit.Password)

        saved_gitlab_token = self.config.get("gitlab_token", "")
        if saved_gitlab_token:
            self.gitlab_token_input.setText(saved_gitlab_token)

        gitlab_help = QLabel(
            "用于创建GitLab Merge Request\n权限范围：api, read_repository"
        )
        gitlab_help.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        gitlab_help.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #666;
                background-color: #f5f5f7;
                padding: 10px;
                border-radius: 6px;
            }
        """)
        gitlab_help.setWordWrap(True)

        token_layout.addWidget(gitlab_label)
        token_layout.addWidget(self.gitlab_token_input)
        token_layout.addWidget(gitlab_help)

        # GitHub Token
        github_label = QLabel("GitHub Personal Access Token:")
        github_label.setStyleSheet("""
            QLabel {
                border: none;
            }
        """)
        github_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.github_token_input = QLineEdit()
        self.github_token_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.github_token_input.setPlaceholderText("输入GitHub Personal Access Token")
        self.github_token_input.setEchoMode(QLineEdit.Password)

        saved_github_token = self.config.get("github_token", "")
        if saved_github_token:
            self.github_token_input.setText(saved_github_token)

        github_help = QLabel("用于创建GitHub Pull Request\n权限范围：repo, read:user")
        github_help.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        github_help.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #666;
                background-color: #f5f5f7;
                padding: 10px;
                border-radius: 6px;
            }
        """)
        github_help.setWordWrap(True)

        token_layout.addSpacing(16)
        token_layout.addWidget(github_label)
        token_layout.addWidget(self.github_token_input)
        token_layout.addWidget(github_help)

        # 令牌链接
        token_links = QLabel(
            "<a href='https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html'>创建GitLab Token</a> | "
            "<a href='https://github.com/settings/tokens'>创建GitHub Token</a>"
        )
        token_links.setOpenExternalLinks(True)
        token_links.setWordWrap(True)
        token_links.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #007aff;
                border: none;
            }
            QLabel a {
                color: #007aff;
                text-decoration: none;
            }
            QLabel a:hover {
                text-decoration: underline;
            }
        """)

        token_layout.addSpacing(16)
        token_layout.addWidget(token_links)
        token_layout.addStretch()

        token_group.setLayout(token_layout)
        layout.addWidget(token_group)

        # 我的 MR 区域
        mr_group = QGroupBox("Merge Requests")
        mr_layout = QVBoxLayout()
        mr_layout.setContentsMargins(15, 15, 15, 15)

        mr_desc = QLabel("查看您在 GitLab 上创建的所有待合并 MR")
        mr_desc.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
                border: none;
            }
        """)
        mr_desc.setWordWrap(True)
        mr_layout.addWidget(mr_desc)

        mr_layout.addSpacing(10)

        self.view_mr_btn = QPushButton("查看我的 MR")
        self.view_mr_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004494;
            }
        """)
        self.view_mr_btn.clicked.connect(self.show_my_mrs)
        mr_layout.addWidget(self.view_mr_btn)

        mr_group.setLayout(mr_layout)
        layout.addWidget(mr_group)

        # 底部间距
        layout.addSpacing(20)

        # 设置滚动内容
        scroll_area.setWidget(scroll_content)
        container_layout.addWidget(scroll_area)

        # 按钮区域（固定在底部）
        button_bar = QFrame()
        button_bar.setFixedHeight(70)
        button_bar.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
                border-radius: 0px;
                
            }
        """)
        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(20, 12, 20, 12)

        self.save_btn = QPushButton("保存")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: white;
                border-radius: 8px;
                padding: 6px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #30B350;
            }
            QPushButton:pressed {
                background-color: #28A745;
            }
        """)
        self.save_btn.setFixedWidth(80)
        self.save_btn.setFixedHeight(30)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                padding: 6px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.02);
            }
        """)
        self.cancel_btn.setFixedWidth(80)
        self.cancel_btn.setFixedHeight(30)
        self.save_btn.clicked.connect(self.save_tokens)
        self.cancel_btn.clicked.connect(self.slide_out)

        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        container_layout.addWidget(button_bar)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(container)

    def setup_animations(self):
        """设置动画"""
        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.InOutQuad)

    def slide_in(self):
        if self.parent_manager:
            parent_geo = self.parent_manager.geometry()
            end_pos = QPoint(parent_geo.width() - self.width(), parent_geo.top())
            start_pos = QPoint(parent_geo.width(), parent_geo.top())

            self.move(start_pos)
            self.show()
            self.raise_()

            self.slide_animation.setStartValue(start_pos)
            self.slide_animation.setEndValue(end_pos)
            self.slide_animation.finished.connect(self.show)
            self.slide_animation.start()

    def slide_out(self):
        """滑出动画"""
        if self.parent_manager:
            parent_geo = self.parent_manager.geometry()
            end_pos = QPoint(parent_geo.width(), parent_geo.top())
            start_pos = self.pos()

            self.slide_animation.setStartValue(start_pos)
            self.slide_animation.setEndValue(end_pos)
            self.slide_animation.finished.connect(self.hide)
            self.slide_animation.start()

    def _on_avatar_clicked(self):
        """头像点击处理"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择头像", "", "图片文件 (*.jpg *.jpeg *.png);;所有文件 (*)"
        )

        if file_path:
            # 立即显示预览
            self.avatar_widget.set_avatar_path(file_path)

            # 保存到配置
            self.config["custom_avatar_path"] = file_path

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
            self.parent_manager.personal_config["gitlab_token"] = self.config.get(
                "gitlab_token", ""
            )
            self.parent_manager.personal_config["github_token"] = self.config.get(
                "github_token", ""
            )

        if self.parent_manager:
            self.parent_manager.log_message("个人中心配置已保存")

        QMessageBox.information(self, "成功", "配置已保存")
        self.slide_out()

    def show_my_mrs(self):
        """显示我的 MR 对话框"""
        gitlab_token = self.gitlab_token_input.text().strip()

        if not gitlab_token:
            QMessageBox.warning(self, "提示", "请先配置 GitLab Token")
            return

        # 从 token 或配置中获取 GitLab 主机
        # 默认使用常见的 GitLab 主机
        gitlab_host = "gitlab.corp.youdao.com"

        dialog = MyMRDialog(gitlab_token, gitlab_host, self.parent_manager)
        dialog.exec_()
