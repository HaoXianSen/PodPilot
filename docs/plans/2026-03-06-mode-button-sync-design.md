# Pod 模式按钮同步设计文档

## 需求概述

选中 Pod 后，模式切换按钮（开发模式、正常模式、Branch模式、Tag模式）自动同步显示当前选中 Pod 的模式状态。

## 用户交互行为

### 单选情况
- 选中单个 Pod 时，对应的模式按钮自动选中
- 例如：选中一个"开发模式"的 Pod → "开发模式"按钮高亮

### 多选情况
- **相同模式**：所有选中 Pod 都是同一模式时，选中对应模式按钮
  - 例如：选中3个"标签模式"的 Pod → "Tag模式"按钮高亮
  
- **不同模式**：选中多个不同模式的 Pod 时，不选中任何模式按钮
  - 例如：选中1个"开发模式"+ 2个"标签模式" → 所有按钮取消选中

### 按钮功能保持不变
- 无论选中状态如何，点击模式按钮仍会将所有选中的 Pod 切换到对应模式
- 现有的切换逻辑不需要修改

## 技术设计

### 方案选择
采用**基于 QButtonGroup 的状态同步方案**，理由：
1. 改动最小，风险最低
2. 充分利用现有的 `mode_btn_group` 和模式判断逻辑
3. 符合 PyQt5 的常规模式
4. 不需要引入新的架构层

### 核心实现

#### 1. 添加选择变化监听

在 `initUI()` 方法中连接信号：
```python
self.pod_list.itemSelectionChanged.connect(self.update_mode_buttons_state)
```

#### 2. 实现状态同步方法

```python
def update_mode_buttons_state(self):
    """根据选中的 Pod 更新模式按钮的选中状态"""
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
    else:
        self.to_dev_btn.setChecked(False)
        self.to_normal_btn.setChecked(False)
        self.to_branch_btn.setChecked(False)
        self.to_tag_btn.setChecked(False)
    
    self.mode_btn_group.setExclusive(True)
```

#### 3. 辅助方法：获取 Pod 模式

```python
def _get_pod_mode_from_item(self, item):
    """从 QListWidgetItem 获取 Pod 的模式"""
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

### 关键技术点

#### QButtonGroup 的 Exclusive 模式处理

由于 `QButtonGroup` 设置为 `setExclusive(True)`，直接使用 `setChecked(False)` 会失败。需要：
1. 暂时设置为 `setExclusive(False)`
2. 修改按钮状态
3. 恢复 `setExclusive(True)`

这个模式确保了在任何时候只有一个按钮处于选中状态（或者全部不选中）。

### 代码位置
- 文件：`src/views/main_window.py`
- 修改点：
  1. `initUI()` 方法：添加信号连接
  2. 新增 `update_mode_buttons_state()` 方法
  3. 新增 `_get_pod_mode_from_item()` 辅助方法

## 测试场景

1. **单选开发模式 Pod**：验证"开发模式"按钮自动选中
2. **单选标签模式 Pod**：验证"Tag模式"按钮自动选中
3. **多选相同模式 Pod**：验证对应模式按钮选中
4. **多选不同模式 Pod**：验证所有按钮取消选中
5. **取消选择**：验证所有按钮取消选中
6. **切换模式**：验证切换后按钮状态正确更新
7. **点击按钮**：验证多选时点击按钮仍能正常切换所有 Pod

## 影响范围

### 不影响现有功能
- 模式切换逻辑（`switch_to_dev_mode` 等）保持不变
- Pod 列表显示逻辑保持不变
- 其他按钮功能保持不变

### 新增功能
- Pod 选择变化时的按钮状态同步

## 实现优先级

- **高优先级**：核心同步功能
- **中优先级**：边界情况处理（如加载项目时的初始状态）
- **低优先级**：性能优化（如大量 Pod 选中时的处理）
