# 退出开发模式功能实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将"正常模式"按钮改为独立的"退出开发"按钮，实现从开发模式智能切换回上次模式的功能。

**Architecture:** 在 ConfigService 中新增 last_pod_modes 字段记录每个 Pod 切换到开发模式前的状态，修改 UI 布局将"正常模式"按钮从 Segmented Control 中移除并作为独立按钮，实现退出开发模式时优先恢复上次模式、无记录时回退到原始引用的逻辑。

**Tech Stack:** Python 3, PyQt5, JSON 配置文件

---

## Task 1: 扩展 ConfigService 支持上次模式存储

**Files:**
- Modify: `src/services/config_service.py`

**Step 1: 在 __init__ 中初始化 last_pod_modes 字段**

在 `ConfigService.__init__()` 方法中添加：

```python
def __init__(self, config_path: Union[str, None] = None):
    self.config_path = config_path or os.path.join(
        os.path.expanduser("~"), ".podpilot_config.json"
    )
    self.projects = []
    self.pods_config = {}
    self.original_pod_references = {}
    self.last_pod_modes = {}  # 新增：记录上次模式
    self.current_project = None
    self.gitlab_token = ""
    self.github_token = ""
```

**Step 2: 在 load_config 中加载 last_pod_modes**

在 `load_config()` 方法的 try 块中添加：

```python
if "last_pod_modes" in config:
    self.last_pod_modes = config["last_pod_modes"]
```

位置：在第 50 行 `if "github_token" in config:` 之后。

**Step 3: 在 save_config 中保存 last_pod_modes**

在 `save_config()` 方法中添加：

```python
config = {
    "projects": self.projects,
    "pods_config": self.pods_config,
    "original_pod_references": self.original_pod_references,
    "last_pod_modes": self.last_pod_modes,  # 新增
    "gitlab_token": self.gitlab_token,
    "github_token": self.github_token,
}
```

**Step 4: 添加 save_last_pod_mode 方法**

在文件末尾添加新方法：

```python
def save_last_pod_mode(
    self, project_path: str, pod_name: str, mode: str, mode_data: Dict[str, Any]
):
    """保存 Pod 的上次模式信息
    
    Args:
        project_path: 项目路径
        pod_name: Pod 名称
        mode: 模式类型 ('branch', 'tag', 'git')
        mode_data: 模式数据 (如 {'branch': 'feature/test'})
    """
    if project_path not in self.last_pod_modes:
        self.last_pod_modes[project_path] = {}

    self.last_pod_modes[project_path][pod_name] = {
        "mode": mode,
        "data": mode_data
    }
    self.save_config()
```

**Step 5: 添加 get_last_pod_mode 方法**

继续添加：

```python
def get_last_pod_mode(
    self, project_path: str, pod_name: str
) -> Union[Dict[str, Any], None]:
    """获取 Pod 的上次模式信息
    
    Args:
        project_path: 项目路径
        pod_name: Pod 名称
        
    Returns:
        上次模式信息，如 {'mode': 'branch', 'data': {'branch': 'feature/test'}}
        如果没有记录返回 None
    """
    if (
        project_path in self.last_pod_modes
        and pod_name in self.last_pod_modes[project_path]
    ):
        return self.last_pod_modes[project_path][pod_name]
    return None
```

**Step 6: 运行应用验证配置加载**

```bash
python3 main.py
```

操作：
1. 打开应用，选择一个项目
2. 关闭应用
3. 检查 `~/.podpilot_config.json` 中是否包含空的 `last_pod_modes` 字段

**Step 7: 提交更改**

```bash
git add src/services/config_service.py
git commit -m "ADD: ConfigService 支持上次模式存储"
```

---

## Task 2: 添加从 Podfile 提取模式信息的辅助方法

**Files:**
- Modify: `src/services/pod_service.py`

**Step 1: 添加 extract_pod_mode_info 方法**

在 `PodService` 类中添加新方法：

