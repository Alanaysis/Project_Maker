# 快速开始指南

## 安装

```bash
# 克隆项目
git clone <repository-url>
cd logic-gates

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 基本使用

### 1. 使用Python API

```python
# 导入逻辑门
from src.gates import AndGate, OrGate, NotGate

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

### 2. 生成真值表

```python
from src.gates import AndGate
from src.truth_table import TruthTableGenerator

and_gate = AndGate()
print(TruthTableGenerator.generate(and_gate))
```

输出：
```
AND Gate Truth Table
----------------------
| IN0  | IN1  | OUT  |
----------------------
|  0   |  0   |  0   |
|  0   |  1   |  0   |
|  1   |  0   |  0   |
|  1   |  1   |  1   |
----------------------
```

### 3. 创建电路

```python
from src.circuit import Circuit
from src.gates import XorGate, AndGate

# 创建半加器电路
circuit = Circuit("Half Adder")
circuit.add_gate(XorGate(), "XOR")
circuit.add_gate(AndGate(), "AND")

# 连接门
circuit.connect("A", "XOR", 0)
circuit.connect("B", "XOR", 1)
circuit.connect("A", "AND", 0)
circuit.connect("B", "AND", 1)

# 设置输入
circuit.set_inputs({"A": 1, "B": 0})

# 计算输出
results = circuit.evaluate()
print(f"Sum: {results['XOR']}, Carry: {results['AND']}")
```

### 4. 使用命令行

```bash
# 显示帮助
python3 -m src.cli --help

# 运行示例
python3 -m src.cli --example and

# 生成真值表
python3 -m src.cli --truth-table AND

# 模拟电路
python3 -m src.cli --circuit half_adder --inputs A=1,B=0
```

## 运行示例

```bash
# 基本逻辑门示例
python3 examples/basic_gates.py

# 电路组合示例
python3 examples/circuit_demo.py

# 真值表示例
python3 examples/truth_table_demo.py
```

## 运行测试

```bash
# 运行所有测试
python3 -m pytest tests/ -v

# 运行特定测试
python3 -m pytest tests/test_gates.py -v

# 运行测试并生成覆盖率报告
python3 -m pytest tests/ --cov=src --cov-report=html
```

## 学习路径

### 初学者

1. 阅读 `docs/01-RESEARCH.md` 了解项目背景
2. 运行 `examples/basic_gates.py` 了解基本逻辑门
3. 阅读 `LEARNING_NOTES.md` 学习核心概念
4. 运行 `examples/circuit_demo.py` 学习电路组合

### 进阶学习

1. 阅读 `docs/02-ARCHITECTURE.md` 了解系统架构
2. 阅读 `docs/03-API.md` 学习API使用
3. 阅读 `docs/04-IMPLEMENTATION.md` 了解实现细节
4. 尝试创建自己的电路

### 高级应用

1. 阅读 `docs/05-DEVELOPMENT.md` 了解开发流程
2. 扩展功能：添加新的逻辑门类型
3. 优化性能：实现缓存机制
4. 贡献代码：提交Pull Request

## 常见问题

### Q: 如何创建自定义逻辑门？

```python
from src.gates import CustomGate

def my_logic(*inputs):
    # 实现你的逻辑
    return int(sum(inputs) > 0)

custom_gate = CustomGate("MY_GATE", 2, my_logic)
result = custom_gate.evaluate(1, 0)  # 返回 1
```

### Q: 如何生成电路的真值表？

```python
from src.truth_table import TruthTableGenerator

# 假设你已经创建了电路
table = circuit.get_truth_table()
print(TruthTableGenerator.format_circuit_table(table, "My Circuit"))
```

### Q: 如何扩展项目？

1. 在 `src/gates.py` 中添加新的逻辑门类
2. 在 `src/registry.py` 中注册新门
3. 在 `tests/test_gates.py` 中添加测试
4. 在 `examples/` 中添加示例

## 获取帮助

- 阅读文档：`docs/` 目录
- 查看示例：`examples/` 目录
- 运行测试：`python3 -m pytest tests/`
- 提交Issue：在GitHub上提交问题

## 下一步

1. 尝试创建更复杂的电路
2. 学习数字电路设计理论
3. 探索硬件描述语言（Verilog/VHDL）
4. 参与开源社区贡献
