#!/usr/bin/env python3
"""测试 Branch → Tag 转换功能"""

import re
import sys


def parse_branch_reference(pod_line):
    """解析pod行中的branch引用，返回(branch_type, branch_value, references)"""
    branch_pattern = r":branch\s*=>\s*([^,\s\n]+)"
    matches = re.finditer(branch_pattern, pod_line)

    references = []
    for match in matches:
        branch_value = match.group(1).strip()
        match_text = match.group(0)

        if (branch_value.startswith("'") and branch_value.endswith("'")) or (
            branch_value.startswith('"') and branch_value.endswith('"')
        ):
            branch_type = "literal"
            actual_value = branch_value[1:-1]
        else:
            branch_type = "variable"
            actual_value = branch_value

        references.append(
            {"type": branch_type, "value": actual_value, "match_text": match_text}
        )

    if references:
        return references[0]["type"], references[0]["value"], references
    return None, None, []


def convert_branch_to_tag(pod_declaration):
    """将Pod声明中的:branch =>转换为:tag =>"""
    return re.sub(r":branch\s*=>", ":tag =>", pod_declaration)


def find_variable_definition(var_name, lines):
    """查找变量定义，返回(行号, 当前值)"""
    for i, line in enumerate(lines):
        match = re.match(rf'^\s*{re.escape(var_name)}\s*=\s*[\'"]([^\'"]*)[\'"]', line)
        if match:
            return i, match.group(1)
    return None, None


def test_branch_to_tag_conversion():
    """测试 Branch → Tag 转换"""

    # 测试用例1: 变量引用分支
    podfile_lines = [
        "pod 'GZUIKit_iOS', :git =>'git@gitlab.corp.youdao.com:hikari/app/ios/LSFoundationGroup_iOS/gzuikit_ios.git', :branch => GZUIKit_VERSION",
        "GZUIKit_VERSION = 'feature/exercise_xxc'",
    ]

    selected_tag = "v1.1.6"

    new_lines = podfile_lines.copy()

    # 查找 Pod 声明
    for i, line in enumerate(new_lines):
        if "pod 'GZUIKit_iOS'" in line or f'pod "GZUIKit_iOS"' in line:
            pod_declaration = line
            print(f"原始 Pod 声明:\n{pod_declaration}\n")

            # 转换 :branch => 为 :tag => 并更新
            branch_references = parse_branch_reference(pod_declaration)
            if branch_references:
                branch_type, branch_value, refs = branch_references

                # 转换所有 :branch => 为 :tag =>
                new_declaration = convert_branch_to_tag(pod_declaration)
                print(f"转换后 Pod 声明:\n{new_declaration}\n")

                # 更新变量值
                if branch_type == "variable":
                    var_line_idx, current_value = find_variable_definition(
                        branch_value, new_lines
                    )
                    if var_line_idx is not None:
                        escaped_var = re.escape(branch_value)
                        new_lines[var_line_idx] = re.sub(
                            rf"({escaped_var}\s*=\s*['\"])[^'\"]*(['\"])",
                            rf"\1{selected_tag}\2",
                            new_lines[var_line_idx],
                        )
                        print(f"更新变量: {new_lines[var_line_idx]}\n")

                # 使用新的 Pod 声明替换旧的
                new_lines[i] = new_declaration

            break

    # 输出完整结果
    print("最终 Podfile 内容:")
    for line in new_lines:
        print(line)


if __name__ == "__main__":
    test_branch_to_tag_conversion()
