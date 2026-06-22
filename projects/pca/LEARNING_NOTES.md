# PCA 主成分分析 - 学习笔记

## 1. 核心概念

### 1.1 什么是降维？

降维是将高维数据转换为低维表示的过程，同时尽可能保留数据的重要信息。

**为什么需要降维？**
- 维度灾难：高维数据难以可视化和分析
- 计算效率：减少计算量和存储空间
- 噪声过滤：去除冗余信息和噪声
- 特征工程：为机器学习准备更好的特征

### 1.2 PCA 的核心思想

PCA 寻找数据方差最大的方向（主成分），将数据投影到这些方向上。

**直观理解**：
- 想象一个椭圆形的数据云
- PC1 是椭圆的长轴方向（方差最大）
- PC2 是椭圆的短轴方向（方差次大）
- 将数据投影到长轴上，保留了大部分信息

**数学目标**：
```
找到方向 w，使得投影后的方差最大：
maximize Var(Xw) = w^T * C * w
subject to ||w|| = 1
```

## 2. 数学基础

### 2.1 协方差矩阵

**定义**：
```
C = (1/(n-1)) * X^T * X
```

**性质**：
- 对称矩阵：C = C^T
- 半正定：所有特征值 >= 0
- 对角线：各特征的方差
- 非对角线：特征间的协方差

**直觉理解**：
- 协方差矩阵描述了数据的"形状"
- 对角线大 → 该特征变化大
- 非对角线大 → 两个特征相关性强

### 2.2 特征值分解

**定义**：
```
C * v = λ * v
```

其中：
- v 是特征向量（方向）
- λ 是特征值（大小）

**物理意义**：
- 特征向量：数据变化的主要方向
- 特征值：该方向上的变化程度

**分解公式**：
```
C = V * Λ * V^T
```

其中：
- V = [v₁, v₂, ..., vₐ] 是特征向量矩阵
- Λ = diag(λ₁, λ₂, ..., λₐ) 是特征值对角矩阵

### 2.3 投影

**公式**：
```
X_projected = X_centered * Vₖ
```

其中 Vₖ 是前 k 个特征向量。

**几何解释**：
- 将数据点投影到主成分方向上
- 从 d 维降到 k 维
- 保留了数据的主要变化模式

## 3. 算法实现

### 3.1 PCA 流程

```
输入: 数据 X (n×d)，目标维度 k

1. 中心化
   X_centered = X - mean(X)

2. 协方差矩阵
   C = (1/(n-1)) * X_centered^T * X_centered

3. 特征值分解
   C = V * Λ * V^T
   按特征值从大到小排序

4. 选择前 k 个特征向量
   Vₖ = V[:, :k]

5. 投影
   X_projected = X_centered * Vₖ

输出: X_projected (n×k)
```

### 3.2 特征值分解算法

#### 幂迭代法

**原理**：
```
从随机向量 v 开始
重复: v = A * v / ||A * v||
v 收敛到最大特征值对应的特征向量
```

**优点**：实现简单
**缺点**：只能求一个特征值

#### QR 算法

**原理**：
```
重复:
  A = Q * R  (QR分解)
  A = R * Q  (更新)
A 收敛到对角矩阵
```

**优点**：可以求所有特征值
**缺点**：实现复杂

## 4. 关键实现细节

### 4.1 为什么需要中心化？

**原因**：
- PCA 寻找方差最大的方向
- 如果数据不中心化，均值会影响方差计算
- 中心化后，协方差矩阵才能正确反映数据的变化模式

**代码**：
```python
mean = np.mean(X, axis=0)
X_centered = X - mean
```

### 4.2 为什么用 n-1 而不是 n？

**原因**：
- 这是无偏估计（Bessel 校正）
- 当样本量大时，差异很小
- 当样本量小时，n-1 更准确

**公式**：
```
有偏估计: σ² = (1/n) * Σ(xi - μ)²
无偏估计: σ² = (1/(n-1)) * Σ(xi - x̄)²
```

### 4.3 如何选择主成分数量？

**方法1：按数量选择**
```python
pca = PCA(n_components=2)
```

**方法2：按解释方差比例选择**
```python
pca = PCA(n_components=0.95)  # 保留95%的方差
```

**经验法则**：
- 保留 95% 以上的方差
- 或观察"肘部"拐点

### 4.4 特征向量的符号问题

**问题**：
- 特征向量 v 和 -v 都是有效的
- 不同实现可能给出不同符号

**解决**：
- 测试时比较绝对值
- 或确保第一个非零元素为正

## 5. 实际应用

### 5.1 数据压缩

**场景**：将 50 维数据压缩到 5 维

**效果**：
- 存储空间减少 90%
- 重建误差很小
- 保留主要信息

**代码**：
```python
pca = PCA(n_components=5)
X_compressed = pca.fit_transform(X)
X_reconstructed = pca.inverse_transform(X_compressed)
```

### 5.2 噪声过滤

**场景**：去除数据中的噪声

**原理**：
- 信号通常在高方差方向
- 噪声通常在低方差方向
- PCA 保留高方差方向，去除低方差方向

**代码**：
```python
pca = PCA(n_components=k)  # k < 原始维度
X_filtered = pca.inverse_transform(pca.fit_transform(X))
```

### 5.3 数据可视化

**场景**：将高维数据降到 2D 或 3D

**应用**：
- 探索数据结构
- 发现聚类
- 识别异常值

**代码**：
```python
pca = PCA(n_components=2)
X_2d = pca.fit_transform(X)
plt.scatter(X_2d[:, 0], X_2d[:, 1])
```

### 5.4 特征工程

