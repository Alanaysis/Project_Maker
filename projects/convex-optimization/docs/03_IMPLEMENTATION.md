# 凸优化实现文档

## 1. 凸函数实现

### 1.1 ConvexFunction 基类

**文件**: `src/functions/convex_function.py`

**核心方法**:

```python
class ConvexFunction(ABC):
    @abstractmethod
    def __call__(self, x: np.ndarray) -> float:
        """计算函数值 f(x)"""
        pass

    @abstractmethod
    def gradient(self, x: np.ndarray) -> np.ndarray:
        """计算梯度 ∇f(x)"""
        pass

    def hessian(self, x: np.ndarray) -> Optional[np.ndarray]:
        """计算海森矩阵 ∇²f(x)，默认返回 None"""
        return None

    def subgradient(self, x: np.ndarray) -> np.ndarray:
        """计算次梯度（对于非光滑函数）"""
        return self.gradient(x)
```

**凸性判断**:

```python
def is_convex_by_definition(self, x, y, alpha=0.5, num_samples=100):
    """通过定义判断凸性"""
    for _ in range(num_samples):
        a = np.random.uniform(0, 1)
        z = a * x + (1 - a) * y
        lhs = self(z)
        rhs = a * self(x) + (1 - a) * self(y)
        if lhs > rhs + 1e-8:
            return False
    return True

def is_convex_by_hessian(self, x):
    """通过海森矩阵判断凸性"""
    H = self.hessian(x)
    if H is None:
        raise ValueError("海森矩阵不可用")
    eigenvalues = np.linalg.eigvalsh(H)
    return np.all(eigenvalues >= -1e-8)
```

### 1.2 二次函数

**文件**: `src/functions/test_functions.py`

```python
class QuadraticFunction(ConvexFunction):
    def __init__(self, A, b=None, c=0.0):
        self.A = np.atleast_2d(A)
        n = self.A.shape[0]
        self.b = np.zeros(n) if b is None else np.atleast_1d(b)
        self.c = c

    def __call__(self, x):
        x = np.atleast_1d(x)
        return 0.5 * x @ self.A @ x + self.b @ x + self.c

    def gradient(self, x):
        x = np.atleast_1d(x)
        return self.A @ x + self.b

    def hessian(self, x):
        return self.A.copy()
```

### 1.3 逻辑损失

```python
class LogisticLoss(ConvexFunction):
    def __init__(self, X, y):
        self.X = np.atleast_2d(X)
        self.y = np.atleast_1d(y)
        self.n = len(y)

    def __call__(self, w):
        w = np.atleast_1d(w)
        z = -self.y * (self.X @ w)
        return np.mean(np.logaddexp(0, z))

    def gradient(self, w):
        w = np.atleast_1d(w)
        z = -self.y * (self.X @ w)
        sigma = 1 / (1 + np.exp(-z))
        return -self.X.T @ (self.y * (1 - sigma)) / self.n
```

## 2. 优化算法实现

### 2.1 梯度下降

**文件**: `src/optimizers/gradient_descent.py`

**标准梯度下降**:

```python
class GradientDescent(BaseOptimizer):
    def __init__(self, learning_rate=0.01, momentum=0.0, nesterov=False, ...):
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.nesterov = nesterov
        self.velocity = None

    def step(self, x, func, grad):
        g = grad(x)
        if self.velocity is None:
            self.velocity = np.zeros_like(x)
        self.velocity = self.momentum * self.velocity + g
        
        if self.nesterov:
            g_ahead = grad(x - self.learning_rate * self.velocity)
            return x - self.learning_rate * g_ahead
        else:
            return x - self.learning_rate * self.velocity
```

**Adam 优化器**:

```python
class Adam(BaseOptimizer):
    def __init__(self, learning_rate=0.001, beta1=0.9, beta2=0.999, ...):
        self.learning_rate = learning_rate
        self.beta1 = beta1
        self.beta2 = beta2
        self.m = None  # 一阶矩
        self.v = None  # 二阶矩
        self.t = 0     # 时间步

    def step(self, x, func, grad):
        g = grad(x)
        self.t += 1
        if self.m is None:
            self.m = np.zeros_like(x)
            self.v = np.zeros_like(x)
        
        self.m = self.beta1 * self.m + (1 - self.beta1) * g
        self.v = self.beta2 * self.v + (1 - self.beta2) * g ** 2
        
        m_hat = self.m / (1 - self.beta1 ** self.t)
        v_hat = self.v / (1 - self.beta2 ** self.t)
        
        return x - self.learning_rate * m_hat / (np.sqrt(v_hat) + self.epsilon)
```

### 2.2 牛顿法

**文件**: `src/optimizers/newton_method.py`

```python
class NewtonMethod(BaseOptimizer):
    def __init__(self, damping=0.0, regularization=1e-6, line_search=True, ...):
        self.damping = damping
        self.regularization = regularization
        self.line_search = line_search

    def solve_newton_system(self, H, g):
        """求解牛顿方程 H * d = -g"""
        n = len(g)
        H_reg = H + self.regularization * np.eye(n)
        
        try:
            L = np.linalg.cholesky(H_reg)
            d = np.linalg.solve(L, -g)
            d = np.linalg.solve(L.T, d)
        except np.linalg.LinAlgError:
            d = np.linalg.solve(H_reg, -g)
        
        return d

    def step(self, x, func, grad, hessian=None):
        g = grad(x)
        if hessian is None:
            raise ValueError("牛顿法需要海森矩阵")
        H = hessian(x)
        d = self.solve_newton_system(H, g)
        
        if self.line_search:
            alpha = self.line_search(x, d, func, grad)
        elif self.damping > 0:
            alpha = self.damping
        else:
            alpha = 1.0
        
        return x + alpha * d
```

### 2.3 BFGS

**文件**: `src/optimizers/bfgs.py`

```python
class BFGS(BaseOptimizer):
    def __init__(self, initial_hessian=None, line_search=True, ...):
        self.initial_hessian = initial_hessian
        self.line_search = line_search
        self.H = None

    def step(self, x, func, grad):
        g = grad(x)
        if self.H is None:
            if self.initial_hessian is not None:
                self.H = self.initial_hessian.copy()
            else:
                self.H = np.eye(len(x))
        
        d = -self.H @ g
        if self.line_search:
            alpha = self.line_search(x, d, func, grad)
        else:
            alpha = 1.0
        
        s = alpha * d
        x_new = x + s
        g_new = grad(x_new)
        y = g_new - g
        
        # BFGS 更新
        ys = y @ s
        if ys > 1e-10:
            rho = 1.0 / ys
            I = np.eye(len(x))
            V = I - rho * np.outer(s, y)
            W = I - rho * np.outer(y, s)
            self.H = V @ self.H @ W + rho * np.outer(s, s)
        
        return x_new
```

**L-BFGS 两循环递归**:

```python
class LBFGS(BaseOptimizer):
    def __init__(self, m=10, line_search=True, ...):
        self.m = m
        self.s_list = []  # s_k = x_{k+1} - x_k
        self.y_list = []  # y_k = g_{k+1} - g_k

    def two_loop_recursion(self, g):
        """L-BFGS 两循环递归"""
        q = g.copy()
        alpha_list = []
        
        # 第一个循环
        for s, y in zip(reversed(self.s_list), reversed(self.y_list)):
            rho = 1.0 / (y @ s)
            alpha = rho * (s @ q)
            q -= alpha * y
            alpha_list.append(alpha)
        
        # 初始 Hessian 近似
        if len(self.s_list) > 0:
            s_last = self.s_list[-1]
            y_last = self.y_list[-1]
            gamma = (s_last @ y_last) / (y_last @ y_last)
            r = gamma * q
        else:
            r = q
        
        # 第二个循环
        alpha_list.reverse()
        for (s, y), alpha in zip(zip(self.s_list, self.y_list), alpha_list):
            rho = 1.0 / (y @ s)
            beta = rho * (y @ r)
            r += (alpha - beta) * s
        
        return r
```

