# HarmonyOS Basic Application (鸿蒙基础应用)

> 学习 HarmonyOS 基础应用开发的项目，通过 Python 模拟鸿蒙架构核心概念。

---

## 项目描述 / Project Description

本项目是一个 HarmonyOS（鸿蒙）基础应用学习项目，通过 Python 模拟鸿蒙架构的核心概念，包括：

- **ArkUI 声明式 UI 框架**：模拟 ArkTS 的声明式 UI 编程范式
- **状态管理**：实现 `@State`、`@Prop`、`@Link` 等装饰器的数据绑定机制
- **分布式能力**：模拟鸿蒙的分布式数据管理和跨设备协同
- **组件生命周期**：模拟页面和组件的生命周期管理
- **布局系统**：实现 Stack、Flex 等鸿蒙常用布局容器

This project is a HarmonyOS basic application learning project that simulates core concepts of the HarmonyOS architecture through Python, including:

- **ArkUI Declarative UI Framework**: Simulates the declarative UI programming paradigm of ArkTS
- **State Management**: Implements data binding mechanisms of `@State`, `@Prop`, `@Link` decorators
- **Distributed Capabilities**: Simulates HarmonyOS distributed data management and cross-device collaboration
- **Component Lifecycle**: Simulates page and component lifecycle management
- **Layout System**: Implements common HarmonyOS layout containers like Stack and Flex

---

## 学习目标 / Learning Objectives

### 理解鸿蒙架构 / Understand HarmonyOS Architecture

1. **鸿蒙系统分层架构**：
   - 内核层（Kernel Layer）：Linux/Kunpeng 内核
   - 系统服务层（System Services Layer）：HDF 驱动框架、分布式软总线
   - 框架层（Framework Layer）：ArkUI、ArkCompiler
   - 应用层（Application Layer）：HAP 应用包

2. **分布式技术**：
   - 分布式数据管理：多设备数据同步
   - 分布式任务调度：跨设备应用迁移
   - 分布式安全：设备认证、数据加密

### 掌握 ArkUI / Master ArkUI

1. **声明式 UI 范式**：
   - 通过描述"是什么"而非"怎么做"来构建 UI
   - UI 是状态的函数：`UI = f(state)`
   - 状态变化自动触发 UI 重建

2. **核心组件**：
   - `Text`：文本显示组件
   - `Button`：按钮组件
   - `Image`：图片显示组件
   - `TextInput`：文本输入组件
   - `List` / `ListItem`：列表组件
   - `Grid`：网格布局组件
   - `Swiper`：轮播图组件

3. **布局容器**：
   - `Column` / `Row`：线性布局
   - `Stack`：堆栈布局（层叠）
   - `Flex`：弹性布局
   - `Grid`：网格布局
   - `RelativeContainer`：相对布局

4. **状态管理装饰器**：
   - `@State`：组件内部状态，变化时触发 UI 更新
   - `@Prop`：单向数据绑定，父组件到子组件
   - `@Link`：双向数据绑定，父子组件共享状态
   - `@ObjectLink`：对象引用绑定
   - `@Provide` / `@Consume`：跨组件层级传递

### 学会分布式能力 / Learn Distributed Capabilities

1. **分布式数据管理**：
   - 数据在多台设备间自动同步
   - 支持结构化/非结构化数据

2. **跨设备协同**：
   - 应用迁移：应用在不同设备间无缝迁移
   - 任务调度：根据设备能力分配任务

3. **统一应用开发**：
   - 一次开发，多端部署
   - 自适应布局适配不同屏幕

---

## 核心循环 / Core Loop

```
UI 设计 → 逻辑实现 → 分布式调用 → 展示
```

1. **UI 设计**：使用 ArkUI 声明式语法定义界面结构
2. **逻辑实现**：编写业务逻辑，处理用户交互
3. **分布式调用**：通过分布式接口实现跨设备协同
4. **展示**：UI 根据状态变化自动更新显示

---

## 项目结构 / Project Structure

