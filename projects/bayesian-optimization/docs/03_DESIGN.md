# 贝叶斯优化 - 设计文档

## 1. 系统架构

### 1.1 整体架构

```
+------------------+     +------------------+     +------------------+
|    用户代码       | --> |   贝叶斯优化器    | --> |   目标函数        |
+------------------+     +------------------+     +------------------+
                              |
                              v
                    +------------------+
                    |   采集函数        |
                    +------------------+
                              |
                              v
                    +------------------+
                    |   高斯过程        |
                    +------------------+
                              |
                              v
                    +------------------+
                    |   核函数          |
                    +------------------+
```

### 1.2 模块依赖

```
optimizer.py
    ├── acquisition.py
    │   └── gaussian_process.py
    │       └── kernels.py
    └── kernels.py
```

## 2. 类设计

### 2.1 核函数层次结构

```
Kernel (ABC)
├── RBF
├── Matern
├── WhiteNoise
└── CompositeKernel
```

#### 核函数基类

```python
class Kernel(ABC):
    @abstractmethod
    def __call__(self, X1, X2):
        """计算核矩阵"""
        pass

    @abstractmethod
    def get_params(self):
        """获取参数"""
        pass

    @abstractmethod
    def set_params(self, **params):
        """设置参数"""
        pass
```

### 2.2 高斯过程类

```python
class GaussianProcess:
    # 核心属性
    kernel: Kernel          # 核函数
    noise_variance: float   # 噪声方差
    X_train: ndarray        # 训练输入
    y_train: ndarray        # 训练输出
    L: ndarray              # Cholesky 因子（缓存）
    alpha: ndarray          # K^{-1}y（缓存）

    # 核心方法
    fit(X, y)               # 拟合模型
    predict(X, return_std)  # 预测
    sample(X, n_samples)    # 后验采样
    optimize(X, y)          # 超参数优化
```

### 2.3 采集函数层次结构

```
AcquisitionFunction (ABC)
├── ExpectedImprovement
├── UpperConfidenceBound
├── ProbabilityOfImprovement
└── ThompsonSampling
```

#### 采集函数基类

```python
class AcquisitionFunction(ABC):
    @abstractmethod
    def __call__(self, X, gp, y_best=None):
        """计算采集函数值"""
        pass
```

### 2.4 优化器类

```python
class BayesianOptimizer:
    # 核心属性
    objective_function: Callable  # 目标函数
    bounds: ndarray               # 搜索空间
    acquisition: AcquisitionFunction  # 采集函数
    gp: GaussianProcess           # 高斯过程
    n_initial: int                # 初始点数
    maximize: bool                # 最大化/最小化

    # 历史记录
    X_history: list
    y_history: list
    best_x: ndarray
    best_y: float

    # 核心方法
    optimize(n_iterations, verbose)
    get_convergence_data()
    plot_convergence()
    plot_objective()
```

## 3. 数据流设计

### 3.1 优化循环数据流

```
初始化阶段:
  bounds, n_initial, kernel
        |
        v
  _initial_sampling()
        |
        v
  X_init, y_init
        |
        v
  更新 X_history, y_history
        |
        v
  更新 best_x, best_y

迭代阶段 (每轮):
  X_history, y_history
        |
        v
  gp.fit(X_train, y_train)
        |
        v
  _propose_point()
        |
        v
  优化采集函数
        |
        v
  x_next
        |
        v
  objective_function(x_next)
        |
        v
  y_next
        |
        v
  更新 X_history, y_history, best_x, best_y
```

### 3.2 预测数据流

```
X_test
    |
    v
K_star = kernel(X_train, X_test)
    |
    v
y_mean = K_star^T @ alpha
    |
    v
v = solve(L, K_star)
    |
    v
y_var = K(X_test, X_test) - v^T @ v
    |
    v
y_std = sqrt(y_var)
```

## 4. 关键算法设计

### 4.1 数值稳定的核矩阵计算

```python
def fit(self, X, y):
    # 计算核矩阵
    K = self.kernel(X, X)

    # 添加噪声项
    K += self.noise_variance * np.eye(len(X))

    # Cholesky 分解
    try:
        L = np.linalg.cholesky(K)
    except np.linalg.LinAlgError:
        # 失败时添加小的对角项
        K += 1e-6 * np.eye(len(X))
        L = np.linalg.cholesky(K)

    # 计算 alpha = K^{-1} y
    self.alpha = np.linalg.solve(L.T, np.linalg.solve(L, y))
```

