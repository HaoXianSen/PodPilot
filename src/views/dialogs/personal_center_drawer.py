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
    QMessageBox,
    QFrame,
    QScrollArea,
    QFileDialog,
)
from PyQt5.QtGui import (
    QPixmap,
    QPainter,
    QColor,
    QPen,
    QPainterPath,
    QBrush,
)
from PyQt5.QtCore import (
    Qt,
    QPropertyAnimation,
    QPoint,
    QEasingCurve,
    QTimer,
    pyqtSignal,
)
from src.views.dialogs.my_mr_dialog import MyMRDialog
from src.styles import Colors, Styles
from src.resources.icons import IconManager


class ClickableAvatar(QWidget):
    """可点击的头像组件"""

    clicked = pyqtSignal()

    def __init__(self, size=80, parent=None):
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
            scaled = self._pixmap.scaled(
                w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            clip_path = QPainterPath()
            clip_path.addEllipse(0, 0, w, h)
            painter.setClipPath(clip_path)
            painter.drawPixmap(0, 0, scaled)
        else:
            painter.setBrush(QBrush(QColor(Colors.BRANCH)))
            painter.setPen(QPen(QColor("transparent")))
            painter.drawEllipse(0, 0, w, h)

            painter.setBrush(QBrush(QColor(Colors.TEXT_PRIMARY)))
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

        if self._hover:
            clip_path = QPainterPath()
            clip_path.addEllipse(0, 0, w, h)
            painter.setClipPath(clip_path)
            painter.setBrush(QBrush(QColor(0, 0, 0, 80)))
            painter.setPen(QPen(QColor("transparent")))
            painter.drawEllipse(0, 0, w, h)

            painter.setPen(QPen(QColor(Colors.TEXT_PRIMARY)))
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


class OverlayWidget(QWidget):
    """半透明背景遮罩"""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.ArrowCursor)
        self._target_alpha = 0
        self._current_alpha = 0

        # 淡入淡出用定时器驱动
        self._timer = QTimer(self)
        self._timer.setInterval(16)  # ~60fps
        self._timer.timeout.connect(self._tick)
        self._fading_in = True

    def fade_in(self):
        self._target_alpha = 90  # 0-255
        self._fading_in = True
        self.show()
        self.raise_()
        self._timer.start()

    def fade_out(self):
        self._target_alpha = 0
        self._fading_in = False
        self._timer.start()

    def _tick(self):
        step = 12
        if self._fading_in:
            self._current_alpha = min(self._current_alpha + step, self._target_alpha)
        else:
            self._current_alpha = max(self._current_alpha - step, 0)
        self.update()
        if self._current_alpha == self._target_alpha:
            self._timer.stop()
            if self._current_alpha == 0:
                self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, self._current_alpha))

    def mousePressEvent(self, event):
        self.clicked.emit()


