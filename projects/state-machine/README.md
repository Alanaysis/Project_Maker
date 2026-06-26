# 状态机框架 / State Machine Framework

**A generic state machine framework for Rust, supporting state transitions, event-driven architecture, and history recording.**

**一个通用的 Rust 状态机框架，支持状态转换、事件驱动架构和历史记录。**

---

## 功能特性 / Features

### 中文
- **通用状态与事件类型**：支持任何实现 `State` 和 `Event` trait 的类型
- **事件驱动架构**：通过事件触发状态转换
- **守卫条件**：可选的转换前置条件检查
- **转换动作**：状态转换时执行的副作用操作
- **历史记录**：带时间戳和持续时间的转换追踪
- **层次状态机**：支持嵌套状态、正交区域和历史恢复
- **转换图可视化**：状态机结构的文本可视化
- **构建器模式**：易于使用的 API 定义转换
- **回调机制**：响应状态变化和转换失败
- **完善的错误处理**：针对不同失败场景的错误类型

### English
- **Generic State & Event Types**: Works with any types that implement the `State` and `Event` traits
- **Event-Driven Architecture**: Process events to trigger state transitions
- **Guard Conditions**: Optional conditions that must be met for transitions to occur
- **Transition Actions**: Execute side effects when transitions happen
- **History Recording**: Track all state transitions with timestamps and durations
- **Hierarchical State Machines**: Nested states, orthogonal regions, and history restoration
- **Transition Graph**: Visualize the state machine's structure
- **Builder Pattern**: Easy-to-use API for defining transitions
- **Callbacks**: React to state changes and transition failures
- **Error Handling**: Comprehensive error types for different failure scenarios

---

## 学习目标 / Learning Objectives

### 中文
1. **理解有限状态机原理**：掌握状态、事件、转换的核心概念
2. **掌握状态转换图设计**：学会设计清晰的状态转换图
3. **学会事件驱动架构**：理解事件驱动的编程范式
4. **理解层次状态机**：掌握 Statechart 语义和正交区域
5. **掌握守卫条件和动作**：学会在适当时机使用守卫和动作
6. **学会历史记录追踪**：理解状态机执行的历史追踪

### English
1. **Understand Finite State Machines**: Master the core concepts of states, events, and transitions
2. **Master State Transition Diagrams**: Learn to design clear state transition diagrams
3. **Learn Event-Driven Architecture**: Understand the event-driven programming paradigm
4. **Understand Hierarchical State Machines**: Master Statechart semantics and orthogonal regions
5. **Master Guard Conditions and Actions**: Learn when and how to use guards and actions
6. **Learn History Tracking**: Understand execution history tracking for state machines

---

## 状态机理论基础 / State Machine Theory Background

### 什么是有限状态机？ / What is a Finite State Machine?

有限状态机（FSM）是一种计算模型，由以下要素组成：

A Finite State Machine (FSM) is a computational model consisting of:

- **状态（States）**：系统可能处于的条件
- **事件（Events）**：触发状态转换的外部刺激
- **转换（Transitions）**：从一个状态到另一个状态的条件映射
- **初始状态（Initial State）**：机器启动时的状态
- **终止状态（Final States）**：表示完成的状态

### 核心循环 / Core Loop

```
事件输入 → 状态查找 → 条件检查 → 状态转换 → 动作执行
Event Input → State Lookup → Condition Check → State Transition → Action Execution
```

### 层次状态机 / Hierarchical State Machines

层次状态机（Statecharts）扩展了传统 FSM：

Hierarchical State Machines (Statecharts) extend traditional FSMs:

1. **嵌套状态（Nested States）**：状态可以包含子状态
2. **正交区域（Orthogonal Regions）**：复合状态可以有多个独立区域并行运行
3. **历史恢复（History Restoration）**：
   - 浅层历史（H）：恢复到最后激活的直接子状态
   - 深层历史（H*）：恢复到最后激活的任意深度子状态
4. **入口/出口动作（Entry/Exit Actions）**：进入/退出状态时执行的操作

