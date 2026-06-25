# 逻辑门模拟器 - 架构设计

## 1. 系统概述

逻辑门模拟器是一个用于模拟数字电路的工具，支持基本逻辑门的组合和真值表生成。

## 2. 设计目标

### 2.1 功能目标
- 实现所有基本逻辑门（AND、OR、NOT、XOR、NAND、NOR）
- 支持逻辑门的任意组合
- 自动生成真值表
- 模拟电路运行

### 2.2 非功能目标
- **易用性**：简洁的API设计
- **可扩展性**：支持自定义逻辑门
- **可测试性**：完善的测试覆盖
- **可维护性**：清晰的代码结构

## 3. 架构模式

采用**分层架构**，将系统分为以下层次：

```
┌─────────────────────────────────────┐
│           应用层 (Application)       │
│    - 命令行接口                      │
│    - 示例程序                        │
├─────────────────────────────────────┤
│           核心层 (Core)              │
│    - 逻辑门实现                      │
│    - 电路组合                        │
│    - 真值表生成                      │
├─────────────────────────────────────┤
│           基础层 (Foundation)        │
│    - 信号定义                        │
│    - 门接口                          │
│    - 工具函数                        │
└─────────────────────────────────────┘
```

## 4. 模块设计

### 4.1 基础层 (foundation)

#### 4.1.1 信号模块 (signal)
```python
class Signal:
    """数字信号"""
    HIGH = 1  # 高电平
    LOW = 0   # 低电平
```

#### 4.1.2 门接口 (gate_interface)
```python
from abc import ABC, abstractmethod

class Gate(ABC):
    """逻辑门接口"""
    
    @abstractmethod
    def evaluate(self, *inputs) -> int:
        """计算输出"""
        pass
    
    @abstractmethod
    def truth_table(self) -> list:
        """生成真值表"""
        pass
```

### 4.2 核心层 (core)

#### 4.2.1 基本逻辑门 (gates)

**AND门**
```python
class AndGate(Gate):
    """与门：所有输入为高电平时输出高电平"""
    def evaluate(self, *inputs):
        return all(inputs)
```

**OR门**
```python
class OrGate(Gate):
    """或门：任一输入为高电平时输出高电平"""
    def evaluate(self, *inputs):
        return any(inputs)
```

**NOT门**
```python
class NotGate(Gate):
    """非门：输入取反"""
    def evaluate(self, input):
        return not input
```

**XOR门**
```python
class XorGate(Gate):
    """异或门：输入不同时输出高电平"""
    def evaluate(self, *inputs):
        return sum(inputs) % 2 == 1
```

**NAND门**
```python
class NandGate(Gate):
    """与非门：AND门取反"""
    def evaluate(self, *inputs):
        return not all(inputs)
```

**NOR门**
```python
class NorGate(Gate):
    """或非门：OR门取反"""
    def evaluate(self, *inputs):
        return not any(inputs)
```

#### 4.2.2 电路组合 (circuit)

```python
class Circuit:
    """电路：多个逻辑门的组合"""
    
    def __init__(self):
        self.gates = []
        self.connections = []
    
    def add_gate(self, gate, name=None):
        """添加逻辑门"""
        pass
    
    def connect(self, from_gate, to_gate, input_index=0):
        """连接逻辑门"""
        pass
    
    def evaluate(self, inputs):
        """计算电路输出"""
        pass
    
    def truth_table(self):
        """生成真值表"""
        pass
```

#### 4.2.3 真值表生成器 (truth_table)

```python
class TruthTableGenerator:
    """真值表生成器"""
    
    @staticmethod
    def generate(gate, num_inputs):
        """生成逻辑门的真值表"""
        pass
    
    @staticmethod
    def format_table(table):
        """格式化真值表输出"""
        pass
```

### 4.3 应用层 (application)

#### 4.3.1 命令行接口 (cli)

```python
def main():
    """命令行入口"""
    # 解析参数
    # 执行模拟
    # 输出结果
```

#### 4.3.2 示例程序 (examples)

