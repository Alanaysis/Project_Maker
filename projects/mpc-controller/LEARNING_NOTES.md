# MPC 控制器 - 学习笔记

## 1. MPC 基础概念

### 1.1 什么是 MPC

模型预测控制（Model Predictive Control, MPC）是一种先进的过程控制方法，其核心思想是：

1. **模型预测**: 使用系统的数学模型预测未来行为
2. **滚动优化**: 在每个时刻求解有限时域优化问题
3. **反馈校正**: 基于实际测量更新预测

### 1.2 MPC 与其他控制方法对比

| 特性 | MPC | PID | LQR |
|------|-----|-----|-----|
| 约束处理 | ✅ 显式 | ❌ 难以处理 | ❌ 无 |
| 预测能力 | ✅ 有 | ❌ 无 | ❌ 无 |
| 多变量 | ✅ 原生 | ⚠️ 需解耦 | ✅ 支持 |
| 计算复杂度 | ❌ 高 | ✅ 低 | ✅ 低 |
| 调参难度 | ⚠️ 中等 | ✅ 简单 | ⚠️ 中等 |

### 1.3 MPC 的优势

1. **约束处理**: 可以显式处理输入、状态、输出约束
2. **预测能力**: 利用模型预测未来，提前做出决策
3. **多变量**: 天然支持多输入多输出系统
4. **灵活性**: 可以调整目标函数和约束

### 1.4 MPC 的局限

1. **计算量大**: 每个时刻都需要求解优化问题
2. **模型依赖**: 需要准确的系统模型
3. **参数调整**: 需要调整多个参数（时域、权重等）

## 2. 数学基础

### 2.1 状态空间模型

离散时间线性系统:

```
x(k+1) = A*x(k) + B*u(k)
y(k) = C*x(k) + D*u(k)
```

其中:
- `x(k)`: 状态向量 (n x 1)
- `u(k)`: 输入向量 (m x 1)
- `y(k)`: 输出向量 (p x 1)
- `A`: 状态转移矩阵 (n x n)
- `B`: 输入矩阵 (n x m)
- `C`: 输出矩阵 (p x n)
- `D`: 前馈矩阵 (p x m)

### 2.2 预测模型

从当前状态 `x(k)` 预测未来 N 步:

```
x(k+1|k) = A*x(k) + B*u(k)
x(k+2|k) = A*x(k+1|k) + B*u(k+1)
...
x(k+N|k) = A*x(k+N-1|k) + B*u(k+N-1)
```

紧凑形式:

```
X = A_bar * x(k) + B_bar * U
```

其中:

```
A_bar = [A; A^2; ...; A^N]
B_bar = [B, 0, ..., 0; AB, B, ..., 0; ...; A^(N-1)B, A^(N-2)B, ..., B]
```

### 2.3 目标函数

标准 MPC 目标函数:

```
J = Σ[k=0 to Np-1] (||y(k) - r(k)||²_Q + ||u(k)||²_R + ||Δu(k)||²_Rd)
    + ||x(Np) - r(Np)||²_P
```

展开:

```
J = Σ[k=0 to Np-1] [
    (C*x(k) - r(k))^T * Q * (C*x(k) - r(k))
    + u(k)^T * R * u(k)
    + (u(k) - u(k-1))^T * Rd * (u(k) - u(k-1))
]
    + (C*x(Np) - r(Np))^T * P * (C*x(Np) - r(Np))
```

### 2.4 约束

输入约束:

```
u_min ≤ u(k) ≤ u_max, k = 0, ..., Nc-1
```

状态约束:

```
x_min ≤ x(k) ≤ x_max, k = 1, ..., Np
```

输入变化率约束:

```
Δu_min ≤ u(k) - u(k-1) ≤ Δu_max
```

## 3. 算法实现

### 3.1 滚动优化流程

```python
def mpc_control_loop():
    while True:
        # 1. 测量当前状态
        x_current = measure_state()

        # 2. 获取参考轨迹
        r = get_reference()

        # 3. 线性化模型（如果需要）
        A, B, C = linearize_model(x_current)

        # 4. 构建预测矩阵
        A_bar, B_bar = build_prediction_matrices(A, B)

        # 5. 构建优化问题
        H, f = build_cost_function(A_bar, B_bar, Q, R, r)

        # 6. 求解 QP 问题
        U_opt = solve_qp(H, f, constraints)

        # 7. 执行第一步控制
        u_apply = U_opt[0]
        apply_control(u_apply)

        # 8. 等待下一时刻
        wait_for_next_sample()
```

