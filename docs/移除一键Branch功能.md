# 移除一键 Branch 功能

## 需求

用户反馈：去除一键 Branch 的功能，感觉比较鸡肋。

## 修改内容

### 1. 移除 UI 按钮

**位置**：`src/views/main_window.py:248-255`

**移除代码**：
```python
self.one_click_branch_btn = QPushButton("一键Branch", left_widget)
self.one_click_branch_btn.setToolTip(
    "自动筛选tag引用的Pod，批量切换到Branch模式"
)
self.one_click_branch_btn.setFixedSize(one_click_btn_w, left_btn_h)
self.one_click_branch_btn.clicked.connect(self.one_click_branch_mode)
self.one_click_branch_btn.setEnabled(False)
btn_layout.addWidget(self.one_click_branch_btn)
```

### 2. 移除按钮启用逻辑

**位置**：`src/views/main_window.py:680`

**移除代码**：
```python
self.one_click_branch_btn.setEnabled(True)
```

### 3. 移除核心功能方法

**位置**：`src/views/main_window.py:1498-1574`

**移除方法**：`one_click_branch_mode(self)` （77行代码）

功能逻辑：
- 自动筛选所有使用 `:tag` 引用的 Pod
- 检查 Pod 是否已配置本地路径
- 自动选择这些 Pod
- 询问是否进入 Branch 切换模式

### 4. 移除辅助方法

**位置**：`src/views/main_window.py:1398-1407`

**移除方法**：`_get_tag_pods(self, project_dir)` （10行代码）

功能：从 Podfile 中获取所有使用 `:tag` 引用的 Pod 列表。

## 影响分析

### 移除的功能
- ❌ "一键Branch" 按钮（UI）
- ❌ 自动筛选 tag 引用的 Pod
- ❌ 一键批量切换到 Branch 模式

### 保留的功能
- ✅ "Branch模式" 按钮（手动选择 Pod 后切换）
- ✅ 批量 Branch 切换对话框（`batch_branch_dialog.py`）
- ✅ `_get_branch_pods()` 辅助方法（被一键Tag和一键MR使用）
- ✅ 所有 Branch 相关的核心功能

### 用户影响
**旧流程**：
1. 点击"一键Branch"按钮
2. 系统自动筛选 tag 引用的 Pod
3. 显示确认对话框
4. 进入 Branch 切换对话框

**新流程**：
1. 手动选择需要切换的 Pod
2. 点击"Branch模式"按钮
3. 进入 Branch 切换对话框

**差异**：少了自动筛选步骤，用户需要手动选择 Pod。

## 代码统计

- **删除按钮定义**：8 行
- **删除按钮启用**：1 行
- **删除核心方法**：77 行
- **删除辅助方法**：10 行
- **总计删除**：96 行代码

## 为什么鸡肋？

推测原因：
1. **使用频率低**：Tag → Branch 的切换场景不如 Branch → Tag 常见
2. **操作冗余**：自动筛选 → 确认 → 手动切换，步骤较多
3. **灵活性差**：无法灵活选择要切换的 Pod
4. **功能重复**：已有"Branch模式"按钮提供相同功能

## 保留的类似功能

### 一键 Tag（保留）
- **场景**：Branch → Tag 切换（开发 → 发布）
- **频率**：高（发版时常用）
- **价值**：自动筛选节省时间

### 一键 MR（保留）
- **场景**：批量创建 Merge Request
- **频率**：高（协作开发常用）
- **价值**：自动收集信息，批量创建

### Branch 模式（保留）
- **场景**：手动选择 Pod 切换到 Branch
- **灵活性**：高（可自由选择）
- **价值**：精确控制

## 修改文件

- `src/views/main_window.py`
  - 移除按钮定义（248-255行）
  - 移除按钮启用（680行）
  - 移除核心方法（1498-1574行）
  - 移除辅助方法（1398-1407行）

## 未修改文件

- `src/views/dialogs/batch_branch_dialog.py` - Branch 切换对话框保留
- 所有其他相关功能保持不变

## 测试建议

### 功能测试
1. ✅ 确认"一键Branch"按钮已从 UI 移除
2. ✅ 确认"Branch模式"按钮仍然可用
3. ✅ 确认手动选择 Pod 后可以切换到 Branch 模式
4. ✅ 确认批量 Branch 对话框正常工作

### 回归测试
- ✅ 一键 Tag 功能正常
- ✅ 一键 MR 功能正常
- ✅ Branch 模式功能正常

## 总结

成功移除了使用频率低、操作冗余的"一键Branch"功能，精简了 UI，提升了应用的简洁性。

✅ **移除完成**：
- 删除 96 行代码
- 精简 UI 按钮
- 保留核心 Branch 切换功能
- 应用更加简洁专注

如需恢复该功能，可从 Git 历史中找回。
