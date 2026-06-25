# 03 - 实现细节

## 1. 模块实现

### 1.1 plant_model.py - 被控对象模型

#### 设计思路

采用继承体系设计：
- `BasePlantModel`: 抽象基类，定义通用接口
- `LinearPlantModel`: 线性系统实现
- `NonlinearPlantModel`: 非线性系统实现
- 预定义系统: 双积分器、倒立摆、水箱系统

#### 关键实现

```python
class BasePlantModel(ABC):
    def linearize(self, state_op, u_op, dt):
        """
        数值线性化方法

        使用有限差分计算 Jacobian 矩阵:
        A = df/dx ≈ (f(x+ε) - f(x)) / ε
        B = df/du ≈ (f(u+ε) - f(u)) / ε
        """
        eps = 1e-6
        # ... 数值差分计算
```

#### 非线性系统积分

使用四阶 Runge-Kutta 方法:

```python
k1 = f(x, u)
k2 = f(x + 0.5*dt*k1, u)
k3 = f(x + 0.5*dt*k2, u)
k4 = f(x + dt*k3, u)
x_next = x + (dt/6) * (k1 + 2*k2 + 2*k3 + k4)
```

### 1.2 models.py - 预测模型

#### 状态空间模型

离散时间状态空间模型：
```
x(k+1) = A * x(k) + B * u(k)
y(k)   = C * x(k) + D * u(k)
```

关键方法：
- `predict(x, u)`: 单步状态预测
- `predict_sequence(x0, U)`: 预测状态和输出序列
- `compute_prediction_matrices(Np)`: 计算 QP 预测矩阵
- `is_stable()`: 检查稳定性
- `is_controllable()`: 检查可控性
- `is_observable()`: 检查可观性

#### 脉冲响应模型

FIR 模型：
```
y(k) = Σ[i=0 to N-1] h(i) * u(k-i)
```

关键方法：
- `predict(u)`: 单步预测
- `predict_sequence(u_history, U_future)`: 序列预测
- `compute_prediction_matrix(Np)`: 计算预测矩阵
- `from_step_response(step)`: 从阶跃响应创建
- `from_state_space(A, B, C, N)`: 从状态空间计算

#### 传递函数

连续/离散传递函数转换：
- `ContinuousTransferFunction`: 连续传递函数
- `DiscreteTransferFunction`: 离散传递函数
- 支持 ZOH、FOH、Tustin 离散化方法

### 1.3 qp_solver.py - QP 求解器

#### 问题形式化

MPC 优化问题可以写成标准 QP 形式:

```
min  0.5 * U^T * H * U + f^T * U
s.t. A_ineq * U ≤ b_ineq
     A_eq * U = b_eq
     lb ≤ U ≤ ub
```

#### 目标函数构建

```python
J = Σ[k=0 to Np-1] (||y(k) - r(k)||²_Q + ||u(k)||²_R + ||Δu(k)||²_Rd)
    + ||x(Np) - r(Np)||²_P
```

展开后:

```python
# 跟踪误差代价
e = C*x(k) - r(k)
cost += e^T * Q * e

# 输入代价
cost += u^T * R * u

# 输入变化率代价
du = u(k) - u(k-1)
cost += du^T * Rd * du

# 终端代价
e_terminal = C*x(Np) - r(Np)
cost += e_terminal^T * P * e_terminal
```

#### 约束处理

使用 scipy 的约束接口:

```python
# 边界约束 (Box constraints)
bounds = [(u_min[i], u_max[i]) for i in range(n_inputs)]

# 不等式约束
constraints = [
    {'type': 'ineq', 'fun': lambda U: U[k] - u_min},
    {'type': 'ineq', 'fun': lambda U: u_max - U[k]}
]
```

#### 求解方法

使用 SLSQP (Sequential Least Squares Programming):

```python
result = minimize(
    objective,
    U0,
    method='SLSQP',
    bounds=bounds,
    constraints=constraints,
    options={'maxiter': 100, 'ftol': 1e-6}
)
```

### 1.3 mpc_controller.py - MPC 控制器