### 应用场景 / Application Scenarios

- **网络协议**：TCP 连接管理、WebSocket 状态
- **UI 状态**：表单验证、页面导航
- **游戏开发**：角色行为、游戏流程
- **工作流引擎**：订单处理、审批流程
- **嵌入式系统**：设备控制、通信协议
- **文件处理**：上传/下载状态管理

---

## 快速开始 / Quick Start

### 添加依赖 / Add to Cargo.toml

```toml
[dependencies]
state-machine = { path = "../state-machine" }
```

### 基本用法 / Basic Usage

```rust
use state_machine::{StateMachine, State, Event, Transition};

// 定义状态 / Define states
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum LightState {
    Off,
    On,
}

// 定义事件 / Define events
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum LightEvent {
    TurnOn,
    TurnOff,
}

// 实现 trait / Implement traits
impl State for LightState {}
impl Event for LightEvent {}

fn main() {
    // 创建状态机 / Create a state machine
    let mut sm = StateMachine::new(LightState::Off);

    // 添加转换 / Add transitions
    sm.add_transition(Transition::new(
        LightState::Off,
        LightState::On,
        LightEvent::TurnOn,
    ));
    sm.add_transition(Transition::new(
        LightState::On,
        LightState::Off,
        LightEvent::TurnOff,
    ));

    // 处理事件 / Process events
    sm.process_event(LightEvent::TurnOn).unwrap();
    assert_eq!(sm.current_state(), &LightState::On);

    sm.process_event(LightEvent::TurnOff).unwrap();
    assert_eq!(sm.current_state(), &LightState::Off);
}
```

### 使用守卫和动作 / With Guards and Actions

```rust
use state_machine::{StateMachine, State, Event, Transition};

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum DoorState {
    Locked,
    Unlocked,
    Open,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum DoorEvent {
    Unlock,
    Lock,
    Open,
    Close,
}

impl State for DoorState {}
impl Event for DoorEvent {}

fn main() {
    let mut sm = StateMachine::new(DoorState::Locked);

    // 带守卫和动作的转换
    sm.add_transition(
        Transition::new(DoorState::Locked, DoorState::Unlocked, DoorEvent::Unlock)
            .with_guard(|_from, _to, _event| {
                // 检查钥匙是否有效 / Check if key is valid
                true
            })
            .with_action(|_from, _to, _event| {
                println!("Door unlocked!");
                Ok(())
            })
            .with_description("Unlock the door"),
    );

    sm.process_event(DoorEvent::Unlock).unwrap();
}
```

### 层次状态机 / Hierarchical State Machine

```rust
use state_machine::hierarchical::*;
use state_machine::{State, Event};

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum FileState {
    Idle,
    Transferring,
    Complete,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum FileEvent {
    StartTransfer,
    TransferComplete,
}

impl State for FileState {}
impl Event for FileEvent {}

fn main() {
    // 创建带有正交区域的复合状态
    let composite = CompositeState::new("file_transfer", "File Transfer")
        .with_region(
            RegionBuilder::new()
                .with_initial_state(FileState::Idle, "idle")
                .build()
        )
        .with_history(HistoryType::Deep)
        .with_entry_action(|state, event| {
            println!("Starting file transfer: {:?}", state);
            Ok(())
        })
        .with_exit_action(|state, event| {
            println!("File transfer ended: {:?}", state);
            Ok(())
        });

    let hsm = HStateMachine::new(HState::composite(composite));
}
```

---

## 运行示例 / Run Examples

### 交通灯示例 / Traffic Light Example

```bash
cd projects/state-machine
cargo run --example traffic_light
```

模拟交通灯的状态转换：Off → Red → Green → Yellow → Red → ...

### 文件传输示例 / File Transfer Example

```bash
cargo run --example file_transfer
```

演示文件传输的完整生命周期：准备 → 传输 → 完成/错误 → 重试

### 订单处理示例 / Order Processing Example

```bash
cargo run --example order_processing
```

