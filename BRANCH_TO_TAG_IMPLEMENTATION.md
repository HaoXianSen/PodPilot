# Tag 模式批量切换 Pod 功能增强说明

## 功能概述

已成功为 `BatchTagSwitchDialog` 添加 **Branch 模式 → Tag 模式** 的批量转换功能。

## 修改内容

### 1. 新增方法

#### `_parse_branch_reference()` (batch_tag_switch_dialog.py:63-94)
- 解析 Pod 声明中的所有 `:branch =>` 引用
- 返回引用类型、引用值和所有引用的完整列表
- 支持变量引用（如 `:branch => VARIABLE`）和字面量引用（如 `:branch => 'feature'`）

#### `_convert_branch_to_tag()` (batch_tag_switch_dialog.py:96-97)
- 将 Pod 声明中的所有 `:branch =>` 替换为 `:tag =>`
- 使用正则表达式进行全局替换

#### `_detect_pod_mode()` (batch_tag_switch_dialog.py:236-257)
- 检测单个 Pod 的当前模式（Branch 或 Tag）
- 为 UI 中的"当前模式"列提供数据

### 2. UI 改进

#### 表格结构变更 (batch_tag_switch_dialog.py:333-361)
- 原有 4 列扩展为 5 列：
  1. Pod名称
  2. **当前模式** (新增)
  3. 当前状态
  4. 远程Tag
  5. 选择Tag

#### 模式显示 (batch_tag_switch_dialog.py:381-391)
- "Branch" 模式显示为**橙色** (#ff9500)
- "Tag" 模式显示为**蓝色** (#007aff)
- 只读模式，无法编辑

### 3. 工作流程增强

#### TagSwitchWorker.run() (batch_tag_switch_dialog.py:197-282)
新增分支到 Tag 的转换逻辑：

**Branch → Tag 转换规则**：
1. 检测 Pod 的当前模式
2. 如果是 Branch 模式：
   - 转换所有 `:branch =>` 为 `:tag =>`
   - 查找变量定义并更新为选中的 Tag 值
   - 更新 Pod 声明
3. 如果是 Tag 模式：
   - 更新现有的 `:tag =>` 引用为选中的 Tag 值
   - 如果是变量引用，更新变量值
   - 如果是字面量引用，更新为新的 Tag 值

## 使用示例

### 示例 1: 变量引用（符合需求）
**输入**：
```
pod 'GZUIKit_iOS', :git =>'git@gitlab.corp.youdao.com:hikari/app/ios/LSFoundationGroup_iOS/gzuikit_ios.git', :branch => GZUIKit_VERSION
GZUIKit_VERSION = 'feature/exercise_xxc'
```

**输出**：
```
pod 'GZUIKit_iOS', :git =>'git@gitlab.corp.youdao.com:hikari/app/ios/LSFoundationGroup_iOS/gzuikit_ios.git', :tag => GZUIKit_VERSION
GZUIKit_VERSION = 'v1.1.6'
```

### 示例 2: 字面量引用
**输入**：
```
pod 'MyPod', :git =>'...', :branch => 'feature/new-feature'
```

**输出**：
```
pod 'MyPod', :git =>'...', :tag => 'v1.1.6'
```

### 示例 3: 多个分支引用
**输入**：
```
pod 'MultiBranchPod', :git =>'...', :branch => BRANCH_VAR1, :branch => BRANCH_VAR2
BRANCH_VAR1 = 'feature/exercise_xxc'
BRANCH_VAR2 = 'develop'
```

**输出**：
```
pod 'MultiBranchPod', :git =>'...', :tag => BRANCH_VAR1, :tag => BRANCH_VAR2
BRANCH_VAR1 = 'v1.1.6'
BRANCH_VAR2 = 'v1.1.6'
```

## 测试验证

已创建测试脚本 `test_branch_to_tag.py` 验证转换逻辑：

```bash
python3 test_branch_to_tag.py
```

测试结果确认：
- ✅ 变量引用正确转换为 `:tag =>`
- ✅ 变量值正确更新为选中的 Tag
- ✅ 多行 Pod 声明正确处理
- ✅ 转换逻辑符合需求规范

## 兼容性

- 保持原有 Tag → Tag 更新功能不变
- 向后兼容现有 Podfile 格式
- 支持单行和多行 Pod 声明
- 支持变量和字面量两种引用方式

## 实现状态

✅ **功能完成**

- UI 改进完成
- 转换逻辑实现
- 测试验证通过
- 集成测试通过
