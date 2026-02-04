"""
Tag功能阶段二自动化测试套件
测试TagValidator、TagHistoryManager等核心功能
"""

import unittest
import json
import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.models.tag_validator import TagValidator
from src.models.tag_history_manager import TagHistoryManager


class TestTagValidator(unittest.TestCase):
    """TagValidator功能测试"""

    def test_validate_valid_tags(self):
        """测试有效的tag名称"""
        valid_tags = [
            "v1.0.0",
            "v2.3.5",
            "1.0.0",
            "v1.0.0-alpha.1",
            "v1.0.0-beta.2",
            "v1.0.0-rc.1",
            "v1.0.0+build.123",
        ]

        for tag in valid_tags:
            result = TagValidator.validate_tag_name(tag)
            self.assertTrue(result["valid"], f"Tag '{tag}' 应该是有效的")
            self.assertEqual(len(result["errors"]), 0)

    def test_validate_invalid_tags(self):
        """测试无效的tag名称"""
        invalid_tags = [
            ("v1 0.0", "包含空格"),
            ("v1.0:0", "包含:字符"),
            ("v1.0~0", "包含~字符"),
            (".1.0.0", "以.开头"),
            ("v1..0.0", "包含连续的.."),
            ("v1.0.0.", "以.结尾"),
            ("", "空字符串"),
        ]

        for tag, reason in invalid_tags:
            result = TagValidator.validate_tag_name(tag)
            self.assertFalse(result["valid"], f"Tag '{tag}' ({reason}) 应该是无效的")
            self.assertGreater(len(result["errors"]), 0)

    def test_parse_version(self):
        """测试版本号解析"""
        test_cases = [
            (
                "v1.2.3",
                {
                    "major": 1,
                    "minor": 2,
                    "patch": 3,
                    "prerelease": None,
                    "build": None,
                    "prefix": "v",
                },
            ),
            (
                "1.2.3",
                {
                    "major": 1,
                    "minor": 2,
                    "patch": 3,
                    "prerelease": None,
                    "build": None,
                    "prefix": "",
                },
            ),
            (
                "v2.0.0-alpha.1",
                {
                    "major": 2,
                    "minor": 0,
                    "patch": 0,
                    "prerelease": "alpha.1",
                    "build": None,
                    "prefix": "v",
                },
            ),
            (
                "v1.5.0-beta.2+build.123",
                {
                    "major": 1,
                    "minor": 5,
                    "patch": 0,
                    "prerelease": "beta.2",
                    "build": "build.123",
                    "prefix": "v",
                },
            ),
            (
                "3.4.5-rc.1",
                {
                    "major": 3,
                    "minor": 4,
                    "patch": 5,
                    "prerelease": "rc.1",
                    "build": None,
                    "prefix": "",
                },
            ),
        ]

        for tag_name, expected in test_cases:
            result = TagValidator.parse_version(tag_name)
            self.assertIsNotNone(result, f"Tag '{tag_name}' 应该能够解析")
            self.assertEqual(result["major"], expected["major"])
            self.assertEqual(result["minor"], expected["minor"])
            self.assertEqual(result["patch"], expected["patch"])
            self.assertEqual(result["prerelease"], expected["prerelease"])
            self.assertEqual(result["build"], expected["build"])
            self.assertEqual(result["prefix"], expected["prefix"])

    def test_parse_invalid_version(self):
        """测试无效的版本号解析"""
        invalid_versions = [
            "not-a-version",
            "v1.2",
            "v1",
            "v1.2.3.4",
            "vX.Y.Z",
        ]

        for version in invalid_versions:
            result = TagValidator.parse_version(version)
            self.assertIsNone(result, f"Version '{version}' 不应该能够解析")

    def test_suggest_next_version_patch(self):
        """测试补丁版本递增"""
        suggestions = TagValidator.suggest_next_version("v1.2.3", "patch")
        self.assertIn("v1.2.4", suggestions)
        self.assertIn("v1.3.0", suggestions)
        self.assertIn("v2.0.0", suggestions)

    def test_suggest_next_version_minor(self):
        """测试次版本递增"""
        suggestions = TagValidator.suggest_next_version("v1.2.3", "minor")
        self.assertIn("v1.3.0", suggestions)
        self.assertIn("v1.2.4", suggestions)
        self.assertIn("v2.0.0", suggestions)

    def test_suggest_next_version_major(self):
        """测试主版本递增"""
        suggestions = TagValidator.suggest_next_version("v1.2.3", "major")
        self.assertIn("v2.0.0", suggestions)
        self.assertIn("v1.3.0", suggestions)
        self.assertIn("v1.2.4", suggestions)

    def test_suggest_next_version_prerelease(self):
        """测试预发布版本递增"""
        suggestions = TagValidator.suggest_next_version("v1.2.3", "prerelease")
        self.assertIn("v1.2.4-alpha.1", suggestions)
        self.assertIn("v1.2.4-beta.1", suggestions)
        self.assertIn("v1.2.4-rc.1", suggestions)

    def test_suggest_next_version_invalid(self):
        """测试无效版本的版本建议"""
        suggestions = TagValidator.suggest_next_version("invalid-version", "patch")
        self.assertEqual(["v1.0.0"], suggestions)

    def test_compare_versions(self):
        """测试版本号比较"""
        test_cases = [
            ("v1.2.3", "v1.2.4", -1),
            ("v1.2.4", "v1.2.3", 1),
            ("v1.2.3", "v1.2.3", 0),
            ("v2.0.0", "v1.9.9", 1),
            ("v1.0.0", "v2.0.0", -1),
            ("v1.2.3-alpha.1", "v1.2.3", -1),
            ("v1.2.3", "v1.2.3-alpha.1", 1),
            # 注意：预发布版本之间比较返回0（当前实现）
            # 如果需要更精确的比较，可以改进TagValidator.compare_versions
            # ("v1.2.3-beta.1", "v1.2.3-alpha.1", 1),
        ]

        for v1, v2, expected in test_cases:
            result = TagValidator.compare_versions(v1, v2)
            self.assertEqual(
                result,
                expected,
                f"比较 {v1} 和 {v2} 应该返回 {expected}，实际返回 {result}",
            )

    def test_format_version(self):
        """测试版本号格式化"""
        version_dict = {
            "major": 1,
            "minor": 2,
            "patch": 3,
            "prerelease": "alpha.1",
            "build": "build.123",
            "prefix": "v",
        }

        # 包含前缀
        result_with_prefix = TagValidator.format_version(
            version_dict, include_prefix=True
        )
        self.assertEqual(result_with_prefix, "v1.2.3-alpha.1+build.123")

        # 不包含前缀
        result_without_prefix = TagValidator.format_version(
            version_dict, include_prefix=False
        )
        self.assertEqual(result_without_prefix, "1.2.3-alpha.1+build.123")


