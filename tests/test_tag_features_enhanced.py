"""
Tag功能阶段二增强功能测试
测试改进的TagValidator和TagHistoryManager功能
"""

import unittest
import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.models.tag_validator import TagValidator
from src.models.tag_history_manager import TagHistoryManager


class TestTagValidatorEnhanced(unittest.TestCase):
    """TagValidator增强功能测试"""

    def test_compare_prerelease_versions(self):
        """测试预发布版本比较"""
        test_cases = [
            ("v1.0.0-alpha.1", "v1.0.0-alpha.2", -1),
            ("v1.0.0-alpha.2", "v1.0.0-alpha.1", 1),
            ("v1.0.0-alpha.1", "v1.0.0-beta.1", -1),
            ("v1.0.0-beta.1", "v1.0.0-rc.1", -1),
            ("v1.0.0-alpha.1", "v1.0.0-alpha.1", 0),
        ]

        for v1, v2, expected in test_cases:
            result = TagValidator.compare_versions(v1, v2)
            self.assertEqual(
                result,
                expected,
                f"比较 {v1} 和 {v2} 应该返回 {expected}，实际返回 {result}",
            )

    def test_compare_complex_prerelease(self):
        """测试复杂的预发布版本比较"""
        # 测试预发布版本号
        result = TagValidator.compare_versions("v1.0.0-alpha.10", "v1.0.0-alpha.2")
        self.assertEqual(result, 1)

        # 测试不同类型的预发布版本
        result = TagValidator.compare_versions("v1.0.0-rc.1", "v1.0.0-beta.10")
        self.assertEqual(result, 1)


