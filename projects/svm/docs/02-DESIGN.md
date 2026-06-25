# 02 - 设计文档

## 1. 架构设计

### 1.1 整体架构

```
                    +------------------+
                    |    SVM Class     |
                    +------------------+
                           |
            +--------------+--------------+
            |              |              |
    +-------v-------+ +---v---+ +--------v--------+
    | Kernel Module  | |  SMO  | | Prediction      |
    | (kernel.py)    | | Module| | Module          |
    +----------------+ +-------+ +-----------------+
    | - linear_kernel| |       | | - predict()     |
    | - rbf_kernel   | |       | | - decision_func |
    | - poly_kernel  | |       | | - score()       |
    | - sigmoid_kern | |       | |                 |
    +----------------+ +-------+ +-----------------+

    +------------------+    +------------------+
    |   SVR Class      |    | Multiclass Module|
    +------------------+    +------------------+
    | - epsilon-SVR    |    | - OneVsRestSVM   |
    | - SMO for SVR    |    | - OneVsOneSVM    |
    +------------------+    +------------------+

    +------------------+
    | Metrics Module   |
    +------------------+
    | - accuracy       |
    | - precision      |
    | - recall, F1     |
    | - MSE, R2, MAE   |
    +------------------+
```

### 1.2 数据流

```
输入数据 X, y
       │
       v
┌──────────────┐
│ 核矩阵预计算  │  K = kernel_matrix(X, kernel_func)
└──────┬───────┘
       │
       v
┌──────────────┐
│  SMO 优化    │  alpha, b = SMO.optimize(K, y)
└──────┬───────┘
       │
       v
┌──────────────┐
│ 提取支持向量  │  SV = X[alpha > 0]
└──────┬───────┘
       │
       v
┌──────────────┐
│  预测新数据   │  f(x) = Σ(α_i * y_i * K(x_i, x)) + b
└──────────────┘
```

## 2. 模块设计

### 2.1 核函数模块 (kernel.py)

**职责**：提供各种核函数实现

**接口**：
```python
def linear_kernel() -> Callable[[np.ndarray, np.ndarray], float]
def rbf_kernel(gamma: float) -> Callable[[np.ndarray, np.ndarray], float]
def polynomial_kernel(degree: int, coef0: float) -> Callable[[np.ndarray, np.ndarray], float]
def sigmoid_kernel(gamma: float, coef0: float) -> Callable[[np.ndarray, np.ndarray], float]
def precompute_kernel_matrix(X: np.ndarray, kernel_func: Callable) -> np.ndarray
```

**设计决策**：
- 使用闭包返回核函数，便于参数化
- 核函数签名统一：`(x, y) -> float`
- 提供预计算核矩阵的功能，避免重复计算

### 2.2 SMO 模块 (smo.py)

**职责**：实现 SMO 优化算法

**接口**：
```python
class SMO:
    def __init__(self, C: float, tol: float, max_passes: int)
    def optimize(self, K: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, float]
```

### 2.3 SVM 模块 (svm.py)

**职责**：提供完整的 SVM 分类器

**接口**：
```python
class SVM:
    def __init__(self, kernel, C, gamma, degree, coef0, tol, max_passes)
    def fit(self, X, y) -> "SVM"
    def predict(self, X) -> np.ndarray
    def decision_function(self, X) -> np.ndarray
    def score(self, X, y) -> float
    def get_support_vectors(self) -> np.ndarray
    def get_n_support_vectors(self) -> int
```

### 2.4 SVR 模块 (svr.py)

**职责**：提供 epsilon-SVR 回归器

**接口**：
```python
class SVR:
    def __init__(self, kernel, C, epsilon, gamma, degree, coef0, tol, max_passes)
    def fit(self, X, y) -> "SVR"
    def predict(self, X) -> np.ndarray
    def score(self, X, y) -> float  # R2 score
```

### 2.5 多分类模块 (multiclass.py)

**职责**：提供多分类策略

**接口**：
```python
class OneVsRestSVM:
    def __init__(self, kernel, C, gamma, ...)
    def fit(self, X, y) -> "OneVsRestSVM"
    def predict(self, X) -> np.ndarray

class OneVsOneSVM:
    def __init__(self, kernel, C, gamma, ...)
    def fit(self, X, y) -> "OneVsOneSVM"
    def predict(self, X) -> np.ndarray
```

### 2.6 评估指标模块 (metrics.py)

**职责**：提供分类和回归评估指标

**接口**：
```python
def accuracy_score(y_true, y_pred) -> float
def precision_score(y_true, y_pred, average='binary') -> float
def recall_score(y_true, y_pred, average='binary') -> float
def f1_score(y_true, y_pred, average='binary') -> float
def confusion_matrix(y_true, y_pred) -> np.ndarray
def mean_squared_error(y_true, y_pred) -> float
def r2_score(y_true, y_pred) -> float
def mean_absolute_error(y_true, y_pred) -> float
```

## 3. 算法设计

### 3.1 SMO 主循环

```python
def optimize(self, K, y):
    alpha = zeros(n)
    b = 0
    passes = 0

    while passes < max_passes:
        num_changed = 0

        for i in range(n):
            Ei = compute_error(i, K, y, alpha, b)

            if violates_kkt(y[i], Ei, alpha[i]):
                j = select_j(i, n)
                Ej = compute_error(j, K, y, alpha, b)

                # 更新 alpha[j]
                eta = K[i,i] + K[j,j] - 2*K[i,j]
                alpha[j] += y[j] * (Ei - Ej) / eta
                alpha[j] = clip(alpha[j], L, H)

                # 更新 alpha[i]
                alpha[i] += y[i] * y[j] * (old_j - alpha[j])

                # 更新 b
                update_b(...)

                num_changed += 1

        if num_changed == 0:
            passes += 1
        else:
            passes = 0

    return alpha, b
```

### 3.2 KKT 条件检查

```python
def violates_kkt(yi, Ei, alpha_i):
    return ((alpha_i < C and yi * Ei < -tol) or
            (alpha_i > 0 and yi * Ei > tol))
```

## 4. 性能设计

### 4.1 核矩阵预计算

在训练前预计算整个核矩阵，避免在 SMO 迭代中重复计算。

**空间复杂度**：O(n²)
**时间复杂度**：O(n² * d)，其中 d 是特征维度

### 4.2 支持向量筛选

只使用 α > 0 的样本进行预测，减少计算量。

```python
support_mask = self.alpha > 1e-7
self.support_vectors = X[support_mask]
```

### 4.3 数值稳定性

- 使用容差 (tol) 判断收敛
- 对 alpha 进行裁剪
- 使用 1e-7 作为零的阈值

## 5. 测试设计

### 5.1 单元测试 (76 个测试)

- 核函数测试 (24 个)
- SMO 算法测试 (3 个)
- SVM 分类器测试 (13 个)
- SVR 回归器测试 (7 个)
- 多分类测试 (8 个)
- 评估指标测试 (17 个)
- 集成测试 (4 个)
