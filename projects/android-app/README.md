# Android 基础应用 - Android Basic Application Learning Project
# Android 基础应用学习项目

> 通过 Python 模拟 Android 核心概念，学习 Android 架构原理

---

## 项目概述 / Project Overview

本项目通过 Python 模拟 Android 应用开发的核心概念，帮助学习者理解 Android 架构原理，包括：

This project simulates core Android application development concepts using Python to help learners understand Android architecture principles, including:

- **Activity 生命周期** - Activity Lifecycle
- **View 系统** - View System
- **布局系统** - Layout System
- **Intent 和导航** - Intent & Navigation
- **Fragment 生命周期** - Fragment Lifecycle
- **数据持久化** - Data Persistence
- **Jetpack Compose 概念** - Jetpack Compose Concepts
- **数据绑定** - Data Binding
- **网络请求** - Network Requests

---

## 学习目标 / Learning Goals

### 理解 Android 架构 / Understand Android Architecture

- Android 应用四层架构：应用层、框架层、运行时层、内核层
- Activity/Fragment 作为应用组件的核心作用
- Android 消息处理机制（Looper/Handler/MessageQueue）

### 掌握 Jetpack Compose / Master Jetpack Compose

- 声明式 UI 设计范式
- Composable 函数的工作原理
- 状态管理（State Hoisting）
- 布局系统（Row/Column/Box）

### 学会生命周期 / Learn Lifecycle

- Activity 生命周期：onCreate → onStart → onResume → onPause → onStop → onDestroy
- Fragment 生命周期
- 生命周期感知型组件（Lifecycle-aware Components）
- LifecycleOwner 与 LifecycleObserver 的关系

---

## Android 架构背景 / Android Architecture Background

### Android 系统架构 / Android System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  应用层 Application Layer            │
│  (Contacts, Browser, Custom Apps, etc.)             │
├─────────────────────────────────────────────────────┤
│                  框架层 Framework Layer              │
│  ActivityManager, WindowManager, PackageManager,    │
│  ContentProvider, View System, Resource Manager      │
├─────────────────────────────────────────────────────┤
│                  运行时层 Runtime Layer              │
│  ART (Android Runtime), Core Libraries              │
├─────────────────────────────────────────────────────┤
│                  内核层 Kernel Layer                 │
│  Linux Kernel, Drivers, Memory Management           │
└─────────────────────────────────────────────────────┘
```

### Activity 生命周期 / Activity Lifecycle

```
┌──────────────────────────┐
│   onCreate()             │  创建 Activity，初始化组件
│   onStart()              │  使 Activity 可见
│   onResume()             │  Activity 获得焦点，可交互
│──────────────────────────│
│   onResume()             │  当前状态
│──────────────────────────│
│   onPause()              │  失去焦点，暂停交互
│   onStop()               │  不再可见
│   onDestroy()            │  销毁 Activity
└──────────────────────────┘
```

### Jetpack Compose 核心概念 / Jetpack Compose Core Concepts

Jetpack Compose 是 Android 的现代声明式 UI 工具包：

1. **声明式 UI** - 描述 UI 应该是什么样子，而非如何构建
2. **Composable 函数** - 使用 `@Composable` 标记的函数
3. **状态管理** - `State`、`MutableState`、`StateFlow`
4. **布局原语** - `Row`、`Column`、`Box`

---

## 项目结构 / Project Structure

```
android-app/
├── src/                          # 源代码 / Source code
│   ├── __init__.py
│   ├── lifecycle.py              # Activity/Fragment 生命周期模拟
│   ├── view.py                   # View 系统 (TextView, Button, etc.)
│   ├── layout.py                 # 布局系统 (LinearLayout, etc.)
│   ├── intent.py                 # Intent 和导航
│   ├── fragment.py               # Fragment 生命周期
│   ├── shared_prefs.py           # SharedPreferences 模拟
│   ├── compose.py                # Jetpack Compose 概念
│   ├── data_binding.py           # 数据绑定
│   └── network.py                # 网络请求模拟
├── examples/                     # 演示示例 / Demo scripts
│   ├── basic_activity_demo.py    # Activity 生命周期演示
│   ├── fragment_demo.py          # Fragment 演示
│   ├── intent_navigation_demo.py # Intent 导航演示
│   └── data_persistence_demo.py  # 数据持久化演示
├── tests/                        # 单元测试 / Unit tests
│   ├── __init__.py
│   ├── test_lifecycle.py
│   ├── test_view.py
│   ├── test_layout.py
│   ├── test_intent.py
│   ├── test_fragment.py
│   ├── test_shared_prefs.py
│   ├── test_compose.py
│   └── test_data_binding.py
├── README.md
└── requirements.txt
```

---

## 如何运行示例 / How to Run Examples

### 运行单个示例 / Run a Single Example

```bash
# Activity 生命周期演示
python examples/basic_activity_demo.py

# Fragment 演示
python examples/fragment_demo.py

# Intent 导航演示
python examples/intent_navigation_demo.py

# 数据持久化演示
python examples/data_persistence_demo.py
```

### 运行所有测试 / Run All Tests

```bash
python -m pytest tests/ -v
```

---

## 核心概念速查 / Core Concepts Quick Reference

### Activity 生命周期方法 / Activity Lifecycle Methods

| 方法 | 说明 |
|------|------|
| `onCreate()` | 首次创建时调用，初始化 UI 和状态 |
| `onStart()` | Activity 即将变为可见时调用 |
| `onResume()` | Activity 开始与用户交互时调用 |
| `onPause()` | 系统准备启动或恢复另一个 Activity 时调用 |
| `onStop()` | Activity 不再可见时调用 |
| `onDestroy()` | Activity 被销毁前调用 |

### Intent 类型 / Intent Types

| 类型 | 用途 |
|------|------|
| 显式 Intent | 指定目标组件 |
| 隐式 Intent | 通过 Action/Category/Data 匹配 |
| Service Intent | 启动后台服务 |
| Broadcast Intent | 发送系统级广播 |

### Jetpack Compose 布局原语 / Compose Layout Primitives

| 组件 | 说明 |
|------|------|
| `Column` | 垂直排列子元素 |
| `Row` | 水平排列子元素 |
| `Box` | 堆叠子元素 |
| `LazyColumn` | 可滚动垂直列表 |
| `LazyRow` | 可滚动水平列表 |

---

## 参考资料 / References

- [Android 开发者文档](https://developer.android.com)
- [Jetpack Compose 文档](https://developer.android.com/jetpack/compose)
- [Android 架构组件](https://developer.android.com/topic/architecture)
- [Activity 生命周期](https://developer.android.com/guide/components/activities/activity-lifecycle)

---

## License

MIT License
