# 设计文档：逻辑门模拟器

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    逻辑门模拟器                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 基本门   │  │ 组合电路 │  │ 时序电路 │  │ 仿真引擎 │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│         │            │            │            │            │
│         └────────────┴────────────┴────────────┘            │
│                           │                                 │
│                    ┌──────┴──────┐                          │
│                    │   电路类    │                          │
│                    └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
logic-gates/
├── src/
│   ├── signal.py          # 信号定义
│   ├── gates.py           # 基本逻辑门
│   ├── circuit.py         # 电路类
│   ├── combinational/     # 组合电路
│   ├── sequential/        # 时序电路
│   ├── simulation/        # 仿真引擎
│   └── applications/      # 实际应用
```

## 2. 核心设计

### 2.1 信号设计

信号是数字电路的基本元素，设计为：

```python
class Signal:
    HIGH = 1  # 高电平
    LOW = 0   # 低电平

    @staticmethod
    def validate(value):
        """验证信号值是否有效"""
        if value not in (0, 1):
            raise InvalidInputError(f"Invalid signal value: {value}")
        return value
```

**设计考虑**：
- 使用整数0和1表示信号
- 提供验证方法确保信号有效
- 支持布尔值转换

### 2.2 逻辑门设计

逻辑门是电路的基本构建块：

```python
class Gate(ABC):
    """逻辑门抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """获取门名称"""
        pass

    @property
    @abstractmethod
    def num_inputs(self) -> int:
        """获取输入数量"""
        pass

    @abstractmethod
    def evaluate(self, *inputs: int) -> int:
        """计算输出"""
        pass

    def truth_table(self) -> List[Tuple[List[int], int]]:
        """生成真值表"""
        table = []
        for inputs in product([0, 1], repeat=self.num_inputs):
            output = self.evaluate(*inputs)
            table.append((list(inputs), output))
        return table
```

**设计考虑**：
- 使用抽象基类定义接口
- 支持真值表生成
- 使门可调用（__call__方法）

### 2.3 电路设计

电路类用于组合多个逻辑门：

```python
class Circuit:
    """电路类"""

    def __init__(self, name: str = "Circuit"):
        self.name = name
        self._gates: Dict[str, Gate] = {}
        self._connections: List[Tuple[str, str, int]] = []
        self._inputs: Dict[str, int] = {}

    def add_gate(self, gate: Gate, name: Optional[str] = None) -> str:
        """添加逻辑门"""
        pass

    def connect(self, from_name: str, to_name: str, input_idx: int = 0):
        """连接两个逻辑门"""
        pass

    def evaluate(self) -> Dict[str, int]:
        """计算电路输出"""
        pass
```

**设计考虑**：
- 使用有向图表示电路连接
- 支持拓扑排序确保正确计算顺序
- 支持真值表生成

### 2.4 时序电路设计

时序电路需要状态管理：

```python
class DFlipFlop:
    """D触发器"""

    def __init__(self):
        self._q = 0
        self._q_bar = 1
        self._last_clk = 0

    def evaluate(self, d: int, clk: int) -> Dict[str, int]:
        """计算触发器输出"""
        # 检测上升沿
        if self._last_clk == 0 and clk == 1:
            self._q = d
            self._q_bar = 1 - d
        self._last_clk = clk
        return self.get_state()
```

**设计考虑**：
- 使用状态变量存储当前状态
- 检测时钟边沿触发状态更新
- 提供状态查询接口

### 2.5 仿真引擎设计

仿真引擎支持事件驱动仿真：

```python
class Simulator:
    """仿真器"""

    def __init__(self):
        self._time = 0
        self._wires: Dict[str, Wire] = {}
        self._events: List[Event] = []

    def schedule_event(self, time: int, target: str, value: int):
        """调度事件"""
        event = Event(time, EventType.SIGNAL_CHANGE, target, value)
        heapq.heappush(self._events, event)

    def run(self, max_time: int):
        """运行仿真"""
        while self._events:
            event = heapq.heappop(self._events)
            if event.time > max_time:
                break
            self._process_event(event)
```

**设计考虑**：
- 使用优先队列管理事件
- 支持延迟模拟
- 支持信号追踪

## 3. 数据结构设计

### 3.1 信号历史

```python
class Wire:
    """连线"""

    def __init__(self, name: str, delay: int = 0):
        self.name = name
        self.delay = delay
        self._value = 0
        self._history: List[tuple] = []  # (时间, 值)
```

### 3.2 真值表

```python
# 真值表格式
truth_table = [
    ([0, 0], 0),  # (输入组合, 输出)
    ([0, 1], 0),
    ([1, 0], 0),
    ([1, 1], 1),
]
```

### 3.3 电路连接

```python
# 连接格式
connections = [
    ("A", "AND1", 0),  # (源, 目标, 输入索引)
    ("B", "AND1", 1),
]
```

## 4. 接口设计

### 4.1 逻辑门接口

```python
class Gate(ABC):
    @property
    def name(self) -> str: ...

    @property
    def num_inputs(self) -> int: ...

    def evaluate(self, *inputs: int) -> int: ...

    def truth_table(self) -> List[Tuple[List[int], int]]: ...

    def __call__(self, *inputs: int) -> int: ...
```

### 4.2 电路接口

```python
class Circuit:
    def add_gate(self, gate: Gate, name: Optional[str] = None) -> str: ...

    def connect(self, from_name: str, to_name: str, input_idx: int = 0): ...

    def set_input(self, name: str, value: int): ...

    def evaluate(self) -> Dict[str, int]: ...

    def get_truth_table(self) -> List[Dict]: ...
```

### 4.3 仿真器接口

```python
class Simulator:
    def add_wire(self, name: str, delay: int = 0) -> Wire: ...

    def schedule_event(self, time: int, target: str, value: int): ...

    def run(self, max_time: int): ...

    def get_waveform(self, name: str) -> List[int]: ...

    def get_state(self) -> Dict[str, int]: ...
```

## 5. 扩展性设计

### 5.1 自定义逻辑门

支持用户定义自己的逻辑门：

```python
class CustomGate(Gate):
    """自定义逻辑门"""

    def __init__(self, name: str, num_inputs: int, logic_func: Callable):
        self._name = name
        self._num_inputs = num_inputs
        self._logic_func = logic_func

    def evaluate(self, *inputs: int) -> int:
        return self._logic_func(*inputs)
```

### 5.2 门注册表

支持动态注册新的逻辑门类型：

```python
class GateRegistry:
    """逻辑门注册表"""

    @classmethod
    def register(cls, name: str, gate_class: Type[Gate]):
        """注册逻辑门"""
        cls._gates[name] = gate_class

    @classmethod
    def create(cls, name: str, *args, **kwargs) -> Gate:
        """创建逻辑门实例"""
        gate_class = cls.get(name)
        return gate_class(*args, **kwargs)
```

### 5.3 电路导出

支持多种格式导出：

```python
class TruthTableGenerator:
    @staticmethod
    def to_csv(table: List[Tuple[List[int], int]]) -> str: ...

    @staticmethod
    def to_json(table: List[Tuple[List[int], int]]) -> List[Dict]: ...
```

## 6. 性能优化

### 6.1 拓扑排序

使用拓扑排序确保正确的计算顺序：

```python
def _topological_sort(self, dependencies: Dict[str, Set[str]]) -> List[str]:
    """拓扑排序"""
    visited = set()
    order = []

    def visit(node):
        if node in visited:
            return
        visited.add(node)
        for dep in dependencies.get(node, set()):
            visit(dep)
        order.append(node)

    for node in all_nodes:
        visit(node)

    return order
```

### 6.2 事件优先队列

使用堆实现高效的事件调度：

```python
import heapq

# 使用堆管理事件
heapq.heappush(self._events, event)
event = heapq.heappop(self._events)
```

### 6.3 缓存优化

对于重复计算，可以使用缓存：

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def evaluate(self, *inputs: int) -> int:
    """带缓存的计算"""
    pass
```

## 7. 错误处理

### 7.1 异常层次

```python
class LogicGateError(Exception):
    """逻辑门基础异常"""
    pass

class InvalidInputError(LogicGateError):
    """无效输入异常"""
    pass

class ConnectionError(LogicGateError):
    """连接错误异常"""
    pass

class CircuitError(LogicGateError):
    """电路错误异常"""
    pass
```

### 7.2 输入验证

```python
def _validate_inputs(self, inputs: tuple):
    """验证输入"""
    if len(inputs) != self.num_inputs:
        raise InvalidInputError(
            f"{self.name} gate requires {self.num_inputs} input(s), "
            f"got {len(inputs)}"
        )

    for i, inp in enumerate(inputs):
        if inp not in (0, 1):
            raise InvalidInputError(
                f"Invalid input at position {i}: {inp}. Must be 0 or 1"
            )
```

## 8. 测试策略

### 8.1 单元测试

每个模块都有对应的单元测试：

```python
class TestAndGate:
    """AND门测试"""

    def test_evaluate_00(self):
        """测试输入00"""
        gate = AndGate()
        assert gate.evaluate(0, 0) == 0

    def test_evaluate_11(self):
        """测试输入11"""
        gate = AndGate()
        assert gate.evaluate(1, 1) == 1
```

### 8.2 集成测试

测试模块之间的交互：

```python
class TestCircuit:
    """电路测试"""

    def test_evaluate_simple(self):
        """测试简单电路"""
        circuit = Circuit()
        circuit.add_gate(AndGate(), "AND1")
        circuit.connect("A", "AND1", 0)
        circuit.connect("B", "AND1", 1)
        circuit.set_inputs({"A": 1, "B": 1})
        results = circuit.evaluate()
        assert results["AND1"] == 1
```

### 8.3 真值表验证

验证逻辑门的正确性：

```python
class TestTruthTableAccuracy:
    """真值表准确性测试"""

    def test_and_accuracy(self):
        """测试AND门真值表准确性"""
        gate = AndGate()
        table = gate.truth_table()

        expected = [
            ([0, 0], 0),
            ([0, 1], 0),
            ([1, 0], 0),
            ([1, 1], 1),
        ]

        for inputs, output in expected:
            assert (inputs, output) in table
```
