import json
import os
from datetime import datetime


class TagHistoryManager:
    """Tag历史记录管理器"""

    def __init__(self, config_path):
        """
        初始化Tag历史管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.history = {}
        self.load_history()

    def load_history(self):
        """加载历史记录"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.history = data.get("tag_history", {})
            except Exception as e:
                print(f"加载Tag历史记录失败: {str(e)}")
                self.history = {}

    def save_history(self):
        """保存历史记录"""
        try:
            # 读取现有配置
            config = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

            # 更新tag历史
            config["tag_history"] = self.history

            # 保存配置
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"保存Tag历史记录失败: {str(e)}")

    def record_tag_operation(
        self, project_path, pod_name, operation, tag_name, details=None
    ):
        """
        记录tag操作

        Args:
            project_path: 项目路径
            pod_name: Pod名称
            operation: 操作类型（create, switch_to_tag, switch_to_normal等）
            tag_name: Tag名称
            details: 额外详情
        """
        key = f"{project_path}:{pod_name}"

        if key not in self.history:
            self.history[key] = []

        record = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "tag_name": tag_name,
            "details": details or {},
        }

        self.history[key].append(record)

        # 只保留最近50条记录
        if len(self.history[key]) > 50:
            self.history[key] = self.history[key][-50:]

        self.save_history()

    def get_pod_tag_history(
        self, project_path, pod_name, limit=10, operation_type=None
    ):
        """
        获取指定Pod的tag历史

        Args:
            project_path: 项目路径
            pod_name: Pod名称
            limit: 返回记录数限制
            operation_type: 操作类型筛选（可选）

        Returns:
            list: 历史记录列表
        """
        key = f"{project_path}:{pod_name}"

        if key not in self.history:
            return []

        # 按时间倒序排列
        history = sorted(self.history[key], key=lambda x: x["timestamp"], reverse=True)

        # 按操作类型筛选
        if operation_type:
            history = [
                record
                for record in history
                if record.get("operation") == operation_type
            ]

        return history[:limit]

    def search_tag_history(
        self,
        project_path=None,
        pod_name=None,
        tag_name=None,
        start_date=None,
        end_date=None,
    ):
        """
        搜索tag历史记录

        Args:
            project_path: 项目路径（可选）
            pod_name: Pod名称（可选）
            tag_name: Tag名称（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            list: 匹配的历史记录列表
        """
        all_records = []

        # 收集符合条件的记录
        for key, records in self.history.items():
            # 根据路径和pod名称过滤
            if project_path and not key.startswith(project_path):
                continue

            if pod_name and not key.endswith(f":{pod_name}"):
                continue

            for record in records:
                # 根据tag名称过滤（包含匹配）
                if (
                    tag_name
                    and tag_name.lower() not in record.get("tag_name", "").lower()
                ):
                    continue

                # 根据日期范围过滤
                record_time = datetime.fromisoformat(record["timestamp"])

                if start_date and record_time < start_date:
                    continue

                if end_date and record_time > end_date:
                    continue

                all_records.append(record)

        # 按时间倒序排列
        all_records.sort(key=lambda x: x["timestamp"], reverse=True)

        return all_records

    def get_tag_usage_trend(self, project_path=None, pod_name=None, days=30):
        """
        获取tag使用趋势

        Args:
            project_path: 项目路径（可选）
            pod_name: Pod名称（可选）
            days: 统计天数

        Returns:
            dict: 使用趋势数据
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)

        trend_data = {"by_date": {}, "by_operation": {}, "total": 0}

        # 遍历历史记录
        for key, records in self.history.items():
            # 根据路径和pod名称过滤
            if project_path and not key.startswith(project_path):
                continue

            if pod_name and not key.endswith(f":{pod_name}"):
                continue

            for record in records:
                record_time = datetime.fromisoformat(record["timestamp"]).timestamp()

                # 只统计指定天数内的记录
                if record_time < cutoff_time:
                    continue

                # 按日期统计
                date_str = datetime.fromisoformat(record["timestamp"]).strftime(
                    "%Y-%m-%d"
                )
                if date_str not in trend_data["by_date"]:
                    trend_data["by_date"][date_str] = 0
                trend_data["by_date"][date_str] += 1

                # 按操作类型统计
                operation = record.get("operation", "unknown")
                if operation not in trend_data["by_operation"]:
                    trend_data["by_operation"][operation] = 0
                trend_data["by_operation"][operation] += 1

                # 统计总数
                trend_data["total"] += 1

        # 按日期排序
        sorted_dates = sorted(trend_data["by_date"].keys(), reverse=True)
        trend_data["by_date"] = {
            date: trend_data["by_date"][date] for date in sorted_dates
        }

        return trend_data

    def get_latest_tag(self, project_path, pod_name):
        """
        获取指定Pod最新使用的tag

        Args:
            project_path: 项目路径
            pod_name: Pod名称

        Returns:
            str or None: 最新tag名称
        """
        history = self.get_pod_tag_history(project_path, pod_name, limit=100)

        for record in history:
            if record["tag_name"]:
                return record["tag_name"]

        return None

    def get_tag_statistics(self, project_path=None, pod_name=None):
        """
        获取tag使用统计

        Args:
            project_path: 项目路径（可选）
            pod_name: Pod名称（可选）

        Returns:
            dict: 统计信息
        """
        stats = {
            "total_operations": 0,
            "operations_by_type": {},
            "most_used_tags": {},
            "recent_activity": [],
        }

        filtered_history = {}

        # 根据参数过滤历史记录
        if project_path and pod_name:
            key = f"{project_path}:{pod_name}"
            if key in self.history:
                filtered_history[key] = self.history[key]
        elif project_path:
            for key, records in self.history.items():
                if key.startswith(project_path):
                    filtered_history[key] = records
        else:
            filtered_history = self.history

        # 统计总操作数
        for records in filtered_history.values():
            stats["total_operations"] += len(records)

            # 统计各类型操作数
            for record in records:
                operation = record["operation"]
                stats["operations_by_type"][operation] = (
                    stats["operations_by_type"].get(operation, 0) + 1
                )

                # 统计tag使用次数
                tag_name = record.get("tag_name")
                if tag_name:
                    stats["most_used_tags"][tag_name] = (
                        stats["most_used_tags"].get(tag_name, 0) + 1
                    )

        # 获取最近的活动
        all_records = []
        for records in filtered_history.values():
            all_records.extend(records)

        # 按时间倒序排列
        all_records.sort(key=lambda x: x["timestamp"], reverse=True)
        stats["recent_activity"] = all_records[:20]

        # 对最常用tag进行排序
        stats["most_used_tags"] = dict(
            sorted(stats["most_used_tags"].items(), key=lambda x: x[1], reverse=True)[
                :10
            ]
        )

        return stats

    def rollback_to_tag(self, project_path, pod_name, target_tag):
        """
        回滚到指定tag（记录回滚操作）

        Args:
            project_path: 项目路径
            pod_name: Pod名称
            target_tag: 目标tag名称

        Returns:
            dict: 回滚信息
        """
        # 查找目标tag的历史记录
        history = self.get_pod_tag_history(project_path, pod_name, limit=100)

        target_record = None
        for record in history:
            if record["tag_name"] == target_tag:
                target_record = record
                break

        rollback_info = {
            "target_tag": target_tag,
            "timestamp": datetime.now().isoformat(),
            "found": target_record is not None,
            "previous_operation": target_record if target_record else None,
        }

        # 记录回滚操作
        self.record_tag_operation(
            project_path,
            pod_name,
            "rollback",
            target_tag,
            details={"previous_operation": target_record},
        )

        return rollback_info

    def clear_history(self, project_path=None, pod_name=None, older_than_days=None):
        """
        清理历史记录

        Args:
            project_path: 项目路径（可选）
            pod_name: Pod名称（可选）
            older_than_days: 清理N天前的记录（可选）
        """
        if older_than_days:
            # 清理指定天数前的记录
            cutoff_time = datetime.now().timestamp() - (older_than_days * 24 * 3600)

            for key, records in self.history.items():
                # 根据路径和pod名称过滤
                if project_path and not key.startswith(project_path):
                    continue

                if pod_name and not key.endswith(f":{pod_name}"):
                    continue

                # 清理旧记录
                filtered_records = []
                for record in records:
                    record_time = datetime.fromisoformat(
                        record["timestamp"]
                    ).timestamp()
                    if record_time >= cutoff_time:
                        filtered_records.append(record)

                self.history[key] = filtered_records

                # 如果没有记录了，删除该key
                if not self.history[key]:
                    del self.history[key]

        elif project_path and pod_name:
            # 删除指定pod的所有历史
            key = f"{project_path}:{pod_name}"
            if key in self.history:
                del self.history[key]

        elif project_path:
            # 删除指定项目的所有历史
            keys_to_delete = [
                key for key in self.history if key.startswith(project_path)
            ]
            for key in keys_to_delete:
                del self.history[key]

        else:
            # 清空所有历史
            self.history = {}

        self.save_history()
