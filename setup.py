#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
py2app setup script for Pod Pilot
"""

from setuptools import setup
import os


# 获取资源文件列表
def get_resources():
    resources = []

    # 添加图标文件
    icons_dir = "resources/icons"
    if os.path.exists(icons_dir):
        icons = [
            os.path.join(icons_dir, f)
            for f in os.listdir(icons_dir)
            if f.startswith("app_icon") and f.endswith(".png")
        ]
        if icons:
            resources.extend(icons)

    return resources


# py2app 配置
APP = ["main.py"]
DATA_FILES = get_resources()
OPTIONS = {
    "argv_emulation": True,
    "packages": ["PyQt5", "src"],
    "includes": ["PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui"],
    "excludes": [],
    "iconfile": "resources/icons/app_icon.icns",  # macOS 图标文件
    "plist": {
        "CFBundleName": "Pod Pilot",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1.0.0",
        "CFBundleIdentifier": "com.podpilot.app",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "10.12",
    },
    "strip": False,
    "optimize": 0,
}

setup(
    app=APP,
    name="Pod Pilot",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
