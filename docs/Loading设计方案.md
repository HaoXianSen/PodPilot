# Loading 设计方案 - PodPilot

## 设计理念

基于 UI/UX Pro Max 分析和项目的 Glassmorphism 设计风格，采用半透明遮罩 + 无边框 loading 的现代化方案。

## 设计特点

### 1. 半透明遮罩层
- **颜色**：rgba(0, 0, 0, 0.5)
- **作用**：让用户看到背后的界面，保持上下文感知
- **UX 原则**：符合"Loading States - Show feedback during async operations"最佳实践

### 2. 无边框 Loading 动画
- **位置**：屏幕居中浮动
- **背景**：透明，无对话框边框
- **效果**：轻量现代，不干扰视觉流

### 3. Glassmorphism 渐变圆环
- **颜色**：使用项目状态色渐变
  - 起点：#3b82f6 (BRANCH 蓝色)
  - 中点：#8b5cf6 (GIT 紫色)
  - 终点：#34c759 (TAG 绿色)
- **动画**：60fps 旋转圆环
- **圆角端点**：Qt.RoundCap 平滑效果

### 4. 文字样式
- **颜色**：rgba(255, 255, 255, 0.9)
- **字体**：13px, 500 weight
- **位置**：loading 动画下方

## 实现方案

### 当前实现（已完成）

```python
# 在主窗口中创建半透明遮罩
loading_overlay = QWidget(self)
loading_overlay.setGeometry(0, 0, self.width(), self.height())
loading_overlay.setStyleSheet("""
    QWidget {
        background-color: rgba(0, 0, 0, 0.5);
    }
""")
loading_overlay.setAttribute(Qt.WA_StyledBackground, True)
loading_overlay.show()
loading_overlay.raise_()

# 在遮罩层上放置LoadingWidget
loading_widget = LoadingWidget(
    "加载远程Tag...",
    LoadingWidget.STYLE_SPINNER,
    loading_overlay
)
loading_widget.setGeometry(
    (self.width() - 200) // 2,
    (self.height() - 120) // 2,
    200,
    120
)
loading_widget.show()
loading_widget.start_animation()
```

### 清理方案

```python
# 停止动画
loading_widget.stop_animation()

# 移除遮罩层（会自动移除子控件）
loading_overlay.deleteLater()
```

## 对比旧方案

| 方面 | 旧方案 | 新方案 |
|------|--------|--------|
| 容器 | QDialog 独立对话框 | QWidget 半透明遮罩 |
| 背景 | 深色渐变卡片 | 透明（只有遮罩） |
| 视觉 | 有边框、有标题栏 | 无边框、极简 |
| 层级 | 独立窗口 | 叠加在主窗口上 |
| 上下文 | 失去上下文感知 | 保持上下文感知 |

## UX 最佳实践遵循

根据 UI/UX Pro Max 分析：

✅ **DO:**
- 使用 spinner 提供视觉反馈
- 操作 > 300ms 显示 loading
- 平滑的 150-300ms 过渡动画
- 保持用户对界面的感知

❌ **DON'T:**
- 不使用连续动画装饰元素
- 不冻结 UI 无反馈
- 不使用过于复杂的动画

## 实际使用位置

1. **Tag 模式切换**（main_window.py:1310-1346）
   - 触发：点击"Tag模式"按钮
   - 文字："加载远程Tag..."
   - 时长：网络请求 + Git 操作

2. **MR 信息收集**（main_window.py:1660-1680）
   - 触发：点击"一键MR"
   - 文字："加载Pod MR信息..."
   - 时长：多个 Git 仓库信息收集

3. **批量操作**（各对话框）
   - 批量 Tag 切换
   - 批量 Branch 切换
   - 批量 Tag 创建
   - 文字：根据操作动态显示

## 技术细节

### 渐变色定义

来自项目配色系统（glassmorphism.py）：
```python
# 状态标签色
BRANCH = "#3b82f6"  # 蓝色
GIT = "#8b5cf6"     # 紫色
TAG = "#34c759"     # 绿色
```

### 动画参数

- 刷新频率：16ms（60fps）
- 圆环半径：20px
- 线条宽度：3px
- 旋转速度：6度/帧

### 性能考虑

- 使用 QPainter 硬件加速
- 抗锯齿渲染（QPA inter.Antialiasing）
- QTimer 精确控制帧率
- 自动资源清理（deleteLater）

## 未来优化方向

1. **进度指示**：对于已知进度的操作，可添加环形进度条
2. **取消按钮**：长时间操作添加取消选项
3. **错误反馈**：loading 失败时的动画过渡
4. **响应式大小**：根据窗口大小自动调整 loading 位置

## 参考资料

- UI/UX Pro Max Skill: Loading States guideline
- Material Design: Progress & activity
- Apple HIG: Progress indicators
- 项目设计系统：glassmorphism.py