**场景**：为机器学习准备特征

**优势**：
- 去除冗余特征
- 减少维度
- 可能提高模型性能

**代码**：
```python
pca = PCA(n_components=50)
X_features = pca.fit_transform(X)
model.fit(X_features, y)
```

## 6. PCA 的局限性

### 6.1 线性假设

**问题**：PCA 只能捕获线性结构

**例子**：
- 对于螺旋形数据，PCA 效果差
- 需要使用核 PCA 或其他非线性方法

### 6.2 方差不等于重要性

**问题**：方差大的方向不一定重要

**例子**：
- 如果噪声方差大于信号方差
- PCA 会保留噪声而不是信号

### 6.3 对异常值敏感

**问题**：异常值会影响协方差矩阵

**解决**：
- 使用鲁棒 PCA
- 先去除异常值

### 6.4 可解释性

**问题**：主成分是原始特征的线性组合，难以解释

**例子**：
- PC1 = 0.3*身高 + 0.5*体重 + 0.2*年龄
- 这个组合代表什么？

## 7. 与其他方法的比较

### 7.1 PCA vs t-SNE

| 方面 | PCA | t-SNE |
|------|-----|-------|
| 类型 | 线性 | 非线性 |
| 速度 | 快 | 慢 |
| 保留结构 | 全局 | 局部 |
| 可逆性 | 可逆 | 不可逆 |
| 主要用途 | 压缩、特征工程 | 可视化 |

### 7.2 PCA vs LDA

| 方面 | PCA | LDA |
|------|-----|-----|
| 类型 | 无监督 | 有监督 |
| 目标 | 最大方差 | 最大类间距离 |
| 适用 | 通用 | 分类问题 |

### 7.3 PCA vs Autoencoder

| 方面 | PCA | Autoencoder |
|------|-----|-------------|
| 类型 | 线性 | 非线性 |
| 参数 | 无 | 需要训练 |
| 解释性 | 强 | 弱 |
| 数据需求 | 少 | 多 |

## 8. 调试技巧

### 8.1 检查协方差矩阵

```python
# 应该对称
assert np.allclose(cov, cov.T)

# 对角线应该非负
assert np.all(np.diag(cov) >= 0)
```

### 8.2 检查特征值

```python
# 特征值应该非负（协方差矩阵半正定）
assert np.all(eigenvalues >= 0)

# 特征值应该从大到小排列
assert np.all(np.diff(eigenvalues) <= 0)
```

### 8.3 检查特征向量

```python
# 应该正交
assert np.allclose(V.T @ V, np.eye(n))

# 应该是单位向量
assert np.allclose(np.linalg.norm(V, axis=0), 1.0)
```

### 8.4 检查投影

```python
# 解释方差比例之和应该为1
assert np.isclose(np.sum(ratio), 1.0)

# 全维度重建应该无损
assert np.allclose(X, pca.inverse_transform(pca.fit_transform(X)))
```

## 9. 常见错误

### 9.1 忘记中心化

**错误**：
```python
cov = X.T @ X  # 错误！
```

**正确**：
```python
X_centered = X - np.mean(X, axis=0)
cov = X_centered.T @ X_centered / (n-1)
```

### 9.2 使用 n 而不是 n-1

**错误**：
```python
cov = X.T @ X / n  # 有偏估计
```

**正确**：
```python
cov = X.T @ X / (n-1)  # 无偏估计
```

### 9.3 特征值排序错误

**错误**：
```python
# 假设特征值已经排序
components = eigenvectors[:, :k]
```

**正确**：
```python
# 先排序
idx = np.argsort(eigenvalues)[::-1]
eigenvalues = eigenvalues[idx]
eigenvectors = eigenvectors[:, idx]
components = eigenvectors[:, :k]
```

### 9.4 忘记保存均值

**错误**：
```python
# 训练时中心化
X_centered = X - np.mean(X, axis=0)

# 测试时忘记用同一个均值
X_test_centered = X_test - np.mean(X_test, axis=0)  # 错误！
```

**正确**：
```python
# 训练时保存均值
mean = np.mean(X, axis=0)
X_centered = X - mean

# 测试时使用训练数据的均值
X_test_centered = X_test - mean
```

## 10. 学习资源

### 10.1 推荐阅读

1. **教科书**：
   - "Pattern Recognition and Machine Learning" - Bishop
   - "The Elements of Statistical Learning" - Hastie et al.

2. **在线资源**：
   - [PCA 维基百科](https://en.wikipedia.org/wiki/Principal_component_analysis)
   - [StatQuest PCA 视频](https://www.youtube.com/watch?v=FgakZw6K1QQ)

3. **论文**：
   - Pearson, K. (1901). "On Lines and Planes of Closest Fit"
   - Hotelling, H. (1933). "Analysis of a Complex of Statistical Variables"

### 10.2 实践建议

1. 从简单数据开始（2-3维）
2. 先理解数学原理
3. 手动计算小例子
4. 与 NumPy 结果对比
5. 尝试不同数据集
6. 分析解释方差比例

## 11. 总结

### 核心要点

1. **PCA 是降维方法**：将高维数据投影到低维空间
2. **基于协方差矩阵**：描述特征之间的关系
3. **特征值分解**：找到主要变化方向
4. **保留主要信息**：按特征值大小选择主成分

### 学习路径

1. 理解协方差矩阵
2. 理解特征值分解
3. 理解投影操作
4. 实现 PCA 算法
5. 应用到实际问题

### 实践建议

1. 多动手实现
2. 多分析结果
3. 多尝试不同数据
4. 多阅读源码
5. 多与他人讨论