### 3.2 目标函数构建

```python
def build_cost_function(A_bar, B_bar, Q, R, r, x0):
    # 预测输出
    Y = C @ (A_bar @ x0 + B_bar @ U)

    # 跟踪误差
    E = Y - R

    # 目标函数
    J = E^T @ Q_bar @ E + U^T @ R_bar @ U

    # 转换为 QP 形式: 0.5 * U^T @ H @ U + f^T @ U
    H = 2 * (B_bar^T @ C^T @ Q_bar @ C @ B_bar + R_bar)
    f = 2 * B_bar^T @ C^T @ Q_bar @ (C @ A_bar @ x0 - r)

    return H, f
```

### 3.3 约束处理

```python
def build_constraints(u_min, u_max, du_min, du_max, u_prev, Nc, m):
    # 输入约束
    bounds = [(u_min[i], u_max[i]) for _ in range(Nc) for i in range(m)]

    # 输入变化率约束
    constraints = []
    for i in range(m):
        # u(0) - u_prev >= du_min
        constraints.append({
            'type': 'ineq',
            'fun': lambda U: U[i] - u_prev[i] - du_min[i]
        })
        # u(0) - u_prev <= du_max
        constraints.append({
            'type': 'ineq',
            'fun': lambda U: du_max[i] - (U[i] - u_prev[i])
        })

    return bounds, constraints
```

## 4. 实践经验

### 4.1 参数调整

#### 预测时域 Np

- **太短**: 无法看到长期影响，可能导致不稳定
- **太长**: 计算量大，可能过于保守
- **经验**: 选择系统响应时间的 1/3 到 1/2

#### 控制时域 Nc

- **太短**: 控制能力受限
- **太长**: 计算量大，自由度太多
- **经验**: 通常 Nc = Np/2 或更小

#### 权重矩阵 Q, R

- **Q 大**: 跟踪性能好，但控制输入大
- **R 大**: 控制输入小，但跟踪性能差
- **经验**: 先设 Q=I, R=0.1I，再调整

#### 约束边界

- **太紧**: 优化可能无解
- **太松**: 约束不起作用
- **经验**: 根据实际物理限制设置

### 4.2 常见问题

#### 问题 1: 优化不收敛

**症状**: 优化返回失败

**原因**:
- 约束冲突
- 权重设置不当
- 初始猜测不好

**解决**:
```python
# 1. 检查约束
print(f"u_min: {u_min}, u_max: {u_max}")

# 2. 调整权重
weights = MPCWeights(Q=np.diag([1.0, 0.1]), R=np.array([[0.01]]))

# 3. 使用热启动
u_init = self._u_sequence
```

#### 问题 2: 跟踪误差大

**症状**: 输出不跟踪参考

**原因**:
- 模型不准确
- 权重设置不当
- 预测时域太短

**解决**:
```python
# 1. 增加预测时域
config = MPCConfig(prediction_horizon=20)

# 2. 增加状态权重
weights = MPCWeights(Q=np.diag([100.0, 1.0]))

# 3. 改进模型
# 使用更精确的模型参数
```

#### 问题 3: 数值不稳定

**症状**: 结果震荡或发散

**原因**:
- 矩阵条件数大
- 浮点误差累积

**解决**:
```python
# 1. 添加正则化
H_reg = H + 1e-6 * np.eye(H.shape[0])

# 2. 使用更稳定的求解器
result = minimize(objective, U0, method='L-BFGS-B')

# 3. 检查矩阵条件数
print(f"条件数: {np.linalg.cond(H)}")
```

### 4.3 调试技巧

#### 可视化预测轨迹

```python
# 绘制预测状态
plt.plot(result.x_predicted, label=['位置', '速度'])
plt.plot(result.y_predicted, '--', label='输出预测')
plt.legend()
plt.show()
```

#### 打印中间结果

```python
# 打印优化信息
print(f"优化成功: {result.info['success']}")
print(f"代价值: {result.cost}")
print(f"迭代次数: {result.info['iterations']}")
```

#### 逐步调试

```python
# 逐步执行控制
for k in range(N):
    result = controller.compute_control(x, ref)
    print(f"Step {k}: x={x}, u={result.u_optimal}")
    x = plant.step(x, result.u_optimal, dt)
```

## 5. 进阶主题

### 5.1 非线性 MPC

对于非线性系统:

```
x(k+1) = f(x(k), u(k))
y(k) = g(x(k))
```

