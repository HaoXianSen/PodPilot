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
                result["__main_project__"] = {
                    "name": os.path.basename(self.project_dir),
                    "current_branch": self.main_project_current_branch,
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
                            if branch_line and "->" in branch_line:
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
    """异步发送MR请求"""

    finished = pyqtSignal(dict)

    def __init__(self, mr_info):
        super().__init__()
        self.mr_info = mr_info

    def run(self):
        success_count = 0
        fail_count = 0
        results = {}

        for pod_name, info in self.mr_info.items():
            git_url = info["git_url"]
            source_branch = info["source_branch"]
            target_branch = info["target_branch"]
            title = info["title"]
            description = info["description"]
            gitlab_token = info.get("gitlab_token", "")
            github_token = info.get("github_token", "")

            try:
                # 判断是GitLab还是GitHub
                if "gitlab" in git_url.lower():
                    if not gitlab_token:
                        results[pod_name] = {"error": "需要GitLab访问令牌"}
                    else:
                        results[pod_name] = self._create_gitlab_mr(
                            git_url,
                            source_branch,
                            target_branch,
                            title,
                            description,
                            gitlab_token,
                        )
                elif "github" in git_url.lower():
                    if not github_token:
                        results[pod_name] = {"error": "需要GitHub访问令牌"}
                    else:
                        results[pod_name] = self._create_github_pr(
                            git_url,
                            source_branch,
                            target_branch,
                            title,
                            description,
                            github_token,
                        )
                else:
                    results[pod_name] = {"error": "不支持的Git平台"}

                if "error" in results[pod_name]:
                    fail_count += 1
                else:
                    success_count += 1
            except urllib.error.URLError as e:
                fail_count += 1
                results[pod_name] = {"error": f"网络错误: {str(e)}"}
            except Exception as e:
                fail_count += 1
                results[pod_name] = {"error": f"创建失败: {str(e)}"}

        self.finished.emit(
            {
                "success_count": success_count,
                "fail_count": fail_count,
                "results": results,
            }
        )

    def _create_gitlab_mr(
        self, git_url, source_branch, target_branch, title, description, token
    ):
        """创建GitLab Merge Request"""
        try:
            # 解析项目路径
            if ":" in git_url:
                path_part = git_url.split(":")[1]
            else:
                from urllib.parse import urlparse

                parsed = urlparse(git_url)
                path_part = parsed.path.replace(".git", "")

            path_part = urllib.parse.quote(path_part, safe="")

            # 解析GitLab URL
            if git_url.startswith("git@"):
                parts = git_url.replace("git@", "").split(":")
                host = parts[0]
                base_url = f"https://{host}/api/v4"
            else:
                from urllib.parse import urlparse

                parsed = urlparse(git_url)
                host = parsed.netloc
                base_url = f"https://{host}/api/v4"

            # 构建API URL
            api_url = f"{base_url}/projects/{path_part}/merge_requests"

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
        self.pods_info = pods_info
        self.parent_manager = parent
        self.config = config or {}
        self.main_project_info = main_project_info
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

        # 显示主工程信息（如果提供）
        if self.main_project_info:
            main_info_group = QGroupBox("主工程信息")
            main_info_layout = QVBoxLayout()

            main_info_text = (
                f"<b>工程名称:</b> {self.main_project_info.get('name', '未知')}<br>"
            )
            main_info_text += f"<b>当前分支:</b> {self.main_project_info.get('current_branch', '未知')}<br>"
            git_url = self.main_project_info.get("git_url", "")
            if git_url:
                main_info_text += f"<b> Git URL:</b> {git_url}<br>"

            main_info_label = QLabel()
            main_info_label.setTextFormat(Qt.RichText)
            main_info_label.setText(main_info_text)
            main_info_label.setWordWrap(True)
            main_info_label.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #e8f0fe;
                    border-radius: 6px;
                    border: 1px solid #d1e5f8;
                }
            """)
            main_info_layout.addWidget(main_info_label)
            main_info_group.setLayout(main_info_layout)
            layout.addWidget(main_info_group)
            layout.addWidget(main_info_group)

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

        row = 0
        for pod_name, info in self.pods_info.items():
            self.table.insertRow(row)

            # Pod名称（不可编辑）
            name_item = QTableWidgetItem(pod_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)

            # 源分支（可选择，默认为Podfile中指定的分支）
            podfile_branch = info.get("podfile_branch", "")
            remote_branches = info.get("remote_branches", [])
            source_branch_combo = QComboBox()
            source_branch_combo.addItems(remote_branches)

            print(f"DEBUG: Setting source branch for {pod_name}")
            print(f"  podfile_branch = '{podfile_branch}'")
            print(f"  remote_branches = {remote_branches}")
            print(
                f"  podfile_branch in remote_branches? {podfile_branch in remote_branches}"
            )

            # 先尝试精确匹配
            if podfile_branch and podfile_branch in remote_branches:
                source_branch_combo.setCurrentText(podfile_branch)
                source_branch = podfile_branch
                print(f"  -> Exact match, selected: {podfile_branch}")
            # 如果精确匹配失败，尝试忽略大小写匹配
            elif podfile_branch:
                print(f"  -> No exact match, trying case-insensitive...")
                matched = False
                for rb in remote_branches:
                    print(
                        f"     Comparing '{rb}' with '{podfile_branch}': {rb.lower() == podfile_branch.lower()}"
                    )
                    if rb.lower() == podfile_branch.lower():
                        source_branch_combo.setCurrentText(rb)
                        source_branch = rb
                        matched = True
                        print(f"  -> Case-insensitive match, selected: {rb}")
                        break
                # 如果还是没匹配到，使用第一个
                if not matched:
                    print(f"  -> No match found, using first branch")
                    if remote_branches:
                        source_branch_combo.setCurrentIndex(0)
                        source_branch = remote_branches[0]
                    else:
                        source_branch = "未指定"
            elif remote_branches:
                source_branch_combo.setCurrentIndex(0)
                source_branch = remote_branches[0]
                print(f"  -> No podfile_branch, using first: {source_branch}")
            else:
                source_branch = "未指定"
                print(f"  -> No branches available")
            self.table.setCellWidget(row, 1, source_branch_combo)

            # 目标分支（可选择，仅远程分支，默认为master）
            remote_branches = info.get("remote_branches", [])
            target_branch_combo = QComboBox()
            target_branch_combo.addItems(remote_branches)
            if "master" in remote_branches:
                target_branch_combo.setCurrentText("master")
            elif remote_branches:
                target_branch_combo.setCurrentIndex(0)
            self.table.setCellWidget(row, 2, target_branch_combo)

            # MR标题（可编辑）
            title_text = (
                f"[{pod_name}] {podfile_branch if podfile_branch else '未指定'}"
            )
            title_item = QTableWidgetItem(title_text)
            self.table.setItem(row, 3, title_item)

            # MR描述（可编辑）
            desc_text = f"Merge branch {podfile_branch if podfile_branch else '未指定'} into master"
            desc_item = QTableWidgetItem(desc_text)
            self.table.setItem(row, 4, desc_item)

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

        # 收集所有Pod的MR信息
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
                QMessageBox.warning(self, "警告", f"Pod {pod_name} 的目标分支不能为空")
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
            }

        # 如果有主工程信息，添加主工程MR
        if self.main_project_info:
            mr_info["__main_project__"] = {
                "git_url": self.main_project_info.get("git_url", ""),
                "source_branch": self.main_project_info.get("current_branch", ""),
                "target_branch": self.main_project_info.get("current_branch", ""),
                "title": f"MR from {self.main_project_info.get('current_branch', '未知')}",
                "description": "主工程MR",
                "gitlab_token": gitlab_token,
                "github_token": github_token,
            }

        # 确认提交
        total_count = len(mr_info)
        pod_count = total_count - 1 if "__main_project__" in mr_info else total_count
        reply = QMessageBox.question(
            self,
            "确认提交",
            f"将为 {pod_count} 个Pod创建MR"
            + (f"，主工程1个MR" if "__main_project__" in mr_info else ""),
            "是否继续？",
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
        self.mr_worker = MRRequestWorker(mr_info)
        self.mr_worker.finished.connect(
            lambda result: self._on_mr_finished(result, loading_dialog)
        )

        self.mr_worker.start()

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
