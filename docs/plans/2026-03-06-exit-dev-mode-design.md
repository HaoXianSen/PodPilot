# 退出开发模式功能设计

## 概述

将现有的"正常模式"按钮改为独立的"退出开发"按钮，实现从开发模式智能切换回上次模式的功能。

## 背景

当前存在的问题：
1. "正常模式"命名误导，实际功能是恢复原始引用
2. 用户实际需求是从开发模式快速切换回上次模式（通常是分支模式）
3. Segmented Control 中"正常模式"的选中状态逻辑混乱

## 目标

1. 提供清晰的"退出开发"功能
2. 记录用户切换到开发模式前的状态
3. 支持智能恢复到上次模式
4. 优化 UI 布局和按钮状态逻辑

## 设计方案

### UI 布局调整

**当前布局：**
```
Segmented Control:
[开发模式] [正常模式] [Branch模式] [Tag模式]
```

**新布局：**
```
Segmented Control (4个按钮):
[开发模式] [Branch模式] [Tag模式] [Git模式]

分隔符 |

独立按钮:
[退出开发] (默认禁用)
```

### 数据存储结构

在配置文件 `~/.podpilot_config.json` 中新增 `last_pod_modes` 字段：

```json
{
  "last_pod_modes": {
    "/path/to/project": {
      "AFNetworking": {
        "mode": "branch",
        "data": {
          "branch": "feature/new-api"
        }
      },
      "Alamofire": {
        "mode": "tag",
        "data": {
          "tag": "5.6.2"
        }
      }
    }
  }
}
```

**字段说明：**
- `mode`: 上次的模式类型 (`branch` | `tag` | `git`)
- `data`: 恢复所需的数据
  - `branch`: 分支名称
  - `tag`: 标签名称
  - `git`: Git URL

### 核心功能流程

#### 1. 记录上次模式

**触发时机：** 切换到开发模式之前

**流程：**
1. 读取当前 Podfile，判断 Pod 当前模式
2. 提取模式数据（branch名/tag名/git URL）
3. 保存到 `last_pod_modes`

**示例代码逻辑：**
```python
def switch_to_dev_mode(self):
    for pod_name in selected_pods:
        # 判断当前模式
        if pod_in_branch_mode(pod_name):
            mode_data = {
                "mode": "branch",
                "data": {"branch": get_branch_name(pod_name)}
            }
        elif pod_in_tag_mode(pod_name):
            mode_data = {
                "mode": "tag", 
                "data": {"tag": get_tag_name(pod_name)}
            }
        elif pod_in_git_mode(pod_name):
            mode_data = {
                "mode": "git",
                "data": {"git": get_git_url(pod_name)}
            }
        
        # 保存上次模式
        config_service.save_last_pod_mode(project, pod_name, mode_data)
    
    # 执行切换到开发模式
    ...
```

#### 2. 退出开发模式

**触发时机：** 点击"退出开发"按钮

**流程：**
1. 检查选中的 Pod 是否都在开发模式
2. 遍历每个 Pod：
   - 优先从 `last_pod_modes` 读取上次模式
   - 如果没有记录，回退到 `original_pod_reference`
   - 如果都没有，跳过该 Pod
3. 根据上次模式执行对应的切换操作

**后备方案优先级：**
1. `last_pod_modes` 中的记录
2. `original_pod_reference` 原始引用
3. 跳过并提示用户

**示例代码逻辑：**
```python
def exit_dev_mode(self):
    for pod_name in selected_pods:
        # 尝试从上次模式恢复
        last_mode = config_service.get_last_pod_mode(project, pod_name)
        
        if last_mode:
            if last_mode["mode"] == "branch":
                switch_to_branch(pod_name, last_mode["data"]["branch"])
            elif last_mode["mode"] == "tag":
                switch_to_tag(pod_name, last_mode["data"]["tag"])
            elif last_mode["mode"] == "git":
                switch_to_git(pod_name, last_mode["data"]["git"])
        else:
            # 回退到原始引用
            original = config_service.get_original_pod_reference(project, pod_name)
            if original:
                restore_original_reference(pod_name, original)
            else:
                log_message(f"{pod_name} 无法退出开发模式：缺少上次模式记录")
```

#### 3. 按钮状态管理

