# 状态机框架实现指南

## 1. 实现概述

本文档详细描述状态机框架的实现细节，包括核心算法、数据结构和关键实现决策。

## 2. 核心实现

### 2.1 状态实现

#### 2.1.1 基础状态

```python
class State(ABC):
    def __init__(self, name: str, **kwargs: Any) -> None:
        self._name = name
        self._metadata = kwargs
        self._entry_actions = []
        self._exit_actions = []
    
    def on_enter(self, context=None):
        for action in self._entry_actions:
            action(self, context)
    
    def on_exit(self, context=None):
        for action in self._exit_actions:
            action(self, context)
```

**关键点**：
- 使用ABC定义抽象基类
- 支持元数据存储
- 动作列表支持多个动作

#### 2.1.2 层次状态

```python
class HierarchicalState(State):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self._sub_states = {}
        self._initial_state = None
        self._current_sub_state = None
        self._history_state = None
        self._use_history = False
    
    def activate(self):
        if self._use_history and self._history_state:
            self._current_sub_state = self._history_state
        elif self._initial_state:
            self._current_sub_state = self._initial_state
    
    def deactivate(self):
        if self._current_sub_state:
            self._history_state = self._current_sub_state
            self._current_sub_state = None
```

**关键点**：
- 继承基础状态
- 管理子状态字典
- 支持历史状态记录

### 2.2 事件实现

```python
@dataclass(frozen=True)
class Event:
    name: str
    data: Dict[str, Any] = field(default_factory=dict, hash=False)
    
    def __eq__(self, other):
        if not isinstance(other, Event):
            return NotImplemented
        return self.name == other.name
    
    def __hash__(self):
        return hash(self.name)
```

**关键点**：
- 使用frozen dataclass确保不可变性
- data字段不参与哈希计算
- 基于name进行相等性比较

### 2.3 守卫实现

#### 2.3.1 函数守卫

```python
@dataclass
class FunctionGuard(Guard):
    func: Callable
    name: Optional[str] = None
    
    def check(self, from_state, to_state, event, context=None):
        return self.func(from_state, to_state, event, context)
```

#### 2.3.2 组合守卫

```python
class AndGuard(Guard):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    
    def check(self, from_state, to_state, event, context=None):
        return (self.left.check(from_state, to_state, event, context) and
                self.right.check(from_state, to_state, event, context))
```

**关键点**：
- 使用组合模式实现逻辑运算
- 支持任意深度的嵌套
- 延迟求值

### 2.4 动作实现

```python
@dataclass
class FunctionAction(Action):
    func: Callable
    name: Optional[str] = None
    
    def execute(self, from_state, to_state, event, context=None):
        return self.func(from_state, to_state, event, context)
```

**关键点**：
- 简单封装可调用对象
- 支持返回值
- 可选的名称用于调试

### 2.5 转换实现

```python
class Transition:
    def __init__(self, from_state, to_state, event, 
                 guard=None, action=None, description=None):
        self.from_state = from_state
        self.to_state = to_state
        self.event = event
        self.guard = guard or always_true()
        self.action = action
        self.description = description
    
    def can_transition(self, context=None):
        return self.guard.check(self.from_state, self.to_state, self.event, context)
    
    def execute(self, context=None):
        if self.action:
            return self.action.execute(self.from_state, self.to_state, self.event, context)
    
    def matches(self, from_state, event):
        return self.from_state == from_state and self.event == event
```

**关键点**：
- 默认守卫总是通过
- 动作可选
- 匹配基于状态和事件

### 2.6 状态机实现

#### 2.6.1 事件处理核心算法

```python
def process_event(self, event, context=None):
    # 合并上下文
    merged_context = {**self._context}
    if context:
        merged_context.update(context)
    
    # 查找匹配转换
    matching_transitions = [
        t for t in self._transitions
        if t.matches(self._current_state, event)
    ]
    
    if not matching_transitions:
        # 无匹配转换
        error = InvalidEventError(event, self._current_state)
        self._handle_failure(error, merged_context)
        return False
    
    # 尝试每个匹配转换
    for transition in matching_transitions:
        if transition.can_transition(merged_context):
            return self._execute_transition(transition, merged_context)
    
    # 所有守卫拒绝
    error = GuardRejectedError(...)
    self._handle_failure(error, merged_context)
    return False
```

#### 2.6.2 转换执行

```python
def _execute_transition(self, transition, context):
    from_state = self._current_state
    to_state = transition.to_state
    event = transition.event
    
    try:
        # 执行退出动作
        from_state.on_exit(context)
        
        # 执行转换动作
        transition.execute(context)
        
        # 更新状态
        self._current_state = to_state
        
        # 执行进入动作
        to_state.on_enter(context)
        
        # 记录历史
        self._record_history(from_state, to_state, event, True, context)
        
        # 触发回调
        self._notify_state_change(from_state, to_state, event)
        
        return True
        
    except Exception as e:
        # 处理异常
        self._handle_action_error(e, from_state, to_state, event, context)
        return False
```

