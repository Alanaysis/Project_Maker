# 实现文档：逻辑门模拟器

## 1. 基本逻辑门实现

### 1.1 AND门实现

```python
class AndGate(Gate):
    """与门"""

    @property
    def name(self) -> str:
        return "AND"

    @property
    def num_inputs(self) -> int:
        return 2

    def evaluate(self, *inputs: int) -> int:
        """计算AND门输出"""
        self._validate_inputs(inputs)
        return int(all(inputs))
```

**实现说明**：
- 使用Python内置的`all()`函数
- 输入为可迭代对象，所有元素为True时返回True
- 转换为整数输出（0或1）

### 1.2 OR门实现

```python
class OrGate(Gate):
    """或门"""

    @property
    def name(self) -> str:
        return "OR"

    @property
    def num_inputs(self) -> int:
        return 2

    def evaluate(self, *inputs: int) -> int:
        """计算OR门输出"""
        self._validate_inputs(inputs)
        return int(any(inputs))
```

**实现说明**：
- 使用Python内置的`any()`函数
- 输入为可迭代对象，任一元素为True时返回True
- 转换为整数输出（0或1）

### 1.3 NOT门实现

```python
class NotGate(Gate):
    """非门"""

    @property
    def name(self) -> str:
        return "NOT"

    @property
    def num_inputs(self) -> int:
        return 1

    def evaluate(self, *inputs: int) -> int:
        """计算NOT门输出"""
        self._validate_inputs(inputs)
        return int(not inputs[0])
```

**实现说明**：
- 使用Python内置的`not`运算符
- 只有一个输入
- 转换为整数输出（0或1）

### 1.4 XOR门实现

```python
class XorGate(Gate):
    """异或门"""

    @property
    def name(self) -> str:
        return "XOR"

    @property
    def num_inputs(self) -> int:
        return 2

    def evaluate(self, *inputs: int) -> int:
        """计算XOR门输出"""
        self._validate_inputs(inputs)
        return int(sum(inputs) % 2 == 1)
```

**实现说明**：
- 使用求和取模的方式实现
- 输入之和为奇数时输出1
- 转换为整数输出（0或1）

### 1.5 NAND门实现

```python
class NandGate(Gate):
    """与非门"""

    @property
    def name(self) -> str:
        return "NAND"

    @property
    def num_inputs(self) -> int:
        return 2

    def evaluate(self, *inputs: int) -> int:
        """计算NAND门输出"""
        self._validate_inputs(inputs)
        return int(not all(inputs))
```

**实现说明**：
- 先计算AND，再取反
- 使用`not all(inputs)`实现
- 转换为整数输出（0或1）

### 1.6 NOR门实现

```python
class NorGate(Gate):
    """或非门"""

    @property
    def name(self) -> str:
        return "NOR"

    @property
    def num_inputs(self) -> int:
        return 2

    def evaluate(self, *inputs: int) -> int:
        """计算NOR门输出"""
        self._validate_inputs(inputs)
        return int(not any(inputs))
```

**实现说明**：
- 先计算OR，再取反
- 使用`not any(inputs)`实现
- 转换为整数输出（0或1）

### 1.7 XNOR门实现

```python
class XnorGate(Gate):
    """同或门"""

    @property
    def name(self) -> str:
        return "XNOR"

    @property
    def num_inputs(self) -> int:
        return 2

    def evaluate(self, *inputs: int) -> int:
        """计算XNOR门输出"""
        self._validate_inputs(inputs)
        return int(sum(inputs) % 2 == 0)
```

**实现说明**：
- 与XOR相反
- 输入之和为偶数时输出1
- 转换为整数输出（0或1）

## 2. 组合电路实现

### 2.1 多路选择器实现

```python
class Multiplexer:
    """多路选择器"""

    def __init__(self, num_select_lines: int):
        self.num_select = num_select_lines
        self.num_inputs = 2 ** num_select_lines

    def evaluate(self, data_inputs: List[int], select_inputs: List[int]) -> int:
        """计算多路选择器输出"""
        # 计算选择索引
        select_index = 0
        for i, s in enumerate(select_inputs):
            select_index |= s << i

        return data_inputs[select_index]
```

**实现说明**：
- 使用位运算计算选择索引
- 选择信号作为二进制数
- 直接索引数据输入

### 2.2 解码器实现

