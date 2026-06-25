# System Response Analysis

控制系统响应分析工具包 -- 支持时域、频域、稳定性分析和控制器设计。

## 功能模块

| 模块 | 文件 | 功能 |
|------|------|------|
| 传递函数 | `src/transfer_function.py` | LTI 系统传递函数表示、运算 |
| 时域响应 | `src/time_response.py` | 阶跃/脉冲/斜坡响应 |
| 频域响应 | `src/frequency_response.py` | 波特图、奈奎斯特图、裕度分析 |
| 性能指标 | `src/performance.py` | 上升时间、超调量、调节时间、稳态误差 |
| 稳定性分析 | `src/stability.py` | 劳斯判据、根轨迹 |
| 系统辨识 | `src/system_id.py` | 从实验数据辨识传递函数 |
| 控制器设计 | `src/controller_design.py` | PID 整定、超前/滞后补偿器 |

## 快速开始

```python
from src import TransferFunction, TimeResponse, FrequencyResponse, PerformanceMetrics

# 创建二阶系统: G(s) = 4 / (s^2 + 2s + 4)
tf = TransferFunction.second_order(gain=1, omega_n=2, zeta=0.5)

# 时域响应
tr = TimeResponse(tf)
step_data = tr.step(t_final=5)

# 性能指标
pm = PerformanceMetrics(tf)
metrics = pm.step_metrics()
print(f"上升时间: {metrics.rise_time:.2f}s")
print(f"超调量: {metrics.overshoot_pct:.1f}%")
print(f"调节时间: {metrics.settling_time:.2f}s")

# 频域分析
fr = FrequencyResponse(tf)
bode = fr.bode()
margins = fr.margins()
print(f"增益裕度: {margins.gain_margin_db} dB")
print(f"相位裕度: {margins.phase_margin_deg} deg")
```

## 核心 API

### TransferFunction

```python
# 多种创建方式
tf = TransferFunction([1], [1, 1])              # 直接指定系数
tf = TransferFunction.first_order(gain=5, tau=2) # 一阶系统
tf = TransferFunction.second_order(omega_n=2, zeta=0.5)  # 二阶系统
tf = TransferFunction.from_poles_zeros(poles=[-1,-2], zeros=[-3])  # 零极点

# 运算
tf_series = tf1 * tf2       # 串联
tf_parallel = tf1 + tf2     # 并联
tf_cl = tf.feedback()       # 单位负反馈
```

### TimeResponse

```python
tr = TimeResponse(tf)
step = tr.step()       # 阶跃响应
impulse = tr.impulse()  # 脉冲响应
ramp = tr.ramp()        # 斜坡响应
```

### FrequencyResponse

```python
fr = FrequencyResponse(tf)
bode = fr.bode()         # 波特图数据
nyquist = fr.nyquist()   # 奈奎斯特图数据
margins = fr.margins()   # 增益/相位裕度
bw = fr.bandwidth()      # 带宽
```

### PerformanceMetrics

```python
pm = PerformanceMetrics(tf)
m = pm.step_metrics()     # 全部性能指标
sse = pm.steady_state_error("step")  # 稳态误差
```

### StabilityAnalyzer

```python
sa = StabilityAnalyzer(tf)
routh = sa.routh()           # 劳斯表
rl = sa.root_locus()         # 根轨迹
stable = sa.is_stable(k=1)   # 稳定性判断
```

### ControllerDesigner

```python
cd = ControllerDesigner(plant)
pid = cd.pid_ziegler_nichols()    # Z-N 整定
lead = cd.design_lead(phase_boost_deg=45, omega_cross=1)  # 超前补偿
lag = cd.design_lag(low_freq_boost=10, omega_cross=1)     # 滞后补偿
```

## 项目结构

```
system-response/
├── src/
│   ├── __init__.py
│   ├── transfer_function.py   # 传递函数
│   ├── time_response.py       # 时域响应
│   ├── frequency_response.py  # 频域响应
│   ├── performance.py         # 性能指标
│   ├── stability.py           # 稳定性分析
│   ├── system_id.py           # 系统辨识
│   └── controller_design.py   # 控制器设计
├── tests/
│   ├── test_transfer_function.py
│   ├── test_time_response.py
│   ├── test_frequency_response.py
│   ├── test_performance.py
│   ├── test_stability.py
│   ├── test_system_id.py
│   └── test_controller_design.py
├── examples/
│   ├── basic_analysis.py
│   ├── controller_design.py
│   └── system_identification.py
├── docs/
│   ├── 01_RESEARCH.md
│   ├── 02_REQUIREMENTS.md
│   ├── 03_DESIGN.md
│   ├── 04_PRODUCT.md
│   └── 05_DEVELOPMENT.md
└── requirements.txt
```

## 依赖

- Python >= 3.10
- NumPy >= 1.24
- SciPy >= 1.10
