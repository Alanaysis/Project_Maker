# 状态空间模型 - 实现细节

## 1. 核心算法实现

### 1.1 状态空间模型仿真

**算法:** 离散时间状态空间模型仿真

```
输入: x0 (初始状态), u (输入序列)
输出: states (状态序列), outputs (输出序列)

1. 初始化
   states[0] = x0
   for k = 0 to N-1:
     outputs[k] = C * states[k] + D * u[k]
     states[k+1] = A * states[k] + B * u[k]
```

**实现要点:**
- 使用numpy矩阵运算
- 预分配输出数组
- 支持单步和批量仿真

**代码位置:** `src/state_space_model.py`

### 1.2 卡尔曼滤波

**算法:** 离散卡尔曼滤波

```
预测步骤:
  x̂(k|k-1) = A * x̂(k-1|k-1) + B * u(k)
  P(k|k-1) = A * P(k-1|k-1) * A^T + Q

更新步骤:
  K(k) = P(k|k-1) * C^T * (C * P(k|k-1) * C^T + R)^(-1)
  x̂(k|k) = x̂(k|k-1) + K(k) * (y(k) - C * x̂(k|k-1))
  P(k|k) = (I - K(k) * C) * P(k|k-1)
```

**实现要点:**
- 使用numpy.linalg.inv求逆
- 保存历史记录
- 支持RTS平滑

**数值稳定性:**
- 避免直接求逆，可使用Cholesky分解
- 使用Joseph形式更新协方差

**代码位置:** `src/kalman_filter.py`

### 1.3 可控性/可观性分析

**算法:** 可控性矩阵计算

```
输入: A (n×n), B (n×m)
输出: C (n×n*m)

C = B
AB = B
for i = 1 to n-1:
    AB = A * AB
    C = [C, AB]
```

**实现要点:**
- 使用numpy.hstack/vstack
- 支持容差参数
- 提供格拉姆矩阵计算

**代码位置:** `src/analysis.py`

### 1.4 极点配置

**算法:** Ackermann公式（SISO系统）

```
输入: A (n×n), B (n×1), desired_poles (n,)
输出: K (1×n)

1. 计算期望特征多项式: φ(s) = (s-p1)(s-p2)...(s-pn)
2. 计算 φ(A) = A^n + a_{n-1}*A^{n-1} + ... + a_0*I
3. 计算可控性矩阵: C = [B, AB, ..., A^{n-1}B]
4. K = [0, ..., 0, 1] * C^{-1} * φ(A)
```

**实现要点:**
- 使用numpy.poly计算特征多项式
- 使用numpy.linalg.matrix_power计算矩阵幂
- MIMO系统使用scipy.signal.place_poles

**代码位置:** `src/controller.py`

### 1.5 LQR控制器

**算法:** 离散代数Riccati方程求解

```
输入: A, B, Q, R
输出: K (LQR增益)

1. 求解Riccati方程:
   P = A^T*P*A - A^T*P*B*(R + B^T*P*B)^{-1}*B^T*P*A + Q

2. 计算增益:
   K = (R + B^T*P*B)^{-1} * B^T*P*A
```

**实现要点:**
- 使用scipy.linalg.solve_discrete_are
- 支持交叉权重项N
- 验证闭环稳定性

**代码位置:** `src/controller.py`

### 1.6 状态观测器

**算法:** 全阶Luenberger观测器

```
输入: A, B, C, L (观测器增益)
输出: x̂ (状态估计)

观测器动态:
  x̂(k+1) = (A - L*C) * x̂(k) + B*u(k) + L*y(k)

设计方法 (极点配置):
  1. 利用对偶性: 设计 (A^T, C^T) 的状态反馈
  2. 期望极点: 观测器极点应比控制器快2-5倍
```

**实现要点:**
- 利用对偶性简化设计
- 使用scipy.signal.place_poles
- 支持状态重置

**代码位置:** `src/observer.py`

## 2. 数学公式

### 2.1 离散时间状态空间模型

**状态方程:**
```
x(k+1) = A*x(k) + B*u(k)
```

**输出方程:**
```
y(k) = C*x(k) + D*u(k)
```

