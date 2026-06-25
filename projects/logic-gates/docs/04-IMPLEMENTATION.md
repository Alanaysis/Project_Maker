# 逻辑门模拟器 - 实现文档

## 1. 实现概述

本文档详细描述了逻辑门模拟器的实现细节，包括核心算法、数据结构和关键代码。

## 2. 项目结构

```
logic-gates/
├── src/
│   ├── __init__.py
│   ├── signal.py          # 信号定义
│   ├── gates.py           # 逻辑门实现
│   ├── circuit.py         # 电路组合
│   ├── truth_table.py     # 真值表生成
│   ├── registry.py        # 门注册表
│   ├── exceptions.py      # 异常定义
│   └── utils.py           # 工具函数
├── tests/
│   ├── __init__.py
│   ├── test_gates.py      # 逻辑门测试
│   ├── test_circuit.py    # 电路测试
│   └── test_truth_table.py # 真值表测试
├── examples/
│   ├── basic_gates.py     # 基本门示例
│   ├── circuit_demo.py    # 电路示例
│   └── truth_table_demo.py # 真值表示例
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-API.md
│   ├── 04-IMPLEMENTATION.md
│   └── 05-DEVELOPMENT.md
├── README.md
├── LEARNING_NOTES.md
└── setup.py
```

## 3. 核心实现

### 3.1 信号模块 (signal.py)

```python
class Signal:
    """数字信号定义"""
    
    HIGH = 1
    LOW = 0
    
    @staticmethod
    def validate(value):
        """验证信号值"""
        if value not in (0, 1):
            raise InvalidInputError(f"Invalid signal value: {value}")
        return value
    
    @staticmethod
    def from_bool(value):
        """从布尔值转换"""
        return 1 if value else 0
    
    @staticmethod
    def to_bool(value):
        """转换为布尔值"""
        return bool(value)
```

### 3.2 逻辑门实现 (gates.py)

#### 3.2.1 基类实现

```python
from abc import ABC, abstractmethod
from itertools import product

class Gate(ABC):
    """逻辑门抽象基类"""
    
    @property
    @abstractmethod
    def name(self):
        pass
    
    @property
    @abstractmethod
    def num_inputs(self):
        pass
    
    @abstractmethod
    def evaluate(self, *inputs):
        pass
    
    def truth_table(self):
        """生成真值表"""
        table = []
        for inputs in product([0, 1], repeat=self.num_inputs):
            output = self.evaluate(*inputs)
            table.append((list(inputs), output))
        return table
    
    def __call__(self, *inputs):
        return self.evaluate(*inputs)
    
    def __repr__(self):
        return f"{self.name}Gate(inputs={self.num_inputs})"
```

#### 3.2.2 AND门实现

```python
class AndGate(Gate):
    """与门实现"""
    
    @property
    def name(self):
        return "AND"
    
    @property
    def num_inputs(self):
        return 2
    
    def evaluate(self, *inputs):
        """
        AND门逻辑：所有输入为1时输出1
        
        真值表：
        A | B | OUT
        0 | 0 | 0
        0 | 1 | 0
        1 | 0 | 0
        1 | 1 | 1
        """
        if len(inputs) != self.num_inputs:
            raise InvalidInputError(
                f"AND gate requires {self.num_inputs} inputs, got {len(inputs)}"
            )
        
        # 验证输入
        for inp in inputs:
            Signal.validate(inp)
        
        # 计算输出：所有输入都为1时返回1
        return int(all(inputs))
```

#### 3.2.3 OR门实现

```python
class OrGate(Gate):
    """或门实现"""
    
    @property
    def name(self):
        return "OR"
    
    @property
    def num_inputs(self):
        return 2
    
    def evaluate(self, *inputs):
        """
        OR门逻辑：任一输入为1时输出1
        
        真值表：
        A | B | OUT
        0 | 0 | 0
        0 | 1 | 1
        1 | 0 | 1
        1 | 1 | 1
        """
        if len(inputs) != self.num_inputs:
            raise InvalidInputError(
                f"OR gate requires {self.num_inputs} inputs, got {len(inputs)}"
            )
        
        for inp in inputs:
            Signal.validate(inp)
        
        # 计算输出：任一输入为1时返回1
        return int(any(inputs))
```