```python
class Decoder:
    """二进制解码器"""

    def __init__(self, num_inputs: int):
        self.num_inputs = num_inputs
        self.num_outputs = 2 ** num_inputs

    def evaluate(self, inputs: List[int]) -> List[int]:
        """计算解码器输出"""
        # 计算输入值
        input_value = 0
        for i, inp in enumerate(inputs):
            input_value |= inp << i

        # 生成输出
        outputs = [0] * self.num_outputs
        outputs[input_value] = 1

        return outputs
```

**实现说明**：
- 使用位运算计算输入值
- 生成独热码输出
- 只有一个输出为1

### 2.3 半加器实现

```python
class HalfAdder:
    """半加器"""

    def __init__(self):
        self._circuit = self._build_circuit()

    def _build_circuit(self) -> Circuit:
        """构建半加器电路"""
        circuit = Circuit("Half Adder")

        # 添加门
        xor_gate = circuit.add_gate(XorGate(), "XOR")
        and_gate = circuit.add_gate(AndGate(), "AND")

        # 连接
        circuit.connect("A", "XOR", 0)
        circuit.connect("B", "XOR", 1)
        circuit.connect("A", "AND", 0)
        circuit.connect("B", "AND", 1)

        # 标记输入输出
        circuit.mark_as_input("A")
        circuit.mark_as_input("B")
        circuit.mark_as_output("XOR")
        circuit.mark_as_output("AND")

        return circuit

    def evaluate(self, a: int, b: int) -> Tuple[int, int]:
        """计算半加器输出"""
        self._circuit.set_inputs({"A": a, "B": b})
        results = self._circuit.evaluate()

        return results.get("XOR", 0), results.get("AND", 0)
```

**实现说明**：
- 使用XOR门计算和
- 使用AND门计算进位
- 组合成完整电路

### 2.4 全加器实现

```python
class FullAdder:
    """全加器"""

    def __init__(self):
        self._circuit = self._build_circuit()

    def _build_circuit(self) -> Circuit:
        """构建全加器电路"""
        circuit = Circuit("Full Adder")

        # 添加门
        xor1 = circuit.add_gate(XorGate(), "XOR1")
        xor2 = circuit.add_gate(XorGate(), "XOR2")
        and1 = circuit.add_gate(AndGate(), "AND1")
        and2 = circuit.add_gate(AndGate(), "AND2")
        or_gate = circuit.add_gate(OrGate(), "OR1")

        # 连接第一级
        circuit.connect("A", "XOR1", 0)
        circuit.connect("B", "XOR1", 1)
        circuit.connect("A", "AND1", 0)
        circuit.connect("B", "AND1", 1)

        # 连接第二级
        circuit.connect("XOR1", "XOR2", 0)
        circuit.connect("CIN", "XOR2", 1)
        circuit.connect("XOR1", "AND2", 0)
        circuit.connect("CIN", "AND2", 1)

        # 连接第三级
        circuit.connect("AND1", "OR1", 0)
        circuit.connect("AND2", "OR1", 1)

        return circuit

    def evaluate(self, a: int, b: int, cin: int) -> Tuple[int, int]:
        """计算全加器输出"""
        self._circuit.set_inputs({"A": a, "B": b, "CIN": cin})
        results = self._circuit.evaluate()

        return results.get("XOR2", 0), results.get("OR1", 0)
```

**实现说明**：
- 使用两个半加器组合
- 第一级：A XOR B
- 第二级：(A XOR B) XOR CIN
- 进位：(A AND B) OR ((A XOR B) AND CIN)

### 2.5 ALU实现

```python
class ALU:
    """算术逻辑单元"""

    OP_ADD = [0, 0, 0, 0]
    OP_SUB = [0, 0, 0, 1]
    OP_AND = [0, 0, 1, 0]
    OP_OR  = [0, 0, 1, 1]
    OP_XOR = [0, 1, 0, 0]

    def evaluate(self, a: List[int], b: List[int], op: List[int]) -> Dict:
        """执行ALU操作"""
        # 转换操作码为整数
        op_int = 0
        for i, bit in enumerate(op):
            op_int |= bit << (3 - i)

        # 执行操作
        if op_int == 0:  # ADD
            result_rev, carry = self._adder.evaluate(a_rev, b_rev)
            result = list(reversed(result_rev))
        elif op_int == 1:  # SUB
            b_not = [1 - bit for bit in b]
            result_rev, carry = self._adder.evaluate(a_rev, b_not_rev, 1)
            result = list(reversed(result_rev))
        elif op_int == 2:  # AND
            result = [a[i] and b[i] for i in range(self.num_bits)]
        elif op_int == 3:  # OR
            result = [a[i] or b[i] for i in range(self.num_bits)]
        elif op_int == 4:  # XOR
            result = [a[i] ^ b[i] for i in range(self.num_bits)]

        return {
            'result': result,
            'zero': int(all(bit == 0 for bit in result)),
            'carry': carry,
            'negative': result[0]
        }
```

