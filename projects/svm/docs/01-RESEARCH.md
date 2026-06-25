# 01 - 调研文档

## 1. 项目背景

### 1.1 什么是 SVM?

支持向量机 (Support Vector Machine, SVM) 是一种监督学习算法，主要用于分类和回归分析。SVM 的核心思想是找到一个最优的超平面，使得不同类别数据之间的间隔最大化。

### 1.2 历史发展

- **1963年**：Vapnik 和 Lerner 提出原始 SVM
- **1992年**：Boser, Guyon, Vapnik 引入核技巧
- **1993年**：Cortes 和 Vapnik 提出软间隔 SVM
- **1998年**：Platt 提出 SMO 算法，大幅提高训练效率

### 1.3 应用领域

- 文本分类
- 图像识别
- 生物信息学
- 手写数字识别
- 人脸检测

## 2. 核心原理

### 2.1 线性可分情况

对于线性可分的数据，存在无数个超平面可以将两类数据分开。SVM 选择的是使间隔最大的那个超平面。

**间隔的定义**：
- 函数间隔：$\hat{\gamma}_i = y_i(w \cdot x_i + b)$
- 几何间隔：$\gamma_i = \frac{y_i(w \cdot x_i + b)}{\|w\|}$

**最大间隔**：
$$\max_{w,b} \frac{2}{\|w\|}$$
$$\text{s.t. } y_i(w \cdot x_i + b) \geq 1, \forall i$$

### 2.2 对偶问题

通过拉格朗日乘子法，将原始问题转化为对偶问题：

$$\max_\alpha \sum_i \alpha_i - \frac{1}{2}\sum_{i,j} \alpha_i \alpha_j y_i y_j (x_i \cdot x_j)$$
$$\text{s.t. } \alpha_i \geq 0, \forall i$$
$$\sum_i \alpha_i y_i = 0$$

**对偶问题的优点**：
1. 只涉及内积，便于引入核函数
2. 优化变量是 $\alpha_i$，数量等于样本数
3. 支持向量对应的 $\alpha_i > 0$

### 2.3 软间隔 SVM

对于线性不可分的数据，引入松弛变量 $\xi_i$：

$$\min_{w,b,\xi} \frac{1}{2}\|w\|^2 + C\sum_i \xi_i$$
$$\text{s.t. } y_i(w \cdot x_i + b) \geq 1 - \xi_i, \forall i$$
$$\xi_i \geq 0, \forall i$$

**参数 C 的作用**：
- C 大：对误分类的惩罚更大，间隔更小，可能过拟合
- C 小：对误分类的惩罚更小，间隔更大，可能欠拟合

## 3. 核函数

### 3.1 核技巧

核技巧允许我们在高维空间中计算内积，而无需显式计算高维映射。

**核函数定义**：$K(x, y) = \phi(x) \cdot \phi(y)$

其中 $\phi$ 是从低维空间到高维空间的映射。

### 3.2 常用核函数

| 核函数 | 公式 | 参数 | 特点 |
|--------|------|------|------|
| 线性核 | $K(x,y) = x \cdot y$ | 无 | 简单，适合线性可分数据 |
| 多项式核 | $K(x,y) = (x \cdot y + c)^d$ | d: 阶数, c: 系数 | 可调复杂度 |
| RBF 核 | $K(x,y) = \exp(-\gamma\|x-y\|^2)$ | γ: 宽度参数 | 最常用，可映射到无限维 |
| Sigmoid 核 | $K(x,y) = \tanh(\gamma x \cdot y + c)$ | γ, c | 类似神经网络，不总满足 Mercer 条件 |

### 3.3 核函数的选择

**选择原则**：
1. 线性可分数据 → 线性核
2. 样本数少，特征多 → 线性核
3. 样本数多，特征少 → RBF 核
4. 不确定 → 先试 RBF 核

**RBF 核的 γ 参数**：
- γ 大：每个支持向量只影响附近的数据点，可能导致过拟合
- γ 小：每个支持向量影响更广的区域，可能导致欠拟合

## 4. SMO 算法

### 4.1 算法思想

SMO (Sequential Minimal Optimization) 算法的核心思想是将大优化问题分解为多个小优化问题。

**为什么选择两个变量?**
由于约束 $\sum \alpha_i y_i = 0$，至少需要同时更新两个变量。

### 4.2 算法步骤

1. **选择变量**：选择两个拉格朗日乘子 $\alpha_i$ 和 $\alpha_j$
2. **计算边界**：计算 $\alpha_j$ 的上下界 L 和 H
3. **计算更新**：
   - 计算 $\eta = K_{ii} + K_{jj} - 2K_{ij}$
   - 更新 $\alpha_j^{new} = \alpha_j^{old} + \frac{y_j(E_i - E_j)}{\eta}$
   - 裁剪 $\alpha_j^{new}$ 到 [L, H]
4. **更新其他变量**：
   - 更新 $\alpha_i^{new} = \alpha_i^{old} + y_i y_j (\alpha_j^{old} - \alpha_j^{new})$
   - 更新偏置 b
5. **检查收敛**：如果所有变量都满足 KKT 条件，则收敛

### 4.3 KKT 条件

KKT (Karush-Kuhn-Tucker) 条件是最优解的必要条件：

- $\alpha_i = 0$：$y_i f(x_i) \geq 1$
- $0 < \alpha_i < C$：$y_i f(x_i) = 1$
- $\alpha_i = C$：$y_i f(x_i) \leq 1$

## 5. SVR 回归

### 5.1 epsilon 不敏感损失

SVR 使用 epsilon 不敏感损失函数：
$$L_\epsilon(y, f(x)) = \max(0, |y - f(x)| - \epsilon)$$

只有当预测误差超过 epsilon 时才计算损失。

### 5.2 SVR 对偶问题

$$\min \frac{1}{2} \sum_{i,j} (\alpha_i - \alpha_i^*)(\alpha_j - \alpha_j^*) K(x_i, x_j) + \epsilon \sum_i (\alpha_i + \alpha_i^*) - \sum_i y_i(\alpha_i - \alpha_i^*)$$

约束：$0 \leq \alpha_i, \alpha_i^* \leq C$，$\sum_i (\alpha_i - \alpha_i^*) = 0$

## 6. 多分类策略

### 6.1 One-vs-Rest (OvR)

为每个类别训练一个二分类器：
- 类别 k 的正类：标签为 k 的样本
- 类别 k 的负类：标签不为 k 的所有样本

预测时选择决策函数值最大的类别。

### 6.2 One-vs-One (OvO)

为每对类别训练一个二分类器：
- 总共需要 $C(n, 2) = \frac{n(n-1)}{2}$ 个分类器
- 预测时使用投票机制

## 7. 实现方案

### 7.1 技术栈

- **语言**：Python
- **依赖**：NumPy
- **测试**：pytest

### 7.2 模块设计

```
svm/
├── kernel.py      # 核函数模块
├── smo.py         # SMO 算法模块
├── svm.py         # SVM 分类器模块
├── svr.py         # SVR 回归器模块
├── multiclass.py  # 多分类策略模块
└── metrics.py     # 模型评估指标模块
```

## 8. 参考资料

1. Vapnik, V. (1995). The Nature of Statistical Learning Theory
2. Platt, J. (1998). Sequential Minimal Optimization
3. [sklearn SVM 文档](https://scikit-learn.org/stable/modules/svm.html)
4. [支持向量机通俗导论](https://blog.csdn.net/v_JULY_v/article/details/7624837)