#### 3.2.4 NOT门实现

```python
class NotGate(Gate):
    """非门实现"""
    
    @property
    def name(self):
        return "NOT"
    
    @property
    def num_inputs(self):
        return 1
    
    def evaluate(self, *inputs):
        """
        NOT门逻辑：输入取反
        
        真值表：
        A | OUT
        0 | 1
        1 | 0
        """
        if len(inputs) != self.num_inputs:
            raise InvalidInputError(
                f"NOT gate requires {self.num_inputs} input, got {len(inputs)}"
            )
        
        Signal.validate(inputs[0])
        
        # 计算输出：输入取反
        return int(not inputs[0])
```

#### 3.2.5 XOR门实现

```python
class XorGate(Gate):
    """异或门实现"""
    
    @property
    def name(self):
        return "XOR"
    
    @property
    def num_inputs(self):
        return 2
    
    def evaluate(self, *inputs):
        """
        XOR门逻辑：输入不同时输出1
        
        真值表：
        A | B | OUT
        0 | 0 | 0
        0 | 1 | 1
        1 | 0 | 1
        1 | 1 | 0
        """
        if len(inputs) != self.num_inputs:
            raise InvalidInputError(
                f"XOR gate requires {self.num_inputs} inputs, got {len(inputs)}"
            )
        
        for inp in inputs:
            Signal.validate(inp)
        
        # 计算输出：输入之和为奇数时返回1
        return int(sum(inputs) % 2 == 1)
```

#### 3.2.6 NAND门实现

```python
class NandGate(Gate):
    """与非门实现"""
    
    @property
    def name(self):
        return "NAND"
    
    @property
    def num_inputs(self):
        return 2
    
    def evaluate(self, *inputs):
        """
        NAND门逻辑：AND门取反
        
        真值表：
        A | B | OUT
        0 | 0 | 1
        0 | 1 | 1
        1 | 0 | 1
        1 | 1 | 0
        """
        if len(inputs) != self.num_inputs:
            raise InvalidInputError(
                f"NAND gate requires {self.num_inputs} inputs, got {len(inputs)}"
            )
        
        for inp in inputs:
            Signal.validate(inp)
        
        # 计算输出：AND门取反
        return int(not all(inputs))
```

#### 3.2.7 NOR门实现

```python
class NorGate(Gate):
    """或非门实现"""
    
    @property
    def name(self):
        return "NOR"
    
    @property
    def num_inputs(self):
        return 2
    
    def evaluate(self, *inputs):
        """
        NOR门逻辑：OR门取反
        
        真值表：
        A | B | OUT
        0 | 0 | 1
        0 | 1 | 0
        1 | 0 | 0
        1 | 1 | 0
        """
        if len(inputs) != self.num_inputs:
            raise InvalidInputError(
                f"NOR gate requires {self.num_inputs} inputs, got {len(inputs)}"
            )
        
        for inp in inputs:
            Signal.validate(inp)
        
        # 计算输出：OR门取反
        return int(not any(inputs))
```

### 3.3 电路实现 (circuit.py)

