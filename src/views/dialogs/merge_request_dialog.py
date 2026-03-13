from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QMessageBox,
    QWidget,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QApplication,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
import os
import json
import subprocess
import re
import urllib.request
import urllib.error
import urllib.parse

from src.styles import Colors, Styles
from src.components.modern_dialog import ModernDialog
from src.widgets.loading_widget import LoadingWidget
from src.widgets.custom_dropdown import CustomDropdown
from src.components.bottom_sheet_dialog import BottomSheetDialog


def get_git_url_from_local_path(local_path):
    """从本地Git仓库获取远程URL"""
    try:
        # 先检查是否是Git仓库
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            cwd=local_path,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        # 获取Git远程URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            cwd=local_path,
            timeout=10,
            check=False,
        )
        if result.returncode == 0:
            git_url = result.stdout.strip()
            if git_url:
                return git_url

        # 尝试另一种方式获取Git远程URL
        result = subprocess.run(
            ["git", "config", "remote.origin.url"],
            capture_output=True,
            text=True,
            cwd=local_path,
            timeout=10,
            check=False,
        )
        if result.returncode == 0:
            git_url = result.stdout.strip()
            if git_url:
                return git_url

        return None
    except Exception:
        return None


class MRInfoCollector(QThread):
    """异步收集Pod的MR信息"""

    finished = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        pod_names,
        pod_config,
        project_dir,
        main_project_current_branch=None,
        main_project_git_url=None,
    ):
        super().__init__()
        self.pod_names = pod_names
        self.pod_config = pod_config
        self.project_dir = project_dir
        self.main_project_current_branch = main_project_current_branch
        self.main_project_git_url = main_project_git_url

    def _get_pod_branches_from_podfile(self, pod_name):
        """从Podfile中获取Pod引用的分支"""
        podfile_path = os.path.join(self.project_dir, "Podfile")
        if not os.path.exists(podfile_path):
            return None

        try:
            with open(podfile_path, "r") as f:
                content = f.read()

            pod_pattern = r"pod\s+['\"]([^'\"]+)['\"]"
            branch_pattern = r":branch\s*=>\s*['\"]?([^'\"\s,]+)['\"]?"
            variable_pattern = r"^(\w+)\s*=\s*['\"]([^'\"]+)['\"]\s*$"

            for m in re.finditer(pod_pattern, content):
                found_pod_name = m.group(1)

                if found_pod_name != pod_name:
                    continue

                pod_declaration_pattern = (
                    r"pod\s+['\"]"
                    + re.escape(pod_name)
                    + r"['\"].*?(?:\n\s*end|\n\s*$|\n\s*(?=pod\s+))"
                )
                pod_declaration_match = re.search(
                    pod_declaration_pattern, content[m.start() :], re.DOTALL
                )

                if pod_declaration_match:
                    pod_declaration = pod_declaration_match.group(0)
                    branch_match = re.search(branch_pattern, pod_declaration)
                    if branch_match:
                        branch_name = branch_match.group(1)

                        if not branch_name.startswith(
                            "'"
                        ) and not branch_name.startswith('"'):
                            for line in content.split("\n"):
                                var_match = re.match(variable_pattern, line.strip())
                                if var_match and var_match.group(1) == branch_name:
                                    return var_match.group(2)

                        return branch_name

            return None
        except Exception:
            return None

    def run(self):
        """收集Pod的Git信息"""
        pods_info = {}

        for pod_name in self.pod_names:
            try:
                local_path = self.pod_config.get(pod_name, "")
                if not local_path or not os.path.exists(local_path):
                    pods_info[pod_name] = {"error": "未配置本地路径或路径不存在"}
                    continue

                git_url = get_git_url_from_local_path(local_path)
                if not git_url:
                    pods_info[pod_name] = {"error": "无法获取Git URL"}
                    continue

                result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=local_path,
                    timeout=10,
                )
                current_branch = (
                    result.stdout.strip() if result.returncode == 0 else "未知"
                )

                result = subprocess.run(
                    ["git", "branch", "-r"],
                    capture_output=True,
                    text=True,
                    cwd=local_path,
                    timeout=10,
                )
                remote_branches = []
                if result.returncode == 0:
                    remote_branches = [
                        b.strip()
                        for b in result.stdout.strip().split("\n")
                        if b.strip() and "->" not in b
                    ]

                podfile_branch = self._get_pod_branches_from_podfile(pod_name)

                pods_info[pod_name] = {
                    "git_url": git_url,
                    "current_branch": current_branch,
                    "remote_branches": remote_branches,
                    "podfile_branch": podfile_branch,
                    "local_path": local_path,
                }

            except Exception as e:
                pods_info[pod_name] = {"error": str(e)}

        # 添加主工程信息
        if self.main_project_git_url:
            # 获取主工程的远程分支列表
            main_remote_branches = []
            try:
                # 主工程目录就是 self.project_dir
                result = subprocess.run(
                    ["git", "branch", "-r"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_dir,
                    timeout=10,
                )
                if result.returncode == 0:
                    main_remote_branches = [
                        b.strip()
                        for b in result.stdout.strip().split("\n")
                        if b.strip() and "->" not in b
                    ]
            except Exception:
                pass

            pods_info["主工程"] = {
                "git_url": self.main_project_git_url,
                "current_branch": self.main_project_current_branch or "未知",
                "remote_branches": main_remote_branches,
                "podfile_branch": self.main_project_current_branch,
                "is_main_project": True,
            }

        self.finished.emit(pods_info)


class MRRequestWorker(QThread):
    """异步提交MR的工作线程"""

    finished = pyqtSignal(dict)

    def __init__(self, mr_info):
        super().__init__()
        self.mr_info = mr_info

    def _parse_git_url(self, git_url):
        """解析Git URL，返回(platform, project_id/owner_repo)"""
        if "gitlab" in git_url.lower():
            match = re.search(r"gitlab[^/]*[:/](.+)\.git", git_url)
            if match:
                project_path = match.group(1)
                project_id = project_path.replace("/", "%2F")
                return "GitLab", project_id
        elif "github" in git_url.lower():
            match = re.search(r"github\.com[:/](.+?)(?:\.git)?$", git_url)
            if match:
                owner_repo = match.group(1).replace(".git", "")
                return "GitHub", owner_repo
        return None, None

    def _get_existing_gitlab_mr(
        self, gitlab_url, project_id, source_branch, target_branch, token
    ):
        """查询GitLab是否已存在指定源分支到目标分支的MR"""
        try:
            api_url = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests"
            params = {
                "source_branch": source_branch,
                "target_branch": target_branch,
                "state": "opened",
            }

            query_string = urllib.parse.urlencode(params)
            full_url = f"{api_url}?{query_string}"

            req = urllib.request.Request(full_url)
            req.add_header("PRIVATE-TOKEN", token)

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                if data and len(data) > 0:
                    return data[0]
                return None

        except Exception:
            return None

    def _parse_existing_mr_links(self, description):
        """解析已有MR描述中的私有库关联表格，去重（同一Pod保留最后一个）"""
        if not description:
            return {}

        mr_links = {}
        in_table = False
        for line in description.split("\n"):
            line = line.strip()

            if line.startswith("| 私有库名"):
                in_table = True
                continue

            if in_table:
                if line.startswith("|") and "|" in line[1:]:
                    parts = [p.strip() for p in line.split("|")[1:-1]]
                    if len(parts) >= 2:
                        pod_name = parts[0]
                        mr_link = parts[1]
                        if pod_name and mr_link and mr_link != "MR链接":
                            mr_links[pod_name] = mr_link
                elif not line.startswith("|"):
                    break

        return mr_links

    def _build_enhanced_description(self, base_description, private_mr_links):
        """构建包含私有库MR链接的增强描述"""
        description = base_description.strip()

        if private_mr_links:
            description += "\n\n## 关联的私有库 MR\n\n"
            description += "| 私有库名 | MR链接 |\n"
            description += "|---------|-------|\n"
            for pod_name, mr_url in private_mr_links.items():
                description += f"| {pod_name} | {mr_url} |\n"

        return description

    def _update_gitlab_mr_description(
        self, gitlab_url, project_id, mr_iid, new_description, token
    ):
        """更新已有GitLab MR的描述"""
        try:
            api_url = (
                f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}"
            )

            data = json.dumps({"description": new_description}).encode("utf-8")

            req = urllib.request.Request(api_url, data=data, method="PUT")
            req.add_header("PRIVATE-TOKEN", token)
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("web_url", "")

        except Exception as e:
            raise Exception(f"更新MR描述失败: {str(e)}")

    def _create_gitlab_mr(
        self,
        gitlab_url,
        project_id,
        source_branch,
        target_branch,
        title,
        description,
        token,
    ):
        """创建GitLab MR"""
        try:
            api_url = f"{gitlab_url}/api/v4/projects/{project_id}/merge_requests"

            data = json.dumps(
                {
                    "source_branch": source_branch,
                    "target_branch": target_branch,
                    "title": title,
                    "description": description,
                }
            ).encode("utf-8")

            req = urllib.request.Request(api_url, data=data)
            req.add_header("PRIVATE-TOKEN", token)
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("web_url", "")

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise Exception(f"HTTP {e.code}: {error_body}")
        except Exception as e:
            raise Exception(str(e))

    def _create_github_pr(
        self, owner_repo, source_branch, target_branch, title, description, token
    ):
        """创建GitHub PR"""
        try:
            api_url = f"https://api.github.com/repos/{owner_repo}/pulls"

            data = json.dumps(
                {
                    "title": title,
                    "head": source_branch,
                    "base": target_branch,
                    "body": description,
                }
            ).encode("utf-8")

            req = urllib.request.Request(api_url, data=data)
            req.add_header("Authorization", f"token {token}")
            req.add_header("Accept", "application/vnd.github.v3+json")
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("html_url", "")

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise Exception(f"HTTP {e.code}: {error_body}")
        except Exception as e:
            raise Exception(str(e))

    def run(self):
        """执行批量创建MR"""
        results = {}
        success_count = 0
        fail_count = 0
        private_mr_links = {}
        main_project_info = None

        # 先处理所有私有库Pod，收集MR链接
        for pod_name, info in self.mr_info.items():
            if info.get("is_main_project", False):
                main_project_info = (pod_name, info)
                continue

            try:
                git_url = info.get("git_url", "")
                source_branch = info.get("source_branch", "")
                target_branch = info.get("target_branch", "")
                title = info.get("title", "")
                description = info.get("description", "")
                gitlab_token = info.get("gitlab_token", "")
                github_token = info.get("github_token", "")

                platform, project_id = self._parse_git_url(git_url)

                if platform == "GitLab" and gitlab_token:
                    gitlab_url_base = re.search(r"(https?://[^/]+)", git_url)
                    if not gitlab_url_base:
                        raise Exception("无法解析GitLab URL")

                    gitlab_url_base = gitlab_url_base.group(1)
                    mr_url = self._create_gitlab_mr(
                        gitlab_url_base,
                        project_id,
                        source_branch,
                        target_branch,
                        title,
                        description,
                        gitlab_token,
                    )
                    results[pod_name] = {"platform": "GitLab", "mr_url": mr_url}
                    private_mr_links[pod_name] = mr_url
                    success_count += 1

                elif platform == "GitHub" and github_token:
                    pr_url = self._create_github_pr(
                        project_id,
                        source_branch,
                        target_branch,
                        title,
                        description,
                        github_token,
                    )
                    results[pod_name] = {"platform": "GitHub", "pr_url": pr_url}
                    private_mr_links[pod_name] = pr_url
                    success_count += 1
                else:
                    results[pod_name] = {"error": "不支持的平台或缺少Token"}
                    fail_count += 1

            except Exception as e:
                results[pod_name] = {"error": str(e)}
                fail_count += 1

        # 处理主工程MR（在所有私有库MR创建完成后）
        if main_project_info:
            pod_name, info = main_project_info
            try:
                git_url = info.get("git_url", "")
                source_branch = info.get("source_branch", "")
                target_branch = info.get("target_branch", "")
                title = info.get("title", "")
                description = info.get("description", "")
                gitlab_token = info.get("gitlab_token", "")

                platform, project_id = self._parse_git_url(git_url)

                if platform == "GitLab" and gitlab_token:
                    gitlab_url_base = re.search(r"(https?://[^/]+)", git_url)
                    if not gitlab_url_base:
                        raise Exception("无法解析GitLab URL")

                    gitlab_url_base = gitlab_url_base.group(1)

                    # 查询是否已存在MR
                    existing_mr = self._get_existing_gitlab_mr(
                        gitlab_url_base,
                        project_id,
                        source_branch,
                        target_branch,
                        gitlab_token,
                    )

                    if existing_mr:
                        # 已存在MR，更新描述
                        existing_description = existing_mr.get("description", "")
                        existing_mr_links = self._parse_existing_mr_links(
                            existing_description
                        )

                        # 合并私有库MR链接
                        merged_links = {**existing_mr_links, **private_mr_links}

                        # 构建增强描述
                        enhanced_description = self._build_enhanced_description(
                            description, merged_links
                        )

                        # 更新MR描述
                        mr_iid = existing_mr.get("iid")
                        mr_url = self._update_gitlab_mr_description(
                            gitlab_url_base,
                            project_id,
                            mr_iid,
                            enhanced_description,
                            gitlab_token,
                        )
                        results[pod_name] = {
                            "platform": "GitLab",
                            "mr_url": mr_url,
                            "action": "updated",
                        }
                        success_count += 1
                    else:
                        # 不存在MR，创建新的
                        enhanced_description = self._build_enhanced_description(
                            description, private_mr_links
                        )

                        mr_url = self._create_gitlab_mr(
                            gitlab_url_base,
                            project_id,
                            source_branch,
                            target_branch,
                            title,
                            enhanced_description,
                            gitlab_token,
                        )
                        results[pod_name] = {
                            "platform": "GitLab",
                            "mr_url": mr_url,
                            "action": "created",
                        }
                        success_count += 1
                else:
                    results[pod_name] = {"error": "不支持的平台或缺少Token"}
                    fail_count += 1

            except Exception as e:
                results[pod_name] = {"error": str(e)}
                fail_count += 1

        self.finished.emit(
            {
                "success_count": success_count,
                "fail_count": fail_count,
                "results": results,
            }
        )


