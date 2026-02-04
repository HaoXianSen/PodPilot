#!/usr/bin/env python3
"""
PodPilot 配置迁移脚本

将旧的 .pod_manager_config.json 迁移到 .podpilot_config.json
"""

import os
import shutil


def migrate_config():
    """迁移配置文件"""
    old_config = os.path.expanduser("~/.pod_manager_config.json")
    new_config = os.path.expanduser("~/.podpilot_config.json")

    # 检查旧配置是否存在
    if not os.path.exists(old_config):
        print(f"旧配置文件不存在: {old_config}")
        print("无需迁移")
        return False

    # 检查新配置是否已存在
    if os.path.exists(new_config):
        print(f"新配置文件已存在: {new_config}")
        choice = input("是否覆盖? (y/n): ").strip().lower()
        if choice != "y":
            print("已取消迁移")
            return False

    # 复制配置文件
    try:
        shutil.copy2(old_config, new_config)
        print(f"✅ 配置文件已成功迁移")
        print(f"   旧配置: {old_config}")
        print(f"   新配置: {new_config}")

        # 询问是否删除旧配置
        print("\n是否删除旧配置文件?")
        choice = input("删除 .pod_manager_config.json? (y/n): ").strip().lower()
        if choice == "y":
            os.remove(old_config)
            print(f"✅ 已删除旧配置文件")

        return True

    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("PodPilot 配置迁移工具")
    print("=" * 50)
    print()

    if migrate_config():
        print("\n✅ 迁移完成！")
        print("请重启 PodPilot 应用。")
    else:
        print("\n⚠️  迁移未执行")
