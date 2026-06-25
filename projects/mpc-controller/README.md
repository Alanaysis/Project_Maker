# MPC 控制器 - 模型预测控制算法实现

## 项目概述

本项目实现了模型预测控制（Model Predictive Control, MPC）算法，用于控制线性和非线性系统。

### 一句话描述

实现 MPC 模型预测控制算法，支持约束处理和多种系统模型。

### 学习目标

- 理解 MPC 原理和滚动优化思想
- 掌握约束优化方法
- 学会设计和实现 MPC 控制器
- 了解系统建模和仿真

## 技术栈

- **语言**: Python 3.8+
- **数值计算**: numpy
- **优化求解**: scipy
- **可视化**: matplotlib

## 项目结构

```
mpc-controller/
├── src/                        # 源代码
│   ├── __init__.py            # 包初始化
│   ├── plant_model.py         # 被控对象模型（线性、非线性）
│   ├── models.py              # 预测模型（状态空间、脉冲响应）
│   ├── mpc_controller.py      # MPC 控制器核心
│   ├── optimizer.py           # 优化求解器
│   ├── qp_solver.py           # QP 求解器（Hildreth、活动集）
│   ├── feedback_correction.py # 反馈校正（误差预测、模型校正）
│   ├── applications.py        # 实际应用（温度控制、轨迹跟踪）
│   └── simulation.py          # 仿真环境
├── tests/                      # 测试代码
│   ├── test_plant_model.py    # 模型测试
│   ├── test_models.py         # 预测模型测试
│   ├── test_mpc_controller.py # 控制器测试
│   ├── test_qp_solver.py      # QP 求解器测试
│   ├── test_feedback_correction.py # 反馈校正测试
│   ├── test_applications.py   # 应用测试
│   └── test_simulation.py     # 仿真测试
├── examples/                   # 示例代码
│   ├── basic_mpc.py           # 基本示例
│   ├── nonlinear_mpc.py       # 非线性示例
│   ├── temperature_control.py # 温度控制示例
│   └── trajectory_tracking.py # 轨迹跟踪示例
├── docs/                       # 文档
└── requirements.txt            # 依赖
```

## 核心功能

### 1. 预测模型

- **状态空间模型**: 离散时间状态空间 x(k+1) = Ax(k) + Bu(k)
- **脉冲响应模型**: FIR 模型 y(k) = Σ h(i)*u(k-i)
- **传递函数**: 连续/离散传递函数转换
- **预定义系统**: 双积分器、倒立摆、水箱系统

### 2. 滚动优化

- **目标函数**: 跟踪误差 + 输入代价 + 变化率代价 + 终端代价
- **约束处理**: 输入约束、状态约束、变化率约束
- **QP 求解器**: Hildreth 方法、活动集方法、scipy 求解器
- **预测矩阵**: 自动构建 QP 问题矩阵

### 3. 反馈校正

- **误差反馈校正**: 基于预测误差修正未来预测
- **自适应模型校正**: 递推最小二乘法在线更新参数
- **增广状态方法**: 将扰动作为增广状态进行估计
- **扰动观测器**: 估计并补偿外部扰动

### 4. 实际应用

- **温度控制**: 热力学系统 MPC 控制
- **轨迹跟踪**: 车辆轨迹跟踪控制
- **MPC 控制器**: 标准 MPC、增量式 MPC、自适应 MPC
- **仿真环境**: 阶跃、正弦、随机参考响应

## 快速开始

### 安装依赖

```bash
cd projects/mpc-controller
pip install -r requirements.txt
```

### 基本使用

```python
from src.plant_model import DoubleIntegrator
from src.mpc_controller import MPCController, MPCConfig
from src.optimizer import MPCConstraints, MPCWeights
from src.simulation import MPCSimulation

# 1. 创建被控对象
plant = DoubleIntegrator(dt=0.1)

# 2. 配置 MPC
config = MPCConfig(
    prediction_horizon=10,
    control_horizon=5,
    sample_time=0.1
)

# 3. 设置权重和约束
weights = MPCWeights(Q=np.diag([10.0, 1.0]), R=np.array([[0.1]]))
constraints = MPCConstraints(u_min=np.array([-2.0]), u_max=np.array([2.0]))

# 4. 创建控制器
controller = MPCController(plant, config, weights, constraints)

# 5. 计算控制输入
state = np.array([0.0, 0.0])
reference = np.array([1.0, 0.0])
result = controller.compute_control(state, reference)

print(f"最优控制输入: {result.u_optimal}")
```

### 温度控制示例

```python
from src.applications import TemperatureController, TemperatureControllerConfig

# 创建温度控制器
config = TemperatureControllerConfig(
    T_setpoint=353.15,  # 80°C
    T_initial=293.15    # 20°C
)
controller = TemperatureController(config)

# 计算控制输入
result = controller.compute_control(293.15)
print(f"加热功率: {result.u_optimal[0]:.2f}")

# 运行仿真
sim_result = controller.simulate()
```

