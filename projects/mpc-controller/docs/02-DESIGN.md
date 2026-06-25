# 02 - 项目设计

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      MPC 控制系统                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │   被控对象    │ ──▶ │   MPC 控制器 │ ──▶ │   执行器     │ │
│  │  (Plant)     │     │ (Controller) │     │ (Actuator)   │ │
│  └──────────────┘     └──────────────┘     └──────────────┘ │
│         │                    │                    │          │
│         │                    ▼                    │          │
│         │            ┌──────────────┐             │          │
│         │            │   优化求解器 │             │          │
│         │            │ (Optimizer)  │             │          │
│         │            └──────────────┘             │          │
│         │                    │                    │          │
│         ▼                    ▼                    ▼          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   仿真环境                           │    │
│  │                (Simulation)                          │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
mpc-controller/
├── src/
│   ├── __init__.py          # 包初始化
│   ├── plant_model.py       # 被控对象模型
│   ├── mpc_controller.py    # MPC 控制器核心
│   ├── optimizer.py         # 优化求解器
│   └── simulation.py        # 仿真环境
├── tests/
│   ├── test_plant_model.py  # 模型测试
│   ├── test_mpc_controller.py  # 控制器测试
│   └── test_simulation.py   # 仿真测试
├── examples/
│   ├── basic_mpc.py         # 基本示例
│   └── nonlinear_mpc.py     # 非线性示例
└── docs/
    ├── 01-RESEARCH.md       # 市场调研
    ├── 02-DESIGN.md         # 项目设计
    ├── 03-IMPLEMENTATION.md # 实现细节
    ├── 04-TESTING.md        # 测试说明
    └── 05-DEVELOPMENT.md    # 开发指南
```

## 2. 核心类设计

### 2.1 被控对象模型 (PlantModel)

```python
class BasePlantModel(ABC):
    """被控对象基类"""
    - n_states: int          # 状态维度
    - n_inputs: int          # 输入维度
    - n_outputs: int         # 输出维度

    + step(state, u, dt) -> state_next
    + output(state) -> y
    + linearize(state_op, u_op, dt) -> (A, B, C, D)

class LinearPlantModel(BasePlantModel):
    """线性系统模型"""
    - A: ndarray             # 状态转移矩阵
    - B: ndarray             # 输入矩阵
    - C: ndarray             # 输出矩阵
    - D: ndarray             # 前馈矩阵

class NonlinearPlantModel(BasePlantModel):
    """非线性系统模型"""
    - dynamics_fn: callable  # 动力学函数
    - output_fn: callable    # 输出函数
```

### 2.2 MPC 控制器 (MPCController)

```python
class MPCController:
    """MPC 控制器"""
    - plant: BasePlantModel  # 被控对象
    - config: MPCConfig      # 配置参数
    - optimizer: MPCOptimizer # 优化器

    + compute_control(state, reference, u_prev) -> MPCResult
    + reset()
    + set_operating_point(state_op, u_op)
    + get_prediction(state, u_sequence) -> (x_pred, y_pred)
```

### 2.3 优化器 (MPCOptimizer)

```python
class MPCOptimizer:
    """MPC 优化求解器"""
    - n_states: int
    - n_inputs: int
    - Np: int                # 预测时域
    - Nc: int                # 控制时域
    - constraints: MPCConstraints
    - weights: MPCWeights

    + solve(x0, A_list, B_list, C_list, x_ref, u_prev) -> (U_opt, info)
```

### 2.4 仿真环境 (MPCSimulation)

```python
class MPCSimulation:
    """MPC 仿真环境"""
    - plant: BasePlantModel
    - controller: MPCController
    - config: SimulationConfig

    + run(x0, reference_fn) -> SimulationResult
    + run_step_response(x0, step_value) -> SimulationResult
    + run_sinusoidal_response(x0, amplitude, frequency) -> SimulationResult
```

## 3. 数据结构设计

### 3.1 配置类

```python
@dataclass
class MPCConfig:
    prediction_horizon: int    # 预测时域
    control_horizon: int       # 控制时域
    sample_time: float         # 采样时间
    mode: MPCMode              # 工作模式

@dataclass
class MPCConstraints:
    u_min: Optional[ndarray]   # 输入下界
    u_max: Optional[ndarray]   # 输入上界
    x_min: Optional[ndarray]   # 状态下界
    x_max: Optional[ndarray]   # 状态上界
    du_min: Optional[ndarray]  # 输入变化下界
    du_max: Optional[ndarray]  # 输入变化上界