```python
from collections import defaultdict
from typing import Dict, List, Optional

class Circuit:
    """电路实现"""
    
    def __init__(self, name="Circuit"):
        self.name = name
        self._gates = {}  # 门实例
        self._connections = []  # 连接关系
        self._inputs = {}  # 输入信号
        self._outputs = {}  # 输出信号
        self._input_gates = set()  # 输入门
        self._output_gates = set()  # 输出门
    
    def add_gate(self, gate, name=None):
        """添加逻辑门"""
        if name is None:
            name = f"{gate.name}_{len(self._gates)}"
        
        if name in self._gates:
            raise CircuitError(f"Gate '{name}' already exists")
        
        self._gates[name] = gate
        return name
    
    def connect(self, from_name, to_name, input_idx=0):
        """连接两个门"""
        if from_name not in self._gates:
            raise CircuitError(f"Source gate '{from_name}' not found")
        if to_name not in self._gates:
            raise CircuitError(f"Target gate '{to_name}' not found")
        
        # 验证输入索引
        target_gate = self._gates[to_name]
        if input_idx >= target_gate.num_inputs:
            raise CircuitError(
                f"Input index {input_idx} out of range for gate '{to_name}'"
            )
        
        self._connections.append((from_name, to_name, input_idx))
    
    def set_input(self, name, value):
        """设置输入信号"""
        Signal.validate(value)
        self._inputs[name] = value
    
    def set_inputs(self, inputs):
        """批量设置输入"""
        for name, value in inputs.items():
            self.set_input(name, value)
    
    def mark_as_input(self, gate_name):
        """标记为输入门"""
        if gate_name not in self._gates:
            raise CircuitError(f"Gate '{gate_name}' not found")
        self._input_gates.add(gate_name)
    
    def mark_as_output(self, gate_name):
        """标记为输出门"""
        if gate_name not in self._gates:
            raise CircuitError(f"Gate '{gate_name}' not found")
        self._output_gates.add(gate_name)
    
    def evaluate(self):
        """计算电路输出"""
        # 构建依赖图
        dependencies = self._build_dependency_graph()
        
        # 拓扑排序
        order = self._topological_sort(dependencies)
        
        # 按顺序计算
        results = {}
        for gate_name in order:
            gate = self._gates[gate_name]
            
            # 获取输入
            inputs = self._get_gate_inputs(gate_name, results)
            
            # 计算输出
            output = gate.evaluate(*inputs)
            results[gate_name] = output
        
        return results
    
    def _build_dependency_graph(self):
        """构建依赖图"""
        deps = defaultdict(set)
        for from_name, to_name, _ in self._connections:
            deps[to_name].add(from_name)
        return deps
    
    def _topological_sort(self, dependencies):
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
        
        for gate_name in self._gates:
            visit(gate_name)
        
        return order
    
    def _get_gate_inputs(self, gate_name, results):
        """获取门的输入"""
        gate = self._gates[gate_name]
        inputs = [0] * gate.num_inputs
        
        # 从连接中获取输入
        for from_name, to_name, input_idx in self._connections:
            if to_name == gate_name:
                if from_name in results:
                    inputs[input_idx] = results[from_name]
                elif from_name in self._inputs:
                    inputs[input_idx] = self._inputs[from_name]
        
        return inputs
    
    def get_truth_table(self):
        """生成真值表"""
        # 获取所有输入门
        input_gates = list(self._input_gates)
        if not input_gates:
            raise CircuitError("No input gates defined")
        
        # 生成所有输入组合
        table = []
        for inputs in product([0, 1], repeat=len(input_gates)):
            # 设置输入
            for i, gate_name in enumerate(input_gates):
                self.set_input(gate_name, inputs[i])
            
            # 计算输出
            results = self.evaluate()
            
            # 收集输出
            outputs = {}
            for gate_name in self._output_gates:
                outputs[gate_name] = results.get(gate_name, 0)
            
            table.append({
                "inputs": dict(zip(input_gates, inputs)),
                "outputs": outputs
            })
        
        return table
```

### 3.4 真值表生成器 (truth_table.py)