class PersonalCenterDrawer(QWidget):
    """个人中心抽屉（右侧滑出）- macOS 系统偏好设置风格"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_manager = parent
        self.config_path = os.path.expanduser("~/.podpilot_config.json")
        self.config = self.load_config()
        self._is_animating = False

        # 创建遮罩
        self.overlay = OverlayWidget(parent)
        self.overlay.clicked.connect(self.slide_out)
        self.overlay.hide()

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
            existing_config = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    existing_config = json.load(f)

            existing_config["gitlab_token"] = self.config.get("gitlab_token", "")
            existing_config["github_token"] = self.config.get("github_token", "")
            existing_config["custom_avatar_path"] = self.config.get(
                "custom_avatar_path", ""
            )

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(existing_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            ModernDialog.error(self, "错误", f"保存配置失败: {str(e)}")

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

    # ── UI 构建 ──────────────────────────────────────────────

    def initUI(self):
        self.setFixedWidth(480)

        if self.parent_manager:
            self.setFixedHeight(self.parent_manager.height())

        # 主容器 - Glassmorphism 风格
        container = QFrame()
        container.setObjectName("drawerContainer")
        container.setStyleSheet(f"""
            QFrame#drawerContainer {{
                background-color: rgba(30, 30, 40, 0.85);
                border-top-left-radius: 12px;
                border-bottom-left-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # ── 顶栏 ──
        container_layout.addWidget(self._build_title_bar())

        # ── 滚动区域 ──
        scroll_area = self._build_scroll_area()
        scroll_content = QWidget()
        scroll_content.setObjectName("scrollContent")
        scroll_content.setStyleSheet(
            "QWidget#scrollContent { background-color: transparent; }"
        )

        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(20, 8, 20, 20)
        layout.setSpacing(12)

        # ── 头像卡片 ──
        layout.addWidget(self._build_avatar_card())

        # ── Token 卡片 ──
        layout.addWidget(self._build_token_card())

        # ── MR 入口卡片 ──
        layout.addWidget(self._build_mr_card())

        layout.addStretch()

        scroll_area.setWidget(scroll_content)
        container_layout.addWidget(scroll_area, 1)  # 添加 stretch factor

        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(container)

    def _build_title_bar(self):
        """构建顶栏: 标题 + 关闭按钮"""
        title_bar = QFrame()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(56)
        title_bar.setStyleSheet("""
            QFrame#titleBar {
                background-color: transparent;
                border: none;
                border-top-left-radius: 12px;
            }
        """)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(24, 0, 16, 0)
        title_layout.setSpacing(0)

        title_label = QLabel("个人中心")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 700;
                color: {Colors.TEXT_PRIMARY};
                background: transparent;
                border: none;
            }}
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        close_btn = QPushButton()
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        IconManager.clear_cache()
        close_btn.setIcon(IconManager.get_icon("x", 14, "#FFFFFF"))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
        """)
        close_btn.clicked.connect(self.slide_out)
        title_layout.addWidget(close_btn)

        return title_bar

    def _build_scroll_area(self):
        """构建滚动区域"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            {Styles.SCROLL_BAR}
        """)
        return scroll_area

    def _build_avatar_card(self):
        """构建头像卡片: 居中大头像 + 用户名"""
        card = QFrame()
        card.setObjectName("avatarCard")
        card.setStyleSheet(f"""
            QFrame#avatarCard {{
                background-color: {Colors.SURFACE};
                border-radius: 10px;
                border: 1px solid {Colors.SURFACE_BORDER};
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 24, 20, 24)
        card_layout.setSpacing(12)

        # 头像居中
        self.avatar_widget = ClickableAvatar(size=80)
        self.avatar_widget.clicked.connect(self._on_avatar_clicked)

        custom_avatar = self.config.get("custom_avatar_path", "")
        if custom_avatar and os.path.exists(custom_avatar):
            self.avatar_widget.set_avatar_path(custom_avatar)

        card_layout.addWidget(self.avatar_widget, 0, Qt.AlignHCenter)

        # 用户名居中
        username = self.get_git_username()
        self.name_input = QLineEdit(username)
        self.name_input.setFixedHeight(32)
        self.name_input.setFixedWidth(200)
        self.name_input.setAlignment(Qt.AlignCenter)
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                font-size: 16px;
                font-weight: 600;
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid transparent;
                padding: 4px 8px;
                border-radius: 6px;
                background: transparent;
            }}
            QLineEdit:hover {{
                border: 1px solid rgba(255, 255, 255, 0.2);
                background: rgba(255, 255, 255, 0.05);
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(102, 126, 234, 0.6);
                background: rgba(255, 255, 255, 0.08);
            }}
        """)
        self.name_input.editingFinished.connect(self._auto_save)
        card_layout.addWidget(self.name_input, 0, Qt.AlignHCenter)

        # 提示文字居中（在名字下方）- 带 info 图标
        help_row = QWidget()
        help_row.setStyleSheet("background: transparent; border: none;")
        help_layout = QHBoxLayout(help_row)
        help_layout.setContentsMargins(0, 0, 0, 0)
        help_layout.setSpacing(4)

        info_icon_label = QLabel()
        info_icon_label.setPixmap(IconManager.get_pixmap("info", 12, Colors.TEXT_MUTED))
        info_icon_label.setStyleSheet("background: transparent; border: none;")
        help_layout.addWidget(info_icon_label)

        help_text = QLabel("修改名字将同步到 Git 本地配置")
        help_text.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {Colors.TEXT_MUTED};
                background: transparent;
                border: none;
            }}
        """)
        help_layout.addWidget(help_text)
        help_layout.addStretch()

        card_layout.addWidget(help_row, 0, Qt.AlignHCenter)

        return card

    def _build_token_card(self):
        """构建 Token 配置卡片"""
        card = QFrame()
        card.setObjectName("tokenCard")
        card.setStyleSheet(f"""
            QFrame#tokenCard {{
                background-color: {Colors.SURFACE};
                border-radius: 10px;
                border: 1px solid {Colors.SURFACE_BORDER};
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(0)

        # 区域标题
        section_title = QLabel("访问令牌")
        section_title.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: 600;
                color: {Colors.TEXT_LABEL};
                text-transform: uppercase;
                letter-spacing: 0.5px;
                background: transparent;
                border: none;
                padding-bottom: 8px;
            }}
        """)
        card_layout.addWidget(section_title)

        # ── GitLab Token ──
        card_layout.addWidget(
            self._build_token_row(
                label_text="GitLab Token",
                placeholder="输入 GitLab Personal Access Token",
                saved_value=self.config.get("gitlab_token", ""),
                attr_name="gitlab_token_input",
            )
        )

        # 说明
        gitlab_help = QLabel("用于创建 Merge Request  ·  权限: api, read_repository")
        gitlab_help.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {Colors.TEXT_MUTED};
                background: transparent;
                border: none;
                padding: 2px 0 12px 0;
            }}
        """)
        gitlab_help.setWordWrap(True)
        card_layout.addWidget(gitlab_help)

        # 分割线
        card_layout.addWidget(self._build_separator())

        # ── GitHub Token ──
        card_layout.addSpacing(12)
        card_layout.addWidget(
            self._build_token_row(
                label_text="GitHub Token",
                placeholder="输入 GitHub Personal Access Token",
                saved_value=self.config.get("github_token", ""),
                attr_name="github_token_input",
            )
        )

        github_help = QLabel("用于创建 Pull Request  ·  权限: repo, read:user")
        github_help.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {Colors.TEXT_MUTED};
                background: transparent;
                border: none;
                padding: 2px 0 8px 0;
            }}
        """)
        github_help.setWordWrap(True)
        card_layout.addWidget(github_help)

        # 链接
        token_links = QLabel(
            "<a href='https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html' "
            f"style='color:{Colors.BRANCH}; text-decoration:none;'>创建 GitLab Token</a>"
            "  ·  "
            "<a href='https://github.com/settings/tokens' "
            f"style='color:{Colors.BRANCH}; text-decoration:none;'>创建 GitHub Token</a>"
        )
        token_links.setOpenExternalLinks(True)
        token_links.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {Colors.BRANCH};
                background: transparent;
                border: none;
                padding: 4px 0 0 0;
            }}
        """)
        card_layout.addWidget(token_links)

        return card

    def _build_token_row(self, label_text, placeholder, saved_value, attr_name):
        """构建单个 Token 输入行"""
        row = QWidget()
        row.setStyleSheet("background: transparent; border: none;")
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)

        label = QLabel(label_text)
        label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 500;
                color: {Colors.TEXT_PRIMARY};
                background: transparent;
                border: none;
            }}
        """)
        row_layout.addWidget(label)

        # 输入框 + 显隐按钮
        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(8)

        token_input = QLineEdit()
        token_input.setPlaceholderText(placeholder)
        token_input.setEchoMode(QLineEdit.Password)
        token_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 7px 12px;
                background-color: rgba(255, 255, 255, 0.08);
                font-size: 13px;
                min-height: 20px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 2px solid rgba(102, 126, 234, 0.6);
                background-color: rgba(255, 255, 255, 0.12);
                padding: 6px 11px;
            }}
            QLineEdit::placeholder {{
                color: rgba(255, 255, 255, 0.4);
            }}
        """)
        if saved_value:
            token_input.setText(saved_value)
        token_input.editingFinished.connect(self._auto_save)

        # 保存引用
        setattr(self, attr_name, token_input)

        toggle_btn = QPushButton("显示")
        toggle_btn.setFixedSize(52, 34)
        toggle_btn.setCursor(Qt.PointingHandCursor)
        toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                font-size: 12px;
                color: {Colors.TEXT_SECONDARY};
                padding: 0 8px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.15);
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        toggle_btn.clicked.connect(
            lambda checked, inp=token_input, btn=toggle_btn: self._toggle_password(
                inp, btn
            )
        )

        input_row.addWidget(token_input)
        input_row.addWidget(toggle_btn)
        row_layout.addLayout(input_row)

        return row

    def _build_separator(self):
        """构建细分割线"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                max-height: 1px;
            }}
        """)
        line.setFixedHeight(1)
        return line

    def _build_mr_card(self):
        """构建 MR 入口卡片"""
        card = QFrame()
        card.setObjectName("mrCard")
        card.setStyleSheet(f"""
            QFrame#mrCard {{
                background-color: {Colors.SURFACE};
                border-radius: 10px;
                border: 1px solid {Colors.SURFACE_BORDER};
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # MR 入口行 - 用 QFrame + 点击事件实现
        mr_row = QFrame()
        mr_row.setObjectName("mrRow")
        mr_row.setFixedHeight(48)
        mr_row.setCursor(Qt.PointingHandCursor)
        mr_row.setStyleSheet("""
            QFrame#mrRow {
                background-color: transparent;
                border: none;
                border-radius: 10px;
            }
            QFrame#mrRow:hover {
                background-color: rgba(255, 255, 255, 0.08);
            }
        """)

        mr_layout = QHBoxLayout(mr_row)
        mr_layout.setContentsMargins(20, 0, 20, 0)
        mr_layout.setSpacing(8)

        mr_icon_label = QLabel()
        mr_icon_label.setPixmap(IconManager.get_pixmap("git-merge", 18, Colors.BRANCH))
        mr_icon_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        mr_layout.addWidget(mr_icon_label)

        mr_label = QLabel("查看我的 Merge Requests")
        mr_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {Colors.TEXT_PRIMARY};
                background: transparent;
                border: none;
            }}
        """)
        mr_layout.addWidget(mr_label)
        mr_layout.addStretch()

        arrow_label = QLabel()
        arrow_label.setPixmap(
            IconManager.get_pixmap("chevron-right", 18, Colors.TEXT_MUTED)
        )
        arrow_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        mr_layout.addWidget(arrow_label)

        # 整行可点击
        mr_row.mousePressEvent = lambda e: self.show_my_mrs()

        card_layout.addWidget(mr_row)

        return card

    def _toggle_password(self, input_widget, btn):
        """切换密码可见性"""
        if input_widget.echoMode() == QLineEdit.Password:
            input_widget.setEchoMode(QLineEdit.Normal)
            btn.setText("隐藏")
        else:
            input_widget.setEchoMode(QLineEdit.Password)
            btn.setText("显示")

    # ── 动画 ──────────────────────────────────────────────────

    def setup_animations(self):
        """设置动画"""
        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.OutCubic)

    def slide_in(self):
        """滑入动画"""
        if self._is_animating:
            return
        self._is_animating = True

        if self.parent_manager:
            parent_geo = self.parent_manager.geometry()

            # 更新尺寸 - 使用 parent 的实际内容区域高度
            target_height = self.parent_manager.height()
            self.setFixedHeight(target_height)

            # 遮罩覆盖整个父窗口内容区域
            self.overlay.setGeometry(0, 0, self.parent_manager.width(), target_height)
            self.overlay.fade_in()

            end_pos = QPoint(self.parent_manager.width() - self.width(), 0)
            start_pos = QPoint(self.parent_manager.width(), 0)

            self.move(start_pos)
            self.show()
            # 确保 z-order: overlay 在内容之上，drawer 在 overlay 之上
            self.overlay.raise_()
            self.raise_()

            self.slide_animation.setStartValue(start_pos)
            self.slide_animation.setEndValue(end_pos)

            try:
                self.slide_animation.finished.disconnect()
            except TypeError:
                pass
            self.slide_animation.finished.connect(self._on_slide_in_done)
            self.slide_animation.start()

    def _on_slide_in_done(self):
        self._is_animating = False

    def slide_out(self):
        """滑出动画"""
        if self._is_animating:
            return
        self._is_animating = True

        # 先自动保存
        self._do_auto_save()

        if self.parent_manager:
            end_pos = QPoint(self.parent_manager.width(), 0)
            start_pos = self.pos()

            # 淡出遮罩
            self.overlay.fade_out()

            self.slide_animation.setStartValue(start_pos)
            self.slide_animation.setEndValue(end_pos)

            try:
                self.slide_animation.finished.disconnect()
            except TypeError:
                pass
            self.slide_animation.finished.connect(self._on_slide_out_done)
            self.slide_animation.start()

    def _on_slide_out_done(self):
        self._is_animating = False
        self.hide()

    # ── 自动保存 ──────────────────────────────────────────────

    def _auto_save(self):
        """自动保存（输入框失焦时触发）"""
        self._do_auto_save()

    def _do_auto_save(self):
        """执行保存逻辑"""
        gitlab_token = self.gitlab_token_input.text().strip()
        github_token = self.github_token_input.text().strip()

        self.config["gitlab_token"] = gitlab_token
        self.config["github_token"] = github_token

        # 保存名称到 Git 配置
        new_name = self.name_input.text().strip()
        if new_name and new_name != self.get_git_username():
            from src.services.git_service import GitService

            GitService.set_username(new_name)

        # 保存配置文件
        self.save_config()

        # 同步更新主窗口
        self._sync_to_parent()

    def _sync_to_parent(self):
        """同步配置到主窗口"""
        if not self.parent_manager:
            return

        if hasattr(self.parent_manager, "personal_config"):
            self.parent_manager.personal_config["gitlab_token"] = self.config.get(
                "gitlab_token", ""
            )
            self.parent_manager.personal_config["github_token"] = self.config.get(
                "github_token", ""
            )
            self.parent_manager.personal_config["custom_avatar_path"] = self.config.get(
                "custom_avatar_path", ""
            )

        if hasattr(self.parent_manager, "avatar_btn"):
            custom_avatar = self.config.get("custom_avatar_path", "")
            self.parent_manager.avatar_btn.set_avatar_path(
                custom_avatar
                if custom_avatar and os.path.exists(custom_avatar)
                else None
            )

        if hasattr(self.parent_manager, "username_btn"):
            new_name = self.name_input.text().strip()
            if new_name:
                self.parent_manager.username_btn.setText(new_name)

    # ── 事件处理 ──────────────────────────────────────────────

    def _on_avatar_clicked(self):
        """头像点击处理"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择头像", "", "图片文件 (*.jpg *.jpeg *.png);;所有文件 (*)"
        )

        if file_path:
            self.avatar_widget.set_avatar_path(file_path)
            self.config["custom_avatar_path"] = file_path
            self._do_auto_save()

    def show_my_mrs(self):
        """显示我的 MR 对话框"""
        gitlab_token = self.gitlab_token_input.text().strip()

        if not gitlab_token:
            ModernDialog.warning(self, "提示", "请先配置 GitLab Token")
            return

        gitlab_host = "gitlab.corp.youdao.com"

        dialog = MyMRDialog(gitlab_token, gitlab_host, self.parent_manager)
        dialog.exec_()
