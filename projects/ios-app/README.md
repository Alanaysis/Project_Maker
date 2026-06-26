"""
iOS 基础应用学习项目
iOS Basic Application Learning Project

通过 Python 模拟 iOS 架构核心概念，帮助理解 iOS 开发流程。

This project simulates core iOS architecture concepts using Python
to help understand iOS development workflows.

================================================================================
目录 / Table of Contents
================================================================================

1. 项目简介 / Project Overview
2. 学习目标 / Learning Objectives
3. iOS 架构背景 / iOS Architecture Background
4. 项目结构 / Project Structure
5. 运行示例 / Running Examples
6. 运行测试 / Running Tests
7. 核心概念对照 / Architecture Mapping

================================================================================
1. 项目简介
================================================================================

本项目通过 Python 模拟 iOS 核心架构组件，包括：

- RunLoop (运行循环): iOS 事件处理的核心机制
- UIView / UIViewController: 视图和视图控制器
- Auto Layout: 基于约束的自动布局系统
- UINavigationController: 导航控制器
- UITableView: 表格视图
- URLSession: 网络请求框架
- KVO (Key-Value Observing): 数据绑定机制
- UIGestureRecognizer: 手势识别器

================================================================================
2. 学习目标
================================================================================

1. 理解 iOS 架构
   - 掌握 MVC/MVVM 架构模式
   - 理解 RunLoop 事件循环机制
   - 理解主线程 UI 更新规则

2. 掌握 UIKit
   - 理解视图层次结构
   - 掌握 Auto Layout 约束系统
   - 理解导航控制器的工作原理
   - 理解 UITableView 的数据源和代理模式

3. 学会网络请求
   - 理解 URLSession 的工作机制
   - 掌握异步回调模式
   - 理解请求/响应生命周期

================================================================================
3. iOS 架构背景
================================================================================

3.1 RunLoop (运行循环)
-----------------------
RunLoop 是 iOS 应用的核心，负责：
- 处理用户输入（触摸、按键）
- 处理系统事件（定时器、网络回调）
- 保持应用运行

每个线程有且仅有一个 RunLoop。
主线程的 RunLoop 默认运行在 DEFAULT mode。

3.2 视图层次 (View Hierarchy)
-------------------------------
iOS UI 采用树形结构：
- UIWindow 是根视图
- UIView 是基本构建块
- UIViewController 管理 UIView 层次

3.3 Auto Layout (自动布局)
---------------------------
基于约束的布局系统：
- NSLayoutConstraint 定义视图间的关系
- 支持相对布局（A = B * multiplier + constant）
- 替代传统的 frame 布局

3.4 导航控制器 (Navigation Controller)
----------------------------------------
管理视图控制器栈：
- push: 压入新页面
- pop: 弹出当前页面
- 支持交互式滑动手势返回

3.5 网络请求 (URLSession)
--------------------------
iOS 网络请求的核心：
- URLSession 管理会话
- URLSessionDataTask 处理异步请求
- 回调机制处理响应

3.6 数据绑定 (KVO)
-------------------
Key-Value Observing 机制：
- 监听属性变化
- 自动通知观察者
- MVVM 架构的基础

================================================================================
4. 项目结构
================================================================================

ios-app/
├── src/                          # 源代码
│   ├── __init__.py               # 模块说明
│   ├── core/                     # 核心架构
│   │   └── __init__.py           # RunLoop, MainThread, Application
│   ├── ui/                       # UI 组件
│   │   └── __init__.py           # UIView, UIViewController, etc.
│   ├── network/                  # 网络模块
│   │   └── __init__.py           # URLSession, URLRequest, etc.
│   └── binding/                  # 数据绑定
│       └── __init__.py           # KVO, Observable, ViewModel
├── examples/                     # 示例脚本
│   ├── 01_basic_ui_layout.py     # 基础 UI 布局
│   ├── 02_navigation_controller.py # 导航控制器
│   ├── 03_table_view_demo.py     # 表格视图
│   └── 04_network_request_demo.py # 网络请求
├── tests/                        # 单元测试
│   └── test_ios_app.py           # 综合测试
├── README.md                     # 本文档
└── requirements.txt              # 依赖 (无)

================================================================================
5. 运行示例
================================================================================

所有示例不需要安装任何依赖，直接运行：

    python examples/01_basic_ui_layout.py    # 基础 UI 布局
    python examples/02_navigation_controller.py  # 导航控制器
    python examples/03_table_view_demo.py    # 表格视图
    python examples/04_network_request_demo.py # 网络请求

或者一次性运行：

    python -m pytest tests/ -v

================================================================================
6. 运行测试
================================================================================

    python -m pytest tests/ -v

测试覆盖：
- RunLoop 事件循环
- UIView 视图层次
- Auto Layout 约束系统
- 手势识别器
- UINavigationController
- UITableView
- URLSession 网络请求
- KVO 数据绑定
- ViewModel MVVM

================================================================================
7. 核心概念对照
================================================================================

iOS 概念              | Python 模拟
---------------------|------------------------------------------
UIApplication        | Application 类
RunLoop              | RunLoop 类
UIView               | UIView 类
UIViewController     | UIViewController 类
UINavigationController | UINavigationController 类
UITableView          | UITableView 类
UILabel              | UILabel 类
UIButton             | UIButton 类
Auto Layout          | UILayout / NSLayoutConstraint
UIGestureRecognizer  | UIGestureRecognizer 系列类
URLSession           | URLSession 类
URLRequest           | URLRequest 类
KVO                  | Observable / KVOObserver
MVVM                 | ViewModel 类
GCD (dispatch)       | RunLoop.perform_on_main()

================================================================================
"""