```python
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
        # 提取 path
        match = re.search(r":path\s*=>\s*['\"]([^'\"]+)['\"]", pod_declaration)
        if match:
            result["data"] = {"path": match.group(1)}
            
    elif ":branch" in pod_declaration:
        result["mode"] = "branch"
        # 提取 branch
        match = re.search(r":branch\s*=>\s*['\"]([^'\"]+)['\"]", pod_declaration)
        if match:
            result["data"] = {"branch": match.group(1)}
            
    elif ":tag" in pod_declaration:
        result["mode"] = "tag"
        # 提取 tag
        match = re.search(r":tag\s*=>\s*['\"]([^'\"]+)['\"]", pod_declaration)
        if match:
            result["data"] = {"tag": match.group(1)}
            
    elif ":git" in pod_declaration:
        result["mode"] = "git"
        # 提取 git URL
        match = re.search(r":git\s*=>\s*['\"]([^'\"]+)['\"]", pod_declaration)
        if match:
            result["data"] = {"git": match.group(1)}
    
    return result
```

**Step 2: 运行简单测试验证**

在 Python 交互式环境中测试：

```python
from src.services import PodService

# 测试分支模式
decl = "pod 'AFNetworking', :git => 'https://github.com/AFNetworking/AFNetworking.git', :branch => 'feature/test'"
print(PodService.extract_pod_mode_info(decl))
# 预期: {'mode': 'branch', 'data': {'branch': 'feature/test'}}

# 测试 Tag 模式
decl = "pod 'Alamofire', :tag => '5.6.2'"
print(PodService.extract_pod_mode_info(decl))
# 预期: {'mode': 'tag', 'data': {'tag': '5.6.2'}}
```

**Step 3: 提交更改**

```bash
git add src/services/pod_service.py
git commit -m "ADD: 添加从 Pod 声明提取模式信息的方法"
```

---

## Task 3: 修改 UI 布局，添加"退出开发"按钮

**Files:**
- Modify: `src/views/main_window.py`

**Step 1: 移除"正常模式"按钮**

在 `initUI()` 方法中，找到 Segmented Control 的部分（约 458-463 行），删除：

```python
# 删除以下代码块：
self.to_normal_btn = QPushButton("正常模式")
self.to_normal_btn.setCheckable(True)
self.to_normal_btn.setFixedHeight(28)
self.to_normal_btn.setStyleSheet(segment_middle_style)
self.to_normal_btn.clicked.connect(self.switch_to_normal_mode)
self.mode_btn_group.addButton(self.to_normal_btn)
```

**Step 2: 添加"退出开发"按钮**

在分隔符之后（约 484 行之后），添加：

```python
# 退出开发按钮 - 独立按钮
self.exit_dev_btn = QPushButton("退出开发")
self.exit_dev_btn.setFixedHeight(28)
self.exit_dev_btn.setFixedWidth(90)
self.exit_dev_btn.setStyleSheet("""
    QPushButton {
        background-color: #ff9500;
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    QPushButton:hover {
        background-color: #e68600;
    }
    QPushButton:disabled {
        background-color: #e0e0e0;
        color: #a0a0a0;
    }
""")
self.exit_dev_btn.clicked.connect(self.exit_dev_mode)
self.exit_dev_btn.setEnabled(False)  # 默认禁用
pod_btn_layout.addWidget(self.exit_dev_btn)
```

**Step 3: 更新 Segmented Control 样式**

将原本的 `segment_middle_style` 和 `segment_last_style` 重新分配：
- `Branch模式` 使用 `segment_middle_style`
- `Tag模式` 使用 `segment_last_style`

修改代码（约 465-477 行）：

```python
self.to_branch_btn = QPushButton("Branch模式")
self.to_branch_btn.setCheckable(True)
self.to_branch_btn.setFixedHeight(28)
self.to_branch_btn.setStyleSheet(segment_middle_style)
self.to_branch_btn.clicked.connect(self.switch_to_branch_mode)
self.mode_btn_group.addButton(self.to_branch_btn)

self.to_tag_btn = QPushButton("Tag模式")
self.to_tag_btn.setCheckable(True)
self.to_tag_btn.setFixedHeight(28)
self.to_tag_btn.setStyleSheet(segment_last_style)
self.to_tag_btn.clicked.connect(self.switch_to_tag_mode)
self.mode_btn_group.addButton(self.to_tag_btn)
```

**Step 4: 从 segment_container 中移除 to_normal_btn**

修改 segment_container 的 addWidget 调用（约 479-482 行）：

```python
segment_container.addWidget(self.to_dev_btn)
segment_container.addWidget(self.to_branch_btn)  # 改为 branch
segment_container.addWidget(self.to_tag_btn)      # 改为 tag
```

**Step 5: 运行应用验证 UI**

```bash
python3 main.py
```