class MergeRequestDialog(BottomSheetDialog):
    """Merge Request对话框 - Bottom Sheet 风格（卡片式布局）"""

    def __init__(self, pods_info, parent=None, config=None, main_project_info=None):
        # 将主工程信息添加到pods_info中
        if main_project_info:
            self.pods_info = pods_info.copy()
            project_name = main_project_info.get("name", "主工程")
            self.pods_info[project_name] = main_project_info
        else:
            self.pods_info = pods_info

        self.parent_manager = parent
        self.config = config or {}
        self.mr_configs = {}
        self.mr_worker = None
        self.loading_widget = None
        self.pod_cards = []

        super().__init__(parent, title="创建 Merge Request", max_height_ratio=0.85)

        self._build_content()
        self._apply_content_styles()
        self.load_tokens_from_config()
        self.load_pods_info()
        self.setup_sheet_ui()

    def _build_content(self):
        """构建内容区域"""
        # Token 配置区域
        token_section = QFrame()
        token_section.setObjectName("tokenSection")
        token_section.setStyleSheet(f"""
            QFrame#tokenSection {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        token_layout = QVBoxLayout(token_section)
        token_layout.setSpacing(12)

        token_title = QLabel("访问令牌配置")
        token_title.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        token_layout.addWidget(token_title)

        # GitLab Token
        gitlab_row = QHBoxLayout()
        gitlab_row.setSpacing(12)

        gitlab_label = QLabel("GitLab Token:")
        gitlab_label.setFixedWidth(100)
        gitlab_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        gitlab_row.addWidget(gitlab_label)

        self.gitlab_token_input = QLineEdit()
        self.gitlab_token_input.setEchoMode(QLineEdit.Password)
        self.gitlab_token_input.setPlaceholderText("输入 GitLab 访问令牌")
        self.gitlab_token_input.setStyleSheet(Styles.LINE_EDIT)
        gitlab_row.addWidget(self.gitlab_token_input)

        token_layout.addLayout(gitlab_row)

        # GitHub Token
        github_row = QHBoxLayout()
        github_row.setSpacing(12)

        github_label = QLabel("GitHub Token:")
        github_label.setFixedWidth(100)
        github_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        github_row.addWidget(github_label)

        self.github_token_input = QLineEdit()
        self.github_token_input.setEchoMode(QLineEdit.Password)
        self.github_token_input.setPlaceholderText("输入 GitHub 访问令牌")
        self.github_token_input.setStyleSheet(Styles.LINE_EDIT)
        github_row.addWidget(self.github_token_input)

        token_layout.addLayout(github_row)

        self.content_layout.addWidget(token_section)

        # 描述
        desc_label = QLabel("为每个项目配置 MR 信息")
        desc_label.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 12px; background: transparent; border: none; margin-top: 8px;"
        )
        self.content_layout.addWidget(desc_label)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.2);
                min-height: 20px;
                border-radius: 4px;
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

        # 卡片容器
        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent; border: none;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 12, 0)
        self.cards_layout.setSpacing(12)

        self.scroll_area.setWidget(self.cards_container)
        self.content_layout.addWidget(self.scroll_area, 1)

        # 修改按钮文本
        self.confirm_btn.setText("提交 MR")
        self.confirm_btn.clicked.disconnect()
        self.confirm_btn.clicked.connect(self.submit_mrs)

    def _apply_content_styles(self):
        """应用样式"""
        self.setStyleSheet(f"""
            QComboBox QAbstractItemView {{
                background-color: #1a1a2e;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 10px;
                min-height: 24px;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: rgba(102, 126, 234, 0.4);
                color: {Colors.TEXT_PRIMARY};
            }}
        """)

    def _create_pod_card(self, pod_name, info):
        """创建单个 Pod/项目 卡片"""
        card = QFrame()
        card.setObjectName("mrCard")
        card.setStyleSheet(f"""
            QFrame#mrCard {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(10)

        # Header: 项目名称 + 当前分支标签
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        name_label = QLabel(pod_name)
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        header_layout.addWidget(name_label)

        # 是否为主工程标记
        if info.get("is_main_project", False):
            main_badge = QLabel("主工程")
            main_badge.setStyleSheet(f"""
                QLabel {{
                    color: #fbbf24;
                    font-size: 11px;
                    background-color: rgba(251, 191, 36, 0.15);
                    border: 1px solid rgba(251, 191, 36, 0.25);
                    border-radius: 4px;
                    padding: 2px 8px;
                }}
            """)
            header_layout.addWidget(main_badge)

        # 当前分支标签
        current_branch = info.get("current_branch", "")
        if current_branch and current_branch != "未知":
            branch_badge = QLabel(current_branch)
            branch_badge.setStyleSheet(f"""
                QLabel {{
                    color: #a5b4fc;
                    font-size: 11px;
                    background-color: rgba(99, 102, 241, 0.15);
                    border: 1px solid rgba(99, 102, 241, 0.25);
                    border-radius: 4px;
                    padding: 2px 8px;
                }}
            """)
            header_layout.addWidget(branch_badge)

        header_layout.addStretch()
        card_layout.addLayout(header_layout)

        # Git URL
        if "error" not in info:
            git_url = info.get("git_url", "")
            url_label = QLabel(git_url)
            url_label.setStyleSheet(f"""
                QLabel {{
                    color: {Colors.TEXT_MUTED};
                    font-size: 10px;
                    background: transparent;
                    border: none;
                }}
            """)
            card_layout.addWidget(url_label)

        # 错误信息
        if "error" in info:
            error_label = QLabel(f"❌ {info['error']}")
            error_label.setStyleSheet(f"""
                QLabel {{
                    color: #f87171;
                    font-size: 12px;
                    background: transparent;
                    border: none;
                }}
            """)
            card_layout.addWidget(error_label)
            return card

        # 源分支选择
        source_row = QHBoxLayout()
        source_row.setSpacing(12)

        source_label = QLabel("源分支:")
        source_label.setFixedWidth(65)
        source_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        source_row.addWidget(source_label)

        remote_branches = info.get("remote_branches", [])
        podfile_branch = info.get("podfile_branch", "")
        is_main_project = info.get("is_main_project", False)

        source_combo = CustomDropdown()
        source_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 确定默认源分支
        if is_main_project:
            default_source = current_branch
        else:
            default_source = podfile_branch if podfile_branch else current_branch

        # 添加分支选项，默认源分支放在第一位
        source_branches = []
        if default_source:
            source_branches.append(default_source)

        # 添加当前分支（如果不同于默认）
        if current_branch and current_branch != default_source:
            source_branches.append(current_branch)

        # 添加其他远程分支
        for branch in remote_branches:
            if branch != default_source and branch != current_branch:
                source_branches.append(branch)

        if source_branches:
            source_combo.addItems(source_branches)
            # 默认选择第一个（即默认源分支）
            source_combo.setCurrentText(source_branches[0])
        else:
            source_combo.addItem(current_branch or "未知")
            source_combo.setEnabled(False)

        source_combo.currentTextChanged.connect(
            lambda text, name=pod_name: self.on_source_branch_changed(name, text)
        )
        source_row.addWidget(source_combo)
        card_layout.addLayout(source_row)

        # 目标分支选择
        target_row = QHBoxLayout()
        target_row.setSpacing(12)

        target_label = QLabel("目标分支:")
        target_label.setFixedWidth(65)
        target_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        target_row.addWidget(target_label)

        target_combo = CustomDropdown()
        target_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 添加常用目标分支（去掉 origin/ 前缀）
        common_targets = ["master", "main", "develop", "release"]
        target_branches = []

        for target in common_targets:
            if target in remote_branches:
                target_branches.append(target)
            elif f"origin/{target}" in remote_branches:
                target_branches.append(target)

        # 添加其他远程分支（去掉 origin/ 前缀）
        for branch in remote_branches:
            branch_name = (
                branch.replace("origin/", "")
                if branch.startswith("origin/")
                else branch
            )
            if branch_name not in target_branches:
                target_branches.append(branch_name)

        if target_branches:
            target_combo.addItems(target_branches)
            # 默认选择 master 或 main
            if "master" in target_branches:
                target_combo.setCurrentText("master")
            elif "main" in target_branches:
                target_combo.setCurrentText("main")
            elif "develop" in target_branches:
                target_combo.setCurrentText("develop")
            else:
                target_combo.setCurrentText(target_branches[0])
        else:
            target_combo.addItem("master")

        target_combo.currentTextChanged.connect(
            lambda text, name=pod_name: self.on_target_branch_changed(name, text)
        )
        target_row.addWidget(target_combo)
        card_layout.addLayout(target_row)

        # MR 标题
        title_row = QHBoxLayout()
        title_row.setSpacing(12)

        title_label = QLabel("MR 标题:")
        title_label.setFixedWidth(65)
        title_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        title_row.addWidget(title_label)

        # 生成默认标题（使用默认源分支）
        default_source_for_title = podfile_branch if podfile_branch else current_branch
        default_title = f"Merge {default_source_for_title} into master"

        title_input = QLineEdit()
        title_input.setText(default_title)
        title_input.setStyleSheet(Styles.LINE_EDIT)
        title_input.textChanged.connect(
            lambda text, name=pod_name: self.on_title_changed(name, text)
        )
        title_row.addWidget(title_input)
        card_layout.addLayout(title_row)

        # MR 描述
        desc_row = QHBoxLayout()
        desc_row.setSpacing(12)

        desc_label = QLabel("MR 描述:")
        desc_label.setFixedWidth(65)
        desc_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        desc_row.addWidget(desc_label)

        desc_input = QLineEdit()
        desc_input.setPlaceholderText("简要描述此次合并...")
        desc_input.setStyleSheet(Styles.LINE_EDIT)
        desc_input.textChanged.connect(
            lambda text, name=pod_name: self.on_description_changed(name, text)
        )
        desc_row.addWidget(desc_input)
        card_layout.addLayout(desc_row)

        # 保存卡片组件引用
        self.pod_cards.append(
            {
                "card": card,
                "pod_name": pod_name,
                "source_combo": source_combo,
                "target_combo": target_combo,
                "title_input": title_input,
                "desc_input": desc_input,
            }
        )

        # 初始化配置
        self.mr_configs[pod_name] = {
            "source_branch": source_combo.currentText(),
            "target_branch": target_combo.currentText(),
            "title": default_title,
            "description": "",
        }

        return card

    def load_tokens_from_config(self):
        """从配置加载Token"""
        config_path = os.path.expanduser("~/.podpilot_config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    full_config = json.load(f)
                    if "gitlab_token" in full_config:
                        self.config["gitlab_token"] = full_config["gitlab_token"]
                    if "github_token" in full_config:
                        self.config["github_token"] = full_config["github_token"]
        except Exception:
            pass

        gitlab_token = self.config.get("gitlab_token", "")
        github_token = self.config.get("github_token", "")

        if gitlab_token:
            self.gitlab_token_input.setText(gitlab_token)
        if github_token:
            self.github_token_input.setText(github_token)

    def load_pods_info(self):
        """加载Pod信息，创建卡片"""
        # 排序：主工程优先，其他按名称排序
        sorted_items = sorted(
            self.pods_info.items(),
            key=lambda x: (0 if x[1].get("is_main_project", False) else 1, x[0]),
        )

        for pod_name, info in sorted_items:
            card = self._create_pod_card(pod_name, info)
            self.cards_layout.addWidget(card)

        # 添加弹性空间
        self.cards_layout.addStretch()

    def on_source_branch_changed(self, pod_name, branch):
        """源分支改变"""
        if pod_name not in self.mr_configs:
            self.mr_configs[pod_name] = {}
        self.mr_configs[pod_name]["source_branch"] = branch

    def on_target_branch_changed(self, pod_name, branch):
        """目标分支改变"""
        if pod_name not in self.mr_configs:
            self.mr_configs[pod_name] = {}
        self.mr_configs[pod_name]["target_branch"] = branch

    def on_title_changed(self, pod_name, title):
        """标题改变"""
        if pod_name not in self.mr_configs:
            self.mr_configs[pod_name] = {}
        self.mr_configs[pod_name]["title"] = title

    def on_description_changed(self, pod_name, desc):
        """描述改变"""
        if pod_name not in self.mr_configs:
            self.mr_configs[pod_name] = {}
        self.mr_configs[pod_name]["description"] = desc

    def submit_mrs(self):
        """提交MR"""
        gitlab_token = self.gitlab_token_input.text().strip()
        github_token = self.github_token_input.text().strip()

        if not gitlab_token and not github_token:
            ModernDialog.warning(self, "警告", "请输入至少一个访问令牌")
            return

        # 收集所有Pod和主工程的MR信息
        mr_info = {}
        for pod_name, info in self.pods_info.items():
            if "error" in info:
                continue

            config = self.mr_configs.get(pod_name, {})
            source_branch = config.get("source_branch", "")
            target_branch = config.get("target_branch", "")
            title = config.get("title", "")
            description = config.get("description", "")

            if not source_branch or not target_branch:
                ModernDialog.warning(
                    self, "警告", f"{pod_name} 的源分支或目标分支不能为空"
                )
                return

            mr_info[pod_name] = {
                "git_url": info.get("git_url", ""),
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": description,
                "gitlab_token": gitlab_token,
                "github_token": github_token,
                "is_main_project": info.get("is_main_project", False),
            }

        # 确认提交
        reply = ModernDialog.question(
            self,
            "确认提交",
            f"将为 {len(mr_info)} 个项目创建MR，是否继续？",
            ModernDialog.Yes | ModernDialog.No,
        )
        if reply != ModernDialog.Yes:
            return

        # 显示loading对话框
        loading_dialog = QWidget(self)
        loading_dialog.setFixedSize(200, 100)
        loading_dialog.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.BG_GRADIENT_START},
                    stop:0.5 {Colors.BG_GRADIENT_MID},
                    stop:1 {Colors.BG_GRADIENT_END}
                );
                border-radius: 12px;
            }}
        """)

        loading_layout = QVBoxLayout()
        loading_layout.setContentsMargins(20, 20, 20, 20)

        self.loading_widget = LoadingWidget("提交中...")
        loading_layout.addWidget(self.loading_widget)

        loading_dialog.setLayout(loading_layout)
        loading_dialog.show()

        self.loading_widget.start_animation()
        QApplication.processEvents()

        # 创建异步提交工作线程
        try:
            self.mr_worker = MRRequestWorker(mr_info)
            self.mr_worker.finished.connect(
                lambda result: self._on_mr_finished(result, loading_dialog)
            )
            self.mr_worker.start()
        except Exception as e:
            if loading_dialog:
                loading_dialog.close()
            ModernDialog.error(self, "错误", f"无法创建MR工作线程: {str(e)}")

    def _on_mr_finished(self, result, loading_dialog):
        """处理MR提交完成"""
        # 清理线程引用
        if hasattr(self, "mr_worker") and self.mr_worker:
            try:
                self.mr_worker.wait()
            except RuntimeError:
                pass
            finally:
                self.mr_worker = None

        if hasattr(self, "loading_widget"):
            self.loading_widget.stop_animation()

        loading_dialog.close()

        success_count = result.get("success_count", 0)
        fail_count = result.get("fail_count", 0)
        results = result.get("results", {})

        # 显示结果
        msg = f"MR创建完成！\n\n成功: {success_count}\n失败: {fail_count}\n\n"

        if results:
            for pod_name, info in results.items():
                if "error" in info:
                    msg += f"❌ {pod_name}: {info['error']}\n"
                else:
                    platform = info.get("platform", "")
                    action = info.get("action", "created")
                    action_text = "已更新" if action == "updated" else "已创建"
                    if platform == "GitLab":
                        mr_url = info.get("mr_url", "")
                        msg += f"✅ {pod_name} ({action_text}): {mr_url}\n"
                    elif platform == "GitHub":
                        pr_url = info.get("pr_url", "")
                        msg += f"✅ {pod_name} ({action_text}): {pr_url}\n"

        if fail_count == 0:
            ModernDialog.information(self, "成功", msg)
            self.accept()
        else:
            ModernDialog.warning(self, "部分成功", msg)

        # 记录日志
        if self.parent_manager:
            self.parent_manager.log_message(
                f"批量创建MR完成: 成功 {success_count}, 失败 {fail_count}"
            )

    def closeEvent(self, event):
        """处理对话框关闭事件，确保线程安全退出"""
        if hasattr(self, "mr_worker") and self.mr_worker:
            try:
                if self.mr_worker.isRunning():
                    reply = ModernDialog.question(
                        self,
                        "确认",
                        "MR提交正在进行中，确定要取消吗？",
                        ModernDialog.Yes | ModernDialog.No,
                        ModernDialog.No,
                    )
                    if reply == ModernDialog.No:
                        event.ignore()
                        return
                    self.mr_worker.quit()
                    self.mr_worker.wait(2000)
            except RuntimeError:
                pass
        super().closeEvent(event)
