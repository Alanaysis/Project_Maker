# 跨平台框架原理 / Cross-Platform Framework Principles

> 实现跨平台框架核心原理的学习项目

## 项目描述 / Project Description

本项目深入探索跨平台 UI 框架的核心原理，以 Flutter 为主要参考实现。通过 Python 模拟 Flutter 的核心组件，帮助理解：

- **跨平台原理**：一套代码如何在不同平台上运行
- **渲染引擎**：Skia 图形引擎的工作原理
- **桥接机制**：Dart 与原生平台之间的通信

This project explores the core principles of cross-platform UI frameworks, using Flutter as the primary reference. By simulating Flutter's core components in Python, it helps understand:

- **Cross-platform principles**: How one codebase runs on different platforms
- **Rendering engine**: How the Skia graphics engine works
- **Bridge mechanism**: Communication between Dart and native platforms

## 学习目标 / Learning Objectives

### 核心概念 / Core Concepts

1. **Dart VM 原理**
   - 字节码编译与执行
   - 垃圾回收机制（标记-清除算法）
   - 对象模型

2. **渲染引擎原理**
   - Skia 图形库核心概念
   - Canvas/Paint/Path 系统
   - 图层合成与光栅化
   - 渲染管线（Widget → Element → Render → Scene → GPU）

3. **Widget 树原理**
   - Widget/Element/RenderObject 三层架构
   - 不可变 Widget 的更新机制
   - 布局约束传递模型

4. **Platform Channel 原理**
   - MethodChannel（方法调用）
   - EventChannel（事件流）
   - BasicMessageChannel（消息传递）
   - 平台编解码器

5. **布局系统原理**
   - BoxConstraints 约束系统
   - FlexLayout（弹性布局）
   - StackLayout（层叠布局）
   - 跨平台像素一致性

### 技术栈 / Tech Stack

| 类别 | 技术 |
|------|------|
| 语言 | Python (用于学习) |
| 参考框架 | Flutter 原理 |
| 图形引擎 | Skia 原理 |
| 依赖 | 仅使用 Python 标准库 |

## 项目结构 / Project Structure

```
cross-platform/
├── src/                          # 核心模块
│   ├── dart_vm.py               # Dart VM 模拟器
│   │   ├── 字节码指令集 (Opcode)
│   │   ├── Dart 对象模型
│   │   ├── 垃圾回收器 (GC)
│   │   └── VM 执行引擎
│   ├── rendering_engine.py      # Skia 渲染引擎模拟器
│   │   ├── 颜色系统 (Color)
│   │   ├── 画笔 (Paint)
│   │   ├── 矩形/偏移量 (Rect/Offset)
│   │   ├── 路径 (Path)
│   │   ├── 画布 (Canvas)
│   │   └── 渲染场景 (Scene)
│   ├── widget_tree.py           # Widget 树构建器
│   │   ├── Widget/Element 模型
│   │   ├── Render 对象
│   │   └── 盒模型/弹性/层叠布局
│   ├── layout_engine.py         # 布局引擎
│   │   ├── BoxConstraints
│   │   ├── 布局策略
│   │   └── 布局调试工具
│   ├── platform_channel.py      # 平台通道/桥接机制
│   │   ├── StandardCodec 编解码器
│   │   ├── MethodChannel
│   │   ├── EventChannel
│   │   ├── BasicMessageChannel
│   │   └── PlatformView
│   └── composition.py           # 合成图层
│       ├── 图层合成器
│       ├── 帧渲染器
│       ├── 光栅缓存
│       └── 渲染管线
├── examples/                     # 演示示例
│   ├── widget_tree_demo.py      # Widget 树构建演示
│   ├── platform_channel_demo.py # 平台通道通信演示
│   ├── custom_rendering_demo.py # 自定义渲染演示
│   └── cross_platform_layout_demo.py  # 跨平台布局演示
├── tests/                        # 单元测试
│   ├── test_dart_vm.py          # Dart VM 测试
│   ├── test_rendering_engine.py # 渲染引擎测试
│   └── test_integration.py      # 集成测试
├── README.md
└── requirements.txt
```

