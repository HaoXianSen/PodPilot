import re
import json
import subprocess
import os
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QGridLayout,
    QDialog,
    QVBoxLayout,
    QGroupBox,
    QTextEdit,
    QMessageBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QWidget,
    QApplication,
    QCheckBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import urllib.request
import urllib.error
import urllib.parse


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
    except Exception as e:
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
        print(f"DEBUG: Looking for Podfile at {podfile_path}")
        if not os.path.exists(podfile_path):
            print(f"DEBUG: Podfile not found!")
            return None

        try:
            with open(podfile_path, "r") as f:
                content = f.read()

            print(f"DEBUG: Podfile content length: {len(content)}")

            pod_pattern = r"pod\s+['\"]([^'\"]+)['\"]"
            branch_pattern = r":branch\s*=>\s*['\"]?([^'\"\s,]+)['\"]?"
            variable_pattern = r"^(\w+)\s*=\s*['\"]([^'\"]+)['\"]\s*$"

            for m in re.finditer(pod_pattern, content):
                start_pos = m.start()
                found_pod_name = m.group(1)

                print(f"DEBUG: Found pod declaration: {found_pod_name}")

                if found_pod_name != pod_name:
                    continue

                print(f"DEBUG: Matching pod found: {pod_name}")

                pod_declaration_pattern = (
                    r"pod\s+['\"]"
                    + re.escape(pod_name)
                    + r"['\"].*?(?:\n\s*end|\n\s*$|\n\s*(?=pod\s+))"
                )
                pod_declaration_match = re.search(
                    pod_declaration_pattern, content[start_pos:], re.DOTALL
                )

                if pod_declaration_match:
                    pod_declaration = pod_declaration_match.group(0)
                    print(f"DEBUG: Pod declaration: {pod_declaration}")
                    branch_match = re.search(branch_pattern, pod_declaration)
                    if branch_match:
                        branch_name = branch_match.group(1)
                        print(f"DEBUG: Found branch pattern: {branch_name}")

                        if not branch_name.startswith(
                            "'"
                        ) and not branch_name.startswith('"'):
                            print(f"DEBUG: Branch is a variable, searching...")
                            for line in content.split("\n"):
                                var_match = re.match(variable_pattern, line.strip())
                                if var_match and var_match.group(1) == branch_name:
                                    print(
                                        f"DEBUG: Found variable: {var_match.group(1)} = {var_match.group(2)}"
                                    )
                                    return var_match.group(2)
                            print(
                                f"DEBUG: Variable not found, returning raw: {branch_name}"
                            )
                            return branch_name
                        else:
                            print(f"DEBUG: Branch is a string: {branch_name}")
                            return branch_name.strip("'\"")

                return None

            print(f"DEBUG: Pod {pod_name} not found in Podfile")
            return None
        except Exception as e:
            print(f"DEBUG: Exception in _get_pod_branches_from_podfile: {e}")
            return None

    def run(self):
        try:
            result = {}

            # 添加主工程信息（如果提供）
            if self.main_project_current_branch:
                # 获取主工程的远程分支列表
                main_remote_branches = []
                try:
                    fetch_result = subprocess.run(
                        ["git", "fetch", "--prune"],
                        capture_output=True,
                        text=True,
                        cwd=self.project_dir,
                        timeout=30,
                        check=False,
                    )

                    branches_result = subprocess.run(
                        ["git", "branch", "-r"],
                        capture_output=True,
                        text=True,
                        cwd=self.project_dir,
                        timeout=10,
                        check=False,
                    )
                    if branches_result.returncode == 0:
                        branch_lines = branches_result.stdout.strip().split("\n")
                        for b in branch_lines:
                            branch_line = b.strip()
                            # 跳过空行和 HEAD 指向行
                            if not branch_line or "->" in branch_line:
                                continue
                            # 移除 origin/ 前缀
                            branch_name = branch_line.replace("origin/", "")
                            main_remote_branches.append(branch_name)
                        main_remote_branches = list(set(main_remote_branches))
                        main_remote_branches.sort()
                except Exception as e:
                    print(f"DEBUG: Error getting main project remote branches: {e}")

                result[self.main_project_current_branch] = {
                    "name": os.path.basename(self.project_dir),
                    "current_branch": self.main_project_current_branch,
                    "remote_branches": main_remote_branches,
                    "git_url": self.main_project_git_url,
                    "is_main_project": True,
                }

            for pod_name in self.pod_names:
                try:
                    local_path = self.pod_config.get(pod_name, "")
                    if not local_path or not os.path.exists(local_path):
                        result[pod_name] = {"error": "本地路径不存在或未配置"}
                        continue

                    branch_result = subprocess.run(
                        ["git", "branch", "--show-current"],
                        capture_output=True,
                        text=True,
                        cwd=local_path,
                        timeout=10,
                        check=False,
                    )
                    if branch_result.returncode != 0:
                        result[pod_name] = {
                            "error": f"获取分支失败: {branch_result.stderr.strip()}"
                        }
                        continue

                    current_branch = branch_result.stdout.strip()
                    if not current_branch:
                        result[pod_name] = {"error": "当前分支为空"}
                        continue

                    fetch_result = subprocess.run(
                        ["git", "fetch", "--prune"],
                        capture_output=True,
                        text=True,
                        cwd=local_path,
                        timeout=30,
                        check=False,
                    )

                    branches_result = subprocess.run(
                        ["git", "branch", "-r"],
                        capture_output=True,
                        text=True,
                        cwd=local_path,
                        timeout=10,
                        check=False,
                    )
                    remote_branches = []
                    if branches_result.returncode == 0:
                        branch_lines = branches_result.stdout.strip().split("\n")
                        for b in branch_lines:
                            branch_line = b.strip()
                            # 跳过空行和 HEAD 指向行
                            if not branch_line or "->" in branch_line:
                                continue
                            # 移除 origin/ 前缀
                            branch_name = branch_line.replace("origin/", "")
                            remote_branches.append(branch_name)
                        remote_branches = list(set(remote_branches))
                        remote_branches.sort()

                    git_url = get_git_url_from_local_path(local_path)
                    if not git_url:
                        result[pod_name] = {"error": "无法获取Git远程URL"}
                        continue

                    podfile_branch = self._get_pod_branches_from_podfile(pod_name)

                    result[pod_name] = {
                        "current_branch": current_branch,
                        "remote_branches": remote_branches,
                        "git_url": git_url,
                        "local_path": local_path,
                        "podfile_branch": podfile_branch,
                    }

                except subprocess.TimeoutExpired:
                    result[pod_name] = {"error": "操作超时"}
                except Exception as e:
                    result[pod_name] = {"error": f"未知错误: {str(e)}"}

            self.finished.emit(result)
        except Exception as e:
            self.error_occurred.emit(f"MRInfoCollector严重错误: {str(e)}")