class TestTagHistoryManagerEnhanced(unittest.TestCase):
    """TagHistoryManager增强功能测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "enhanced_test_config.json")
        self.manager = TagHistoryManager(self.config_path)
        self.project_path = "/path/to/project"
        self.pod_name = "TestPod"

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_get_pod_tag_history_with_operation_type(self):
        """测试按操作类型筛选历史记录"""
        # 记录不同类型的操作
        operations = [
            ("create", "v1.0.0", {}),
            ("switch_to_tag", "v1.0.0", {}),
            ("switch_to_normal", None, {}),
            ("create", "v1.0.1", {}),
            ("switch_to_tag", "v1.0.1", {}),
        ]

        for operation, tag_name, details in operations:
            self.manager.record_tag_operation(
                self.project_path, self.pod_name, operation, tag_name, details
            )

        # 测试筛选create操作
        create_history = self.manager.get_pod_tag_history(
            self.project_path, self.pod_name, operation_type="create"
        )
        self.assertEqual(len(create_history), 2)
        for record in create_history:
            self.assertEqual(record["operation"], "create")

        # 测试筛选switch_to_tag操作
        switch_history = self.manager.get_pod_tag_history(
            self.project_path, self.pod_name, operation_type="switch_to_tag"
        )
        self.assertEqual(len(switch_history), 2)

    def test_search_tag_history(self):
        """测试搜索tag历史记录"""
        # 记录一些操作
        self.manager.record_tag_operation(
            self.project_path, self.pod_name, "create", "v1.0.0", {}
        )
        self.manager.record_tag_operation(
            self.project_path, self.pod_name, "create", "v1.0.1", {}
        )
        self.manager.record_tag_operation(
            self.project_path, self.pod_name, "create", "v2.0.0", {}
        )

        # 搜索包含"1.0"的记录
        results = self.manager.search_tag_history(
            project_path=self.project_path, pod_name=self.pod_name, tag_name="1.0"
        )
        self.assertEqual(len(results), 2)  # v1.0.0 和 v1.0.1

        # 搜索不存在的tag
        results = self.manager.search_tag_history(
            project_path=self.project_path, pod_name=self.pod_name, tag_name="999.0.0"
        )
        self.assertEqual(len(results), 0)

    def test_search_by_date_range(self):
        """测试按日期范围搜索"""
        now = datetime.now()
        old_time = now - timedelta(days=40)

        # 手动创建不同时间的记录
        key = f"{self.project_path}:{self.pod_name}"
        self.manager.history[key] = [
            {
                "timestamp": old_time.isoformat(),
                "operation": "create",
                "tag_name": "v0.9.0",
                "details": {},
            },
            {
                "timestamp": now.isoformat(),
                "operation": "create",
                "tag_name": "v1.0.0",
                "details": {},
            },
        ]

        # 搜索最近30天的记录
        results = self.manager.search_tag_history(
            project_path=self.project_path,
            pod_name=self.pod_name,
            start_date=now - timedelta(days=30),
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["tag_name"], "v1.0.0")

    def test_get_tag_usage_trend(self):
        """测试获取使用趋势"""
        # 记录一些操作
        for i in range(10):
            self.manager.record_tag_operation(
                self.project_path, self.pod_name, "create", f"v1.0.{i}", {}
            )

        # 获取趋势
        trend = self.manager.get_tag_usage_trend(
            project_path=self.project_path, pod_name=self.pod_name, days=30
        )

        # 验证趋势数据
        self.assertGreater(trend["total"], 0)
        self.assertIn("by_date", trend)
        self.assertIn("by_operation", trend)
        self.assertIn("create", trend["by_operation"])

    def test_trend_data_accuracy(self):
        """测试趋势数据准确性"""
        # 记录特定日期的操作
        now = datetime.now()
        past_5_days = now - timedelta(days=5)
        past_15_days = now - timedelta(days=15)

        key = f"{self.project_path}:{self.pod_name}"
        self.manager.history[key] = [
            {
                "timestamp": past_15_days.isoformat(),
                "operation": "create",
                "tag_name": "v1.0.0",
                "details": {},
            },
            {
                "timestamp": past_5_days.isoformat(),
                "operation": "create",
                "tag_name": "v1.0.1",
                "details": {},
            },
            {
                "timestamp": now.isoformat(),
                "operation": "create",
                "tag_name": "v1.0.2",
                "details": {},
            },
        ]

        # 获取趋势
        trend = self.manager.get_tag_usage_trend(
            project_path=self.project_path,
            pod_name=self.pod_name,
            days=10,  # 只统计最近10天
        )

        # 应该只包含最近5天的记录（过去15天的不在10天内）
        self.assertEqual(trend["total"], 2)
        self.assertIn("v1.0.1", [r["tag_name"] for r in self.manager.history[key][-2:]])


class TestEnhancedIntegration(unittest.TestCase):
    """增强功能的集成测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "integration_enhanced_test.json")
        self.manager = TagHistoryManager(self.config_path)

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_complete_enhanced_workflow(self):
        """测试完整的增强工作流"""
        project_path = "/path/to/project"
        pod_name = "TestPod"

        # 1. 创建多个tag
        tags = ["v1.0.0", "v1.0.1", "v1.0.2", "v1.1.0", "v2.0.0"]
        for tag in tags:
            self.manager.record_tag_operation(project_path, pod_name, "create", tag, {})

        # 2. 按操作类型筛选
        create_history = self.manager.get_pod_tag_history(
            project_path, pod_name, operation_type="create"
        )
        self.assertEqual(len(create_history), 5)

        # 3. 搜索特定tag
        results = self.manager.search_tag_history(
            project_path=project_path, pod_name=pod_name, tag_name="v1.0"
        )
        # v1.0.0, v1.0.1, v1.0.2都包含"v1.0"
        self.assertEqual(len(results), 3)

        # 4. 获取趋势
        trend = self.manager.get_tag_usage_trend(
            project_path=project_path, pod_name=pod_name, days=30
        )
        self.assertGreater(trend["total"], 0)

        # 5. 验证版本比较
        comparison = TagValidator.compare_versions("v1.0.1", "v1.0.0")
        self.assertEqual(comparison, 1)

        comparison = TagValidator.compare_versions("v1.0.0-alpha.1", "v1.0.0-alpha.2")
        self.assertEqual(comparison, -1)


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)
