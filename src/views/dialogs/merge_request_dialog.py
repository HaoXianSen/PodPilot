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

    def _get_pod_git_url_from_podfile(self, pod_name):
        """从Podfile中获取Pod的Git URL"""
        podfile_path = os.path.join(self.project_dir, "Podfile")
        if not os.path.exists(podfile_path):
            print(f"[DEBUG] Podfile not found at {podfile_path}")
            return None

        try:
            with open(podfile_path, "r") as f:
                content = f.read()

            pod_pattern = r"pod\s+['\"]([^'\"]+)['\"]"
            git_pattern = r":git\s*=>\s*['\"]([^'\"]+)['\"]"

            for m in re.finditer(pod_pattern, content):
                start_pos = m.start()
                found_pod_name = m.group(1)

                if found_pod_name != pod_name:
                    continue

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
                    git_match = re.search(git_pattern, pod_declaration)
                    if git_match:
                        git_url = git_match.group(1)
                        print(
                            f"[DEBUG] Found git URL from Podfile for {pod_name}: {git_url}"
                        )
                        return git_url

            print(f"[DEBUG] Git URL for {pod_name} not found in Podfile")
            return None
        except Exception as e:
            print(f"[DEBUG] Exception in _get_pod_git_url_from_podfile: {e}")
            return None

    def _get_recent_commits(self, repo_path, count=3):
        """获取最近的commit信息"""
        try:
            result = subprocess.run(
                ["git", "log", f"-{count}", "--pretty=format:%s"],
                capture_output=True,
                text=True,
                cwd=repo_path,
                timeout=10,
                check=False,
            )
            if result.returncode == 0:
                commits = result.stdout.strip().split("\n")
                # 过滤空行
                commits = [c.strip() for c in commits if c.strip()]
                return commits
            return []
        except Exception as e:
            print(f"DEBUG: Error getting recent commits: {e}")
            return []

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

                # 获取主工程最近3次commit
                main_recent_commits = self._get_recent_commits(self.project_dir)

                result[self.main_project_current_branch] = {
                    "name": os.path.basename(self.project_dir),
                    "current_branch": self.main_project_current_branch,
                    "remote_branches": main_remote_branches,
                    "git_url": self.main_project_git_url,
                    "is_main_project": True,
                    "recent_commits": main_recent_commits,
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

                    # 优先从 Podfile 获取 Git URL，这样更准确
                    git_url = self._get_pod_git_url_from_podfile(pod_name)
                    print(f"[DEBUG] Git URL from Podfile for {pod_name}: {git_url}")

                    # 如果 Podfile 中没有，则从本地仓库获取
                    if not git_url:
                        git_url = get_git_url_from_local_path(local_path)
                        print(
                            f"[DEBUG] Git URL from local repo for {pod_name}: {git_url}"
                        )

                    if not git_url:
                        result[pod_name] = {"error": "无法获取Git远程URL"}
                        continue

                    podfile_branch = self._get_pod_branches_from_podfile(pod_name)

                    # 获取最近3次commit
                    recent_commits = self._get_recent_commits(local_path)

                    result[pod_name] = {
                        "current_branch": current_branch,
                        "remote_branches": remote_branches,
                        "git_url": git_url,
                        "local_path": local_path,
                        "podfile_branch": podfile_branch,
                        "recent_commits": recent_commits,
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

        # 第二阶段：创建或更新主工程 MR（如果有的话）
        if main_project_info and main_project_name:
            source_branch = main_project_info.get("source_branch", "")
            target_branch = main_project_info.get("target_branch", "")

            # 检查主工程是否已有对应的 MR
            existing_mr = None
            if source_branch and target_branch:
                existing_mr = self._get_existing_gitlab_mr(
                    main_project_info, source_branch, target_branch
                )

            if existing_mr:
                # 已存在 MR，更新描述
                print(
                    f"[DEBUG] 主工程已存在 MR，将更新描述: {existing_mr.get('web_url')}"
                )

                if pod_mr_links:
                    # 解析现有描述中的关联
                    existing_description = existing_mr.get("description", "")
                    existing_links = self._parse_existing_mr_links(existing_description)

                    # 构建新的描述（合并已有和新创建的）
                    enhanced_desc = self._build_enhanced_description(
                        existing_description, pod_mr_links, existing_links
                    )

                    # 更新 MR 描述
                    mr_iid = existing_mr.get("iid")
                    update_result = self._update_gitlab_mr_description(
                        main_project_info, mr_iid, enhanced_desc
                    )

                    if "error" in update_result:
                        results[main_project_name] = update_result
                        fail_count += 1
                    else:
                        results[main_project_name] = {
                            "platform": "GitLab",
                            "mr_url": update_result.get(
                                "mr_url", existing_mr.get("web_url")
                            ),
                            "mr_iid": mr_iid,
                            "action": "updated",
                            "success": True,
                        }
                        success_count += 1
                else:
                    # 没有新的私有库 MR 关联需要添加
                    results[main_project_name] = {
                        "platform": "GitLab",
                        "mr_url": existing_mr.get("web_url"),
                        "mr_iid": existing_mr.get("iid"),
                        "action": "exists",
                        "message": "MR 已存在，无需更新",
                        "success": True,
                    }
                    success_count += 1
            else:
                # 不存在 MR，创建新的
                print(f"[DEBUG] 主工程不存在 MR，将创建新的")

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

    def _parse_existing_mr_links(self, description):
        """解析 MR 描述中已有的私有库关联链接

        Returns:
            list: 已有的关联列表 [{"name": xxx, "url": xxx}, ...]
            同一 Pod 只保留最后一个（去重）
        """
        if not description:
            return []

        import re

        links = []

        # 匹配 Markdown 表格格式: | Pod 名称 | MR 链接 |
        # 表格格式:
        # | Pod 名称 | MR 链接 |
        # |----------|--------|
        # | name1 | url1 |
        # | name2 | url2 |

        # 查找表格内容
        table_pattern = r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|"
        matches = re.finditer(table_pattern, description)

        for match in matches:
            pod_name = match.group(1).strip()
            mr_url = match.group(2).strip()

            # 跳过表头和分隔线
            if pod_name == "Pod 名称" or pod_name == "----------" or not mr_url:
                continue

            # 验证是否是有效的 URL（包含 gitlab 或 github）
            if "http" in mr_url.lower():
                links.append({"name": pod_name, "url": mr_url})

        # 去重：同一 Pod 保留最后一个
        seen = {}
        for link in links:
            seen[link["name"]] = link

        result = list(seen.values())

        print(f"[DEBUG] 解析到已有关联（去重后）: {result}")
        return result

    def _build_enhanced_description(
        self, original_desc, pod_mr_links, existing_links=None
    ):
        """构建包含私有库 MR 链接的增强描述

        处理步骤：
        1. 如果存在多个"关联的私有库 MR"表格，只保留最后一个
        2. 合并本次成功的链接（新的覆盖旧的）
        3. 构建完整新表格并替换所有旧表格

        Args:
            original_desc: 原始描述
            pod_mr_links: 本次新创建的 MR 链接列表（只处理成功的）
            existing_links: 已有的 MR 链接列表
        """
        enhanced_desc = original_desc or ""

        import re

        # 1. 如果存在多个表格，只保留最后一个，删除其他的
        table_pattern = r"\n*---\n*\n*## 关联的私有库 MR\n*\n*\| Pod 名称 \| MR 链接 \|\n*\|[-|]+\|[-|]+\|\n*(.*?)(?=\n*---\n*|\Z)"
        matches = list(re.finditer(table_pattern, enhanced_desc, re.DOTALL))

        if len(matches) > 1:
            # 有多个表格，保留最后一个，删除其他的
            last_match = matches[-1]
            # 从后往前删除（避免索引变化）
            for i in range(len(matches) - 2, -1, -1):
                match = matches[i]
                enhanced_desc = (
                    enhanced_desc[: match.start()] + enhanced_desc[match.end() :]
                )

        # 2. 合并链接：本次成功的优先，覆盖旧的
        all_links = []
        seen = set()

        # 先添加本次成功的（优先）
        if pod_mr_links:
            for link in pod_mr_links:
                all_links.append({"name": link["name"], "url": link["url"]})
                seen.add(link["name"])

        # 再添加旧的（不在本次成功中的）
        if existing_links:
            for link in existing_links:
                if link["name"] not in seen:
                    all_links.append({"name": link["name"], "url": link["url"]})

        # 3. 构建新表格并替换
        if all_links:
            new_table = "\n\n---\n\n"
            new_table += "## 关联的私有库 MR\n\n"
            new_table += "| Pod 名称 | MR 链接 |\n"
            new_table += "|----------|--------|\n"

            for link in all_links:
                new_table += f"| {link['name']} | {link['url']} |\n"

            # 替换所有旧的表格
            enhanced_desc = re.sub(
                table_pattern, new_table, enhanced_desc, flags=re.DOTALL
            )

            # 如果没有匹配到（原来没有表格），直接追加
            if "## 关联的私有库 MR" not in enhanced_desc:
                enhanced_desc += new_table

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
        # 在 try 块外初始化变量，确保在 except 块中可以访问
        host = ""
        path_part = ""
        base_url = ""
        api_url = ""

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

            # 构建请求数据
            data = {
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": description,
                "remove_source_branch": False,
            }

            # 尝试不同的路径编码方式（针对不同 GitLab 版本的兼容性）
            encoding_attempts = [
                ("标准编码（斜杠编码）", urllib.parse.quote(path_part, safe="")),
                ("不编码斜杠", urllib.parse.quote(path_part, safe="/")),
            ]

            last_error = None

            for attempt_name, encoded_path in encoding_attempts:
                # 构建API URL
                api_url = f"{base_url}/projects/{encoded_path}/merge_requests"

                print(f"[DEBUG] 尝试 {attempt_name}")
                print(f"[DEBUG] GitLab MR API URL: {api_url}")
                print(f"[DEBUG] Original path: {path_part}")
                print(f"[DEBUG] Encoded path: {encoded_path}")
                print(f"[DEBUG] Source: {source_branch}, Target: {target_branch}")

                # 发送请求
                req = urllib.request.Request(
                    api_url,
                    data=json.dumps(data).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "PRIVATE-TOKEN": token,
                    },
                )

                try:
                    with urllib.request.urlopen(req, timeout=30) as response:
                        result = json.loads(response.read().decode("utf-8"))
                        print(f"[DEBUG] {attempt_name} 成功！")
                        return {
                            "platform": "GitLab",
                            "mr_url": result.get("web_url", ""),
                            "mr_iid": result.get("iid", 0),
                            "success": True,
                        }
                except urllib.error.HTTPError as e:
                    last_error = e
                    error_body = ""
                    try:
                        error_body = e.read().decode("utf-8")
                    except:
                        pass

                    print(f"[DEBUG] {attempt_name} 失败: HTTP {e.code} - {error_body}")

                    # 如果是 404，尝试下一种编码方式
                    if e.code == 404:
                        continue
                    else:
                        # 其他 HTTP 错误，直接返回
                        return {"error": f"HTTP错误 {e.code}: {e.reason}. {error_body}"}
                except urllib.error.URLError as e:
                    # 网络错误，直接返回
                    return {"error": f"网络错误: {str(e)}"}

            # 所有编码方式都失败，返回最后一个错误
            if last_error:
                error_body = ""
                try:
                    error_body = last_error.read().decode("utf-8")
                except:
                    pass
                return {
                    "error": f"所有编码方式都失败。最后错误: HTTP {last_error.code}: {last_error.reason}. {error_body}"
                }
            else:
                return {"error": "未知的错误"}
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except:
                pass

            print(f"[DEBUG] HTTP Error Details:")
            print(f"[DEBUG] Status Code: {e.code}")
            print(f"[DEBUG] Reason: {e.reason}")
            print(f"[DEBUG] Response Body: {error_body}")
            if api_url:
                print(f"[DEBUG] Failed URL: {api_url}")
            print(f"[DEBUG] Original path_part: {path_part}")
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

    def _parse_gitlab_url(self, git_url):
        """解析 GitLab URL，返回 host 和 path_part"""
        if git_url.startswith("git@"):
            parts = git_url.replace("git@", "").split(":")
            host = parts[0]
            path_part = parts[1] if len(parts) > 1 else ""
            path_part = path_part.replace(".git", "")
        else:
            from urllib.parse import urlparse

            parsed = urlparse(git_url)
            host = parsed.hostname
            path_part = parsed.path.lstrip("/").replace(".git", "")

        return host, path_part

    def _get_existing_gitlab_mr(self, project_info, source_branch, target_branch):
        """查询已存在的 GitLab MR

        Returns:
            dict: MR 信息（包含 iid, web_url, description）
            None: 不存在
        """
        git_url = project_info.get("git_url", "")
        token = project_info.get("gitlab_token", "")

        if not git_url or not token:
            return None

        if "gitlab" not in git_url.lower():
            return None

        try:
            host, path_part = self._parse_gitlab_url(git_url)
            base_url = f"https://{host}/api/v4"

            # 尝试不同的编码方式
            encoding_attempts = [
                urllib.parse.quote(path_part, safe=""),
                urllib.parse.quote(path_part, safe="/"),
            ]

            for encoded_path in encoding_attempts:
                # 查询 MR: GET /projects/:id/merge_requests?source_branch=xxx&target_branch=xxx
                api_url = f"{base_url}/projects/{encoded_path}/merge_requests?source_branch={source_branch}&target_branch={target_branch}&state=opened"

                req = urllib.request.Request(
                    api_url,
                    headers={
                        "PRIVATE-TOKEN": token,
                    },
                    method="GET",
                )

                try:
                    with urllib.request.urlopen(req, timeout=30) as response:
                        result = json.loads(response.read().decode("utf-8"))

                        # GitLab 返回的是数组
                        if result and isinstance(result, list) and len(result) > 0:
                            mr = result[0]
                            print(
                                f"[DEBUG] 找到已存在的 MR: IID={mr.get('iid')}, URL={mr.get('web_url')}"
                            )
                            return {
                                "iid": mr.get("iid"),
                                "web_url": mr.get("web_url"),
                                "description": mr.get("description", ""),
                            }
                except urllib.error.HTTPError as e:
                    if e.code == 404:
                        continue
                    else:
                        print(f"[DEBUG] 查询 MR 失败: HTTP {e.code}")
                        return None
                except Exception as e:
                    print(f"[DEBUG] 查询 MR 异常: {e}")
                    return None

            return None
        except Exception as e:
            print(f"[DEBUG] _get_existing_gitlab_mr 异常: {e}")
            return None

    def _update_gitlab_mr_description(self, project_info, mr_iid, new_description):
        """更新 GitLab MR 的描述

        Returns:
            dict: 更新结果
        """
        git_url = project_info.get("git_url", "")
        token = project_info.get("gitlab_token", "")

        if not git_url or not token:
            return {"error": "Git URL 或 Token 为空"}

        if "gitlab" not in git_url.lower():
            return {"error": "不是 GitLab 项目"}

        try:
            host, path_part = self._parse_gitlab_url(git_url)
            base_url = f"https://{host}/api/v4"

            # 尝试不同的编码方式
            encoding_attempts = [
                urllib.parse.quote(path_part, safe=""),
                urllib.parse.quote(path_part, safe="/"),
            ]

            for encoded_path in encoding_attempts:
                # 更新 MR: PUT /projects/:id/merge_requests/:iid
                api_url = f"{base_url}/projects/{encoded_path}/merge_requests/{mr_iid}"

                data = {
                    "description": new_description,
                }

                req = urllib.request.Request(
                    api_url,
                    data=json.dumps(data).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "PRIVATE-TOKEN": token,
                    },
                    method="PUT",
                )

                try:
                    with urllib.request.urlopen(req, timeout=30) as response:
                        result = json.loads(response.read().decode("utf-8"))
                        print(f"[DEBUG] MR 描述更新成功: {result.get('web_url')}")
                        return {
                            "success": True,
                            "mr_url": result.get("web_url", ""),
                        }
                except urllib.error.HTTPError as e:
                    if e.code == 404:
                        continue
                    else:
                        error_body = e.read().decode("utf-8")
                        return {"error": f"HTTP错误 {e.code}: {error_body}"}
                except Exception as e:
                    return {"error": f"更新失败: {str(e)}"}

            return {"error": "无法找到项目"}
        except Exception as e:
            return {"error": f"_update_gitlab_mr_description 异常: {str(e)}"}


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
        self.initUI()
        self.load_tokens_from_config()

    def load_tokens_from_config(self):
        """从配置加载Token"""
        # 从配置文件重新加载，确保使用最新的token
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

    def initUI(self):
        """初始化UI"""
        self.setWindowTitle("创建 Merge Request")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Token 配置区域
        token_group = QGroupBox("访问令牌配置")
        token_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        token_layout = QGridLayout()
        token_layout.setSpacing(10)

        # GitLab Token
        gitlab_label = QLabel("GitLab Token:")
        self.gitlab_token_input = QLineEdit()
        self.gitlab_token_input.setEchoMode(QLineEdit.Password)
        self.gitlab_token_input.setPlaceholderText("输入 GitLab 访问令牌")
        token_layout.addWidget(gitlab_label, 0, 0)
        token_layout.addWidget(self.gitlab_token_input, 0, 1)

        # GitHub Token
        github_label = QLabel("GitHub Token:")
        self.github_token_input = QLineEdit()
        self.github_token_input.setEchoMode(QLineEdit.Password)
        self.github_token_input.setPlaceholderText("输入 GitHub 访问令牌")
        token_layout.addWidget(github_label, 1, 0)
        token_layout.addWidget(self.github_token_input, 1, 1)

        token_group.setLayout(token_layout)
        layout.addWidget(token_group)

        # MR 信息表格
        table_group = QGroupBox("Merge Request 信息")
        table_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        table_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["项目名称", "源分支", "目标分支", "标题", "描述"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: #ffffff;
                gridline-color: #e5e5e5;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #e5e5e5;
                font-weight: bold;
            }
        """)

        # 填充表格数据
        self._populate_table()

        table_layout.addWidget(self.table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 1px solid #e5e5e5;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.02);
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        submit_btn = QPushButton("提交 MR")
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        submit_btn.clicked.connect(self.submit_mrs)
        button_layout.addWidget(submit_btn)

        layout.addLayout(button_layout)

    def _populate_table(self):
        """填充表格数据"""
        self.table.setRowCount(len(self.pods_info))

        # 设置行高以便下拉框完整显示
        self.table.verticalHeader().setDefaultSectionSize(40)

        # 对项目进行排序：主工程优先，其他按名称排序
        sorted_items = sorted(
            self.pods_info.items(),
            key=lambda x: (0 if x[1].get("is_main_project", False) else 1, x[0]),
        )

        row = 0
        for pod_name, info in sorted_items:
            if "error" in info:
                continue

            is_main_project = info.get("is_main_project", False)

            # 项目名称
            name_item = QTableWidgetItem(pod_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)

            # 源分支下拉框
            source_combo = QComboBox()
            source_combo.setMinimumHeight(32)
            remote_branches = info.get("remote_branches", [])
            current_branch = info.get("current_branch", "")
            podfile_branch = info.get("podfile_branch", "")

            # 确定默认源分支：
            # - 主工程：使用当前分支
            # - Pod库：优先使用 podfile_branch，否则使用当前分支
            if is_main_project:
                default_source = current_branch
            else:
                default_source = podfile_branch if podfile_branch else current_branch

            # 添加分支选项，默认源分支放在第一位
            if default_source:
                source_combo.addItem(default_source)
            # 添加当前分支（如果不同于默认）
            if current_branch and current_branch != default_source:
                source_combo.addItem(current_branch)
            # 添加其他远程分支
            for branch in remote_branches:
                if branch != default_source and branch != current_branch:
                    source_combo.addItem(branch)

            self.table.setCellWidget(row, 1, source_combo)

            # 目标分支下拉框
            target_combo = QComboBox()
            target_combo.setMinimumHeight(32)
            target_combo.setEditable(True)  # 允许手动输入

            # 添加常用目标分支
            common_targets = ["master", "main", "develop", "release"]
            for target in common_targets:
                if target in remote_branches:
                    target_combo.addItem(target)

            # 添加其他远程分支
            for branch in remote_branches:
                if branch not in common_targets:
                    target_combo.addItem(branch)

            # 默认选择 master 或 main
            if "master" in remote_branches:
                target_combo.setCurrentText("master")
            elif "main" in remote_branches:
                target_combo.setCurrentText("main")
            elif "develop" in remote_branches:
                target_combo.setCurrentText("develop")

            self.table.setCellWidget(row, 2, target_combo)

            # 标题 - 使用实际的默认源分支
            default_title = f"Merge {default_source} into target"
            title_item = QTableWidgetItem(default_title)
            self.table.setItem(row, 3, title_item)

            # 描述 - 默认为最近3次commit信息
            recent_commits = info.get("recent_commits", [])
            if recent_commits:
                desc_text = "\n".join([f"- {commit}" for commit in recent_commits])
            else:
                desc_text = ""
            desc_item = QTableWidgetItem(desc_text)
            self.table.setItem(row, 4, desc_item)

            # 设置当前行高度
            self.table.setRowHeight(row, 40)

            row += 1

        # 调整实际行数
        self.table.setRowCount(row)
