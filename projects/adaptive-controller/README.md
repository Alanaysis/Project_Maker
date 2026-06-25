# 自适应控制器 (Adaptive Controller)

实现模型参考自适应控制 (MRAC)、自校正控制 (STR) 算法，支持参数自动调整，包含温度控制和电机控制实际应用示例。

## 项目概述

自适应控制器是一种能够根据系统动态特性自动调整控制参数的控制器。本项目实现了：

- **模型参考自适应控制 (MRAC)**：使被控系统输出跟踪参考模型的期望行为
- **自校正控制 (STR)**：在线估计系统参数，根据估计参数设计控制器
- **MIT 规则**：基于梯度下降最小化误差平方
- **Lyapunov 方法**：基于 Lyapunov 稳定性理论，保证系统稳定
- **参数估计**：在线估计系统参数，支持 RLS、梯度下降等方法
- **实际应用**：温度控制、电机速度控制

## 核心概念

### 自适应控制循环

```
系统输出 --> 参数估计 --> 控制器更新 --> 控制输出
```

### 模型参考自适应控制 (MRAC)

1. **参考模型**：定义期望的闭环系统行为
2. **自适应律**：根据跟踪误差调整控制器参数
3. **控制律**：生成控制信号驱动系统

### 自校正控制 (STR)

1. **参数估计**：在线估计被控对象参数
2. **控制器设计**：根据估计参数设计控制器 (极点配置)
3. **控制应用**：应用控制信号并重复

### 自适应律类型

- **MIT 规则**：基于梯度下降最小化误差平方
- **Lyapunov 方法**：基于 Lyapunov 稳定性理论，保证系统稳定

## 项目结构

```
adaptive-controller/
├── README.md                      # 项目说明
├── requirements.txt               # 依赖列表
├── LEARNING_NOTES.md              # 学习笔记
├── src/                           # 源代码
│   ├── __init__.py
│   ├── adaptive_controller.py     # MRAC + STR 控制器核心
│   ├── reference_model.py         # 参考模型
│   ├── parameter_estimator.py     # 参数估计器
│   ├── plant_model.py            # 被控对象模型
│   ├── simulation.py             # 仿真引擎
│   └── analyzer.py               # 性能分析器
├── tests/                         # 测试代码
│   ├── test_adaptive_controller.py
│   ├── test_parameter_estimator.py
│   └── test_self_tuning.py
├── examples/                      # 示例代码
│   ├── basic_mrac.py             # 基本 MRAC 示例
│   ├── advanced_mrac.py          # 高级示例
│   ├── temperature_control.py    # 温度控制应用
│   └── motor_control.py          # 电机控制应用
└── docs/                          # 文档
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 快速开始

### 安装依赖

```bash
pip install numpy scipy matplotlib pytest
```

### 运行基本示例

```bash
cd projects/adaptive-controller
python examples/basic_mrac.py
```

### 运行实际应用示例

```bash
# 温度控制
python examples/temperature_control.py

# 电机控制
python examples/motor_control.py
```

### 运行测试

```bash
cd projects/adaptive-controller
pytest tests/ -v
```

## 使用示例

### 基本 MRAC 控制器

```python
from src import MRACController, SimulationEngine, PerformanceAnalyzer
from src.reference_model import create_first_order_model
from src.plant_model import create_first_order_plant
from src.simulation import SimulationConfig, ReferenceSignal

# 创建参考模型 (期望的闭环行为)
ref_model = create_first_order_model(time_constant=0.5, steady_state_gain=1.0)

# 创建被控对象 (实际系统)
plant = create_first_order_plant(time_constant=1.0, gain=2.0)

# 创建自适应控制器
controller = MRACController(
    reference_model=ref_model,
    adaptation_law="lyapunov",
    adaptation_gain=0.5,
)

# 配置仿真
config = SimulationConfig(
    duration=10.0,
    dt=0.01,
    reference_type=ReferenceSignal.STEP,
    reference_amplitude=1.0,
)