@dataclass
class MPCWeights:
    Q: Optional[ndarray]       # 状态权重
    R: Optional[ndarray]       # 输入权重
    Rd: Optional[ndarray]      # 输入变化率权重
    P: Optional[ndarray]       # 终端权重
```

### 3.2 结果类

```python
@dataclass
class MPCResult:
    u_optimal: ndarray         # 最优控制输入
    u_sequence: ndarray        # 最优控制序列
    x_predicted: ndarray       # 预测状态序列
    y_predicted: ndarray       # 预测输出序列
    cost: float                # 最优代价
    info: Dict                 # 优化信息

@dataclass
class SimulationResult:
    time: ndarray              # 时间序列
    states: ndarray            # 状态序列
    inputs: ndarray            # 输入序列
    outputs: ndarray           # 输出序列
    references: ndarray        # 参考序列
    costs: ndarray             # 代价序列
```

## 4. 算法设计

### 4.1 MPC 核心算法

```
输入: 当前状态 x(k), 参考轨迹 r(k:k+Np)

1. 获取系统模型
   - 线性系统: 直接使用 (A, B, C)
   - 非线性系统: 在工作点处线性化

2. 构建优化问题
   min J = Σ[k=0 to Np-1] ||y(k) - r(k)||²_Q + ||u(k)||²_R + ||Δu(k)||²_Rd
         + ||y(Np) - r(Np)||²_P

   s.t.
   - x(k+1) = A*x(k) + B*u(k)
   - y(k) = C*x(k)
   - u_min ≤ u(k) ≤ u_max
   - du_min ≤ Δu(k) ≤ du_max

3. 求解优化问题
   - 使用 scipy.optimize.minimize

4. 返回第一步控制输入
   u(k) = U_opt[0]
```

### 4.2 滚动优化流程

```
for each time step k:
    1. 测量/估计当前状态 x(k)
    2. 获取参考轨迹 r(k:k+Np)
    3. 线性化模型（如果需要）
    4. 构建优化问题
    5. 求解得到 U_opt
    6. 执行 u(k) = U_opt[0]
    7. 等待下一时刻
```

### 4.3 约束处理方法

1. **边界约束**: 直接设置变量上下界
2. **线性约束**: 使用 LinearConstraint
3. **非线性约束**: 使用 NonlinearConstraint

## 5. 接口设计

### 5.1 被控对象接口

```python
# 创建线性系统
plant = LinearPlantModel(A, B, C, D)

# 创建非线性系统
plant = NonlinearPlantModel(n_states, n_inputs, n_outputs, dynamics_fn)

# 创建预定义系统
plant = DoubleIntegrator(dt=0.1)
plant = PendulumModel(m=1.0, L=1.0, b=0.1, g=9.81)
```

### 5.2 控制器接口

```python
# 创建控制器
controller = MPCController(plant, config, weights, constraints)

# 计算控制
result = controller.compute_control(state, reference)

# 获取最优输入
u_opt = result.u_optimal
```

### 5.3 仿真接口

```python
# 创建仿真环境
sim = MPCSimulation(plant, controller, sim_config)

# 运行阶跃响应
result = sim.run_step_response(x0, step_value)

# 运行自定义参考
result = sim.run(x0, reference_fn)
```

## 6. 扩展性设计

### 6.1 新增被控对象

```python
class MySystem(NonlinearPlantModel):
    def __init__(self):
        def dynamics(x, u):
            # 自定义动力学
            return dx_dt

        super().__init__(n_states, n_inputs, n_outputs, dynamics)
```

### 6.2 新增优化器

```python
class MyOptimizer(MPCOptimizer):
    def solve(self, ...):
        # 自定义优化算法
        pass
```

### 6.3 新增控制器

```python
class MyMPC(MPCController):
    def compute_control(self, ...):
        # 自定义控制逻辑
        pass
```

## 7. 性能考虑

### 7.1 计算复杂度

- 模型线性化: O(n³)
- 矩阵运算: O(Np * n²)
- 优化求解: O(Nc³)

### 7.2 优化策略

1. 使用向量化运算
2. 缓存常数矩阵
3. 选择合适的优化算法
4. 控制时域小于预测时域

### 7.3 实时性保障

1. 限制迭代次数
2. 设置收敛容差
3. 使用热启动
4. 并行计算（可选）

## 8. 错误处理

### 8.1 输入验证

- 状态维度检查
- 参考轨迹维度检查
- 约束范围检查

### 8.2 异常处理

- 优化失败处理
- 数值溢出处理
- 约束冲突处理

### 8.3 日志记录

- 控制输入历史
- 状态历史
- 代价历史
- 优化信息
