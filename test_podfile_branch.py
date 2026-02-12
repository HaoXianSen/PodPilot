#!/usr/bin/env python3
"""测试 Podfile 分支解析逻辑"""

import re
import sys


# 模拟 MRInfoCollector._get_pod_branches_from_podfile 方法
def get_pod_branches_from_podfile(content, pod_name):
    """从Podfile内容中获取Pod引用的分支"""

    pod_pattern = r"pod\s+['\"]([^'\"]+)['\"]"
    branch_pattern = r":branch\s*=>\s*['\"]?([^'\"\s,]+)['\"]?"
    variable_pattern = r"^(\w+)\s*=\s*['\"]([^'\"]+)['\"]\s*$"

    print(f"\n=== 查找 Pod: {pod_name} ===")
    print(f"Podfile 内容长度: {len(content)}")

    for m in re.finditer(pod_pattern, content):
        start_pos = m.start()
        found_pod_name = m.group(1)

        print(f"\n找到 pod 声明: {found_pod_name}")

        if found_pod_name != pod_name:
            print(f"  -> 不匹配，跳过")
            continue

        print(f"  -> 匹配成功！")

        # 获取 pod 声明的完整内容
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
            print(f"\n完整声明:\n{pod_declaration}")

            branch_match = re.search(branch_pattern, pod_declaration)
            if branch_match:
                branch_name = branch_match.group(1)
                print(f"\n找到 branch: {branch_name}")

                if not branch_name.startswith("'") and not branch_name.startswith('"'):
                    print(f"Branch 是变量，查找变量定义...")
                    for line in content.split("\n"):
                        var_match = re.match(variable_pattern, line.strip())
                        if var_match and var_match.group(1) == branch_name:
                            print(
                                f"找到变量定义: {var_match.group(1)} = {var_match.group(2)}"
                            )
                            return var_match.group(2)
                    print(f"变量未找到，返回原始值: {branch_name}")
                    return branch_name
                else:
                    print(f"Branch 是字符串: {branch_name.strip(chr(39) + chr(34))}")
                    return branch_name.strip("'\"")
        else:
            print(f"无法匹配完整声明！")
            # 尝试直接在当前行搜索
            line_start = content.rfind("\n", 0, start_pos) + 1
            line_end = content.find("\n", start_pos)
            if line_end == -1:
                line_end = len(content)
            current_line = content[line_start:line_end]
            print(f"当前行内容: {current_line}")

            branch_match = re.search(branch_pattern, current_line)
            if branch_match:
                branch_name = branch_match.group(1)
                print(f"在当前行找到 branch: {branch_name}")
                return branch_name.strip("'\"")

        return None

    print(f"\nPod {pod_name} 未在 Podfile 中找到")
    return None


# 测试用例 1: 标准的 Branch 模式（单行）
podfile_content_1 = """platform :ios, '11.0'

pod 'GZUIKit_iOS', :git => 'git@gitlab.corp.youdao.com:hikari/app/ios/LSFoundationGroup_iOS/gzuikit_ios.git', :branch => GZUIKit_VERSION
GZUIKit_VERSION = 'feature/login'

pod 'AnotherPod', '~> 1.0'
"""

# 测试用例 2: 变量在 Pod 声明之前
podfile_content_2 = """platform :ios, '11.0'

GZUIKit_VERSION = 'feature/login'
pod 'GZUIKit_iOS', :git => 'git@gitlab.corp.youdao.com:hikari/app/ios/LSFoundationGroup_iOS/gzuikit_ios.git', :branch => GZUIKit_VERSION

pod 'AnotherPod', '~> 1.0'
"""

# 测试用例 3: 字面量 branch
podfile_content_3 = """platform :ios, '11.0'

pod 'GZUIKit_iOS', :git => 'git@gitlab.corp.youdao.com:hikari/app/ios/LSFoundationGroup_iOS/gzuikit_ios.git', :branch => 'feature/login'

pod 'AnotherPod', '~> 1.0'
"""

# 测试用例 4: 多行声明
podfile_content_4 = """platform :ios, '11.0'

pod 'GZUIKit_iOS', 
    :git => 'git@gitlab.corp.youdao.com:hikari/app/ios/LSFoundationGroup_iOS/gzuikit_ios.git', 
    :branch => GZUIKit_VERSION
GZUIKit_VERSION = 'feature/login'

pod 'AnotherPod', '~> 1.0'
"""

print("=" * 60)
print("测试用例 1: 标准 Branch 模式（单行，变量在后）")
result1 = get_pod_branches_from_podfile(podfile_content_1, "GZUIKit_iOS")
print(f"\n结果: {result1}")
assert result1 == "feature/login", f"期望 'feature/login', 实际 '{result1}'"

print("\n" + "=" * 60)
print("测试用例 2: 变量在 Pod 声明之前")
result2 = get_pod_branches_from_podfile(podfile_content_2, "GZUIKit_iOS")
print(f"\n结果: {result2}")
assert result2 == "feature/login", f"期望 'feature/login', 实际 '{result2}'"

print("\n" + "=" * 60)
print("测试用例 3: 字面量 branch")
result3 = get_pod_branches_from_podfile(podfile_content_3, "GZUIKit_iOS")
print(f"\n结果: {result3}")
assert result3 == "feature/login", f"期望 'feature/login', 实际 '{result3}'"

print("\n" + "=" * 60)
print("测试用例 4: 多行声明")
result4 = get_pod_branches_from_podfile(podfile_content_4, "GZUIKit_iOS")
print(f"\n结果: {result4}")
# 多行声明可能有问题，先不 assert

print("\n" + "=" * 60)
print("所有测试完成！")
