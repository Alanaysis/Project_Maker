# 03 - 实现文档

## 1. 实现概述

本文档记录 SVM 支持向量机的实现细节，包括关键代码片段、设计决策和实现难点。

## 2. 核函数实现

### 2.1 线性核

```python
def linear_kernel() -> Callable[[np.ndarray, np.ndarray], float]:
    """
    线性核函数: K(x, y) = x · y
    """
    def kernel(x: np.ndarray, y: np.ndarray) -> float:
        return np.dot(x, y)
    return kernel
```

**实现要点**：
- 使用闭包返回核函数
- 使用 `np.dot` 计算点积
- 返回浮点数

### 2.2 RBF 核

```python
def rbf_kernel(gamma: float = 1.0) -> Callable[[np.ndarray, np.ndarray], float]:
    """
    RBF 核函数: K(x, y) = exp(-gamma * ||x - y||^2)
    """
    if gamma <= 0:
        raise ValueError("gamma 必须为正数")

    def kernel(x: np.ndarray, y: np.ndarray) -> float:
        diff = x - y
        return np.exp(-gamma * np.dot(diff, diff))
    return kernel
```

**实现要点**：
- 验证 gamma 参数
- 使用 `np.dot(diff, diff)` 计算 ||x-y||²
- 使用 `np.exp` 计算指数

### 2.3 多项式核

```python
def polynomial_kernel(
    degree: int = 3,
    coef0: float = 1.0
) -> Callable[[np.ndarray, np.ndarray], float]:
    """
    多项式核函数: K(x, y) = (x · y + coef0)^degree
    """
    if degree <= 0:
        raise ValueError("degree 必须为正整数")

    def kernel(x: np.ndarray, y: np.ndarray) -> float:
        return (np.dot(x, y) + coef0) ** degree
    return kernel
```

**实现要点**：
- 验证 degree 参数
- 先计算点积，再加 coef0，最后求幂

### 2.4 核矩阵预计算

```python
def precompute_kernel_matrix(
    X: np.ndarray,
    kernel_func: Callable[[np.ndarray, np.ndarray], float]
) -> np.ndarray:
    """
    预计算核矩阵 (Gram 矩阵)
    """
    n_samples = X.shape[0]
    K = np.zeros((n_samples, n_samples))

    for i in range(n_samples):
        for j in range(i, n_samples):
            K[i, j] = kernel_func(X[i], X[j])
            K[j, i] = K[i, j]  # 对称性

    return K
```

**实现要点**：
- 利用对称性，只计算上三角
- 时间复杂度 O(n²)

## 3. SMO 算法实现

### 3.1 主优化循环

```python
def optimize(self, K: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    使用 SMO 算法求解 SVM 对偶问题
    """
    n_samples = K.shape[0]
    alpha = np.zeros(n_samples)
    b = 0.0
    passes = 0

    while passes < self.max_passes:
        num_changed_alphas = 0

        for i in range(n_samples):
            # 计算误差
            Ei = self._compute_error(i, K, y, alpha, b)

            # 检查 KKT 条件
            if self._violates_kkt(y[i], Ei, alpha[i]):
                # 选择第二个变量
                j = self._select_j(i, n_samples)
                Ej = self._compute_error(j, K, y, alpha, b)

                # 保存旧值
                alpha_i_old = alpha[i]
                alpha_j_old = alpha[j]

                # 计算边界
                L, H = self._compute_bounds(y[i], y[j], alpha[i], alpha[j])

                if L == H:
                    continue

                # 计算 eta
                eta = K[i, i] + K[j, j] - 2 * K[i, j]

                if eta <= 0:
                    continue

                # 更新 alpha[j]
                alpha[j] = alpha_j_old + y[j] * (Ei - Ej) / eta
                alpha[j] = np.clip(alpha[j], L, H)

                # 检查变化
                if abs(alpha[j] - alpha_j_old) < 1e-5:
                    continue

                # 更新 alpha[i]
                alpha[i] = alpha_i_old + y[i] * y[j] * (alpha_j_old - alpha[j])

                # 更新 b
                b1 = (b - Ei
                      - y[i] * (alpha[i] - alpha_i_old) * K[i, i]
                      - y[j] * (alpha[j] - alpha_j_old) * K[i, j])

                b2 = (b - Ej
                      - y[i] * (alpha[i] - alpha_i_old) * K[i, j]
                      - y[j] * (alpha[j] - alpha_j_old) * K[j, j])

                if 0 < alpha[i] < self.C:
                    b = b1
                elif 0 < alpha[j] < self.C:
                    b = b2
                else:
                    b = (b1 + b2) / 2.0

                num_changed_alphas += 1

        if num_changed_alphas == 0:
            passes += 1
        else:
            passes = 0

    return alpha, b
```

**实现要点**：
- 使用 `passes` 计数器判断收敛
- 遍历所有样本，找到违反 KKT 条件的样本
- 更新两个变量并计算新的偏置

### 3.2 误差计算

```python
def _compute_error(
    self,
    i: int,
    K: np.ndarray,
    y: np.ndarray,
    alpha: np.ndarray,
    b: float
) -> float:
    """
    计算第 i 个样本的预测误差
    Ei = f(xi) - yi
    """
    prediction = np.sum(alpha * y * K[i]) + b
    return prediction - y[i]
```

**实现要点**：
- 使用向量化计算
- `K[i]` 是第 i 行，即 xi 与所有样本的核值

### 3.3 KKT 条件检查

```python
def _violates_kkt(self, yi: float, Ei: float, alpha_i: float) -> bool:
    """
    检查是否违反 KKT 条件
    """
    return ((alpha_i < self.C and yi * Ei < -self.tol) or
            (alpha_i > 0 and yi * Ei > self.tol))
```