验证：
1. Segmented Control 只剩 3 个按钮：开发模式、Branch模式、Tag模式
2. "退出开发"按钮显示在分隔符右侧
3. 按钮默认禁用（灰色）

**Step 6: 提交更改**

```bash
git add src/views/main_window.py
git commit -m "UI: 移除正常模式按钮，添加退出开发按钮"
```

---

## Task 4: 更新按钮状态管理逻辑

**Files:**
- Modify: `src/views/main_window.py`

**Step 1: 修改 update_mode_buttons_state 方法**

找到 `update_mode_buttons_state()` 方法（约 587 行），修改为：

```python
def update_mode_buttons_state(self):
    selected_items = self.pod_list.selectedItems()

    if not selected_items:
        self.mode_btn_group.setExclusive(False)
        self.to_dev_btn.setChecked(False)
        self.to_branch_btn.setChecked(False)
        self.to_tag_btn.setChecked(False)
        self.mode_btn_group.setExclusive(True)
        self.exit_dev_btn.setEnabled(False)  # 禁用退出开发按钮
        return

    modes = set()
    for item in selected_items:
        mode = self._get_pod_mode_from_item(item)
        modes.add(mode)

    # 更新 Segmented Control 选中状态
    self.mode_btn_group.setExclusive(False)

    if len(modes) == 1:
        mode = modes.pop()
        self.to_dev_btn.setChecked(False)
        self.to_branch_btn.setChecked(False)
        self.to_tag_btn.setChecked(False)

        if mode == "dev":
            self.to_dev_btn.setChecked(True)
        elif mode == "branch":
            self.to_branch_btn.setChecked(True)
        elif mode == "tag":
            self.to_tag_btn.setChecked(True)
        elif mode == "git":
            # Git 模式不选中任何按钮
            pass
        elif mode == "configured":
            # 已配置不选中任何按钮
            pass
        else:
            # normal 也不选中任何按钮
            pass
    else:
        self.to_dev_btn.setChecked(False)
        self.to_branch_btn.setChecked(False)
        self.to_tag_btn.setChecked(False)

    self.mode_btn_group.setExclusive(True)

    # 更新退出开发按钮状态
    # 只有所有选中的 Pod 都在开发模式时才启用
    all_in_dev_mode = all(
        self._get_pod_mode_from_item(item) == "dev"
        for item in selected_items
    )
    self.exit_dev_btn.setEnabled(all_in_dev_mode)
```

**Step 2: 测试按钮状态逻辑**

```bash
python3 main.py
```

测试场景：
1. 未选中任何 Pod → 所有按钮都不选中，"退出开发"禁用
2. 选中一个开发模式的 Pod → "开发模式"选中，"退出开发"启用
3. 选中一个分支模式的 Pod → "Branch模式"选中，"退出开发"禁用
4. 选中一个开发模式 + 一个分支模式 → 按钮都不选中，"退出开发"禁用

**Step 3: 提交更改**

```bash
git add src/views/main_window.py
git commit -m "MOD: 更新按钮状态管理，支持退出开发按钮"
```

---

## Task 5: 实现记录上次模式的逻辑

**Files:**
- Modify: `src/views/main_window.py`

**Step 1: 修改 switch_to_dev_mode 方法**

找到 `switch_to_dev_mode()` 方法（约 1085 行），在切换到开发模式前记录上次模式：

在 `for item in current_items:` 循环开始后添加：

```python
def switch_to_dev_mode(self):
    if not self.current_project:
        QMessageBox.warning(self, "警告", "请先选择项目")
        return

    current_items = self.pod_list.selectedItems()
    if not current_items:
        QMessageBox.warning(self, "警告", "请先选择要切换的Pod")
        return

    podfile_path = os.path.join(self.current_project, "Podfile")
    if not os.path.exists(podfile_path):
        QMessageBox.warning(self, "错误", "未找到Podfile")
        return

    try:
        with open(podfile_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = lines.copy()
        current_config = self.get_current_pods_config()

        for item in current_items:
            pod_name = self.get_pod_name_from_item(item)

            # 记录当前模式（新增）
            _, _, full_declaration = PodService.get_full_pod_declaration(
                lines, pod_name
            )
            if full_declaration:
                mode_info = PodService.extract_pod_mode_info(full_declaration)
                
                # 只记录非开发模式
                if mode_info["mode"] != "dev" and mode_info["mode"] != "normal":
                    self.config_service.save_last_pod_mode(
                        self.current_project,
                        pod_name,
                        mode_info["mode"],
                        mode_info["data"]
                    )

            if pod_name not in current_config:
                QMessageBox.warning(self, "警告", f"未配置 {pod_name} 的本地路径")
                continue

            local_path = current_config[pod_name]
            new_lines, modified = PodService.switch_pod_mode(
                new_lines, pod_name, "dev", local_path
            )

            if modified:
                self.log_message(f"已将 {pod_name} 切换到开发模式")

        with open(podfile_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        self.load_pods(self.current_project)

        reply = QMessageBox.question(
            self,
            "确认",
            "已切换到开发模式，是否执行 pod install?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.run_pod_install()

    except Exception as e:
        QMessageBox.critical(self, "错误", f"切换失败: {str(e)}")
```

