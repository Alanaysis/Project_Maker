# 逻辑门模拟器 - API设计

## 1. 概述

本文档定义了逻辑门模拟器的API接口，包括核心类、方法和使用示例。

## 2. 核心API

### 2.1 信号定义

```python
class Signal:
    """数字信号常量"""
    HIGH = 1  # 高电平
    LOW = 0   # 低电平
    
    @staticmethod
    def validate(value):
        """验证信号值是否有效"""
        if value not in (0, 1):
            raise InvalidInputError(f"Invalid signal: {value}")
        return value
```

### 2.2 逻辑门基类

```python
from abc import ABC, abstractmethod
from typing import List, Tuple

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
        """计算输出
        
        Args:
            *inputs: 输入信号，每个为0或1
            
        Returns:
            输出信号，0或1
            
        Raises:
            InvalidInputError: 输入信号无效
        """
        pass
    
    def truth_table(self) -> List[Tuple[List[int], int]]:
        """生成真值表
        
        Returns:
            真值表，每个元素为([输入组合], 输出)
        """
        table = []
        for inputs in self._generate_inputs():
            output = self.evaluate(*inputs)
            table.append((list(inputs), output))
        return table
    
    def _generate_inputs(self):
        """生成所有输入组合"""
        from itertools import product
        return product([0, 1], repeat=self.num_inputs)
    
    def __call__(self, *inputs):
        """使门可调用"""
        return self.evaluate(*inputs)
```

### 2.3 基本逻辑门

#### AND门

```python
class AndGate(Gate):
    """与门：所有输入为1时输出1"""
    
    @property
    def name(self):
        return "AND"
    
    @property
    def num_inputs(self):
        return 2
    
    def evaluate(self, *inputs):
        if len(inputs) != self.num_inputs:
            raise InvalidInputError(f"AND gate requires {self.num_inputs} inputs")
        return int(all(inputs))
```

#### OR门

```python
class OrGate(Gate):
    """或门：任一输入为1时输出1"""
    
    @property
    def name(self):
        return "OR"
    
    @property
    def num_inputs(self):
        return 2
    
    def evaluate(self, *inputs):
        if len(inputs) != self.num_inputs:
            raise InvalidInputError(f"OR gate requires {self.num_inputs} inputs")
        return int(any(inputs))
```

#### NOT门

```python
class NotGate(Gate):
    """非门：输入取反"""
    
    @property
    def name(self):
        return "NOT"
    
    @property
    def num_inputs(self):
        return 1
    
    def evaluate(self, *inputs):
        if len(inputs) != self.num_inputs:
            raise InvalidInputError(f"NOT gate requires {self.num_inputs} inputs")
        return int(not inputs[0])
```

#### XOR门

```python
class XorGate(Gate):
    """异或门：输入不同时输出1"""
    
    @property
    def name(self):
        return "XOR"
    
    @property
    def num_inputs(self):
        return 2
    
    def evaluate(self, *inputs):
        if len(inputs) != self.num_inputs:
            raise InvalidInputError(f"XOR gate requires {self.num_inputs} inputs")
        return int(sum(inputs) % 2 == 1)
```

#### NAND门

```python
class NandGate(Gate):
    """与非门：AND门取反"""
    
    @property
    def name(self):
        return "NAND"
    
    @property
    def num_inputs(self):
        return 2
    
    def evaluate(self, *inputs):
        if len(inputs) != self.num_inputs:
            raise InvalidInputError(f"NAND gate requires {self.num_inputs} inputs")
        return int(not all(inputs))
```

#### NOR门

```python
class NorGate(Gate):
    """或非门：OR门取反"""
    
    @property
    def name(self):
        return "NOR"
    
    @property
    def num_inputs(self):
        return 2
    
    def evaluate(self, *inputs):
        if len(inputs) != self.num_inputs:
            raise InvalidInputError(f"NOR gate requires {self.num_inputs} inputs")
        return int(not any(inputs))
```

### 2.4 自定义逻辑门

```python
class CustomGate(Gate):
    """自定义逻辑门"""
    
    def __init__(self, name: str, num_inputs: int, logic_func):
        """
        Args:
            name: 门名称
            num_inputs: 输入数量
            logic_func: 逻辑函数，接收输入参数，返回0或1
        """
        self._name = name
        self._num_inputs = num_inputs
        self._logic_func = logic_func
    
    @property
    def name(self):
        return self._name
    
    @property
    def num_inputs(self):
        return self._num_inputs
    
    def evaluate(self, *inputs):
        if len(inputs) != self.num_inputs:
            raise InvalidInputError(f"{self.name} requires {self.num_inputs} inputs")
        return int(self._logic_func(*inputs))
```

