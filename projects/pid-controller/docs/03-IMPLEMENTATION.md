# PID 控制器 - 实现文档

## 1. PID 核心算法实现

### 1.1 比例项

```python
error = setpoint - measurement
p_term = Kp * error
```

最简单的项，直接对当前误差做出响应。

### 1.2 积分项

```python
# 梯形积分法
if first_update:
    integral += error * dt
else:
    integral += (prev_error + error) / 2.0 * dt

# 抗饱和限幅
integral = clip(integral, integral_min, integral_max)
i_term = Ki * integral
```

使用梯形法而非矩形法提高精度。抗饱和通过限幅实现。

### 1.3 微分项

```python
# 微分作用于测量值 (避免设定值冲击)
raw_derivative = -(measurement - prev_measurement) / dt

# 低通滤波
filtered = alpha * raw_derivative + (1 - alpha) * prev_derivative
d_term = Kd * filtered
```

关键点:
- 微分测量值而非误差，避免设定值突变时的冲击
- 低通滤波减少噪声影响

### 1.4 反计算抗饱和

```python
output = p_term + i_term + d_term
output_clamped = clip(output, output_min, output_max)

if output != output_clamped and Ki != 0:
    excess = output - output_clamped
    integral -= excess / Ki  # 回退积分
```

当输出饱和时，将多余的积分量回退，防止积分累积。

## 2. 被控对象实现

### 2.1 一阶系统 (Euler 法)

```python
dy_dt = (K * u - y) / tau
y += dy_dt * dt
```

简单但精度有限，适合小时间步长。

### 2.2 二阶系统 (Runge-Kutta 4 阶)

```python
# 状态方程
dx1/dt = x2
dx2/dt = -ωn²*x1 - 2ζωn*x2 + K*ωn²*u

# RK4 积分
k1 = f(x, u)
k2 = f(x + 0.5*dt*k1, u)
k3 = f(x + 0.5*dt*k2, u)
k4 = f(x + dt*k3, u)
x += (dt/6) * (k1 + 2*k2 + 2*k3 + k4)
```

RK4 比 Euler 法精度高得多，适合刚性系统。

## 3. 参数整定实现

### 3.1 Ziegler-Nichols 方法

```python
kp = initial_kp
while kp <= max_kp:
    # P-only 仿真
    # 检测振荡
    if oscillation_detected:
        Ku = kp
        Tu = oscillation_period
        # 应用 Z-N 公式
        return {
            "Kp": 0.6 * Ku,
            "Ki": 1.2 * Ku / Tu,
            "Kd": 0.075 * Ku * Tu
        }
    kp += increment
```

逐步增加 Kp 直到检测到持续振荡。

### 3.2 Cohen-Coon 方法

```python
# 开环阶跃响应
outputs = [plant.update(step) for _ in range(max_steps)]

# 识别一阶参数
K = final_value / step  # 稳态增益
L = time_to_5pct        # 死时间
tau = time_to_63pct     # 时间常数

# Cohen-Coon 公式
Kp = (1/K) * (tau/L + 1/3)
Ki = Kp / (L * (32 + 6*L/tau) / (13 + 8*L/tau))
Kd = Kp * L * 4 / (11 + 2*L/tau)
```

## 4. 性能指标计算

### 4.1 超调量

```python
max_output = max(measurement)
overshoot = (max_output - setpoint) / setpoint * 100
```

### 4.2 上升时间

```python
# 从 10% 到 90% 设定值的时间
t_10 = first_time(measurement >= 0.1 * setpoint)
t_90 = first_time(measurement >= 0.9 * setpoint)
rise_time = t_90 - t_10
```

### 4.3 调节时间

```python
# 最后一次误差超过 2% 设定值的时间
settling_time = last_time(abs(error) > 0.02 * setpoint)
```

## 5. 改进 PID 变体实现

### 5.1 积分分离

```python
if integral_separation and abs(error) > threshold:
    # 误差过大，暂停积分累积
    pass
else:
    # 正常积分
    integral += (prev_error + error) / 2.0 * dt
```

当误差超过阈值时，停止积分累积，防止大范围变化时的积分饱和。

### 5.2 不完全微分

```python
# 基本微分滤波
filtered = alpha * raw_derivative + (1 - alpha) * prev_derivative

# 不完全微分：额外的一阶滤波
if incomplete_derivative:
    d_filtered = beta * filtered + (1 - beta) * prev_incomplete_d
else:
    d_filtered = filtered
```

在基本低通滤波基础上，增加额外的一阶滤波，进一步减少高频噪声。

### 5.3 死区控制

```python
if dead_zone > 0 and abs(error) < dead_zone:
    # 误差在死区内，不输出控制
    return 0.0
```

当误差小于死区宽度时，控制器不动作，适用于有摩擦或间隙的系统。

## 6. 延迟系统实现

### 6.1 延迟缓冲区

```python
# 存储当前输入到缓冲区
buffer[buffer_idx] = control_input

# 获取延迟后的输入
delayed_idx = (buffer_idx + 1) % delay_steps
delayed_input = buffer[delayed_idx]

# 更新缓冲区索引
buffer_idx = delayed_idx
```

使用循环缓冲区实现时间延迟，缓冲区大小由延迟时间和时间步长决定。

### 6.2 延迟系统动力学

```python
# 一阶系统 + 延迟输入
dy_dt = (K * delayed_input - y) / tau
y += dy_dt * dt
```

## 7. 数值稳定性

- 时间步长 dt 不宜过大 (Euler 法稳定性)
- 二阶系统使用 RK4 提高精度
- 微分滤波避免数值噪声
- 积分限幅防止溢出
- 延迟缓冲区使用循环数组
