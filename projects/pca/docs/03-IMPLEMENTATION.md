# 03 - 实现细节：PCA 主成分分析

## 1. 实现概述

本文档详细描述 PCA 各模块的实现细节，包括算法选择、代码结构和关键实现决策。

## 2. 协方差矩阵实现

### 2.1 数据中心化

```python
def center_data(X):
    mean = np.mean(X, axis=0)
    X_centered = X - mean
    return X_centered, mean
```

实现要点：
- 使用 `np.mean(X, axis=0)` 计算每列（特征）的均值
- 使用广播机制 `X - mean` 进行中心化
- 返回中心化数据和均值向量（均值需要保存，用于逆变换）

### 2.2 协方差矩阵计算

#### 向量化实现

```python
def compute_covariance_matrix(X):
    n = X.shape[0]
    cov = (1.0 / (n - 1)) * (X.T @ X)
    return cov
```

实现要点：
- 使用矩阵乘法 `X.T @ X`，时间复杂度 O(n×d²)
- 使用 n-1 进行无偏估计（Bessel 校正）
- 假设输入数据已中心化

#### 手动实现（教学用）

```python
def compute_covariance_matrix_manual(X):
    n, d = X.shape
    cov = np.zeros((d, d))
    for i in range(d):
        for j in range(d):
            cov[i, j] = np.sum(X[:, i] * X[:, j]) / (n - 1)
    return cov
```

实现要点：
- 逐元素计算，便于理解协方差定义
- 时间复杂度 O(n×d²)，常数因子较大
- 仅用于教学目的

## 3. 特征值分解实现

### 3.1 幂迭代法

```python
def power_iteration(A, max_iter=1000, tol=1e-10):
    n = A.shape[0]
    v = np.random.randn(n)
    v = v / np.linalg.norm(v)

    for i in range(max_iter):
        Av = A @ v
        eigenvalue = v @ Av
        v_new = Av / np.linalg.norm(Av)

        if np.abs(eigenvalue - eigenvalue_old) < tol:
            return eigenvalue, v_new

        v = v_new

    return eigenvalue, v
```

算法要点：
- 初始向量随机生成并归一化
- 每次迭代：矩阵向量乘法 → Rayleigh 商 → 归一化
- 收敛条件：特征值变化小于阈值
- 收敛速度：|λ₂/λ₁|^t，取决于前两个特征值的比值

### 3.2 矩阵压缩（Deflation）

```python
def deflate(A, eigenvalue, eigenvector):
    return A - eigenvalue * np.outer(eigenvector, eigenvector)
```

算法要点：
- 去除已求得的特征分量
- 压缩后的矩阵的次大特征值就是原矩阵的次大特征值
- 可以重复使用幂迭代求解所有特征值

### 3.3 QR 算法

```python
def qr_algorithm(A, max_iter=1000, tol=1e-10):
    n = A.shape[0]
    A_k = A.copy()
    Q_total = np.eye(n)

    for _ in range(max_iter):
        # Wilkinson shift
        sigma = A_k[-1, -1]

        # QR 分解
        Q, R = np.linalg.qr(A_k - sigma * np.eye(n))

        # 更新
        A_k = R @ Q + sigma * np.eye(n)
        Q_total = Q_total @ Q

        # 检查收敛
        if np.max(np.abs(A_k - np.diag(np.diag(A_k)))) < tol:
            break

    return np.diag(A_k), Q_total
```

算法要点：
- 使用 Wilkinson shift 加速收敛
- 每次迭代进行 QR 分解
- A_k 收敛到对角矩阵，对角线元素即为特征值
- Q_total 的列是对应的特征向量

## 4. PCA 类实现

### 4.1 fit 方法

```python
def fit(self, X):
    # 1. 中心化
    X_centered, self.mean_ = center_data(X)

    # 2. 协方差矩阵
    cov = compute_covariance_matrix(X_centered)

    # 3. 特征值分解
    eigenvalues, eigenvectors = eigen_decomposition(cov, method=self.method)

    # 4. 选择前 k 个
    self.n_components_ = self._resolve_n_components(eigenvalues)
    self.explained_variance_ = eigenvalues[:self.n_components_]
    self.components_ = eigenvectors[:, :self.n_components_].T

    # 5. 计算解释方差比例
    self.explained_variance_ratio_ = self.explained_variance_ / np.sum(eigenvalues)

    return self
```