#### 2.6.3 转换查找优化

```python
# 使用索引优化查找
self._transition_index = {}  # {(from_state, event): [transitions]}

def _index_transition(self, transition):
    key = (transition.from_state, transition.event)
    if key not in self._transition_index:
        self._transition_index[key] = []
    self._transition_index[key].append(transition)

def _find_transitions(self, from_state, event):
    key = (from_state, event)
    return self._transition_index.get(key, [])
```

### 2.7 层次状态机实现

#### 2.7.1 事件冒泡

```python
def process_event(self, event, context=None, bubble=True):
    merged_context = self._merge_context(context)
    
    # 从当前状态向上查找
    for i in range(len(self._state_stack) - 1, -1, -1):
        current = self._state_stack[i]
        
        # 查找匹配转换
        matching = self._find_transitions(current, event)
        
        for transition in matching:
            if transition.can_transition(merged_context):
                return self._execute_hierarchical_transition(
                    transition, merged_context, i
                )
        
        if not bubble:
            break
    
    return False
```

#### 2.7.2 层次转换执行

```python
def _execute_hierarchical_transition(self, transition, context, level):
    from_state = self._state_stack[level]
    to_state = transition.to_state
    
    # 退出当前状态栈中的所有状态
    for i in range(len(self._state_stack) - 1, level - 1, -1):
        self._state_stack[i].on_exit(context)
    
    # 截断状态栈
    self._state_stack = self._state_stack[:level]
    
    # 执行转换动作
    transition.execute(context)
    
    # 进入新状态
    to_state.on_enter(context)
    self._state_stack.append(to_state)
    
    # 如果是层次状态，进入子状态
    if isinstance(to_state, HierarchicalState):
        sub_state = to_state.current_sub_state
        if sub_state:
            sub_state.on_enter(context)
            self._state_stack.append(sub_state)
    
    return True
```

## 3. 数据结构设计

### 3.1 状态存储

```python
# 使用集合存储状态，O(1)查找
self._states: Set[State] = set()

# 使用字典存储层次状态的子状态
self._sub_states: Dict[str, State] = {}
```

### 3.2 转换存储

```python
# 使用列表存储转换（保持顺序）
self._transitions: List[Transition] = []

# 可选：使用索引优化查找
self._transition_index: Dict[Tuple[State, Event], List[Transition]] = {}
```

### 3.3 历史记录存储

```python
# 使用双端队列，支持固定容量
self._entries: Deque[HistoryEntry] = deque(maxlen=max_entries)
```

### 3.4 状态栈存储

```python
# 使用列表实现栈
self._state_stack: List[State] = []
```

## 4. 算法实现

### 4.1 转换匹配算法

```python
def matches(self, from_state, event):
    # 简单相等性比较
    return self.from_state == from_state and self.event == event
```

**时间复杂度**：O(1)

### 4.2 守卫检查算法

```python
def check(self, from_state, to_state, event, context):
    # 执行守卫函数
    return self.func(from_state, to_state, event, context)
```

**时间复杂度**：取决于守卫函数

### 4.3 动作执行算法

```python
def execute(self, from_state, to_state, event, context):
    # 执行动作函数
    return self.func(from_state, to_state, event, context)
```

**时间复杂度**：取决于动作函数

### 4.4 历史记录算法

```python
def push(self, entry):
    # 计算持续时间
    if self._entries and self._last_state_change:
        duration = (entry.timestamp - self._last_state_change).total_seconds()
        self._entries[-1].duration = duration
    
    # 添加记录（自动淘汰旧记录）
    self._entries.append(entry)
    
    # 更新时间戳
    if entry.success:
        self._last_state_change = entry.timestamp
```

**时间复杂度**：O(1)

## 5. 错误处理实现

### 5.1 异常捕获

```python
try:
    # 执行转换
    from_state.on_exit(context)
    transition.execute(context)
    self._current_state = to_state
    to_state.on_enter(context)
except Exception as e:
    # 包装异常
    error = ActionError(
        f"Action failed: {e}",
        original_error=e
    )
    # 触发失败回调
    if self._on_transition_failed:
        self._on_transition_failed(from_state, event, error)
    return False
```

### 5.2 错误传播

```python
# 记录到历史
if self._enable_history and self._history:
    self._history.push(HistoryEntry(
        timestamp=datetime.now(),
        from_state=from_state,
        to_state=to_state,
        event=event,
        success=False,
        context=context,
        error=error
    ))
```

