# 热力学模拟 (Thermodynamics Simulation)

## 项目描述 / Project Description

**中文**: 本项目实现热传导和热对流数值模拟，帮助学习者理解热力学基本原理。通过有限差分法求解热传导方程，可视化温度场随时间和空间的演化过程。

**English**: This project implements numerical simulation of heat conduction and convection, helping learners understand fundamental principles of thermodynamics. It solves the heat conduction equation using finite difference methods and visualizes the evolution of temperature fields over time and space.

---

## 学习目标 / Learning Objectives

### 热力学原理 / Thermodynamics Principles
- 理解热传导、热对流和热辐射三种传热方式
- 掌握傅里叶热传导定律
- 理解热扩散系数和热阻的概念

### 数值方法 / Numerical Methods
- 掌握有限差分法 (Finite Difference Method)
- 理解显式和隐式时间积分方法的差异
- 掌握 Crank-Nicolson 方法
- 理解数值稳定性条件 (傅里叶数)

### 边界条件 / Boundary Conditions
- Dirichlet 边界 (第一类): 指定边界温度
- Neumann 边界 (第二类): 指定边界热流
- Robin 边界 (第三类): 对流换热条件

---

## 项目结构 / Project Structure

```
thermodynamics/
├── src/
│   ├── __init__.py              # 包初始化
│   ├── heat_conduction.py       # 热传导方程求解器
│   ├── boundary_conditions.py   # 边界条件模块
│   ├── heat_source.py           # 热源建模
│   └── analysis.py              # 稳态和瞬态分析
├── examples/
│   ├── example_1d_rod.py        # 一维杆热传导
│   ├── example_2d_plate.py      # 二维平板温度分布
│   ├── example_transient.py     # 瞬态热传递
│   └── example_boundary_effects.py  # 边界条件影响
├── tests/
│   └── test_heat_conduction.py  # 单元测试
├── requirements.txt             # 依赖
└── README.md                    # 本文件
```

---

## 快速开始 / Quick Start

### 安装依赖 / Install Dependencies

```bash
pip install -r requirements.txt
```

### 运行示例 / Run Examples

```bash
# 一维杆热传导
python examples/example_1d_rod.py

# 二维平板温度分布
python examples/example_2d_plate.py

# 瞬态热传递
python examples/example_transient.py

# 边界条件影响对比
python examples/example_boundary_effects.py
```

### 运行测试 / Run Tests

```bash
python run_tests.py
# 或
python -m pytest tests/ -v
```

---

## 传热理论基础 / Heat Transfer Theory Background

### 傅里叶热传导定律 / Fourier's Law of Heat Conduction

热流密度与温度梯度成正比：

```
q = -k ∇T
```

其中：
- `q` - 热流密度 (W/m²)
- `k` - 热导率 (W/(m·K))
- `∇T` - 温度梯度 (K/m)

负号表示热量从高温流向低温。

### 热传导方程 / Heat Conduction Equation

```
ρc ∂T/∂t = ∇·(k∇T) + Q
```

其中：
- `T` - 温度 (K 或 °C)
- `t` - 时间 (s)
- `ρ` - 密度 (kg/m³)
- `c` - 比热容 (J/(kg·K))
- `k` - 热导率 (W/(m·K))
- `Q` - 热源功率密度 (W/m³)

### 热扩散系数 / Thermal Diffusivity

```
α = k / (ρc)
```

热扩散系数表示材料传播热量的能力。α 越大，温度均衡越快。

### 无量纲数 / Dimensionless Numbers

| 无量纲数 | 公式 | 物理意义 |
|---------|------|---------|
| 傅里叶数 Fo | αt/L² | 无量纲时间，热扩散速率与储能速率之比 |
| 毕渥数 Bi | hL/k | 表面对流换热与内部传导换热之比 |
| 普朗特数 Pr | ν/α | 动量扩散率与热扩散率之比 |

### 数值方法 / Numerical Methods

#### 显式方法 (Explicit Method)
- 格式简单，易于实现
- 稳定性条件: Fo ≤ 0.5
- 需要小时间步长

#### 隐式方法 (Implicit Method)
- 需要求解线性方程组
- 无条件稳定
- 可以使用较大时间步长

#### Crank-Nicolson 方法
- 对时间二阶精度
- 无条件稳定
- 结合了显式和隐式的优点

---

## 材料参数参考 / Material Properties Reference

| 材料 | 热导率 k (W/(m·K)) | 密度 ρ (kg/m³) | 比热容 c (J/(kg·K)) |
|------|-------------------|----------------|-------------------|
| 铝 | 237 | 2700 | 900 |
| 铜 | 401 | 8960 | 385 |
| 钢 | 50 | 7800 | 500 |
| 玻璃 | 1.05 | 2500 | 840 |
| 水 | 0.6 | 1000 | 4186 |

---

## 学习建议 / Learning Suggestions

1. **先理解物理**: 在运行代码前，先理解热传导方程的物理意义
2. **从简单开始**: 先运行一维示例，再尝试二维
3. **改变参数**: 尝试修改材料参数、边界条件，观察结果变化
4. **对比方法**: 对比显式和隐式方法的计算效率和稳定性
5. **验证解析解**: 将数值解与解析解对比，验证代码正确性

---

## License

MIT License