# 运行仿真
engine = SimulationEngine(controller, plant, config)
result = engine.run()

# 分析性能
analyzer = PerformanceAnalyzer()
print(analyzer.generate_report(result.metrics))
```

### 自校正控制器 (STR)

```python
from src import SelfTuningController
from src.plant_model import create_first_order_plant
import numpy as np

# 创建被控对象
plant = create_first_order_plant(time_constant=1.0, gain=1.0)

# 创建自校正控制器
controller = SelfTuningController(
    n_params=2,
    desired_poles=[0.5],
    estimation_method="forgetting_factor",
    forgetting_factor=0.98,
)

# 运行控制循环
for _ in range(1000):
    y = plant.get_output()
    phi = np.array([1.0, -y])  # 回归向量
    u = controller.compute_control(1.0, y, 0.01, phi)
    plant.update(u, 0.01)
```

### 参数估计

```python
from src.parameter_estimator import ParameterEstimator, EstimationMethod

# 创建参数估计器
estimator = ParameterEstimator(
    n_params=3,
    estimation_method=EstimationMethod.RLS,
    adaptation_gain=0.1,
)

# 在线估计
for i in range(100):
    phi = np.random.randn(3)  # 回归向量
    y = np.dot(phi, true_params) + noise  # 观测值
    params, error = estimator.update(phi, y, dt=0.1)
```

## 核心算法

### MIT 规则

基于梯度下降最小化误差平方：

```
J = 0.5 * e^2
dθ/dt = -γ * ∂J/∂θ = -γ * e * ∂e/∂θ
```

其中：
- θ 为控制器参数
- γ 为自适应增益
- e 为跟踪误差

### Lyapunov 方法

基于 Lyapunov 稳定性理论：

```
V = 0.5 * e^2 + 0.5 * (θ - θ*)^T * Γ^{-1} * (θ - θ*)
dθ/dt = -Γ * e * φ(x)
```

其中：
- V 为 Lyapunov 函数
- Γ 为自适应增益矩阵
- φ(x) 为回归向量

### 自校正控制 (STR)

结合在线参数估计和控制器设计：

```
1. 估计系统参数: θ_hat = estimator.update(φ, y, dt)
2. 设计控制器: K = pole_placement(θ_hat, desired_poles)
3. 计算控制: u = K[0] * r + K[1] * y
```

## 实际应用

### 温度控制

- 一阶惯性环节 (热容量)
- 参数时变 (环境温度变化、材料老化)
- 扰动抑制 (环境温度、负载变化)
- 传感器噪声

### 电机速度控制

- 二阶动态特性 (电气 + 机械)
- 非线性特性 (摩擦、饱和)
- 负载扰动
- 参数变化 (温度影响电阻)

## 性能指标

本项目支持以下性能评估指标：

### 跟踪性能
- MSE (均方误差)
- RMSE (均方根误差)
- MAE (平均绝对误差)
- IAE (绝对误差积分)
- ISE (平方误差积分)
- ITAE (时间加权绝对误差积分)

### 瞬态性能
- 上升时间
- 调节时间
- 超调量
- 峰值时间

### 控制性能
- 控制能量
- 最大控制量
- 控制量方差

## 应用场景

自适应控制器适用于：

1. **参数不确定系统**：系统参数未知或缓慢变化
2. **时变系统**：系统特性随时间变化
3. **非线性系统**：在工作点附近线性化
4. **扰动抑制**：存在未知扰动的系统

## 学习资源

- [自适应控制理论](https://en.wikipedia.org/wiki/Adaptive_control)
- [模型参考自适应控制](https://en.wikipedia.org/wiki/Model_reference_adaptive_control)
- Astrom, K.J. & Wittenmark, B. "Adaptive Control"
- Ioannou, P.A. & Sun, J. "Robust Adaptive Control"

## 许可证

本项目仅用于学习目的。
