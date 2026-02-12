---
description: 提交当前工程代码并且push到远程
agent: build
---

git add 当前代码到暂存区，然后git commit提交当前代码，并且push到远程

```bash
git commit -m "类型: 描述"
```

## 提交类型

- `feat`: 新功能
- `fix`: 修复 Bug
- `refactor`: 代码重构
- `test`: 测试相关
- `perf`: 性能优化

## 提交信息规范

每个提交应该：
1. 以简洁的英文开头，使用冒号分隔类型和描述
2. 遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范
3. 一句话概括本次提交的变更内容
4. 避免使用过多的描述性词语
5. 使用中文描述

## 常用命令

```bash
# 查看状态
git status

# 查看更改
git diff

# 查看提交历史
git log --oneline

# 添加文件到暂存区
git add <file>

# 创建提交
git commit -m "类型: 描述"

# 推送到远程仓库
git push origin <branch-name>

# 查看分支
git branch

# 创建并切换到新分支
git checkout -b <branch-name>

# 拉取最新代码
git pull
```
