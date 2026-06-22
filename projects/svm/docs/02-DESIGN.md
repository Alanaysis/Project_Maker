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
    +----------------+ +-------+ +-----------------+
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

**核心方法**：
- `optimize()`：主优化循环
- `_compute_error()`：计算预测误差
- `_violates_kkt()`：检查 KKT 条件
- `_select_j()`：选择第二个变量
- `_compute_bounds()`：计算边界

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

## 3. 类设计

### 3.1 SVM 类

```python
class SVM:
    """SVM 分类器"""

    # 类型注解
    kernel_type: str
    C: float
    gamma: float
    degree: int
    coef0: float
    tol: float
    max_passes: int

    # 训练后属性
    alpha: Optional[np.ndarray]
    b: Optional[float]
    support_vectors: Optional[np.ndarray]
    support_vector_labels: Optional[np.ndarray]
    support_vector_alphas: Optional[np.ndarray]
    _X_train: Optional[np.ndarray]
    _y_train: Optional[np.ndarray]
```

### 3.2 SMO 类

```python
class SMO:
    """SMO 优化器"""

    C: float
    tol: float
    max_passes: int
```

## 4. 算法设计

### 4.1 SMO 主循环

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

### 4.2 KKT 条件检查

```python
def violates_kkt(yi, Ei, alpha_i):
    # alpha_i < C 时，yi * Ei 应该 >= -tol
    # alpha_i > 0 时，yi * Ei 应该 <= tol
    return ((alpha_i < C and yi * Ei < -tol) or
            (alpha_i > 0 and yi * Ei > tol))
```

### 4.3 边界计算

```python
def compute_bounds(yi, yj, alpha_i, alpha_j):
    if yi != yj:
        L = max(0, alpha_j - alpha_i)
        H = min(C, C + alpha_j - alpha_i)
    else:
        L = max(0, alpha_i + alpha_j - C)
        H = min(C, alpha_i + alpha_j)
    return L, H
```

## 5. 数据设计

### 5.1 输入格式

**训练数据**：
- `X`: numpy 数组，形状 (n_samples, n_features)
- `y`: numpy 数组，形状 (n_samples,)，值为 +1 或 -1

**预测数据**：
- `X`: numpy 数组，形状 (n_samples, n_features)

### 5.2 内部数据

**核矩阵**：
- `K`: numpy 数组，形状 (n_samples, n_samples)

**拉格朗日乘子**：
- `alpha`: numpy 数组，形状 (n_samples,)

### 5.3 输出格式

**预测结果**：
- `predictions`: numpy 数组，形状 (n_samples,)，值为 +1 或 -1

**决策值**：
- `decision_values`: numpy 数组，形状 (n_samples,)

## 6. 错误处理

### 6.1 输入验证

```python
# 检查标签格式
unique_labels = np.unique(y)
if not np.array_equal(unique_labels, [-1, 1]):
    raise ValueError("标签必须为 +1 或 -1")

# 检查 gamma 参数
if gamma <= 0:
    raise ValueError("gamma 必须为正数")

# 检查 degree 参数
if degree <= 0:
    raise ValueError("degree 必须为正整数")
```

### 6.2 训练状态检查

```python
# 预测前检查是否已训练
if self.alpha is None:
    raise RuntimeError("模型尚未训练，请先调用 fit() 方法")
```

## 7. 性能设计

### 7.1 核矩阵预计算

在训练前预计算整个核矩阵，避免在 SMO 迭代中重复计算。

**空间复杂度**：O(n²)
**时间复杂度**：O(n² * d)，其中 d 是特征维度

### 7.2 支持向量筛选

只使用 α > 0 的样本进行预测，减少计算量。

```python
support_mask = self.alpha > 1e-7
self.support_vectors = X[support_mask]
```

### 7.3 数值稳定性

- 使用容差 (tol) 判断收敛
- 对 alpha 进行裁剪
- 使用 1e-7 作为零的阈值

## 8. 测试设计

### 8.1 单元测试

- 核函数测试
- SMO 算法测试
- SVM 分类器测试

### 8.2 集成测试

- 完整流程测试
- 不同核函数测试

### 8.3 测试数据

- 简单线性可分数据
- XOR 问题
- 圆形分布数据
- 随机生成数据
