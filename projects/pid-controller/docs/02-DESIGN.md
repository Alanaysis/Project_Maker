# PID 控制器 - 设计文档

## 1. 系统架构

```
pid-controller/
├── src/
│   ├── __init__.py          # 包入口，导出公共 API
│   ├── pid_controller.py    # PID 控制器核心
│   ├── plant.py             # 被控对象模型
│   ├── tuner.py             # 参数整定方法
│   └── simulator.py         # 仿真器
├── tests/
│   ├── test_pid_controller.py  # 控制器测试
│   ├── test_plant.py           # 被控对象测试
│   ├── test_tuner.py           # 整定方法测试
│   └── test_simulator.py       # 仿真器测试
├── examples/
│   ├── basic_usage.py       # 基础用法示例
│   └── visualization.py     # 可视化示例
└── docs/
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 2. 核心类设计

### 2.1 PIDController

职责: 实现 PID 控制算法及改进变体

```
PIDController
├── 属性
│   ├── Kp, Ki, Kd          # PID 增益
│   ├── output_min/max      # 输出限幅
│   ├── integral_min/max    # 积分限幅 (抗饱和)
│   ├── derivative_filter_coeff  # 微分滤波系数
│   ├── dt                  # 时间步长
│   ├── integral_separation       # 积分分离开关
│   ├── integral_separation_threshold  # 积分分离阈值
│   ├── incomplete_derivative     # 不完全微分开关
│   ├── incomplete_derivative_coeff  # 不完全微分系数
│   └── dead_zone           # 死区宽度
├── 方法
│   ├── update(setpoint, measurement, t) -> output
│   ├── reset()
│   ├── gains (property)
│   ├── history (property)
│   └── get/set_tuning_params()
└── 内部状态
    ├── _integral           # 积分累积器
    ├── _prev_error         # 上一步误差
    ├── _prev_derivative    # 上一步微分值 (滤波后)
    ├── _prev_measurement   # 上一步测量值
    └── _prev_incomplete_d  # 上一步不完全微分值
```

### 2.2 Plant (被控对象)

职责: 模拟物理系统的动态响应

```
FirstOrderPlant
├── 属性: K (增益), tau (时间常数), dt
├── 方法: update(input) -> output, reset()
└── 模型: τ * dy/dt + y = K * u

SecondOrderPlant
├── 属性: K, omega_n (自然频率), zeta (阻尼比), dt
├── 方法: update(input) -> output, reset(), velocity (property)
└── 模型: d²y/dt² + 2ζωn*dy/dt + ωn²*y = K*ωn²*u

DelaySystem
├── 属性: K, tau (时间常数), delay (死时间), dt
├── 方法: update(input) -> output, reset()
└── 模型: G(s) = K * e^(-Ls) / (τs + 1)
```

### 2.3 PIDTuner

职责: 自动整定 PID 参数

```
PIDTuner
├── ziegler_nichols(plant_fn, ...) -> gains
├── cohen_coon(plant_fn, ...) -> gains
├── tyreus_luyben(plant_fn, ...) -> gains
└── get_tuning_guide() -> str
```

### 2.4 Simulator

职责: 运行闭环仿真

```
Simulator
├── 属性: controller, plant, dt
├── 方法: run(setpoint, duration, setpoint_fn) -> SimulationResult
└── 闭环控制循环:
    测量 → PID 计算 → 执行器 → 被控对象 → 反馈

SimulationResult
├── 时间序列: time, setpoint, measurement, error, control
├── PID 项: p_term, i_term, d_term
└── 性能指标: overshoot, settling_time, rise_time, steady_state_error
```

## 3. 数据流

```
设定值 ──┐
         ├──→ 误差计算 ──→ PID 控制器 ──→ 控制输出 ──→ 被控对象 ──→ 测量值
测量值 ──┘                                                        │
         └────────────────────────────────────────────────────────┘
```

## 4. 关键设计决策

### 4.1 离散化方法

- **积分**: 梯形法 (比矩形法更精确)
- **微分**: 后向差分 + 低通滤波
- **二阶系统**: 四阶 Runge-Kutta (比 Euler 法更精确)

### 4.2 抗饱和策略

采用反计算 (Back-calculation) 方法:
1. 检测输出是否饱和
2. 如果饱和，回退积分累积器
3. 防止积分项在饱和方向继续增长

### 4.3 微分处理

- 微分作用于测量值 (而非误差)，避免设定值突变时的冲击
- 低通滤波器减少高频噪声影响
- 滤波系数可调 (0-1)

### 4.4 仿真接口

- 支持常数设定值和时变设定值函数
- 自动计算性能指标
- 记录完整历史用于分析

## 5. 接口设计

### 5.1 基本使用

```python
# 1. 创建组件
controller = PIDController(Kp=2.0, Ki=0.5, Kd=0.3)
plant = FirstOrderPlant(K=1.0, tau=2.0)

# 2. 仿真
sim = Simulator(controller, plant)
result = sim.run(setpoint=1.0, duration=10.0)

# 3. 分析
print(result.summary())
```

### 5.2 参数整定

```python
# 自动整定
tuner = PIDTuner()
gains = tuner.cohen_coon(plant.update, step_magnitude=1.0)

# 应用整定结果
controller.set_tuning_params(gains)
```

### 5.3 多配置对比

```python
configs = {
    "Conservative": {"Kp": 1.0, "Ki": 0.1, "Kd": 0.05},
    "Aggressive": {"Kp": 5.0, "Ki": 2.0, "Kd": 1.0},
}
results = run_comparison(configs, make_plant, setpoint=1.0, duration=10.0)
```
