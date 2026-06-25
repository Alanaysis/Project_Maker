# 贝叶斯优化 - 研究文档

## 1. 研究背景

### 1.1 问题定义

贝叶斯优化（Bayesian Optimization, BO）是一种用于全局优化黑盒函数的序列化决策策略。其核心问题是：

$$\max_{x \in \mathcal{X}} f(x)$$

其中：
- $f(x)$ 是目标函数（可能是非凸、非连续、噪声观测）
- $\mathcal{X}$ 是搜索空间（通常是有界子集）
- 每次函数评估代价高昂

### 1.2 应用场景

1. **机器学习超参数调优**
   - 学习率、批大小、正则化参数
   - 神经网络架构搜索（NAS）
   - 模型选择

2. **实验设计与优化**
   - 药物发现
   - 材料科学
   - 化学反应条件优化

3. **工程优化**
   - 控制器参数调优
   - 机器人控制策略
   - 芯片设计

4. **推荐系统**
   - A/B 测试优化
   - 用户体验优化

### 1.3 与其他优化方法的比较

| 方法 | 梯度信息 | 全局最优 | 评估次数 | 适用场景 |
|------|---------|---------|---------|---------|
| 梯度下降 | 需要 | 局部 | 大量 | 连续可微函数 |
| 随机搜索 | 不需要 | 近似 | 大量 | 低维空间 |
| 网格搜索 | 不需要 | 近似 | 指数级 | 离散空间 |
| 贝叶斯优化 | 不需要 | 近似全局 | 少量 | 高代价黑盒函数 |

## 2. 理论基础

### 2.1 高斯过程

高斯过程（Gaussian Process, GP）是贝叶斯优化的核心代理模型。

#### 定义

高斯过程是随机变量的集合，其中任意有限个随机变量的联合分布都是高斯分布：