```python
class TruthTableGenerator:
    """真值表生成器"""
    
    @staticmethod
    def generate(gate):
        """生成单个门的真值表"""
        table = gate.truth_table()
        return TruthTableGenerator.format_table(table, gate.name)
    
    @staticmethod
    def format_table(table, name=""):
        """格式化真值表"""
        if not table:
            return ""
        
        # 计算列数
        num_inputs = len(table[0][0])
        
        # 计算列宽
        col_width = max(6, len(name) + 2)
        
        # 生成表头
        headers = [f"IN{i}" for i in range(num_inputs)] + ["OUT"]
        header_line = " | ".join([f"{h:^{col_width}}" for h in headers])
        
        # 生成分隔线
        separator = "-" * len(header_line)
        
        # 生成数据行
        rows = []
        for inputs, output in table:
            row_inputs = [f"{inp:^{col_width}}" for inp in inputs]
            row_output = f"{output:^{col_width}}"
            row = " | ".join(row_inputs + [row_output])
            rows.append(row)
        
        # 组合结果
        result = [name, separator, header_line, separator]
        result.extend(rows)
        result.append(separator)
        
        return "\n".join(result)
    
    @staticmethod
    def generate_circuit_table(circuit):
        """生成电路真值表"""
        table = circuit.get_truth_table()
        return TruthTableGenerator.format_circuit_table(table)
    
    @staticmethod
    def format_circuit_table(table):
        """格式化电路真值表"""
        if not table:
            return ""
        
        # 获取输入和输出名称
        first_row = table[0]
        input_names = list(first_row["inputs"].keys())
        output_names = list(first_row["outputs"].keys())
        
        # 计算列宽
        all_names = input_names + output_names
        col_width = max(len(name) for name in all_names) + 2
        
        # 生成表头
        header_line = " | ".join([f"{n:^{col_width}}" for n in all_names])
        
        # 生成分隔线
        separator = "-" * len(header_line)
        
        # 生成数据行
        rows = []
        for row in table:
            input_values = [f"{row['inputs'][n]:^{col_width}}" for n in input_names]
            output_values = [f"{row['outputs'][n]:^{col_width}}" for n in output_names]
            row_line = " | ".join(input_values + output_values)
            rows.append(row_line)
        
        # 组合结果
        result = ["Circuit Truth Table", separator, header_line, separator]
        result.extend(rows)
        result.append(separator)
        
        return "\n".join(result)
```

### 3.5 门注册表 (registry.py)

```python
class GateRegistry:
    """逻辑门注册表"""
    
    _gates = {}
    _instances = {}
    
    @classmethod
    def register(cls, name, gate_class):
        """注册逻辑门"""
        cls._gates[name] = gate_class
    
    @classmethod
    def get(cls, name):
        """获取逻辑门类"""
        return cls._gates.get(name)
    
    @classmethod
    def create(cls, name, *args, **kwargs):
        """创建逻辑门实例"""
        gate_class = cls.get(name)
        if gate_class is None:
            raise ValueError(f"Unknown gate type: {name}")
        return gate_class(*args, **kwargs)
    
    @classmethod
    def get_or_create(cls, name):
        """获取或创建单例"""
        if name not in cls._instances:
            cls._instances[name] = cls.create(name)
        return cls._instances[name]
    
    @classmethod
    def list_gates(cls):
        """列出所有门类型"""
        return list(cls._gates.keys())
    
    @classmethod
    def clear(cls):
        """清除注册表"""
        cls._gates.clear()
        cls._instances.clear()


# 注册默认门
def register_default_gates():
    """注册默认逻辑门"""
    GateRegistry.register("AND", AndGate)
    GateRegistry.register("OR", OrGate)
    GateRegistry.register("NOT", NotGate)
    GateRegistry.register("XOR", XorGate)
    GateRegistry.register("NAND", NandGate)
    GateRegistry.register("NOR", NorGate)

# 初始化时注册
register_default_gates()
```

### 3.6 异常定义 (exceptions.py)

```python
class LogicGateError(Exception):
    """逻辑门基础异常"""
    pass

class InvalidInputError(LogicGateError):
    """无效输入异常"""
    
    def __init__(self, message="Invalid input signal"):
        super().__init__(message)

class ConnectionError(LogicGateError):
    """连接错误异常"""
    
    def __init__(self, message="Invalid connection"):
        super().__init__(message)

class CircuitError(LogicGateError):
    """电路错误异常"""
    
    def __init__(self, message="Circuit error"):
        super().__init__(message)
```

### 3.7 工具函数 (utils.py)

