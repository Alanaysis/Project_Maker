# 自适应控制器 - 实现细节

## 1. 核心算法实现

### 1.1 MRAC 控制器实现

#### 控制律计算

```python
def _compute_control_signal(self, r: float, y: float, e: float) -> float:
    """
    计算控制律 u = theta_r * r - theta_x * y + theta_d

    参数：
        r: 参考输入
        y: 被控对象输出
        e: 跟踪误差
    """
    theta_r = self.params.get("theta_r", 0.0)
    theta_x = self.params.get("theta_x", np.array([0.0]))
    theta_d = self.params.get("theta_d", 0.0)

    # 前馈 + 反馈 + 扰动补偿
    u = theta_r * r - np.sum(theta_x * y) + theta_d

    return u
```

#### Lyapunov 自适应律

```python
def _lyapunov_update(self, e: float, r: float, y: float, dt: float):
    """
    Lyapunov 方法自适应律

    基于 Lyapunov 稳定性理论:
    V = 0.5 * e^2 + 0.5 * (θ - θ*)^T * Γ^{-1} * (θ - θ*)
    dθ/dt = -Γ * e * φ(x)
    """
    # 回归向量 φ(x) = [r, -y, 1]^T
    phi = np.array([r, -y, 1.0])

    # Lyapunov 自适应律: dθ/dt = -Γ * e * φ
    grad = self.gamma * e * phi

    # 更新参数
    self.params["theta_r"] -= grad[0] * dt
    if isinstance(self.params["theta_x"], np.ndarray):
        self.params["theta_x"] -= grad[1] * dt
    self.params["theta_d"] -= grad[2] * dt
```

### 1.2 参考模型实现

#### 一阶参考模型

```python
def _update_first_order(self, r: float, dt: float):
    """
    一阶参考模型: ẏ_m = -a_m * y_m + b_m * r

    使用欧拉法更新:
    y_m(t+dt) = y_m(t) + (-a_m * y_m(t) + b_m * r) * dt
    """
    a_m = self.params.a_m
    b_m = self.params.b_m

    self.dy_m = -a_m * self.y_m + b_m * r
    self.y_m += self.dy_m * dt
```

#### 二阶参考模型 (RK4 积分)

```python
def _update_second_order(self, r: float, dt: float):
    """
    二阶参考模型: ÿ_m + 2ζω_n * ẏ_m + ω_n^2 * y_m = ω_n^2 * r

    使用 RK4 方法积分以保证精度和稳定性
    """
    omega_n = self.params.omega_n
    zeta = self.params.zeta

    x1 = self.y_m
    x2 = self.dy_m

    # RK4 积分
    k1_x1 = x2
    k1_x2 = -omega_n**2 * x1 - 2 * zeta * omega_n * x2 + omega_n**2 * r

    k2_x1 = x2 + 0.5 * dt * k1_x2
    k2_x2 = -omega_n**2 * (x1 + 0.5 * dt * k1_x1) - 2 * zeta * omega_n * (x2 + 0.5 * dt * k1_x2) + omega_n**2 * r

    # ... (k3, k4 类似)

    # 更新状态
    self.y_m += (dt / 6.0) * (k1_x1 + 2 * k2_x1 + 2 * k3_x1 + k4_x1)
    self.dy_m += (dt / 6.0) * (k1_x2 + 2 * k2_x2 + 2 * k3_x2 + k4_x2)
```

### 1.3 参数估计器实现

#### 递归最小二乘 (RLS)

```python
def _rls_update(self, phi: np.ndarray, error: float):
    """
    递归最小二乘 (RLS) 更新

    K = P * φ / (λ + φ^T * P * φ)
    θ = θ + K * e
    P = (I - K * φ^T) * P / λ
    """
    # 计算卡尔曼增益
    S = np.dot(phi, np.dot(self.P, phi))
    K = np.dot(self.P, phi) / (1.0 + S)

    # 更新参数估计
    self.theta += K * error

    # 更新协方差矩阵
    I = np.eye(self.n_params)
    self.P = np.dot(I - np.outer(K, phi), self.P)
```

#### 带遗忘因子的 RLS

