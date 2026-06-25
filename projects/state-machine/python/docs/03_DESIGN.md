# 状态机框架详细设计

## 1. 类设计

### 1.1 状态类层次

```python
State (ABC)
├── name: str
├── metadata: Dict[str, Any]
├── entry_actions: List[Callable]
├── exit_actions: List[Callable]
├── add_entry_action(action: Callable)
├── add_exit_action(action: Callable)
├── on_enter(context: Optional[Dict])
└── on_exit(context: Optional[Dict])

HierarchicalState (State)
├── sub_states: Dict[str, State]
├── initial_state: Optional[str]
├── current_sub_state: Optional[str]
├── history_state: Optional[str]
├── use_history: bool
├── add_sub_state(state: State)
├── remove_sub_state(state_name: str)
├── activate() -> State
├── deactivate()
└── transition_to(state_name: str) -> Optional[State]
```

### 1.2 事件类设计

```python
Event (frozen=True)
├── name: str
├── data: Dict[str, Any]
├── __eq__(other) -> bool
├── __hash__() -> int
└── with_data(**kwargs) -> Event

EventBuilder
├── _name: str
├── _data: Dict[str, Any]
├── with_data(**kwargs) -> EventBuilder
├── with_key_value(key, value) -> EventBuilder
└── build() -> Event
```

### 1.3 守卫类层次

```python
Guard (ABC)
├── check(from_state, to_state, event, context) -> bool
├── __and__(other) -> Guard
├── __or__(other) -> Guard
└── __invert__() -> Guard

FunctionGuard (Guard)
├── func: Callable
├── name: Optional[str]
└── check(...)

AndGuard (Guard)
├── left: Guard
├── right: Guard
└── check(...)

OrGuard (Guard)
├── left: Guard
├── right: Guard
└── check(...)

NotGuard (Guard)
├── guard: Guard
└── check(...)

AlwaysTrueGuard (Guard)
└── check(...)

AlwaysFalseGuard (Guard)
└── check(...)
```

### 1.4 动作类层次

```python
Action (ABC)
├── execute(from_state, to_state, event, context) -> Optional[Any]

FunctionAction (Action)
├── func: Callable
├── name: Optional[str]
└── execute(...)

EntryAction (Action)
├── _func: Callable[[State, Optional[Dict]], Any]
├── _name: Optional[str]
└── execute(...)

ExitAction (Action)
├── _func: Callable[[State, Optional[Dict]], Any]
├── _name: Optional[str]
└── execute(...)

TransitionAction (Action)
├── _func: Callable
├── _name: Optional[str]
└── execute(...)

CompositeAction (Action)
├── _actions: List[Action]
├── add(action: Action)
└── execute(...)
```

### 1.5 转换类设计

```python
Transition
├── from_state: State
├── to_state: State
├── event: Event
├── guard: Optional[Guard]
├── action: Optional[Action]
├── description: Optional[str]
├── can_transition(context) -> bool
├── execute(context) -> Optional[Any]
└── matches(from_state, event) -> bool

TransitionBuilder
├── _from_state: Optional[State]
├── _to_state: Optional[State]
├── _event: Optional[Event]
├── _guard: Optional[Guard]
├── _action: Optional[Action]
├── _description: Optional[str]
├── from_state(state) -> TransitionBuilder
├── to_state(state) -> TransitionBuilder
├── to(state) -> TransitionBuilder
├── on(event) -> TransitionBuilder
├── when(guard) -> TransitionBuilder
├── do(action) -> TransitionBuilder
├── describe(description) -> TransitionBuilder
└── build() -> Transition
```

### 1.6 历史管理类设计

```python
HistoryEntry
├── timestamp: datetime
├── from_state: State
├── to_state: State
├── event: Event
├── success: bool
├── duration: Optional[float]
├── context: Optional[Dict]
└── error: Optional[Exception]

HistoryManager
├── _max_entries: int
├── _entries: Deque[HistoryEntry]
├── _last_state_change: Optional[datetime]
├── max_entries: int (property)
├── push(entry: HistoryEntry)
├── last() -> Optional[HistoryEntry]
├── first() -> Optional[HistoryEntry]
├── len() -> int
├── is_empty() -> bool
├── entries() -> List[HistoryEntry]
├── entries_reversed() -> List[HistoryEntry]
├── entries_for_state(state) -> List[HistoryEntry]
├── entries_for_event(event) -> List[HistoryEntry]
├── successful_entries() -> List[HistoryEntry]
├── failed_entries() -> List[HistoryEntry]
├── clear()
├── format_all() -> str
└── format_summary() -> str

HistoryState
├── _states: Dict[str, str]
├── save(parent_state: str, sub_state: str)
├── get(parent_state: str) -> Optional[str]
└── clear(parent_state: Optional[str])
```

### 1.7 状态机类设计

