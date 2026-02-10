from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGridLayout,
    QDialog,
    QVBoxLayout,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QComboBox,
    QCheckBox,
    QWidget,
    QSizePolicy,
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QBrush, QColor
import os

from src.services.git_service import GitService
from src.widgets.loading_widget import LoadingWidget


class BranchSwitchWorker(QThread):
    """异步切换到Branch模式的工作线程"""

    finished = pyqtSignal(dict)

    def __init__(
        self,
        pods_info,
        branch_configs,
        git_urls,
        podfile_path,
        podfile_lines,
    ):
        super().__init__()
        self.pods_info = pods_info
        self.branch_configs = branch_configs
        self.git_urls = git_urls
        self.podfile_path = podfile_path
        self.podfile_lines = podfile_lines

    def run(self):
        success_count = 0
        fail_count = 0
        error_messages = []

        new_lines = self.podfile_lines.copy()

        for row, pod_info in enumerate(self.pods_info):
            pod_name = pod_info["name"]
            local_path = pod_info["path"]
            git_url = self.git_urls.get(pod_name, "")

            if not git_url or git_url == "获取失败":
                error_messages.append(f"{pod_name}: 无法获取Git URL")
                fail_count += 1
                continue

            # 获取配置
            config = self.branch_configs.get(row, {})
            selected_branch = config.get("branch", "")
            is_new_branch = config.get("is_new", False)
            base_branch = config.get("base_branch", "origin/master")

            if not selected_branch:
                error_messages.append(f"{pod_name}: 未选择分支")
                fail_count += 1
                continue

            try:
                # 如果是新分支，先创建并推送
                if is_new_branch:
                    if not GitService.create_branch(
                        local_path, selected_branch, base_branch
                    ):
                        raise Exception("创建分支失败")
                    if not GitService.push_branch(local_path, selected_branch):
                        raise Exception("推送分支失败")

                # 修改Podfile - 去掉 origin/ 前缀
                branch_for_podfile = selected_branch
                if branch_for_podfile.startswith("origin/"):
                    branch_for_podfile = branch_for_podfile[7:]  # 去掉 "origin/" 前缀

                modified = self._update_podfile_for_branch(
                    new_lines, pod_name, git_url, branch_for_podfile
                )

                if not modified:
                    error_messages.append(f"{pod_name}: 未找到Pod引用")
                    fail_count += 1
                else:
                    success_count += 1

            except Exception as e:
                error_messages.append(f"{pod_name}: {str(e)}")
                fail_count += 1

        # 写回Podfile
        try:
            with open(self.podfile_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception as e:
            error_messages.append(f"写入Podfile失败: {str(e)}")
            fail_count += success_count
            success_count = 0

        self.finished.emit(
            {
                "success_count": success_count,
                "fail_count": fail_count,
                "error_messages": error_messages,
            }
        )

    def _get_full_pod_declaration(self, lines, start_idx, pod_name):
        """获取完整的pod声明（可能跨越多行）"""
        if start_idx >= len(lines):
            return None, None, None

        line = lines[start_idx]
        # 支持 pod 'Name' 和 pod 'Name/Subspec' 格式
        pod_pattern = f"pod '{pod_name}'"
        pod_with_subspec_pattern = f"pod '{pod_name}/"
        if (
            pod_pattern not in line
            and pod_with_subspec_pattern not in line
            and f'pod "{pod_name}"' not in line
            and f'pod "{pod_name}/' not in line
        ):
            return None, None, None

        full_lines = [line.rstrip("\n")]
        end_idx = start_idx

        i = start_idx
        while i < len(lines):
            current_line = lines[i]
            stripped = current_line.rstrip()

            if stripped.endswith("\\"):
                full_lines.append(stripped[:-1])
                i += 1
                end_idx = i
            else:
                if i > start_idx:
                    full_lines.append(stripped)
                break

        full_declaration = "\n".join(full_lines)
        return start_idx, end_idx, full_declaration

    def _extract_version_constant(self, declaration):
        """从pod声明中提取版本常量名

        例如: pod 'XXX', :git => '...', :tag => UI_OC_VERSION
        返回: UI_OC_VERSION

        支持 :tag 和 :branch 参数
        """
        import re

        # 匹配 :tag => CONSTANT 或 :branch => CONSTANT 模式
        # 常量名以大写字母开头，可包含字母、数字、下划线
        patterns = [
            r":tag\s*=>\s*([A-Z]\w*)",
            r":branch\s*=>\s*([A-Z]\w*)",
        ]

        for pattern in patterns:
            match = re.search(pattern, declaration)
            if match:
                return match.group(1)

        return None

    def _update_constant_value(self, lines, constant_name, new_value):
        """更新Podfile中常量的值

        查找 CONSTANT = 'value' 或 CONSTANT = "value" 模式并替换
        返回是否成功更新
        """
        import re

        # 匹配常量定义: CONSTANT = 'value' 或 CONSTANT = "value"
        pattern = rf"^({re.escape(constant_name)}\s*=\s*['\"])[^'\"]*(['\"])"

        for i, line in enumerate(lines):
            if re.match(pattern, line.strip()):
                # 替换常量的值
                lines[i] = re.sub(pattern, rf"\g<1>{new_value}\g<2>", line)
                return True

        return False

    def _update_podfile_for_branch(self, lines, pod_name, git_url, branch_name):
        """更新Podfile以切换到branch模式

        如果pod声明使用常量，则更新常量的值
        否则直接修改pod声明行

        返回是否成功修改
        """
        for i, line in enumerate(lines):
            # 支持 pod 'Name' 和 pod 'Name/Subspec' 格式
            pod_pattern = f"pod '{pod_name}'"
            pod_with_subspec_pattern = f"pod '{pod_name}/"

            matches = (
                pod_pattern in line
                or pod_with_subspec_pattern in line
                or f'pod "{pod_name}"' in line
                or f'pod "{pod_name}/' in line
            )

            if not matches:
                continue

            start_idx, end_idx, full_declaration = self._get_full_pod_declaration(
                lines, i, pod_name
            )

            if full_declaration is None:
                continue

            # 检查是否使用常量
            constant_name = self._extract_version_constant(full_declaration)

            if constant_name:
                # 使用常量，更新常量的值，并将 :tag 改为 :branch
                if self._update_constant_value(lines, constant_name, branch_name):
                    # 将 pod 声明中的 :tag => CONSTANT 改为 :branch => CONSTANT
                    updated_declaration = full_declaration.replace(
                        f":tag => {constant_name}", f":branch => {constant_name}"
                    )
                    if start_idx == end_idx:
                        lines[start_idx] = updated_declaration + "\n"
                    else:
                        lines[start_idx] = updated_declaration + "\n"
                        for j in range(start_idx + 1, end_idx + 1):
                            lines[j] = ""
                    return True
            else:
                # 不使用常量，只替换 :tag 或 :branch 部分，保留原有的 git URL
                updated_declaration = full_declaration

                # 将 :tag => 'xxx' 或 :tag => "xxx" 替换为 :branch => 'branch_name'
                import re

                updated_declaration = re.sub(
                    r":tag\s*=>\s*['\"][^'\"]*['\"]",
                    f":branch => '{branch_name}'",
                    updated_declaration,
                )

                # 如果原本就是 :branch，则只更新值
                updated_declaration = re.sub(
                    r":branch\s*=>\s*['\"][^'\"]*['\"]",
                    f":branch => '{branch_name}'",
                    updated_declaration,
                )

                if start_idx == end_idx:
                    lines[start_idx] = updated_declaration + "\n"
                else:
                    lines[start_idx] = updated_declaration + "\n"
                    for j in range(start_idx + 1, end_idx + 1):
                        lines[j] = ""
                return True

        return False


class BatchBranchDialog(QDialog):
    """批量切换到Branch模式的对话框（内联编辑版）"""

    def __init__(self, pods_info, podfile_path=None, podfile_lines=None, parent=None):
        super().__init__(parent)
        self.pods_info = pods_info
        self.podfile_path = podfile_path
        self.podfile_lines = podfile_lines or []
        self.branch_configs = {}  # {row: {"branch": "xxx", "is_new": False, "base_branch": "origin/master"}}
        self.git_urls = {}
        self.worker = None
        self.loading_widget = None
        self.initUI()
        self.load_pods_info()

    def initUI(self):
        self.setWindowTitle("批量切换到Branch模式")
        self.setGeometry(200, 200, 1500, 700)

        # 获取图标路径
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        checked_icon = os.path.join(
            base_dir, "resources", "icons", "check_box.svg"
        ).replace("\\", "/")
        unchecked_icon = os.path.join(
            base_dir, "resources", "icons", "uncheck_box.svg"
        ).replace("\\", "/")

        self.setStyleSheet(
            """
            QDialog {
                background-color: #f5f5f7;
            }
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 400;
                min-height: 26px;
                max-height: 26px;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #0051d5;
            }
            QPushButton[type="cancel"] {
                background-color: #e8e8ed;
                color: #1d1d1f;
            }
            QPushButton[type="cancel"]:hover {
                background-color: #d1d1d6;
            }
            QLabel {
                color: #86868b;
                font-size: 12px;
                font-weight: 600;
            }
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: 600;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                color: #1d1d1f;
            }
            QTableWidget {
                border: none;
                background-color: white;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #007aff;
                color: white;
            }
            QHeaderView::section {
                background-color: #f5f5f7;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #d1d1d6;
                font-weight: 600;
                color: #1d1d1f;
            }
            QComboBox {
                border: 1px solid #d1d1d6;
                border-radius: 4px;
                padding: 2px 6px;
                background-color: white;
            }
            QComboBox QAbstractItemView {
                min-width: 250px;
            }
            QComboBox:hover {
                border-color: #007aff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QCheckBox {
                spacing: 4px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: none;
                image: url("""
            + unchecked_icon
            + """);
            }
            QCheckBox::indicator:checked {
                image: url("""
            + checked_icon
            + """);
            }
        """
        )

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题和说明
        header_layout = QVBoxLayout()
        title_label = QLabel("批量切换到Branch模式")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1d1d1f;")
        header_layout.addWidget(title_label)

        desc_label = QLabel(
            '为每个Pod选择目标分支，勾选"创建新分支"可基于现有分支创建新分支'
        )
        desc_label.setStyleSheet("color: #86868b; font-size: 12px;")
        header_layout.addWidget(desc_label)
        layout.addLayout(header_layout)

        # 表格区域
        table_group = QGroupBox("Pod列表")
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(12, 16, 12, 12)

        self.pod_table = QTableWidget()
        self.pod_table.setColumnCount(7)
        self.pod_table.setHorizontalHeaderLabels(
            [
                "Pod名称",
                "本地路径",
                "当前分支",
                "Git URL",
                "目标分支",
                "创建新分支",
                "基于分支",
            ]
        )

        # 设置列宽 - 调整以防止选择框超出单元格
        self.pod_table.setColumnWidth(0, 120)  # Pod名称
        self.pod_table.setColumnWidth(1, 200)  # 本地路径
        self.pod_table.setColumnWidth(2, 90)  # 当前分支
        self.pod_table.setColumnWidth(3, 240)  # Git URL
        self.pod_table.setColumnWidth(4, 200)  # 目标分支
        self.pod_table.setColumnWidth(5, 80)  # 创建新分支
        self.pod_table.setColumnWidth(6, 200)  # 基于分支

        self.pod_table.horizontalHeader().setStretchLastSection(True)
        self.pod_table.setAlternatingRowColors(True)
        self.pod_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.pod_table.setEditTriggers(QTableWidget.NoEditTriggers)

        table_layout.addWidget(self.pod_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # 快捷操作按钮
        quick_layout = QHBoxLayout()
        quick_label = QLabel("快捷设置:")
        quick_label.setStyleSheet("font-weight: 600;")
        quick_layout.addWidget(quick_label)

        set_all_master_btn = QPushButton("全部设为 master")
        set_all_master_btn.clicked.connect(lambda: self.set_all_branches("master"))
        set_all_master_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #30b350;
            }
        """)
        quick_layout.addWidget(set_all_master_btn)

        set_all_develop_btn = QPushButton("全部设为 develop")
        set_all_develop_btn.clicked.connect(lambda: self.set_all_branches("develop"))
        set_all_develop_btn.setStyleSheet("""
            QPushButton {
                background-color: #5856d6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #4c4ab8;
            }
        """)
        quick_layout.addWidget(set_all_develop_btn)

        quick_layout.addStretch()
        layout.addLayout(quick_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        switch_all_btn = QPushButton("批量切换所有")
        switch_all_btn.setFixedHeight(26)
        switch_all_btn.clicked.connect(self.switch_all_to_branch)

        cancel_btn = QPushButton("取消")
        cancel_btn.setProperty("type", "cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(switch_all_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def load_pods_info(self):
        """加载Pod信息到表格"""
        self.pod_table.setRowCount(len(self.pods_info))

        for row, pod_info in enumerate(self.pods_info):
            self.pod_table.setRowHeight(row, 50)
            pod_name = pod_info["name"]
            local_path = pod_info["path"]
            branches = pod_info.get("branches", [])
            current_branch = pod_info.get("current_branch", "获取中...")

            # 获取git URL
            git_url = GitService.get_remote_url(local_path)
            self.git_urls[pod_name] = git_url if git_url else "获取失败"

            # 填充基本信息
            self.pod_table.setItem(row, 0, QTableWidgetItem(pod_name))

            # 本地路径 - 添加tooltip显示完整路径
            local_path_item = QTableWidgetItem(local_path)
            local_path_item.setToolTip(local_path)
            self.pod_table.setItem(row, 1, local_path_item)

            self.pod_table.setItem(row, 2, QTableWidgetItem(current_branch))

            # Git URL - 添加tooltip显示完整URL
            git_url_text = git_url or "获取失败"
            git_url_item = QTableWidgetItem(git_url_text)
            git_url_item.setToolTip(git_url_text)
            self.pod_table.setItem(row, 3, git_url_item)

            # 目标分支下拉框（可编辑）- 使用容器包装以控制大小
            branch_combo = QComboBox()
            branch_combo.setEditable(True)
            branch_combo.setInsertPolicy(QComboBox.InsertAlphabetically)
            branch_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            branch_combo.addItems(branches)
            branch_combo.view().setMinimumWidth(250)
            # 默认选择origin/master或第一个分支
            if "origin/master" in branches:
                branch_combo.setCurrentText("origin/master")
            elif "origin/main" in branches:
                branch_combo.setCurrentText("origin/main")
            elif branches:
                branch_combo.setCurrentText(branches[0])
            branch_combo.currentTextChanged.connect(
                lambda text, r=row: self.on_branch_changed(r, text)
            )
            # 包装在容器中并设置边距
            branch_container = QWidget()
            branch_layout = QHBoxLayout(branch_container)
            branch_layout.addWidget(branch_combo)
            branch_layout.setContentsMargins(4, 0, 4, 0)
            self.pod_table.setCellWidget(row, 4, branch_container)
            # 初始化：禁用编辑，只可选择
            branch_combo.lineEdit().setReadOnly(True)

            # 创建新分支复选框 - 增大点击区域
            create_new_checkbox = QCheckBox("创建")
            create_new_checkbox.setStyleSheet("QCheckBox { padding: 4px; }")
            create_new_checkbox.stateChanged.connect(
                lambda state, r=row: self.on_create_new_changed(r, state)
            )
            # 居中显示
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(create_new_checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(2, 2, 2, 2)
            self.pod_table.setCellWidget(row, 5, checkbox_widget)

            # 基于分支下拉框（初始禁用）- 使用容器包装以控制大小
            base_branch_combo = QComboBox()
            base_branch_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            base_branch_combo.addItems(branches)
            base_branch_combo.view().setMinimumWidth(250)
            if "origin/master" in branches:
                base_branch_combo.setCurrentText("origin/master")
            elif "origin/main" in branches:
                base_branch_combo.setCurrentText("origin/main")
            elif branches:
                base_branch_combo.setCurrentText(branches[0])
            base_branch_combo.setEnabled(False)
            base_branch_combo.currentTextChanged.connect(
                lambda text, r=row: self.on_base_branch_changed(r, text)
            )
            # 包装在容器中并设置边距
            base_container = QWidget()
            base_layout = QHBoxLayout(base_container)
            base_layout.addWidget(base_branch_combo)
            base_layout.setContentsMargins(4, 0, 4, 0)
            self.pod_table.setCellWidget(row, 6, base_container)

            # 初始化配置
            self.branch_configs[row] = {
                "branch": branch_combo.currentText(),
                "is_new": False,
                "base_branch": base_branch_combo.currentText(),
            }

    def on_branch_changed(self, row, text):
        """目标分支改变"""
        if row in self.branch_configs:
            self.branch_configs[row]["branch"] = text

    def on_create_new_changed(self, row, state):
        """创建新分支复选框改变"""
        if row in self.branch_configs:
            is_checked = state == 2  # Qt.Checked = 2
            self.branch_configs[row]["is_new"] = is_checked

            # 启用或禁用基于分支下拉框（从容器中获取）
            base_container = self.pod_table.cellWidget(row, 6)
            if base_container and base_container.layout():
                base_branch_combo = base_container.layout().itemAt(0).widget()
                if base_branch_combo:
                    base_branch_combo.setEnabled(is_checked)

            # 切换目标分支下拉框的可编辑状态
            branch_container = self.pod_table.cellWidget(row, 4)
            if branch_container and branch_container.layout():
                branch_combo = branch_container.layout().itemAt(0).widget()
                if branch_combo:
                    line_edit = branch_combo.lineEdit()
                    if line_edit:
                        if is_checked:
                            # 选中"创建新分支"时：只可编辑，不可选择下拉列表
                            branch_combo.clear()
                            branch_combo.setEditable(True)
                            line_edit.setReadOnly(False)
                        else:
                            # 未选中时：只可选择，不可编辑
                            branch_combo.setEditable(False)
                            line_edit.setReadOnly(True)

    def on_base_branch_changed(self, row, text):
        """基于分支改变"""
        if row in self.branch_configs:
            self.branch_configs[row]["base_branch"] = text

    def set_all_branches(self, branch_name):
        """将所有Pod的目标分支设置为指定分支"""
        for row in range(self.pod_table.rowCount()):
            # 获取容器中的QComboBox
            branch_container = self.pod_table.cellWidget(row, 4)
            if branch_container and branch_container.layout():
                branch_combo = branch_container.layout().itemAt(0).widget()
                if branch_combo and isinstance(branch_combo, QComboBox):
                    branch_combo.setCurrentText(branch_name)
                    if row in self.branch_configs:
                        self.branch_configs[row]["branch"] = branch_name

    def switch_all_to_branch(self):
        """批量切换所有Pod到Branch模式"""
        # 检查是否所有Pod都选择了分支
        for row, pod_info in enumerate(self.pods_info):
            config = self.branch_configs.get(row, {})
            if not config.get("branch", ""):
                QMessageBox.warning(self, "警告", f"请为 {pod_info['name']} 选择分支")
                return

        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认",
            f"确定要将 {len(self.branch_configs)} 个Pod切换到Branch模式吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        # 创建Loading对话框
        loading_dialog = QDialog(self)
        loading_dialog.setFixedSize(200, 100)
        self.loading_widget = LoadingWidget("切换中...")
        loading_layout = QVBoxLayout()
        loading_layout.addWidget(self.loading_widget)
        loading_dialog.setLayout(loading_layout)
        loading_dialog.show()
        self.loading_widget.start_animation()

        # 读取Podfile
        if not self.podfile_lines:
            try:
                with open(self.podfile_path, "r", encoding="utf-8") as f:
                    self.podfile_lines = f.readlines()
            except Exception as e:
                self.loading_widget.stop_animation()
                loading_dialog.close()
                QMessageBox.critical(self, "错误", f"读取Podfile失败: {str(e)}")
                return

        # 创建工作线程
        self.worker = BranchSwitchWorker(
            self.pods_info,
            self.branch_configs,
            self.git_urls,
            self.podfile_path,
            self.podfile_lines,
        )
        self.worker.setParent(None)
        self.worker.finished.connect(
            lambda result: self._on_branch_switch_finished(result, loading_dialog)
        )
        self.worker.start()

    def _on_branch_switch_finished(self, result, loading_dialog):
        """处理Branch切换完成"""
        if self.loading_widget:
            self.loading_widget.stop_animation()

        loading_dialog.close()

        success_count = result["success_count"]
        fail_count = result["fail_count"]
        error_messages = result["error_messages"]

        result_msg = f"切换完成：成功 {success_count} 个，失败 {fail_count} 个"
        if error_messages:
            result_msg += "\n\n失败详情:\n" + "\n".join(error_messages[:10])

        if fail_count == 0:
            QMessageBox.information(self, "成功", result_msg)
            self.accept()
        else:
            QMessageBox.warning(self, "警告", result_msg)

    def closeEvent(self, event):
        """处理关闭事件"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "确认",
                "分支切换正在进行中，确定要取消吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return
            self.worker.quit()
            self.worker.wait(2000)
        event.accept()
