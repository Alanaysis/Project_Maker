"""
iOS 基础应用学习项目 - iOS Basic Application Learning Project

本项目通过 Python 模拟 iOS 架构核心概念，帮助理解 iOS 开发流程。
This project simulates core iOS architecture concepts using Python
to help understand iOS development workflows.

iOS Architecture Overview / iOS 架构概览:
==========================================

1. Run Loop (运行循环)
   - iOS 应用的核心，负责处理事件循环
   - RunLoop 持续运行，处理输入源（触摸、定时器、网络等）
   - 类比：Python 的事件循环 / 消息队列

2. View Hierarchy (视图层次)
   - UIViewController 管理 UIView
   - UIView 构成视图树
   - 每个 UIView 可以包含子视图，形成树形结构

3. Auto Layout (自动布局)
   - 基于约束的布局系统
   - NSLayoutConstraint 定义视图之间的关系
   - 替代传统的 frame 布局

4. Data Binding (数据绑定)
   - KVO (Key-Value Observing) 监听属性变化
   - 类似 Python 的 descriptor 模式

5. Network (网络请求)
   - URLSession 处理 HTTP 请求
   - 异步回调机制

6. Navigation (导航)
   - UINavigationController 管理视图控制器栈
   - push/pop 实现页面切换
"""