### 4.2 transform 方法

```python
def transform(self, X):
    # 中心化（使用训练数据的均值）
    X_centered = X - self.mean_

    # 投影
    X_projected = X_centered @ self.components_.T

    return X_projected
```

### 4.3 inverse_transform 方法

```python
def inverse_transform(self, X_projected):
    # 反投影
    X_reconstructed = X_projected @ self.components_ + self.mean_

    return X_reconstructed
```

### 4.4 n_components 选择

```python
def _resolve_n_components(self, eigenvalues):
    if isinstance(self.n_components, float):
        # 按解释方差比例选择
        cumulative = np.cumsum(eigenvalues) / np.sum(eigenvalues)
        n = np.searchsorted(cumulative, self.n_components) + 1
        return n
    else:
        # 直接使用指定数量
        return self.n_components
```

## 5. 可视化实现

### 5.1 可选依赖处理

```python
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
```

### 5.2 2D 散点图

```python
def plot_pca_2d(X_projected, labels=None, ...):
    fig, ax = plt.subplots()

    if labels is not None:
        # 按标签着色
        for label in np.unique(labels):
            mask = labels == label
            ax.scatter(X_projected[mask, 0], X_projected[mask, 1], ...)
    else:
        ax.scatter(X_projected[:, 0], X_projected[:, 1], ...)

    return fig
```

### 5.3 解释方差图

```python
def plot_explained_variance(ratio, ...):
    fig, (ax1, ax2) = plt.subplots(1, 2)

    # 左图：柱状图
    ax1.bar(range(1, len(ratio)+1), ratio)

    # 右图：累积曲线
    cumulative = np.cumsum(ratio)
    ax2.plot(range(1, len(ratio)+1), cumulative, "o-")

    return fig
```

## 6. 关键实现决策

### 6.1 特征向量存储

决策：components_ 存储为 (n_components, n_features) 形状，每行是一个主成分方向。

原因：
- 与 scikit-learn 接口一致
- 便于理解（每行是一个方向）
- 投影时使用 `X @ components_.T`

### 6.2 均值存储

决策：在 fit 时存储训练数据的均值。

原因：
- transform 时需要对新数据进行相同的中心化
- inverse_transform 时需要加回均值

### 6.3 特征值排序

决策：特征值从大到小排列。

原因：
- 大特征值对应重要的主成分
- 便于选择前 k 个成分

### 6.4 数值稳定性

决策：对协方差矩阵进行对称化处理。

```python
A = (A + A.T) / 2.0
```

原因：
- 浮点运算可能导致矩阵不对称
- 对称性是特征值分解的前提

## 7. 代码规范

### 7.1 类型注解

使用 Python 类型注解提高代码可读性：

```python
def compute_covariance_matrix(X: NDArray[np.float64]) -> NDArray[np.float64]:
```

### 7.2 文档字符串

使用 NumPy 风格的文档字符串：

```python
"""
计算协方差矩阵。

Parameters
----------
X : np.ndarray of shape (n_samples, n_features)
    输入数据矩阵。

Returns
-------
cov : np.ndarray of shape (n_features, n_features)
    协方差矩阵。
"""
```

### 7.3 错误处理

使用明确的错误消息：

```python
if X.ndim != 2:
    raise ValueError(f"输入必须是2D矩阵，当前维度: {X.ndim}")
```

## 8. 性能优化

### 8.1 矩阵运算

使用 NumPy 的矩阵运算，避免 Python 循环：

```python
# 好：向量化
cov = X.T @ X

# 差：逐元素循环
for i in range(d):
    for j in range(d):
        cov[i,j] = ...
```

### 8.2 内存管理

避免不必要的数据复制：

```python
# 好：原地操作
X -= mean

# 差：创建新数组
X = X - mean
```

注意：本项目为了代码清晰，选择创建新数组。

## 9. 测试策略

### 9.1 已知结果验证

使用已知解析解的矩阵进行验证：