**"退出开发"按钮启用条件：**
- 选中的所有 Pod 都在开发模式（`:path` 引用）
- 至少选中一个 Pod

**实现逻辑：**
```python
def update_mode_buttons_state(self):
    selected_items = self.pod_list.selectedItems()
    
    if not selected_items:
        # 禁用所有按钮
        self.exit_dev_btn.setEnabled(False)
        return
    
    # 检查是否所有选中的 Pod 都在开发模式
    all_in_dev_mode = all(
        self._get_pod_mode_from_item(item) == "dev"
        for item in selected_items
    )
    
    self.exit_dev_btn.setEnabled(all_in_dev_mode)
```

## 实现清单

### 1. ConfigService 扩展 (config_service.py)

**新增方法：**
- `save_last_pod_mode(project_path, pod_name, mode_data)` - 保存上次模式
- `get_last_pod_mode(project_path, pod_name)` - 获取上次模式
- `clear_last_pod_mode(project_path, pod_name)` - 清除记录（可选）

**修改方法：**
- `save_config()` - 添加 `last_pod_modes` 字段
- `load_config()` - 加载 `last_pod_modes` 字段

### 2. UI 布局调整 (main_window.py)

**修改 initUI() 方法：**
1. 从 Segmented Control 中移除"正常模式"按钮
2. 在分隔符右侧新增"退出开发"按钮
3. 连接按钮到 `exit_dev_mode()` 方法

### 3. 业务逻辑实现 (main_window.py)

**新增方法：**
- `exit_dev_mode()` - 退出开发模式主逻辑

**修改方法：**
- `switch_to_dev_mode()` - 添加记录上次模式的逻辑
- `update_mode_buttons_state()` - 添加"退出开发"按钮状态控制
- `_get_pod_mode_from_item()` - 确保 Git 模式识别正确

### 4. PodService 扩展 (pod_service.py)

**扩展 switch_pod_mode() 方法：**
- 支持 `branch` 模式恢复
- 支持 `tag` 模式恢复  
- 支持 `git` 模式恢复

**或新增方法：**
- `restore_pod_mode()` - 专门用于恢复模式

### 5. 模式判断辅助方法 (main_window.py)

**需要实现：**
- 从 Podfile 中提取 Pod 的当前模式
- 提取 branch/tag/git 数据的方法

## 测试场景

### 场景 1：分支 → 开发 → 退出开发
1. Pod 当前在分支模式（`:branch => 'feature/test'`）
2. 切换到开发模式（`:path => '/local/path'`）
3. 点击"退出开发"
4. **预期：** 恢复到分支模式（`:branch => 'feature/test'`）

### 场景 2：Tag → 开发 → 退出开发
1. Pod 当前在 Tag 模式（`:tag => '1.0.0'`）
2. 切换到开发模式
3. 点击"退出开发"
4. **预期：** 恢复到 Tag 模式（`:tag => '1.0.0'`）

### 场景 3：Git → 开发 → 退出开发
1. Pod 当前在 Git 模式（`:git => 'https://...'`）
2. 切换到开发模式
3. 点击"退出开发"
4. **预期：** 恢复到 Git 模式

### 场景 4：普通 → 开发 → 退出开发
1. Pod 当前是普通引用（`pod 'AFNetworking', '4.0.0'`）
2. 切换到开发模式
3. 点击"退出开发"
4. **预期：** 恢复到原始引用（`pod 'AFNetworking', '4.0.0'`）

### 场景 5：按钮状态测试
1. 选中一个开发模式的 Pod → "退出开发"启用
2. 选中多个开发模式的 Pod → "退出开发"启用
3. 选中一个开发模式 + 一个分支模式 → "退出开发"禁用
4. 未选中任何 Pod → "退出开发"禁用

## 配置迁移

现有配置文件无需特殊迁移，新增的 `last_pod_modes` 字段会自动初始化为空对象。

## 风险评估

**低风险：**
- 配置文件格式向后兼容
- 不影响现有功能
- UI 改动范围小

**需要注意：**
- 确保 Podfile 解析准确（特别是多行声明）
- 处理好 Git URL 的提取和恢复
- 错误提示要清晰友好

## 后续优化

1. 可考虑在 Pod 列表中显示"上次模式"图标提示
2. 可添加快捷键支持（如 Cmd+D 退出开发）
3. 可支持批量操作时的进度提示