```python
def print_truth_table(gate):
    """打印真值表"""
    print(TruthTableGenerator.generate(gate))

def print_circuit_table(circuit):
    """打印电路真值表"""
    print(TruthTableGenerator.generate_circuit_table(circuit))

def create_circuit_from_description(description):
    """从描述创建电路"""
    circuit = Circuit(description.get("name", "Circuit"))
    
    # 添加门
    for gate_desc in description.get("gates", []):
        gate_type = gate_desc["type"]
        gate_name = gate_desc.get("name")
        gate = GateRegistry.create(gate_type)
        circuit.add_gate(gate, gate_name)
    
    # 添加连接
    for conn in description.get("connections", []):
        circuit.connect(conn["from"], conn["to"], conn.get("input_idx", 0))
    
    # 标记输入输出
    for input_name in description.get("inputs", []):
        circuit.mark_as_input(input_name)
    
    for output_name in description.get("outputs", []):
        circuit.mark_as_output(output_name)
    
    return circuit

def format_binary(value, width=8):
    """格式化二进制输出"""
    return format(value, f'0{width}b')

def binary_to_decimal(binary_str):
    """二进制转十进制"""
    return int(binary_str, 2)

def decimal_to_binary(decimal, width=8):
    """十进制转二进制"""
    return format(decimal, f'0{width}b')
```

## 4. 关键算法

### 4.1 拓扑排序算法

用于确定电路中门的计算顺序：

```python
def topological_sort(gates, connections):
    """
    拓扑排序算法
    
    Args:
        gates: 门字典
        connections: 连接列表
    
    Returns:
        排序后的门名称列表
    """
    # 构建邻接表和入度表
    in_degree = {name: 0 for name in gates}
    adjacency = defaultdict(list)
    
    for from_name, to_name, _ in connections:
        adjacency[from_name].append(to_name)
        in_degree[to_name] += 1
    
    # 找到所有入度为0的节点
    queue = [name for name, degree in in_degree.items() if degree == 0]
    result = []
    
    while queue:
        node = queue.pop(0)
        result.append(node)
        
        # 更新相邻节点的入度
        for neighbor in adjacency[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # 检查是否有环
    if len(result) != len(gates):
        raise CircuitError("Circuit contains a cycle")
    
    return result
```

### 4.2 信号传播算法

```python
def propagate_signals(circuit, inputs):
    """
    信号传播算法
    
    Args:
        circuit: 电路实例
        inputs: 输入信号字典
    
    Returns:
        所有门的输出信号
    """
    # 初始化结果
    results = {}
    
    # 设置输入
    for name, value in inputs.items():
        results[name] = value
    
    # 按拓扑顺序计算
    order = topological_sort(circuit._gates, circuit._connections)
    
    for gate_name in order:
        if gate_name in results:
            continue  # 已经计算过（是输入）
        
        gate = circuit._gates[gate_name]
        gate_inputs = []
        
        # 收集输入
        for from_name, to_name, input_idx in circuit._connections:
            if to_name == gate_name:
                gate_inputs.append((input_idx, results[from_name]))
        
        # 排序并提取值
        gate_inputs.sort()
        inputs = [value for _, value in gate_inputs]
        
        # 计算输出
        output = gate.evaluate(*inputs)
        results[gate_name] = output
    
    return results
```

## 5. 性能优化

### 5.1 缓存机制

```python
class CachedGate(Gate):
    """带缓存的逻辑门"""
    
    def __init__(self, gate):
        self._gate = gate
        self._cache = {}
    
    def evaluate(self, *inputs):
        key = inputs
        if key not in self._cache:
            self._cache[key] = self._gate.evaluate(*inputs)
        return self._cache[key]
    
    def clear_cache(self):
        self._cache.clear()
```

### 5.2 惰性计算

```python
class LazyCircuit(Circuit):
    """惰性计算电路"""
    
    def __init__(self, name="LazyCircuit"):
        super().__init__(name)
        self._dirty = set()
        self._cached_results = {}
    
    def set_input(self, name, value):
        super().set_input(name, value)
        self._dirty.add(name)
        self._propagate_dirty(name)
    
    def _propagate_dirty(self, gate_name):
        """传播脏标记"""
        for from_name, to_name, _ in self._connections:
            if from_name == gate_name:
                self._dirty.add(to_name)
                self._propagate_dirty(to_name)
    
    def evaluate(self):
        """只计算脏节点"""
        order = self._topological_sort()
        
        for gate_name in order:
            if gate_name not in self._dirty:
                continue
            
            gate = self._gates[gate_name]
            inputs = self._get_gate_inputs(gate_name)
            output = gate.evaluate(*inputs)
            self._cached_results[gate_name] = output
            self._dirty.discard(gate_name)
        
        return self._cached_results
```