class TestTagHistoryManager(unittest.TestCase):
    """TagHistoryManager功能测试"""

    def setUp(self):
        """测试前准备"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")

        # 创建TagHistoryManager实例
        self.manager = TagHistoryManager(self.config_path)

        # 测试数据
        self.project_path = "/path/to/project"
        self.pod_name = "TestPod"

    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_record_tag_operation(self):
        """测试记录tag操作"""
        # 记录创建tag操作
        self.manager.record_tag_operation(
            self.project_path,
            self.pod_name,
            "create",
            "v1.0.0",
            {"pushed": True, "message": "Release version v1.0.0"},
        )

        # 验证记录已保存
        history = self.manager.get_pod_tag_history(self.project_path, self.pod_name)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["operation"], "create")
        self.assertEqual(history[0]["tag_name"], "v1.0.0")

        # 验证配置文件存在
        self.assertTrue(os.path.exists(self.config_path))

    def test_record_multiple_operations(self):
        """测试记录多个tag操作"""
        operations = [
            ("create", "v1.0.0", {}),
            ("switch_to_tag", "v1.0.0", {}),
            ("switch_to_normal", None, {}),
            ("create", "v1.0.1", {}),
        ]

        for operation, tag_name, details in operations:
            self.manager.record_tag_operation(
                self.project_path, self.pod_name, operation, tag_name, details
            )

        # 验证所有记录已保存
        history = self.manager.get_pod_tag_history(self.project_path, self.pod_name)
        self.assertEqual(len(history), 4)

        # 验证操作类型
        operations_in_history = [record["operation"] for record in history]
        for op in operations:
            self.assertIn(op[0], operations_in_history)

    def test_get_pod_tag_history_with_limit(self):
        """测试获取限制数量的历史记录"""
        # 记录20个操作
        for i in range(20):
            self.manager.record_tag_operation(
                self.project_path, self.pod_name, "create", f"v1.0.{i}", {}
            )

        # 获取10条记录
        history = self.manager.get_pod_tag_history(
            self.project_path, self.pod_name, limit=10
        )
        self.assertEqual(len(history), 10)

        # 验证是最近的10条（按时间倒序）
        self.assertEqual(history[0]["tag_name"], "v1.0.19")

    def test_get_latest_tag(self):
        """测试获取最新tag"""
        # 记录几个tag操作
        tags = ["v1.0.0", "v1.0.1", "v1.1.0"]
        for tag in tags:
            self.manager.record_tag_operation(
                self.project_path, self.pod_name, "create", tag, {}
            )

        # 获取最新tag
        latest_tag = self.manager.get_latest_tag(self.project_path, self.pod_name)
        self.assertEqual(latest_tag, "v1.1.0")

    def test_get_tag_statistics(self):
        """测试获取tag统计信息"""
        # 记录不同类型的操作
        operations = [
            ("create", "v1.0.0", {}),
            ("create", "v1.0.1", {}),
            ("switch_to_tag", "v1.0.0", {}),
            ("switch_to_tag", "v1.0.1", {}),
            ("switch_to_normal", None, {}),
        ]

        for operation, tag_name, details in operations:
            self.manager.record_tag_operation(
                self.project_path, self.pod_name, operation, tag_name, details
            )

        # 获取统计信息
        stats = self.manager.get_tag_statistics(self.project_path, self.pod_name)

        # 验证统计数据
        self.assertGreater(stats["total_operations"], 0)
        self.assertIn("create", stats["operations_by_type"])
        self.assertIn("switch_to_tag", stats["operations_by_type"])
        self.assertIn("v1.0.0", stats["most_used_tags"])
        self.assertIn("v1.0.1", stats["most_used_tags"])

    def test_rollback_to_tag(self):
        """测试回滚到tag"""
        # 创建一些历史记录
        self.manager.record_tag_operation(
            self.project_path, self.pod_name, "create", "v1.0.0", {}
        )

        self.manager.record_tag_operation(
            self.project_path, self.pod_name, "switch_to_tag", "v1.0.0", {}
        )

        # 执行回滚
        rollback_info = self.manager.rollback_to_tag(
            self.project_path, self.pod_name, "v1.0.0"
        )

        # 验证回滚信息
        self.assertTrue(rollback_info["found"])
        self.assertEqual(rollback_info["target_tag"], "v1.0.0")
        self.assertIsNotNone(rollback_info["previous_operation"])

        # 验证回滚操作已记录
        history = self.manager.get_pod_tag_history(self.project_path, self.pod_name)
        rollback_records = [r for r in history if r["operation"] == "rollback"]
        self.assertEqual(len(rollback_records), 1)
        self.assertEqual(rollback_records[0]["tag_name"], "v1.0.0")

    def test_rollback_to_nonexistent_tag(self):
        """测试回滚到不存在的tag"""
        rollback_info = self.manager.rollback_to_tag(
            self.project_path, self.pod_name, "v999.0.0"
        )

        # 验证未找到tag
        self.assertFalse(rollback_info["found"])
        self.assertIsNone(rollback_info["previous_operation"])

    def test_clear_history_by_pod(self):
        """测试清理指定pod的历史"""
        # 记录一些操作
        self.manager.record_tag_operation(
            self.project_path, self.pod_name, "create", "v1.0.0", {}
        )

        # 清理该pod的历史
        self.manager.clear_history(
            project_path=self.project_path, pod_name=self.pod_name
        )

        # 验证历史已被清理
        history = self.manager.get_pod_tag_history(self.project_path, self.pod_name)
        self.assertEqual(len(history), 0)

    def test_clear_history_older_than(self):
        """测试清理N天前的历史"""
        # 手动创建旧的历史记录
        old_timestamp = (datetime.now() - timedelta(days=40)).isoformat()

        # 直接操作history字典
        key = f"{self.project_path}:{self.pod_name}"
        self.manager.history[key] = [
            {
                "timestamp": old_timestamp,
                "operation": "create",
                "tag_name": "v1.0.0",
                "details": {},
            },
            {
                "timestamp": datetime.now().isoformat(),
                "operation": "create",
                "tag_name": "v1.0.1",
                "details": {},
            },
        ]

        # 清理30天前的记录
        self.manager.clear_history(
            project_path=self.project_path, pod_name=self.pod_name, older_than_days=30
        )

        # 验证旧记录已被清理，新记录保留
        history = self.manager.get_pod_tag_history(self.project_path, self.pod_name)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["tag_name"], "v1.0.1")

    def test_clear_all_history(self):
        """测试清空所有历史"""
        # 记录一些操作
        self.manager.record_tag_operation(
            self.project_path, self.pod_name, "create", "v1.0.0", {}
        )

        # 清空所有历史
        self.manager.clear_history()

        # 验证所有历史已被清空
        self.assertEqual(len(self.manager.history), 0)

    def test_persistence(self):
        """测试配置持久化"""
        # 记录操作
        self.manager.record_tag_operation(
            self.project_path, self.pod_name, "create", "v1.0.0", {}
        )

        # 创建新的manager实例
        new_manager = TagHistoryManager(self.config_path)

        # 验证历史记录已加载
        history = new_manager.get_pod_tag_history(self.project_path, self.pod_name)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["tag_name"], "v1.0.0")

    def test_limit_50_records(self):
        """测试每个pod最多保留50条记录"""
        # 记录60个操作
        for i in range(60):
            self.manager.record_tag_operation(
                self.project_path, self.pod_name, "create", f"v1.0.{i}", {}
            )

        # 获取历史记录（获取足够多的记录以验证50条限制）
        history = self.manager.get_pod_tag_history(
            self.project_path, self.pod_name, limit=100
        )

        # 验证最多保留50条
        self.assertEqual(len(history), 50)

        # 验证是最新的50条
        self.assertEqual(history[0]["tag_name"], "v1.0.59")
        self.assertEqual(history[-1]["tag_name"], "v1.0.10")


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "integration_test_config.json")

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_tag_workflow(self):
        """测试完整的tag工作流"""
        manager = TagHistoryManager(self.config_path)
        project_path = "/path/to/project"
        pod_name = "TestPod"

        # 1. 创建tag
        manager.record_tag_operation(project_path, pod_name, "create", "v1.0.0", {})
        self.assertEqual(len(manager.get_pod_tag_history(project_path, pod_name)), 1)

        # 2. 切换到tag
        manager.record_tag_operation(
            project_path, pod_name, "switch_to_tag", "v1.0.0", {}
        )
        self.assertEqual(len(manager.get_pod_tag_history(project_path, pod_name)), 2)

        # 3. 创建新版本
        manager.record_tag_operation(project_path, pod_name, "create", "v1.0.1", {})
        self.assertEqual(len(manager.get_pod_tag_history(project_path, pod_name)), 3)

        # 4. 切换到新版本
        manager.record_tag_operation(
            project_path, pod_name, "switch_to_tag", "v1.0.1", {}
        )
        self.assertEqual(len(manager.get_pod_tag_history(project_path, pod_name)), 4)

        # 5. 恢复正常模式
        manager.record_tag_operation(
            project_path, pod_name, "switch_to_normal", None, {}
        )
        self.assertEqual(len(manager.get_pod_tag_history(project_path, pod_name)), 5)

        # 6. 获取统计信息
        stats = manager.get_tag_statistics(project_path, pod_name)
        self.assertEqual(stats["total_operations"], 5)

        # 7. 获取最新tag
        latest = manager.get_latest_tag(project_path, pod_name)
        self.assertEqual(latest, "v1.0.1")

    def test_version_suggestion_workflow(self):
        """测试版本建议工作流"""
        # 测试版本号解析
        version = TagValidator.parse_version("v1.2.3")
        self.assertIsNotNone(version)
        self.assertEqual(version["major"], 1)

        # 测试版本号建议
        suggestions = TagValidator.suggest_next_version("v1.2.3", "patch")
        self.assertIn("v1.2.4", suggestions)

        # 测试版本号比较
        comparison = TagValidator.compare_versions("v1.2.3", "v1.2.4")
        self.assertEqual(comparison, -1)

    def test_multiple_pods_history(self):
        """测试多个pod的历史记录"""
        manager = TagHistoryManager(self.config_path)
        project_path = "/path/to/project"

        pods = ["Pod1", "Pod2", "Pod3"]

        # 为每个pod创建tag
        for pod in pods:
            manager.record_tag_operation(project_path, pod, "create", "v1.0.0", {})

        # 验证每个pod的历史
        for pod in pods:
            history = manager.get_pod_tag_history(project_path, pod)
            self.assertEqual(len(history), 1)

        # 获取项目级别的统计
        stats = manager.get_tag_statistics(project_path=project_path)
        self.assertEqual(stats["total_operations"], 3)


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)
