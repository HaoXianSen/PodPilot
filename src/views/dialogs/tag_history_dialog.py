from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QTextEdit,
    QComboBox,
    QGroupBox,
    QDateEdit,
    QMessageBox,
    QGridLayout,
    QLineEdit,
    QSplitter,
    QListWidgetItem,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from datetime import datetime
from src.models.tag_history_manager import TagHistoryManager
import os


class TagHistoryDialog(QDialog):
    """Tag历史记录对话框"""

    def __init__(self, project_path, pod_name, config_path, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.pod_name = pod_name
        self.config_path = config_path
        self.history_manager = TagHistoryManager(config_path)
        self.initUI()
        self.load_history()

    def initUI(self):
        self.setWindowTitle(f"Tag历史记录 - {self.pod_name}")
        self.setGeometry(300, 300, 900, 650)

        layout = QVBoxLayout()

        # 筛选区域
        filter_group = QGroupBox("筛选条件")
        filter_layout = QGridLayout()

        # 第一行：操作类型和显示数量
        filter_layout.addWidget(QLabel("操作类型:"), 0, 0)
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(
            [
                "全部",
                "create",
                "switch_to_tag",
                "switch_to_branch",
                "switch_to_dev",
                "exit_dev",
                "switch_to_normal",
                "rollback",
            ]
        )
        self.operation_combo.currentIndexChanged.connect(self.filter_history)
        filter_layout.addWidget(self.operation_combo, 0, 1)

        filter_layout.addWidget(QLabel("显示数量:"), 0, 2)
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(["20", "50", "100", "200"])
        self.limit_combo.setCurrentText("50")
        self.limit_combo.currentIndexChanged.connect(self.load_history)
        filter_layout.addWidget(self.limit_combo, 0, 3)

        # 第二行：搜索和日期范围
        filter_layout.addWidget(QLabel("搜索关键词:"), 1, 0)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入Tag/分支/路径搜索...")
        self.search_edit.textChanged.connect(self.filter_history)
        filter_layout.addWidget(self.search_edit, 1, 1)

        filter_layout.addWidget(QLabel("开始日期:"), 1, 2)
        from PyQt5.QtWidgets import QDateEdit

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDateRange(
            self.start_date_edit.minimumDate(), self.start_date_edit.maximumDate()
        )
        self.start_date_edit.setDate(self.start_date_edit.minimumDate())
        filter_layout.addWidget(self.start_date_edit, 1, 3)

        # 第三行：按钮
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_history)
        btn_layout.addWidget(refresh_btn)

        clear_btn = QPushButton("清理旧记录")
        clear_btn.clicked.connect(self.clear_old_records)
        btn_layout.addWidget(clear_btn)

        trend_btn = QPushButton("使用趋势")
        trend_btn.setProperty("type", "success")
        trend_btn.clicked.connect(self.show_usage_trend)
        btn_layout.addWidget(trend_btn)

        filter_layout.addLayout(btn_layout, 2, 0, 1, 4)

        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # 创建分割器
        from PyQt5.QtWidgets import QSplitter, QWidget

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # 左侧：历史记录列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        left_layout.addWidget(QLabel("历史记录:"))
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.show_history_detail)
        left_layout.addWidget(self.history_list)

        splitter.addWidget(left_widget)

        # 右侧：详细信息
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        right_layout.addWidget(QLabel("详细信息:"))
        self.detail_edit = QTextEdit()
        self.detail_edit.setReadOnly(True)
        right_layout.addWidget(self.detail_edit)

        # 操作按钮
        action_layout = QHBoxLayout()
        rollback_btn = QPushButton("回滚到此Tag")
        rollback_btn.clicked.connect(self.rollback_to_selected)
        action_layout.addWidget(rollback_btn)

        export_btn = QPushButton("导出记录")
        export_btn.clicked.connect(self.export_history)
        action_layout.addWidget(export_btn)

        right_layout.addLayout(action_layout)

        splitter.addWidget(right_widget)

        splitter.setSizes([400, 400])

        # 统计信息
        stats_layout = QHBoxLayout()
        stats_label = QLabel()
        stats_label.setStyleSheet("color: #86868b; font-size: 11px;")
        stats_layout.addWidget(stats_label)
        layout.addLayout(stats_layout)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

        self.stats_label = stats_label

        # 应用样式
        self.setStyleSheet("""
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
            QPushButton[type="danger"] {
                background-color: #ff3b30;
            }
            QPushButton[type="danger"]:hover {
                background-color: #d63026;
            }
            QPushButton[type="success"] {
                background-color: #34c759;
            }
            QPushButton[type="success"]:hover {
                background-color: #30b150;
            }
            QLabel {
                color: #86868b;
                font-size: 12px;
                font-weight: 600;
            }
            QComboBox {
                border: 1px solid #d1d1d6;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
                min-height: 26px;
            }
            QListWidget {
                border: 1px solid #d1d1d6;
                border-radius: 4px;
                padding: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 4px;
                margin: 2px 0;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #007aff;
                color: white;
            }
            QTextEdit {
                border: 1px solid #d1d1d6;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
                font-family: monospace;
                font-size: 11px;
            }
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                font-weight: 600;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                color: #1d1d1f;
            }
        """)

    def load_history(self):
        """加载历史记录"""
        self.history_list.clear()

        limit = int(self.limit_combo.currentText())
        operation_filter = self.operation_combo.currentText()
        search_text = self.search_edit.text().strip()

        # 使用增强的查询方法
        if operation_filter != "全部":
            history = self.history_manager.get_pod_tag_history(
                self.project_path, self.pod_name, limit, operation_type=operation_filter
            )
        else:
            history = self.history_manager.get_pod_tag_history(
                self.project_path, self.pod_name, limit
            )

        # 按tag名称搜索
        if search_text:
            history = [
                record
                for record in history
                if record.get("tag_name", "").lower().find(search_text.lower()) >= 0
            ]

        # 显示历史记录
        for record in history:
            timestamp = datetime.fromisoformat(record["timestamp"])
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            operation = record.get("operation", "unknown")
            tag_name = record.get("tag_name", "N/A")

            # 操作类型映射
            operation_names = {
                "create": "创建Tag",
                "switch_to_tag": "切换到Tag",
                "switch_to_normal": "恢复正常模式",
                "rollback": "回滚",
            }

            display_text = (
                f"{time_str} - {operation_names.get(operation, operation)}: {tag_name}"
            )
            self.history_list.addItem(display_text)

            # 存储完整记录数据
            self.history_list.item(self.history_list.count() - 1).setData(
                Qt.UserRole, record
            )
            self.history_list.addItem(display_text)

            # 存储完整记录数据
            self.history_list.item(self.history_list.count() - 1).setData(
                Qt.UserRole, record
            )

            # 显示详细说明
            help_text = QListWidgetItem("💡 创建或切换Tag后，记录将显示在这里")
            help_text.setForeground(QColor("#007aff"))
            help_text.setTextAlignment(Qt.AlignCenter)
            self.history_list.addItem(help_text)
            help_item = QListWidgetItem("📝 所有操作都会自动记录到历史")
            help_item.setForeground(QColor("#34c759"))
            help_item.setTextAlignment(Qt.AlignCenter)
            self.history_list.addItem(help_item)

        self.update_statistics()

    def filter_history(self):
        """根据筛选条件过滤历史记录"""
        self.load_history()

    def show_history_detail(self, item):
        """显示历史记录详细信息"""
        record = item.data(Qt.UserRole)
        if not record:
            return

        timestamp = datetime.fromisoformat(record["timestamp"])
        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        operation = record.get("operation", "unknown")
        tag_name = record.get("tag_name", "N/A")
        details = record.get("details", {})

        # 操作类型映射
        operation_names = {
            "create": "创建Tag",
            "switch_to_tag": "切换到Tag",
            "switch_to_normal": "恢复正常模式",
            "rollback": "回滚",
        }

        detail_text = f"""时间: {time_str}
操作: {operation_names.get(operation, operation)}
Tag名称: {tag_name}
"""

        if details:
            detail_text += "\n详细信息:\n"
            for key, value in details.items():
                detail_text += f"  {key}: {value}\n"

        self.detail_edit.setText(detail_text)

    def rollback_to_selected(self):
        """回滚到选中的tag"""
        current_item = self.history_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一条历史记录")
            return

        record = current_item.data(Qt.UserRole)
        if not record or not record.get("tag_name"):
            QMessageBox.warning(self, "警告", "所选记录没有Tag信息")
            return

        tag_name = record["tag_name"]

        # 确认回滚
        reply = QMessageBox.question(
            self,
            "确认回滚",
            f"确定要回滚到Tag '{tag_name}' 吗？\n\n"
            f"这将记录回滚操作，但不会自动修改Podfile。",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # 执行回滚
            rollback_info = self.history_manager.rollback_to_tag(
                self.project_path, self.pod_name, tag_name
            )

            QMessageBox.information(
                self,
                "回滚成功",
                f"已记录回滚到Tag '{tag_name}' 的操作。\n\n"
                f"时间: {rollback_info['timestamp']}\n"
                f"前一个操作: {rollback_info.get('previous_operation', 'N/A')}",
            )

            # 刷新历史记录
            self.load_history()

    def export_history(self):
        """导出历史记录"""
        history = self.history_manager.get_pod_tag_history(
            self.project_path, self.pod_name, limit=1000
        )

        if not history:
            QMessageBox.information(self, "提示", "没有可导出的历史记录")
            return

        # 生成文本内容
        export_text = f"""Tag历史记录导出
===================
Pod名称: {self.pod_name}
项目路径: {self.project_path}
导出时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
总记录数: {len(history)}
"""

        for record in history:
            timestamp = datetime.fromisoformat(record["timestamp"])
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            operation = record.get("operation", "unknown")
            tag_name = record.get("tag_name", "N/A")
            details = record.get("details", {})

            export_text += f"""
---
时间: {time_str}
操作: {operation}
Tag: {tag_name}
"""
            if details:
                for key, value in details.items():
                    export_text += f"{key}: {value}\n"

        # 保存到文件
        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存历史记录",
            f"{self.pod_name}_tag_history.txt",
            "文本文件 (*.txt);;JSON文件 (*.json)",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(export_text)
                QMessageBox.information(self, "成功", f"历史记录已导出到:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导出失败: {str(e)}")

    def clear_old_records(self):
        """清理旧记录"""
        reply = QMessageBox.question(
            self,
            "确认清理",
            "确定要清理30天前的历史记录吗？\n\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.history_manager.clear_history(
                project_path=self.project_path,
                pod_name=self.pod_name,
                older_than_days=30,
            )

            QMessageBox.information(self, "成功", "旧记录已清理")

            # 刷新历史记录
            self.load_history()

    def update_statistics(self):
        """更新统计信息"""
        history = self.history_manager.get_pod_tag_history(
            self.project_path, self.pod_name, limit=1000
        )

        total = len(history)

        # 统计各操作类型
        operations = {}
        for record in history:
            operation = record.get("operation", "unknown")
            operations[operation] = operations.get(operation, 0) + 1

        stats_text = f"总记录数: {total} | "
        stats_text += " | ".join([f"{op}: {count}" for op, count in operations.items()])

        self.stats_label.setText(stats_text)

    def show_usage_trend(self):
        """显示使用趋势"""
        # 获取30天的使用趋势
        trend = self.history_manager.get_tag_usage_trend(
            self.project_path, self.pod_name, days=30
        )

        if trend["total"] == 0:
            QMessageBox.information(self, "提示", "没有足够的历史记录数据")
            return

        # 生成趋势报告
        trend_text = f"""Tag使用趋势报告
===================
Pod: {self.pod_name}
统计天数: 30天
总操作数: {trend["total"]}

按日期统计:
"""
        # 按日期显示操作数（按时间倒序）
        sorted_dates = sorted(trend["by_date"].keys(), reverse=True)
        for date in sorted_dates[:10]:  # 显示最近10天
            count = trend["by_date"][date]
            trend_text += f"{date}: {count} 次操作\n"

        trend_text += "\n按操作类型统计:\n"
        operation_names = {
            "create": "创建Tag",
            "switch_to_tag": "切换到Tag",
            "switch_to_normal": "恢复正常模式",
            "rollback": "回滚",
        }
        for op, count in trend["by_operation"].items():
            op_name = operation_names.get(op, op)
            trend_text += f"{op_name}: {count} 次\n"

        # 显示趋势对话框
        trend_dialog = QDialog(self)
        trend_dialog.setWindowTitle("使用趋势")
        trend_dialog.setGeometry(300, 300, 600, 500)

        trend_layout = QVBoxLayout()

        trend_edit = QTextEdit()
        trend_edit.setReadOnly(True)
        trend_edit.setFontFamily("monospace")
        trend_edit.setFontPointSize(11)
        trend_edit.setText(trend_text)
        trend_layout.addWidget(trend_edit)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(trend_dialog.accept)
        trend_layout.addWidget(close_btn)

        trend_dialog.setLayout(trend_layout)
        trend_dialog.exec_()
