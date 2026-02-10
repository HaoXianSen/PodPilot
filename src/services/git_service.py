import subprocess
import os
from typing import List, Optional


class GitService:
    """Git操作服务"""

    @staticmethod
    def get_username() -> str:
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

    @staticmethod
    def get_remote_tags(local_path: str) -> List[str]:
        """获取远程Tag列表"""
        import re

        try:
            result = subprocess.run(
                ["git", "ls-remote", "--tags", "origin"],
                cwd=local_path,
                capture_output=True,
                text=True,
                check=True,
            )
            remote_refs = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )

            remote_tags = []
            for ref in remote_refs:
                if ref and "\t" in ref:
                    tag_name = ref.split("\t")[1].replace("refs/tags/", "")
                    if "^{}" in tag_name:
                        continue
                    if re.match(r"v?\d+\.\d+\.\d+", tag_name):
                        remote_tags.append(tag_name)

            remote_tags.sort(
                key=lambda x: [int(v) for v in re.findall(r"\d+", x)], reverse=True
            )

            return remote_tags
        except subprocess.CalledProcessError:
            return []

    @staticmethod
    def get_branches(local_path: str) -> List[str]:
        """获取分支列表"""
        try:
            result = subprocess.run(
                ["git", "branch", "-a"],
                capture_output=True,
                text=True,
                cwd=local_path,
                check=True,
            )
            branches = result.stdout.strip().split("\n")
            branches = [b.replace("*", "").strip() for b in branches if b.strip()]
            # 过滤掉 HEAD 指向和包含 HEAD -> 的分支
            branches = [b for b in branches if not b.startswith("HEAD ->")]
            branches = [b for b in branches if "HEAD ->" not in b]

            # 只保留远程分支，并保留完整的 origin/xxx 格式
            branches = [
                b.replace("remotes/", "")
                for b in branches
                if b.startswith("remotes/origin/")
            ]

            return branches
        except subprocess.CalledProcessError:
            return []

    @staticmethod
    def get_current_branch(local_path: str) -> str:
        """获取当前分支"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=local_path,
                check=True,
            )
            return result.stdout.strip()
        except:
            return "未知"

    @staticmethod
    def get_tags_info(local_path: str, pod_name: str) -> str:
        """获取Tag历史信息"""
        try:
            result = subprocess.run(
                ["git", "tag", "--sort=-version:refname", "-n9"],
                cwd=local_path,
                capture_output=True,
                text=True,
                check=True,
            )
            tags_info = result.stdout.strip()

            if tags_info:
                return f"Pod: {pod_name}\n{'=' * 60}\n{tags_info}"
            else:
                return f"Pod: {pod_name}\n{'=' * 60}\n状态: 没有标签历史"

        except subprocess.CalledProcessError as e:
            return f"Pod: {pod_name}\n{'=' * 60}\n错误: {str(e)}"

    @staticmethod
    def get_pods_info(
        pods: List[str], pod_config: dict, get_pod_name_func
    ) -> List[dict]:
        """批量获取Pod信息（用于异步加载）"""
        pods_info = []

        for pod_name in pods:
            if pod_name not in pod_config:
                continue

            local_path = pod_config[pod_name]
            remote_tags = GitService.get_remote_tags(local_path)

            pods_info.append(
                {
                    "name": pod_name,
                    "path": local_path,
                    "remote_tags": remote_tags,
                }
            )

        return pods_info

    @staticmethod
    def get_remote_url(local_path: str) -> Optional[str]:
        """获取本地仓库的远程URL"""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=local_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    @staticmethod
    def create_branch(
        local_path: str, new_branch: str, base_branch: str = "origin/master"
    ) -> bool:
        """创建新分支"""
        try:
            subprocess.run(
                ["git", "fetch", "origin"],
                cwd=local_path,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "checkout", "-b", new_branch, base_branch],
                cwd=local_path,
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"创建分支失败: {str(e)}")
            return False

    @staticmethod
    def push_branch(local_path: str, branch: str) -> bool:
        """推送分支到远程"""
        try:
            subprocess.run(
                ["git", "push", "-u", "origin", branch],
                cwd=local_path,
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"推送分支失败: {str(e)}")
            return False
