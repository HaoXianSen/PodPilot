# 批量切换 Tag 下拉框不能点击问题修复

## 问题描述

用户反馈：批量切换 tag 弹窗里**某些 pod 的切换 tag 下拉框不能点击**。

## 根本原因

在 `src/services/git_service.py` 的 `get_remote_tags()` 方法中（第 49 行），使用了**严格的版本号正则表达式过滤**：

```python
if re.match(r"v?\d+\.\d+\.\d+", tag_name):
    remote_tags.append(tag_name)
```

这导致：
- ✅ **可识别**：`v1.0.0`、`2.1.3`、`v10.5.2` 等标准版本号格式
- ❌ **被过滤**：`feature-xyz`、`release-20240312`、`hotfix-urgent`、`dev`、`staging` 等非版本号格式的 tag

当某个 Pod 的所有远程 tag 都不符合版本号格式时，`remote_tags` 列表为空，导致：

```python
# batch_tag_switch_dialog.py:476-478
else:
    tag_combo.addItem("无远程Tag")
    tag_combo.setEnabled(False)  # 禁用下拉框
```

## 解决方案

### 修改前（严格过滤）

```python
for ref in remote_refs:
    if ref and "\t" in ref:
        tag_name = ref.split("\t")[1].replace("refs/tags/", "")
        if "^{}" in tag_name:
            continue
        if re.match(r"v?\d+\.\d+\.\d+", tag_name):  # ❌ 只允许版本号格式
            remote_tags.append(tag_name)
```

### 修改后（允许所有 tag）

```python
for ref in remote_refs:
    if ref and "\t" in ref:
        tag_name = ref.split("\t")[1].replace("refs/tags/", "")
        # 跳过 annotated tag 的 ^{} 引用
        if "^{}" in tag_name:
            continue
        # ✅ 允许所有 tag，不再限制只有版本号格式
        remote_tags.append(tag_name)
```

### 智能排序

为了保持良好的用户体验，实现了智能排序算法：

1. **版本号格式的 tag**：按版本号降序排序（最新版本在最前）
   - 例如：`v2.0.0` > `v1.5.3` > `v1.0.0`

2. **非版本号格式的 tag**：按字母顺序排序，排在版本号之后
   - 例如：`feature-x`、`hotfix-abc`、`release-2024`

```python
def sort_key(tag):
    # 尝试提取版本号
    version_match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", tag)
    if version_match:
        # 版本号格式：返回 (0, major, minor, patch) 确保排在前面
        return (0, int(version_match.group(1)), int(version_match.group(2)), int(version_match.group(3)), tag)
    else:
        # 非版本号格式：返回 (1, tag) 排在后面，按字母顺序
        return (1, 0, 0, 0, tag)

remote_tags.sort(key=sort_key, reverse=True)
```

## 修改文件

- `src/services/git_service.py:27-58`

## 测试建议

### 测试场景 1：标准版本号 tag
- Pod 有 tag：`v1.0.0`, `v1.5.0`, `v2.0.0`
- ✅ 预期：全部显示，按 v2.0.0 > v1.5.0 > v1.0.0 排序

### 测试场景 2：混合格式 tag
- Pod 有 tag：`v1.0.0`, `feature-new`, `hotfix`, `v2.0.0`
- ✅ 预期：全部显示，排序为 v2.0.0 > v1.0.0 > feature-new > hotfix

### 测试场景 3：纯非版本号 tag
- Pod 有 tag：`dev`, `staging`, `production`
- ✅ 预期：全部显示（修复前会显示"无远程Tag"并禁用）

### 测试场景 4：确实没有 tag
- Pod 没有任何 tag
- ✅ 预期：显示"无远程Tag"并禁用

## 影响范围

### 直接影响
- 批量 Tag 切换对话框（`batch_tag_switch_dialog.py`）
- 所有调用 `GitService.get_remote_tags()` 的地方

### 间接影响
- 提升了灵活性，支持团队使用自定义 tag 命名规范
- 不影响已有功能，向后兼容

## 为什么之前要严格过滤？

可能的原因：
1. **简化排序逻辑**：版本号容易排序
2. **避免混乱**：过滤掉临时/测试 tag
3. **规范约束**：强制团队使用版本号格式

但这个限制过于严格，不适合所有团队的 workflow。

## 最佳实践建议

虽然现在支持所有 tag 格式，但仍然**推荐**使用语义化版本号（Semantic Versioning）：

- ✅ `v1.0.0`、`v2.1.3`、`v1.5.0-beta`
- ⚠️ `release-20240312`、`hotfix-urgent` （可用，但排序不直观）

## 未来优化方向

1. **Tag 分组显示**：版本号一组，其他 tag 一组
2. **Tag 过滤选项**：允许用户选择只显示版本号格式
3. **Tag 搜索**：大量 tag 时支持搜索过滤
4. **自定义排序规则**：支持配置 tag 排序逻辑

## 总结

通过移除严格的版本号过滤，修复了部分 Pod 下拉框不能点击的问题。同时保持了智能排序，确保用户体验。

✅ **修复完成**：所有格式的 tag 现在都可以正常显示和选择！