**维度:**
- x ∈ ℝ^n (状态向量)
- u ∈ ℝ^m (输入向量)
- y ∈ ℝ^p (输出向量)
- A ∈ ℝ^{n×n} (状态转移矩阵)
- B ∈ ℝ^{n×m} (输入矩阵)
- C ∈ ℝ^{p×n} (输出矩阵)
- D ∈ ℝ^{p×m} (前馈矩阵)

### 2.2 特征值和稳定性

**特征值:**
```
det(A - λI) = 0
```

**稳定性条件:**
- 连续时间: 所有特征值实部 < 0
- 离散时间: 所有特征值模 < 1

### 2.3 可控性矩阵

**定义:**
```
C = [B, AB, A²B, ..., A^{n-1}B]
```

**可控性条件:**
```
rank(C) = n
```

### 2.4 可观性矩阵

**定义:**
```
O = [C; CA; CA²; ...; CA^{n-1}]
```

**可观性条件:**
```
rank(O) = n
```

### 2.5 卡尔曼增益

**公式:**
```
K = P(k|k-1) * C^T * (C * P(k|k-1) * C^T + R)^{-1}
```

**稳态卡尔曼增益:**
通过离散代数Riccati方程求解。

### 2.6 LQR增益

**公式:**
```
K = (R + B^T*P*B)^{-1} * B^T*P*A
```

**Riccati方程:**
```
P = A^T*P*A - A^T*P*B*(R + B^T*P*B)^{-1}*B^T*P*A + Q
```

### 2.7 观测器增益

**设计方法:**
利用对偶性，设计(A^T, C^T)的状态反馈增益。

**期望极点:**
观测器极点应比控制器快2-5倍，确保快速收敛。

## 3. 数值计算

### 3.1 矩阵求逆

**问题:** 直接求逆可能数值不稳定。

**解决方案:**
```python
# 不推荐
K = P @ C.T @ np.linalg.inv(S)

# 推荐 (使用Cholesky分解)
L = np.linalg.cholesky(S)
K = P @ C.T @ np.linalg.solve(L.T, np.linalg.solve(L, np.eye(p)))
```

### 3.2 特征值计算

**问题:** 特征值可能为复数。

**处理方法:**
```python
eigenvalues = np.linalg.eigvals(A)
# 判断稳定性
is_stable = np.all(np.abs(eigenvalues) < 1.0)  # 离散时间
```

### 3.3 矩阵指数

**连续时间到离散时间转换:**
```python
from scipy.linalg import expm

# 矩阵指数
A_d = expm(A * dt)

# 输入矩阵
B_d = np.linalg.solve(A, (A_d - np.eye(n))) @ B
```

### 3.4 Riccati方程求解

**使用scipy:**
```python
from scipy.linalg import solve_discrete_are

P = solve_discrete_are(A, B, Q, R)
```

**迭代求解:**
```python
def solve_dare_iterative(A, B, Q, R, max_iter=100, tol=1e-10):
    P = Q.copy()
    for _ in range(max_iter):
        P_new = A.T @ P @ A - A.T @ P @ B @ np.linalg.inv(R + B.T @ P @ B) @ B.T @ P @ A + Q
        if np.linalg.norm(P_new - P) < tol:
            return P_new
        P = P_new
    return P
```

## 4. 边界条件处理

### 4.1 空输入

```python
def step(self, x, u=None):
    if u is None:
        u = np.zeros(self.m)
    # ...
```

### 4.2 单步输入

```python
def simulate(self, x0, u, n_steps=None):
    u = np.atleast_2d(u)
    if u.shape[0] == 1 and n_steps is not None:
        u = np.tile(u, (n_steps, 1))
    # ...
```

### 4.3 维度验证

```python
def _validate_dimensions(self):
    assert self.A.shape == (self.n_states, self.n_states)
    assert self.B.shape == (self.n_states, self.n_inputs)
    # ...
```

## 5. 性能优化

### 5.1 向量化计算

```python
# 不推荐 (使用循环)
for k in range(n_steps):
    states[k+1] = A @ states[k] + B @ u[k]

# 推荐 (向量化)
# 使用numpy的批量矩阵运算
```

