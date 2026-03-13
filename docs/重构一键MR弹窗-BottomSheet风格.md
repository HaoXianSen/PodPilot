# 重构一键MR弹窗 - Bottom Sheet 风格

## 概述

将一键 MR 弹窗重构为与批量 Branch 弹窗相同的现代化 Bottom Sheet 风格，提升用户体验的一致性。

---

## 主要改进

### 1. 从 QDialog 迁移到 BottomSheetDialog ✅

**旧版**：
```python
class MergeRequestDialog(QDialog):
    def __init__(self, pods_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle("创建 Merge Request")
        self.setMinimumSize(900, 600)
```

**新版**：
```python
class MergeRequestDialog(BottomSheetDialog):
    def __init__(self, pods_info, parent=None):
        super().__init__(parent, title="创建 Merge Request", max_height_ratio=0.85)
```

**效果**：
- ✅ 从底部滑入动画
- ✅ 半透明遮罩背景
- ✅ 可拖拽关闭
- ✅ 圆角 Glassmorphism 风格

---

### 2. 从表格布局改为卡片式布局 ✅

**旧版**：使用 QTableWidget 展示所有项目信息
- 行列结构
- 密集信息展示
- 传统表格风格

**新版**：使用独立卡片展示每个项目
- 每个项目一张卡片
- 信息分层清晰
- 现代化视觉设计

### 卡片结构

```
┌────────────────────────────────────┐
│ 项目名称  [主工程] [current-branch] │
│ git@gitlab.com:xxx/xxx.git         │
├────────────────────────────────────┤
│ 源分支:   [branch-dropdown ▾]      │
│ 目标分支: [master-dropdown ▾]      │
│ MR标题:   [Merge xxx into...]      │
│ MR描述:   [简要描述...]            │
└────────────────────────────────────┘
```

---

### 3. 使用 CustomDropdown 组件 ✅

**旧版**：QComboBox
```python
source_combo = QComboBox()
source_combo.setMinimumHeight(32)
```

**新版**：CustomDropdown
```python
source_combo = CustomDropdown()
source_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
```

**优势**：
- ✅ 更美观的下拉样式
- ✅ 与批量 Branch/Tag 对话框风格统一
- ✅ 圆角、半透明、平滑动画

---

### 4. 分支处理逻辑优化 ✅

#### 源分支逻辑

**优先级**：
1. 主工程：使用当前分支
2. Pod库：优先使用 Podfile 中的分支，否则使用当前分支

**列表内容**：
- 默认源分支（第一位）
- 当前分支（如果不同于默认）
- 其他远程分支

```python
# 确定默认源分支
if is_main_project:
    default_source = current_branch
else:
    default_source = podfile_branch if podfile_branch else current_branch

# 构建分支列表
source_branches = []
if default_source:
    source_branches.append(default_source)
if current_branch and current_branch != default_source:
    source_branches.append(current_branch)
for branch in remote_branches:
    if branch != default_source and branch != current_branch:
        source_branches.append(branch)

source_combo.addItems(source_branches)
```

#### 目标分支逻辑

**优先级**：
1. 常用分支：master → main → develop → release
2. 其他远程分支

**自动去除 `origin/` 前缀**：
```python
common_targets = ["master", "main", "develop", "release"]
target_branches = []

# 添加常用分支
for target in common_targets:
    if target in remote_branches or f"origin/{target}" in remote_branches:
        target_branches.append(target)

# 添加其他分支（去重）
for branch in remote_branches:
    branch_name = branch.replace("origin/", "")
    if branch_name not in target_branches:
        target_branches.append(branch_name)

target_combo.addItems(target_branches)
```

---

### 5. Token 配置区域优化 ✅

**旧版**：QGroupBox 样式
```python
token_group = QGroupBox("访问令牌配置")
token_layout = QGridLayout()
```

**新版**：独立 QFrame 卡片
```python
token_section = QFrame()
token_section.setObjectName("tokenSection")
token_section.setStyleSheet("""
    QFrame#tokenSection {
        background-color: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 16px;
    }
""")
```

**优势**：
- ✅ 与卡片风格一致
- ✅ 更加扁平现代
- ✅ 统一的 Glassmorphism 设计

---

## 修复的问题

### 1. CustomDropdown 方法兼容性 ✅

**问题**：CustomDropdown 没有 `count()` 和 `setCurrentIndex()` 方法

**解决**：
- ❌ `source_combo.count()` → ✅ `len(source_branches)`
- ❌ `source_combo.setCurrentIndex(0)` → ✅ `source_combo.setCurrentText(source_branches[0])`

### 2. 源分支列表为空 ✅

**问题**：直接使用 `remote_branches` 导致可能包含不需要的分支

**解决**：按优先级构建 `source_branches` 列表，先添加默认源分支和当前分支

### 3. 目标分支显示 `origin/` 前缀 ✅

**问题**：目标分支直接显示远程分支名称（如 `origin/master`）

**解决**：自动去除 `origin/` 前缀，只显示分支名称（如 `master`）

---

## 视觉对比

### 旧版（表格式）

