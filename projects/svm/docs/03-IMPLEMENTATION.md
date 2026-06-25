# 03 - 实现文档

## 1. 实现概述

本项目从零实现了完整的 SVM 系统，包括分类、回归、多分类和评估指标。所有代码仅依赖 NumPy。

## 2. 核函数实现 (kernel.py)

### 2.1 线性核

```python
def linear_kernel():
    def kernel(x, y):
        return np.dot(x, y)
    return kernel
```

### 2.2 RBF 核

```python
def rbf_kernel(gamma=1.0):
    def kernel(x, y):
        diff = x - y
        return np.exp(-gamma * np.dot(diff, diff))
    return kernel
```

### 2.3 多项式核

```python
def polynomial_kernel(degree=3, coef0=1.0):
    def kernel(x, y):
        return (np.dot(x, y) + coef0) ** degree
    return kernel
```

### 2.4 Sigmoid 核

```python
def sigmoid_kernel(gamma=1.0, coef0=0.0):
    def kernel(x, y):
        return np.tanh(gamma * np.dot(x, y) + coef0)
    return kernel
```

### 2.5 核矩阵预计算

```python
def precompute_kernel_matrix(X, kernel_func):
    n = X.shape[0]
    K = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            K[i, j] = kernel_func(X[i], X[j])
            K[j, i] = K[i, j]
    return K
```

## 3. SMO 算法实现 (smo.py)

### 3.1 主优化循环

SMO 算法的核心是交替优化两个拉格朗日乘子：

1. 遍历所有样本
2. 检查是否违反 KKT 条件
3. 如果违反，选择第二个乘子进行更新
4. 更新 alpha_i, alpha_j 和偏置 b
5. 重复直到收敛

### 3.2 KKT 条件检查

```python
def _violates_kkt(self, yi, Ei, alpha_i):
    return ((alpha_i < self.C and yi * Ei < -self.tol) or
            (alpha_i > 0 and yi * Ei > self.tol))
```

### 3.3 边界计算

```python
def _compute_bounds(self, yi, yj, alpha_i, alpha_j):
    if yi != yj:
        L = max(0, alpha_j - alpha_i)
        H = min(self.C, self.C + alpha_j - alpha_i)
    else:
        L = max(0, alpha_i + alpha_j - self.C)
        H = min(self.C, alpha_i + alpha_j)
    return L, H
```

## 4. SVM 分类器实现 (svm.py)

### 4.1 训练流程

```python
def fit(self, X, y):
    # 1. 验证标签 (+1/-1)
    # 2. 预计算核矩阵
    K = precompute_kernel_matrix(X, self._kernel_func)
    # 3. 使用 SMO 求解
    self.alpha, self.b = smo.optimize(K, y)
    # 4. 提取支持向量
    support_mask = self.alpha > 1e-7
    self.support_vectors = X[support_mask]
```

### 4.2 预测流程

```python
def predict(self, X):
    decision_values = self.decision_function(X)
    return np.sign(decision_values).astype(int)

def decision_function(self, X):
    # f(x) = sum(alpha_i * y_i * K(x_i, x)) + b
    for i in range(n_test):
        for j in range(n_train):
            if alpha[j] > 1e-7:
                s += alpha[j] * y[j] * K(x_j, x_i)
        decision[i] = s + b
```

## 5. SVR 回归器实现 (svr.py)

### 5.1 SVR 的 SMO 算法

SVR 引入两组乘子 alpha 和 alpha_star，满足：
- `alpha_i * alpha_star_i = 0` (互补松弛)
- `sum(alpha - alpha_star) = 0`

每次迭代选择一个样本，更新其 alpha 或 alpha_star。

### 5.2 预测

```python
def predict(self, X):
    w = self.alpha - self.alpha_star
    for i in range(n_test):
        for j in range(n_train):
            if abs(w[j]) > 1e-7:
                s += w[j] * K(x_j, x_i)
        predictions[i] = s + self.b
```

## 6. 多分类实现 (multiclass.py)

### 6.1 One-vs-Rest

```python
class OneVsRestSVM:
    def fit(self, X, y):
        for cls in self.classes:
            binary_y = np.where(y == cls, 1, -1)
            svm = SVM(...)
            svm.fit(X, binary_y)
            self.classifiers.append(svm)

    def predict(self, X):
        # 选择决策值最大的类别
        decision_values[:, idx] = svm.decision_function(X)
        return self.classes[argmax(decision_values)]
```

### 6.2 One-vs-One

```python
class OneVsOneSVM:
    def fit(self, X, y):
        for i, j in combinations(classes, 2):
            mask = (y == i) | (y == j)
            svm.fit(X[mask], binary_y)
            self.classifiers.append(svm)

    def predict(self, X):
        # 投票机制
        for svm in classifiers:
            votes[pred == cls_i] += 1
        return self.classes[argmax(votes)]
```

## 7. 评估指标实现 (metrics.py)

### 7.1 分类指标

- **准确率**：`accuracy = correct / total`
- **精确率**：`precision = TP / (TP + FP)`
- **召回率**：`recall = TP / (TP + FN)`
- **F1**：`f1 = 2 * p * r / (p + r)`
- **混淆矩阵**：`C[i][j] = 真实为i且预测为j的样本数`

支持 binary/micro/macro 三种平均方式。

### 7.2 回归指标

- **MSE**：`mse = mean((y_true - y_pred)^2)`
- **R2**：`r2 = 1 - SS_res / SS_tot`
- **MAE**：`mae = mean(|y_true - y_pred|)`