```python
StateMachine
├── _current_state: State
├── _transitions: List[Transition]
├── _states: Set[State]
├── _events: Set[Event]
├── _enable_history: bool
├── _history: Optional[HistoryManager]
├── _history_state: HistoryState
├── _on_state_change: Optional[Callable]
├── _on_transition_failed: Optional[Callable]
├── _on_event_processed: Optional[Callable]
├── _context: Dict[str, Any]
├── current_state: State (property)
├── states: Set[State] (property)
├── events: Set[Event] (property)
├── transitions: List[Transition] (property)
├── history: Optional[HistoryManager] (property)
├── context: Dict[str, Any] (property)
├── add_transition(transition: Transition)
├── add_transitions(transitions: List[Transition])
├── on_state_change(callback: Callable)
├── on_transition_failed(callback: Callable)
├── on_event_processed(callback: Callable)
├── process_event(event, context) -> bool
├── can_process_event(event) -> bool
├── possible_events() -> List[Event]
├── possible_transitions() -> List[Transition]
├── set_state(state: State)
├── reset(state: Optional[State])
├── format_transitions() -> str
└── format_graph() -> str
```

### 1.8 层次状态机类设计

```python
HierarchicalStateMachine
├── _root_state: State
├── _state_stack: List[State]
├── _transitions: List[Transition]
├── _states: Set[State]
├── _events: Set[Event]
├── _enable_history: bool
├── _history: Optional[HistoryManager]
├── _history_state: HistoryState
├── _on_state_change: Optional[Callable]
├── _on_transition_failed: Optional[Callable]
├── _context: Dict[str, Any]
├── current_state: State (property)
├── state_stack: List[State] (property)
├── root_state: State (property)
├── states: Set[State] (property)
├── transitions: List[Transition] (property)
├── history: Optional[HistoryManager] (property)
├── context: Dict[str, Any] (property)
├── add_transition(transition: Transition)
├── add_transitions(transitions: List[Transition])
├── on_state_change(callback: Callable)
├── on_transition_failed(callback: Callable)
├── process_event(event, context, bubble) -> bool
├── enter_sub_state(state_name: str) -> bool
├── can_process_event(event, bubble) -> bool
├── possible_events(bubble) -> List[Event]
├── get_history_state(parent_state_name) -> Optional[str]
├── set_history_state(parent_state_name, sub_state_name)
├── reset(state: Optional[State])
├── format_hierarchy() -> str
└── format_transitions() -> str
```

## 2. 状态设计模式

### 2.1 简单状态

```python
# 创建状态
idle = State("Idle")
running = State("Running", speed=100)

# 添加动作
idle.add_entry_action(lambda s, c: print("Entering idle"))
idle.add_exit_action(lambda s, c: print("Exiting idle"))
```

### 2.2 层次状态

```python
# 创建层次状态
active = HierarchicalState("Active", use_history=True)

# 添加子状态
processing = State("Processing")
waiting = State("Waiting")
active.add_sub_state(processing)
active.add_sub_state(waiting)

# 设置初始状态
active.initial_state = "Processing"
```

### 2.3 并发状态（概念设计）

```python
# 并发状态容器
class ConcurrentStates:
    def __init__(self):
        self._regions: List[StateMachine] = []
    
    def add_region(self, sm: StateMachine):
        self._regions.append(sm)
    
    def process_event(self, event):
        results = []
        for region in self._regions:
            results.append(region.process_event(event))
        return any(results)
```

## 3. 转换设计模式

### 3.1 简单转换

```python
transition = Transition(
    from_state=idle,
    to_state=running,
    event=start_event
)
```

### 3.2 带守卫的转换

```python
transition = Transition(
    from_state=idle,
    to_state=running,
    event=start_event,
    guard=FunctionGuard(lambda f, t, e, c: c.get("authorized", False))
)
```

### 3.3 带动作的转换

```python
transition = Transition(
    from_state=idle,
    to_state=running,
    event=start_event,
    action=FunctionAction(lambda f, t, e, c: print("Starting..."))
)
```

### 3.4 使用构建器

```python
transition = (TransitionBuilder()
    .from_state(idle)
    .to_state(running)
    .on(start_event)
    .when(lambda f, t, e, c: True)
    .do(lambda f, t, e, c: print("Started"))
    .describe("Start the system")
    .build())
```

## 4. 守卫设计模式

### 4.1 函数守卫

```python
def has_permission(from_state, to_state, event, context):
    return context.get("role") == "admin"

guard = FunctionGuard(has_permission, "admin_check")
```

### 4.2 组合守卫

```python
is_admin = context_has("role", "admin")
has_token = context_has("token")
can_access = is_admin & has_token  # AND

is_guest = context_has("role", "guest")
is_public = context_has("public", True)
can_view = is_guest | is_public  # OR

is_not_blocked = ~context_has("blocked", True)
```

### 4.3 便捷守卫

```python
always_ok = always_true()
never_ok = always_false()
has_data = context_has("data")
is_idle_state = state_is("Idle")
```

## 5. 动作设计模式

### 5.1 函数动作

```python
def log_transition(from_state, to_state, event, context):
    print(f"{from_state} -> {to_state} on {event}")

action = FunctionAction(log_transition, "logger")
```

