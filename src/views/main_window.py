import os
import re
import subprocess
import shutil
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QFileDialog,
    QLabel,
    QMessageBox,
    QCheckBox,
    QSplitter,
    QListWidgetItem,
    QLineEdit,
    QDialog,
    QTextEdit,
    QButtonGroup,
    QFrame,
)
from PyQt5.QtCore import (
    Qt,
    QProcess,
    QProcessEnvironment,
    QThread,
    pyqtSignal,
    QSize,
    QByteArray,
)
from PyQt5.QtGui import QColor, QPainter, QPixmap, QIcon
from PyQt5.QtSvg import QSvgRenderer

from src.views.dialogs.pod_config_dialog import PodConfigDialog
from src.views.dialogs.batch_tag_dialog import BatchTagDialog
from src.views.dialogs.batch_tag_switch_dialog import BatchTagSwitchDialog
from src.views.dialogs.branch_create_dialog import BranchCreateDialog
from src.views.dialogs.batch_branch_dialog import BatchBranchDialog
from src.widgets.loading_widget import LoadingWidget
from src.views.dialogs.merge_request_dialog import MergeRequestDialog, MRInfoCollector
from src.views.dialogs.personal_center_drawer import PersonalCenterDrawer
from src.views.dialogs.project_mr_dialog import ProjectMRDialog

from src.services import (
    ConfigService,
    PodService,
    GitService,
    PodInstallService,
    PodCacheService,
)
from src.components import AvatarButton
from src.utils.podfile_reader import PodfileReader
from src.styles.glassmorphism import GlassmorphismStyle, Styles, Colors


class RemoteTagLoader(QThread):
    """异步加载远程Tag的工作线程"""

    finished = pyqtSignal(list)

    def __init__(self, current_items, current_config, get_pod_name_func):
        super().__init__()
        self.current_items = current_items
        self.current_config = current_config
        self.get_pod_name_func = get_pod_name_func

    def run(self):
        # 将QListWidgetItem转换为pod名称列表
        pod_names = [self.get_pod_name_func(item) for item in self.current_items]
        pods_info = GitService.get_pods_info(
            pod_names, self.current_config, self.get_pod_name_func
        )
        self.finished.emit(pods_info)