```
┌────────────────────────────────────────────┐
│ 访问令牌配置                                │
│ ┌────────────────────────────────────────┐ │
│ │ GitLab Token: [____________]           │ │
│ │ GitHub Token: [____________]           │ │
│ └────────────────────────────────────────┘ │
│                                            │
│ Merge Request 信息                         │
│ ┌────────────────────────────────────────┐ │
│ │ 项目名称│源分支│目标分支│标题│描述     │ │
│ ├────────┼──────┼────────┼────┼────────┤ │
│ │ Pod1   │ ▾    │ ▾      │    │        │ │
│ │ Pod2   │ ▾    │ ▾      │    │        │ │
│ └────────────────────────────────────────┘ │
│                                            │
│                     [取消] [提交 MR]       │
└────────────────────────────────────────────┘
```

### 新版（卡片式 Bottom Sheet）

```
        [从底部滑入动画]
        ↓
┌────────────────────────────────────────────┐
│ ━━━  (拖拽手柄)                            │
│                                            │
│ 创建 Merge Request                         │
│                                            │
│ ┌────────────────────────────────────────┐ │
│ │ 访问令牌配置                            │ │
│ │ GitLab Token: [____________]           │ │
│ │ GitHub Token: [____________]           │ │
│ └────────────────────────────────────────┘ │
│                                            │
│ 为每个项目配置 MR 信息                     │
│                                            │
│ ┌────────────────────────────────────────┐ │ ↕
│ │ PodName  [主工程] [current-branch]     │ │ 滚
│ │ git@gitlab.com:xxx/xxx.git             │ │ 动
│ │ 源分支:   [branch-dropdown ▾]          │ │
│ │ 目标分支: [master-dropdown ▾]          │ │
│ │ MR标题:   [Merge xxx into...]          │ │
│ │ MR描述:   [简要描述...]                │ │
│ └────────────────────────────────────────┘ │
│                                            │
│ ┌────────────────────────────────────────┐ │
│ │ PodName2 [feature-branch]              │ │
│ │ ...                                    │ │
│ └────────────────────────────────────────┘ │
│                                            │
│                     [取消] [提交 MR]       │
└────────────────────────────────────────────┘
```

---

## 技术细节

### 继承结构

```python
BottomSheetDialog
├── content_layout (QVBoxLayout)
│   ├── Token 配置区域
│   ├── 描述标签
│   └── 滚动卡片区域
│
├── confirm_btn (提交 MR)
└── cancel_btn (取消)
```

### 卡片组件

每张卡片包含：
1. **Header**：项目名称 + 标签（主工程/当前分支）
2. **Git URL**：显示仓库地址
3. **源分支下拉**：CustomDropdown
4. **目标分支下拉**：CustomDropdown
5. **MR 标题输入**：QLineEdit
6. **MR 描述输入**：QLineEdit

### 数据流

```
用户选择 → on_xxx_changed() → self.mr_configs[pod_name] → submit_mrs() → MRRequestWorker
```

---

## 兼容性保持

### API 兼容

```python
# 旧版调用方式（完全兼容）
dialog = MergeRequestDialog(
    pods_info=pods_info,
    parent=self,
    config=config,
    main_project_info=main_project_info
)
dialog.exec_()
```

### 功能保持

- ✅ GitLab/GitHub MR 创建
- ✅ 主工程 MR 更新（追加私有库链接）
- ✅ Token 配置保存
- ✅ 异步提交（MRRequestWorker）
- ✅ 线程安全清理

---

## 修复的问题

### 问题1：源分支列表为空 ✅

**原因**：使用 `remote_branches` 直接填充，但逻辑不完整

**修复**：
```python
# 构建完整的源分支列表
source_branches = []
if default_source:
    source_branches.append(default_source)
if current_branch and current_branch != default_source:
    source_branches.append(current_branch)
for branch in remote_branches:
    if branch not in [default_source, current_branch]:
        source_branches.append(branch)

source_combo.addItems(source_branches)
```

### 问题2：目标分支显示不对 ✅

**原因**：没有去除 `origin/` 前缀，且没有优先显示常用分支

**修复**：
```python
# 优先添加常用分支，去除 origin/ 前缀
common_targets = ["master", "main", "develop", "release"]
target_branches = []

for target in common_targets:
    if target in remote_branches or f"origin/{target}" in remote_branches:
        target_branches.append(target)  # 不带 origin/

for branch in remote_branches:
    branch_name = branch.replace("origin/", "")
    if branch_name not in target_branches:
        target_branches.append(branch_name)

target_combo.addItems(target_branches)
```

### 问题3：CustomDropdown 方法不兼容 ✅

**原因**：CustomDropdown 没有 `count()` 和 `setCurrentIndex()` 方法

**修复**：
- ❌ `dropdown.count()` → ✅ `len(branches_list)`
- ❌ `dropdown.setCurrentIndex(0)` → ✅ `dropdown.setCurrentText(branches_list[0])`

---

## 文件变化

### 修改的文件
- `src/views/dialogs/merge_request_dialog.py` - 完全重构（1174行）

