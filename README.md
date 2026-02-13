# Pod Pilot

一个用于管理 iOS 项目 CocoaPods 依赖的桌面应用程序，基于 PyQt5 构建。

## 功能特性

### Pod 依赖管理
- **项目管理**：轻松添加和移除 iOS 项目
- **Pod 配置**：配置 Pod 的本地开发路径
- **模式切换**：
  - 开发模式 (`:path`) - 使用本地代码进行开发
  - 正常模式 - 恢复为远程依赖
  - Tag 模式 (`:tag`) - 指定特定版本标签
  - Branch 模式 (`:branch`) - 指定特定分支
- **批量切换分支**：
  - 一键批量切换多个 Pod 到 Branch 模式
  - 支持选择远程分支或创建新分支
  - 智能处理使用常量定义版本的 Podfile
  - 自动更新常量值并修改为 branch 引用
  - 创建新分支时可指定基于的远程分支
- **搜索筛选**：快速查找和过滤 Pod

### Git Tag 管理
- **创建 Tag**：为 Pod 仓库创建带注释的 Git Tag
- **批量创建 Tag**：一键为多个 Pod 创建相同或不同的 Tag
- **智能验证**：
  - Tag 名称格式验证
  - 检测已存在的 Tag
  - 自动检测非法字符
- **版本建议**：根据已有 Tag 智能建议下一个版本号
- **消息模板**：预定义的 Tag 消息模板
- **Tag 历史**：查看和浏览 Pod 的 Tag 历史

### Git Branch 管理
- **批量切换分支**：一次性为多个 Pod 切换到指定分支
- **创建新分支**：基于远程分支创建新分支并自动推送
- **远程分支显示**：完整显示 `origin/xxx` 格式的远程分支列表
- **智能 Podfile 处理**：
  - 自动识别使用常量定义版本的 Podfile（如 `UI_OC_VERSION = 'v1.0.0'`）
  - 更新常量值为目标分支名
  - 将 `:tag => CONSTANT` 自动改为 `:branch => CONSTANT`
  - 保留原有的 git URL 和其他配置

### Merge Request 管理
- **一键 MR**：批量创建主工程和私有库的 Merge Request
  - 自动筛选 branch 引用的 Pod
  - 先创建私有库 MR，再创建主工程 MR
  - 主工程 MR 描述中自动关联所有私有库 MR 链接
  - **智能 MR 更新**：如果主工程已存在相同源分支到目标分支的 MR，自动更新 MR 描述而非创建新 MR
  - **增量关联**：后续提交时，只追加或更新本次成功的私有库 MR 链接，不重复处理已失败的
- **查看我的 MR**：在个人中心查看用户在 GitLab 上创建的所有待合并 MR
- **查看工程 MR**：查看当前工程及其关联私有库的待合并 MR
  - 左侧项目列表，右侧 MR 详情
  - 点击 MR 可直接在浏览器中打开

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

#### 使用 PyInstaller（推荐用于快速测试）
```bash
pyinstaller pod_manager.spec
```

#### 使用 py2app（推荐用于正式发布）
```bash
# 开发模式（快速测试）
python3 setup.py py2app -A

# 生产模式（完整打包）
python3 setup.py py2app
```

打包后的应用位于 `dist/Pod Pilot.app`

## 使用指南

1. **添加项目**：点击"添加项目"按钮，选择包含 Podfile 的 iOS 项目目录
2. **配置 Pod**：
   - 双击 Pod 或选中后点击"配置"
   - 选择本地开发路径
3. **切换模式**：
   - 选中 Pod 后点击"开发模式"、"正常模式"、"Tag模式"或"Branch模式"
4. **批量切换分支**：
   - 选中多个 Pod 后点击"批量切换到 Branch 模式"
   - 为每个 Pod 选择目标分支（从远程分支列表选择）
   - 可选：勾选"创建新分支"并指定基于哪个远程分支创建
   - 点击"批量切换所有"执行切换
5. **创建 Tag**：
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
│   │       ├── batch_branch_dialog.py        # 批量切换分支对话框
│   │       ├── branch_create_dialog.py       # 创建分支对话框
│   │       ├── merge_request_dialog.py
│   │       ├── my_mr_dialog.py
│   │       ├── project_mr_dialog.py
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
│       ├── app_icon.png         # 应用图标（1024x1024）
│       ├── app_icon.icns        # macOS 应用图标
│       ├── app_icon_*.png       # 多尺寸图标（16-512px）
│       ├── check_box.svg        # 选中状态图标
│       └── uncheck_box.svg      # 未选中状态图标
│
├── main.py                     # 应用入口
├── setup.py                    # py2app 打包配置
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

## 特色功能说明

### 批量切换分支模式

批量切换分支功能支持智能处理使用常量定义版本的 Podfile：

**示例场景：**

原 Podfile：
```ruby
UI_OC_VERSION = 'v1.0.0'
pod 'JPKUI-iOS/All', :git => 'git@gitlab.com:xxx.git', :tag => UI_OC_VERSION
```

切换到分支 `feature/new-ui` 后：
```ruby
UI_OC_VERSION = 'feature/new-ui'
pod 'JPKUI-iOS/All', :git => 'git@gitlab.com:xxx.git', :branch => UI_OC_VERSION
```

**功能特点：**
- 自动识别常量引用（支持包含小写字母的常量名，如 `GZUIKit_VERSION`）
- 同时更新常量值和引用类型（`:tag` → `:branch`）
- 保留原有的 git URL 和其他配置
- 远程分支显示 `origin/xxx` 格式，写入 Podfile 时自动去掉 `origin/` 前缀
- 支持创建新分支并自动推送到远程

## Pod 列表排序规则

Pod 列表按照以下优先级排序，优先级数字越小越靠前：

| 优先级 | 状态 | 说明 |
|--------|------|------|
| 1 | 开发模式 | 使用 `:path` 引用的本地依赖 |
| 2 | 分支模式 | 使用 `:branch` 引用的依赖 |
| 3 | 已配置 | 在配置中有本地路径的依赖 |
| 4 | 标签模式 | 使用 `:tag` 引用的依赖 |
| 5 | Git 模式 | 使用 `:git` 引用的依赖 |
| 6 | 普通 | 普通依赖（无特殊引用） |

同一优先级内，按 Podfile 中的原始顺序排序。

## 注意事项

- 确保已安装 CocoaPods 和 Git
- 确保本地 Pod 路径是有效的 Git 仓库
- 建议在修改 Podfile 之前备份

## 许可证

本项目仅供学习和个人使用。
