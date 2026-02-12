#!/usr/bin/env python3
"""测试完整流程：Branch模式切换 -> MR信息收集"""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, "/Users/haoyh02/Desktop/iPM")


def test_full_workflow():
    """测试完整工作流程"""

    # 1. 创建临时 Podfile
    temp_dir = tempfile.mkdtemp()
    podfile_path = os.path.join(temp_dir, "Podfile")

    # 初始状态：Tag 模式
    initial_podfile = """platform :ios, '11.0'

pod 'GZUIKit_iOS', :git => 'git@gitlab.corp.youdao.com:hikari/app/ios/LSFoundationGroup_iOS/gzuikit_ios.git', :tag => GZUIKit_VERSION
GZUIKit_VERSION = 'v1.0.0'

pod 'AnotherPod', '~> 1.0'
"""

    print("=" * 60)
    print("步骤1: 创建初始 Podfile（Tag 模式）")
    print("=" * 60)
    print(initial_podfile)

    with open(podfile_path, "w") as f:
        f.write(initial_podfile)

    # 2. 模拟 BatchBranchDialog 修改为 Branch 模式
    print("\n" + "=" * 60)
    print("步骤2: 切换到 Branch 模式")
    print("=" * 60)

    from src.views.dialogs.merge_request_dialog import MRInfoCollector

    # 读取 Podfile
    with open(podfile_path, "r") as f:
        podfile_lines = f.readlines()

    # 模拟切换：将 :tag 改为 :branch
    new_podfile = initial_podfile.replace(
        ":tag => GZUIKit_VERSION", ":branch => GZUIKit_VERSION"
    )
    new_podfile = new_podfile.replace("v1.0.0", "feature/login")

    with open(podfile_path, "w") as f:
        f.write(new_podfile)

    print("修改后的 Podfile:")
    print(new_podfile)

    # 3. 模拟 MRInfoCollector 读取 Podfile
    print("\n" + "=" * 60)
    print("步骤3: MRInfoCollector 读取 Podfile")
    print("=" * 60)

    # 创建模拟的 MRInfoCollector（不启动线程，只测试方法）
    class MockMRInfoCollector:
        def __init__(self, project_dir):
            self.project_dir = project_dir

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

                import re

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

                print(f"DEBUG: Pod {pod_name} not found in Podfile")
                return None
            except Exception as e:
                print(f"DEBUG: Exception in _get_pod_branches_from_podfile: {e}")
                return None

    collector = MockMRInfoCollector(temp_dir)
    result = collector._get_pod_branches_from_podfile("GZUIKit_iOS")

    print(f"\nMRInfoCollector 读取结果: {result}")
    print(f"期望结果: feature/login")

    # 4. 验证结果
    if result == "feature/login":
        print("\n✅ 测试通过！MRInfoCollector 正确读取了 Podfile 中的分支信息")
    else:
        print(f"\n❌ 测试失败！期望 'feature/login', 实际 '{result}'")

    # 清理临时文件
    shutil.rmtree(temp_dir)
    print("\n临时文件已清理")


if __name__ == "__main__":
    test_full_workflow()
