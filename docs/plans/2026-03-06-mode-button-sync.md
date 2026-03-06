# Pod 模式按钮同步实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现选中 Pod 后，模式切换按钮自动同步显示当前选中 Pod 的模式状态

**Architecture:** 在主窗口中添加选择变化监听，通过解析 Pod 列表项的文本判断模式，利用 QButtonGroup 的状态管理来同步按钮选中状态

**Tech Stack:** PyQt5, QListWidget, QButtonGroup

---

## Task 1: 添加辅助方法获取 Pod 模式

**Files:**
- Modify: `src/views/main_window.py` (在 `get_pod_name_from_item` 方法后添加)

**Step 1: 添加 `_get_pod_mode_from_item` 方法**

在 `src/views/main_window.py` 的 `get_pod_name_from_item` 方法后添加以下代码：

```python
def _get_pod_mode_from_item(self, item):
    text = item.text()
    if '(开发模式)' in text:
        return 'dev'
    elif '(分支)' in text:
        return 'branch'
    elif '(标签)' in text:
        return 'tag'
    elif '(Git)' in text:
        return 'git'
    else:
        return 'normal'
```

**Step 2: 验证代码添加正确**

运行应用确保没有语法错误：
```bash
python3 -m py_compile src/views/main_window.py
```

**Step 3: 提交**

```bash
git add src/views/main_window.py
git commit -m "ADD: 添加获取 Pod 模式的辅助方法"
```

---

## Task 2: 实现模式按钮状态同步方法

**Files:**
- Modify: `src/views/main_window.py` (在 `_get_pod_mode_from_item` 方法后添加)

**Step 1: 添加 `update_mode_buttons_state` 方法**

在刚添加的 `_get_pod_mode_from_item` 方法后添加：

```python
def update_mode_buttons_state(self):
    selected_items = self.pod_list.selectedItems()
    
    if not selected_items:
        self.mode_btn_group.setExclusive(False)
        self.to_dev_btn.setChecked(False)
        self.to_normal_btn.setChecked(False)
        self.to_branch_btn.setChecked(False)
        self.to_tag_btn.setChecked(False)
        self.mode_btn_group.setExclusive(True)
        return
    
    modes = set()
    for item in selected_items:
        mode = self._get_pod_mode_from_item(item)
        modes.add(mode)
    
    self.mode_btn_group.setExclusive(False)
    
    if len(modes) == 1:
        mode = modes.pop()
        if mode == 'dev':
            self.to_dev_btn.setChecked(True)
        elif mode == 'normal':
            self.to_normal_btn.setChecked(True)
        elif mode == 'branch':
            self.to_branch_btn.setChecked(True)
        elif mode == 'tag':
            self.to_tag_btn.setChecked(True)
        elif mode == 'git':
            self.to_normal_btn.setChecked(True)
    else:
        self.to_dev_btn.setChecked(False)
        self.to_normal_btn.setChecked(False)
        self.to_branch_btn.setChecked(False)
        self.to_tag_btn.setChecked(False)
    
    self.mode_btn_group.setExclusive(True)
```

**Step 2: 验证代码添加正确**

```bash
python3 -m py_compile src/views/main_window.py
```

**Step 3: 提交**

```bash
git add src/views/main_window.py
git commit -m "ADD: 实现模式按钮状态同步方法"
```

---

## Task 3: 连接选择变化信号

**Files:**
- Modify: `src/views/main_window.py:334` (在 `pod_list` 初始化处)

**Step 1: 找到信号连接位置**

定位到 `src/views/main_window.py` 第 334 行附近的代码：
```python
self.pod_list.itemDoubleClicked.connect(self.configure_pod)
```

**Step 2: 添加信号连接**

在该行后添加：
```python
self.pod_list.itemSelectionChanged.connect(self.update_mode_buttons_state)
```

**Step 3: 验证代码正确**

```bash
python3 -m py_compile src/views/main_window.py
```

**Step 4: 提交**

```bash
git add src/views/main_window.py
git commit -m "ADD: 连接 Pod 选择变化信号到模式按钮更新"
```

---

## Task 4: 确保加载 Pod 后初始化按钮状态

**Files:**
- Modify: `src/views/main_window.py` (在 `load_pods` 方法末尾)

**Step 1: 找到 `load_pods` 方法末尾**

定位到 `load_pods` 方法的最后，应该在 `self.log_message(f"已加载 {len(pods)} 个Pod")` 这一行。

**Step 2: 添加初始化按钮状态的调用**

在该行后添加：
```python
self.update_mode_buttons_state()
```

这确保了加载新项目时，如果没有选中任何 Pod，按钮会正确重置。

**Step 3: 验证代码正确**

```bash
python3 -m py_compile src/views/main_window.py
```

**Step 4: 提交**

```bash
git add src/views/main_window.py
git commit -m "ADD: 加载 Pod 后初始化模式按钮状态"
```

---

## Task 5: 功能测试验证

**Files:**
- 无文件修改

**Step 1: 启动应用**

```bash
python3 main.py
```

**Step 2: 手动测试以下场景**

1. **单选开发模式 Pod**
   - 选择一个"开发模式"的 Pod
   - 验证："开发模式"按钮自动选中（蓝色高亮）

2. **单选标签模式 Pod**
   - 选择一个"标签"的 Pod
   - 验证："Tag模式"按钮自动选中

3. **多选相同模式 Pod**
   - 选择多个相同模式的 Pod（如3个"标签"）
   - 验证：对应的模式按钮选中

4. **多选不同模式 Pod**
   - 选择多个不同模式的 Pod（如1个"开发模式" + 2个"标签"）
   - 验证：所有模式按钮都不选中

5. **取消选择**
   - 点击列表空白处取消选择
   - 验证：所有按钮取消选中

6. **切换模式后验证**
   - 选中一个 Pod，切换到另一个模式
   - 验证：按钮状态正确更新为新模式

7. **加载新项目**
   - 切换到另一个项目
   - 验证：按钮状态重置（无选中）

**Step 3: 验证按钮功能正常**

确保点击模式按钮仍能正常切换 Pod 模式（现有功能不受影响）。

---

## Task 6: 最终提交

**Step 1: 确认所有更改已提交**

```bash
git status
```

**Step 2: 查看提交历史**

```bash
git log --oneline -5
```

---

## 实现总结

这个实现计划遵循以下原则：
- **DRY**: 复用现有的模式判断逻辑
- **YAGNI**: 只实现必要功能，不添加额外复杂性
- **单一职责**: 每个方法职责明确
- **最小改动**: 充分利用现有架构，改动最小

关键技术点：
1. 使用 `itemSelectionChanged` 信号监听选择变化
2. 通过解析文本判断 Pod 模式
3. 正确处理 `QButtonGroup` 的 `exclusive` 模式
4. 在加载新项目时重置状态
