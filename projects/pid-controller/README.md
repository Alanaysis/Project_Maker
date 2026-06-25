# PID 控制器 (PID Controller)

从零实现 PID 控制算法，支持参数整定和仿真，深入理解反馈控制的核心原理。

## 学习目标

- **理解 PID 控制原理**：掌握比例、积分、微分三项的作用和相互关系
- **掌握 P、I、D 各项作用**：通过实验观察每项对系统响应的影响
- **学会参数整定方法**：掌握 Ziegler-Nichols、Cohen-Coon 等经典整定方法
- **掌握改进 PID 变体**：积分分离、不完全微分、死区控制等实用技术
- **理解实际应用**：温度控制、电机控制、液位控制等工程场景

## 核心循环

```
设定值 → 误差计算 → PID 计算 → 控制输出 → 系统响应 → 反馈
```

1. **误差计算**：计算设定值与测量值的差
2. **PID 计算**：P 项响应当前误差，I 项消除累积误差，D 项预测误差趋势
3. **控制输出**：三项之和，经限幅后输出到执行器
4. **系统响应**：被控对象根据控制输入产生输出
5. **反馈**：测量输出并返回到误差计算

## 项目结构

```
pid-controller/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── docs/
│   ├── 01-RESEARCH.md          # 调研文档
│   ├── 02-DESIGN.md            # 设计文档
│   ├── 03-IMPLEMENTATION.md    # 实现文档
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发文档
├── src/
│   ├── __init__.py
│   ├── pid_controller.py       # PID 控制器核心 (含改进变体)
│   ├── plant.py                # 被控对象模型 (含延迟系统)
│   ├── tuner.py                # 参数整定方法 (含手动整定)
│   └── simulator.py            # 仿真器
├── tests/
│   ├── __init__.py
│   ├── test_pid_controller.py  # 控制器测试 (含改进变体)
│   ├── test_plant.py           # 被控对象测试 (含延迟系统)
│   ├── test_tuner.py           # 整定方法测试
│   └── test_simulator.py       # 仿真器测试
└── examples/
    ├── basic_usage.py          # 基础用法示例
    ├── visualization.py        # 可视化示例
    ├── temperature_control.py  # 温度控制示例
    ├── motor_control.py        # 电机控制示例
    └── liquid_level_control.py # 液位控制示例
```

## 快速开始

### 基本使用

```python
from src import PIDController, FirstOrderPlant, Simulator

# 创建 PID 控制器
controller = PIDController(
    Kp=2.0,       # 比例增益
    Ki=0.5,       # 积分增益
    Kd=0.3,       # 微分增益
    output_min=-10,  # 最小输出
    output_max=10,   # 最大输出
)

# 创建被控对象 (一阶系统，如加热器)
plant = FirstOrderPlant(K=1.0, tau=2.0)  # 增益=1，时间常数=2秒

# 运行仿真
sim = Simulator(controller, plant)
result = sim.run(setpoint=1.0, duration=15.0)

# 查看结果
print(f"超调量: {result.overshoot:.1f}%")
print(f"调节时间: {result.settling_time:.2f}s")
print(f"上升时间: {result.rise_time:.2f}s")
print(f"稳态误差: {result.steady_state_error:.4f}")
```

### P vs PI vs PID 对比

```python
from src import PIDController, FirstOrderPlant, Simulator
from src.simulator import run_comparison

# 定义不同控制器配置
configs = {
    "P only": {"Kp": 3.0, "Ki": 0.0, "Kd": 0.0},
    "PI": {"Kp": 2.0, "Ki": 0.5, "Kd": 0.0},
    "PID": {"Kp": 2.0, "Ki": 0.5, "Kd": 0.3},
}

# 创建被控对象工厂
def make_plant():
    return FirstOrderPlant(K=1.0, tau=2.0)

# 运行对比
results = run_comparison(configs, make_plant, setpoint=1.0, duration=15.0)

# 打印对比
for name, result in results.items():
    m = result.summary()
    print(f"{name}: overshoot={m['overshoot_pct']:.1f}%, "
          f"settling={m['settling_time_s']:.2f}s")
```

### 自动参数整定

```python
from src import PIDTuner, FirstOrderPlant

# 创建被控对象
plant = FirstOrderPlant(K=1.0, tau=2.0)

# Cohen-Coon 整定
tuner = PIDTuner()
gains = tuner.cohen_coon(plant.update, step_magnitude=1.0)

print(f"整定结果:")
print(f"  Kp = {gains['Kp']:.3f}")
print(f"  Ki = {gains['Ki']:.3f}")
print(f"  Kd = {gains['Kd']:.3f}")
```

### 二阶系统 (振荡系统)

```python
from src import PIDController, SecondOrderPlant, Simulator

# 欠阻尼二阶系统 (如弹簧-质量-阻尼)
plant = SecondOrderPlant(K=1.0, omega_n=2.0, zeta=0.3)

controller = PIDController(Kp=2.0, Ki=0.5, Kd=0.5)
sim = Simulator(controller, plant)
result = sim.run(setpoint=1.0, duration=15.0)
```

### 延迟系统

```python
from src import PIDController, DelaySystem, Simulator

# 带延迟的一阶系统 (如管道流量控制)
plant = DelaySystem(K=1.0, tau=2.0, delay=3.0)

# 延迟系统需要更保守的 PID 参数
controller = PIDController(Kp=1.0, Ki=0.2, Kd=0.5)
sim = Simulator(controller, plant)
result = sim.run(setpoint=1.0, duration=30.0)
```

### 积分分离 PID