## 6. 错误处理

### 6.1 输入验证

```python
def validate_inputs(gate, inputs):
    """验证门输入"""
    if len(inputs) != gate.num_inputs:
        raise InvalidInputError(
            f"{gate.name} gate requires {gate.num_inputs} inputs, "
            f"got {len(inputs)}"
        )
    
    for i, inp in enumerate(inputs):
        if inp not in (0, 1):
            raise InvalidInputError(
                f"Invalid input at position {i}: {inp}. "
                f"Must be 0 or 1"
            )
```

### 6.2 连接验证

```python
def validate_connection(circuit, from_name, to_name, input_idx):
    """验证连接"""
    if from_name not in circuit._gates:
        raise ConnectionError(f"Source gate '{from_name}' not found")
    
    if to_name not in circuit._gates:
        raise ConnectionError(f"Target gate '{to_name}' not found")
    
    target_gate = circuit._gates[to_name]
    if input_idx >= target_gate.num_inputs:
        raise ConnectionError(
            f"Input index {input_idx} out of range for "
            f"gate '{to_name}' (max: {target_gate.num_inputs - 1})"
        )
```

## 7. 测试策略

### 7.1 单元测试

```python
import unittest

class TestAndGate(unittest.TestCase):
    def setUp(self):
        self.gate = AndGate()
    
    def test_basic_operation(self):
        self.assertEqual(self.gate.evaluate(0, 0), 0)
        self.assertEqual(self.gate.evaluate(0, 1), 0)
        self.assertEqual(self.gate.evaluate(1, 0), 0)
        self.assertEqual(self.gate.evaluate(1, 1), 1)
    
    def test_invalid_input(self):
        with self.assertRaises(InvalidInputError):
            self.gate.evaluate(0)
        with self.assertRaises(InvalidInputError):
            self.gate.evaluate(0, 0, 0)
    
    def test_truth_table(self):
        table = self.gate.truth_table()
        self.assertEqual(len(table), 4)
```

### 7.2 集成测试

```python
class TestCircuit(unittest.TestCase):
    def test_half_adder(self):
        """测试半加器电路"""
        circuit = Circuit("Half Adder")
        
        # 添加门
        xor_gate = circuit.add_gate(XorGate(), "XOR")
        and_gate = circuit.add_gate(AndGate(), "AND")
        
        # 连接
        circuit.connect("A", "XOR", 0)
        circuit.connect("B", "XOR", 1)
        circuit.connect("A", "AND", 0)
        circuit.connect("B", "AND", 1)
        
        # 测试所有输入组合
        test_cases = [
            (0, 0, 0, 0),
            (0, 1, 1, 0),
            (1, 0, 1, 0),
            (1, 1, 0, 1),
        ]
        
        for a, b, sum_expected, carry_expected in test_cases:
            circuit.set_inputs({"A": a, "B": b})
            results = circuit.evaluate()
            self.assertEqual(results["XOR"], sum_expected)
            self.assertEqual(results["AND"], carry_expected)
```

## 8. 部署和发布

### 8.1 打包配置

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="logic-gates",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[],
    author="Logic Gates Simulator",
    description="A logic gate simulator for learning digital circuits",
    python_requires=">=3.8",
)
```

### 8.2 发布流程

1. 运行测试：`python -m pytest tests/`
2. 构建包：`python setup.py sdist bdist_wheel`
3. 上传到PyPI：`twine upload dist/*`

## 9. 总结

本文档详细描述了逻辑门模拟器的实现细节，包括：
- 核心类和接口设计
- 关键算法实现
- 性能优化策略
- 错误处理机制
- 测试策略

通过这些实现，我们构建了一个功能完整、性能良好、易于扩展的逻辑门模拟器。
