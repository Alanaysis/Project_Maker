# embedded-gui - 嵌入式 GUI 框架
# Embedded GUI Framework

## 项目描述 / Project Description

**嵌入式 GUI 框架** - 一个为资源受限嵌入式系统设计的轻量级图形用户界面框架。
**Embedded GUI Framework** - A lightweight GUI framework designed for resource-constrained embedded systems.

本项目从零实现了一个完整的嵌入式 GUI 框架，涵盖:
- 帧缓冲区和像素渲染
- 2D 绘图基元 (线、矩形、圆、文字)
- Widget 系统 (按钮、标签、文本框、滑块、复选框)
- 布局引擎 (绝对、相对、流式、重力对齐)
- 事件处理 (触摸、按键)
- 主题/样式系统
- 窗口管理

This project implements a complete embedded GUI framework from scratch, covering:
- Framebuffer and pixel rendering
- 2D drawing primitives (lines, rectangles, circles, text)
- Widget system (buttons, labels, textboxes, sliders, checkboxes)
- Layout engine (absolute, relative, flow, gravity)
- Event handling (touch, key)
- Theme/style system
- Window management

---

## 架构 / Architecture

```
┌─────────────────────────────────────────────┐
│                 GUI Core                     │
├─────────────────────────────────────────────┤
│  Window Management  │  Event Dispatch       │
├─────────────────────────────────────────────┤
│  Layout Engine      │  Theme System         │
├─────────────────────────────────────────────┤
│  Widget System      │  Font System          │
├─────────────────────────────────────────────┤
│  Rendering Engine   │  Drawing Primitives   │
├─────────────────────────────────────────────┤
│  Framebuffer        │  Display Driver       │
├─────────────────────────────────────────────┤
│  Input Driver       │  Event Queue          │
└─────────────────────────────────────────────┘
```

**核心循环 / Core Loop:**
```
UI 定义 → 布局计算 → 渲染 → 事件处理
UI Definition → Layout → Rendering → Event Handling
```

---

## 目录结构 / Directory Structure

```
embedded-gui/
├── include/
│   └── embedded_gui.h      # 公共头文件 / Public header
├── src/
│   ├── display.c           # 帧缓冲区和显示驱动 / Framebuffer & display driver
│   ├── renderer.c          # 渲染引擎 / Rendering engine
│   ├── widget.c            # Widget 系统 / Widget system
│   ├── layout.c            # 布局引擎 / Layout engine
│   ├── event.c             # 事件处理 / Event handling
│   ├── window.c            # 窗口管理 / Window management
│   ├── theme.c             # 主题系统 / Theme system
│   └── font.c              # 字体渲染 / Font rendering
├── examples/
│   ├── 01_basic_widget_demo.c    # 基础 Widget 演示
│   ├── 02_form_interface_demo.c  # 表单界面演示
│   ├── 03_menu_system_demo.c     # 菜单系统演示
│   └── 04_touch_interaction_demo.c # 触摸交互演示
├── tests/
│   ├── test_color.c        # 颜色系统测试
│   ├── test_renderer.c     # 渲染引擎测试
│   ├── test_widget.c       # Widget 系统测试
│   ├── test_layout.c       # 布局引擎测试
│   ├── test_event.c        # 事件处理测试
│   └── test_theme.c        # 主题系统测试
├── Makefile
└── README.md
```

---

## 学习目标 / Learning Objectives

### 理解嵌入式 GUI / Understand Embedded GUI
- 帧缓冲区的工作原理 (Framebuffer basics)
- RGB565 颜色格式 (Color format)
- 双缓冲渲染 (Double buffering)

### 掌握渲染引擎 / Master Rendering Engine
- Bresenham 画线算法 (Line drawing)
- 圆形算法 (Circle algorithms)
- 位图字体渲染 (Bitmap font rendering)
- 裁剪优化 (Clipping optimization)

### 学会事件处理 / Learn Event Handling
- 事件队列管理 (Event queue management)
- 命中测试 (Hit testing)
- 事件冒泡 (Event bubbling)
- 焦点管理 (Focus management)

### 布局算法 / Layout Algorithms
- 绝对定位 (Absolute positioning)
- 相对定位 (Relative positioning)
- 流式布局 (Flow layout)
- 重力对齐 (Gravity alignment)

---

## 如何编译 / How to Build

```bash
# 编译所有测试 / Build all tests
make

# 编译单个测试 / Build individual test
make test-color
make test-renderer
make test-widget
make test-layout
make test-event
make test-theme

# 编译示例 / Build examples
make example-01
make example-02
make example-03
make example-04

# 运行测试 / Run tests
make test

# 清理 / Clean
make clean
```

---

## 如何运行示例 / How to Run Examples

```bash
# 基础 Widget 演示
./build/01_basic_widget_demo

# 表单界面演示
./build/02_form_interface_demo

# 菜单系统演示
./build/03_menu_system_demo

# 触摸交互演示
./build/04_touch_interaction_demo
```

---

## 技术细节 / Technical Details

### 颜色格式 / Color Format
- **RGB565**: 16-bit 颜色格式
  - R: 5 bits (bits 11-15)
  - G: 6 bits (bits 5-10)
  - B: 5 bits (bits 0-4)
- 节省 33% 内存相比 RGB888
- 人眼对绿色更敏感，所以 G 占 6 bits

### 字体系统 / Font System
- 8x12 位图字体 (8-bit per pixel)
- ASCII 32-127 字符支持
- 固定宽度字符 (简化布局)
- 编译时嵌入 (无外部文件依赖)

### 事件处理 / Event Handling
- 固定大小事件队列 (32 个事件)
- FIFO 事件分发
- 命中测试 (从顶层 widget 开始)
- 事件冒泡 (子 → 父)

### 布局引擎 / Layout Engine
- **绝对定位**: 手动指定 (x, y)，性能最高
- **相对定位**: 基于容器和 margin
- **流式布局**: 自动换行，类似 HTML
- **重力对齐**: 靠边对齐 (左/右/上/下/居中)

---

## 嵌入式适配 / Embedded Adaptation

### 内存管理 / Memory Management
- 无动态内存分配 (无 malloc/free)
- 静态池管理 widget 和窗口
- 固定大小事件队列

### 性能优化 / Performance Optimization
- 裁剪: 只绘制可见区域
- 批量渲染: 按行写入
- 整数运算: 无浮点需求

### 显示适配 / Display Adaptation
- 通过 `egui_display_driver_t` 接口适配
- 支持 SPI/RGB/E-Ink 等接口
- 支持任意分辨率

### 输入适配 / Input Adaptation
- 通过 `egui_input_driver_t` 接口适配
- 支持电容/电阻触摸屏
- 支持物理按键

---

## 扩展方向 / Extension Directions

1. **更多 Widget**: 进度条、图像、滚动视图
2. **动画系统**: 过渡动画、淡入淡出
3. **布局管理器**: 约束布局、网格布局
4. **图形效果**: 阴影、渐变、抗锯齿
5. **多语言支持**: Unicode 字体
6. **文件系统**: 字体/图像从 flash 加载
7. **网络**: 远程 UI 调试

---

## License

MIT License
