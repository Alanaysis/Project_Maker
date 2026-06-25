# 状态机框架架构设计

## 1. 架构概述

状态机框架采用分层架构设计，将核心功能、扩展功能和应用层分离，确保代码的可维护性和可扩展性。

```
┌─────────────────────────────────────────────────────────────┐
│                    应用层 (Application)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  订单管理    │  │  工作流引擎  │  │  游戏AI     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                    扩展层 (Extensions)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  序列化      │  │  可视化      │  │  持久化     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                    核心层 (Core)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  StateMachine│  │  Transition │  │  Guard      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  State      │  │  Event      │  │  Action     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                    基础层 (Foundation)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Error      │  │  History    │  │  Types      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 2. 模块设计

### 2.1 基础层（Foundation）

#### 2.1.1 错误处理模块（error.py）

定义框架的所有异常类型：

```python
StateMachineError          # 基础异常
├── TransitionError        # 转换错误
│   └── GuardRejectedError # 守卫拒绝
├── InvalidStateError      # 无效状态
├── InvalidEventError      # 无效事件
├── ActionError            # 动作错误
└── ConfigurationError     # 配置错误
```

**设计原则**：
- 每个异常类型都有明确的语义
- 异常携带足够的上下文信息
- 支持异常链（原始异常）

#### 2.1.2 历史记录模块（history.py）

管理状态转换历史：

```python
HistoryEntry           # 单个历史记录
├── timestamp          # 时间戳
├── from_state         # 源状态
├── to_state           # 目标状态
├── event              # 触发事件
├── success            # 是否成功
├── duration           # 持续时间
├── context            # 上下文数据
└── error              # 错误信息

HistoryManager         # 历史管理器
├── entries()          # 获取所有记录
├── entries_for_state()# 按状态过滤
├── entries_for_event()# 按事件过滤
├── successful_entries()# 成功记录
└── failed_entries()   # 失败记录

HistoryState           # 历史状态
├── save()             # 保存状态
└── get()              # 获取状态
```

### 2.2 核心层（Core）

#### 2.2.1 状态模块（state.py）

定义状态的基类和层次状态：

```python
State                  # 基础状态
├── name               # 状态名称
├── metadata           # 元数据
├── entry_actions      # 进入动作列表
├── exit_actions       # 退出动作列表
├── on_enter()         # 执行进入动作
└── on_exit()          # 执行退出动作

HierarchicalState      # 层次状态（继承State）
├── sub_states         # 子状态字典
├── initial_state      # 初始子状态
├── current_sub_state  # 当前子状态
├── history_state      # 历史状态
├── use_history        # 是否使用历史
├── add_sub_state()    # 添加子状态
├── activate()         # 激活状态
├── deactivate()       # 停用状态
└── transition_to()    # 转换到子状态
```

#### 2.2.2 事件模块（event.py）

定义事件：

```python
Event                  # 事件
├── name               # 事件名称
├── data               # 事件数据
└── with_data()        # 创建带数据的事件

EventBuilder           # 事件构建器
├── with_data()        # 添加数据
└── build()            # 构建事件
```

#### 2.2.3 守卫模块（guard.py）

定义守卫条件：

```python
Guard                  # 守卫基类
├── check()            # 检查条件
├── __and__()          # AND组合
├── __or__()           # OR组合
└── __invert__()       # NOT取反

FunctionGuard          # 函数守卫
├── func               # 守卫函数
└── name               # 守卫名称

AndGuard               # AND守卫
OrGuard                # OR守卫
NotGuard               # NOT守卫
AlwaysTrueGuard        # 总是True
AlwaysFalseGuard       # 总是False
```

#### 2.2.4 动作模块（action.py）

定义动作：

```python
Action                 # 动作基类
├── execute()          # 执行动作

FunctionAction         # 函数动作
EntryAction            # 进入动作
ExitAction             # 退出动作
TransitionAction       # 转换动作
CompositeAction        # 组合动作
```

#### 2.2.5 转换模块（transition.py）

定义转换：

```python
Transition             # 转换
├── from_state         # 源状态
├── to_state           # 目标状态
├── event              # 触发事件
├── guard              # 守卫条件
├── action             # 转换动作
├── description        # 描述
├── can_transition()   # 检查是否可转换
├── execute()          # 执行转换
└── matches()          # 匹配检查

