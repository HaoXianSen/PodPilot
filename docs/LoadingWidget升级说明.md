# LoadingWidget 现代化升级说明

## 概述

全新设计的 `LoadingWidget` 提供了4种现代化的 loading 动画样式，替代了原来单调的三点跳动动画。

## 可用样式

### 1. STYLE_SPINNER（旋转圆环）- **推荐默认**
- 流畅的旋转圆环动画
- 渐变色彩（蓝色→紫色→粉色）
- 60fps 平滑动画
- 视觉效果最佳

### 2. STYLE_DOTS（跳动圆点）
- 三个彩色圆点上下跳动
- 简洁轻快的视觉效果
- 适合快速加载场景

### 3. STYLE_PULSE（脉冲圆环）
- 圆环大小缩放动画
- 呼吸般的节奏感
- 半透明外圈效果

### 4. STYLE_BARS（竖条动画）
- 5个彩色竖条波浪起伏
- 音乐可视化风格
- 活泼动感

## 使用方法

### 方式1：直接使用 LoadingWidget

```python
from src.widgets.loading_widget import LoadingWidget

# 创建旋转圆环样式（推荐）
loading = LoadingWidget("加载中...", LoadingWidget.STYLE_SPINNER)
layout.addWidget(loading)
loading.start_animation()

# 切换样式
loading.set_style(LoadingWidget.STYLE_DOTS)

# 修改文本
loading.set_text("处理中...")

# 停止动画
loading.stop_animation()
```

### 方式2：使用 ModernLoadingDialog（带半透明背景）

```python
from src.widgets.loading_widget import ModernLoadingDialog

# 创建对话框
dialog = ModernLoadingDialog("处理中...", LoadingWidget.STYLE_SPINNER, self)
dialog.start()

# ... 执行耗时操作 ...

# 停止并关闭
dialog.stop()
```

### 方式3：在现有代码中升级

**旧代码（仍然兼容）**：
```python
self.loading_widget = LoadingWidget("加载中...")
self.loading_widget.start_animation()
```

**新代码（使用新样式）**：
```python
# 指定样式（默认为 STYLE_SPINNER）
self.loading_widget = LoadingWidget("加载中...", LoadingWidget.STYLE_SPINNER)
self.loading_widget.start_animation()
```

## 迁移指南

### 现有代码无需修改
所有现有代码都能正常工作，因为：
- 默认样式设置为 `STYLE_SPINNER`（最流畅）
- API 完全向后兼容
- `start_animation()` 和 `stop_animation()` 保持不变

### 推荐升级步骤

1. **主窗口加载（main_window.py:1326）**
```python
# 当前代码
self.loading_widget = LoadingWidget("加载远程Tag...")

# 升级为（可选）
self.loading_widget = LoadingWidget("加载远程Tag...", LoadingWidget.STYLE_SPINNER)
```

2. **批量操作对话框**
```python
# batch_tag_switch_dialog.py:591
# batch_branch_dialog.py:588
# batch_tag_dialog.py:465

# 当前代码
self.loading_widget = LoadingWidget("切换中...")

# 升级为
self.loading_widget = LoadingWidget("切换中...", LoadingWidget.STYLE_SPINNER)
```

## 演示程序

运行以下命令查看所有样式的实时演示：

```bash
cd /Users/haoyh02/Desktop/iPM
python3 loading_demo.py
```

## 技术细节

### 性能优化
- 旋转圆环：16ms 刷新间隔（60fps）
- 其他样式：50ms 刷新间隔
- 使用 QPainter 硬件加速
- 自动清理定时器资源

### 视觉设计
- 渐变色彩：`#667eea` → `#8b5cf6` → `#ec4899`
- 抗锯齿渲染
- 圆角端点
- 半透明效果

### 代码组织
```
src/widgets/loading_widget.py
├── LoadingWidget          # 核心组件
└── ModernLoadingDialog    # 独立对话框（可选）
```

## 常见问题

### Q: 旧代码还能用吗？
A: 能！完全向后兼容，默认使用最佳的旋转圆环样式。

### Q: 如何选择样式？
A: 
- 通用场景：`STYLE_SPINNER`（默认）
- 快速加载：`STYLE_DOTS`
- 强调节奏：`STYLE_PULSE`
- 活泼场景：`STYLE_BARS`

### Q: 可以动态切换样式吗？
A: 可以！使用 `loading.set_style(LoadingWidget.STYLE_DOTS)`

### Q: 颜色可以自定义吗？
A: 当前版本使用统一的渐变配色，如需自定义请修改 `loading_widget.py` 中的颜色值。

## 视觉对比

**旧版**：
- ⚫⚫⚫ 三个灰色圆点依次高亮
- 单色，视觉单调

**新版**：
- 🌀 流畅旋转的渐变圆环
- 多彩，视觉现代化
- 更流畅的动画效果

## 推荐使用场景

| 场景 | 推荐样式 | 说明 |
|------|---------|------|
| 网络请求 | SPINNER | 流畅平滑，适合不确定时长 |
| 快速操作 | DOTS | 轻快简洁，适合1-2秒完成 |
| 后台处理 | PULSE | 呼吸节奏，适合持续任务 |
| 媒体处理 | BARS | 活泼动感，适合创意场景 |

## 升级建议

虽然旧代码能正常工作，但建议在以下场景明确指定样式：

1. **关键用户体验路径**：如首次加载、登录等
2. **长时间加载**：明确使用 `STYLE_SPINNER` 或 `STYLE_PULSE`
3. **品牌一致性**：全局统一使用同一种样式

升级只需一行代码改动，收益明显！
