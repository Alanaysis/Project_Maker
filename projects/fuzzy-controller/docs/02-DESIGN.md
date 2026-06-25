# 设计文档

## 1. 系统概述

模糊控制器是一个从零实现的模糊逻辑控制系统，支持 Mamdani 和 Sugeno 两种推理方式，并提供温度控制和速度控制的实际应用。

### 1.1 设计目标

- **教育性**：清晰展示模糊逻辑的核心概念
- **模块化**：各组件职责单一，易于理解和扩展
- **可测试**：每个组件都可以独立测试
- **实用性**：提供完整的控制示例和实际应用

### 1.2 核心循环

```
输入 → 模糊化 → 规则推理 → 去模糊化 → 输出
```

## 2. 模块设计

### 2.1 模块结构

```
fuzzy-controller/
├── src/
│   ├── __init__.py          # 包初始化
│   ├── fuzzy_set.py         # 模糊集合模块
│   ├── fuzzifier.py         # 模糊化模块
│   ├── rule_engine.py       # 规则引擎模块 (Mamdani + Sugeno)
│   ├── defuzzifier.py       # 去模糊化模块
│   ├── controller.py        # 控制器模块
│   └── applications.py      # 实际应用 (温度/速度控制)
├── tests/
│   ├── __init__.py
│   ├── test_fuzzy_set.py
│   ├── test_fuzzifier.py
│   ├── test_rule_engine.py
│   ├── test_defuzzifier.py
│   ├── test_controller.py
│   ├── test_sugeno.py       # Sugeno 推理测试
│   └── test_applications.py # 应用测试
├── examples/
│   └── example_usage.py
└── docs/
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

### 2.2 模块职责

#### fuzzy_set.py - 模糊集合模块

**职责**：
- 定义隶属函数基类
- 实现常见隶属函数（三角形、梯形、高斯、钟形）
- 实现模糊集合类
- 提供模糊集合运算（并、交、补）

**核心类**：
- `MembershipFunction`: 隶属函数基类
- `TriangularMF`: 三角形隶属函数
- `TrapezoidalMF`: 梯形隶属函数
- `GaussianMF`: 高斯隶属函数
- `BellShapedMF`: 钟形隶属函数
- `FuzzySet`: 模糊集合类

#### fuzzifier.py - 模糊化模块

**职责**：
- 将精确输入转换为模糊值
- 管理输入变量的模糊集合

**核心类**：
- `Fuzzifier`: 模糊化器

#### rule_engine.py - 规则引擎模块

**职责**：
- 定义模糊规则 (IF-THEN)
- 执行规则推理
- 支持 Mamdani 推理（裁剪+聚合）
- 支持 Sugeno (TSK) 推理（加权平均）

**核心类**：
- `FuzzyRule`: 模糊规则
- `RuleEngine`: 规则引擎

#### defuzzifier.py - 去模糊化模块

**职责**：
- 将模糊输出转换为精确值
- 支持多种去模糊化方法

**核心类**：
- `Defuzzifier`: 去模糊化器

**支持方法**：
- `cog`: 重心法 (Center of Gravity)
- `mom`: 最大隶属度法 (Mean of Maximum)
- `cos`: 面积中心法 (Center of Sums, 使用梯形积分)
- `wa`: 加权平均法

#### controller.py - 控制器模块

**职责**：
- 组合所有组件
- 提供 Mamdani 控制接口
- 提供 Sugeno 控制接口

**核心类**：
- `FuzzyController`: 模糊控制器

#### applications.py - 实际应用模块

**职责**：
- 提供预配置的温度控制和速度控制应用
- 封装完整的模糊控制系统配置

**核心类**：
- `TemperatureController`: 温度控制器
- `SpeedController`: 速度控制器

## 3. 类图

```
┌─────────────────────────────────────────────────────────────┐
│                      FuzzyController                        │
├─────────────────────────────────────────────────────────────┤
│ - fuzzifier: Fuzzifier                                      │
│ - rule_engine: RuleEngine                                   │
│ - defuzzifier: Defuzzifier                                  │
│ - input_variables: Dict[str, Dict[str, FuzzySet]]          │
│ - output_variables: Dict[str, Dict[str, FuzzySet]]         │
├─────────────────────────────────────────────────────────────┤
│ + add_input_variable()                                      │
│ + add_output_variable()                                     │
│ + add_rule()                                                │
│ + control()          # Mamdani 推理                         │
│ + control_sugeno()   # Sugeno 推理                          │
│ + control_step_by_step()                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 组合
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Fuzzifier   │     │  RuleEngine  │     │ Defuzzifier  │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ + fuzzify()  │     │ + add_rule() │     │ + defuzzify()│
└──────────────┘     │ + infer()    │     └──────────────┘
        │            │ + infer_     │             │
        │            │   mamdani()  │             │
        ▼            │ + infer_     │             ▼