TransitionBuilder      # 转换构建器
├── from_state()       # 设置源状态
├── to_state()         # 设置目标状态
├── on()               # 设置事件
├── when()             # 设置守卫
├── do()               # 设置动作
├── describe()         # 设置描述
└── build()            # 构建转换
```

#### 2.2.6 状态机模块（state_machine.py）

核心状态机实现：

```python
StateMachine           # 有限状态机
├── current_state      # 当前状态
├── states             # 所有状态
├── events             # 所有事件
├── transitions        # 所有转换
├── history            # 历史管理器
├── context            # 上下文数据
├── add_transition()   # 添加转换
├── process_event()    # 处理事件
├── can_process_event()# 检查事件
├── possible_events()  # 可能事件
├── on_state_change()  # 状态变化回调
├── on_transition_failed()# 失败回调
└── reset()            # 重置状态机
```

#### 2.2.7 层次状态机模块（hierarchical.py）

层次状态机实现：

```python
HierarchicalStateMachine# 层次状态机
├── current_state      # 当前状态（最深层）
├── state_stack        # 状态栈
├── root_state         # 根状态
├── process_event()    # 处理事件（支持冒泡）
├── enter_sub_state()  # 进入子状态
├── get_history_state()# 获取历史状态
└── set_history_state()# 设置历史状态
```

### 2.3 扩展层（Extensions）

#### 2.3.1 序列化模块

支持状态机的序列化和反序列化：

```python
StateMachineSerializer # 序列化器
├── serialize()        # 序列化为JSON/YAML
├── deserialize()      # 从JSON/YAML反序列化
└── to_dict()          # 转换为字典
```

#### 2.3.2 可视化模块

生成状态图：

```python
StateMachineVisualizer # 可视化器
├── to_dot()           # 生成DOT格式
├── to_mermaid()       # 生成Mermaid格式
├── to_plantuml()      # 生成PlantUML格式
└── render()           # 渲染为图片
```

### 2.4 应用层（Application）

提供实际应用场景的实现示例：
- 订单状态管理
- 工作流引擎
- 游戏AI

## 3. 数据流

### 3.1 事件处理流程

```
用户调用 process_event(event)
        │
        ▼
┌───────────────────┐
│  查找匹配转换      │
│  (from_state, event)│
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  检查守卫条件      │
│  guard.check()     │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  执行退出动作      │
│  from_state.on_exit()│
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  执行转换动作      │
│  transition.execute()│
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  更新当前状态      │
│  current_state = to│
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  执行进入动作      │
│  to_state.on_enter()│
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  记录历史          │
│  history.push()    │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  触发回调          │
│  on_state_change() │
└───────────────────┘
```

### 3.2 层次状态机事件处理

```
process_event(event, bubble=True)
        │
        ▼
┌───────────────────┐
│  从当前状态开始    │
│  向上查找转换      │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  找到匹配转换？    │
│  且守卫通过？      │
└───────────────────┘
        │
        ▼ (是)
┌───────────────────┐
│  退出当前状态栈    │
│  中的所有状态      │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  进入新状态        │
│  （包括子状态）    │
└───────────────────┘
        │
        ▼ (否且bubble=True)
┌───────────────────┐
│  向父状态冒泡      │
│  继续查找          │
└───────────────────┘
```

## 4. 接口设计

### 4.1 核心接口

```python
# 状态接口
class State(ABC):
    @abstractmethod
    def on_enter(self, context): pass
    
    @abstractmethod
    def on_exit(self, context): pass

# 守卫接口
class Guard(ABC):
    @abstractmethod
    def check(self, from_state, to_state, event, context) -> bool: pass

# 动作接口
class Action(ABC):
    @abstractmethod
    def execute(self, from_state, to_state, event, context) -> Any: pass
```

### 4.2 回调接口

```python
# 状态变化回调
def on_state_change(from_state: State, to_state: State, event: Event) -> None

# 转换失败回调
def on_transition_failed(from_state: State, event: Event, error: Exception) -> None

# 事件处理回调
def on_event_processed(event: Event, success: bool) -> None
```

## 5. 扩展点

### 5.1 自定义守卫

```python
class CustomGuard(Guard):
    def check(self, from_state, to_state, event, context):
        # 自定义逻辑
        return True
```

### 5.2 自定义动作

```python
class CustomAction(Action):
    def execute(self, from_state, to_state, event, context):
        # 自定义逻辑
        pass
```

### 5.3 自定义状态

```python
class CustomState(State):
    def on_enter(self, context):
        # 自定义进入逻辑
        pass
    
    def on_exit(self, context):
        # 自定义退出逻辑
        pass
```

## 6. 性能考虑

### 6.1 时间复杂度

- **状态查找**：O(1) - 使用集合
- **转换查找**：O(n) - n为转换数量
- **守卫检查**：O(g) - g为守卫复杂度
- **动作执行**：O(a) - a为动作复杂度

### 6.2 空间复杂度

- **状态存储**：O(s) - s为状态数量
- **转换存储**：O(t) - t为转换数量
- **历史记录**：O(h) - h为历史容量

### 6.3 优化策略

- **索引优化**：为常用查询建立索引
- **缓存优化**：缓存守卫计算结果
- **懒加载**：按需加载历史记录

## 7. 测试策略

### 7.1 单元测试

- 状态创建和比较
- 事件创建和数据处理
- 守卫条件组合
- 动作执行
- 转换匹配和执行

### 7.2 集成测试

- 完整的状态机生命周期
- 层次状态机的嵌套
- 历史状态的保存和恢复
- 错误处理和恢复

### 7.3 性能测试

- 大量状态和转换的处理
- 高频率事件处理
- 内存使用情况

## 8. 未来扩展

### 8.1 计划功能

- 并发状态机支持
- 状态机可视化工具
- 状态机序列化
- 状态机调试器

### 8.2 性能优化

- JIT编译状态机
- 状态机缓存
- 异步事件处理