### 2.5 电路类

```python
class Circuit:
    """电路：多个逻辑门的组合"""
    
    def __init__(self, name: str = "Circuit"):
        """
        Args:
            name: 电路名称
        """
        self.name = name
        self._gates = {}
        self._connections = []
        self._inputs = {}
        self._outputs = {}
    
    def add_gate(self, gate: Gate, name: str = None) -> str:
        """添加逻辑门到电路
        
        Args:
            gate: 逻辑门实例
            name: 门的名称（可选，默认使用门的类型名）
            
        Returns:
            门的名称
            
        Raises:
            CircuitError: 名称已存在
        """
        if name is None:
            name = f"{gate.name}_{len(self._gates)}"
        if name in self._gates:
            raise CircuitError(f"Gate '{name}' already exists")
        self._gates[name] = gate
        return name
    
    def connect(self, from_name: str, to_name: str, input_idx: int = 0):
        """连接两个逻辑门
        
        Args:
            from_name: 源门名称
            to_name: 目标门名称
            input_idx: 目标门的输入索引
            
        Raises:
            CircuitError: 门不存在或连接无效
        """
        if from_name not in self._gates:
            raise CircuitError(f"Gate '{from_name}' not found")
        if to_name not in self._gates:
            raise CircuitError(f"Gate '{to_name}' not found")
        self._connections.append((from_name, to_name, input_idx))
    
    def set_input(self, name: str, value: int):
        """设置输入信号
        
        Args:
            name: 输入名称
            value: 信号值（0或1）
        """
        Signal.validate(value)
        self._inputs[name] = value
    
    def set_inputs(self, inputs: dict):
        """批量设置输入信号
        
        Args:
            inputs: 输入字典，键为名称，值为信号
        """
        for name, value in inputs.items():
            self.set_input(name, value)
    
    def evaluate(self) -> dict:
        """计算电路输出
        
        Returns:
            输出字典，键为门名称，值为输出信号
        """
        # 实现信号传播算法
        pass
    
    def get_truth_table(self) -> List[dict]:
        """生成完整真值表
        
        Returns:
            真值表，每个元素为一行
        """
        pass
```

### 2.6 真值表生成器

```python
class TruthTableGenerator:
    """真值表生成器"""
    
    @staticmethod
    def generate(gate: Gate) -> str:
        """生成格式化的真值表
        
        Args:
            gate: 逻辑门实例
            
        Returns:
            格式化的真值表字符串
        """
        table = gate.truth_table()
        return TruthTableGenerator.format(table, gate.name)
    
    @staticmethod
    def format(table: List[Tuple], name: str = "") -> str:
        """格式化真值表
        
        Args:
            table: 真值表数据
            name: 表名称
            
        Returns:
            格式化的字符串
        """
        if not table:
            return ""
        
        # 计算列宽
        num_inputs = len(table[0][0])
        col_width = max(6, len(name) + 2)
        
        # 生成表头
        header = " | ".join([f"IN{i:^{col_width}}" for i in range(num_inputs)])
        header += f" | {'OUT':^{col_width}} |"
        
        # 生成分隔线
        separator = "-" * len(header)
        
        # 生成数据行
        rows = []
        for inputs, output in table:
            row = " | ".join([f"{inp:^{col_width}}" for inp in inputs])
            row += f" | {output:^{col_width}} |"
            rows.append(row)
        
        # 组合结果
        result = [name, separator, header, separator]
        result.extend(rows)
        result.append(separator)
        
        return "\n".join(result)
```

### 2.7 门注册表

```python
class GateRegistry:
    """逻辑门注册表"""
    
    _gates = {}
    
    @classmethod
    def register(cls, name: str, gate_class):
        """注册逻辑门
        
        Args:
            name: 门名称
            gate_class: 门类
        """
        cls._gates[name] = gate_class
    
    @classmethod
    def get(cls, name: str):
        """获取逻辑门
        
        Args:
            name: 门名称
            
        Returns:
            门类，如果不存在返回None
        """
        return cls._gates.get(name)
    
    @classmethod
    def create(cls, name: str, *args, **kwargs):
        """创建逻辑门实例
        
        Args:
            name: 门名称
            *args, **kwargs: 传递给门构造函数的参数
            
        Returns:
            门实例
        """
        gate_class = cls.get(name)
        if gate_class is None:
            raise ValueError(f"Unknown gate: {name}")
        return gate_class(*args, **kwargs)
    
    @classmethod
    def list_gates(cls):
        """列出所有注册的门"""
        return list(cls._gates.keys())
```

## 3. 异常类

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

## 4. 工具函数