- 基本逻辑门演示
- 电路组合示例
- 真值表生成示例

## 5. 数据流设计

### 5.1 信号流

```
输入信号 → 逻辑门 → 输出信号
    ↓
多级组合
    ↓
最终输出
```

### 5.2 电路模拟流程

1. **输入阶段**：接收输入信号
2. **传播阶段**：信号通过逻辑门传播
3. **计算阶段**：每个门计算输出
4. **输出阶段**：返回最终结果

## 6. 接口设计

### 6.1 逻辑门接口

```python
class Gate(ABC):
    @abstractmethod
    def evaluate(self, *inputs) -> int:
        """计算输出
        
        Args:
            *inputs: 输入信号（0或1）
        
        Returns:
            输出信号（0或1）
        """
        pass
    
    @abstractmethod
    def truth_table(self) -> List[Tuple]:
        """生成真值表
        
        Returns:
            真值表，每个元素为(输入组合, 输出)
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """门名称"""
        pass
    
    @property
    @abstractmethod
    def num_inputs(self) -> int:
        """输入数量"""
        pass
```

### 6.2 电路接口

```python
class Circuit:
    def add_gate(self, gate: Gate, name: str) -> None:
        """添加逻辑门到电路"""
        pass
    
    def connect(self, from_name: str, to_name: str, input_idx: int = 0) -> None:
        """连接两个逻辑门"""
        pass
    
    def set_inputs(self, inputs: Dict[str, int]) -> None:
        """设置电路输入"""
        pass
    
    def evaluate(self) -> Dict[str, int]:
        """计算电路输出"""
        pass
    
    def get_truth_table(self) -> List[Dict]:
        """生成完整真值表"""
        pass
```

## 7. 错误处理设计

### 7.1 异常类型

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

### 7.2 错误处理策略

1. **输入验证**：检查输入信号是否为0或1
2. **连接验证**：检查连接是否有效
3. **电路验证**：检查电路是否完整
4. **异常传播**：向上层传播异常

## 8. 性能设计

### 8.1 性能目标
- **小规模电路**：< 1ms
- **中规模电路**：< 100ms
- **大规模电路**：< 1s

### 8.2 优化策略

1. **缓存机制**：缓存中间结果
2. **惰性计算**：只在需要时计算
3. **并行处理**：独立门并行计算
4. **内存优化**：减少不必要的数据复制

## 9. 可扩展性设计

### 9.1 自定义逻辑门

```python
class CustomGate(Gate):
    """自定义逻辑门基类"""
    
    def __init__(self, name, num_inputs, logic_func):
        self._name = name
        self._num_inputs = num_inputs
        self._logic_func = logic_func
    
    def evaluate(self, *inputs):
        return self._logic_func(*inputs)
```

### 9.2 插件机制

```python
class GateRegistry:
    """逻辑门注册表"""
    
    _gates = {}
    
    @classmethod
    def register(cls, name, gate_class):
        """注册自定义逻辑门"""
        cls._gates[name] = gate_class
    
    @classmethod
    def get(cls, name):
        """获取逻辑门"""
        return cls._gates.get(name)
```

## 10. 测试设计

### 10.1 单元测试
- 每个逻辑门的独立测试
- 边界条件测试
- 异常情况测试

### 10.2 集成测试
- 电路组合测试
- 多级电路测试
- 复杂电路测试

### 10.3 性能测试
- 大规模电路测试
- 并发测试
- 内存使用测试

## 11. 部署设计

### 11.1 依赖管理
- Python 3.8+
- 无外部依赖（核心功能）

### 11.2 安装方式
- pip安装
- 源码安装
- Docker容器

### 11.3 运行环境
- Linux、macOS、Windows
- 命令行界面
- Python环境

## 12. 总结

本架构设计采用分层架构，将系统分为基础层、核心层和应用层。通过清晰的接口设计和模块划分，实现了高内聚、低耦合的系统结构。同时，考虑了可扩展性、性能和错误处理等方面，为项目的长期发展奠定了基础。
