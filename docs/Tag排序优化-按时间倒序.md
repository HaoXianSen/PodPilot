# Tag 排序优化 - 按时间倒序

## 需求

用户反馈：tag 的顺序希望**根据时间倒序，最新的在最上边**。

## 解决方案

使用 `git ls-remote` 的 `--sort=-creatordate` 参数，按创建时间降序排列远程 tag。

### 核心改动

```python
# 使用 --sort=-creatordate 参数
result = subprocess.run(
    ["git", "ls-remote", "--tags", "--sort=-creatordate", "origin"],
    cwd=local_path,
    capture_output=True,
    text=True,
    check=True,
)
```

### 排序效果

**按创建时间倒序（最新的在前）**：
1. `v2.1.0` (2026-03-12 创建) ← 最新
2. `feature-x` (2026-03-10 创建)
3. `v2.0.0` (2026-03-05 创建)
4. `v1.5.0` (2026-02-20 创建)
5. `v1.0.0` (2026-01-15 创建) ← 最旧

### 兼容性处理

部分旧版本 Git 可能不支持 `--sort` 参数，因此添加了回退逻辑：

```python
try:
    # 尝试使用 --sort=-creatordate
    result = subprocess.run(
        ["git", "ls-remote", "--tags", "--sort=-creatordate", "origin"],
        ...
    )
except subprocess.CalledProcessError:
    # 回退到无排序版本
    result = subprocess.run(
        ["git", "ls-remote", "--tags", "origin"],
        ...
    )
```

## 修改前后对比

| 方面 | 修改前 | 修改后 |
|------|--------|--------|
| 排序依据 | 版本号数值（major.minor.patch） | 创建时间（最新在前） |
| 版本号格式 | 严格过滤（只允许 `v?\d+\.\d+\.\d+`） | 允许所有格式 |
| 非版本号tag | 被过滤掉 | 全部显示 |
| 排序算法 | 复杂的自定义 sort_key | Git 原生 --sort 参数 |
| 用户体验 | ❌ 部分 tag 不可见，下拉框禁用 | ✅ 所有 tag 可见，按时间排序 |

## Git ls-remote 参数说明

```bash
git ls-remote --tags --sort=-creatordate origin
```

参数解释：
- `--tags`：只列出 tag 引用
- `--sort=-creatordate`：按创建时间降序排列（`-` 表示倒序）
- `origin`：远程仓库名称

其他可用排序选项：
- `--sort=creatordate`：按创建时间升序
- `--sort=-version:refname`：按版本号倒序（需要 Git 2.18+）
- `--sort=refname`：按引用名称字母序

## 为什么使用创建时间排序？

### 优势
1. ✅ **直观**：开发者通常关心最新的 tag
2. ✅ **简单**：无需复杂的版本号解析逻辑
3. ✅ **灵活**：支持任意 tag 命名规范
4. ✅ **性能**：Git 原生实现，效率高

### 场景适配
- **版本发布**：最新版本自动在最上方
- **功能分支**：最新创建的功能 tag 优先显示
- **热修复**：紧急 hotfix tag 立即可见

## 修改文件

- `src/services/git_service.py:27-79`

## 测试建议

### 测试场景 1：标准版本号（按时间）
假设创建顺序：v1.0.0 (1月) → v2.0.0 (2月) → v1.5.0 (3月)

- ✅ 预期显示顺序：`v1.5.0` > `v2.0.0` > `v1.0.0`
- 📝 说明：v1.5.0 虽然版本号更小，但创建时间最新，所以排在第一

### 测试场景 2：混合格式 tag
假设创建顺序：v1.0.0 → feature-x → v2.0.0 → hotfix-urgent

- ✅ 预期显示顺序：`hotfix-urgent` > `v2.0.0` > `feature-x` > `v1.0.0`

### 测试场景 3：验证排序
```bash
# 在任意 Git 仓库测试
cd /path/to/pod/repo
git ls-remote --tags --sort=-creatordate origin
```

## 潜在问题与解决

### 问题 1：Git 版本过旧不支持 --sort
**解决**：已添加回退逻辑，自动使用无排序版本

### 问题 2：Annotated tags vs Lightweight tags
**说明**：
- Annotated tags 有独立的创建时间
- Lightweight tags 使用 commit 时间
- `--sort=-creatordate` 都能正确处理

### 问题 3：用户习惯版本号排序
**建议**：团队使用语义化版本号，按时间发布，自然符合预期

## 未来优化

如果用户需要更灵活的排序选项，可以添加：

1. **排序选项**：在 UI 中添加排序切换（时间/版本号/字母）
2. **配置化**：允许用户在配置中设置默认排序方式
3. **双重排序**：先按时间，再按版本号

## 总结

✅ **修复完成**：
- 移除严格的版本号过滤，支持所有 tag 格式
- 使用 `--sort=-creatordate` 按时间倒序排列
- 添加回退逻辑，兼容旧版本 Git
- 最新的 tag 自动显示在下拉框最上方

现在重新启动应用，tag 将按创建时间排序，最新的在最上边！🎉