## 快速开始 / Quick Start

### 运行示例 / Run Examples

```bash
# 进入项目目录
cd projects/cross-platform

# 运行 Widget 树演示
python examples/widget_tree_demo.py

# 运行平台通道演示
python examples/platform_channel_demo.py

# 运行自定义渲染演示
python examples/custom_rendering_demo.py

# 运行跨平台布局演示
python examples/cross_platform_layout_demo.py
```

### 运行测试 / Run Tests

```bash
# 运行所有测试
python -m pytest tests/

# 运行单个测试文件
python tests/test_dart_vm.py
python tests/test_rendering_engine.py
python tests/test_integration.py
```

## 跨平台架构背景 / Architecture Background

### Flutter 架构概览 / Flutter Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│                  (Flutter / Dart Code)                   │
├──────────────────────────────────────────────────────────┤
│                     Widget Layer                         │
│            (UI 描述 / 不可变的配置)                       │
├──────────────────────────────────────────────────────────┤
│                    Element Layer                         │
│            (Widget 与 Render 的桥梁)                      │
├──────────────────────────────────────────────────────────┤
│                   Render Object Layer                    │
│            (布局、绘制、事件处理)                          │
├──────────────────────────────────────────────────────────┤
│                   Skia Graphics Engine                   │
│              (2D 矢量图形渲染引擎)                        │
├──────────────────────────────────────────────────────────┤
│                  Platform Layer                          │
│          (Android / iOS / Web / Desktop)                 │
├──────────────────────────────────────────────────────────┤
│                   Operating System                       │
│              (Linux / Windows / macOS)                   │
└──────────────────────────────────────────────────────────┘
```

### 核心原理 / Core Principles

#### 1. 跨平台原理

```
Dart 代码 → 编译 → 字节码 → VM 执行 → 渲染引擎 → 原生平台
```

- **Dart 编译**：AOT（发布）或 JIT（开发）
- **统一渲染**：Skia 引擎在所有平台绘制相同像素
- **原生集成**：通过 Platform Channel 访问原生 API

#### 2. 渲染管线

```
Widget Tree → Element Tree → Render Tree → Scene → GPU → Screen
   (描述)      (桥梁)        (布局+绘制)   (场景)  (光栅化)  (显示)
```

#### 3. 布局系统

```
约束传递（自上而下）:
  Parent → Constraints → Child

尺寸报告（自下而上）:
  Child → Size → Parent

位置设置（自顶向下）:
  Parent → Position → Child
```

#### 4. Platform Channel 通信

```
Dart ←→ StandardCodec ←→ Platform Channel ←→ Native Code
  (请求)   (序列化)          (传输)            (处理)
```

## 学习路径建议 / Learning Path

1. **第一阶段**：理解 Dart VM 原理
   - 阅读 `src/dart_vm.py`
   - 运行 `examples/widget_tree_demo.py`

2. **第二阶段**：掌握渲染引擎
   - 阅读 `src/rendering_engine.py`
   - 运行 `examples/custom_rendering_demo.py`

3. **第三阶段**：学习 Widget 树
   - 阅读 `src/widget_tree.py`
   - 运行 `examples/widget_tree_demo.py`

4. **第四阶段**：理解布局系统
   - 阅读 `src/layout_engine.py`
   - 运行 `examples/cross_platform_layout_demo.py`

5. **第五阶段**：掌握桥接机制
   - 阅读 `src/platform_channel.py`
   - 运行 `examples/platform_channel_demo.py`

6. **第六阶段**：综合理解
   - 阅读 `src/composition.py`
   - 运行测试套件
   - 理解完整渲染管线

## 参考资料 / References

- [Flutter Architecture Docs](https://docs.flutter.dev/platform-integration/engine)
- [Skia Graphics Engine](https://skia.org/)
- [Dart Language Specification](https://dart.dev/guides/language/spec)
- [Flutter Rendering Pipeline](https://docs.flutter.dev/perf/rendering)

## License

MIT License