### 5.2 进入/退出动作

```python
def on_enter_state(state, context):
    print(f"Entered {state.name}")

def on_exit_state(state, context):
    print(f"Exited {state.name}")

entry = EntryAction(on_enter_state)
exit = ExitAction(on_exit_state)
```

### 5.3 组合动作

```python
composite = CompositeAction([
    FunctionAction(lambda f, t, e, c: print("Step 1")),
    FunctionAction(lambda f, t, e, c: print("Step 2")),
    FunctionAction(lambda f, t, e, c: print("Step 3")),
])
```

### 5.4 便捷动作

```python
log = log_action("Transition: {from_state} -> {to_state}")
update = update_context_action("status", "active")
```

## 6. 错误处理设计

### 6.1 异常层次

```python
StateMachineError (Exception)
├── details: Optional[Any]

TransitionError (StateMachineError)
├── from_state: Optional[Any]
├── to_state: Optional[Any]
├── event: Optional[Any]

GuardRejectedError (TransitionError)
├── guard: Optional[Any]

InvalidStateError (StateMachineError)
├── state: Optional[Any]

InvalidEventError (StateMachineError)
├── event: Optional[Any]
├── state: Optional[Any]

ActionError (StateMachineError)
├── action: Optional[Any]
├── original_error: Optional[Exception]

ConfigurationError (StateMachineError)
├── component: Optional[str]
```

### 6.2 错误处理策略

1. **转换失败**：返回False，触发on_transition_failed回调
2. **守卫拒绝**：返回False，记录到历史
3. **动作异常**：捕获异常，触发on_transition_failed回调
4. **配置错误**：抛出ConfigurationError

## 7. 上下文设计

### 7.1 上下文传递

```python
# 实例上下文
sm.context = {"global_key": "global_value"}

# 事件上下文
sm.process_event(event, {"local_key": "local_value"})

# 合并上下文
merged = {**sm.context, **event_context}
```

### 7.2 上下文使用

```python
# 在守卫中使用
def has_data(from_state, to_state, event, context):
    return "data" in context

# 在动作中使用
def process_data(from_state, to_state, event, context):
    data = context.get("data")
    # 处理数据
```

## 8. 回调设计

### 8.1 状态变化回调

```python
def on_state_change(from_state, to_state, event):
    print(f"State changed: {from_state} -> {to_state}")

sm.on_state_change(on_state_change)
```

### 8.2 转换失败回调

```python
def on_failure(from_state, event, error):
    print(f"Transition failed: {error}")

sm.on_transition_failed(on_failure)
```

### 8.3 事件处理回调

```python
def on_processed(event, success):
    print(f"Event {event}: {'success' if success else 'failed'}")

sm.on_event_processed(on_processed)
```

## 9. 序列化设计（扩展）

### 9.1 状态机序列化

```python
class StateMachineSerializer:
    def serialize(self, sm: StateMachine) -> Dict:
        return {
            "current_state": str(sm.current_state),
            "states": [str(s) for s in sm.states],
            "transitions": [
                {
                    "from": str(t.from_state),
                    "to": str(t.to_state),
                    "event": str(t.event),
                    "description": t.description
                }
                for t in sm.transitions
            ],
            "context": sm.context
        }
    
    def deserialize(self, data: Dict) -> StateMachine:
        # 反序列化逻辑
        pass
```

## 10. 可视化设计（扩展）

### 10.1 DOT格式输出

```python
class StateMachineVisualizer:
    def to_dot(self, sm: StateMachine) -> str:
        lines = ["digraph StateMachine {"]
        lines.append('  rankdir=LR;')
        
        # 添加节点
        for state in sm.states:
            shape = "doublecircle" if state == sm.current_state else "circle"
            lines.append(f'  "{state}" [shape={shape}];')
        
        # 添加边
        for t in sm.transitions:
            label = str(t.event)
            if t.description:
                label = t.description
            lines.append(f'  "{t.from_state}" -> "{t.to_state}" [label="{label}"];')
        
        lines.append("}")
        return "\n".join(lines)
```

## 11. 测试设计

### 11.1 单元测试覆盖

- 状态创建、比较、哈希
- 事件创建、数据处理
- 守卫条件、组合逻辑
- 动作执行、错误处理
- 转换匹配、执行

### 11.2 集成测试场景

- 完整生命周期
- 层次状态嵌套
- 历史状态保存/恢复
- 错误恢复

### 11.3 性能测试指标

- 转换执行时间
- 内存使用情况
- 并发处理能力

## 12. 接口契约

### 12.1 前置条件

- 状态名称必须唯一
- 转换的源状态和目标状态必须存在
- 守卫和动作必须可调用

### 12.2 后置条件

- 状态转换后，current_state更新
- 历史记录被正确添加
- 回调被正确触发

### 12.3 不变式

- 状态机始终有一个当前状态
- 转换不会修改状态机的结构
- 历史记录不会超过最大容量