## 6. 性能优化

### 6.1 查找优化

```python
# 预计算转换索引
def _build_index(self):
    for transition in self._transitions:
        key = (transition.from_state, transition.event)
        if key not in self._transition_index:
            self._transition_index[key] = []
        self._transition_index[key].append(transition)
```

### 6.2 内存优化

```python
# 使用__slots__减少内存占用
class State:
    __slots__ = ['_name', '_metadata', '_entry_actions', '_exit_actions']

# 使用生成器减少中间列表
def entries_reversed(self):
    return reversed(self._entries)
```

### 6.3 惰性计算

```python
# 延迟计算可能事件
def possible_events(self):
    return [
        t.event for t in self._transitions
        if t.from_state == self._current_state
    ]
```

## 7. 测试实现

### 7.1 单元测试

```python
class TestStateMachine(unittest.TestCase):
    def test_process_event(self):
        sm = StateMachine(State("A"))
        sm.add_transition(Transition(State("A"), State("B"), Event("E")))
        result = sm.process_event(Event("E"))
        self.assertTrue(result)
        self.assertEqual(sm.current_state, State("B"))
```

### 7.2 集成测试

```python
class TestOrderWorkflow(unittest.TestCase):
    def test_complete_workflow(self):
        sm = create_order_state_machine()
        context = {"items": [...], "payment": 100}
        
        sm.process_event(VALIDATE, context)
        sm.process_event(REQUEST_PAYMENT, context)
        sm.process_event(CONFIRM_PAYMENT, context)
        
        self.assertEqual(sm.current_state, PAID)
```

### 7.3 性能测试

```python
class TestPerformance(unittest.TestCase):
    def test_many_transitions(self):
        sm = StateMachine(State("Initial"))
        for i in range(1000):
            sm.add_transition(Transition(
                State(f"S{i}"),
                State(f"S{i+1}"),
                Event(f"E{i}")
            ))
        
        start = time.time()
        for i in range(1000):
            sm.process_event(Event(f"E{i}"))
        elapsed = time.time() - start
        
        self.assertLess(elapsed, 1.0)  # 应该在1秒内完成
```

## 8. 调试支持

### 8.1 日志记录

```python
import logging

logger = logging.getLogger(__name__)

def process_event(self, event, context=None):
    logger.debug(f"Processing event: {event}")
    logger.debug(f"Current state: {self._current_state}")
    
    # ... 处理逻辑
    
    logger.info(f"Transition: {from_state} -> {to_state}")
```

### 8.2 状态可视化

```python
def format_graph(self):
    lines = ["digraph StateMachine {"]
    for t in self._transitions:
        lines.append(f'  "{t.from_state}" -> "{t.to_state}" [label="{t.event}"];')
    lines.append("}")
    return "\n".join(lines)
```

## 9. 扩展点实现

### 9.1 自定义守卫

```python
class CustomGuard(Guard):
    def __init__(self, param):
        self.param = param
    
    def check(self, from_state, to_state, event, context):
        # 自定义逻辑
        return context.get(self.param) is not None
```

### 9.2 自定义动作

```python
class CustomAction(Action):
    def __init__(self, service):
        self.service = service
    
    def execute(self, from_state, to_state, event, context):
        # 调用外部服务
        self.service.notify_transition(from_state, to_state, event)
```

### 9.3 自定义序列化

```python
class CustomSerializer:
    def serialize(self, sm):
        return {
            "state": str(sm.current_state),
            "context": sm.context
        }
    
    def deserialize(self, data):
        # 自定义反序列化
        pass
```

## 10. 最佳实践

### 10.1 状态命名

- 使用有意义的名称
- 避免缩写
- 保持一致性

### 10.2 事件命名

- 使用动词或动词短语
- 明确表示触发条件
- 避免歧义

### 10.3 守卫设计

- 保持简单
- 避免副作用
- 提供有意义的名称

### 10.4 动作设计

- 单一职责
- 错误处理
- 幂等性（如果可能）

## 11. 常见问题

### 11.1 状态冲突

**问题**：多个转换匹配同一状态和事件

**解决**：使用优先级或第一个匹配的转换

### 11.2 死锁

**问题**：状态机无法继续

**解决**：添加超时或取消机制

### 11.3 内存泄漏

**问题**：历史记录无限增长

**解决**：设置最大容量，自动淘汰旧记录

## 12. 未来改进

### 12.1 并发支持

- 线程安全的状态机
- 并发状态机
- 异步事件处理

### 12.2 持久化支持

- 状态机序列化
- 状态恢复
- 数据库集成

### 12.3 可视化工具

- 图形界面编辑器
- 实时状态监控
- 调试工具