**Step 2: 测试记录功能**

```bash
python3 main.py
```

测试步骤：
1. 选择一个项目
2. 选择一个分支模式的 Pod
3. 点击"开发模式"切换
4. 关闭应用
5. 检查 `~/.podpilot_config.json` 中的 `last_pod_modes` 字段
6. 预期看到类似：`{"/path/to/project": {"PodName": {"mode": "branch", "data": {"branch": "feature/test"}}}}`

**Step 3: 提交更改**

```bash
git add src/views/main_window.py
git commit -m "ADD: 切换到开发模式时记录上次模式"
```

---

## Task 6: 实现退出开发模式功能

**Files:**
- Modify: `src/views/main_window.py`
- Modify: `src/services/pod_service.py`

**Step 1: 在 PodService 中添加恢复模式的方法**

在 `pod_service.py` 中添加新方法：

```python
@staticmethod
def restore_pod_to_mode(
    podfile_lines: List[str],
    pod_name: str,
    mode: str,
    mode_data: Dict[str, Any],
    original_line: Union[str, None] = None,
) -> Tuple[List[str], bool]:
    """将 Pod 恢复到指定模式
    
    Args:
        podfile_lines: Podfile 行列表
        pod_name: Pod 名称
        mode: 目标模式 ('branch', 'tag', 'git')
        mode_data: 模式数据
        original_line: 原始行（备用）
        
    Returns:
        (新行列表, 是否修改成功)
    """
    if mode == "branch":
        branch_name = mode_data.get("branch", "")
        if branch_name:
            # 使用 switch_pod_mode 的 branch 模式
            return PodService.switch_pod_mode(
                podfile_lines, pod_name, "branch", branch_name
            )
            
    elif mode == "tag":
        tag_name = mode_data.get("tag", "")
        if tag_name:
            # 使用 switch_pod_mode 的 tag 模式
            return PodService.switch_pod_mode(
                podfile_lines, pod_name, "tag", tag_name
            )
            
    elif mode == "git":
        git_url = mode_data.get("git", "")
        if git_url and original_line:
            # 恢复原始 Git 引用
            new_lines = podfile_lines.copy()
            start_idx, end_idx, _ = PodService.get_full_pod_declaration(
                new_lines, pod_name
            )
            
            if start_idx is not None and end_idx is not None:
                if start_idx == end_idx:
                    new_lines[start_idx] = original_line + "\n"
                else:
                    new_lines[start_idx:end_idx] = [original_line + "\n"]
                return new_lines, True
    
    # 无法恢复，使用原始引用
    if original_line:
        new_lines = podfile_lines.copy()
        start_idx, end_idx, _ = PodService.get_full_pod_declaration(
            new_lines, pod_name
        )
        
        if start_idx is not None and end_idx is not None:
            if start_idx == end_idx:
                new_lines[start_idx] = original_line + "\n"
            else:
                new_lines[start_idx:end_idx] = [original_line + "\n"]
            return new_lines, True
    
    return podfile_lines, False
```

**Step 2: 在 main_window.py 中实现 exit_dev_mode 方法**

在 `switch_to_normal_mode()` 方法位置（约 1139 行），替换为新方法：