#### 控制流程

```python
def compute_control(self, state, reference, u_prev):
    # 1. 获取线性化模型
    A_list, B_list, C_list = self._get_linearized_model(state, u_prev)

    # 2. 处理参考轨迹
    ref = self._process_reference(reference)

    # 3. 求解优化问题
    U_opt, info = self.optimizer.solve(x0, A_list, B_list, C_list, ref, u_prev)

    # 4. 预测状态和输出
    x_pred, y_pred = self._predict(state, U_opt, A_list, B_list, C_list)

    # 5. 保存历史
    self._save_history(state, U_opt[0], ref)

    # 6. 返回结果
    return MPCResult(u_optimal=U_opt[0], ...)
```

#### 线性化策略

**线性模式**: 在固定工作点处线性化一次

```python
if isinstance(plant, LinearPlantModel):
    A, B, C, D = plant.A, plant.B, plant.C, plant.D
elif mode == MPCMode.LINEAR:
    A, B, C, D = plant.linearize(state_op, u_op, dt)
```

**非线性模式**: 在线线性化

```python
for k in range(Np):
    # 在预测点处线性化
    A, B, C, D = plant.linearize(x_pred[k], u_sequence[k], dt)
    # 更新预测状态
    x_pred[k+1] = plant.step(x_pred[k], u_sequence[k], dt)
```

### 1.4 feedback_correction.py - 反馈校正

#### 误差反馈校正

利用当前时刻的预测误差修正未来预测：
```python
y_corrected(k+i) = y_predicted(k+i) + correction_gain * e(k)
# 其中 e(k) = y_measured(k) - y_predicted(k)
```

#### 自适应模型校正

使用递推最小二乘法 (RLS) 在线更新模型参数：
```python
# RLS 更新
K = P * phi / (lambda + phi^T * P * phi)
theta += K * (y_measured - phi^T * theta)
P = (1/lambda) * (P - K * phi^T * P)
```

#### 增广状态方法

将扰动作为增广状态进行估计：
```python
# 增广状态: x_aug = [x, d]
# 增广模型:
x(k+1) = A * x(k) + B * u(k) + Bd * d(k)
d(k+1) = d(k)
y(k) = C * x(k) + Cd * d(k)
```

#### 扰动观测器

使用扰动观测器估计外部扰动：
```python
d_hat(k) = L * (x(k) - x_hat(k))
x_hat(k+1) = A * x_hat(k) + B * u(k) + Bd * d_hat(k)
```

### 1.5 applications.py - 实际应用

#### 温度控制

热力学系统模型：
```python
dT/dt = (1/(m*c)) * (Q_in - Q_loss)
Q_in = eta * P * u
Q_loss = h * A * (T - T_env)
```

#### 轨迹跟踪

Dubins 车模型：
```python
dx/dt = v * cos(theta)
dy/dt = v * sin(theta)
dtheta/dt = omega
```

### 1.6 simulation.py - 仿真环境

#### 仿真主循环

```python
def run(self, x0, reference_fn):
    for k in range(N):
        # 1. 获取当前状态
        current_state = states[k]

        # 2. 生成参考信号
        ref = reference_fn(k * dt)

        # 3. MPC 计算控制输入
        result = controller.compute_control(current_state, ref)
        u = result.u_optimal

        # 4. 系统状态更新
        states[k+1] = plant.step(states[k], u, dt)

        # 5. 添加噪声
        states[k+1] += np.random.randn() * noise_std

    return SimulationResult(...)
```

#### 参考信号生成

支持多种参考信号:

```python
# 阶跃信号
def step_reference(t):
    return step_value if t >= step_time else 0.0

# 正弦信号
def sinusoidal_reference(t):
    return amplitude * sin(2π * frequency * t)

# 随机信号
def random_reference(t):
    if t >= next_change:
        return np.random.uniform(min_val, max_val)
    return current_ref
```

## 2. 算法细节

### 2.1 模型预测

状态预测公式:

```
x(k+1|k) = A*x(k|k) + B*u(k|k)
x(k+2|k) = A*x(k+1|k) + B*u(k+1|k)
...
x(k+Np|k) = A*x(k+Np-1|k) + B*u(k+Np-1|k)
```