```python
# 对角矩阵的特征值就是对角线元素
A = np.diag([5, 3, 1])
eigenvalues, _ = eigen_decomposition(A)
assert np.allclose(eigenvalues, [5, 3, 1])
```

### 9.2 NumPy 结果对比

与 NumPy 内置函数结果对比：

```python
cov_ours = compute_covariance_matrix(X)
cov_numpy = np.cov(X, rowvar=False)
assert np.allclose(cov_ours, cov_numpy)
```

### 9.3 数学性质验证

验证数学性质：

```python
# 协方差矩阵对称
assert np.allclose(cov, cov.T)

# 特征向量正交
assert np.allclose(V.T @ V, np.eye(n))

# 解释方差比例之和为1
assert np.isclose(np.sum(ratio), 1.0)
```

## 10. 核 PCA 实现

### 10.1 核矩阵计算

```python
def _compute_kernel(self, X, Y=None):
    if Y is None:
        Y = X

    if self.kernel == 'rbf':
        sq_dists = np.sum(X**2, axis=1, keepdims=True) + \
                   np.sum(Y**2, axis=1, keepdims=True).T - \
                   2 * X @ Y.T
        K = np.exp(-self.gamma_ * sq_dists)

    elif self.kernel == 'poly':
        K = (self.gamma_ * X @ Y.T + self.coef0) ** self.degree

    return K
```

实现要点：
- 使用广播机制计算距离矩阵
- 支持多种核函数
- gamma 参数控制 RBF 核的宽度

### 10.2 核矩阵中心化

```python
one_n = np.ones((n_samples, n_samples)) / n_samples
K_centered = K - one_n @ K - K @ one_n + one_n @ K @ one_n
```

实现要点：
- 核矩阵必须中心化，否则特征值分解结果不正确
- 使用矩阵乘法实现中心化

### 10.3 特征值分解和归一化

```python
eigenvalues, eigenvectors = np.linalg.eigh(K_centered)

# 选择正特征值
positive_idx = eigenvalues > 1e-10
eigenvalues = eigenvalues[positive_idx]
eigenvectors = eigenvectors[:, positive_idx]

# 归一化特征向量
alphas = eigenvectors / np.sqrt(eigenvalues)[np.newaxis, :]
```

实现要点：
- 只保留正特征值
- 归一化确保投影后方差为 1

## 11. 增量 PCA 实现

### 11.1 增量均值更新

```python
# 增量更新均值
delta = col_mean - self.mean_
self.mean_ = self.mean_ + delta * n_samples / n_total
```

实现要点：
- 使用增量公式避免重新计算全部数据的均值
- 数值稳定

### 11.2 增量 SVD 更新

```python
# 构建组合矩阵
K = np.vstack([
    np.diag(self.singular_values_[:self.n_components]),
    X_centered @ self.components_[:self.n_components].T
])

# 更新 SVD
U_k, S_k, Vt_k = np.linalg.svd(K, full_matrices=False)

# 更新主成分
self.components_ = Vt_k[:n_comp] @ self.components_[:self.n_components]
```

实现要点：
- 使用矩阵分解技巧避免重新计算完整 SVD
- 保持主成分的正交性

### 11.3 增量方差更新

```python
# 增量更新方差
self.var_ = (
    (self.n_samples_seen_ * self.var_ + n_samples * col_var) / n_total +
    self.n_samples_seen_ * n_samples * (delta ** 2) / (n_total ** 2)
)
```

实现要点：
- 使用 Welford 算法的增量版本
- 考虑均值变化对方差的影响

## 12. 实现总结

### 12.1 代码量统计

| 模块 | 行数 | 说明 |
|------|------|------|
| covariance.py | ~80 | 协方差矩阵计算 |
| eigen.py | ~180 | 特征值分解 |
| pca.py | ~200 | PCA 核心类 |
| kernel_pca.py | ~150 | 核 PCA |
| incremental_pca.py | ~200 | 增量 PCA |
| visualization.py | ~250 | 可视化工具 |
| 总计 | ~1060 | |

### 12.2 关键学习点

1. 协方差矩阵的计算和性质
2. 特征值分解的两种算法
3. PCA 的完整流程
4. 数值计算的稳定性问题
5. 核技巧实现非线性降维
6. 增量算法处理大数据