**实现要点**：
- 检查两种违反情况
- 使用容差 `tol` 避免数值问题

### 3.4 边界计算

```python
def _compute_bounds(
    self,
    yi: float,
    yj: float,
    alpha_i: float,
    alpha_j: float
) -> Tuple[float, float]:
    """
    计算 alpha_j 的上下界
    """
    if yi != yj:
        L = max(0, alpha_j - alpha_i)
        H = min(self.C, self.C + alpha_j - alpha_i)
    else:
        L = max(0, alpha_i + alpha_j - self.C)
        H = min(self.C, alpha_i + alpha_j)

    return L, H
```

**实现要点**：
- 根据 yi 和 yj 的关系计算不同的边界
- 确保 alpha_j 在 [0, C] 范围内

## 4. SVM 分类器实现

### 4.1 初始化

```python
def __init__(
    self,
    kernel: Literal["linear", "rbf", "polynomial"] = "rbf",
    C: float = 1.0,
    gamma: float = 1.0,
    degree: int = 3,
    coef0: float = 1.0,
    tol: float = 1e-3,
    max_passes: int = 10
):
    self.kernel_type = kernel
    self.C = C
    self.gamma = gamma
    self.degree = degree
    self.coef0 = coef0
    self.tol = tol
    self.max_passes = max_passes

    # 初始化核函数
    self._kernel_func = self._create_kernel()

    # 训练后的属性
    self.alpha = None
    self.b = None
    self.support_vectors = None
    self.support_vector_labels = None
    self.support_vector_alphas = None
    self._X_train = None
    self._y_train = None
```

**实现要点**：
- 使用 `Literal` 类型注解限制核函数类型
- 在初始化时创建核函数
- 训练后的属性初始化为 None

### 4.2 训练

```python
def fit(self, X: np.ndarray, y: np.ndarray) -> "SVM":
    """
    训练 SVM 分类器
    """
    # 验证标签
    unique_labels = np.unique(y)
    if not np.array_equal(unique_labels, [-1, 1]):
        raise ValueError("标签必须为 +1 或 -1")

    n_samples = X.shape[0]

    # 预计算核矩阵
    K = precompute_kernel_matrix(X, self._kernel_func)

    # 使用 SMO 算法求解
    smo = SMO(C=self.C, tol=self.tol, max_passes=self.max_passes)
    self.alpha, self.b = smo.optimize(K, y)

    # 提取支持向量
    support_mask = self.alpha > 1e-7
    self.support_vectors = X[support_mask]
    self.support_vector_labels = y[support_mask]
    self.support_vector_alphas = self.alpha[support_mask]

    # 保存训练数据
    self._X_train = X
    self._y_train = y

    return self
```

**实现要点**：
- 验证标签格式
- 预计算核矩阵
- 使用 SMO 优化
- 提取支持向量
- 返回 self 支持链式调用

### 4.3 预测

```python
def predict(self, X: np.ndarray) -> np.ndarray:
    """
    预测新数据的类别
    """
    if self.alpha is None:
        raise RuntimeError("模型尚未训练，请先调用 fit() 方法")

    decision_values = self.decision_function(X)
    return np.sign(decision_values).astype(int)
```

**实现要点**：
- 检查是否已训练
- 使用决策函数的符号作为预测结果

### 4.4 决策函数

```python
def decision_function(self, X: np.ndarray) -> np.ndarray:
    """
    计算决策函数值
    f(x) = sum(alpha_i * y_i * K(xi, x)) + b
    """
    if self.alpha is None:
        raise RuntimeError("模型尚未训练，请先调用 fit() 方法")

    n_samples = X.shape[0]
    decision_values = np.zeros(n_samples)

    for i in range(n_samples):
        s = 0.0
        for j in range(len(self._X_train)):
            if self.alpha[j] > 1e-7:
                s += (self.alpha[j] * self._y_train[j] *
                      self._kernel_func(self._X_train[j], X[i]))
        decision_values[i] = s + self.b

    return decision_values
```

**实现要点**：
- 只使用支持向量 (alpha > 0)
- 计算所有支持向量的贡献之和
- 加上偏置 b

### 4.5 准确率计算

```python
def score(self, X: np.ndarray, y: np.ndarray) -> float:
    """
    计算分类准确率
    """
    predictions = self.predict(X)
    return np.mean(predictions == y)
```

## 5. 实现难点

### 5.1 数值稳定性

**问题**：浮点运算可能导致精度问题

**解决方案**：
- 使用容差 `tol` 判断收敛
- 对 alpha 进行裁剪
- 使用 `1e-7` 作为零的阈值

### 5.2 收敛性

**问题**：SMO 算法可能收敛很慢

**解决方案**：
- 设置合理的 `max_passes`
- 使用 `passes` 计数器判断收敛
- 优化第二个变量的选择策略

### 5.3 内存占用

**问题**：核矩阵需要 O(n²) 的存储空间

**解决方案**：
- 对于小数据集，预计算核矩阵
- 对于大数据集，考虑使用线性核或近似方法

## 6. 测试策略

### 6.1 单元测试

- 测试每个核函数的正确性
- 测试 SMO 算法的收敛性
- 测试 SVM 分类器的功能

### 6.2 集成测试

- 测试完整流程
- 测试不同核函数
- 测试不同数据分布

### 6.3 边界测试

- 测试空数据
- 测试单样本数据
- 测试无效参数

## 7. 优化建议

### 7.1 性能优化

- 使用向量化计算
- 预计算核矩阵
- 优化第二个变量的选择

### 7.2 功能扩展

- 添加更多核函数
- 支持多分类
- 支持回归

### 7.3 代码优化

- 添加类型注解
- 添加文档字符串
- 添加日志记录
