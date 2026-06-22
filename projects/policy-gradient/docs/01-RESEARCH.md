# 策略梯度研究笔记

## 核心概念

### 什么是策略梯度？

策略梯度（Policy Gradient）是一类直接优化策略的强化学习算法。与基于价值的方法（如 Q-learning）不同，策略梯度方法直接参数化策略 π(a|s; θ)，并通过梯度上升来最大化期望回报。

### 策略梯度定理

策略梯度定理是策略梯度方法的理论基础：

```
∇J(θ) = E_τ~πθ [∑_{t=0}^{T} ∇log π(a_t|s_t; θ) * G_t]
```

其中：
- J(θ) 是策略的期望回报
- τ 是轨迹（trajectory）
- G_t 是从时间步 t 开始的累积回报（return）
- π(a_t|s_t; θ) 是策略在状态 s_t 下选择动作 a_t 的概率

### REINFORCE 算法

REINFORCE（REward Increment = Nonnegative Factor × Offset Reinforcement × Characteristic Eligibility）是最基本的策略梯度算法。

**算法流程：**
1. 采样一条完整的轨迹 τ = (s_0, a_0, r_0, s_1, a_1, r_1, ...)
2. 计算每个时间步的回报 G_t = ∑_{k=t}^{T} γ^{k-t} * r_k
3. 更新策略参数：θ ← θ + α * ∑_t ∇log π(a_t|s_t; θ) * G_t

**优点：**
- 无偏估计
- 可以处理连续动作空间
- 可以学习随机策略

**缺点：**
- 高方差
- 样本效率低
- 只能用于 episodic 任务

### 基线减法（Baseline Subtraction）

基线减法是减少策略梯度方差的重要技术。

**原理：**
在策略梯度估计中减去一个基线 b(s)：

```
∇J(θ) = E[∑_t ∇log π(a_t|s_t; θ) * (G_t - b(s_t))]
```

**关键性质：**
- 基线不依赖于动作，所以不会引入偏差
- 但可以显著减少方差

**常用基线：**
1. **常数基线**：b = E[G_t]（回报的期望）
2. **状态依赖基线**：b = V(s_t)（状态价值函数）
3. **移动平均基线**：b = running_mean(G_t)

### 优势函数（Advantage Function）

优势函数定义为：

```
A(s, a) = Q(s, a) - V(s)
```

在策略梯度中，我们可以用回报来估计优势：

```
A_t ≈ G_t - V(s_t)
```

使用优势函数的好处：
- 自动减去基线
- 估计哪个动作比平均水平更好

## 与价值方法的比较

| 特性 | 策略梯度 | 价值方法 |
|------|----------|----------|
| 优化目标 | 直接优化策略 | 估计价值函数 |
| 动作空间 | 连续和离散 | 通常离散 |
| 收敛性 | 保证收敛到局部最优 | 可能不稳定 |
| 探索 | 自然探索 | 需要探索策略 |
| 方差 | 高方差 | 低方差 |
| 偏差 | 无偏（REINFORCE） | 可能有偏 |

## 学习资源

- [Sutton & Barto - Reinforcement Learning: An Introduction](http://incompleteideas.net/book/the-book-2nd.html)
- [OpenAI Spinning Up - Policy Gradient](https://spinningup.openai.com/en/latest/algorithms/vpg.html)
- [Policy Gradient Algorithms (Lil'Log)](https://lilianweng.github.io/posts/2018-04-08-policy-gradient/)
