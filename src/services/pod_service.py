import os
import re
from typing import List, Dict, Tuple, Any, Union


class PodService:
    """Pod管理服务"""

    @staticmethod
    def get_pod_name_from_text(text: str) -> str:
        """从显示文本中提取真实的pod名称"""
        match = re.search(r"[\w/\-]+", text)
        if match:
            return match.group(0)
        return text.strip()

    @staticmethod
    def load_pods_from_podfile(
        podfile_path: str,
    ) -> Tuple[List[str], List[str], List[str], List[str], List[str]]:
        """
        从Podfile加载Pod列表
        返回: (所有pods, dev_pods, tag_pods, branch_pods, git_pods)
        """
        if not os.path.exists(podfile_path):
            return [], [], [], [], []

        try:
            with open(podfile_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            filtered_lines = []
            for line in lines:
                if not line.lstrip().startswith("#"):
                    filtered_lines.append(line)

            filtered_content = "\n".join(filtered_lines)
            pod_pattern = r"pod\s+['\"]([^'\"]+)['\"]"

            pods = []
            dev_pods = []
            tag_pods = []
            branch_pods = []
            git_pods = []

            for m in re.finditer(pod_pattern, filtered_content):
                start_pos = m.start()
                pod_name = m.group(1)

                next_pod_match = re.search(pod_pattern, filtered_content[m.end() :])
                if next_pod_match:
                    end_pos = m.end() + next_pod_match.start()
                else:
                    end_pos = len(filtered_content)

                pod_declaration = filtered_content[start_pos:end_pos].rstrip()
                pods.append(pod_name)

                if ":path" in pod_declaration:
                    dev_pods.append(pod_name)
                elif ":tag" in pod_declaration:
                    tag_pods.append(pod_name)
                elif ":branch" in pod_declaration:
                    branch_pods.append(pod_name)
                elif ":git" in pod_declaration:
                    git_pods.append(pod_name)

            return pods, dev_pods, tag_pods, branch_pods, git_pods

        except Exception as e:
            print(f"加载Pod失败: {str(e)}")
            return [], [], [], [], []

    @staticmethod
    def get_full_pod_declaration(
        lines: List[str], pod_name: str
    ) -> Tuple[Union[int, None], Union[int, None], str]:
        """
        获取完整的pod声明（可能跨越多行）
        返回: (start_idx, end_idx, full_declaration)
        """
        for i, line in enumerate(lines):
            if f"pod '{pod_name}'" in line or f'pod "{pod_name}"' in line:
                first_line = line.rstrip("\n")

                if first_line.rstrip().endswith("\\"):
                    full_lines = [first_line[:-1]]
                    j = i + 1
                    while j < len(lines):
                        current_line = lines[j].rstrip("\n")
                        stripped = current_line.rstrip()

                        if stripped.endswith("\\"):
                            full_lines.append(stripped[:-1])
                            j += 1
                        else:
                            full_lines.append(stripped)
                            break

                    end_idx = j + 1
                else:
                    full_lines = [first_line]
                    end_idx = i + 1

                full_declaration = "\n".join(full_lines)
                return i, end_idx, full_declaration

        return None, None, ""

    @staticmethod
    def filter_pods(pods: List[str], search_text: str) -> List[str]:
        """过滤Pod列表"""
        search_text_lower = search_text.lower()
        return [pod for pod in pods if search_text_lower in pod.lower()]

    @staticmethod
    def save_original_pod_references(
        lines: List[str], project_path: str, dev_pods: List[str]
    ) -> Dict[str, Dict[str, str]]:
        """解析并保存原始Pod引用信息"""
        original_pod_references = {}

        for line in lines:
            line_stripped = line.lstrip()
            if line_stripped.startswith("#"):
                continue

            pod_full_pattern = r"(pod\s+['\"][^'\"]+['\"].*)"
            match = re.search(pod_full_pattern, line_stripped)

            if match:
                full_declaration = match.group(1)
                pod_name_match = re.search(
                    r"pod\s+['\"]([^'\"]+)['\"]", full_declaration
                )
                if pod_name_match:
                    pod_name = pod_name_match.group(1)
                    if pod_name not in dev_pods:
                        original_pod_references[pod_name] = {
                            "line": line.rstrip("\n"),
                            "full_declaration": full_declaration,
                        }

        return original_pod_references

    @staticmethod
    def get_pod_priority(
        pod: str,
        dev_pods: List[str],
        branch_pods: List[str],
        tag_pods: List[str],
        git_pods: List[str],
        current_config: Dict[str, str],
    ) -> int:
        """计算Pod的优先级"""
        if pod in dev_pods:
            return 1
        elif pod in branch_pods:
            return 2
        elif pod in current_config:
            return 3
        elif pod in tag_pods:
            return 4
        elif pod in git_pods:
            return 5
        else:
            return 6

    @staticmethod
    def switch_pod_mode(
        podfile_lines: List[str],
        pod_name: str,
        mode: str,
        local_path: Union[str, None] = None,
        original_line: Union[str, None] = None,
    ) -> Tuple[List[str], bool]:
        """
        切换Pod的引用模式
        mode: 'dev', 'normal', 'tag', 'branch'
        返回: (新行列表, 是否修改成功)
        """
        new_lines = podfile_lines.copy()
        start_idx, end_idx, full_declaration = PodService.get_full_pod_declaration(
            new_lines, pod_name
        )

        if full_declaration is None:
            return new_lines, False

        modified = False

        if mode == "dev":
            if ":path" not in full_declaration and local_path:
                new_declaration = re.sub(
                    r"pod\s+['\"]" + re.escape(pod_name) + r"['\"].*",
                    f"pod '{pod_name}', :path => '{local_path}'",
                    full_declaration,
                )
                if start_idx is not None and end_idx is not None:
                    new_line = new_declaration + "\n"
                    if start_idx == end_idx:
                        new_lines[start_idx] = new_line
                    else:
                        new_lines[start_idx:end_idx] = [new_line]
                modified = True

        elif mode == "normal" and original_line:
            if (
                ":path" in full_declaration
                or ":tag" in full_declaration
                or ":branch" in full_declaration
            ):
                if start_idx is not None and end_idx is not None:
                    if start_idx == end_idx:
                        new_lines[start_idx] = original_line + "\n"
                    else:
                        new_lines[start_idx:end_idx] = [original_line + "\n"]
                modified = True

        elif mode == "tag" and local_path:
            if ":tag =>" in full_declaration:
                new_declaration = re.sub(
                    r"(:tag\s*=>\s*)['\"][^'\"]*['\"]",
                    f":tag => '{local_path}'",
                    full_declaration,
                )
            else:
                if full_declaration.rstrip().endswith(","):
                    new_declaration = (
                        full_declaration.rstrip() + f" :tag => '{local_path}'"
                    )
                else:
                    if "," in full_declaration:
                        parts = full_declaration.rsplit(",", 1)
                        new_declaration = (
                            parts[0]
                            + ","
                            + parts[1].rstrip()
                            + f", :tag => '{local_path}'"
                        )
                    else:
                        new_declaration = (
                            full_declaration.rstrip() + f", :tag => '{local_path}'"
                        )

            if start_idx is not None and end_idx is not None:
                new_line = new_declaration + "\n"
                if start_idx == end_idx:
                    new_lines[start_idx] = new_line
                else:
                    new_lines[start_idx:end_idx] = [new_line]
            modified = True

        elif mode == "branch" and local_path:
            if ":branch =>" in full_declaration:
                new_declaration = re.sub(
                    r"(:branch\s*=>\s*)['\"][^'\"]*['\"]",
                    f":branch => '{local_path}'",
                    full_declaration,
                )
            else:
                if full_declaration.rstrip().endswith(","):
                    new_declaration = (
                        full_declaration.rstrip() + f" :branch => '{local_path}'"
                    )
                else:
                    if "," in full_declaration:
                        parts = full_declaration.rsplit(",", 1)
                        new_declaration = (
                            parts[0]
                            + ","
                            + parts[1].rstrip()
                            + f", :branch => '{local_path}'"
                        )
                    else:
                        new_declaration = (
                            full_declaration.rstrip() + f", :branch => '{local_path}'"
                        )

            if start_idx is not None and end_idx is not None:
                new_line = new_declaration + "\n"
                if start_idx == end_idx:
                    new_lines[start_idx] = new_line
                else:
                    new_lines[start_idx:end_idx] = [new_line]
            modified = True

        return new_lines, modified

    @staticmethod
    def extract_pod_mode_info(pod_declaration: str) -> Dict[str, Any]:
        """从 Pod 声明中提取模式信息

        Args:
            pod_declaration: Pod 的完整声明（可能跨多行）

        Returns:
            {'mode': 'branch'|'tag'|'git'|'dev'|'normal', 'data': {...}}
            例如: {'mode': 'branch', 'data': {'branch': 'feature/test'}}
        """
        result = {"mode": "normal", "data": {}}

        if ":path" in pod_declaration:
            result["mode"] = "dev"
            match = re.search(r":path\s*=>\s*['\"]([^'\"]+)['\"]", pod_declaration)
            if match:
                result["data"] = {"path": match.group(1)}

        elif ":branch" in pod_declaration:
            result["mode"] = "branch"
            match = re.search(r":branch\s*=>\s*['\"]([^'\"]+)['\"]", pod_declaration)
            if match:
                result["data"] = {"branch": match.group(1)}

        elif ":tag" in pod_declaration:
            result["mode"] = "tag"
            match = re.search(r":tag\s*=>\s*['\"]([^'\"]+)['\"]", pod_declaration)
            if match:
                result["data"] = {"tag": match.group(1)}

        elif ":git" in pod_declaration:
            result["mode"] = "git"
            match = re.search(r":git\s*=>\s*['\"]([^'\"]+)['\"]", pod_declaration)
            if match:
                result["data"] = {"git": match.group(1)}

        return result