```python
def _rls_with_forgetting(self, phi: np.ndarray, error: float):
    """
    带遗忘因子的 RLS

    使用指数遗忘因子 λ (0 < λ < 1)
    λ 越小，对旧数据遗忘越快
    """
    # 计算卡尔曼增益
    S = np.dot(phi, np.dot(self.P, phi))
    K = np.dot(self.P, phi) / (self.lambda_ff + S)

    # 更新参数估计
    self.theta += K * error

    # 更新协方差矩阵 (带遗忘因子)
    I = np.eye(self.n_params)
    self.P = (np.dot(I - np.outer(K, phi), self.P)) / self.lambda_ff
```

## 2. 数值方法

### 2.1 积分方法选择

| 方法 | 精度 | 稳定性 | 计算量 | 适用场景 |
|------|------|--------|--------|---------|
| 欧拉法 | O(h) | 条件稳定 | 低 | 简单系统 |
| 改进欧拉 | O(h²) | 条件稳定 | 中 | 一般系统 |
| RK4 | O(h⁴) | 条件稳定 | 高 | 高精度要求 |
| 隐式欧拉 | O(h) | 无条件稳定 | 中 | 刚性系统 |

本项目选择：
- 一阶系统：欧拉法（计算简单）
- 二阶系统：RK4（精度高）

### 2.2 时间步长选择

```python
# 经验法则：时间常数的 1/10 ~ 1/100
dt = min(time_constant / 10, 0.01)

# 对于二阶系统：考虑自然频率
dt = min(1 / (omega_n * 10), 0.01)
```

## 3. 被控对象建模

### 3.1 一阶惯性环节

```python
def _update_first_order(self, u: float, d: float, dt: float):
    """
    一阶系统: ẏ = -a * y + b * u + d

    解析解: y(t) = (b/a) * u + (y(0) - b/a * u) * exp(-a * t)
    """
    a = self.params.a
    b = self.params.b

    self.dy = -a * self.y + b * u + d
    self.y += self.dy * dt
```

### 3.2 二阶振荡系统

```python
def _update_second_order(self, u: float, d: float, dt: float):
    """
    二阶系统: ÿ + 2ζω_n * ẏ + ω_n^2 * y = ω_n^2 * u + d

    状态空间:
    x1 = y
    x2 = ẏ
    ẋ1 = x2
    ẋ2 = -ω_n^2 * x1 - 2ζω_n * x2 + ω_n^2 * u + d
    """
    omega_n = self.params.omega_n
    zeta = self.params.zeta

    x1 = self.y
    x2 = self.dy

    # RK4 积分
    # ...
```

### 3.3 非线性系统

```python
def _update_nonlinear(self, u: float, d: float, dt: float):
    """
    非线性系统: ẏ = -a * y + b * tanh(u) + c * y^2 * sin(t) + d
    """
    a = self.params.a
    b = self.params.b
    c = 0.1  # 非线性系数

    # 添加非线性项
    nonlinear_term = c * self.y**2 * np.sin(self.time)

    self.dy = -a * self.y + b * np.tanh(u) + nonlinear_term + d
    self.y += self.dy * dt
```

## 4. 扰动和噪声建模

### 4.1 正弦扰动

```python
def _compute_disturbance(self) -> float:
    """计算正弦扰动"""
    amp = self.params.disturbance_amplitude
    freq = self.params.disturbance_frequency

    if amp > 0 and freq > 0:
        return amp * np.sin(2 * np.pi * freq * self.time)
    return 0.0
```

### 4.2 测量噪声

```python
# 添加高斯白噪声
noise = np.random.normal(0, self.params.noise_std) if self.params.noise_std > 0 else 0
measured_output = self.y + noise
```

## 5. 性能指标计算

### 5.1 上升时间

```python
def _compute_rise_time(self, times: np.ndarray, response: np.ndarray) -> float:
    """计算上升时间 (10% 到 90%)"""
    try:
        idx_10 = np.where(response >= 0.1)[0][0]
        idx_90 = np.where(response >= 0.9)[0][0]
        return times[idx_90] - times[idx_10]
    except IndexError:
        return float('inf')
```

### 5.2 调节时间

```python
def _compute_settling_time(self, times: np.ndarray, response: np.ndarray) -> float:
    """计算调节时间 (进入±2% 范围)"""
    tolerance = self.tolerance
    steady_value = 1.0

    # 从后往前找，找到最后一次超出容限的时间
    for i in range(len(response) - 1, -1, -1):
        if abs(response[i] - steady_value) > tolerance:
            if i < len(response) - 1:
                return times[i + 1]
            else:
                return times[-1]
    return times[0]
```