```python
from src import PIDController, FirstOrderPlant, Simulator

# 积分分离：大误差时暂停积分，防止积分饱和
controller = PIDController(
    Kp=2.0, Ki=0.5, Kd=0.3,
    integral_separation=True,
    integral_separation_threshold=5.0,  # 误差 > 5 时暂停积分
)

plant = FirstOrderPlant(K=1.0, tau=2.0)
sim = Simulator(controller, plant)
result = sim.run(setpoint=10.0, duration=20.0)  # 大范围设定值变化
```

### 带死区 PID

```python
from src import PIDController, SecondOrderPlant, Simulator

# 死区控制：小误差时不动作，适用于有摩擦的系统
controller = PIDController(
    Kp=2.0, Ki=0.5, Kd=0.3,
    dead_zone=0.1,  # 误差 < 0.1 时不输出控制
)

plant = SecondOrderPlant(K=1.0, omega_n=2.0, zeta=0.5)
sim = Simulator(controller, plant)
result = sim.run(setpoint=1.0, duration=15.0)
```

### 温度控制应用

```python
from src import PIDController, DelaySystem, Simulator

# 温度控制系统：加热器 + 传感器延迟
# 详见 examples/temperature_control.py
plant = DelaySystem(K=1.0, tau=10.0, delay=2.0)
controller = PIDController(
    Kp=1.5, Ki=0.1, Kd=3.0,
    output_min=0.0,      # 加热器只能加热
    output_max=5.0,      # 最大功率
    integral_separation=True,
    integral_separation_threshold=0.5,
)
```

### 电机控制应用

```python
from src import PIDController, SecondOrderPlant, Simulator

# 电机速度控制：带摩擦的二阶系统
# 详见 examples/motor_control.py
controller = PIDController(
    Kp=0.5, Ki=2.0, Kd=0.01,
    output_min=-24.0,    # 电机电压范围
    output_max=24.0,
    dead_zone=0.5,       # 摩擦死区
)
```

### 液位控制应用

```python
from src import PIDController, FirstOrderPlant, Simulator

# 液位控制系统：非线性阀门特性
# 详见 examples/liquid_level_control.py
controller = PIDController(
    Kp=50.0, Ki=2.0, Kd=10.0,
    output_min=0.0,      # 阀门只能打开
    output_max=100.0,    # 最大开度
    integral_min=-50.0,  # 抗饱和限幅
    integral_max=50.0,
)
```

## 核心算法

### 1. PID 控制算法

```python
def update(self, setpoint, measurement):
    error = setpoint - measurement

    # 比例项
    p_term = self.Kp * error

    # 积分项 (梯形法)
    self._integral += (self._prev_error + error) / 2.0 * self.dt
    i_term = self.Ki * self._integral

    # 微分项 (作用于测量值，带滤波)
    raw_derivative = -(measurement - self._prev_measurement) / self.dt
    filtered = alpha * raw_derivative + (1 - alpha) * self._prev_derivative
    d_term = self.Kd * filtered

    # 输出限幅 + 抗饱和
    output = p_term + i_term + d_term
    output = clip(output, self.output_min, self.output_max)

    return output
```

### 2. 一阶系统模型

```python
# τ * dy/dt + y = K * u
# 离散化: y(t+dt) = y(t) + (dt/τ) * (K*u - y)
def update(self, u):
    dy_dt = (self.K * u - self._output) / self.tau
    self._output += dy_dt * self.dt
    return self._output
```

### 3. Ziegler-Nichols 整定

```python
# 1. P-only 控制，逐渐增加 Kp
# 2. 检测持续振荡，记录 Ku 和 Tu
# 3. 应用公式:
#    Kp = 0.6 * Ku
#    Ki = 1.2 * Ku / Tu
#    Kd = 0.075 * Ku * Tu
```

## 关键概念

### 比例、积分、微分的直觉

- **P (比例)**: 看到误差就修正。误差越大，修正越大。
- **I (积分)**: 如果误差持续存在，逐渐增加修正力度。
- **D (微分)**: 预测误差的变化趋势，提前做出反应。

### 积分饱和 (Windup)

当执行器饱和时 (如阀门全开)，积分项继续累积会导致大超调。解决方法:
- 积分限幅
- 反计算抗饱和

### 微分冲击 (Derivative Kick)

设定值突变时，微分项会产生巨大冲击。解决方法:
- 微分只作用于测量值 (不微分设定值)

### 积分分离 (Integral Separation)

当误差较大时，暂停积分累积，防止积分饱和:
- 设定阈值，当 |误差| > 阈值时停止积分
- 适用于大范围设定值变化的场景
- 如温度从 20°C 升到 60°C

### 不完全微分 (Incomplete Derivative)

在微分项上增加额外的低通滤波:
- 进一步减少高频噪声影响
- 适用于传感器噪声较大的系统
- 以微分响应速度为代价换取平滑性

### 带死区 PID (Dead Zone PID)

当误差在死区内时，控制器不动作:
- 适用于有摩擦或间隙的系统
- 如电机、机械传动系统
- 避免在小误差时的频繁动作

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_pid_controller.py -v

# 运行示例
python examples/basic_usage.py
python examples/visualization.py  # 需要 matplotlib
```

## 参考资料

- [PID Controller - Wikipedia](https://en.wikipedia.org/wiki/PID_controller)
- Åström, K. J., & Hägglund, T. (2006). *Advanced PID Control*. ISA.
- Ogata, K. (2010). *Modern Control Engineering*. Prentice Hall.
- [Ziegler-Nichols Tuning](http://www.controlguru.com/)

## License

This project is for educational purposes.

---

[返回控制理论模块](../) | [返回主目录](../../README.md)
