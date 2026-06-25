# 凸优化设计文档

## 1. 系统架构

### 1.1 模块划分

```
convex-optimization/
├── src/
│   ├── functions/        # 凸函数模块
│   ├── optimizers/       # 优化算法模块
│   ├── constrained/      # 约束优化模块
│   └── applications/     # 实际应用模块
```

### 1.2 依赖关系

```
applications
    ↓
constrained ← optimizers
    ↓           ↓
functions ← functions
```

## 2. 核心类设计

### 2.1 凸函数层次

```
ConvexFunction (ABC)
├── QuadraticFunction
├── RosenbrockFunction
├── LogisticLoss
├── HuberLoss
├── L1Norm
└── ElasticNet
```

**ConvexFunction 接口**:
- `__call__(x)`: 计算函数值
- `gradient(x)`: 计算梯度
- `hessian(x)`: 计算海森矩阵（可选）
- `subgradient(x)`: 计算次梯度
- `is_convex_by_definition(x, y)`: 通过定义判断凸性
- `is_convex_by_hessian(x)`: 通过海森矩阵判断凸性
- `is_strongly_convex(x, mu)`: 判断强凸性

### 2.2 优化器层次

```
BaseOptimizer (ABC)
├── GradientDescent
│   ├── Momentum
│   └── Nesterov
├── NewtonMethod
│   ├── DampedNewton
│   └── RegularizedNewton
├── BFGS
├── LBFGS
├── SR1
├── AdaGrad
├── RMSProp
└── Adam
```

**BaseOptimizer 接口**:
- `step(x, func, grad)`: 执行一步优化
- `optimize(func, grad, x0)`: 执行完整优化
- `line_search(x, direction, func, grad)`: 线搜索

### 2.3 约束优化类

```
Lagrangian
├── DualProblem
└── AugmentedLagrangian

KKTChecker

InteriorPointMethod
├── BarrierMethod
└── PrimalDualInteriorPoint
```

### 2.4 应用类

```
LeastSquares
├── RidgeRegression
├── LassoRegression
└── ElasticNetRegression

SVM
├── LinearSVM
└── KernelSVM

PortfolioOptimizer
├── MinVariance
├── MaxSharpe
├── RiskParity
└── EfficientFrontier
```

## 3. 数据结构设计

### 3.1 OptimizationResult

```python
@dataclass
class OptimizationResult:
    x: np.ndarray           # 最优解
    fun: float              # 最优函数值
    nit: int                # 迭代次数
    nfev: int               # 函数评估次数
    success: bool           # 是否收敛
    message: str            # 收敛信息
    trajectory: List[np.ndarray]  # 迭代轨迹
    grad_norms: List[float]       # 梯度范数历史
```

### 3.2 KKTResult

```python
@dataclass
class KKTResult:
    stationarity: bool      # 平稳性条件
    primal_feasibility: bool # 原始可行性
    dual_feasibility: bool  # 对偶可行性
    complementary_slackness: bool  # 互补松弛性
    is_satisfied: bool      # 是否满足所有 KKT 条件
    violation: float        # 违背程度
```

### 3.3 PortfolioResult

```python
@dataclass
class PortfolioResult:
    weights: np.ndarray     # 资产权重
    expected_return: float  # 期望收益
    risk: float             # 风险（标准差）
    sharpe_ratio: float     # 夏普比率
```

## 4. 算法设计

### 4.1 梯度下降

**标准梯度下降**:
```python
def step(self, x, func, grad):
    g = grad(x)
    return x - self.learning_rate * g
```

**动量梯度下降**:
```python
def step(self, x, func, grad):
    g = grad(x)
    self.velocity = self.momentum * self.velocity + g
    return x - self.learning_rate * self.velocity
```

**Nesterov 加速**:
```python
def step(self, x, func, grad):
    g = grad(x)
    self.velocity = self.momentum * self.velocity + g
    g_ahead = grad(x - self.learning_rate * self.velocity)
    return x - self.learning_rate * g_ahead
```

### 4.2 牛顿法

**标准牛顿法**:
```python
def step(self, x, func, grad, hessian):
    g = grad(x)
    H = hessian(x)
    d = solve(H, -g)  # 求解线性系统
    return x + d
```