class MRRequestWorker(QThread):
    """异步发送MR请求 - 先创建私有库MR，再创建主工程MR并关联链接"""

    finished = pyqtSignal(dict)

    def __init__(self, mr_info):
        super().__init__()
        self.mr_info = mr_info

    def run(self):
        success_count = 0
        fail_count = 0
        results = {}

        # 分离主工程和私有库
        main_project_info = None
        main_project_name = None
        pod_infos = {}

        for pod_name, info in self.mr_info.items():
            if info.get("is_main_project"):
                main_project_info = info
                main_project_name = pod_name
            else:
                pod_infos[pod_name] = info

        # 第一阶段：先创建所有私有库的 MR
        pod_mr_links = []  # 收集成功创建的 MR 链接

        for pod_name, info in pod_infos.items():
            result = self._create_single_mr(pod_name, info)
            results[pod_name] = result

            if "error" in result:
                fail_count += 1
            else:
                success_count += 1
                # 收集成功的 MR 链接
                mr_url = result.get("mr_url") or result.get("pr_url", "")
                if mr_url:
                    pod_mr_links.append({"name": pod_name, "url": mr_url})

        # 第二阶段：创建主工程 MR（如果有的话）
        if main_project_info and main_project_name:
            # 在主工程描述中追加私有库 MR 链接
            if pod_mr_links:
                original_desc = main_project_info.get("description", "")
                enhanced_desc = self._build_enhanced_description(
                    original_desc, pod_mr_links
                )
                main_project_info["description"] = enhanced_desc

            result = self._create_single_mr(main_project_name, main_project_info)
            results[main_project_name] = result

            if "error" in result:
                fail_count += 1
            else:
                success_count += 1

        self.finished.emit(
            {
                "success_count": success_count,
                "fail_count": fail_count,
                "results": results,
            }
        )

    def _build_enhanced_description(self, original_desc, pod_mr_links):
        """构建包含私有库 MR 链接的增强描述"""
        enhanced_desc = original_desc or ""

        if pod_mr_links:
            enhanced_desc += "\n\n---\n\n"
            enhanced_desc += "## 关联的私有库 MR\n\n"
            enhanced_desc += "| Pod 名称 | MR 链接 |\n"
            enhanced_desc += "|----------|--------|\n"

            for link_info in pod_mr_links:
                pod_name = link_info["name"]
                mr_url = link_info["url"]
                enhanced_desc += f"| {pod_name} | {mr_url} |\n"

        return enhanced_desc

    def _create_single_mr(self, pod_name, info):
        """创建单个 MR"""
        git_url = info.get("git_url", "")
        source_branch = info.get("source_branch", "")
        target_branch = info.get("target_branch", "")
        title = info.get("title", "")
        description = info.get("description", "")
        gitlab_token = info.get("gitlab_token", "")
        github_token = info.get("github_token", "")

        print(f"[DEBUG] Processing {pod_name}")
        print(f"[DEBUG]   git_url: '{git_url}'")
        print(f"[DEBUG]   source_branch: {source_branch}")
        print(f"[DEBUG]   target_branch: {target_branch}")

        # 检查 git_url 是否为空
        if not git_url or not git_url.strip():
            return {"error": "Git URL 为空，无法创建 MR"}

        try:
            # 判断是GitLab还是GitHub
            if "gitlab" in git_url.lower():
                if not gitlab_token:
                    return {"error": "需要GitLab访问令牌"}
                else:
                    return self._create_gitlab_mr(
                        git_url,
                        source_branch,
                        target_branch,
                        title,
                        description,
                        gitlab_token,
                    )
            elif "github" in git_url.lower():
                if not github_token:
                    return {"error": "需要GitHub访问令牌"}
                else:
                    return self._create_github_pr(
                        git_url,
                        source_branch,
                        target_branch,
                        title,
                        description,
                        github_token,
                    )
            else:
                return {"error": "不支持的Git平台"}
        except urllib.error.URLError as e:
            return {"error": f"网络错误: {str(e)}"}
        except Exception as e:
            return {"error": f"创建失败: {str(e)}"}

    def _create_gitlab_mr(
        self, git_url, source_branch, target_branch, title, description, token
    ):
        """创建GitLab Merge Request"""
        try:
            # 解析项目路径和主机
            if git_url.startswith("git@"):
                # 格式: git@gitlab.example.com:group/project.git
                parts = git_url.replace("git@", "").split(":")
                host = parts[0]
                path_part = parts[1] if len(parts) > 1 else ""
                # 移除 .git 后缀
                path_part = path_part.replace(".git", "")
            else:
                # 格式: https://gitlab.example.com/group/project.git
                # 或: https://username@gitlab.example.com/group/project.git
                from urllib.parse import urlparse

                parsed = urlparse(git_url)
                host = (
                    parsed.hostname
                )  # 使用 hostname 而不是 netloc，这样会自动移除用户名
                path_part = parsed.path
                # 移除开头的 / 和 .git 后缀
                path_part = path_part.lstrip("/").replace(".git", "")

            base_url = f"https://{host}/api/v4"

            # URL 编码项目路径（GitLab API 需要）
            encoded_path = urllib.parse.quote(path_part, safe="")

            # 构建API URL
            api_url = f"{base_url}/projects/{encoded_path}/merge_requests"

            print(f"[DEBUG] GitLab MR API URL: {api_url}")
            print(f"[DEBUG] Source: {source_branch}, Target: {target_branch}")

            # 构建请求数据
            data = {
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": description,
                "remove_source_branch": False,
            }

            # 发送请求
            req = urllib.request.Request(
                api_url,
                data=json.dumps(data).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "PRIVATE-TOKEN": token,
                },
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                return {
                    "platform": "GitLab",
                    "mr_url": result.get("web_url", ""),
                    "mr_iid": result.get("iid", 0),
                    "success": True,
                }
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except:
                pass
            return {"error": f"HTTP错误 {e.code}: {e.reason}. {error_body}"}
        except urllib.error.URLError as e:
            return {"error": f"网络错误: {str(e)}"}
        except Exception as e:
            return {"error": f"创建失败: {str(e)}"}

    def _create_github_pr(
        self, git_url, source_branch, target_branch, title, description, token
    ):
        """创建GitHub Pull Request"""
        try:
            # 提取项目信息
            if ":" in git_url:
                path_part = git_url.split(":")[1]
            else:
                from urllib.parse import urlparse

                parsed = urlparse(git_url)
                path_part = parsed.path.replace(".git", "")

            path_part = path_part.replace(".git", "")
            owner, repo = path_part.split("/")

            # 构建API URL
            api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

            # 构建请求数据
            data = {
                "title": title,
                "body": description,
                "head": source_branch,
                "base": target_branch,
            }

            # 发送请求
            req = urllib.request.Request(
                api_url,
                data=json.dumps(data).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"token {token}",
                    "User-Agent": "iPM",
                },
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                return {
                    "platform": "GitHub",
                    "pr_url": result.get("html_url", ""),
                    "pr_number": result.get("number", 0),
                    "success": True,
                }
        except urllib.error.URLError as e:
            return {"error": f"网络错误: {str(e)}"}
        except Exception as e:
            return {"error": f"创建失败: {str(e)}"}


