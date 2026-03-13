from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QTextEdit,
    QComboBox,
    QFrame,
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
from src.styles import Colors, Styles, GlassmorphismStyle


class TagHistoryDialog(QDialog):
    """Tag历史记录对话框"""

    def __init__(self, project_path, pod_name, config_path, parent=None):
        super().__init__(parent)
        self._titlebar_setup = False
        self.project_path = project_path
        self.pod_name = pod_name
        self.config_path = config_path
        self.history_manager = TagHistoryManager(config_path)
        self.initUI()
        self.load_history()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._titlebar_setup:
            GlassmorphismStyle.setup_transparent_titlebar(self)
            self._titlebar_setup = True

    def initUI(self):
        self.setWindowTitle(f"Tag历史记录 - {self.pod_name}")
        self.setGeometry(300, 300, 900, 650)

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        filter_card = QFrame()
        filter_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.SURFACE_BORDER};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        filter_layout = QGridLayout(filter_card)
        filter_layout.setSpacing(12)

        filter_layout.addWidget(self._create_label("操作类型:"), 0, 0)
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

        filter_layout.addWidget(self._create_label("显示数量:"), 0, 2)
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(["20", "50", "100", "200"])
        self.limit_combo.setCurrentText("50")
        self.limit_combo.currentIndexChanged.connect(self.load_history)
        filter_layout.addWidget(self.limit_combo, 0, 3)

        filter_layout.addWidget(self._create_label("搜索关键词:"), 1, 0)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入Tag/分支/路径搜索...")
        self.search_edit.textChanged.connect(self.filter_history)
        filter_layout.addWidget(self.search_edit, 1, 1)

        filter_layout.addWidget(self._create_label("开始日期:"), 1, 2)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDateRange(
            self.start_date_edit.minimumDate(), self.start_date_edit.maximumDate()
        )
        self.start_date_edit.setDate(self.start_date_edit.minimumDate())
        filter_layout.addWidget(self.start_date_edit, 1, 3)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_history)
        btn_layout.addWidget(refresh_btn)

        clear_btn = QPushButton("清理旧记录")
        clear_btn.clicked.connect(self.clear_old_records)
        btn_layout.addWidget(clear_btn)

        trend_btn = QPushButton("使用趋势")
        trend_btn.clicked.connect(self.show_usage_trend)
        btn_layout.addWidget(trend_btn)

        filter_layout.addLayout(btn_layout, 2, 0, 1, 4)

        layout.addWidget(filter_card)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        left_widget = QFrame()
        left_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.SURFACE_BORDER};
                border-radius: 12px;
            }}
        """)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        left_layout.addWidget(self._create_section_label("历史记录"))
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.show_history_detail)
        left_layout.addWidget(self.history_list)

        splitter.addWidget(left_widget)

        right_widget = QFrame()
        right_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.SURFACE_BORDER};
                border-radius: 12px;
            }}
        """)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        right_layout.addWidget(self._create_section_label("详细信息"))
        self.detail_edit = QTextEdit()
        self.detail_edit.setReadOnly(True)
        right_layout.addWidget(self.detail_edit)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)

        rollback_btn = QPushButton("回滚到此Tag")
        rollback_btn.clicked.connect(self.rollback_to_selected)
        action_layout.addWidget(rollback_btn)

        export_btn = QPushButton("导出记录")
        export_btn.clicked.connect(self.export_history)
        action_layout.addWidget(export_btn)

        right_layout.addLayout(action_layout)

        splitter.addWidget(right_widget)
        splitter.setSizes([400, 400])

        stats_label = QLabel()
        stats_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_MUTED};
                font-size: 11px;
                padding: 4px 8px;
            }}
        """)
        layout.addWidget(stats_label)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)
        self.stats_label = stats_label

        self._apply_styles()

    def _create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_LABEL};
                font-size: 12px;
                font-weight: 500;
            }}
        """)
        return label

    def _create_section_label(self, text):
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: 13px;
                font-weight: 600;
            }}
        """)
        return label

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.BG_GRADIENT_START},
                    stop:0.5 {Colors.BG_GRADIENT_MID},
                    stop:1 {Colors.BG_GRADIENT_END}
                );
            }}
            QWidget {{
                color: {Colors.TEXT_PRIMARY};
                font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
            }}
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.15);
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.25);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            QComboBox {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 6px 12px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 12px;
                min-height: 28px;
            }}
            QComboBox:hover {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid rgba(255, 255, 255, 0.6);
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: rgba(26, 26, 46, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 4px;
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: rgba(255, 255, 255, 0.2);
            }}
            QListWidget {{
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                padding: 8px;
                outline: none;
            }}
            QListWidget::item {{
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px 12px;
                margin: 2px 4px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QListWidget::item:hover:!selected {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
            QListWidget::item:selected {{
                background-color: rgba(255, 255, 255, 0.25);
            }}
            QTextEdit {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 12px;
                font-family: "SF Mono", "Menlo", "Monaco", monospace;
            }}
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 6px 12px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 12px;
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
            QDateEdit {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 6px 12px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 12px;
            }}
            QDateEdit:hover {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 20px;
            }}
            QDateEdit::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid rgba(255, 255, 255, 0.6);
                margin-right: 8px;
            }}
            QCalendarWidget {{
                background-color: rgba(26, 26, 46, 0.95);
                color: {Colors.TEXT_PRIMARY};
            }}
            QCalendarWidget QToolButton {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {Colors.TEXT_PRIMARY};
                border-radius: 4px;
                padding: 4px;
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            QCalendarWidget QMenu {{
                background-color: rgba(26, 26, 46, 0.95);
            }}
            QCalendarWidget QSpinBox {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 2px;
            }}
            QCalendarWidget QTableView {{
                background-color: rgba(255, 255, 255, 0.05);
                selection-background-color: rgba(102, 126, 234, 0.4);
                alternate-background-color: rgba(255, 255, 255, 0.03);
                gridline-color: rgba(255, 255, 255, 0.1);
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.2);
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 0.3);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

    def load_history(self):
        """加载历史记录"""
        self.history_list.clear()

        limit = int(self.limit_combo.currentText())
        operation_filter = self.operation_combo.currentText()
        search_text = self.search_edit.text().strip()

        if operation_filter != "全部":
            history = self.history_manager.get_pod_tag_history(
                self.project_path, self.pod_name, limit, operation_type=operation_filter
            )
        else:
            history = self.history_manager.get_pod_tag_history(
                self.project_path, self.pod_name, limit
            )

        if search_text:
            history = [
                record
                for record in history
                if record.get("tag_name", "").lower().find(search_text.lower()) >= 0
            ]

        for record in history:
            timestamp = datetime.fromisoformat(record["timestamp"])
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            operation = record.get("operation", "unknown")
            tag_name = record.get("tag_name", "N/A")

            operation_names = {
                "create": "创建Tag",
                "switch_to_tag": "切换到Tag",
                "switch_to_normal": "恢复正常模式",
                "rollback": "回滚",
            }

            display_text = (
                f"{time_str} - {operation_names.get(operation, operation)}: {tag_name}"
            )
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, record)
            self.history_list.addItem(item)

        if not history:
            help_text = QListWidgetItem("没有历史记录")
            help_text.setForeground(QColor(Colors.TEXT_MUTED))
            help_text.setTextAlignment(Qt.AlignCenter)
            self.history_list.addItem(help_text)
            help_item = QListWidgetItem("创建或切换Tag后，记录将显示在这里")
            help_item.setForeground(QColor(Colors.TEXT_MUTED))
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
            ModernDialog.warning(self, "警告", "请先选择一条历史记录")
            return

        record = current_item.data(Qt.UserRole)
        if not record or not record.get("tag_name"):
            ModernDialog.warning(self, "警告", "所选记录没有Tag信息")
            return

        tag_name = record["tag_name"]

        reply = ModernDialog.question(
            self,
            "确认回滚",
            f"确定要回滚到Tag '{tag_name}' 吗？\n\n"
            f"这将记录回滚操作，但不会自动修改Podfile。",
            ModernDialog.Yes | ModernDialog.No,
        )

        if reply == ModernDialog.Yes:
            rollback_info = self.history_manager.rollback_to_tag(
                self.project_path, self.pod_name, tag_name
            )

            ModernDialog.information(
                self,
                "回滚成功",
                f"已记录回滚到Tag '{tag_name}' 的操作。\n\n"
                f"时间: {rollback_info['timestamp']}\n"
                f"前一个操作: {rollback_info.get('previous_operation', 'N/A')}",
            )

            self.load_history()

    def export_history(self):
        """导出历史记录"""
        history = self.history_manager.get_pod_tag_history(
            self.project_path, self.pod_name, limit=1000
        )

        if not history:
            ModernDialog.information(self, "提示", "没有可导出的历史记录")
            return

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

        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存历史记录",
            f"{self.pod_name}_tag_history.txt",
            "文本文件;;JSON文件",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(export_text)
                ModernDialog.information(self, "成功", f"历史记录已导出到:\n{file_path}")
            except Exception as e:
                ModernDialog.warning(self, "错误", f"导出失败: {str(e)}")

    def clear_old_records(self):
        """清理旧记录"""
        reply = ModernDialog.question(
            self,
            "确认清理",
            "确定要清理30天前的历史记录吗？\n\n此操作不可撤销。",
            ModernDialog.Yes | ModernDialog.No,
        )

        if reply == ModernDialog.Yes:
            self.history_manager.clear_history(
                project_path=self.project_path,
                pod_name=self.pod_name,
                older_than_days=30,
            )

            ModernDialog.information(self, "成功", "旧记录已清理")

            self.load_history()

    def update_statistics(self):
        """更新统计信息"""
        history = self.history_manager.get_pod_tag_history(
            self.project_path, self.pod_name, limit=1000
        )

        total = len(history)

        operations = {}
        for record in history:
            operation = record.get("operation", "unknown")
            operations[operation] = operations.get(operation, 0) + 1

        stats_text = f"总记录数: {total} | "
        stats_text += " | ".join([f"{op}: {count}" for op, count in operations.items()])

        self.stats_label.setText(stats_text)

    def show_usage_trend(self):
        """显示使用趋势"""
        trend = self.history_manager.get_tag_usage_trend(
            self.project_path, self.pod_name, days=30
        )

        if trend["total"] == 0:
            ModernDialog.information(self, "提示", "没有足够的历史记录数据")
            return

        trend_text = f"""Tag使用趋势报告
===================
Pod: {self.pod_name}
统计天数: 30天
总操作数: {trend["total"]}

按日期统计:
"""
        sorted_dates = sorted(trend["by_date"].keys(), reverse=True)
        for date in sorted_dates[:10]:
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

        trend_dialog = QDialog(self)
        trend_dialog.setWindowTitle("使用趋势")
        trend_dialog.setGeometry(300, 300, 600, 500)

        trend_layout = QVBoxLayout()
        trend_layout.setSpacing(16)
        trend_layout.setContentsMargins(20, 20, 20, 20)

        trend_edit = QTextEdit()
        trend_edit.setReadOnly(True)
        trend_edit.setText(trend_text)
        trend_layout.addWidget(trend_edit)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(trend_dialog.accept)
        trend_layout.addWidget(close_btn)

        trend_dialog.setLayout(trend_layout)

        trend_dialog.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.BG_GRADIENT_START},
                    stop:0.5 {Colors.BG_GRADIENT_MID},
                    stop:1 {Colors.BG_GRADIENT_END}
                );
            }}
            QTextEdit {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 12px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 12px;
                font-family: "SF Mono", "Menlo", "Monaco", monospace;
            }}
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.15);
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.25);
            }}
        """)

        trend_dialog.exec_()