┌──────────────┐     │   sugeno()   │     ┌──────────────┐
│  FuzzySet    │     └──────────────┘     │ Membership   │
├──────────────┘             │             │  Function    │
│ + membership │             │             ├──────────────┤
│ + complement │     ┌───────▼──────┐     │ + __call__() │
│ + intersect  │     │  FuzzyRule   │     └──────────────┘
│ + union      │     ├──────────────┤
└──────────────┘     │ + evaluate() │
                     └──────────────┘

┌──────────────────────────────────────────────┐
│              Applications                     │
├──────────────────────────────────────────────┤
│  TemperatureController    SpeedController     │
│  - setpoint               - setpoint          │
│  - compute()              - compute()         │
│  - reset()                - reset()           │
└──────────────────────────────────────────────┘
```

## 4. 数据流

### 4.1 Mamdani 控制流程

```
1. 接收精确输入
   ↓
2. 模糊化
   - 对每个输入变量，计算其在各模糊集合中的隶属度
   - 输出：{变量名: {集合名: 隶属度}}
   ↓
3. 规则推理 (Mamdani)
   - 对每条规则，计算激活强度
   - 使用激活强度裁剪输出隶属函数
   - 聚合所有规则的输出（取最大值）
   ↓
4. 去模糊化
   - 将模糊输出转换为精确值
   - 输出：{变量名: 精确值}
```

### 4.2 Sugeno 控制流程

```
1. 接收精确输入
   ↓
2. 模糊化
   - 计算各模糊集合的隶属度
   ↓
3. 规则推理 (Sugeno)
   - 对每条规则，计算激活强度
   - 计算每条规则的输出函数值
   - 加权平均得到最终输出
   ↓
4. 输出精确值（无需去模糊化）
```

### 4.3 数据格式

**模糊输入**：
```python
{
    'temperature': {
        'cold': 0.0,
        'warm': 0.5,
        'hot': 0.5
    }
}
```

**精确输出**：
```python
{
    'fan_speed': 65.5
}
```

## 5. 扩展性设计

### 5.1 添加新的隶属函数

继承 `MembershipFunction` 基类：

```python
class CustomMF(MembershipFunction):
    def __init__(self, name, param1, param2):
        super().__init__(name)
        self.param1 = param1
        self.param2 = param2

    def __call__(self, x):
        # 实现自定义隶属函数
        pass
```

### 5.2 添加新的去模糊化方法

在 `Defuzzifier` 类中添加新方法：

```python
def _custom_method(self, x, mf_values):
    # 实现自定义去模糊化方法
    pass
```

### 5.3 添加新的应用

创建新的控制器类，封装完整的模糊系统配置：

```python
class CustomController:
    def __init__(self):
        self.controller = FuzzyController()
        self._build_system()

    def _build_system(self):
        # 定义隶属函数、规则等
        pass

    def compute(self, *inputs):
        return self.controller.control(...)
```

## 6. 性能考虑

- 使用 NumPy 进行批量计算
- 避免不必要的循环
- 预计算常用值
- 使用向量化操作

## 7. 依赖关系

- **必需**：numpy
- **可选**：matplotlib（用于绘图）
- **测试**：pytest
