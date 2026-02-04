# Tag功能完善文档和规划

## 当前功能现状分析

### 1. 创建Tag功能 (`create_tag_for_pod` / `execute_create_tag`)

**现有功能：**
- ✅ 检查Pod是否已配置本地路径
- ✅ 使用`TagDialog`输入tag名称和消息
- ✅ 检查git仓库状态（未提交更改）
- ✅ 创建带注释的git tag（annotated tag）
- ✅ 推送tag到远程仓库

**存在的问题：**
- ❌ Tag名称没有格式验证
- ❌ 没有检查tag是否已存在
- ❌ 没有查看已有tag列表的功能
- ❌ 无法选择已有tag进行重新创建
- ❌ Tag消息可以为空但无默认值
- ❌ 没有tag版本管理建议
- ❌ 错误处理不够详细

### 2. 切换到Tag引用功能 (`switch_to_tag_mode`)

**现有功能：**
- ✅ 使用`QInputDialog`获取tag名称
- ✅ 修改Podfile为tag引用模式
- ✅ 自动执行pod install

**存在的问题：**
- ❌ 没有可用tag列表供选择
- ❌ 无法自动获取远程tag列表
- ❌ 没有tag版本提示或历史记录
- ❌ 输入的tag名称没有验证
- ❌ 无法预览tag对应的commit信息
- ❌ 多个pod使用不同tag时的管理不便

### 3. Tag恢复功能 (`switch_to_normal_mode`)

**现有功能：**
- ✅ 支持从tag模式恢复到原始引用

**存在的问题：**
- ⚠️ 依赖original_pod_references，如果丢失则无法准确恢复

---

## 功能完善规划

### 阶段一：基础功能增强（优先级：高）

#### 1.1 Tag对话框改进

**目标：** 提供更好的tag创建体验

**具体改进：**
1. **添加tag名称格式验证**
   - 遵循git tag命名规范
   - 不允许特殊字符（空格、~^:等）
   - 建议使用语义化版本号（如v1.0.0）

2. **添加已有tag列表查看**
   - 获取本地已有tag列表
   - 按时间倒序排列
   - 显示tag名称和创建时间

3. **Tag名称自动补全**
   - 根据历史tag建议版本号
   - 支持常见tag格式（v1.0.0, 1.0.0, release-1.0等）

4. **Tag消息模板**
   - 提供常用tag消息模板
   - 支持保存自定义模板
   - 默认使用"Release version X.Y.Z"

5. **Tag存在性检查**
   - 创建前检查tag是否已存在
   - 如果存在，提示是否删除后重新创建

#### 1.2 Tag选择对话框新增

**目标：** 改进tag引用时的选择体验

**新功能：**
1. **Tag选择对话框** `TagSelectDialog`
   - 显示本地tag列表
   - 显示远程tag列表（可刷新）
   - 显示tag对应的commit信息
   - 支持搜索和过滤tag

2. **Tag信息预览**
   - 显示tag的完整message
   - 显示创建时间
   - 显示commit hash
   - 显示创建者信息

3. **Tag推荐功能**
   - 根据pod名称推荐相关tag
   - 显示最新的稳定版本tag
   - 高亮推荐tag

#### 1.3 错误处理增强

**目标：** 提供更详细的错误信息和恢复建议

**改进内容：**
1. **Git命令错误处理**
   - 捕获并解析git命令错误
   - 提供具体的错误原因
   - 提供解决方案建议

2. **网络错误处理**
   - 检测网络连接问题
   - 提供重试机制
   - 显示推送进度

3. **权限错误处理**
   - 检测git仓库权限
   - 提供权限设置指导

---

### 阶段二：高级功能（优先级：中）

#### 2.1 Tag版本管理

**目标：** 提供专业的tag版本管理

**新功能：**
1. **版本号自动递增**
   - 根据当前最新tag自动建议下一个版本号
   - 支持主版本、次版本、补丁版本递增
   - 支持预发布版本（alpha、beta、rc）

2. **Tag分支管理**
   - 建议基于当前分支创建tag
   - 显示tag所属分支
   - 支持在不同分支切换tag

3. **Tag发布流程**
   - 支持创建release notes
   - 集成changelog功能
   - 支持批量发布多个pod

#### 2.2 Tag引用管理

**目标：** 更好地管理多个pod的tag引用

**新功能：**
1. **批量Tag引用**
   - 支持为多个pod选择同一个tag
   - 支持为多个pod选择不同tag
   - 提供tag版本一致性检查

2. **Tag依赖关系**
   - 检查pod之间的tag依赖
   - 提示不兼容的tag版本
   - 建议兼容的tag组合

3. **Tag历史记录**
   - 记录每个pod的tag切换历史
   - 支持回滚到之前的tag
   - 显示tag使用统计