class MergeRequestDialog(QDialog):
    """Merge Request对话框"""

    def __init__(self, pods_info, parent=None, config=None, main_project_info=None):
        super().__init__(parent)

        # 将主工程信息添加到pods_info中，使用实际项目名
        if main_project_info:
            self.pods_info = pods_info.copy()
            project_name = main_project_info.get("name", "未知")
            self.pods_info[project_name] = main_project_info
        else:
            self.pods_info = pods_info

        self.parent_manager = parent
        self.config = config or {}
        self._debug_print_pods_info()
        self.initUI()
        self.load_tokens_from_config()

    def _debug_print_pods_info(self):
        """打印调试信息"""
        for pod_name, info in self.pods_info.items():
            print(f"DEBUG: Pod={pod_name}")
            print(f"  podfile_branch={info.get('podfile_branch', 'None')}")
            print(f"  remote_branches={info.get('remote_branches', [])}")
            if info.get("podfile_branch"):
                print(
                    f"  branch in remote? {info.get('podfile_branch') in info.get('remote_branches', [])}"
                )

    def initUI(self):
        """初始化UI"""
        self.setWindowTitle("批量创建Merge Request")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout()

        # Token输入区域
        token_group = QGroupBox("访问令牌配置")
        token_layout = QHBoxLayout()

        gitlab_label = QLabel("GitLab Token:")
        self.gitlab_token_input = QLineEdit()
        self.gitlab_token_input.setPlaceholderText("输入GitLab Personal Access Token")
        self.gitlab_token_input.setEchoMode(QLineEdit.Password)
        self.gitlab_token_input.setReadOnly(True)

        github_label = QLabel("GitHub Token:")
        self.github_token_input = QLineEdit()
        self.github_token_input.setPlaceholderText("输入GitHub Personal Access Token")
        self.github_token_input.setEchoMode(QLineEdit.Password)
        self.github_token_input.setReadOnly(True)

        token_layout.addWidget(gitlab_label)
        token_layout.addWidget(self.gitlab_token_input, 1)
        token_layout.addWidget(github_label)
        token_layout.addWidget(self.github_token_input, 1)
        token_group.setLayout(token_layout)

        # Pod信息表格
        table_group = QGroupBox("Pod MR信息配置")
        table_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Pod名称", "源分支", "目标分支", "MR标题", "MR描述"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        # 对 pods_info 排序，主工程放第一行
        sorted_pods = []
        for pod_name, info in self.pods_info.items():
            if info.get("is_main_project"):
                sorted_pods.insert(0, (pod_name, info))
            else:
                sorted_pods.append((pod_name, info))

        row = 0
        for pod_name, info in sorted_pods:
            self.table.insertRow(row)

            # Pod名称（不可编辑）
            name_item = QTableWidgetItem(pod_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)

            # 调试信息
            print(f"[DEBUG] ===== {pod_name} =====")
            print(f"[DEBUG] is_main_project: {info.get('is_main_project', False)}")
            print(f"[DEBUG] current_branch: {info.get('current_branch', 'N/A')}")
            print(f"[DEBUG] remote_branches: {info.get('remote_branches', [])}")
            print(f"[DEBUG] podfile_branch: {info.get('podfile_branch', 'N/A')}")

            # 源分支（ComboBox）
            source_branch_combo = QComboBox()
            source_branch_combo.setEditable(True)
            # 只设置下拉列表宽度，不改变选择框本身
            source_branch_combo.view().setMinimumWidth(250)
            current_branch = info.get("current_branch", "")
            remote_branches = info.get("remote_branches", [])
            podfile_branch = info.get("podfile_branch", "")
            is_main_project = info.get("is_main_project", False)

            # 添加当前分支（如果存在）
            if current_branch:
                source_branch_combo.addItem(current_branch)

            # 添加远程分支
            for branch in remote_branches:
                if branch != current_branch:
                    source_branch_combo.addItem(branch)

            # 设置默认源分支：
            # - 主工程：使用当前分支
            # - 依赖库：使用 Podfile 中引用的分支，如果没有则使用 master
            if is_main_project:
                # 主工程使用当前分支
                if current_branch:
                    source_branch_combo.setCurrentText(current_branch)
            else:
                # 依赖库使用 Podfile 中的分支
                if podfile_branch and podfile_branch in remote_branches:
                    # 如果 Podfile 分支在远程分支列表中，优先使用
                    source_branch_combo.setCurrentText(podfile_branch)
                elif podfile_branch:
                    # Podfile 分支不在远程列表中，添加并选中
                    source_branch_combo.insertItem(0, podfile_branch)
                    source_branch_combo.setCurrentText(podfile_branch)
                elif "master" in remote_branches:
                    # 如果没有 Podfile 分支，使用 master
                    source_branch_combo.setCurrentText("master")
                elif current_branch:
                    # 最后回退到当前分支
                    source_branch_combo.setCurrentText(current_branch)

            self.table.setCellWidget(row, 1, source_branch_combo)

            # 目标分支（ComboBox）
            target_branch_combo = QComboBox()
            target_branch_combo.setEditable(True)
            # 只设置下拉列表宽度，不改变选择框本身
            target_branch_combo.view().setMinimumWidth(250)

            # 添加远程分支
            for branch in remote_branches:
                target_branch_combo.addItem(branch)

            # 目标分支优先选择 master/main，其次是 podfile_branch
            if "master" in remote_branches:
                target_branch_combo.setCurrentText("master")
            elif "main" in remote_branches:
                target_branch_combo.setCurrentText("main")
            else:
                podfile_branch = info.get("podfile_branch", "")
                if podfile_branch and podfile_branch in remote_branches:
                    target_branch_combo.setCurrentText(podfile_branch)
                elif remote_branches:
                    target_branch_combo.setCurrentIndex(0)

            self.table.setCellWidget(row, 2, target_branch_combo)

            # MR标题
            default_title = (
                f"Merge {current_branch}" if current_branch else "Merge Request"
            )
            title_item = QTableWidgetItem(default_title)
            self.table.setItem(row, 3, title_item)

            # MR描述 - 默认内容
            target_branch_text = target_branch_combo.currentText() or "master"
            default_description = (
                f"Merge branch '{current_branch}' into '{target_branch_text}'"
                if current_branch
                else "Merge Request"
            )
            description_item = QTableWidgetItem(default_description)
            self.table.setItem(row, 4, description_item)

            row += 1

        table_layout.addWidget(self.table)
        table_group.setLayout(table_layout)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.submit_btn = QPushButton("提交MR")
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #30B350;
            }
            QPushButton:pressed {
                background-color: #28A745;
            }
        """)
        self.submit_btn.clicked.connect(self.submit_mrs)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF3B30;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FF453A;
            }
            QPushButton:pressed {
                background-color: #D63027;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.submit_btn)
        button_layout.addWidget(self.cancel_btn)

        # 添加所有组件到主布局
        layout.addWidget(token_group)
        layout.addWidget(table_group, 1)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_tokens_from_config(self):
        """从配置加载Token"""
        gitlab_token = self.config.get("gitlab_token", "")
        github_token = self.config.get("github_token", "")

        if gitlab_token:
            self.gitlab_token_input.setText(gitlab_token)
        if github_token:
            self.github_token_input.setText(github_token)

    def submit_mrs(self):
        """提交MR"""
        gitlab_token = self.gitlab_token_input.text().strip()
        github_token = self.github_token_input.text().strip()

        if not gitlab_token and not github_token:
            QMessageBox.warning(self, "警告", "请输入至少一个访问令牌")
            return

        # 收集所有Pod和主工程的MR信息
        mr_info = {}
        for row in range(self.table.rowCount()):
            pod_name = self.table.item(row, 0).text()
            source_branch_combo = self.table.cellWidget(row, 1)
            target_branch_combo = self.table.cellWidget(row, 2)
            source_branch = source_branch_combo.currentText()
            target_branch = target_branch_combo.currentText()
            title = self.table.item(row, 3).text()
            description = self.table.item(row, 4).text()

            if not target_branch.strip():
                QMessageBox.warning(self, "警告", f"{pod_name} 的目标分支不能为空")
                return

            info = self.pods_info.get(pod_name, {})
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
        reply = QMessageBox.question(
            self,
            "确认提交",
            f"将为 {len(mr_info)} 个项目创建MR，是否继续？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        # 创建loading对话框
        loading_dialog = QDialog(self)
        loading_dialog.setWindowTitle("提交中")
        loading_dialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint)
        loading_dialog.setFixedSize(200, 100)
        loading_dialog.setStyleSheet(
            """
            QDialog {
                background-color: #f5f5f7;
                border-radius: 12px;
            }
        """
        )

        loading_layout = QVBoxLayout()
        loading_layout.setContentsMargins(20, 20, 20, 20)

        loading_label = QLabel("正在提交MR...")
        loading_label.setAlignment(Qt.AlignCenter)
        loading_layout.addWidget(loading_label)

        loading_dialog.setLayout(loading_layout)
        loading_dialog.show()

        # 创建异步提交工作线程并保存为实例变量以防止被垃圾回收
        try:
            self.mr_worker = MRRequestWorker(mr_info)
            self.mr_worker.finished.connect(
                lambda result: self._on_mr_finished(result, loading_dialog)
            )
            self.mr_worker.start()
        except Exception as e:
            if loading_dialog:
                loading_dialog.close()
            QMessageBox.critical(self, "错误", f"无法创建MR工作线程: {str(e)}")

    def _on_mr_finished(self, result, loading_dialog):
        """处理MR提交完成"""
        # 清理线程引用
        if hasattr(self, "mr_worker"):
            self.mr_worker = None

        if loading_dialog is not None:
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
                    if platform == "GitLab":
                        mr_url = info.get("mr_url", "")
                        msg += f"✅ {pod_name}: {mr_url}\n"
                    elif platform == "GitHub":
                        pr_url = info.get("pr_url", "")
                        msg += f"✅ {pod_name}: {pr_url}\n"

        QMessageBox.information(self, "完成", msg)

        # 记录日志
        if self.parent_manager:
            self.parent_manager.log_message(
                f"批量创建MR完成: 成功 {success_count}, 失败 {fail_count}"
            )

        self.accept()

    def closeEvent(self, event):
        """处理对话框关闭事件，确保线程安全退出"""
        if hasattr(self, "mr_worker") and self.mr_worker:
            try:
                if self.mr_worker.isRunning():
                    reply = QMessageBox.question(
                        self,
                        "确认",
                        "MR提交正在进行中，确定要取消吗？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    if reply == QMessageBox.No:
                        event.ignore()
                        return
                    # 等待线程完成
                    self.mr_worker.quit()
                    self.mr_worker.wait(2000)  # 等待最多2秒
            except RuntimeError:
                pass
        event.accept()

    def reject(self):
        """处理取消/关闭操作，确保线程安全退出"""
        if hasattr(self, "mr_worker") and self.mr_worker:
            try:
                if self.mr_worker.isRunning():
                    reply = QMessageBox.question(
                        self,
                        "确认",
                        "MR提交正在进行中，确定要取消吗？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    if reply == QMessageBox.No:
                        return
                    self.mr_worker.quit()
                    self.mr_worker.wait(2000)
            except RuntimeError:
                pass
        super().reject()