class PodPilot(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config_service = ConfigService()
        self.pod_install_service = PodInstallService(log_callback=self.log_message)
        self.pod_cache_service = PodCacheService(log_callback=self.log_message)
        self.podfile_reader = None  # 将在选择项目时初始化

        self.personal_config = self._load_personal_config()

        self.initUI()
        self.set_modern_style()
        self._load_avatar()

        self.load_config()

    def _load_personal_config(self):
        """加载个人中心配置"""
        config_path = os.path.expanduser("~/.podpilot_config.json")
        try:
            if os.path.exists(config_path):
                import json

                with open(config_path, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _load_avatar(self):
        """加载自定义头像"""
        custom_avatar = self.personal_config.get("custom_avatar_path", "")
        if custom_avatar and os.path.exists(custom_avatar):
            self.avatar_btn.set_avatar_path(custom_avatar)

    def initUI(self):
        self.setWindowTitle("PodPilot")
        self.setGeometry(100, 100, 1200, 750)

        # macOS 透明标题栏，让渐变背景延伸到标题栏下方
        self._setup_transparent_titlebar()

        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局 - 增加顶部边距给标题栏留空间
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 48, 16, 16)
        main_layout.setSpacing(12)

        # 顶部栏 - Glassmorphism 卡片样式
        top_bar = QWidget()
        top_bar.setFixedHeight(56)
        top_bar.setStyleSheet(
            "background: rgba(255, 255, 255, 0.15); "
            "border: 1px solid rgba(255, 255, 255, 0.2); "
            "border-radius: 12px;"
        )
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(16, 10, 16, 10)
        top_bar_layout.setSpacing(12)

        # 左侧：Logo + 应用名称
        left_section = QWidget()
        left_section.setStyleSheet("background: transparent; border: none;")
        left_layout = QHBoxLayout(left_section)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # Logo
        logo_label = QLabel("P")
        logo_label.setFixedSize(32, 32)
        logo_label.setStyleSheet(
            "background: rgba(255, 255, 255, 0.25); "
            "border-radius: 8px; "
            "color: white; font-weight: bold; font-size: 14px;"
        )
        logo_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(logo_label)

        # 应用名称
        app_name = QLabel("PodPilot")
        app_name.setStyleSheet(
            "color: white; font-weight: 600; font-size: 15px; "
            "background: transparent; border: none;"
        )
        left_layout.addWidget(app_name)

        top_bar_layout.addWidget(left_section)
        top_bar_layout.addStretch()

        # 右侧：头像 + 用户名
        right_section = QWidget()
        right_section.setStyleSheet("background: transparent; border: none;")
        right_layout = QHBoxLayout(right_section)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self.avatar_btn = AvatarButton()
        self.avatar_btn.clicked.connect(self.toggle_personal_drawer)
        right_layout.addWidget(self.avatar_btn, 0, Qt.AlignVCenter)

        username = GitService.get_username()
        self.username_btn = QPushButton(username)
        self.username_btn.setCursor(Qt.PointingHandCursor)
        self.username_btn.clicked.connect(self.toggle_personal_drawer)
        self.username_btn.setStyleSheet(
            "background: transparent; border: none; "
            "color: rgba(255, 255, 255, 0.8); font-size: 13px; "
            "padding: 4px 8px;"
        )
        right_layout.addWidget(self.username_btn, 0, Qt.AlignVCenter)

        top_bar_layout.addWidget(right_section)
        main_layout.addWidget(top_bar)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧区域 - 项目管理
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(8)

        # 项目列表
        left_layout.addWidget(QLabel("项目列表:"))
        self.project_list = QListWidget()
        self.project_list.itemClicked.connect(self.on_project_selected)
        left_layout.addWidget(self.project_list, 1)

        # 项目操作按钮 - 第一行：添加/移除 + 一键操作
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        # 统一按钮高度
        left_btn_h = 32

        self.add_btn = QPushButton("添加项目")
        self.add_btn.setFixedHeight(left_btn_h)
        self.add_btn.clicked.connect(self.add_project)
        self.remove_btn = QPushButton("移除项目")
        self.remove_btn.setFixedHeight(left_btn_h)
        self.remove_btn.clicked.connect(self.remove_project)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)

        # 分隔符
        left_separator = QFrame()
        left_separator.setFrameShape(QFrame.VLine)
        left_separator.setFrameShadow(QFrame.Sunken)
        left_separator.setStyleSheet("color: rgba(255, 255, 255, 0.3);")
        left_separator.setFixedHeight(20)
        btn_layout.addWidget(left_separator)

        # 一键操作按钮组 - 统一宽度，使用 Glassmorphism 样式
        one_click_btn_w = 120

        self.one_click_tag_btn = QPushButton("一键Tag", left_widget)
        self.one_click_tag_btn.setToolTip(
            "自动筛选branch/git引用的Pod，批量切换到Tag引用"
        )
        self.one_click_tag_btn.setFixedSize(one_click_btn_w, left_btn_h)
        self.one_click_tag_btn.clicked.connect(self.one_click_tag_mode)
        self.one_click_tag_btn.setEnabled(False)
        btn_layout.addWidget(self.one_click_tag_btn)

        self.one_click_branch_btn = QPushButton("一键Branch", left_widget)
        self.one_click_branch_btn.setToolTip(
            "自动筛选tag引用的Pod，批量切换到Branch模式"
        )
        self.one_click_branch_btn.setFixedSize(one_click_btn_w, left_btn_h)
        self.one_click_branch_btn.clicked.connect(self.one_click_branch_mode)
        self.one_click_branch_btn.setEnabled(False)
        btn_layout.addWidget(self.one_click_branch_btn)

        self.one_click_mr_btn = QPushButton("一键MR", left_widget)
        self.one_click_mr_btn.setToolTip(
            "自动筛选branch/git引用的Pod，批量创建Merge Request"
        )
        self.one_click_mr_btn.setFixedSize(one_click_btn_w, left_btn_h)
        self.one_click_mr_btn.clicked.connect(self.one_click_mr_mode)
        self.one_click_mr_btn.setEnabled(False)
        btn_layout.addWidget(self.one_click_mr_btn)

        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)

        # 第二行：查看工程MR
        self.view_project_mr_btn = QPushButton("查看工程MR", left_widget)
        self.view_project_mr_btn.setToolTip("查看当前工程及其关联Pod的待合并MR")
        self.view_project_mr_btn.setFixedHeight(left_btn_h)
        self.view_project_mr_btn.clicked.connect(self.show_project_mrs)
        self.view_project_mr_btn.setEnabled(False)
        left_layout.addWidget(self.view_project_mr_btn)

        splitter.addWidget(left_widget)

        # 右侧区域 - Pod管理
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(8)

        # Pod列表
        right_layout.addWidget(QLabel("Pod 依赖列表:"))

        # 搜索框
        search_layout = QHBoxLayout()
        self.pod_search = QLineEdit()
        self.pod_search.setPlaceholderText("搜索 Pod...")
        self.pod_search.textChanged.connect(self.filter_pods)
        search_layout.addWidget(self.pod_search)
        right_layout.addLayout(search_layout)

        self.pod_list = QListWidget()
        self.pod_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.pod_list.setIconSize(QSize(34, 16))
        self.pod_list.itemDoubleClicked.connect(self.configure_pod)
        self.pod_list.itemSelectionChanged.connect(self.update_mode_buttons_state)
        self.pod_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                padding: 8px;
                outline: none;
            }
            QListWidget::item {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 0;
                margin: 2px 4px;
            }
            QListWidget::item:hover:!selected {
                background-color: rgba(255, 255, 255, 0.15);
            }
            QListWidget::item:selected {
                background-color: rgba(255, 255, 255, 0.25);
            }
        """)
        right_layout.addWidget(self.pod_list, 1)

        # Pod操作按钮 - 使用分段控制器布局
        # 独立功能按钮 + 分隔符 + 模式切换Segmented Control
        pod_btn_layout = QHBoxLayout()
        pod_btn_layout.setSpacing(6)

        # 统一按钮高度
        right_btn_h = 32

        self.config_pod_btn = QPushButton("配置")
        self.config_pod_btn.setFixedSize(80, right_btn_h)
        self.config_pod_btn.clicked.connect(self.configure_selected_pod)

        self.create_tag_btn = QPushButton("创建Tag")
        self.create_tag_btn.setFixedSize(80, right_btn_h)
        self.create_tag_btn.clicked.connect(self.create_tag_for_pod)

        self.clean_cache_btn = QPushButton("清理缓存")
        self.clean_cache_btn.setFixedSize(80, right_btn_h)
        self.clean_cache_btn.clicked.connect(self.clean_pod_cache)

        pod_btn_layout.addWidget(self.config_pod_btn)
        pod_btn_layout.addWidget(self.create_tag_btn)
        pod_btn_layout.addWidget(self.clean_cache_btn)

        # 分隔符
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setStyleSheet("color: rgba(255, 255, 255, 0.3);")
        separator1.setFixedHeight(20)
        pod_btn_layout.addWidget(separator1)

        # 模式切换 - Segmented Control（macOS 风格）
        self.mode_btn_group = QButtonGroup(self)
        self.mode_btn_group.setExclusive(True)

        # Segmented Control 容器，间距为0实现连续边框
        segment_container = QHBoxLayout()
        segment_container.setSpacing(0)

        self.to_dev_btn = QPushButton("开发模式")
        self.to_dev_btn.setCheckable(True)
        self.to_dev_btn.setFixedHeight(right_btn_h)
        self.to_dev_btn.setStyleSheet(Styles.SEGMENT_FIRST)
        self.to_dev_btn.clicked.connect(self.switch_to_dev_mode)
        self.mode_btn_group.addButton(self.to_dev_btn)

        self.to_branch_btn = QPushButton("Branch模式")
        self.to_branch_btn.setCheckable(True)
        self.to_branch_btn.setFixedHeight(right_btn_h)
        self.to_branch_btn.setStyleSheet(Styles.SEGMENT_MIDDLE)
        self.to_branch_btn.clicked.connect(self.switch_to_branch_mode)
        self.mode_btn_group.addButton(self.to_branch_btn)

        self.to_tag_btn = QPushButton("Tag模式")
        self.to_tag_btn.setCheckable(True)
        self.to_tag_btn.setFixedHeight(right_btn_h)
        self.to_tag_btn.setStyleSheet(Styles.SEGMENT_LAST)
        self.to_tag_btn.clicked.connect(self.switch_to_tag_mode)
        self.mode_btn_group.addButton(self.to_tag_btn)

        segment_container.addWidget(self.to_dev_btn)
        segment_container.addWidget(self.to_branch_btn)
        segment_container.addWidget(self.to_tag_btn)
        pod_btn_layout.addLayout(segment_container)

        # 分隔符
        separator = QLabel("|")
        separator.setStyleSheet(
            "color: rgba(255, 255, 255, 0.3); font-size: 14px; margin: 0 8px;"
        )
        pod_btn_layout.addWidget(separator)

        # 退出开发按钮 - 独立按钮
        self.exit_dev_btn = QPushButton("退出开发")
        self.exit_dev_btn.setFixedHeight(right_btn_h)
        self.exit_dev_btn.setFixedWidth(90)
        self.exit_dev_btn.clicked.connect(self.exit_dev_mode)
        self.exit_dev_btn.setEnabled(False)
        pod_btn_layout.addWidget(self.exit_dev_btn)

        pod_btn_layout.addStretch()
        right_layout.addLayout(pod_btn_layout)

        # 日志输出区域
        right_layout.addWidget(QLabel("操作日志:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(200)
        right_layout.addWidget(self.log_output)

        # 添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])

        # 状态栏
        self.statusBar().showMessage("准备就绪")

    def set_avatar(self, button):
        """设置默认头像 - 使用setIcon方式，避免绘制问题"""
        try:
            # 获取按钮的实际大小
            actual_size = button.size()
            width = actual_size.width()
            height = actual_size.height()
            size = min(width, height)  # 使用较小值确保圆形不会超出边界

            pixmap = QPixmap(size, size)
            pixmap.fill(QColor("transparent"))  # 透明背景

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # 绘制主圆形背景
            painter.setBrush(QColor("#007aff"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, size, size)

            # 根据按钮大小调整头像元素
            head_radius = int(size * 0.15)
            body_width = int(size * 0.3)
            body_height = int(size * 0.25)

            # 计算垂直居中位置
            avatar_total_height = head_radius * 2 + body_height
            avatar_top = (size - avatar_total_height) // 2

            # 计算水平居中位置
            head_x = (size - head_radius * 2) // 2
            head_y = avatar_top
            body_x = (size - body_width) // 2
            body_y = head_y + head_radius * 2

            # 绘制头像图案
            painter.setBrush(QColor("white"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(head_x, head_y, head_radius * 2, head_radius * 2)
            painter.drawEllipse(body_x, body_y, body_width, body_height)

            painter.end()

            # 设置图标并调整大小
            icon = QIcon(pixmap)
            button.setIcon(icon)
            button.setIconSize(QSize(size, size))
            button.setText("")  # 清除文字

        except Exception as e:
            # 出错时显示默认图标
            button.setText("👤")
            button.setStyleSheet(
                """
                QPushButton {
                    border: none;
                    border-radius: 18px;
                    background-color: #f0f0f5;
                    font-size: 20px;
                }
                QPushButton:hover {
                    background-color: #e0e5ff;
                }
            """
            )

    def get_pod_name_from_item(self, item):
        return item.data(Qt.UserRole) or ""

    def _get_pod_mode_from_item(self, item):
        mode = item.data(Qt.UserRole + 1)
        return mode if mode else "normal"

    def update_mode_buttons_state(self):
        selected_items = self.pod_list.selectedItems()

        if not selected_items:
            self.mode_btn_group.setExclusive(False)
            self.to_dev_btn.setChecked(False)
            self.to_branch_btn.setChecked(False)
            self.to_tag_btn.setChecked(False)
            self.mode_btn_group.setExclusive(True)
            self.exit_dev_btn.setEnabled(False)
            return

        modes = set()
        for item in selected_items:
            mode = self._get_pod_mode_from_item(item)
            modes.add(mode)

        # 更新 Segmented Control 选中状态
        self.mode_btn_group.setExclusive(False)

        if len(modes) == 1:
            # 不要用 pop()，它会移除元素！使用迭代器获取唯一元素
            mode = next(iter(modes))
            self.to_dev_btn.setChecked(False)
            self.to_branch_btn.setChecked(False)
            self.to_tag_btn.setChecked(False)

            if mode == "dev":
                self.to_dev_btn.setChecked(True)
            elif mode == "branch":
                self.to_branch_btn.setChecked(True)
            elif mode == "tag":
                self.to_tag_btn.setChecked(True)
        else:
            self.to_dev_btn.setChecked(False)
            self.to_branch_btn.setChecked(False)
            self.to_tag_btn.setChecked(False)

        self.mode_btn_group.setExclusive(True)

        # 退出开发按钮：仅当所有选中的 Pod 都是开发模式时启用
        has_dev_pods = "dev" in modes
        only_dev_pods = modes == {"dev"}
        self.exit_dev_btn.setEnabled(has_dev_pods and only_dev_pods)

    def get_current_pods_config(self):
        if not self.current_project:
            return {}
        return self.config_service.get_project_pods_config(self.current_project)

    def set_pod_config(self, pod_name, local_path):
        if self.current_project:
            self.config_service.set_pod_config(
                self.current_project, pod_name, local_path
            )

    def _setup_transparent_titlebar(self):
        """设置 macOS 透明标题栏"""
        import sys

        if sys.platform != "darwin":
            return

        try:
            from AppKit import (
                NSWindow,
                NSFullSizeContentViewWindowMask,
                NSWindowTitleHidden,
            )
            from ctypes import c_void_p

            # 获取 NSWindow
            ns_view = self.winId()

            # 使用 objc 获取窗口
            import objc

            ns_window = objc.objc_object(c_void_p=int(ns_view))

            # 从 NSView 获取 NSWindow
            ns_window = ns_window.window()

            # 设置透明标题栏
            style_mask = ns_window.styleMask()
            ns_window.setStyleMask_(style_mask | NSFullSizeContentViewWindowMask)
            ns_window.setTitlebarAppearsTransparent_(True)
            ns_window.setTitleVisibility_(NSWindowTitleHidden)
        except Exception as e:
            print(f"透明标题栏设置失败: {e}")

    def set_modern_style(self):
        """设置现代化UI样式 - Glassmorphism 风格"""
        self.setStyleSheet(GlassmorphismStyle.get_full_stylesheet())

    def closeEvent(self, event):
        """当窗口关闭时保存配置并处理线程"""
        # 等待MR信息收集线程完成
        if hasattr(self, "mr_info_loader") and self.mr_info_loader:
            try:
                if self.mr_info_loader.isRunning():
                    reply = QMessageBox.question(
                        self,
                        "确认",
                        "MR信息收集正在进行中，确定要关闭吗？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    if reply == QMessageBox.No:
                        event.ignore()
                        return
                    self.mr_info_loader.quit()
                    self.mr_info_loader.wait(2000)
            except RuntimeError:
                pass
        self.save_config()
        super().closeEvent(event)

    def save_config(self):
        self.config_service.save_config()

    def load_config(self):
        if self.config_service.load_config():
            if hasattr(self, "project_list"):
                for project in self.config_service.projects:
                    if "path" in project and os.path.exists(project["path"]):
                        item = QListWidgetItem(f"{project['name']} ({project['path']})")
                        item.setData(Qt.UserRole, project["path"])
                        self.project_list.addItem(item)

                if self.project_list.count() > 0:
                    first_item = self.project_list.item(0)
                    self.project_list.setCurrentItem(first_item)
                    self.on_project_selected(first_item)

            if self.config_service.current_project and os.path.exists(
                self.config_service.current_project
            ):
                self.current_project = self.config_service.current_project
                for i in range(self.project_list.count()):
                    item = self.project_list.item(i)
                    if item.data(Qt.UserRole) == self.current_project:
                        self.project_list.setCurrentItem(item)
                        self.load_pods(self.current_project)
                        break

    def add_project(self):
        project_dir = QFileDialog.getExistingDirectory(self, "选择iOS项目目录")
        if not project_dir:
            return

        podfile_path = os.path.join(project_dir, "Podfile")
        if not os.path.exists(podfile_path):
            QMessageBox.warning(self, "警告", f"所选目录未找到Podfile: {podfile_path}")
            return

        project_name = os.path.basename(project_dir)
        self.config_service.add_project(project_name, project_dir)

        item = QListWidgetItem(f"{project_name} ({project_dir})")
        item.setData(Qt.UserRole, project_dir)
        self.project_list.addItem(item)

        self.log_message(f"已添加项目: {project_name}")

    def remove_project(self):
        current_item = self.project_list.currentItem()
        if current_item:
            project_dir = current_item.data(Qt.UserRole)
            row = self.project_list.row(current_item)
            self.project_list.takeItem(row)
            self.config_service.remove_project(project_dir)

            self.log_message(f"已移除项目: {os.path.basename(project_dir)}")

            if self.current_project == project_dir:
                self.current_project = None
                self.pod_list.clear()

    def on_project_selected(self, item):
        project_dir = item.data(Qt.UserRole)
        self.current_project = project_dir
        self.load_pods(project_dir)

        self.one_click_tag_btn.setEnabled(True)
        self.one_click_branch_btn.setEnabled(True)
        self.one_click_mr_btn.setEnabled(True)
        self.view_project_mr_btn.setEnabled(True)

        self.save_config()

    def _render_svg_icon(self, icon_path, size=16, color=None):
        """将SVG图标渲染为QPixmap
        Args:
            icon_path: SVG文件路径
            size: 图标大小
            color: 图标填充颜色（如 "#34c759"），如果提供会替换SVG中的fill属性
        Returns:
            QPixmap对象
        """
        try:
            if not os.path.exists(icon_path):
                return None

            # 读取SVG文件内容
            with open(icon_path, "r", encoding="utf-8") as f:
                svg_content = f.read()

            # 如果指定了颜色，替换SVG中的fill属性
            if color and "#1296db" in svg_content:
                svg_content = re.sub(r'fill="#1296db"', f'fill="{color}"', svg_content)

            # 将替换后的内容转换为QByteArray
            svg_bytes = svg_content.encode("utf-8")
            svg_data = QByteArray(svg_bytes)

            renderer = QSvgRenderer(svg_data)
            if not renderer.isValid():
                return None

            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()

            return pixmap
        except Exception:
            return None

    def _build_pod_icon(
        self, type_icon_name, is_configured, icon_size=16, spacing=2, color=None
    ):
        """构建Pod图标，支持类型图标和已配置图标同时显示
        Args:
            type_icon_name: 类型图标名称 (branch, tag_fill等)，None表示无类型图标
            is_configured: 是否已配置
            icon_size: 单个图标大小
            spacing: 图标间距
            color: 图标颜色
        Returns:
            QIcon对象
        """
        type_pixmap = None
        config_pixmap = None

        if type_icon_name:
            type_pixmap = self._render_svg_icon(
                self._get_icon_path(type_icon_name), icon_size, color
            )
        if is_configured:
            config_pixmap = self._render_svg_icon(
                self._get_icon_path("configed"), icon_size, color
            )

        if not type_pixmap and not config_pixmap:
            return None

        # 只有一个图标
        if type_pixmap and not config_pixmap:
            return QIcon(type_pixmap)
        if config_pixmap and not type_pixmap:
            return QIcon(config_pixmap)

        # 两个图标合并，已配置图标在前
        total_width = icon_size * 2 + spacing
        combined = QPixmap(total_width, icon_size)
        combined.fill(Qt.transparent)

        painter = QPainter(combined)
        painter.drawPixmap(0, 0, config_pixmap)
        painter.drawPixmap(icon_size + spacing, 0, type_pixmap)
        painter.end()

        return QIcon(combined)

    def _get_icon_path(self, icon_name):
        """获取图标文件路径
        Args:
            icon_name: 图标名称 (branch, configed, tag_fill等)
        Returns:
            图标完整路径
        """
        # __file__ = src/views/main_window.py -> src/views -> src -> 项目根目录
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        return os.path.join(project_root, "resources", "icons", f"{icon_name}.svg")

    def load_pods(self, project_dir):
        self.pod_list.clear()

        pods, dev_pods, tag_pods, branch_pods, git_pods = (
            PodService.load_pods_from_podfile(os.path.join(project_dir, "Podfile"))
        )

        podfile_path = os.path.join(project_dir, "Podfile")
        try:
            with open(podfile_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            original_pod_references = PodService.save_original_pod_references(
                lines, project_dir, dev_pods
            )

            for pod_name, line_info in original_pod_references.items():
                self.config_service.save_original_pod_reference(
                    project_dir,
                    pod_name,
                    line_info["line"],
                    line_info["full_declaration"],
                )

        except Exception as e:
            self.log_message(f"保存原始Pod引用失败: {str(e)}")

        current_project_config = self.get_current_pods_config()

        pod_list_with_priority = []
        for pod in pods:
            priority = PodService.get_pod_priority(
                pod, dev_pods, branch_pods, tag_pods, git_pods, current_project_config
            )
            pod_list_with_priority.append((pod, priority))

        pod_list_with_priority.sort(key=lambda x: (x[1], pods.index(x[0])))

        badge_map = {
            1: ("DEV", Colors.DEV),
            2: ("BRANCH", Colors.BRANCH),
            3: ("TAG", Colors.TAG),
            4: ("GIT", Colors.GIT),
        }

        for pod, priority in pod_list_with_priority:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, pod)

            is_configured = pod in current_project_config
            mode = (
                "dev"
                if priority == 1
                else (
                    "branch"
                    if priority == 2
                    else (
                        "tag"
                        if priority == 3
                        else ("git" if priority == 4 else "normal")
                    )
                )
            )
            item.setData(Qt.UserRole + 1, mode)

            row_widget = QWidget()
            row_widget.setStyleSheet("background: transparent; border: none;")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(12, 8, 12, 8)
            row_layout.setSpacing(8)

            if is_configured:
                icon_path = self._get_icon_path("configed")
                if os.path.exists(icon_path):
                    renderer = QSvgRenderer(icon_path)
                    if renderer.isValid():
                        default_size = renderer.defaultSize()
                        pixmap = QPixmap(default_size)
                        pixmap.fill(Qt.transparent)
                        painter = QPainter(pixmap)
                        renderer.render(painter)
                        painter.end()
                        icon_label = QLabel()
                        icon_label.setPixmap(
                            pixmap.scaled(
                                16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation
                            )
                        )
                        icon_label.setStyleSheet(
                            "background: transparent; border: none; padding: 0; margin: 0; opacity: 0.7;"
                        )
                        row_layout.addWidget(icon_label)

            name_label = QLabel(pod)
            name_label.setStyleSheet(
                f"color: {Colors.TEXT_PRIMARY}; font-size: 13px; "
                "background: transparent; border: none; padding: 0;"
            )
            row_layout.addWidget(name_label)

            row_layout.addStretch()

            badge_info = badge_map.get(priority)
            if badge_info:
                badge_text, badge_color = badge_info
                r, g, b = (
                    int(badge_color[1:3], 16),
                    int(badge_color[3:5], 16),
                    int(badge_color[5:7], 16),
                )
                badge = QLabel(badge_text)
                badge.setFixedHeight(18)
                badge.setStyleSheet(
                    f"background-color: rgba({r}, {g}, {b}, 0.4); "
                    f"color: white; "
                    "padding: 0px 8px; border-radius: 4px; "
                    "font-size: 11px; font-weight: 500; border: none;"
                )
                row_layout.addWidget(badge, 0, Qt.AlignVCenter)

            # 设置 item 高度
            item.setSizeHint(QSize(0, 36))
            self.pod_list.addItem(item)
            self.pod_list.setItemWidget(item, row_widget)

        self.log_message(f"已加载 {len(pods)} 个Pod")
        self.update_mode_buttons_state()

    def filter_pods(self):
        search_text = self.pod_search.text().lower()
        for i in range(self.pod_list.count()):
            item = self.pod_list.item(i)
            pod_name = item.data(Qt.UserRole).lower()
            if search_text in pod_name:
                item.setHidden(False)
            else:
                item.setHidden(True)

    def configure_selected_pod(self):
        current_items = self.pod_list.selectedItems()
        if not current_items:
            QMessageBox.warning(self, "警告", "请先选择要配置的Pod")
            return

        for item in current_items:
            self.configure_pod(item)

    def configure_pod(self, item):
        pod_name = self.get_pod_name_from_item(item)
        current_config = self.get_current_pods_config()
        local_path = current_config.get(pod_name, "")

        dialog = PodConfigDialog(pod_name, local_path)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            new_local_path = dialog.get_local_path()
            self.set_pod_config(pod_name, new_local_path)
            self.save_config()

            if self.current_project:
                self.load_pods(self.current_project)

    def switch_to_dev_mode(self):
        if not self.current_project:
            QMessageBox.warning(self, "警告", "请先选择项目")
            return

        current_items = self.pod_list.selectedItems()
        if not current_items:
            QMessageBox.warning(self, "警告", "请先选择要切换的Pod")
            return

        podfile_path = os.path.join(self.current_project, "Podfile")
        if not os.path.exists(podfile_path):
            QMessageBox.warning(self, "错误", "未找到Podfile")
            return

        selected_pod_names = [
            self.get_pod_name_from_item(item) for item in current_items
        ]

        try:
            with open(podfile_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            new_lines = lines.copy()
            current_config = self.get_current_pods_config()

            for item in current_items:
                pod_name = self.get_pod_name_from_item(item)

                _, _, full_declaration = PodService.get_full_pod_declaration(
                    lines, pod_name
                )
                if full_declaration:
                    mode_info = PodService.extract_pod_mode_info(full_declaration)

                    if mode_info["mode"] != "dev" and mode_info["mode"] != "normal":
                        self.config_service.save_last_pod_mode(
                            self.current_project,
                            pod_name,
                            mode_info["mode"],
                            mode_info["data"],
                        )

                if pod_name not in current_config:
                    QMessageBox.warning(self, "警告", f"未配置 {pod_name} 的本地路径")
                    continue

                local_path = current_config[pod_name]
                new_lines, modified = PodService.switch_pod_mode(
                    new_lines, pod_name, "dev", local_path
                )

                if modified:
                    self.log_message(f"已将 {pod_name} 切换到开发模式")

            with open(podfile_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            self.load_pods(self.current_project)

            for i in range(self.pod_list.count()):
                item = self.pod_list.item(i)
                pod_name = self.get_pod_name_from_item(item)
                if pod_name in selected_pod_names:
                    item.setSelected(True)

            reply = QMessageBox.question(
                self,
                "确认",
                "已切换到开发模式，是否执行 pod install?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.run_pod_install()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"切换失败: {str(e)}")

    def switch_to_normal_mode(self):
        if not self.current_project:
            QMessageBox.warning(self, "警告", "请先选择项目")
            return

        current_items = self.pod_list.selectedItems()
        if not current_items:
            QMessageBox.warning(self, "警告", "请先选择要切换的Pod")
            return

        podfile_path = os.path.join(self.current_project, "Podfile")
        if not os.path.exists(podfile_path):
            QMessageBox.warning(self, "错误", "未找到Podfile")
            return

        try:
            with open(podfile_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            new_lines = []
            for line in lines:
                new_lines.append(line)

            for item in current_items:
                pod_name = self.get_pod_name_from_item(item)

                original_pod_reference = self.config_service.get_original_pod_reference(
                    self.current_project, pod_name
                )
                if not original_pod_reference:
                    self.log_message(f"未找到 {pod_name} 的原始引用，跳过")
                    continue

                original_line = original_pod_reference["line"]
                new_lines, modified = PodService.switch_pod_mode(
                    new_lines, pod_name, "normal", original_line=original_line
                )

                if modified:
                    self.log_message(f"已将 {pod_name} 恢复为正常模式")

            with open(podfile_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            self.load_pods(self.current_project)

            reply = QMessageBox.question(
                self,
                "确认",
                "已恢复为正常模式，是否执行 pod install?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.run_pod_install()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"切换失败: {str(e)}")

    def exit_dev_mode(self):
        """退出开发模式，恢复到上次的模式"""
        if not self.current_project:
            QMessageBox.warning(self, "警告", "请先选择项目")
            return

        current_items = self.pod_list.selectedItems()
        if not current_items:
            QMessageBox.warning(self, "警告", "请先选择要切换的Pod")
            return

        podfile_path = os.path.join(self.current_project, "Podfile")
        if not os.path.exists(podfile_path):
            QMessageBox.warning(self, "错误", "未找到Podfile")
            return

        try:
            with open(podfile_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            new_lines = lines.copy()
            restored_count = 0

            for item in current_items:
                pod_name = self.get_pod_name_from_item(item)

                current_mode = self._get_pod_mode_from_item(item)
                if current_mode != "dev":
                    self.log_message(f"{pod_name} 不在开发模式，跳过")
                    continue

                last_mode_info = self.config_service.get_last_pod_mode(
                    self.current_project, pod_name
                )

                original_reference = self.config_service.get_original_pod_reference(
                    self.current_project, pod_name
                )

                if last_mode_info:
                    mode = last_mode_info["mode"]
                    mode_data = last_mode_info["data"]
                    original_line = (
                        original_reference["line"] if original_reference else None
                    )

                    new_lines, modified = PodService.restore_pod_to_mode(
                        new_lines, pod_name, mode, mode_data, original_line
                    )

                    if modified:
                        self.log_message(f"已将 {pod_name} 恢复到{mode}模式")
                        restored_count += 1
                    else:
                        self.log_message(f"{pod_name} 恢复失败")

                elif original_reference:
                    original_line = original_reference["line"]
                    new_lines, modified = PodService.switch_pod_mode(
                        new_lines, pod_name, "normal", original_line=original_line
                    )

                    if modified:
                        self.log_message(f"已将 {pod_name} 恢复到原始引用")
                        restored_count += 1
                else:
                    self.log_message(
                        f"{pod_name} 无法退出开发模式：缺少上次模式记录和原始引用"
                    )

            with open(podfile_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            self.load_pods(self.current_project)

            if restored_count > 0:
                reply = QMessageBox.question(
                    self,
                    "确认",
                    f"已退出开发模式（{restored_count}个Pod），是否执行 pod install?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    self.run_pod_install()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"退出开发模式失败: {str(e)}")

    def create_tag_for_pod(self):
        current_items = self.pod_list.selectedItems()
        if not current_items:
            QMessageBox.warning(self, "警告", "请先选择要创建标签的Pod")
            return

        current_config = self.get_current_pods_config()
        pods_info = []

        for item in current_items:
            pod_name = self.get_pod_name_from_item(item)

            if pod_name not in current_config:
                self.log_message(f"未配置 {pod_name} 的本地路径，跳过")
                continue

            local_path = current_config[pod_name]
            if not os.path.exists(local_path):
                self.log_message(f"本地路径不存在: {local_path}，跳过 {pod_name}")
                continue

            branches = GitService.get_branches(local_path)
            current_branch = GitService.get_current_branch(local_path)

            pods_info.append(
                {
                    "name": pod_name,
                    "path": local_path,
                    "branches": branches,
                    "current_branch": current_branch,
                }
            )

        if not pods_info:
            QMessageBox.warning(self, "警告", "没有可创建Tag的Pod")
            return

        dialog = BatchTagDialog(pods_info, self)
        if dialog.exec_() == QDialog.Accepted:
            self.log_message("批量创建Tag完成")

    def switch_to_branch_mode(self):
        """切换到Branch模式"""
        if not self.current_project:
            QMessageBox.warning(self, "警告", "请先选择项目")
            return

        current_items = self.pod_list.selectedItems()
        if not current_items:
            QMessageBox.warning(self, "警告", "请先选择要切换的Pod")
            return

        podfile_path = os.path.join(self.current_project, "Podfile")
        if not os.path.exists(podfile_path):
            QMessageBox.warning(self, "错误", "未找到Podfile")
            return

        current_config = self.get_current_pods_config()
        pods_info = []

        for item in current_items:
            pod_name = self.get_pod_name_from_item(item)

            if pod_name not in current_config:
                self.log_message(f"未配置 {pod_name} 的本地路径，跳过")
                continue

            local_path = current_config[pod_name]
            if not os.path.exists(local_path):
                self.log_message(f"本地路径不存在: {local_path}，跳过 {pod_name}")
                continue

            branches = GitService.get_branches(local_path)
            current_branch = GitService.get_current_branch(local_path)

            pods_info.append(
                {
                    "name": pod_name,
                    "path": local_path,
                    "branches": branches,
                    "current_branch": current_branch,
                }
            )

        if not pods_info:
            QMessageBox.warning(self, "警告", "没有可切换到Branch模式的Pod")
            return

        dialog = BatchBranchDialog(pods_info, podfile_path, None, self)
        if dialog.exec_() == QDialog.Accepted:
            # 记录分支模式切换历史
            for pod_info in pods_info:
                if pod_info.get("selected_branch"):
                    self.log_message("批量切换到Branch模式完成")
            self.load_pods(self.current_project)

            reply = QMessageBox.question(
                self,
                "确认",
                "已切换到Branch模式，是否执行 pod install?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.run_pod_install()

    def switch_to_tag_mode(self):
        """切换到Tag模式"""
        if not self.current_project:
            QMessageBox.warning(self, "警告", "请先选择项目")
            return

        current_items = self.pod_list.selectedItems()
        if not current_items:
            QMessageBox.warning(self, "警告", "请先选择要切换的Pod")
            return

        podfile_path = os.path.join(self.current_project, "Podfile")
        if not os.path.exists(podfile_path):
            QMessageBox.warning(self, "错误", "未找到Podfile")
            return

        # 读取Podfile内容
        try:
            with open(podfile_path, "r") as f:
                podfile_lines = f.readlines()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取Podfile失败: {str(e)}")
            return

        # 创建loading对话框
        loading_dialog = QDialog(self)
        loading_dialog.setWindowTitle("加载中")
        loading_dialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint)
        loading_dialog.setFixedSize(200, 100)
        loading_dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f5f7;
                border-radius: 12px;
            }
        """)

        loading_layout = QVBoxLayout()
        loading_layout.setContentsMargins(20, 20, 20, 20)

        # 使用LoadingWidget
        self.loading_widget = LoadingWidget("加载远程Tag...")
        loading_layout.addWidget(self.loading_widget)

        loading_dialog.setLayout(loading_layout)
        loading_dialog.show()

        # 开始动画
        self.loading_widget.start_animation()

        # 获取当前Pod配置
        current_config = self.get_current_pods_config()

        # 创建异步加载工作线程
        self.tag_loader = RemoteTagLoader(
            current_items, current_config, self.get_pod_name_from_item
        )
        self.tag_loader.finished.connect(
            lambda pods_info: self._on_tags_loaded(
                pods_info, podfile_path, podfile_lines, loading_dialog
            )
        )

        # 启动工作线程
        self.tag_loader.start()

    def _on_tags_loaded(self, pods_info, podfile_path, podfile_lines, loading_dialog):
        """处理Tag数据加载完成"""
        # 清理线程引用
        if hasattr(self, "tag_loader"):
            self.tag_loader = None

        # 停止loading动画
        if hasattr(self, "loading_widget"):
            self.loading_widget.stop_animation()

        loading_dialog.close()

        if not pods_info:
            QMessageBox.warning(self, "警告", "没有可切换的Pod")
            return

        # 使用批量Tag切换对话框
        dialog = BatchTagSwitchDialog(pods_info, podfile_path, podfile_lines, self)
        if dialog.exec_() == QDialog.Accepted:
            self.log_message("批量切换Tag完成")
            # 重新加载Pod列表
            self.load_pods(self.current_project)

            # 询问是否执行pod install
            reply = QMessageBox.question(
                self,
                "确认",
                f"已切换 {len(pods_info)} 个Pod到标签模式，是否执行 pod install?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.run_pod_install()

    def _switch_to_tag_mode_with_items(self, selected_items):
        """使用指定的items进行Tag切换"""
        # 临时设置pod_list的选择状态
        self.pod_list.clearSelection()
        for item in selected_items:
            item.setSelected(True)

        # 调用原始的switch_to_tag_mode方法
        self.switch_to_tag_mode()

    def _get_branch_pods(self, project_dir):
        podfile_path = os.path.join(project_dir, "Podfile")
        if not os.path.exists(podfile_path):
            return []

        pods, dev_pods, tag_pods, branch_pods, git_pods = (
            PodService.load_pods_from_podfile(podfile_path)
        )
        return branch_pods

    def _get_tag_pods(self, project_dir):
        """获取所有使用:tag引用的Pod"""
        podfile_path = os.path.join(project_dir, "Podfile")
        if not os.path.exists(podfile_path):
            return []

        pods, dev_pods, tag_pods, branch_pods, git_pods = (
            PodService.load_pods_from_podfile(podfile_path)
        )
        return tag_pods

    def one_click_tag_mode(self):
        """一键Tag模式：自动筛选所有branch引用的pod并批量切换到Tag"""
        if not self.current_project:
            QMessageBox.warning(self, "警告", "请先选择项目")
            return

        # 获取所有branch引用的pod
        target_pods = self._get_branch_pods(self.current_project)
        if not target_pods:
            QMessageBox.information(
                self, "提示", "当前项目中没有发现使用branch引用的Pod"
            )
            return

        # 检查每个Pod是否有配置
        current_config = self.get_current_pods_config()
        configured_pods = []
        unconfigured_pods = []

        for pod_name in target_pods:
            if pod_name in current_config:
                configured_pods.append(pod_name)
            else:
                unconfigured_pods.append(pod_name)

        # 如果有未配置的Pod，必须先配置
        if unconfigured_pods:
            msg = f"发现 {len(unconfigured_pods)} 个branch Pod没有配置本地路径:\n\n"
            msg += "\n".join(f"• {pod}" for pod in unconfigured_pods)
            msg += f"\n\n请先为这些Pod配置本地路径，然后再使用一键Tag功能。"

            # 选择所有未配置的Pod，方便用户配置
            self.pod_list.clearSelection()
            for pod_name in unconfigured_pods:
                for i in range(self.pod_list.count()):
                    item = self.pod_list.item(i)
                    if self.get_pod_name_from_item(item) == pod_name:
                        item.setSelected(True)
                        break

            # 询问是否立即配置
            reply = QMessageBox.question(
                self,
                "配置检查",
                msg + "\n\n是否立即配置这些Pod?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.configure_selected_pod()
            return

        if not configured_pods:
            return

        # 自动选择已配置的pod
        self.pod_list.clearSelection()
        selected_items = []

        for i in range(self.pod_list.count()):
            item = self.pod_list.item(i)
            pod_name = self.get_pod_name_from_item(item)
            if pod_name in configured_pods:
                item.setSelected(True)
                selected_items.append(item)

        self.log_message(
            f"一键Tag: 成功选择 {len(selected_items)} 个已配置的Pod进行Tag切换"
        )

        if not selected_items:
            QMessageBox.warning(self, "警告", "未能自动选择branch引用的Pod")
            return

        # 显示选择结果
        reply = QMessageBox.question(
            self,
            "一键Tag",
            f"已自动选择 {len(selected_items)} 个branch引用的Pod:\n\n"
            + "\n".join(
                [f"• {self.get_pod_name_from_item(item)}" for item in selected_items]
            )
            + "\n\n是否立即进入Tag切换模式?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # 直接调用switch_to_tag_mode，传递选中的items
            self._switch_to_tag_mode_with_items(selected_items)

    def one_click_branch_mode(self):
        """一键Branch模式：自动筛选所有tag引用的pod并批量切换到Branch"""
        if not self.current_project:
            QMessageBox.warning(self, "警告", "请先选择项目")
            return

        # 获取所有tag引用的pod
        target_pods = self._get_tag_pods(self.current_project)
        if not target_pods:
            QMessageBox.information(self, "提示", "当前项目中没有发现使用tag引用的Pod")
            return

        # 检查每个Pod是否有配置
        current_config = self.get_current_pods_config()
        configured_pods = []
        unconfigured_pods = []

        for pod_name in target_pods:
            if pod_name in current_config:
                configured_pods.append(pod_name)
            else:
                unconfigured_pods.append(pod_name)

        # 如果有未配置的Pod，必须先配置
        if unconfigured_pods:
            msg = f"发现 {len(unconfigured_pods)} 个tag Pod没有配置本地路径:\n\n"
            msg += "\n".join([f"• {pod}" for pod in unconfigured_pods[:5]])
            if len(unconfigured_pods) > 5:
                msg += f"\n... 还有 {len(unconfigured_pods) - 5} 个"

            reply = QMessageBox.question(
                self,
                "配置检查",
                msg + "\n\n是否立即配置这些Pod?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.configure_selected_pod()
            return

        if not configured_pods:
            return

        # 自动选择已配置的pod
        self.pod_list.clearSelection()
        selected_items = []

        for i in range(self.pod_list.count()):
            item = self.pod_list.item(i)
            pod_name = self.get_pod_name_from_item(item)
            if pod_name in configured_pods:
                item.setSelected(True)
                selected_items.append(item)

        self.log_message(
            f"一键Branch: 成功选择 {len(selected_items)} 个已配置的Pod进行Branch切换"
        )

        if not selected_items:
            QMessageBox.warning(self, "警告", "未能自动选择tag引用的Pod")
            return

        # 显示选择结果
        reply = QMessageBox.question(
            self,
            "一键Branch",
            f"已自动选择 {len(selected_items)} 个tag引用的Pod:\n\n"
            + "\n".join(
                [f"• {self.get_pod_name_from_item(item)}" for item in selected_items]
            )
            + "\n\n是否立即进入Branch切换模式?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # 直接调用switch_to_branch_mode
            self.switch_to_branch_mode()

    def one_click_mr_mode(self):
        """一键MR模式：自动筛选所有branch引用的pod并批量创建Merge Request"""
        if not self.current_project:
            QMessageBox.warning(self, "警告", "请先选择项目")
            return

        # 获取所有branch引用的pod
        target_pods = self._get_branch_pods(self.current_project)
        if not target_pods:
            QMessageBox.information(
                self, "提示", "当前项目中没有发现使用branch引用的Pod"
            )
            return

        # 检查每个Pod是否有配置
        current_config = self.get_current_pods_config()
        configured_pods = []
        unconfigured_pods = []

        for pod_name in target_pods:
            if pod_name in current_config:
                configured_pods.append(pod_name)
            else:
                unconfigured_pods.append(pod_name)

        # 如果有未配置的Pod，必须先配置
        if unconfigured_pods:
            msg = f"发现 {len(unconfigured_pods)} 个branch Pod没有配置本地路径:\n\n"
            msg += "\n".join(f"• {pod}" for pod in unconfigured_pods)
            msg += f"\n\n请先为这些Pod配置本地路径，然后再使用一键MR功能。"

            # 选择所有未配置的Pod，方便用户配置
            self.pod_list.clearSelection()
            for pod_name in unconfigured_pods:
                for i in range(self.pod_list.count()):
                    item = self.pod_list.item(i)
                    if self.get_pod_name_from_item(item) == pod_name:
                        item.setSelected(True)
                        break

            # 询问是否立即配置
            reply = QMessageBox.question(
                self,
                "配置检查",
                msg + "\n\n是否立即配置这些Pod?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.configure_selected_pod()
            return

        if not configured_pods:
            return

        # 自动选择已配置的pod
        self.pod_list.clearSelection()
        selected_items = []

        for i in range(self.pod_list.count()):
            item = self.pod_list.item(i)
            pod_name = self.get_pod_name_from_item(item)
            if pod_name in configured_pods:
                item.setSelected(True)
                selected_items.append(item)

        self.log_message(
            f"一键MR: 成功选择 {len(selected_items)} 个已配置的Pod进行MR创建"
        )

        if not selected_items:
            QMessageBox.warning(self, "警告", "未能自动选择branch引用的Pod")
            return

        # 创建loading对话框并保存为实例变量以防止被垃圾回收
        self.loading_dialog = QDialog(self)
        self.loading_dialog.setWindowTitle("加载中")
        self.loading_dialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint)
        self.loading_dialog.setFixedSize(200, 100)
        self.loading_dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f5f7;
                border-radius: 12px;
            }
        """)

        loading_layout = QVBoxLayout()
        loading_layout.setContentsMargins(20, 20, 20, 20)

        # 使用LoadingWidget
        self.loading_widget = LoadingWidget("加载Pod MR信息...")
        loading_layout.addWidget(self.loading_widget)

        self.loading_dialog.setLayout(loading_layout)
        self.loading_dialog.show()

        # 开始动画
        self.loading_widget.start_animation()

        # 收集Pod信息
        pods_info_dict = {}
        for item in selected_items:
            pod_name = self.get_pod_name_from_item(item)
            local_path = current_config.get(pod_name, "")
            pods_info_dict[pod_name] = local_path

        # 获取主工程的当前分支和远程URL
        main_project_current_branch = None
        main_project_git_url = None
        try:
            # 获取主工程当前分支
            import subprocess

            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.current_project,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if branch_result.returncode == 0:
                main_project_current_branch = branch_result.stdout.strip()

            # 获取主工程远程URL
            url_result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.current_project,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if url_result.returncode == 0:
                main_project_git_url = url_result.stdout.strip()

        except Exception as e:
            self.log_message(f"获取主工程信息失败: {str(e)}")

        # 创建异步加载工作线程并保存为实例变量以防止被垃圾回收
        self.mr_info_loader = MRInfoCollector(
            configured_pods,
            current_config,
            self.current_project,
            main_project_current_branch=main_project_current_branch,
            main_project_git_url=main_project_git_url,
        )
        self.mr_info_loader.finished.connect(
            lambda mr_info: self._on_mr_info_loaded(mr_info)
        )
        self.mr_info_loader.error_occurred.connect(
            lambda error_msg: self._on_mr_info_error(error_msg)
        )

        # 启动工作线程
        self.mr_info_loader.start()

    def _on_mr_info_loaded(self, mr_info):
        """处理MR信息加载完成"""
        try:
            # 清理线程引用
            if hasattr(self, "mr_info_loader"):
                self.mr_info_loader = None

            # 停止loading动画
            if hasattr(self, "loading_widget") and self.loading_widget is not None:
                self.loading_widget.stop_animation()
                self.loading_widget = None

            # 关闭loading对话框并清理引用
            if hasattr(self, "loading_dialog") and self.loading_dialog is not None:
                self.loading_dialog.close()
                self.loading_dialog = None

            # 过滤掉有错误的Pod，并提取主工程信息
            valid_pods_info = {}
            main_project_info = None

            for pod_name, info in mr_info.items():
                if info.get("is_main_project"):
                    main_project_info = info
                elif "error" not in info:
                    valid_pods_info[pod_name] = info
                else:
                    self.log_message(f"{pod_name}: {info['error']}")

            if not valid_pods_info and not main_project_info:
                QMessageBox.warning(self, "警告", "没有可用的Pod信息")
                return

            # 使用MR对话框，传入config以加载Token（重新加载最新配置）
            self.personal_config = self._load_personal_config()
            personal_config = {
                "gitlab_token": self.personal_config.get("gitlab_token", ""),
                "github_token": self.personal_config.get("github_token", ""),
            }

            dialog = MergeRequestDialog(
                valid_pods_info, self, personal_config, main_project_info
            )
            if dialog.exec_() == QDialog.Accepted:
                self.log_message("批量创建MR完成")
        except Exception as e:
            self.log_message(f"处理MR信息时发生错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"处理MR信息时发生错误: {str(e)}")

    def _on_mr_info_error(self, error_msg):
        """处理MR信息收集错误"""
        try:
            # 清理线程引用
            if hasattr(self, "mr_info_loader"):
                self.mr_info_loader = None

            self.log_message(f"错误: {error_msg}")

            # 停止loading动画
            if hasattr(self, "loading_widget") and self.loading_widget is not None:
                self.loading_widget.stop_animation()
                self.loading_widget = None

            # 关闭loading对话框并清理引用
            if hasattr(self, "loading_dialog") and self.loading_dialog is not None:
                self.loading_dialog.close()
                self.loading_dialog = None

            QMessageBox.critical(self, "错误", error_msg)
        except Exception as e:
            self.log_message(f"处理错误时发生异常: {str(e)}")

    def show_project_mrs(self):
        """显示当前工程相关的 MR"""
        if not self.current_project:
            QMessageBox.warning(self, "提示", "请先选择一个工程")
            return

        # 加载个人配置获取 Token
        self.personal_config = self._load_personal_config()
        gitlab_token = self.personal_config.get("gitlab_token", "")

        if not gitlab_token:
            QMessageBox.warning(self, "提示", "请先在个人中心配置 GitLab Token")
            return

        # 获取主工程信息
        project_name = os.path.basename(self.current_project)
        main_project_git_url = None
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                cwd=self.current_project,
                timeout=10,
                check=False,
            )
            if result.returncode == 0:
                main_project_git_url = result.stdout.strip()
        except Exception:
            pass

        project_info = {
            "name": project_name,
            "git_url": main_project_git_url,
        }

        # 从 Podfile 中获取所有 branch/git 引用的私有库及其 git URL
        pods_info = self._get_pods_git_urls_from_podfile()

        # 显示对话框
        dialog = ProjectMRDialog(project_info, pods_info, gitlab_token, self)
        dialog.exec_()

    def _get_pods_git_urls_from_podfile(self):
        """从 Podfile 中提取所有 branch 引用的私有库 Pod 的 git URL"""
        pods_info = {}

        if not self.current_project:
            return pods_info

        podfile_path = os.path.join(self.current_project, "Podfile")
        if not os.path.exists(podfile_path):
            return pods_info

        try:
            with open(podfile_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 匹配 pod 声明和 git URL
            # 格式1: pod 'PodName', :git => 'git@xxx.git', :branch => 'xxx'
            # 格式2: pod 'PodName', :git => 'https://xxx.git', :branch => 'xxx'
            pod_pattern = r"pod\s+['\"]([^'\"]+)['\"]"
            git_pattern = r":git\s*=>\s*['\"]([^'\"]+)['\"]"

            for m in re.finditer(pod_pattern, content):
                pod_name = m.group(1)
                start_pos = m.start()

                # 查找该 pod 声明的结束位置
                next_pod = re.search(pod_pattern, content[m.end() :])
                if next_pod:
                    end_pos = m.end() + next_pod.start()
                else:
                    end_pos = len(content)

                pod_declaration = content[start_pos:end_pos]

                # 只筛选有 :branch 引用的私有库（需要创建 MR 的）
                # 排除 :tag 引用的（已发布版本，不需要 MR）
                if ":branch" in pod_declaration and ":tag" not in pod_declaration:
                    # 提取 git URL
                    git_match = re.search(git_pattern, pod_declaration)
                    if git_match:
                        git_url = git_match.group(1)
                        # 只添加 gitlab 的项目（排除 github 等公开仓库）
                        if "gitlab" in git_url.lower():
                            pods_info[pod_name] = {
                                "git_url": git_url,
                            }

        except Exception as e:
            self.log_message(f"解析 Podfile 获取 git URL 失败: {str(e)}")

        return pods_info

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

    def set_avatar(self, button):
        """设置默认头像 - 适应实际按钮尺寸"""
        try:
            actual_size = button.size()
            width = actual_size.width()
            height = actual_size.height()
            size = min(width, height)

            pixmap = QPixmap(size, size)
            pixmap.fill(QColor("transparent"))

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            margin = 1
            painter.setBrush(QColor("#007aff"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(margin, margin, size - 2 * margin, size - 2 * margin)

            head_radius = int(size * 0.15)
            body_width = int(size * 0.4)
            body_height = int(size * 0.25)

            avatar_total_height = head_radius * 2 + body_height
            avatar_top = (size - avatar_total_height) // 2

            head_x = (size - head_radius * 2) // 2
            head_y = avatar_top

            body_x = (size - body_width) // 2
            body_y = head_y + head_radius * 2

            painter.setBrush(QColor("white"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(head_x, head_y, head_radius * 2, head_radius * 2)
            painter.drawEllipse(body_x, body_y, body_width, body_height)

            painter.end()

            icon = QIcon(pixmap)
            button.setIcon(icon)
            button.setIconSize(QSize(size, size))
            button.setText("")

        except Exception as e:
            button.setText("👤")
            button.setStyleSheet(
                """
                QPushButton {
                    border: none;
                    border-radius: 18px;
                    background-color: #f0f0f5;
                    font-size: 20px;
                }
            """
            )

    def toggle_personal_drawer(self):
        """切换个人中心抽屉"""
        if not hasattr(self, "personal_drawer"):
            self.personal_drawer = PersonalCenterDrawer(self)
            self.personal_drawer.hide()

        if self.personal_drawer.isVisible():
            self.personal_drawer.slide_out()
        else:
            self.personal_drawer.slide_in()

    def show_tag_history(self):
        """显示Pod的操作历史"""
        current_items = self.pod_list.selectedItems()
        if not current_items:
            QMessageBox.warning(self, "警告", "请先选择要查看历史的Pod")
            return

        if len(current_items) > 1:
            QMessageBox.warning(self, "警告", "一次只能查看一个Pod的历史")
            return

        item = current_items[0]
        pod_name = self.get_pod_name_from_item(item)

        dialog = TagHistoryDialog(
            self.current_project,
            pod_name,
            self.config_service.config_path,
            self,
        )
        dialog.exec_()

        dialog.setLayout(layout)

        current_config = self.get_current_pods_config()
        all_tags_info = ""

        for item in current_items:
            pod_name = self.get_pod_name_from_item(item)

            if pod_name not in current_config:
                all_tags_info += f"\n{'=' * 60}\n"
                all_tags_info += f"Pod: {pod_name}\n"
                all_tags_info += f"状态: 未配置本地路径\n"
                all_tags_info += f"{'=' * 60}\n"
                continue

            local_path = current_config[pod_name]
            tags_info = GitService.get_tags_info(local_path, pod_name)
            all_tags_info += tags_info + "\n"

        text_edit.setText(all_tags_info.strip())
        dialog.exec_()

    def clean_pod_cache(self):
        if not self.current_project:
            QMessageBox.warning(self, "警告", "请先选择项目")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("清理Pod缓存")
        dialog.resize(400, 250)

        layout = QVBoxLayout()

        info_label = QLabel("请选择要清理的内容：")
        info_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(info_label)

        checkbox_layout = QVBoxLayout()
        self.clean_pods_cb = QCheckBox("删除 Pods 目录")
        self.clean_pods_cb.setChecked(True)
        self.clean_pods_cb.setStyleSheet("font-size: 12px;")
        checkbox_layout.addWidget(self.clean_pods_cb)

        self.clean_lock_cb = QCheckBox("删除 Podfile.lock 文件")
        self.clean_lock_cb.setChecked(True)
        self.clean_lock_cb.setStyleSheet("font-size: 12px;")
        checkbox_layout.addWidget(self.clean_lock_cb)

        self.clean_cache_cb = QCheckBox("清理 CocoaPods 缓存")
        self.clean_cache_cb.setChecked(True)
        self.clean_cache_cb.setStyleSheet("font-size: 12px;")
        checkbox_layout.addWidget(self.clean_cache_cb)

        warning_label = QLabel("此操作不可逆，请谨慎选择！")
        warning_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet(
            "color: #ff3b30; font-weight: bold; margin-top: 15px; padding: 8px; border: 1px solid #ff3b30; border-radius: 4px; background-color: #fff3f3;"
        )
        layout.addWidget(warning_label)

        layout.addLayout(checkbox_layout)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.setProperty("type", "cancel")
        cancel_btn.clicked.connect(dialog.reject)
        ok_btn = QPushButton("开始清理")
        ok_btn.setProperty("buttonType", "warning")
        ok_btn.clicked.connect(dialog.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

        dialog.setLayout(layout)

        if dialog.exec_() != QDialog.Accepted:
            return

        clean_pods = self.clean_pods_cb.isChecked()
        clean_lock = self.clean_lock_cb.isChecked()
        clean_cache = self.clean_cache_cb.isChecked()

        if not clean_pods and not clean_lock and not clean_cache:
            QMessageBox.information(self, "提示", "未选择任何清理项")
            return

        def on_clean_finished(exit_code):
            summary_parts = []
            if clean_pods:
                summary_parts.append("Pods目录")
            if clean_lock:
                summary_parts.append("Podfile.lock")
            if clean_cache:
                summary_parts.append("CocoaPods缓存")

            if exit_code == 0 or not clean_cache:
                self.log_message("Pod缓存清理完成")
                QMessageBox.information(
                    self, "成功", f"已清理：\n{', '.join(summary_parts)}"
                )
            else:
                self.log_message(f"Pod缓存清理失败，退出码: {exit_code}")
                QMessageBox.warning(
                    self,
                    "警告",
                    f"部分清理失败\n\n已清理：\n{', '.join(summary_parts)}\n\n请查看日志了解详情",
                )

        self.pod_cache_service.set_finished_callback(on_clean_finished)
        self.pod_cache_service.clean_cache(
            self.current_project, clean_pods, clean_lock, clean_cache
        )

    def log_message(self, message):
        self.log_output.append(message)

    def run_pod_install(self):
        if not self.current_project:
            QMessageBox.warning(self, "警告", "请先选择项目")
            return

        podfile_path = os.path.join(self.current_project, "Podfile")
        if not os.path.exists(podfile_path):
            QMessageBox.warning(self, "错误", "未找到Podfile")
            return

        self.log_message(f"项目路径: {self.current_project}")
        self.log_message("正在运行 pod install...")

        def on_pod_install_finished(exit_code, exit_status):
            if exit_code == 0:
                self.log_message("pod install 完成")
                QMessageBox.information(self, "成功", "pod install 完成")
            else:
                self.log_message(f"pod install 失败，退出码: {exit_code}")
                QMessageBox.warning(
                    self, "警告", f"pod install 失败，请查看日志了解详情"
                )

        self.pod_install_service.set_finished_callback(on_pod_install_finished)
        self.pod_install_service.run_pod_install(self.current_project)
        """清理Pod缓存"""
        if not self.current_project:
            QMessageBox.warning(self, "警告", "请先选择项目")
            return

        # 创建清理选项对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("清理Pod缓存")
        dialog.resize(400, 250)

        layout = QVBoxLayout()

        # 添加说明
        info_label = QLabel("请选择要清理的内容：")
        info_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(info_label)

        # 添加复选框
        checkbox_layout = QVBoxLayout()
        self.clean_pods_cb = QCheckBox("删除 Pods 目录")
        self.clean_pods_cb.setChecked(True)
        self.clean_pods_cb.setStyleSheet("font-size: 12px;")
        checkbox_layout.addWidget(self.clean_pods_cb)

        self.clean_lock_cb = QCheckBox("删除 Podfile.lock 文件")
        self.clean_lock_cb.setChecked(True)
        self.clean_lock_cb.setStyleSheet("font-size: 12px;")
        checkbox_layout.addWidget(self.clean_lock_cb)

        self.clean_cache_cb = QCheckBox("清理 CocoaPods 缓存")
        self.clean_cache_cb.setChecked(True)
        self.clean_cache_cb.setStyleSheet("font-size: 12px;")
        checkbox_layout.addWidget(self.clean_cache_cb)

        # 添加警告
        warning_label = QLabel("此操作不可逆，请谨慎选择！")
        warning_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet(
            "color: #ff3b30; font-weight: bold; margin-top: 15px; padding: 8px; border: 1px solid #ff3b30; border-radius: 4px; background-color: #fff3f3;"
        )
        layout.addWidget(warning_label)

        layout.addLayout(checkbox_layout)

        # 添加按钮
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.setProperty("type", "cancel")
        cancel_btn.clicked.connect(dialog.reject)
        ok_btn = QPushButton("开始清理")
        ok_btn.setProperty("buttonType", "warning")
        ok_btn.clicked.connect(dialog.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

        dialog.setLayout(layout)

        if dialog.exec_() != QDialog.Accepted:
            return

        # 获取用户选择
        clean_pods = self.clean_pods_cb.isChecked()
        clean_lock = self.clean_lock_cb.isChecked()
        clean_cache = self.clean_cache_cb.isChecked()

        if not clean_pods and not clean_lock and not clean_cache:
            QMessageBox.information(self, "提示", "未选择任何清理项")
            return

        self.log_message("开始清理Pod缓存...")

        try:
            # 1. 删除Pods目录
            if clean_pods:
                pods_dir = os.path.join(self.current_project, "Pods")
                if os.path.exists(pods_dir):
                    self.log_message(f"删除Pods目录: {pods_dir}")
                    shutil.rmtree(pods_dir)
                    self.log_message("Pods目录已删除")
                else:
                    self.log_message("Pods目录不存在，跳过")

            # 2. 删除Podfile.lock
            if clean_lock:
                lock_file = os.path.join(self.current_project, "Podfile.lock")
                if os.path.exists(lock_file):
                    self.log_message(f"删除Podfile.lock: {lock_file}")
                    os.remove(lock_file)
                    self.log_message("Podfile.lock已删除")
                else:
                    self.log_message("Podfile.lock不存在，跳过")

            # 3. 清理CocoaPods缓存
            if clean_cache:
                self.log_message("清理CocoaPods缓存...")
                process = QProcess(self)
                process.setProcessEnvironment(QProcessEnvironment.systemEnvironment())

                shell_cmd = """
source ~/.rvm/scripts/rvm 2>/dev/null || source ~/.rvm/bin/rvm 2>/dev/null || true
pod cache clean --all
"""

                # 设置输出回调
                process.readyReadStandardOutput.connect(
                    lambda: self.log_output.append(
                        process.readAllStandardOutput().data().decode()
                    )
                )
                process.readyReadStandardError.connect(
                    lambda: self.log_output.append(
                        process.readAllStandardError().data().decode()
                    )
                )
                process.finished.connect(
                    lambda exit_code, exit_status: self.on_cache_clean_finished(
                        exit_code, clean_pods, clean_lock, clean_cache
                    )
                )

                # 启动进程
                user_shell = os.environ.get("SHELL", "/bin/zsh")
                if not os.path.exists(user_shell):
                    user_shell = "/bin/zsh"

                process.start(user_shell, ["-l", "-c", shell_cmd])
            else:
                # 如果不需要清理缓存，直接显示完成
                self.on_cache_clean_finished(0, clean_pods, clean_lock, clean_cache)

        except Exception as e:
            self.log_message(f"清理失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"清理失败: {str(e)}")

    def on_cache_clean_finished(self, exit_code, clean_pods, clean_lock, clean_cache):
        """缓存清理完成回调"""
        summary_parts = []
        if clean_pods:
            summary_parts.append("Pods目录")
        if clean_lock:
            summary_parts.append("Podfile.lock")
        if clean_cache:
            summary_parts.append("CocoaPods缓存")

        if exit_code == 0 or not clean_cache:
            self.log_message("Pod缓存清理完成")
            QMessageBox.information(
                self, "成功", f"已清理：\n{', '.join(summary_parts)}"
            )
        else:
            self.log_message(f"Pod缓存清理失败，退出码: {exit_code}")
            QMessageBox.warning(
                self,
                "警告",
                f"部分清理失败\n\n已清理：\n{', '.join(summary_parts)}\n\n请查看日志了解详情",
            )

    def log_message(self, message):
        """记录日志消息"""
        self.log_output.append(message)

    def run_pod_install(self):
        """运行pod install"""
        if not self.current_project:
            QMessageBox.warning(self, "警告", "请先选择项目")
            return

        podfile_path = os.path.join(self.current_project, "Podfile")
        if not os.path.exists(podfile_path):
            QMessageBox.warning(self, "错误", "未找到Podfile")
            return

        self.log_message(f"项目路径: {self.current_project}")
        self.log_message("正在运行 pod install...")

        # 使用QProcess异步执行，不阻塞主线程
        process = QProcess(self)
        process.setWorkingDirectory(self.current_project)

        # 使用系统默认环境，不做任何修改
        # 这样可以保留用户的所有环境配置
        process.setProcessEnvironment(QProcessEnvironment.systemEnvironment())

        # 初始化RVM和运行pod install，使用当前用户权限（避免root权限问题）
        shell_cmd = f'''
source ~/.rvm/scripts/rvm 2>/dev/null || source ~/.rvm/bin/rvm 2>/dev/null || true
cd "{self.current_project}" && pod install
'''

        # 连接信号槽
        process.readyReadStandardOutput.connect(
            lambda: self.log_output.append(
                process.readAllStandardOutput().data().decode()
            )
        )
        process.readyReadStandardError.connect(
            lambda: self.log_output.append(
                process.readAllStandardError().data().decode()
            )
        )
        process.finished.connect(
            lambda exit_code, exit_status: self.on_pod_install_finished(
                process, exit_code, exit_status
            )
        )

        # 启动进程，使用用户的默认shell
        user_shell = os.environ.get("SHELL", "/bin/zsh")
        if not os.path.exists(user_shell):
            user_shell = "/bin/zsh"

        process.start(user_shell, ["-l", "-c", shell_cmd])

    def on_pod_install_finished(self, process, exit_code, exit_status):
        """pod install完成后的回调"""
        if exit_code == 0:
            self.log_message("pod install 完成")
            QMessageBox.information(self, "成功", "pod install 完成")
        else:
            self.log_message(f"pod install 失败，退出码: {exit_code}")
            QMessageBox.warning(self, "警告", f"pod install 失败，请查看日志了解详情")

        # 删除进程对象
        process.deleteLater()