```
harmonyos-app/
├── src/                          # 源代码目录
│   ├── __init__.py
│   ├── component/                # ArkUI 组件系统
│   │   ├── base.py               # 组件基类
│   │   ├── text.py               # Text 文本组件
│   │   ├── button.py             # Button 按钮组件
│   │   ├── image.py              # Image 图片组件
│   │   ├── input.py              # TextInput 输入组件
│   │   ├── list_component.py     # List/ListItem 列表组件
│   │   └── container.py          # 布局容器 (Column/Row/Stack/Flex/Grid)
│   ├── state/                    # 状态管理
│   │   ├── manager.py            # 状态管理器核心
│   │   ├── decorators.py         # @State/@Prop/@Link 装饰器
│   │   └── observable.py         # 可观察对象
│   ├── distributed/              # 分布式能力
│   │   ├── data_sync.py          # 分布式数据同步
│   │   ├── device_manager.py     # 设备管理
│   │   └── task_scheduler.py     # 任务调度
│   ├── lifecycle/                # 生命周期管理
│   │   ├── page_lifecycle.py     # 页面生命周期
│   │   └── component_lifecycle.py # 组件生命周期
│   └── layout/                   # 布局系统
│       ├── constraints.py        # 约束系统
│       └── measure.py            # 测量系统
├── examples/                     # 示例脚本
│   ├── 01_basic_ui.py            # 基础 UI 组件演示
│   ├── 02_state_management.py    # 状态管理演示
│   ├── 03_distributed_call.py    # 分布式调用模拟
│   └── 04_page_navigation.py     # 页面导航演示
├── tests/                        # 单元测试
│   ├── test_components.py
│   ├── test_state_management.py
│   ├── test_distributed.py
│   └── test_lifecycle.py
├── README.md
└── requirements.txt
```

---

## 如何运行示例 / How to Run Examples

### 环境要求 / Requirements

- Python 3.8+
- 无外部依赖 (no external dependencies)

### 运行示例 / Run Examples

```bash
# 进入项目目录
cd projects/harmonyos-app

# 运行基础 UI 组件演示
python examples/01_basic_ui.py

# 运行状态管理演示
python examples/02_state_management.py

# 运行分布式调用模拟
python examples/03_distributed_call.py

# 运行页面导航演示
python examples/04_page_navigation.py
```

### 运行测试 / Run Tests

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行单个测试文件
python -m pytest tests/test_components.py -v
```

---

## HarmonyOS 架构背景 / HarmonyOS Architecture Background

### 鸿蒙系统架构 / HarmonyOS System Architecture

```
┌─────────────────────────────────────────────────┐
│              应用层 Application Layer            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ HAP 应用  │  │ HAP 应用  │  │ HAP 应用  │     │
│  └──────────┘  └──────────┘  └──────────┘     │
├─────────────────────────────────────────────────┤
│              框架层 Framework Layer              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  ArkUI   │  │ArkCompiler│  │ 系统服务  │     │
│  │ 声明式UI  │  │ 编译优化  │  │ Framework │     │
│  └──────────┘  └──────────┘  └──────────┘     │
├─────────────────────────────────────────────────┤
│            系统服务层 System Services Layer      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  HDF驱动  │  │分布式软总线│  │ 安全框架  │     │
│  │ Framework │  │Distributed │  │ Security │     │
│  └──────────┘  │  Bus      │  └──────────┘     │
│                └──────────┘                       │
├─────────────────────────────────────────────────┤
│              内核层 Kernel Layer                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Linux   │  │  Kunpeng  │  │  LiteOS  │     │
│  │  内核     │  │  微内核   │  │  A       │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────┘
```

### ArkUI 核心概念 / ArkUI Core Concepts

**声明式 UI (Declarative UI)**：

```
// ArkTS 原生写法（参考）
@Entry
@Component
struct Greeting {
  @State message: string = 'Hello HarmonyOS'

  build() {
    Column() {
      Text(this.message)
        .fontSize(24)
        .fontWeight(FontWeight.Bold)
      Button('Change')
        .onClick(() => {
          this.message = 'Updated!'
        })
    }
  }
}

// Python 模拟写法
greeting = Component('Greeting')
greeting.state(message='Hello HarmonyOS')

@greeting.build
def build():
    with Column():
        Text(this['message']).font_size(24)
        Button('Change').on_click(lambda: this.update(message='Updated!'))
```

**数据驱动 UI**：

```
状态变化 → UI 自动重建 → 显示新状态
```

### 分布式技术 / Distributed Technology

**分布式数据管理**：

```
设备 A  ──[数据同步]──▶  分布式数据集群  ◀──[数据同步]──▶  设备 B
                                    │
                          [数据一致性保证]
```

**关键特性**：

1. **分布式数据同步**：多设备间数据自动同步，保证一致性
2. **分布式任务调度**：根据设备能力动态分配任务
3. **分布式设备发现**：自动发现附近设备
4. **分布式安全**：设备认证、数据传输加密

---

## 参考资源 / References

- [HarmonyOS 官方文档](https://developer.harmonyos.com/)
- [ArkUI 开发指南](https://developer.harmonyos.com/cn/docs/documentation/doc-guides/V3/arkui-overview)
- [分布式技术详解](https://developer.harmonyos.com/cn/docs/documentation/doc-guides/guides/distributed-data)

---

*本项目为学习用途，通过 Python 模拟鸿蒙架构核心概念，帮助理解 HarmonyOS 应用开发.*