其中 `x(i|k)` 表示在时刻 k 对时刻 i 的状态预测。

### 2.2 输出预测

```
y(k|k) = C*x(k|k)
y(k+1|k) = C*x(k+1|k)
...
y(k+Np-1|k) = C*x(k+Np-1|k)
```

### 2.3 目标函数梯度

对于 QP 问题，需要计算梯度:

```
∂J/∂U = H * U + f
```

其中:

```
H = Σ[k] (B^T * C^T * Q * C * B + R + Rd)
f = Σ[k] (B^T * C^T * Q * (C * A * x(k) - r(k)))
```

### 2.4 约束矩阵构建

输入约束:

```
U_min ≤ U ≤ U_max
```

输入变化率约束:

```
du_min ≤ u(k) - u(k-1) ≤ du_max
```

状态约束（间接）:

```
通过输入约束间接保证状态约束
```

## 3. 数值计算

### 3.1 数值稳定性

1. **条件数检查**: 检查矩阵条件数
2. **正则化**: 添加小的正则项
3. **浮点精度**: 使用 float64

### 3.2 优化求解

SLSQP 算法流程:

```
1. 初始化
2. 计算目标函数值和梯度
3. 构建 QP 子问题
4. 求解 QP 得到搜索方向
5. 线搜索确定步长
6. 更新变量
7. 检查收敛条件
8. 重复直到收敛
```

### 3.3 热启动

使用上一次的解作为初始猜测:

```python
u_init = self._u_sequence  # 上一次的控制序列
U0 = u_init.flatten()
```

## 4. 性能优化

### 4.1 向量化运算

使用 numpy 向量化:

```python
# 避免循环
cost = np.sum((Y - X_ref)**2 @ Q)

# 使用矩阵运算
cost = (Y - X_ref).T @ Q @ (Y - X_ref)
```

### 4.2 稀疏矩阵

对于大规模问题，使用稀疏矩阵:

```python
from scipy.sparse import csc_matrix

H_sparse = csc_matrix(H)
```

### 4.3 并行计算

可选的并行化:

```python
from multiprocessing import Pool

with Pool() as pool:
    results = pool.map(compute_prediction, range(Np))
```

## 5. 错误处理

### 5.1 输入验证

```python
def _validate_inputs(self, state, reference):
    if state.shape != (self.n_states,):
        raise ValueError(f"状态维度错误: {state.shape} != {(self.n_states,)}")

    if reference.shape[0] != self.n_outputs:
        raise ValueError(f"参考维度错误: {reference.shape[0]} != {self.n_outputs}")
```

### 5.2 优化失败处理

```python
if not result.success:
    # 使用上一次的输入
    u_optimal = self._u_prev

    # 记录警告
    warnings.warn(f"优化失败: {result.message}")
```

### 5.3 数值异常处理

```python
try:
    u_optimal = result.x[0]
except FloatingPointError:
    # 处理数值溢出
    u_optimal = np.clip(self._u_prev, u_min, u_max)
```

## 6. 测试策略

### 6.1 单元测试

- 模型测试: 验证状态更新、线性化
- 优化器测试: 验证约束满足、收敛性
- 控制器测试: 验证控制计算

### 6.2 集成测试

- 端到端仿真测试
- 不同系统配置测试
- 边界条件测试

### 6.3 性能测试

- 计算时间测试
- 内存使用测试
- 数值精度测试

## 7. 代码规范

### 7.1 命名规范

- 类名: PascalCase
- 函数名: snake_case
- 常量: UPPER_SNAKE_CASE
- 私有方法: _前缀

### 7.2 文档规范

- 所有公共方法必须有 docstring
- 包含参数说明和返回值说明
- 包含使用示例

### 7.3 类型注解

```python
def compute_control(
    self,
    state: np.ndarray,
    reference: np.ndarray,
    u_prev: Optional[np.ndarray] = None
) -> MPCResult:
    """计算 MPC 控制输入"""
    pass
```