### 5.3 超调量

```python
def _compute_overshoot(self, response: np.ndarray) -> float:
    """计算超调量 (%)"""
    steady_value = 1.0
    peak_value = np.max(response)

    if steady_value > 1e-6:
        overshoot = (peak_value - steady_value) / steady_value * 100
        return max(0, overshoot)
    return 0.0
```

## 6. 仿真引擎实现

### 6.1 主循环

```python
def run(self) -> SimulationResult:
    """运行仿真"""
    dt = self.config.dt
    duration = self.config.duration
    n_steps = int(duration / dt)

    # 初始化记录数组
    times = np.zeros(n_steps)
    ref_signal = np.zeros(n_steps)
    # ...

    # 重置控制器和被控对象
    self.controller.reset()
    self.plant.reset()

    # 运行仿真循环
    for i in range(n_steps):
        t = i * dt

        # 生成参考信号
        r = self._generate_reference(t)

        # 获取当前被控对象输出
        y = self.plant.get_output()

        # 计算控制信号
        u = self.controller.compute_control(r, y, dt)

        # 更新被控对象
        y_new = self.plant.update(u, dt)

        # 获取参考模型输出
        y_m = self.controller.reference_model.get_output()

        # 记录数据
        times[i] = t
        ref_signal[i] = r
        # ...

    return SimulationResult(...)
```

### 6.2 参考信号生成

```python
def _generate_reference(self, t: float) -> float:
    """生成参考信号"""
    if self.config.reference_type == ReferenceSignal.STEP:
        return self.config.reference_amplitude if t > 0 else 0.0

    elif self.config.reference_type == ReferenceSignal.SINE:
        return self.config.reference_amplitude * np.sin(
            2 * np.pi * self.config.reference_frequency * t
        )

    elif self.config.reference_type == ReferenceSignal.SQUARE:
        return self.config.reference_amplitude * np.sign(
            np.sin(2 * np.pi * self.config.reference_frequency * t)
        )

    elif self.config.reference_type == ReferenceSignal.RAMP:
        return self.config.ramp_rate * t
```

## 7. 工厂函数

### 7.1 创建一阶参考模型

```python
def create_first_order_model(
    time_constant: float = 1.0,
    steady_state_gain: float = 1.0,
) -> ReferenceModel:
    """
    创建一阶参考模型

    参数：
        time_constant: 时间常数 (越大响应越慢)
        steady_state_gain: 稳态增益
    """
    a_m = 1.0 / time_constant
    b_m = steady_state_gain * a_m
    params = ModelParameters(a_m=a_m, b_m=b_m)
    return ReferenceModel(ModelOrder.FIRST_ORDER, params)
```

### 7.2 创建二阶参考模型

```python
def create_second_order_model(
    natural_frequency: float = 1.0,
    damping_ratio: float = 0.7,
) -> ReferenceModel:
    """
    创建二阶参考模型

    参数：
        natural_frequency: 自然频率 (越大响应越快)
        damping_ratio: 阻尼比 (0.7 左右为临界阻尼)
    """
    params = ModelParameters(omega_n=natural_frequency, zeta=damping_ratio)
    return ReferenceModel(ModelOrder.SECOND_ORDER, params)
```

## 8. 测试实现

### 8.1 单元测试示例

```python
class TestMRACController:
    def test_lyapunov_adaptation(self):
        """测试 Lyapunov 自适应律"""
        controller = MRACController(
            reference_model=create_first_order_model(),
            adaptation_law=AdaptationLaw.LYAPUNOV,
            adaptation_gain=1.0,
        )

        # 运行仿真
        plant = create_first_order_plant(time_constant=1.0, gain=2.0)
        for _ in range(1000):
            y = plant.get_output()
            u = controller.compute_control(1.0, y, 0.01)
            plant.update(u, 0.01)

        # 验证参数有变化
        assert controller.params["theta_r"] != initial_value
```

### 8.2 集成测试示例