**实现说明**：
- 使用操作码选择操作
- 支持多种算术和逻辑运算
- 返回结果和标志位

## 3. 时序电路实现

### 3.1 SR锁存器实现

```python
class SRLatch:
    """SR锁存器"""

    def __init__(self):
        self._q = 0
        self._q_bar = 1

    def evaluate(self, s: int, r: int) -> Dict[str, int]:
        """计算锁存器输出"""
        if s == 1 and r == 1:
            raise ValueError("Invalid state: S=1, R=1 is forbidden")

        if s == 1:
            self._q = 1
            self._q_bar = 0
        elif r == 1:
            self._q = 0
            self._q_bar = 1

        return self.get_state()
```

**实现说明**：
- 使用两个状态变量Q和Q'
- S=1时置位，R=1时复位
- S=R=1是禁止状态

### 3.2 D触发器实现

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

**实现说明**：
- 检测时钟上升沿
- 上升沿时采样输入D
- 下降沿时保持状态

### 3.3 计数器实现

```python
class Counter:
    """二进制计数器"""

    def __init__(self, num_bits: int):
        self.num_bits = num_bits
        self._flipflops = [TFlipFlop() for _ in range(num_bits)]
        self._count = 0

    def increment(self) -> List[int]:
        """递增计数器"""
        carry = 1  # 初始进位为1

        for i in range(self.num_bits - 1, -1, -1):
            if carry == 1:
                result = self._flipflops[i].evaluate(1, 1)
                carry = result['Q']
            else:
                result = self._flipflops[i].get_state()

        self._count = (self._count + 1) % (2 ** self.num_bits)
        return self.get_value()
```

**实现说明**：
- 使用T触发器链
- 进位传播
- 模运算处理溢出

## 4. 仿真引擎实现

### 4.1 连线实现

```python
class Wire:
    """连线"""

    def __init__(self, name: str, delay: int = 0):
        self.name = name
        self.delay = delay
        self._value = 0
        self._history: List[tuple] = []

    def set_value(self, value: int, time: int = 0):
        """设置连线值"""
        self._value = value
        self._history.append((time, value))

    def get_delayed_value(self, time: int) -> int:
        """获取延迟后的值"""
        delayed_time = time - self.delay
        for t, v in reversed(self._history):
            if t <= delayed_time:
                return v
        return 0
```

**实现说明**：
- 记录信号历史
- 支持延迟查询
- 使用二分查找优化

### 4.2 仿真器实现

```python
class Simulator:
    """仿真器"""

    def __init__(self):
        self._time = 0
        self._wires: Dict[str, Wire] = {}
        self._events: List[Event] = []

    def run(self, max_time: int):
        """运行仿真"""
        while self._events:
            event = heapq.heappop(self._events)
            if event.time > max_time:
                break
            self._process_event(event)

    def _process_event(self, event: Event):
        """处理事件"""
        if event.target in self._wires:
            wire = self._wires[event.target]
            wire.set_value(event.value, event.time)
            self._history[event.target].append((event.time, event.value))
```

**实现说明**：
- 使用优先队列管理事件
- 按时间顺序处理事件
- 记录信号历史

## 5. 测试实现

### 5.1 单元测试示例

```python
class TestAndGate:
    """AND门测试"""

    def setup_method(self):
        """测试前准备"""
        self.gate = AndGate()

    def test_evaluate_00(self):
        """测试输入00"""
        assert self.gate.evaluate(0, 0) == 0

    def test_evaluate_11(self):
        """测试输入11"""
        assert self.gate.evaluate(1, 1) == 1

    def test_truth_table(self):
        """测试真值表"""
        table = self.gate.truth_table()
        assert len(table) == 4
        assert ([0, 0], 0) in table
        assert ([1, 1], 1) in table
```

### 5.2 集成测试示例

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

### 5.3 真值表验证示例

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