## 3. 约束优化实现

### 3.1 拉格朗日函数

**文件**: `src/constrained/lagrangian.py`

```python
class Lagrangian:
    def __init__(self, objective, eq_constraints=None, ineq_constraints=None):
        self.objective = objective
        self.eq_constraints = eq_constraints or []
        self.ineq_constraints = ineq_constraints or []

    def __call__(self, x, lambda_ineq=None, nu_eq=None):
        result = self.objective(x)
        
        if lambda_ineq is not None and self.ineq_constraints:
            for i, g in enumerate(self.ineq_constraints):
                result += lambda_ineq[i] * g(x)
        
        if nu_eq is not None and self.eq_constraints:
            for j, h in enumerate(self.eq_constraints):
                result += nu_eq[j] * h(x)
        
        return result
```

### 3.2 KKT 条件检验

**文件**: `src/constrained/kkt.py`

```python
class KKTChecker:
    def check_stationarity(self, x, lambda_ineq, nu_eq):
        """检查平稳性条件"""
        grad = self.grad_obj(x)
        for i, grad_g in enumerate(self.grad_ineq):
            grad += lambda_ineq[i] * grad_g(x)
        for j, grad_h in enumerate(self.grad_eq):
            grad += nu_eq[j] * grad_h(x)
        violation = np.linalg.norm(grad)
        return violation < self.tol, violation

    def check_primal_feasibility(self, x):
        """检查原始可行性"""
        max_violation = 0.0
        for g in self.ineq_constraints:
            gx = g(x)
            if gx > self.tol:
                max_violation = max(max_violation, gx)
        for h in self.eq_constraints:
            hx = h(x)
            max_violation = max(max_violation, abs(hx))
        return max_violation < self.tol, max_violation

    def check_complementary_slackness(self, x, lambda_ineq):
        """检查互补松弛性"""
        max_violation = 0.0
        for i, g in enumerate(self.ineq_constraints):
            product = lambda_ineq[i] * g(x)
            max_violation = max(max_violation, abs(product))
        return max_violation < self.tol, max_violation
```

### 3.3 内点法

**文件**: `src/constrained/interior_point.py`

```python
class BarrierMethod:
    def __init__(self, objective, grad_obj, ineq_constraints, ...):
        self.objective = objective
        self.grad_obj = grad_obj
        self.ineq_constraints = ineq_constraints
        self.t0 = t0
        self.mu = mu

    def barrier_function(self, x, t):
        """障碍函数"""
        result = self.objective(x)
        for g in self.ineq_constraints:
            gx = g(x)
            if gx >= 0:
                return np.inf
            result -= np.log(-gx) / t
        return result

    def solve(self, x0):
        x = x0.copy()
        t = self.t0
        
        for i in range(self.max_iter):
            x = self.solve_barrier_problem(x, t)
            gap = len(self.ineq_constraints) / t
            
            if gap < self.tol:
                lambda_ineq = np.zeros(len(self.ineq_constraints))
                for j, g in enumerate(self.ineq_constraints):
                    lambda_ineq[j] = 1.0 / (t * (-g(x)))
                return InteriorPointResult(x=x, ...)
            
            t *= self.mu
        
        return InteriorPointResult(x=x, ...)
```

## 4. 应用实现

### 4.1 最小二乘

**文件**: `src/applications/least_squares.py`

```python
class LeastSquares:
    def __init__(self, A, b):
        self.A = np.atleast_2d(A)
        self.b = np.atleast_1d(b)

    def solve_analytical(self):
        """解析解"""
        return np.linalg.lstsq(self.A, self.b, rcond=None)[0]

    def solve_normal_equations(self):
        """正规方程"""
        AtA = self.A.T @ self.A
        Atb = self.A.T @ self.b
        return np.linalg.solve(AtA, Atb)

    def solve_qr(self):
        """QR 分解"""
        Q, R = np.linalg.qr(self.A)
        return np.linalg.solve(R, Q.T @ self.b)
```

