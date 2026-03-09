import os
import json
from typing import Dict, Any, List, Union


class ConfigService:
    """配置管理服务"""

    def __init__(self, config_path: Union[str, None] = None):
        self.config_path = config_path or os.path.join(
            os.path.expanduser("~"), ".podpilot_config.json"
        )
        self.projects = []
        self.pods_config = {}
        self.original_pod_references = {}
        self.last_pod_modes = {}
        self.current_project = None
        self.gitlab_token = ""
        self.github_token = ""

    def load_config(self) -> bool:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            return False

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            if "pods_config" in config:
                self.pods_config = config["pods_config"]
                cleaned_pods_config = {}
                for key, value in self.pods_config.items():
                    if os.path.sep in key or key.startswith("/"):
                        cleaned_pods_config[key] = value
                self.pods_config = cleaned_pods_config

            if "original_pod_references" in config:
                self.original_pod_references = config["original_pod_references"]

            if "current_project" in config:
                self.current_project = config["current_project"]

            if "projects" in config:
                self.projects = config["projects"]

            if "gitlab_token" in config:
                self.gitlab_token = config["gitlab_token"]

            if "github_token" in config:
                self.github_token = config["github_token"]

            if "last_pod_modes" in config:
                self.last_pod_modes = config["last_pod_modes"]

            return True

        except Exception as e:
            print(f"加载配置失败: {str(e)}")
            return False

    def save_config(self) -> bool:
        """保存配置文件"""
        config = {
            "projects": self.projects,
            "pods_config": self.pods_config,
            "original_pod_references": self.original_pod_references,
            "last_pod_modes": self.last_pod_modes,
            "gitlab_token": self.gitlab_token,
            "github_token": self.github_token,
        }

        if self.current_project:
            config["current_project"] = self.current_project

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
            return False

    def add_project(self, project_name: str, project_path: str):
        """添加项目"""
        self.projects.append({"name": project_name, "path": project_path})
        self.save_config()

    def remove_project(self, project_path: str):
        """移除项目"""
        self.projects = [p for p in self.projects if p["path"] != project_path]
        if self.current_project == project_path:
            self.current_project = None
        self.save_config()

    def get_project_pods_config(self, project_path: str) -> Dict[str, str]:
        """获取指定项目的Pod配置"""
        if project_path not in self.pods_config:
            self.pods_config[project_path] = {}
        return self.pods_config[project_path]

    def set_pod_config(self, project_path: str, pod_name: str, local_path: str):
        """设置Pod配置"""
        if project_path not in self.pods_config:
            self.pods_config[project_path] = {}

        if local_path:
            self.pods_config[project_path][pod_name] = local_path
        else:
            if pod_name in self.pods_config[project_path]:
                del self.pods_config[project_path][pod_name]
        self.save_config()

    def save_original_pod_reference(
        self, project_path: str, pod_name: str, line: str, full_declaration: str
    ):
        """保存Pod的原始引用信息"""
        if project_path not in self.original_pod_references:
            self.original_pod_references[project_path] = {}

        self.original_pod_references[project_path][pod_name] = {
            "line": line,
            "full_declaration": full_declaration,
        }
        self.save_config()

    def get_original_pod_reference(
        self, project_path: str, pod_name: str
    ) -> Union[Dict[str, Any], None]:
        """获取Pod的原始引用信息"""
        if (
            project_path in self.original_pod_references
            and pod_name in self.original_pod_references[project_path]
        ):
            return self.original_pod_references[project_path][pod_name]
        return None

    def save_last_pod_mode(
        self, project_path: str, pod_name: str, mode: str, mode_data: Dict[str, Any]
    ):
        """保存 Pod 的上次模式信息

        Args:
            project_path: 项目路径
            pod_name: Pod 名称
            mode: 模式类型 ('branch', 'tag', 'git')
            mode_data: 模式数据 (如 {'branch': 'feature/test'})
        """
        if project_path not in self.last_pod_modes:
            self.last_pod_modes[project_path] = {}

        self.last_pod_modes[project_path][pod_name] = {"mode": mode, "data": mode_data}
        self.save_config()

    def get_last_pod_mode(
        self, project_path: str, pod_name: str
    ) -> Union[Dict[str, Any], None]:
        """获取 Pod 的上次模式信息

        Args:
            project_path: 项目路径
            pod_name: Pod 名称

        Returns:
            上次模式信息，如 {'mode': 'branch', 'data': {'branch': 'feature/test'}}
            如果没有记录返回 None
        """
        if (
            project_path in self.last_pod_modes
            and pod_name in self.last_pod_modes[project_path]
        ):
            return self.last_pod_modes[project_path][pod_name]
        return None
