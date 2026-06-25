# 模糊控制器 (Fuzzy Controller)

从零实现模糊逻辑控制系统，支持 Mamdani 和 Sugeno 两种推理方式，包含温度控制和速度控制的实际应用。

## 项目概述

本项目实现了完整的模糊控制系统，包括：

- **模糊化**：三角形、梯形、高斯、钟形隶属函数
- **模糊规则**：IF-THEN 规则，支持 AND/OR/NOT 操作
- **推理引擎**：Mamdani 推理（裁剪+聚合）和 Sugeno 推理（加权平均）
- **去模糊化**：重心法、最大隶属度法、面积中心法、加权平均法
- **实际应用**：温度控制器、速度控制器

## 核心概念

### 模糊控制循环

```
输入 → 模糊化 → 规则推理 → 去模糊化 → 输出
```

### Mamdani vs Sugeno

| 特性 | Mamdani | Sugeno |
|------|---------|--------|
| 结论部分 | 模糊集合 | 线性函数 |
| 去模糊化 | 需要 (COG/MOM等) | 加权平均 |
| 计算复杂度 | 较高 | 较低 |
| 可解释性 | 好 | 一般 |

## 项目结构

```
fuzzy-controller/
├── README.md                    # 项目说明
├── requirements.txt             # 依赖
├── src/                         # 源代码
│   ├── __init__.py
│   ├── fuzzy_set.py            # 模糊集合 (隶属函数)
│   ├── fuzzifier.py            # 模糊化
│   ├── rule_engine.py          # 规则引擎 (Mamdani + Sugeno)
│   ├── defuzzifier.py          # 去模糊化
│   ├── controller.py           # 控制器
│   └── applications.py         # 温度/速度控制应用
├── tests/                       # 测试 (84 个测试用例)
│   ├── test_fuzzy_set.py
│   ├── test_fuzzifier.py
│   ├── test_rule_engine.py
│   ├── test_defuzzifier.py
│   ├── test_controller.py
│   ├── test_sugeno.py
│   └── test_applications.py
├── examples/                    # 示例
│   └── example_usage.py
└── docs/                        # 文档
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 快速开始

### 安装依赖

```bash
pip install numpy matplotlib pytest
```

### 基本使用 (Mamdani)

```python
from src.fuzzy_set import FuzzySet, TriangularMF
from src.rule_engine import FuzzyRule
from src.controller import FuzzyController

# 创建控制器
controller = FuzzyController()

# 定义输入变量
temp_sets = {
    'cold': FuzzySet('cold', TriangularMF('cold', 0, 0, 20)),
    'warm': FuzzySet('warm', TriangularMF('warm', 10, 20, 30)),
    'hot': FuzzySet('hot', TriangularMF('hot', 20, 40, 40))
}
controller.add_input_variable('temperature', temp_sets)

# 定义输出变量
fan_sets = {
    'slow': FuzzySet('slow', TriangularMF('slow', 0, 0, 50)),
    'medium': FuzzySet('medium', TriangularMF('medium', 25, 50, 75)),
    'fast': FuzzySet('fast', TriangularMF('fast', 50, 100, 100))
}
controller.add_output_variable('fan_speed', fan_sets, universe=(0, 100))

# 添加规则
controller.add_rules([
    FuzzyRule([('temperature', 'cold', 'IS')], [('fan_speed', 'slow')]),
    FuzzyRule([('temperature', 'warm', 'IS')], [('fan_speed', 'medium')]),
    FuzzyRule([('temperature', 'hot', 'IS')], [('fan_speed', 'fast')]),
])

# 控制
output = controller.control({'temperature': 25})
print(f"风扇转速: {output['fan_speed']:.1f}%")
```

### Sugeno 推理

```python
controller = FuzzyController()
# ... (添加变量和规则，同上)

# 零阶 Sugeno 参数: 每条规则输出常数
sugeno_params = {
    'power': [(20.0,), (50.0,), (90.0,)]
}

result, details = controller.control_sugeno(
    {'temperature': 25}, sugeno_params
)
print(f"功率: {result['power']:.1f}%")
```

### 温度控制应用

```python
from src.applications import TemperatureController

controller = TemperatureController(setpoint=25.0)
power = controller.compute(current_temp=20.0)
print(f"加热功率: {power:+.1f}%")
```

### 速度控制应用

```python
from src.applications import SpeedController

controller = SpeedController(setpoint=60.0)
throttle = controller.compute(current_speed=40.0)
print(f"油门: {throttle:+.1f}%")
```

### 运行示例

```bash
cd projects/fuzzy-controller
python3 examples/example_usage.py
```

## API 文档

### 隶属函数

| 类 | 参数 | 说明 |
|---|---|---|
| `TriangularMF` | a, b, c | 三角形 |
| `TrapezoidalMF` | a, b, c, d | 梯形 |
| `GaussianMF` | mean, sigma | 高斯 |
| `BellShapedMF` | a, b, c | 钟形 |

### FuzzyController

| 方法 | 说明 |
|---|---|
| `add_input_variable(name, sets)` | 添加输入变量 |
| `add_output_variable(name, sets, universe)` | 添加输出变量 |
| `add_rule(rule)` | 添加规则 |
| `control(inputs)` | Mamdani 控制 |
| `control_sugeno(inputs, params)` | Sugeno 控制 |
| `control_step_by_step(inputs)` | 逐步执行 (调试) |

### TemperatureController

| 方法 | 说明 |
|---|---|
| `__init__(setpoint, method)` | 设定温度、去模糊化方法 |
| `compute(current_temp)` | 计算加热/制冷功率 |
| `reset()` | 重置状态 |

### SpeedController

| 方法 | 说明 |
|---|---|
| `__init__(setpoint, method)` | 设定速度、去模糊化方法 |
| `compute(current_speed)` | 计算油门/制动力 |
| `reset()` | 重置状态 |

## 测试

```bash
cd projects/fuzzy-controller
python3 -m pytest tests/ -v
```

84 个测试用例全部通过，覆盖：
- 隶属函数 (三角/梯形/高斯/钟形)
- 模糊集合运算 (并/交/补)
- 模糊化
- 规则引擎 (AND/OR/NOT)
- Mamdani 推理
- Sugeno 推理 (零阶/一阶)
- 去模糊化 (COG/MOM/COS/WA)
- 温度控制应用
- 速度控制应用

## 应用场景

1. **温度控制**：加热/制冷系统功率控制
2. **速度控制**：电机/车辆速度调节
3. **工业过程控制**：压力、流量、液位控制
4. **消费电子**：空调、洗衣机、相机对焦

## 学习资源

- [Fuzzy Logic - Wikipedia](https://en.wikipedia.org/wiki/Fuzzy_logic)
- [Fuzzy Control Systems](https://en.wikipedia.org/wiki/Fuzzy_control_system)
- [scikit-fuzzy](https://scikit-fuzzy.github.io/scikit-fuzzy/)
- Timothy J. Ross, "Fuzzy Logic with Engineering Applications"

## 许可证

本项目仅用于学习目的。