$$f(x) \sim \mathcal{GP}(m(x), k(x, x'))$$

其中：
- $m(x)$ 是均值函数：$m(x) = E[f(x)]$
- $k(x, x')$ 是核函数（协方差函数）：$k(x, x') = E[(f(x) - m(x))(f(x') - m(x'))]$

#### 核函数

1. **径向基函数核（RBF/高斯核）**

   $$k(x, x') = \sigma_f^2 \exp\left(-\frac{\|x - x'\|^2}{2l^2}\right)$$

   - 无限可微
   - 最常用的默认选择

2. **Matérn 核**

   $$k(x, x') = \sigma_f^2 \frac{2^{1-\nu}}{\Gamma(\nu)} \left(\frac{\sqrt{2\nu}\|x - x'\|}{l}\right)^\nu K_\nu\left(\frac{\sqrt{2\nu}\|x - x'\|}{l}\right)$$

   - $\nu = 1/2$：指数核（不连续）
   - $\nu = 3/2$：一阶可微
   - $\nu = 5/2$：二阶可微（常用）
   - $\nu \to \infty$：RBF 核

3. **白噪声核**

   $$k(x, x') = \sigma_n^2 \delta(x, x')$$

   - 用于建模观测噪声

#### 预测

给定训练数据 $\mathcal{D} = \{(x_i, y_i)\}_{i=1}^n$，在新点 $x_*$ 的预测分布为：

$$p(f_* | x_*, \mathcal{D}) = \mathcal{N}(\mu_*, \sigma_*^2)$$

其中：
$$\mu_* = K(x_*, X) [K(X, X) + \sigma_n^2 I]^{-1} y$$
$$\sigma_*^2 = K(x_*, x_*) - K(x_*, X) [K(X, X) + \sigma_n^2 I]^{-1} K(X, x_*)$$

### 2.2 采集函数

采集函数 $\alpha(x)$ 用于平衡探索（exploration）和开发（exploitation）。

#### 期望改进（Expected Improvement, EI）

$$EI(x) = E[\max(f(x) - f_{best}, 0)]$$

$$= (\mu(x) - f_{best} - \xi) \Phi(Z) + \sigma(x) \phi(Z)$$

其中：
$$Z = \frac{\mu(x) - f_{best} - \xi}{\sigma(x)}$$

- $\xi \geq 0$：探索参数，越大越倾向于探索
- $\Phi$：标准正态分布 CDF
- $\phi$：标准正态分布 PDF

**性质**：
- 在 $f_{best}$ 附近值较大（开发）
- 在不确定性大的区域值较大（探索）
- 可微，便于优化

#### 置信上界（Upper Confidence Bound, UCB）

$$UCB(x) = \mu(x) + \kappa \sigma(x)$$

- $\kappa > 0$：探索参数
- 简单直观
- 可以证明有理论保证

**变体**：
- 随时间衰减的 $\kappa$：$\kappa_t = \kappa_0 \sqrt{\frac{\log t}{t}}$

#### 概率改进（Probability of Improvement, PI）

$$PI(x) = P(f(x) > f_{best} + \xi) = \Phi\left(\frac{\mu(x) - f_{best} - \xi}{\sigma(x)}\right)$$

- 最简单的采集函数
- 只考虑是否改进，不考虑改进幅度
- 可能过于保守

#### Thompson 采样

从后验分布中采样函数 $f^{(i)} \sim p(f | \mathcal{D})$，选择：

$$x_{next} = \arg\max_x f^{(i)}(x)$$

- 简单直观
- 有理论保证
- 需要能够从后验采样

### 2.3 优化循环

贝叶斯优化的标准流程：

```
输入: 目标函数 f, 搜索空间 X, 初始点数 n₀, 迭代次数 T
输出: 最优点 x*

1. 初始化: 使用拉丁超立方采样选择 n₀ 个初始点
   D ← {(x_i, f(x_i))}_{i=1}^{n₀}

2. 循环 t = 1, 2, ..., T:
   a. 拟合高斯过程: GP ← fit(D)
   b. 优化采集函数: x_t ← argmax_x α(x; GP)
   c. 评估目标函数: y_t ← f(x_t)
   d. 更新数据集: D ← D ∪ {(x_t, y_t)}

3. 返回 x* = argmax_{(x,y)∈D} y
```

## 3. 数值稳定性

### 3.1 核矩阵计算

核矩阵 $K$ 必须是对称正定的。数值问题可能出现在：

1. **条件数过大**
   - 解决方案：添加小的对角项 $K + \epsilon I$

2. **Cholesky 分解失败**
   - 解决方案：使用数值稳定的分解方法
   - 或使用 QR 分解

3. **浮点精度**
   - 使用双精度浮点数
   - 避免数值下溢

### 3.2 采集函数优化

采集函数可能有多个局部最优，需要：

1. **多起点优化**
2. **全局搜索策略**
3. **处理边界**

## 4. 扩展方向

### 4.1 多目标优化

同时优化多个目标函数：
- ParEGO
- Expected Hypervolume Improvement (EHVI)

### 4.2 约束优化

带约束的优化问题：
- Constrained Expected Improvement

### 4.3 高维优化

维度 > 20 的问题：
- Additive GP
- Random Embedding
- Trust Regions

### 4.4 多保真度优化

利用不同精度的评估：
- Multi-fidelity GP
- Knowledge Gradient

### 4.5 并行评估

同时评估多个点：
- Batch Bayesian Optimization
- Local Penalization

## 5. 参考文献

1. Shahriari, B., et al. (2016). "Taking the Human Out of the Loop: A Review of Bayesian Optimization." *Proceedings of the IEEE*, 104(1), 148-175.

2. Rasmussen, C. E., & Williams, C. K. (2006). *Gaussian Processes for Machine Learning*. MIT Press.

3. Brochu, E., Cora, V. M., & De Freitas, N. (2010). "A Tutorial on Bayesian Optimization of Expensive Cost Functions."

4. Snoek, J., Larochelle, H., & Adams, R. P. (2012). "Practical Bayesian Optimization of Machine Learning Algorithms." *NeurIPS*.

5. Jones, D. R., Schonlau, M., & Welch, W. J. (1998). "Efficient Global Optimization of Expensive Black-Box Functions." *Journal of Global Optimization*.

6. Srinivas, N., et al. (2009). "Gaussian Process Optimization in the Bandit Setting: No Regret and Experimental Design." *ICML*.
