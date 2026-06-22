# 学习笔记 - SVM 支持向量机

## 1. 核心概念理解

### 1.1 什么是 SVM?

SVM (Support Vector Machine) 是一种二分类算法，核心思想是找到一个超平面，使得两类数据之间的间隔最大化。

**关键概念**：
- **超平面**：将数据分为两类的决策边界
- **间隔 (Margin)**：超平面到最近数据点的距离
- **支持向量 (Support Vectors)**：距离超平面最近的数据点，决定了超平面的位置

**直觉理解**：
想象两堆豆子被一条线分开，SVM 找的不是任意一条线，而是那条让两堆豆子离线最远的线。

### 1.2 为什么需要核函数?

**问题**：很多数据在原始空间中线性不可分

**解决方案**：将数据映射到高维空间，使其变得线性可分

**核技巧**：通过核函数，我们可以在高维空间中计算内积，而无需显式计算高维映射

```
原始空间 (2D)          高维空间 (3D)
    o o                    o
   o o o    映射到        o o o
   ------              ----
   x x x               x x x
    x x                   x
```

### 1.3 SMO 算法的作用

**问题**：SVM 对偶问题有约束，不能直接用梯度下降

**SMO 解决方案**：
1. 每次只优化两个变量 (因为等式约束至少需要两个变量)
2. 固定其他变量，解析求解这两个变量的最优解
3. 重复直到收敛

**为什么是两个变量?**
因为约束 $\sum \alpha_i y_i = 0$，改变一个 $\alpha_i$ 必须同时改变另一个来保持约束。

## 2. 数学推导

### 2.1 SVM 原始问题

目标：找到最大间隔的超平面

超平面：$w \cdot x + b = 0$

间隔：$\frac{2}{\|w\|}$

优化问题：
$$\min_{w,b} \frac{1}{2} \|w\|^2$$
$$\text{s.t. } y_i(w \cdot x_i + b) \geq 1, \forall i$$

### 2.2 对偶问题

使用拉格朗日乘子法，引入 $\alpha_i \geq 0$：

$$L(w, b, \alpha) = \frac{1}{2}\|w\|^2 - \sum_i \alpha_i [y_i(w \cdot x_i + b) - 1]$$

对 $w$ 和 $b$ 求导并令其为零，得到对偶问题：

$$\max_\alpha \sum_i \alpha_i - \frac{1}{2}\sum_{i,j} \alpha_i \alpha_j y_i y_j (x_i \cdot x_j)$$
$$\text{s.t. } 0 \leq \alpha_i \leq C, \forall i$$
$$\sum_i \alpha_i y_i = 0$$

### 2.3 核函数引入

将内积 $(x_i \cdot x_j)$ 替换为核函数 $K(x_i, x_j)$：

$$\max_\alpha \sum_i \alpha_i - \frac{1}{2}\sum_{i,j} \alpha_i \alpha_j y_i y_j K(x_i, x_j)$$

### 2.4 SMO 更新公式

选择 $\alpha_i$ 和 $\alpha_j$，固定其他变量：

1. 计算误差：$E_i = f(x_i) - y_i$
2. 计算边界：$L, H$
3. 计算 $\eta = K_{ii} + K_{jj} - 2K_{ij}$
4. 更新 $\alpha_j$：$\alpha_j^{new} = \alpha_j^{old} + \frac{y_j(E_i - E_j)}{\eta}$
5. 裁剪：$\alpha_j^{new} = \text{clip}(\alpha_j^{new}, L, H)$
6. 更新 $\alpha_i$：$\alpha_i^{new} = \alpha_i^{old} + y_i y_j (\alpha_j^{old} - \alpha_j^{new})$
7. 更新 $b$

## 3. 实现细节

### 3.1 核函数实现

```python
def linear_kernel():
    def kernel(x, y):
        return np.dot(x, y)
    return kernel

def rbf_kernel(gamma=1.0):
    def kernel(x, y):
        diff = x - y
        return np.exp(-gamma * np.dot(diff, diff))
    return kernel
```

**设计决策**：
- 使用闭包返回核函数，便于参数化
- 核函数签名统一：`(x, y) -> float`

### 3.2 SMO 实现要点

```python
def _violates_kkt(self, yi, Ei, alpha_i):
    """检查是否违反 KKT 条件"""
    return ((alpha_i < self.C and yi * Ei < -self.tol) or
            (alpha_i > 0 and yi * Ei > self.tol))
```

**KKT 条件**：
- $\alpha_i = 0$：$y_i f(x_i) \geq 1$
- $0 < \alpha_i < C$：$y_i f(x_i) = 1$
- $\alpha_i = C$：$y_i f(x_i) \leq 1$

### 3.3 支持向量提取

```python
support_mask = self.alpha > 1e-7
self.support_vectors = X[support_mask]
```

支持向量是 $\alpha_i > 0$ 的样本。

## 4. 调试经验

### 4.1 常见问题

**问题 1**：准确率只有 50%
- 原因：标签格式错误，应该是 +1/-1 而不是 0/1
- 解决：检查标签格式

**问题 2**：收敛速度慢
- 原因：max_passes 太小或 tol 太大
- 解决：增大 max_passes，减小 tol

**问题 3**：过拟合
- 原因：C 太大或 gamma 太大
- 解决：减小 C 或 gamma

### 4.2 调试技巧

1. 打印支持向量数量，应该远小于总样本数
2. 检查约束 $\sum \alpha_i y_i = 0$ 是否满足
3. 可视化决策边界

## 5. 性能优化

### 5.1 核矩阵预计算

```python
K = precompute_kernel_matrix(X, kernel_func)
```

避免在 SMO 迭代中重复计算核函数。

### 5.2 启发式选择

当前实现使用随机选择第二个乘子，更优的方法是选择使 $|E_i - E_j|$ 最大的 $j$。

## 6. 与其他算法对比

| 算法 | 优点 | 缺点 |
|------|------|------|
| SVM | 小样本效果好，核技巧 | 大数据集慢，对参数敏感 |
| 逻辑回归 | 简单，概率输出 | 线性边界 |
| 决策树 | 可解释性强 | 容易过拟合 |
| 神经网络 | 表达能力强 | 需要大量数据 |

## 7. 进一步学习

- [ ] 软间隔 SVM
- [ ] 多分类 SVM (一对一、一对多)
- [ ] SVR (支持向量回归)
- [ ] 核方法的更多应用
- [ ] 与深度学习的结合

## 8. 总结

通过从零实现 SVM，我深入理解了：
1. SVM 的几何直觉和数学原理
2. 核函数如何将数据映射到高维空间
3. SMO 算法如何高效求解对偶问题
4. 支持向量的概念和作用

**最有价值的收获**：
- 理解了"核技巧"的优雅之处
- 体会了优化算法设计的精妙
- 认识到理论和实践之间的差距 (如数值稳定性)