演示订单处理工作流：创建 → 验证 → 支付 → 发货 → 交付/取消/退款

### 层次状态机示例 / Hierarchical State Machine Example

```bash
cargo run --example hierarchical_sm
```

演示层次状态机：网络连接的生命周期管理，包括超时、重试、认证错误恢复

---

## 运行测试 / Run Tests

```bash
cargo test
```

---

## 项目结构 / Project Structure

```
state-machine/
├── src/
│   ├── lib.rs              # 主入口，导出所有公共 API
│   ├── state_machine.rs    # 核心状态机引擎
│   ├── transition.rs       # 状态转换定义（含构建器模式）
│   ├── error.rs            # 错误类型定义
│   ├── history.rs          # 历史记录管理
│   └── hierarchical/       # 层次状态机模块
│       ├── mod.rs          # 层次状态机核心
│       ├── region.rs       # 正交区域实现
│       ├── state_entry.rs  # 入口/出口动作
│       └── transition_table.rs  # 层次转换表
├── examples/
│   ├── traffic_light.rs    # 交通灯示例
│   ├── file_transfer.rs    # 文件传输示例
│   ├── order_processing.rs # 订单处理示例
│   └── hierarchical_sm.rs  # 层次状态机示例
├── tests/
│   └── integration_tests.rs  # 集成测试
├── Cargo.toml
└── README.md
```

---

## API 参考 / API Reference

### StateMachine<S, E>

| 方法 | 描述 |
|------|------|
| `new(initial_state)` | 创建新的状态机 |
| `new_without_history(initial_state)` | 创建不记录历史的狀態机 |
| `with_history_capacity(capacity)` | 设置历史容量 |
| `on_state_change(callback)` | 设置状态变化回调 |
| `on_transition_failed(callback)` | 设置转换失败回调 |
| `add_transition(transition)` | 添加转换 |
| `add_transitions(transitions)` | 批量添加转换 |
| `process_event(event)` | 处理事件 |
| `current_state()` | 获取当前状态 |
| `set_state(state)` | 直接设置状态 |
| `can_process_event(event)` | 检查是否可以处理事件 |
| `possible_events()` | 获取当前状态可能的所有事件 |
| `history()` | 获取历史记录管理器 |
| `format_transitions()` | 格式化所有转换 |
| `format_graph()` | 格式化转换图 |

### Transition<S, E>

| 方法 | 描述 |
|------|------|
| `new(from, to, event)` | 创建新转换 |
| `with_guard(guard)` | 添加守卫条件 |
| `with_action(action)` | 添加动作 |
| `with_description(desc)` | 添加描述 |

### HStateMachine<S, E>

| 方法 | 描述 |
|------|------|
| `new(root_state)` | 创建新的层次状态机 |
| `add_transition(transition)` | 添加转换 |
| `process_event(event)` | 处理事件 |
| `current_state()` | 获取当前状态 |
| `format_hierarchy()` | 格式化状态层次结构 |

### CompositeState

| 方法 | 描述 |
|------|------|
| `new(id, name)` | 创建复合状态 |
| `with_region(region)` | 添加正交区域 |
| `with_entry_action(action)` | 设置入口动作 |
| `with_exit_action(action)` | 设置出口动作 |
| `with_history(type)` | 设置历史类型 |

---

## 测试 / Testing

```bash
# 运行所有测试
cargo test

# 运行特定模块测试
cargo test --lib

# 运行集成测试
cargo test --test integration_tests

# 运行层次状态机测试
cargo test hierarchical
```

---

## 状态机理论参考 / Theory References

1. **David Harel**, "Statecharts: A Visual Formalism for Complex Systems", Science of Computer Programming, 1987
2. **Erich Gamma et al.**, "Design Patterns: Elements of Reusable Object-Oriented Software", State Machine pattern
3. **UML 2.5 Specification**, State Machine diagrams and semantics
4. **Michael Huzika**, "An Introduction to Statecharts", 2016

---

## License

MIT