```python
def print_truth_table(gate: Gate):
    """打印真值表"""
    print(TruthTableGenerator.generate(gate))

def create_circuit_from_description(description: dict) -> Circuit:
    """从描述创建电路
    
    Args:
        description: 电路描述字典
        
    Returns:
        电路实例
    """
    circuit = Circuit(description.get("name", "Circuit"))
    
    # 添加门
    for gate_desc in description.get("gates", []):
        gate = GateRegistry.create(gate_desc["type"])
        circuit.add_gate(gate, gate_desc.get("name"))
    
    # 添加连接
    for conn in description.get("connections", []):
        circuit.connect(conn["from"], conn["to"], conn.get("input_idx", 0))
    
    return circuit
```

## 5. 使用示例

### 5.1 基本使用

```python
from logic_gates import AndGate, OrGate, NotGate

# 创建逻辑门
and_gate = AndGate()
or_gate = OrGate()
not_gate = NotGate()

# 计算输出
result = and_gate.evaluate(1, 1)  # 返回 1
result = or_gate.evaluate(0, 1)   # 返回 1
result = not_gate.evaluate(0)     # 返回 1

# 使用可调用接口
result = and_gate(1, 1)  # 返回 1
```

### 5.2 真值表生成

```python
from logic_gates import AndGate, TruthTableGenerator

and_gate = AndGate()
print(TruthTableGenerator.generate(and_gate))
```

输出：
```
AND
------------------------------------
|   IN0   |   IN1   |   OUT   |
------------------------------------
|    0    |    0    |    0    |
|    0    |    1    |    0    |
|    1    |    0    |    0    |
|    1    |    1    |    1    |
------------------------------------
```

### 5.3 电路组合

```python
from logic_gates import Circuit, AndGate, OrGate, NotGate

# 创建电路
circuit = Circuit("Half Adder")

# 添加门
xor_gate = circuit.add_gate(XorGate(), "XOR")
and_gate = circuit.add_gate(AndGate(), "AND")

# 连接门（需要先设置输入）
circuit.set_inputs({"A": 1, "B": 0})

# 计算输出
result = circuit.evaluate()
```

### 5.4 自定义逻辑门

```python
from logic_gates import CustomGate

# 创建自定义门：多数表决器
def majority(*inputs):
    return int(sum(inputs) > len(inputs) / 2)

majority_gate = CustomGate("MAJ", 3, majority)
result = majority_gate.evaluate(1, 1, 0)  # 返回 1
```

## 6. 命令行接口

### 6.1 基本用法

```bash
# 显示帮助
python -m logic_gates --help

# 运行示例
python -m logic_gates --example and

# 生成真值表
python -m logic_gates --truth-table AND

# 模拟电路
python -m logic_gates --circuit half_adder --inputs A=1,B=0
```

### 6.2 命令行参数

```
usage: logic_gates [-h] [--example EXAMPLE] [--truth-table GATE]
                   [--circuit CIRCUIT] [--inputs INPUTS] [--verbose]

逻辑门模拟器

optional arguments:
  -h, --help            show this help message and exit
  --example EXAMPLE     运行示例 (and, or, not, xor, circuit)
  --truth-table GATE    生成真值表 (AND, OR, NOT, XOR, NAND, NOR)
  --circuit CIRCUIT     模拟电路 (half_adder, full_adder, etc.)
  --inputs INPUTS       输入信号 (A=1,B=0,...)
  --verbose             详细输出
```

## 7. 配置选项

### 7.1 全局配置

```python
class Config:
    """全局配置"""
    
    # 输出格式
    OUTPUT_FORMAT = "table"  # table, json, csv
    
    # 信号表示
    SIGNAL_HIGH = 1
    SIGNAL_LOW = 0
    
    # 真值表格式
    TABLE_ALIGNMENT = "center"  # left, center, right
    TABLE_SEPARATOR = "|"
    
    # 调试模式
    DEBUG = False
```

### 7.2 环境变量

```bash
LOGIC_GATES_OUTPUT_FORMAT=table
LOGIC_GATES_DEBUG=false
LOGIC_GATES_SIGNAL_HIGH=1
LOGIC_GATES_SIGNAL_LOW=0
```

## 8. 版本信息

```python
__version__ = "1.0.0"
__author__ = "Logic Gates Simulator Team"
__license__ = "MIT"
```

## 9. 总结

本API设计遵循以下原则：
1. **简洁性**：接口简单直观
2. **一致性**：所有门遵循相同接口
3. **可扩展性**：支持自定义门和电路
4. **易用性**：提供多种使用方式

通过这些API，用户可以轻松地创建、组合和模拟逻辑门电路。