**阻尼牛顿法**:
```python
def step(self, x, func, grad, hessian):
    g = grad(x)
    H = hessian(x)
    d = solve(H, -g)
    alpha = line_search(x, d, func, grad)
    return x + alpha * d
```

### 4.3 BFGS

**BFGS 更新**:
```python
def step(self, x, func, grad):
    g = grad(x)
    d = -self.H @ g  # 搜索方向
    alpha = line_search(x, d, func, grad)
    s = alpha * d
    x_new = x + s
    g_new = grad(x_new)
    y = g_new - g
    
    # BFGS 更新
    ys = y @ s
    if ys > 0:
        rho = 1.0 / ys
        V = I - rho * outer(s, y)
        W = I - rho * outer(y, s)
        self.H = V @ self.H @ W + rho * outer(s, s)
    
    return x_new
```

### 4.4 内点法

**障碍函数法**:
```python
def solve(self, x0):
    x = x0
    t = self.t0
    
    for i in range(max_iter):
        # 求解障碍问题
        x = solve_barrier_problem(x, t)
        
        # 检查收敛
        gap = n_ineq / t
        if gap < tol:
            break
        
        # 增加 t
        t *= self.mu
    
    return x
```

## 5. 接口设计

### 5.1 统一优化接口

```python
def optimize(
    func: Callable,        # 目标函数
    grad: Callable,        # 梯度函数
    x0: np.ndarray,        # 初始点
    hessian: Optional[Callable] = None,  # 海森矩阵
    method: str = "auto",  # 优化方法
    **kwargs               # 其他参数
) -> OptimizationResult:
    """统一优化接口"""
    pass
```

### 5.2 约束优化接口

```python
def minimize_constrained(
    func: Callable,
    grad: Callable,
    eq_constraints: List[Callable] = None,
    ineq_constraints: List[Callable] = None,
    x0: np.ndarray = None,
    method: str = "interior_point",
    **kwargs
) -> OptimizationResult:
    """约束优化接口"""
    pass
```

## 6. 错误处理

### 6.1 常见错误

1. **非凸函数**: 警告用户可能陷入局部最优
2. **病态问题**: 建议使用正则化或预处理
3. **不收敛**: 建议调整参数或更换算法
4. **数值溢出**: 使用数值稳定的实现

### 6.2 异常处理

```python
class OptimizationError(Exception):
    """优化错误基类"""
    pass

class ConvergenceError(OptimizationError):
    """收敛错误"""
    pass

class NumericalError(OptimizationError):
    """数值错误"""
    pass
```

## 7. 性能优化

### 7.1 向量化计算

使用 NumPy 的向量化操作避免循环：
```python
# 差
for i in range(n):
    result[i] = func(x[i])

# 好
result = func(x)  # 假设 func 支持向量化
```

### 7.2 缓存计算

缓存重复计算的结果：
```python
class CachedFunction:
    def __init__(self, func):
        self.func = func
        self.cache = {}
    
    def __call__(self, x):
        key = tuple(x)
        if key not in self.cache:
            self.cache[key] = self.func(x)
        return self.cache[key]
```

### 7.3 稀疏矩阵

对于大规模稀疏问题，使用稀疏矩阵：
```python
from scipy import sparse

# 创建稀疏矩阵
A = sparse.csr_matrix((data, (row, col)), shape=(m, n))

# 稀疏矩阵运算
x = sparse.linalg.spsolve(A, b)
```

## 8. 测试策略

### 8.1 单元测试

- 测试每个函数的正确性
- 测试边界条件
- 测试数值稳定性

### 8.2 集成测试

- 测试优化器的收敛性
- 测试不同问题类型的兼容性
- 测试大规模问题的性能

### 8.3 回归测试

- 保存已知问题的解
- 验证新版本的解与旧版本一致

## 9. 未来扩展

### 9.1 计划功能

1. **随机优化**: SGD、SVRG、SAGA
2. **分布式优化**: ADMM、联邦学习
3. **GPU 加速**: CuPy、JAX
4. **自动微分**: PyTorch、TensorFlow 集成

### 9.2 性能改进

1. **并行计算**: 多线程梯度计算
2. **GPU 加速**: 大规模矩阵运算
3. **内存优化**: 流式处理大规模数据
