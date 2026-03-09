"""Podfile 读取和解析工具"""

import os
from enum import Enum
from typing import List, Tuple, Dict
from src.services import PodService


class PodMode(Enum):
    """Pod 模式枚举"""

    DEV = "dev"  # 开发模式 (:path)
    BRANCH = "branch"  # 分支模式 (:branch)
    TAG = "tag"  # 标签模式 (:tag)
    GIT = "git"  # Git 模式 (:git)
    NORMAL = "normal"  # 普通模式（无特殊引用）
    CONFIGURED = "configured"  # 已配置（仅本地路径）


class PodfileReader:
    """负责读取和解析 Podfile

    职责：
    - 读取 Podfile 内容
    - 解析 Pod 列表
    - 判断 Pod 模式
    - 获取 Pod 优先级
    """

    def __init__(self, podfile_path: str):
        """初始化 PodfileReader

        Args:
            podfile_path: Podfile 文件路径
        """
        self.podfile_path = podfile_path
        self.content = ""
        self._read_file()

    def _read_file(self):
        """读取 Podfile 内容"""
        if not os.path.exists(self.podfile_path):
            raise FileNotFoundError(f"Podfile 不存在: {self.podfile_path}")

        try:
            with open(self.podfile_path, "r", encoding="utf-8") as f:
                self.content = f.read()
        except Exception as e:
            raise Exception(f"读取 Podfile 失败: {e}")

    def get_pods(self) -> Tuple[List[str], List[str], List[str], List[str], List[str]]:
        """获取所有 Pod 列表及其分类

        Returns:
            (all_pods, dev_pods, branch_pods, tag_pods, git_pods)
        """
        return PodService.load_pods_from_podfile(self.podfile_path)

    def get_pod_mode(self, pod_name: str) -> PodMode:
        """获取指定 Pod 的当前模式

        Args:
            pod_name: Pod 名称

        Returns:
            PodMode: Pod 的模式
        """
        # 获取 Pod 的完整声明
        lines = self.content.split("\n")
        _, _, full_declaration = PodService.get_full_pod_declaration(lines, pod_name)

        if full_declaration:
            mode_info = PodService.extract_pod_mode_info(full_declaration)
            mode = mode_info.get("mode", "normal")

            # 映射到 PodMode 枚举
            mode_mapping = {
                "dev": PodMode.DEV,
                "branch": PodMode.BRANCH,
                "tag": PodMode.TAG,
                "git": PodMode.GIT,
                "normal": PodMode.NORMAL,
            }

            return mode_mapping.get(mode, PodMode.NORMAL)

        return PodMode.NORMAL

    def get_pod_priority(self, pod_name: str, current_config: Dict[str, str]) -> int:
        """获取 Pod 的优先级

        Args:
            pod_name: Pod 名称
            current_config: 当前配置（Pod -> 本地路径）

        Returns:
            int: 优先级（1-6，数字越小优先级越高）
        """
        all_pods, dev_pods, branch_pods, tag_pods, git_pods = self.get_pods()

        return PodService.get_pod_priority(
            pod_name, dev_pods, branch_pods, tag_pods, git_pods, current_config
        )

    def get_pod_full_declaration(self, pod_name: str) -> str:
        """获取 Pod 的完整声明

        Args:
            pod_name: Pod 名称

        Returns:
            str: Pod 的完整声明（可能跨多行）
        """
        lines = self.content.split("\n")
        _, _, full_declaration = PodService.get_full_pod_declaration(lines, pod_name)
        return full_declaration or ""

    def get_pod_mode_info(self, pod_name: str) -> Dict[str, any]:
        """获取 Pod 的模式信息

        Args:
            pod_name: Pod 名称

        Returns:
            dict: {'mode': PodMode, 'data': {...}}
        """
        full_declaration = self.get_pod_full_declaration(pod_name)

        if full_declaration:
            mode_info = PodService.extract_pod_mode_info(full_declaration)
            mode = mode_info.get("mode", "normal")
            data = mode_info.get("data", {})

            # 映射到 PodMode 枚举
            mode_mapping = {
                "dev": PodMode.DEV,
                "branch": PodMode.BRANCH,
                "tag": PodMode.TAG,
                "git": PodMode.GIT,
                "normal": PodMode.NORMAL,
            }

            return {"mode": mode_mapping.get(mode, PodMode.NORMAL), "data": data}

        return {"mode": PodMode.NORMAL, "data": {}}