---

### 阶段三：用户体验优化（优先级：低）

#### 3.1 UI/UX改进

**目标：** 提供更好的用户交互体验

**改进内容：**
1. **Tag可视化**
   - 在pod列表中显示当前使用的tag
   - 用不同颜色区分tag类型（stable、beta、rc）
   - 显示tag发布时间

2. **快捷操作**
   - 右键菜单快速创建tag
   - 支持拖拽tag到pod
   - 快捷键支持

3. **搜索和过滤**
   - 在tag列表中搜索
   - 按时间、版本过滤tag
   - 收藏常用tag

#### 3.2 集成和自动化

**目标：** 与其他工具集成，提供自动化支持

**新功能：**
1. **CI/CD集成**
   - 支持自动创建tag
   - 集成GitHub Actions、GitLab CI等
   - 支持tag发布后自动触发构建

2. **通知和提醒**
   - 新tag发布通知
   - Tag过期提醒
   - 定期检查tag更新

3. **配置文件支持**
   - 支持从配置文件导入tag规则
   - 支持导出tag历史
   - 支持团队协作配置

---

## 技术实现方案

### 1. 新增类设计

```python
class TagSelectDialog(QDialog):
    """Tag选择对话框"""
    def __init__(self, pod_name, local_path, parent=None):
        # 显示tag列表
        # 支持搜索和过滤
        # 显示tag详情
        pass

class TagValidator:
    """Tag验证器"""
    @staticmethod
    def validate_tag_name(tag_name):
        # 验证tag名称格式
        pass

    @staticmethod
    def suggest_next_version(current_version, increment_type):
        # 建议下一个版本号
        pass

class TagManager:
    """Tag管理器"""
    def __init__(self, local_path):
        # 管理tag相关操作
        pass

    def get_local_tags(self):
        # 获取本地tag列表
        pass

    def get_remote_tags(self):
        # 获取远程tag列表
        pass

    def get_tag_info(self, tag_name):
        # 获取tag详细信息
        pass
```

### 2. 现有类改进

#### TagDialog改进

```python
class TagDialog(QDialog):
    def __init__(self, pod_name, local_path, parent=None):
        # 添加tag历史列表
        # 添加tag名称验证
        # 添加tag消息模板
        # 添加版本号建议
        pass
```

#### PodManager改进

```python
class PodManager(QMainWindow):
    def create_tag_for_pod(self):
        # 使用改进的TagDialog
        # 添加tag存在性检查
        # 添加错误处理
        pass

    def switch_to_tag_mode(self):
        # 使用TagSelectDialog
        # 添加tag列表获取
        # 支持tag预览
        pass
```

### 3. 数据持久化

**新增配置项：**
```json
{
  "tag_history": {
    "PodName": ["v1.0.0", "v1.0.1", "v1.1.0"]
  },
  "tag_templates": [
    "Release version {version}",
    "Hotfix for {issue}",
    "Feature {feature}"
  ],
  "favorite_tags": ["v1.0.0", "stable-1.0"],
  "tag_settings": {
    "auto_increment": true,
    "check_exists": true,
    "push_after_create": true
  }
}
```

---

## 测试计划

### 1. 单元测试

- Tag名称格式验证
- Tag版本号递增逻辑
- Git命令执行
- Tag存在性检查

### 2. 集成测试

- 创建tag完整流程
- 切换到tag引用完整流程
- 恢复到正常模式
- 批量操作测试

### 3. UI测试

- Tag对话框交互
- Tag选择对话框交互
- 错误提示显示
- 搜索和过滤功能

---

## 开发时间估算

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| 阶段一 | 基础功能增强 | 2-3天 |
| 阶段二 | 高级功能 | 3-4天 |
| 阶段三 | 用户体验优化 | 2-3天 |
| 测试和优化 | - | 1-2天 |
| **总计** | | **8-12天** |

---

## 风险和挑战

### 1. 技术风险
- Git命令在不同平台的兼容性
- 网络请求的稳定性
- 错误处理的完整性

### 2. 用户体验风险
- 功能过多导致界面复杂
- 学习成本增加
- 性能问题（大量tag时的加载速度）

### 3. 缓解措施
- 提供简洁模式和高级模式
- 异步加载tag列表
- 缓存tag信息
- 提供详细的帮助文档

---

## 下一步行动

1. **确认功能优先级**
   - 哪些功能必须实现？
   - 哪些功能可以后续迭代？

2. **确定开发范围**
   - 本次实现到哪个阶段？
   - 是否需要分批发布？

3. **技术准备**
   - 设计TagSelectDialog UI原型
   - 确定TagManager的API接口
   - 准备测试用例

---

**请确认：**
1. 是否同意这个规划？
2. 优先级是否需要调整？
3. 是否需要先实现某个具体功能？