### 4.2 SVM

**文件**: `src/applications/svm.py`

```python
class SVM:
    def fit(self, X, y):
        """训练 SVM（SMO 算法）"""
        n_samples = X.shape[0]
        alphas = np.zeros(n_samples)
        b = 0.0
        
        for iteration in range(self.max_iter):
            n_changed = 0
            for i in range(n_samples):
                f_i = np.sum(alphas * y * (X @ X[i])) + b
                E_i = f_i - y[i]
                
                if (y[i] * E_i < -self.tol and alphas[i] < self.C) or \
                   (y[i] * E_i > self.tol and alphas[i] > 0):
                    # 选择 j != i
                    j = np.random.randint(0, n_samples)
                    # 更新 alpha_i, alpha_j
                    # ...
            
            if n_changed == 0:
                break
        
        w = np.sum((alphas * y)[:, np.newaxis] * X, axis=0)
        return SVMResult(w=w, b=b, ...)
```

### 4.3 投资组合优化

**文件**: `src/applications/portfolio.py`

```python
class PortfolioOptimizer:
    def __init__(self, returns, risk_free_rate=0.0):
        self.returns = np.atleast_2d(returns)
        self.mean_returns = np.mean(self.returns, axis=0)
        self.cov_matrix = np.cov(self.returns, rowvar=False)

    def min_variance_portfolio(self):
        """最小方差组合"""
        n = self.n_assets
        Sigma = self.cov_matrix
        ones = np.ones(n)
        
        Sigma_inv = np.linalg.inv(Sigma)
        w = Sigma_inv @ ones / (ones @ Sigma_inv @ ones)
        
        return PortfolioResult(weights=w, ...)

    def max_sharpe_portfolio(self):
        """最大夏普比率组合"""
        n = self.n_assets
        Sigma = self.cov_matrix
        excess_returns = self.mean_returns - self.risk_free_rate
        
        Sigma_inv = np.linalg.inv(Sigma)
        w = Sigma_inv @ excess_returns / (np.ones(n) @ Sigma_inv @ excess_returns)
        
        return PortfolioResult(weights=w, ...)
```

## 5. 数值稳定性

### 5.1 避免数值溢出

```python
# 使用 log-sum-exp 技巧
def log_sum_exp(x):
    c = np.max(x)
    return c + np.log(np.sum(np.exp(x - c)))

# 使用 logaddexp
z = np.logaddexp(0, -y * (X @ w))
```

### 5.2 处理病态矩阵

```python
# 添加正则化
H_reg = H + epsilon * np.eye(n)

# 使用 SVD 分解
U, s, Vt = np.linalg.svd(A)
s_inv = np.where(s > epsilon, 1 / s, 0)
A_inv = Vt.T @ np.diag(s_inv) @ U.T
```

### 5.3 避免除以零

```python
# 检查分母
if abs(denominator) < epsilon:
    denominator = epsilon

# 使用 safe_divide
def safe_divide(a, b, epsilon=1e-10):
    return a / np.where(np.abs(b) < epsilon, epsilon, b)
```

## 6. 性能优化

### 6.1 向量化计算

```python
# 使用 NumPy 广播
result = A @ x + b  # 而不是循环

# 使用 Einstein 求和
result = np.einsum('ij,jk->ik', A, B)
```

### 6.2 缓存计算

```python
# 预计算常用值
AtA = A.T @ A
Atb = A.T @ b

# 缓存梯度
if not hasattr(self, '_cached_grad'):
    self._cached_grad = grad(x)
```

### 6.3 内存优化

```python
# 使用 in-place 操作
x += alpha * d  # 而不是 x = x + alpha * d

# 使用视图而不是复制
x_view = x[indices]  # 而不是 x[indices].copy()
```
