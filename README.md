# iOS Pod Manager

一个用于管理 iOS 项目 CocoaPods 依赖的桌面应用程序，基于 PyQt5 构建。

## 功能特性

### Pod 依赖管理
- **项目管理**：轻松添加和移除 iOS 项目
- **Pod 配置**：配置 Pod 的本地开发路径
- **模式切换**：
  - 开发模式 (`:path`) - 使用本地代码进行开发
  - 正常模式 - 恢复为远程依赖
  - Tag模式 (`:tag`) - 指定特定版本标签
  - Branch模式 (`:branch`) - 指定特定分支
- **搜索筛选**：快速查找和过滤 Pod

### Git Tag 管理
- **创建 Tag**：为 Pod 仓库创建带注释的 Git Tag
- **智能验证**：
  - Tag 名称格式验证
  - 检测已存在的 Tag
  - 自动检测非法字符
- **版本建议**：根据已有 Tag 智能建议下一个版本号
- **消息模板**：预定义的 Tag 消息模板
- **Tag 历史**：查看和浏览 Pod 的 Tag 历史

### 现代化 UI
- macOS 风格的设计
- 实时操作日志
- 直观的状态提示
- 多选支持

## 安装和运行

### 环境要求
- Python 3.6+
- PyQt5
- CocoaPods
- Git

### 安装依赖
```bash
pip install PyQt5
```

### 运行应用
```bash
python3 main.py
```

### 构建应用
```bash
pyinstaller pod_manager.spec
```

## 使用指南

1. **添加项目**：点击"添加项目"按钮，选择包含 Podfile 的 iOS 项目目录
2. **配置 Pod**：
   - 双击 Pod 或选中后点击"配置"
   - 选择本地开发路径
3. **切换模式**：
   - 选中 Pod 后点击"开发模式"、"正常模式"、"Tag模式"或"Branch模式"
4. **创建 Tag**：
   - 选中 Pod 后点击"创建Tag"
   - 输入 Tag 名称和消息
   - 点击创建

## 文件结构

本项目采用 MVVM 架构模式：

```
iPM/
├── src/                         # 源代码目录
│   ├── models/                  # 数据模型层
│   │   ├── tag_history_manager.py    # Tag 历史管理
│   │   └── tag_validator.py          # Tag 验证器
│   │
│   ├── views/                   # 视图层
│   │   ├── main_window.py            # 主窗口
│   │   └── dialogs/                 # 对话框
│   │       ├── pod_config_dialog.py
│   │       ├── tag_dialog.py
│   │       ├── batch_tag_dialog.py
│   │       ├── batch_tag_switch_dialog.py
│   │       ├── merge_request_dialog.py
│   │       ├── tag_history_dialog.py
│   │       ├── info_dialog.py
│   │       └── personal_center_drawer.py
│   │
│   └── widgets/                # 自定义组件
│       └── loading_widget.py
│
├── tests/                      # 测试文件
│   ├── test_tag_features.py
│   └── test_tag_features_enhanced.py
│
├── resources/                  # 资源文件
│   └── icons/                  # 图标文件
│
├── main.py                     # 应用入口
├── mac_env_setup.py            # macOS 环境设置
├── pod_manager.spec            # PyInstaller 构建配置
├── AGENTS.md                   # 开发代理指南
└── README.md                   # 项目说明文档
```

## 代码规范

### 文件命名规范

本项目遵循 Python PEP 8 代码规范：

- **模块文件名**：使用小写字母 + 下划线（snake_case）
  - 示例：`pod_manager.py`, `batch_tag_dialog.py`
  - 避免：`PodManager.py`, `MyModule.py`

- **类名**：使用 PascalCase（首字母大写的驼峰命名）
  - 示例：`class PodManager`, `class BatchTagDialog`

- **函数/方法名**：使用 snake_case
  - 示例：`def load_pods()`, `def switch_to_dev_mode()`

- **常量**：使用 UPPER_CASE
  - 示例：`MAX_RETRIES`, `DEFAULT_TIMEOUT`

### 导入顺序

按照以下顺序组织导入：

1. 标准库导入（如 `os`, `re`, `json`, `subprocess`）
2. 第三方库导入（如 `PyQt5`）
3. 本地模块导入（如 `from pod_config_dialog import PodConfigDialog`）

示例：
```python
import os
import re
import json

from PyQt5.QtWidgets import QDialog, QVBoxLayout

from pod_config_dialog import PodConfigDialog
from tag_dialog import TagDialog
```

### 格式化规范

- 使用 4 空格缩进
- 最大行长度：推荐 79 字符（遵循 PEP 8）
- 避免尾随空白字符

## 配置文件

应用配置保存在 `~/.pod_manager_config.json`，包含：
- 项目列表
- Pod 本地路径配置
- 原始 Pod 引用信息

## 注意事项

- 确保已安装 CocoaPods 和 Git
- 确保本地 Pod 路径是有效的 Git 仓库
- 建议在修改 Podfile 之前备份

## 许可证

本项目仅供学习和个人使用。
