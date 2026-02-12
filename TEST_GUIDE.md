# Tag 模式批量切换功能测试指南

## 测试环境
- Python 3.x
- PyQt5
- iPM Pod Manager 应用程序

## 测试准备

### 1. 创建测试 Podfile
```bash
cat > ~/TestPodfile.podfile << 'EOF'
platform :ios, '10.0'

pod 'GZUIKit_iOS', :git =>'git@gitlab.corp.youdao.com:hikari/app/ios/LSFoundationGroup_iOS/gzuikit_ios.git', :branch => GZUIKit_VERSION
GZUIKit_VERSION = 'feature/exercise_xxc'

pod 'MyPod', :git =>'git@gitlab.corp.youdao.com:hikari/app/ios/test.git', :tag => 'v1.0.0'
EOF
```

### 2. 运行应用程序
```bash
cd /Users/haoyh02/Desktop/iPM
python3 main.py
```

## 测试场景

### 测试场景 1: Branch → Tag 转换（变量引用）

**前置条件**：
- Podfile 中存在使用变量引用的 Branch 模式 Pod

**操作步骤**：
1. 在主界面找到 "批量切换Tag" 按钮
2. 点击打开 "批量切换Tag" 对话框
3. 查看表格中的 "当前模式" 列：
   - 应该显示 "Branch"（橙色）
4. 为该 Pod 选择一个 Tag（如 `v1.1.6`）
5. 点击 "批量切换所有Tag" 按钮
6. 确认切换操作

**预期结果**：
```
原始 Podfile:
pod 'GZUIKit_iOS', :git =>'...', :branch => GZUIKit_VERSION
GZUIKit_VERSION = 'feature/exercise_xxc'

切换后 Podfile:
pod 'GZUIKit_iOS', :git =>'...', :tag => GZUIKit_VERSION
GZUIKit_VERSION = 'v1.1.6'
```

**成功标志**：
- ✅ "当前模式" 列正确显示 "Branch" 或 "Tag"
- ✅ 切换对话框正常打开
- ✅ 表格正确显示 5 列内容
- ✅ 变量名保持不变：`GZUIKit_VERSION`
- ✅ 变量值更新为选择的 Tag：`v1.1.6`
- ✅ `:branch =>` 正确转换为 `:tag =>`
- ✅ 无错误提示

---

### 测试场景 2: Tag → Tag 更新（变量引用）

**前置条件**：
- Podfile 中已存在 Tag 模式的 Pod

**操作步骤**：
1. 打开 "批量切换Tag" 对话框
2. 查看表格中的 "当前模式" 列：
   - 应该显示 "Tag"（蓝色）
3. 为该 Pod 选择一个新的 Tag
4. 点击 "批量切换所有Tag" 按钮
5. 确认切换操作

**预期结果**：
```
原始 Podfile:
pod 'MyPod', :git =>'...', :tag => MY_TAG
MY_TAG = 'v1.0.0'

切换后 Podfile:
pod 'MyPod', :git =>'...', :tag => MY_TAG
MY_TAG = 'v1.1.6'
```

**成功标志**：
- ✅ "当前模式" 列正确显示 "Tag"
- ✅ 变量名保持不变：`MY_TAG`
- ✅ 变量值更新为选择的 Tag：`v1.1.6`
- ✅ `:tag =>` 保持不变
- ✅ 无错误提示

---

### 测试场景 3: 字面量引用转换

**前置条件**：
- Podfile 中存在使用字面量的 Branch 模式 Pod

**操作步骤**：
1. 打开 "批量切换Tag" 对话框
2. 选择模式为 "Branch" 的 Pod
3. 选择一个 Tag 值
4. 点击 "批量切换所有Tag"

**预期结果**：
```
原始 Podfile:
pod 'TestPod', :git =>'...', :branch => 'feature/new'

切换后 Podfile:
pod 'TestPod', :git =>'...', :tag => 'v1.1.6'
```

**成功标志**：
- ✅ 字面量 `feature/new` 转换为 `v1.1.6`
- ✅ 引号保持不变
- ✅ 无错误提示

---

### 测试场景 4: 多行 Pod 声明处理

**前置条件**：
- Pod 声明跨越多行

**操作步骤**：
1. 创建包含多行 Pod 声明的 Podfile
2. 打开 "批量切换Tag" 对话框
3. 选择相关 Pod
4. 点击 "批量切换所有Tag"

**预期结果**：
- ✅ 多行 Pod 声明正确转换
- ✅ 没有遗漏或错误
- ✅ 行尾符号正确

---

## UI 验证点

### 1. 对话框外观
- ✅ 窗口标题正确
- ✅ 表格显示 5 列（Pod名称、当前模式、当前状态、远程Tag、选择Tag）
- ✅ 列宽设置合理
- ✅ 表头样式一致

### 2. 表格内容
- ✅ "Pod名称" 列显示 Pod 名称
- ✅ "当前模式" 列：
  - Branch: 橙色文字
  - Tag: 蓝色文字
- ✅ "当前状态" 列显示 "准备切换"
- ✅ "远程Tag" 列显示远程 Tag 列表
- ✅ "选择Tag" 列显示选择 Tag 的下拉框

### 3. 按钮功能
- ✅ "取消" 按钮：关闭对话框
- ✅ "批量切换所有Tag" 按钮：
  - 显示确认对话框
  - 启动切换操作
  - 显示加载动画
  - 显示结果统计
  - 成功或失败提示

## 自动化测试脚本

```bash
python3 test_branch_to_tag.py
```

测试覆盖：
- ✅ 变量引用解析
- ✅ Branch → Tag 转换
- ✅ 变量值更新
- ✅ 字面量引用处理

## 常见问题排查

### 问题 1: Attribute Error
```
AttributeError: 'BatchTagSwitchDialog' object has no attribute '_detect_pod_mode'
```

**解决方案**：
方法定义顺序已修复，确保 `_detect_pod_mode` 在 `__init__` 之前定义。

### 问题 2: 切换失败
**排查步骤**：
1. 检查 Podfile 路径是否正确
2. 检查 Pod 名称是否匹配
3. 查看错误提示信息
4. 验证 Git 仓库权限

### 问题 3: UI 显示不正常
**排查步骤**：
1. 重启应用程序
2. 清理缓存：`rm ~/.pod_manager_config.json`
3. 重新打开对话框

## 测试报告模板

```
测试日期: [YYYY-MM-DD]
测试人员: [姓名]
测试环境:
  - Python 版本: [版本]
  - PyQt 版本: [版本]
  - 操作系统: [macOS/Windows/Linux]

测试场景:
  [ ] 测试场景 1: Branch → Tag 变量引用
  [ ] 测试场景 2: Tag → Tag 变量引用
  [ ] 测试场景 3: 字面量引用转换
  [ ] 测试场景 4: 多行 Pod 声明处理

UI 验证:
  [ ] 对话框正常打开
  [ ] 表格显示正确
  [ ] 模式列颜色正确
  [ ] 按钮功能正常

自动化测试:
  [ ] 脚本执行通过
  [ ] 转换结果正确

总体评价:
  [ ] 通过
  [ ] 需要修复
  [ ] 跳过

备注:
  [详细说明]
```