### 备份文件
- `src/views/dialogs/merge_request_dialog_old.py` - 旧版备份（1556行）

### 代码减少
- **旧版**：1556 行
- **新版**：1174 行
- **减少**：382 行（24.5%）

**原因**：
- 移除了复杂的表格布局代码
- 使用 BottomSheetDialog 基类简化了 UI 初始化
- 卡片式布局代码更简洁

---

## 核心改动

### 1. 继承 BottomSheetDialog
```python
super().__init__(parent, title="创建 Merge Request", max_height_ratio=0.85)

self._build_content()
self._apply_content_styles()
self.load_tokens_from_config()
self.load_pods_info()
self.setup_sheet_ui()
```

### 2. 构建内容区域
```python
def _build_content(self):
    # Token 配置区域
    token_section = QFrame()
    # ... 配置 GitLab/GitHub Token
    
    # 滚动卡片区域
    self.scroll_area = QScrollArea()
    self.cards_container = QWidget()
    # ... 配置滚动区域
    
    # 修改按钮
    self.confirm_btn.setText("提交 MR")
    self.confirm_btn.clicked.connect(self.submit_mrs)
```

### 3. 创建卡片
```python
def _create_pod_card(self, pod_name, info):
    card = QFrame()
    # ... 卡片样式
    
    # Header: 名称 + 标签
    # Git URL
    # 源分支下拉
    # 目标分支下拉
    # MR 标题输入
    # MR 描述输入
    
    # 保存引用
    self.pod_cards.append({...})
    
    # 初始化配置
    self.mr_configs[pod_name] = {...}
    
    return card
```

### 4. 加载卡片
```python
def load_pods_info(self):
    # 排序：主工程优先
    sorted_items = sorted(
        self.pods_info.items(),
        key=lambda x: (0 if x[1].get("is_main_project", False) else 1, x[0]),
    )
    
    for pod_name, info in sorted_items:
        card = self._create_pod_card(pod_name, info)
        self.cards_layout.addWidget(card)
```

---

## 视觉设计

### Bottom Sheet 动画
- **出现**：从底部向上滑入（300ms，EaseOutCubic）
- **消失**：向下滑出消失（250ms，EaseInCubic）
- **拖拽**：支持拖拽手柄关闭

### 卡片样式
- **背景**：`rgba(255, 255, 255, 0.08)`
- **边框**：`1px solid rgba(255, 255, 255, 0.12)`
- **圆角**：12px
- **间距**：卡片之间 12px

### 标签设计
- **主工程**：黄色标签 `#fbbf24`
- **当前分支**：蓝紫色标签 `#a5b4fc`
- **字体**：11px，圆角 4px

### CustomDropdown
- **背景**：半透明
- **边框**：微光边框
- **展开**：向下滑动动画
- **选中**：蓝色高亮

---

## 用户体验提升

| 方面 | 旧版 | 新版 |
|------|------|------|
| 出现方式 | 直接弹出 | 从底部滑入 ✨ |
| 消失方式 | 直接关闭 | 向下滑出 ✨ |
| 信息展示 | 表格密集 | 卡片清晰 ✨ |
| 下拉框 | QComboBox | CustomDropdown ✨ |
| 视觉风格 | 传统对话框 | Glassmorphism ✨ |
| 交互反馈 | 基础 | 平滑动画 ✨ |

---

## 功能验证清单

- [x] Token 配置区域显示正常
- [x] 卡片按主工程优先排序
- [x] 源分支列表包含：默认源分支、当前分支、其他分支
- [x] 目标分支列表优先显示 master/main，去除 origin/ 前缀
- [x] MR 标题自动生成（基于默认源分支）
- [x] 所有输入变化正确更新 mr_configs
- [x] 提交 MR 功能正常
- [x] 线程安全清理
- [x] Bottom Sheet 动画流畅
- [x] 卡片滚动正常

---

## 测试建议

### 场景1：私有库 Pod
- 源分支：应优先显示 Podfile 中的分支
- 目标分支：应优先显示 master/main
- 标题：应为 "Merge {podfile_branch} into master"

### 场景2：主工程
- 源分支：应优先显示当前分支
- 目标分支：应优先显示 master/main
- 标签：应显示"主工程"黄色标签

### 场景3：错误处理
- 无 Git URL 的 Pod：显示错误信息，不显示下拉框
- 无远程分支：源分支禁用，显示当前分支

---

## 未来优化方向

1. **MR 模板**：支持保存和加载 MR 描述模板
2. **批量编辑**：支持一键设置所有项目的目标分支
3. **历史记录**：记录最近使用的分支和标题
4. **实时预览**：显示 MR 描述的 Markdown 预览

---

## 总结

通过重构为 Bottom Sheet 风格 + 卡片式布局：

✅ **视觉统一**：与批量 Branch/Tag 对话框风格一致  
✅ **交互优化**：平滑动画，现代化体验  
✅ **代码简化**：减少 382 行代码（24.5%）  
✅ **功能完整**：保持所有原有功能  
✅ **问题修复**：源分支、目标分支显示正确  

重构完成！🎊