处理方法:
1. **在线线性化**: 在每个预测点处线性化
2. **直接优化**: 使用非线性优化求解器
3. **序列线性化**: 迭代线性化

### 5.2 自适应 MPC

在线更新模型参数:

```python
def update_model(x, u, x_next):
    # 使用递推最小二乘法
    # θ(k+1) = θ(k) + L(k) * (y(k) - φ(k)^T * θ(k))
    pass
```

### 5.3 鲁棒 MPC

处理模型不确定性:

```
x(k+1) = (A + ΔA)*x(k) + (B + ΔB)*u(k)
```

方法:
1. **最坏情况优化**: min-max 优化
2. **场景优化**: 多场景平均
3. **管式 MPC**: 不变集约束

### 5.4 分布式 MPC

多智能体协调:

```
每个智能体:
1. 本地 MPC 优化
2. 与邻居交换信息
3. 协调约束处理
```

## 6. 学习资源

### 6.1 推荐书籍

1. **Model Predictive Control: Theory, Computation, and Design**
   - 作者: Rawlings, Mayne, Diehl
   - 特点: 全面、理论严谨

2. **Predictive Control with Constraints**
   - 作者: Maciejowski
   - 特点: 实用、工程导向

3. **Nonlinear Model Predictive Control**
   - 作者: Allgower, Zheng
   - 特点: 非线性 MPC 专题

### 6.2 在线课程

1. **MPC 课程** - ETH Zurich
2. **控制理论** - MIT OCW
3. **优化方法** - Stanford Online

### 6.3 开源项目

1. **do-mpc**: https://www.do-mpc.com/
   - Python MPC 框架
   - 支持线性和非线性 MPC

2. **CasADi**: https://web.casadi.org/
   - 符号计算框架
   - 适合 NMPC

3. **ACADO Toolkit**: https://acado.github.io/
   - C++ MPC 库
   - 自动代码生成

## 7. 项目总结

### 7.1 实现的功能

1. ✅ 线性系统模型
2. ✅ 非线性系统模型
3. ✅ MPC 控制器核心算法
4. ✅ 约束优化求解
5. ✅ 仿真环境
6. ✅ 可视化工具
7. ✅ 示例和测试

### 7.2 学到的知识

1. **MPC 原理**: 理解了滚动优化和反馈校正
2. **优化方法**: 学会了 QP 问题构建和求解
3. **约束处理**: 掌握了边界约束和不等式约束
4. **系统建模**: 了解了状态空间模型和线性化

### 7.3 未来改进

1. **性能优化**: 使用更高效的 QP 求解器
2. **功能扩展**: 支持更多系统模型
3. **鲁棒性**: 添加自适应和鲁棒 MPC
4. **实时性**: 优化代码以支持实时控制

## 8. 常用代码片段

### 8.1 创建 MPC 控制器

```python
from src.plant_model import DoubleIntegrator
from src.mpc_controller import MPCController, MPCConfig
from src.optimizer import MPCConstraints, MPCWeights

# 创建系统
plant = DoubleIntegrator(dt=0.1)

# 配置 MPC
config = MPCConfig(prediction_horizon=10, control_horizon=5)
weights = MPCWeights(Q=np.diag([10.0, 1.0]), R=np.array([[0.1]]))
constraints = MPCConstraints(u_min=np.array([-2.0]), u_max=np.array([2.0]))

# 创建控制器
controller = MPCController(plant, config, weights, constraints)
```

### 8.2 运行仿真

```python
from src.simulation import MPCSimulation

# 创建仿真环境
sim = MPCSimulation(plant, controller)

# 阶跃响应
result = sim.run_step_response(
    x0=np.array([0.0, 0.0]),
    step_value=np.array([1.0, 0.0]),
    step_time=0.5
)
```

### 8.3 可视化结果

```python
from src.simulation import MPCVisualizer

# 绘制仿真结果
MPCVisualizer.plot_simulation_result(
    result,
    state_names=['位置', '速度'],
    input_names=['加速度'],
    output_names=['位置', '速度'],
    title="MPC 仿真结果"
)
```

### 8.4 自定义系统

```python
from src.plant_model import NonlinearPlantModel

# 定义动力学
def dynamics(x, u):
    return np.array([-x[0] + u[0], -x[1]])

# 创建非线性系统
plant = NonlinearPlantModel(
    n_states=2,
    n_inputs=1,
    n_outputs=2,
    dynamics_fn=dynamics
)
```