### 轨迹跟踪示例

```python
from src.applications import TrajectoryTracker, TrajectoryTrackerConfig

# 创建轨迹跟踪器
config = TrajectoryTrackerConfig(
    trajectory_type="circle",
    radius=5.0,
    speed=1.0
)
tracker = TrajectoryTracker(config)

# 计算控制输入
state = np.array([0.0, 0.0, 0.0])
result = tracker.compute_control(state, t=0.0)
print(f"速度: {result.u_optimal[0]:.2f}, 角速度: {result.u_optimal[1]:.2f}")

# 运行仿真
sim_result = tracker.simulate()
```

### 使用脉冲响应模型

```python
from src.models import ImpulseResponseModel

# 从阶跃响应创建
step_response = np.array([0.0, 0.5, 0.75, 0.875, 0.9375])
model = ImpulseResponseModel.from_step_response(step_response)

# 预测
y = model.predict(np.array([1.0]))
```

### 使用反馈校正

```python
from src.feedback_correction import FeedbackCorrection, CorrectionMethod

# 创建误差反馈校正器
corrector = FeedbackCorrection(
    method=CorrectionMethod.ERROR_FEEDBACK,
    n_states=1, n_inputs=1, n_outputs=1
)

# 执行校正
Y_corrected = corrector.correct(
    y_measured=np.array([1.2]),
    y_predicted=np.array([1.0]),
    Y_predicted=np.array([[0.9], [0.8], [0.7]])
)
```

### 运行示例

```bash
# 基本示例
python examples/basic_mpc.py

# 非线性示例
python examples/nonlinear_mpc.py

# 温度控制示例
python examples/temperature_control.py

# 轨迹跟踪示例
python examples/trajectory_tracking.py
```

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_models.py -v
python -m pytest tests/test_qp_solver.py -v
python -m pytest tests/test_feedback_correction.py -v
python -m pytest tests/test_applications.py -v
```

## 核心概念

### MPC 算法流程

```
当前状态 → 模型预测 → 反馈校正 → 优化求解 → 控制执行 → 状态更新
     ↑                                                    |
     └────────────────────────────────────────────────────┘
                           滚动优化
```

### 目标函数

```
J = Σ[k=0 to Np-1] (||y(k) - r(k)||²_Q + ||u(k)||²_R + ||Δu(k)||²_Rd)
    + ||y(Np) - r(Np)||²_P
```

### 约束

- 输入约束: u_min ≤ u(k) ≤ u_max
- 状态约束: x_min ≤ x(k) ≤ x_max
- 输入变化率约束: du_min ≤ Δu(k) ≤ du_max

## 应用场景

### 1. 运动控制

- 机器人控制
- 机械臂控制
- 无人机控制

### 2. 过程控制

- 化工过程
- 温度控制
- 液位控制

### 3. 汽车控制

- 自动驾驶
- 发动机控制
- 电池管理

## 进阶功能

### 1. 自适应 MPC

在线更新模型参数以适应系统变化。

### 2. 增量式 MPC

使用增量形式消除稳态误差。

### 3. 非线性 MPC

在线线性化处理非线性系统。

## 文档

- [01-RESEARCH.md](docs/01-RESEARCH.md) - 市场调研
- [02-DESIGN.md](docs/02-DESIGN.md) - 项目设计
- [03-IMPLEMENTATION.md](docs/03-IMPLEMENTATION.md) - 实现细节
- [04-TESTING.md](docs/04-TESTING.md) - 测试说明
- [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) - 开发指南
- [LEARNING_NOTES.md](LEARNING_NOTES.md) - 学习笔记

## 性能指标

### 典型性能

| 指标 | 值 |
|------|-----|
| 控制频率 | 10-100 Hz |
| 预测时域 | 10-20 步 |
| 控制时域 | 5-10 步 |
| 计算时间 | < 10 ms |

### 跟踪精度

| 系统 | 稳态误差 |
|------|----------|
| 双积分器 | < 0.01 |
| 倒立摆 | < 0.05 rad |
| 水箱系统 | < 0.02 |

## 扩展方向

1. **鲁棒 MPC**: 处理模型不确定性
2. **随机 MPC**: 处理随机扰动
3. **分布式 MPC**: 多智能体协调
4. **显式 MPC**: 离线计算控制律
5. **深度学习 MPC**: 使用神经网络模型

## 参考资源

### 书籍

- "Model Predictive Control: Theory, Computation, and Design" - Rawlings et al.
- "Predictive Control with Constraints" - Maciejowski

### 开源项目

- do-mpc: https://www.do-mpc.com/
- CasADi: https://web.casadi.org/

## 许可证

本项目仅供学习使用。

## 贡献

欢迎提交 Issue 和 Pull Request。