### 5.2 预分配数组

```python
# 预分配
states = np.zeros((n_steps + 1, n))
outputs = np.zeros((n_steps, p))

# 填充
states[0] = x0
for k in range(n_steps):
    # ...
```

### 5.3 缓存中间结果

```python
class KalmanFilter:
    def __init__(self):
        self._S_cache = None  # 缓存新息协方差

    def update(self, y):
        if self._S_cache is None:
            self._S_cache = self.C @ self.P @ self.C.T + self.R
        # ...
```

## 6. 测试策略

### 6.1 单元测试

**测试维度验证:**
```python
def test_dimension_validation():
    with pytest.raises(AssertionError):
        StateSpaceModel(np.eye(2), np.array([[1.0]]), np.array([[1.0, 0.0]]))
```

**测试数值精度:**
```python
def test_numerical_precision():
    x_next, y = model.step(x, u)
    np.testing.assert_array_almost_equal(x_next, expected, decimal=10)
```

### 6.2 集成测试

**测试完整工作流:**
```python
def test_lqr_with_kalman_filter():
    # 创建系统
    # 设计控制器
    # 设计滤波器
    # 仿真
    # 验证结果
```

### 6.3 边界测试

**测试极值情况:**
```python
def test_zero_input():
    states, outputs = model.simulate(x0, np.zeros((10, 1)))
    # 验证零输入响应
```

## 7. 错误处理

### 7.1 输入验证

```python
def validate_input(x, expected_shape):
    if x.shape != expected_shape:
        raise ValueError(f"输入形状错误: {x.shape}, 期望 {expected_shape}")
```

### 7.2 数值错误

```python
try:
    K = np.linalg.inv(S)
except np.linalg.LinAlgError:
    raise ValueError("矩阵奇异，无法求逆")
```

### 7.3 状态错误

```python
if self.K is None:
    raise ValueError("反馈增益K未设置")
```

## 8. 调试技巧

### 8.1 打印中间结果

```python
def predict(self, u=None):
    x_hat_prior = self.A @ self.x_hat + self.B @ u
    P_prior = self.A @ self.P @ self.A.T + self.Q

    print(f"x_hat_prior: {x_hat_prior}")
    print(f"P_prior: {P_prior}")

    return x_hat_prior, P_prior
```

### 8.2 可视化调试

```python
import matplotlib.pyplot as plt

# 绘制状态轨迹
plt.plot(states[:, 0], states[:, 1])
plt.xlabel('x1')
plt.ylabel('x2')
plt.title('State Trajectory')
plt.grid(True)
plt.show()
```

### 8.3 断言检查

```python
# 检查协方差矩阵正定性
assert np.all(np.linalg.eigvals(P) > 0), "协方差矩阵非正定"

# 检查稳定性
assert model.is_stable(), "系统不稳定"
```

## 9. 扩展指南

### 9.1 添加新的滤波器

```python
class ExtendedKalmanFilter(KalmanFilter):
    def __init__(self, f, h, Q, R, x0=None):
        self.f = f  # 非线性状态方程
        self.h = h  # 非线性观测方程
        # ...

    def predict(self, u=None):
        # 使用非线性函数
        x_hat_prior = self.f(self.x_hat, u)
        # 计算雅可比矩阵
        F = self.jacobian_f(self.x_hat, u)
        P_prior = F @ self.P @ F.T + self.Q
        # ...
```

### 9.2 添加新的控制器

```python
class MPCController:
    def __init__(self, A, B, Q, R, N):
        self.N = N  # 预测时域
        # ...

    def compute_control(self, x):
        # 求解优化问题
        # ...
```

## 10. 常见问题

### 10.1 数值不稳定

**问题:** 协方差矩阵失去正定性。

**解决方案:**
- 使用Joseph形式更新协方差
- 使用UD分解
- 使用平方根滤波

### 10.2 收敛慢

**问题:** 观测器或控制器收敛慢。

**解决方案:**
- 调整极点位置
- 增加反馈增益
- 使用LQR自动调整

### 10.3 计算量大

**问题:** 大规模系统计算慢。

**解决方案:**
- 使用稀疏矩阵
- 并行计算
- 降阶模型
