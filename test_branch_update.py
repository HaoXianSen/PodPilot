#!/usr/bin/env python3
"""测试 BatchBranchDialog 修改 Podfile 的实际效果"""

import sys

sys.path.insert(0, "/Users/haoyh02/Desktop/iPM")


# 模拟 BranchSwitchWorker._update_podfile_for_branch 方法
def update_podfile_for_branch(lines, pod_name, git_url, branch_name):
    """更新Podfile以切换到branch模式"""
    import re

    def _get_full_pod_declaration(lines, start_idx, pod_name):
        if start_idx >= len(lines):
            return None, None, None

        line = lines[start_idx]
        pod_pattern = f"pod '{pod_name}'"
        pod_with_subspec_pattern = f"pod '{pod_name}/"

        if (
            pod_pattern not in line
            and pod_with_subspec_pattern not in line
            and f'pod "{pod_name}"' not in line
            and f'pod "{pod_name}/' not in line
        ):
            return None, None, None

        full_lines = [line.rstrip("\n")]
        end_idx = start_idx

        i = start_idx
        while i < len(lines):
            current_line = lines[i]
            stripped = current_line.rstrip()

            if stripped.endswith("\\"):
                full_lines.append(stripped[:-1])
                i += 1
                end_idx = i
            else:
                if i > start_idx:
                    full_lines.append(stripped)
                break

        full_declaration = "\n".join(full_lines)
        return start_idx, end_idx, full_declaration

    def _extract_version_constant(declaration):
        patterns = [
            r":tag\s*=>\s*([A-Z]\w*)",
            r":branch\s*=>\s*([A-Z]\w*)",
        ]
        for pattern in patterns:
            match = re.search(pattern, declaration)
            if match:
                return match.group(1)
        return None

    def _update_constant_value(lines, constant_name, new_value):
        pattern = rf"^({re.escape(constant_name)}\s*=\s*['\"])[^'\"]*(['\"])"
        for i, line in enumerate(lines):
            if re.match(pattern, line.strip()):
                lines[i] = re.sub(pattern, rf"\g<1>{new_value}\g<2>", line)
                return True
        return False

    for i, line in enumerate(lines):
        pod_pattern = f"pod '{pod_name}'"
        pod_with_subspec_pattern = f"pod '{pod_name}/"

        matches = (
            pod_pattern in line
            or pod_with_subspec_pattern in line
            or f'pod "{pod_name}"' in line
            or f'pod "{pod_name}/' in line
        )

        if not matches:
            continue

        start_idx, end_idx, full_declaration = _get_full_pod_declaration(
            lines, i, pod_name
        )

        if full_declaration is None:
            continue

        print(f"找到 Pod 声明 ({start_idx}-{end_idx}):")
        print(full_declaration)
        print()

        constant_name = _extract_version_constant(full_declaration)

        if constant_name:
            print(f"使用常量: {constant_name}")
            if _update_constant_value(lines, constant_name, branch_name):
                print(f"更新常量值: {constant_name} = '{branch_name}'")
                updated_declaration = full_declaration.replace(
                    f":tag => {constant_name}", f":branch => {constant_name}"
                )
                print(f"更新声明: {updated_declaration}")
                if start_idx == end_idx:
                    lines[start_idx] = updated_declaration + "\n"
                else:
                    lines[start_idx] = updated_declaration + "\n"
                    for j in range(start_idx + 1, end_idx + 1):
                        lines[j] = ""
                return True
        else:
            print("不使用常量")
            updated_declaration = full_declaration

            updated_declaration = re.sub(
                r":tag\s*=>\s*['\"][^'\"]*['\"]",
                f":branch => '{branch_name}'",
                updated_declaration,
            )

            updated_declaration = re.sub(
                r":branch\s*=>\s*['\"][^'\"]*['\"]",
                f":branch => '{branch_name}'",
                updated_declaration,
            )

            print(f"更新声明: {updated_declaration}")
            if start_idx == end_idx:
                lines[start_idx] = updated_declaration + "\n"
            else:
                lines[start_idx] = updated_declaration + "\n"
                for j in range(start_idx + 1, end_idx + 1):
                    lines[j] = ""
            return True

    return False


# 测试用例 1: Tag 模式（使用常量）-> Branch 模式
print("=" * 60)
print("测试用例 1: Tag 模式（使用常量）-> Branch 模式")
print("=" * 60)

podfile_lines_1 = [
    "platform :ios, '11.0'\n",
    "\n",
    "pod 'GZUIKit_iOS', :git => 'git@gitlab.corp.youdao.com:hikari/app/ios/LSFoundationGroup_iOS/gzuikit_ios.git', :tag => GZUIKit_VERSION\n",
    "GZUIKit_VERSION = 'v1.0.0'\n",
    "\n",
    "pod 'AnotherPod', '~> 1.0'\n",
]

print("\n原始 Podfile:")
print("".join(podfile_lines_1))

result = update_podfile_for_branch(
    podfile_lines_1,
    "GZUIKit_iOS",
    "git@gitlab.corp.youdao.com:hikari/app/ios/LSFoundationGroup_iOS/gzuikit_ios.git",
    "feature/login",
)

print(f"\n修改结果: {result}")
print("\n修改后的 Podfile:")
print("".join(podfile_lines_1))

# 验证常量值是否更新
print("\n验证:")
for i, line in enumerate(podfile_lines_1):
    if "GZUIKit_VERSION" in line:
        print(f"  行 {i}: {line.strip()}")

# 测试用例 2: 字面量 Tag -> Branch
print("\n" + "=" * 60)
print("测试用例 2: 字面量 Tag -> Branch")
print("=" * 60)

podfile_lines_2 = [
    "platform :ios, '11.0'\n",
    "\n",
    "pod 'GZUIKit_iOS', :git => 'git@gitlab.corp.youdao.com:hikari/app/ios/LSFoundationGroup_iOS/gzuikit_ios.git', :tag => 'v1.0.0'\n",
    "\n",
    "pod 'AnotherPod', '~> 1.0'\n",
]

print("\n原始 Podfile:")
print("".join(podfile_lines_2))

result = update_podfile_for_branch(
    podfile_lines_2,
    "GZUIKit_iOS",
    "git@gitlab.corp.youdao.com:hikari/app/ios/LSFoundationGroup_iOS/gzuikit_ios.git",
    "feature/login",
)

print(f"\n修改结果: {result}")
print("\n修改后的 Podfile:")
print("".join(podfile_lines_2))

print("\n所有测试完成！")
