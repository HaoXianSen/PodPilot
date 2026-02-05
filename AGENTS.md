# AGENTS.md - 编码代理指南

## 构建/测试/运行命令

### 运行应用
```bash
python3 main.py
```

### 构建应用 (PyInstaller)
```bash
pyinstaller pod_manager.spec
```

### 无测试套件
本项目没有自动化测试。通过以下方式验证更改：
1. 使用 `python3 main.py` 运行应用
2. 手动测试 Pod 管理功能
3. 使用 PyInstaller 构建以确保打包正常工作

## 代码风格指南

### 导入
- 标准库导入优先 (os, re, json, subprocess)
- 第三方导入其次 (PyQt5)
- 本地导入最后 (PodConfigDialog, TagDialog)
- 使用括号进行多行导入：
  ```python
  from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget,
                              QVBoxLayout, QHBoxLayout, QListWidget)
  ```

### 格式化
- 使用 4 空格缩进
- 无尾随空白字符
- 最大行长度：遵循 PEP 8（推荐 79 字符）

### 命名约定
- 文件名：snake_case（如 `pod_manager.py`, `pod_config_dialog.py`）
- 类：PascalCase（如 `PodManager`, `PodConfigDialog`, `TagDialog`）
- 方法/函数：snake_case（如 `load_pods`, `switch_to_dev_mode`）
- 变量：大多使用 snake_case，UI 组件使用混合大小写（如 `add_btn`, `pod_list`, `local_path`）
- 常量：如果添加则使用 UPPER_CASE（当前未使用）

### 文件命名规范
本项目严格遵循 Python PEP 8 规范：
- 模块文件使用小写字母和下划线：`pod_manager.py`
- 避免使用 PascalCase 作为文件名
- 示例：
  - ✅ `pod_manager.py`
  - ❌ `PodManager.py`

### 类型
- 当前未使用类型提示 - 除非添加新功能，否则保持此风格
- 保持代码简单，不使用复杂的类型注解

### 错误处理
- 对文件操作和 subprocess 调用使用 try-except 块
- 使用 `QMessageBox` 显示面向用户的错误：
  ```python
  QMessageBox.warning(self, "警告", "错误信息")
  QMessageBox.critical(self, "错误", "错误信息")
  ```
- 将错误记录到 UI log_output：`self.log_message(f"错误: {str(e)}")`
- 使用备用逻辑优雅地处理 subprocess 失败

### PyQt5/UI 模式
- 从适当的 Qt 小部件继承（QMainWindow, QDialog）
- 在 `__init__` 中使用 `initUI()` 方法进行 UI 设置
- 连接信号到槽以进行事件处理
- 使用布局管理器（QVBoxLayout, QHBoxLayout, QGridLayout）
- 使用 `item.setData(Qt.UserRole, data)` 设置项目数据
- 在适当的地方支持多选（如 `QListWidget.ExtendedSelection`）

### 文件 I/O & 配置
- 配置以 JSON 格式存储在 `~/.pod_manager_config.json`
- 对文件操作使用 `with open()` 上下文管理器
- 加载/保存配置方法应优雅地处理缺失文件
- 在会话之间保留用户状态

### Subprocess 执行
- 对同步命令使用 `subprocess.run()`
- 对异步操作使用 `QProcess`（如 `pod install`）
- 适当设置工作目录：`cwd=path`
- 处理 macOS Ruby/pod 位置的 PATH 环境变量：
  ```python
  paths = ["/usr/local/bin", "/usr/bin", "/opt/homebrew/bin",
           os.path.expanduser("~/.rbenv/shims")]
  ```

### 字符串处理
- 使用中文作为 UI 字符串（这是一个中文应用）
- 对用户输入使用 `re.escape()` 转义正则表达式
- 去除用户输入的空白字符：`text().strip()`

### 注释
- 保持注释最少
- 为中文开发者使用中文注释
- 仅对复杂方法添加文档字符串
- 对于明显代码不添加内联注释

### 项目结构

本项目采用 MVVM 架构模式进行组织：

```
iPM/
├── src/                         # 源代码目录
│   ├── models/                  # 数据模型层
│   │   ├── tag_history_manager.py    # Tag 历史管理
│   │   └── tag_validator.py          # Tag 验证器
│   │
│   ├── views/                   # 视图层
│   │   ├── main_window.py            # 主窗口 (pod_manager.py)
│   │   │
│   │   └── dialogs/                 # 对话框
│   │       ├── pod_config_dialog.py
│   │       ├── tag_dialog.py
│   │       ├── batch_tag_dialog.py
│   │       ├── batch_tag_switch_dialog.py
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
│
├── main.py                     # 应用入口
├── mac_env_setup.py            # macOS 环境设置
├── pod_manager.spec            # PyInstaller 构建配置
├── AGENTS.md                   # 开发代理指南
└── README.md                   # 项目说明文档
```

#### 目录说明
- `src/models/`：数据模型和业务逻辑层
- `src/views/`：UI 视图层，包含主窗口和所有对话框
- `src/widgets/`：可复用的自定义 UI 组件
- `tests/`：测试文件
- `resources/`：静态资源（图片、图标等）

### 添加新功能
1. 根据类型将文件放置在合适的目录下：
   - 数据模型和业务逻辑：`src/models/`
   - 主窗口：`src/views/main_window.py`
   - 新对话框：`src/views/dialogs/`
   - 可复用 UI 组件：`src/widgets/`
2. 遵循现有模式（如新对话框继承自 QDialog）
3. 使用 initUI() 进行 UI 设置
4. 如需要更新 config.json 结构
5. 使用 QMessageBox 添加错误处理
6. 将操作记录到 log_output
7. 更改后自动保存配置
8. 添加相应的 `__init__.py` 文件使目录成为 Python 包

### 测试更改
1. 使用 `python3 main.py` 运行
2. 测试所有 pod 管理操作（添加/移除、配置、模式切换）
3. 验证配置保存/加载正确
4. 测试 pod install 执行
5. 使用 PyInstaller 构建以验证打包