```python
def test_full_mrac_system(self):
    """测试完整的 MRAC 系统"""
    # 创建系统
    ref_model = create_first_order_model()
    plant = create_first_order_plant(time_constant=2.0, gain=0.5)
    controller = MRACController(reference_model=ref_model)

    # 运行长时间仿真
    for _ in range(2000):
        y = plant.get_output()
        u = controller.compute_control(1.0, y, 0.01)
        plant.update(u, 0.01)

    # 验证跟踪误差在减小
    errors = [s.tracking_error for s in controller.history]
    early_error = np.mean(np.abs(errors[:100]))
    late_error = np.mean(np.abs(errors[-100:]))

    assert late_error < early_error
```

## 9. 优化技巧

### 9.1 向量化计算

```python
# 避免循环，使用 NumPy 向量化操作
# 差的写法
for i in range(n):
    result[i] = a[i] * b[i]

# 好的写法
result = a * b
```

### 9.2 预分配数组

```python
# 预分配数组，避免动态扩展
times = np.zeros(n_steps)
plant_output = np.zeros(n_steps)
```

### 9.3 减少函数调用

```python
# 将频繁调用的函数内联
# 或使用 @jit 装饰器加速
```

## 10. 自校正控制器 (STR) 实现

### 10.1 STR 控制器类

```python
class SelfTuningController:
    """
    自校正控制器 (Self-Tuning Regulator, STR)

    工作原理：
    1. 使用参数估计器在线估计被控对象参数
    2. 根据估计参数设计控制器 (极点配置)
    3. 应用控制信号
    4. 重复以上步骤
    """

    def __init__(
        self,
        n_params: int = 2,
        desired_poles: Optional[list] = None,
        estimation_method: str = "rls",
        forgetting_factor: float = 0.98,
        adaptation_gain: float = 0.1,
    ):
        self.n_params = n_params
        self.desired_poles = desired_poles or [0.5]
        self.estimator = ParameterEstimator(...)
        self.estimated_params = np.zeros(n_params)
        self.controller_gains = np.zeros(n_params)
```

### 10.2 极点配置设计

```python
def _design_controller(self):
    """
    根据估计参数设计控制器

    对于一阶系统 y = a*y + b*u
    期望闭环极点为 p
    控制律: u = (p - a_hat) / b_hat * r - (a_hat + p) / b_hat * y
    """
    params = self.estimated_params

    if len(params) >= 2:
        a_hat = params[0]
        b_hat = params[1]

        if abs(b_hat) < 1e-6:
            b_hat = 0.1

        p = self.desired_poles[0]

        # 前馈增益
        self.controller_gains[0] = (p - a_hat) / b_hat

        # 反馈增益
        self.controller_gains[1] = -(a_hat + p) / b_hat
```

### 10.3 MIT 规则实现

```python
def _mit_update(self, e, r, y, dt):
    """
    MIT 规则自适应律

    基于梯度下降最小化误差平方:
    J = 0.5 * e^2
    dθ/dt = -γ * ∂J/∂θ = -γ * e * ∂e/∂θ

    灵敏度导数:
    ∂e/∂θ_r ≈ -r, ∂e/∂θ_x ≈ y, ∂e/∂θ_d ≈ -1
    """
    grad_r = e * (-r)
    grad_x = e * y
    grad_d = e * (-1.0)

    self.params["theta_r"] -= self.gamma * grad_r * dt
    self.params["theta_x"] -= self.gamma * grad_x * dt
    self.params["theta_d"] -= self.gamma * grad_d * dt
```

## 11. 常见问题解决

### 10.1 参数发散

**现象**：参数值变得非常大或 NaN

**原因**：
- 自适应增益过大
- 回归向量持续激励不足

**解决**：
```python
# 限制参数范围
self.params["theta_r"] = np.clip(self.params["theta_r"], -10, 10)

# 减小自适应增益
self.gamma = 0.1
```

### 10.2 跟踪误差不收敛

**现象**：误差保持较大值或振荡

**原因**：
- 参考模型选择不当
- 系统不确定性过大

**解决**：
```python
# 调整参考模型参数
ref_model = create_first_order_model(time_constant=1.0)

# 增加自适应增益
controller.gamma = 1.0
```

### 10.3 数值不稳定

**现象**：输出出现异常值或 NaN

**原因**：
- 时间步长过大
- 积分方法不稳定

**解决**：
```python
# 减小时间步长
dt = 0.001

# 使用更稳定的积分方法 (如 RK4 或隐式方法)
```