```python
def exit_dev_mode(self):
    """退出开发模式，恢复到上次的模式"""
    if not self.current_project:
        QMessageBox.warning(self, "警告", "请先选择项目")
        return

    current_items = self.pod_list.selectedItems()
    if not current_items:
        QMessageBox.warning(self, "警告", "请先选择要切换的Pod")
        return

    podfile_path = os.path.join(self.current_project, "Podfile")
    if not os.path.exists(podfile_path):
        QMessageBox.warning(self, "错误", "未找到Podfile")
        return

    try:
        with open(podfile_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = lines.copy()
        restored_count = 0

        for item in current_items:
            pod_name = self.get_pod_name_from_item(item)

            # 检查当前是否在开发模式
            current_mode = self._get_pod_mode_from_item(item)
            if current_mode != "dev":
                self.log_message(f"{pod_name} 不在开发模式，跳过")
                continue

            # 尝试获取上次模式
            last_mode_info = self.config_service.get_last_pod_mode(
                self.current_project, pod_name
            )

            # 获取原始引用（后备方案）
            original_reference = self.config_service.get_original_pod_reference(
                self.current_project, pod_name
            )

            if last_mode_info:
                # 使用上次模式恢复
                mode = last_mode_info["mode"]
                mode_data = last_mode_info["data"]
                original_line = original_reference["line"] if original_reference else None
                
                new_lines, modified = PodService.restore_pod_to_mode(
                    new_lines, pod_name, mode, mode_data, original_line
                )
                
                if modified:
                    self.log_message(
                        f"已将 {pod_name} 恢复到{mode}模式"
                    )
                    restored_count += 1
                else:
                    self.log_message(f"{pod_name} 恢复失败")
                    
            elif original_reference:
                # 回退到原始引用
                original_line = original_reference["line"]
                new_lines, modified = PodService.switch_pod_mode(
                    new_lines, pod_name, "normal", original_line=original_line
                )
                
                if modified:
                    self.log_message(f"已将 {pod_name} 恢复到原始引用")
                    restored_count += 1
            else:
                self.log_message(
                    f"{pod_name} 无法退出开发模式：缺少上次模式记录和原始引用"
                )

        with open(podfile_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        self.load_pods(self.current_project)

        if restored_count > 0:
            reply = QMessageBox.question(
                self,
                "确认",
                f"已退出开发模式（{restored_count}个Pod），是否执行 pod install?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.run_pod_install()

    except Exception as e:
        QMessageBox.critical(self, "错误", f"退出开发模式失败: {str(e)}")
```

**Step 3: 测试退出开发功能**

```bash
python3 main.py
```

测试场景：
1. 选择一个分支模式的 Pod，切换到开发模式
2. 点击"退出开发"按钮
3. 验证 Pod 恢复到分支模式
4. 检查 Podfile 内容

**Step 4: 提交更改**

```bash
git add src/views/main_window.py src/services/pod_service.py
git commit -m "ADD: 实现退出开发模式功能"
```

---

## Task 7: 测试完整流程

**Step 1: 测试分支 → 开发 → 退出开发**

```bash
python3 main.py
```

操作：
1. 选择一个项目
2. 选择一个分支模式的 Pod
3. 点击"开发模式"
4. 确认切换成功
5. 点击"退出开发"
6. 验证恢复到分支模式

**Step 2: 测试 Tag → 开发 → 退出开发**

操作：
1. 选择一个 Tag 模式的 Pod
2. 切换到开发模式
3. 退出开发模式
4. 验证恢复到 Tag 模式

**Step 3: 测试普通 → 开发 → 退出开发**

操作：
1. 选择一个普通引用的 Pod
2. 切换到开发模式
3. 退出开发模式
4. 验证恢复到原始引用

**Step 4: 测试按钮状态**

操作：
1. 选中一个开发模式的 Pod → "退出开发"启用
2. 选中一个非开发模式的 Pod → "退出开发"禁用
3. 选中混合模式的 Pod → "退出开发"禁用

**Step 5: 最终提交**

```bash
git add -A
git commit -m "COMPLETE: 退出开发模式功能实现完成"
```

---

## 验收标准

- [ ] "正常模式"按钮已移除
- [ ] "退出开发"按钮正确显示
- [ ] 分支模式 → 开发模式 → 退出开发模式，正确恢复
- [ ] Tag 模式 → 开发模式 → 退出开发模式，正确恢复
- [ ] Git 模式 → 开发模式 → 退出开发模式，正确恢复
- [ ] 普通引用 → 开发模式 → 退出开发模式，正确恢复
- [ ] 按钮状态逻辑正确
- [ ] 配置文件正确保存和加载
- [ ] 无 Python 语法错误
- [ ] 无明显 UI 布局问题