### 4.2 采集函数优化

```python
def _propose_point(self):
    n_restarts = 10
    best_x = None
    best_acquisition = -np.inf

    for _ in range(n_restarts):
        # 随机初始点
        x0 = np.random.uniform(self.bounds[:, 0], self.bounds[:, 1])

        # 优化采集函数
        result = minimize(neg_acquisition, x0,
                         bounds=self.bounds,
                         method='L-BFGS-B')

        if -result.fun > best_acquisition:
            best_acquisition = -result.fun
            best_x = result.x

    return best_x
```

### 4.3 拉丁超立方采样

```python
def _initial_sampling(self):
    n_dims = len(self.bounds)
    X = np.zeros((self.n_initial, n_dims))

    for i in range(n_dims):
        low, high = self.bounds[i]
        points = np.linspace(low, high, self.n_initial)
        np.random.shuffle(points)
        X[:, i] = points

    return X
```

## 5. 错误处理设计

### 5.1 异常类型

| 异常 | 触发条件 | 处理方式 |
|------|---------|---------|
| ValueError | 参数无效 | 抛出异常，附带详细信息 |
| RuntimeError | 未拟合时预测 | 抛出异常，提示先 fit |
| LinAlgError | 矩阵分解失败 | 添加正则化项重试 |

### 5.2 数值问题处理

| 问题 | 处理方式 |
|------|---------|
| 核矩阵非正定 | 添加小的对角项 |
| 方差为负 | 裁剪到 0 |
| 除零错误 | 使用 np.errstate 处理 |
| 优化失败 | 随机采样作为备选 |

## 6. 性能优化设计

### 6.1 缓存策略

- Cholesky 因子 L：拟合后缓存
- alpha 向量：拟合后缓存
- 核矩阵：不缓存（每次重新计算）

### 6.2 计算优化

- 使用 Cholesky 分解代替矩阵求逆
- 使用 BLAS/LAPACK 加速矩阵运算
- 避免不必要的数组复制

### 6.3 内存优化

- 使用 in-place 操作
- 及时释放临时变量
- 使用视图代替复制

## 7. 扩展性设计

### 7.1 新核函数

实现 `Kernel` 接口即可：

```python
class MyKernel(Kernel):
    def __call__(self, X1, X2):
        # 实现核函数计算
        pass

    def get_params(self):
        return {...}

    def set_params(self, **params):
        # 更新参数
        pass
```

### 7.2 新采集函数

实现 `AcquisitionFunction` 接口即可：

```python
class MyAcquisition(AcquisitionFunction):
    def __call__(self, X, gp, y_best=None):
        # 实现采集函数计算
        pass
```

### 7.3 新优化策略

继承 `BayesianOptimizer` 并重写关键方法：

```python
class MyOptimizer(BayesianOptimizer):
    def _propose_point(self):
        # 自定义点提议策略
        pass
```

## 8. 测试设计

### 8.1 测试层次

```
单元测试
├── 核函数测试
├── 高斯过程测试
├── 采集函数测试
└── 优化器测试

集成测试
├── 1D 函数优化
├── 2D 函数优化
└── 不同配置组合

性能测试
├── 核矩阵计算
└── 优化循环
```

### 8.2 测试数据

- 使用固定的随机种子确保可重复性
- 使用已知最优解的测试函数
- 包含边界情况和异常情况

## 9. 依赖管理

### 9.1 核心依赖

```python
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm
from scipy.special import gamma, kv
```

### 9.2 可选依赖

```python
import matplotlib.pyplot as plt  # 可视化
from sklearn.svm import SVC  # 示例代码
```

## 10. 部署设计

### 10.1 包结构

```
bayesian-optimization/
├── src/
│   └── bayesian_optimization/
│       ├── __init__.py
│       ├── kernels.py
│       ├── gaussian_process.py
│       ├── acquisition.py
│       └── optimizer.py
├── tests/
├── examples/
├── docs/
├── setup.py
└── README.md
```

### 10.2 安装方式

```bash
# 开发模式
pip install -e .

# 正式安装
pip install .
```
