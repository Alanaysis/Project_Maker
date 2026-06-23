# Actor-Critic 算法研究

## 1. 算法概述

Actor-Critic 是一种结合了策略梯度（Policy Gradient）和价值函数（Value Function）的强化学习算法。它由两个组件组成：

- **Actor（演员）**：学习策略 π(a|s)，决定在给定状态下采取什么动作
- **Critic（评论家）**：学习价值函数 V(s)，评估状态的好坏

## 2. 核心思想

### 2.1 策略梯度基础

策略梯度方法直接优化策略参数 θ，目标是最大化期望回报：

```
J(θ) = E[Σ γ^t * r_t]
```

策略梯度定理给出梯度：

```
∇J(θ) = E[∇log π(a|s; θ) * A(s, a)]
```

其中 A(s, a) 是优势函数。

### 2.2 优势函数

优势函数衡量在状态 s 下采取动作 a 相对于平均水平的优势：

```
A(s, a) = Q(s, a) - V(s)
```

在 Actor-Critic 中，我们使用 TD 误差来估计优势：

```
A(s_t, a_t) ≈ r_t + γ * V(s_{t+1}) - V(s_t)
```

### 2.3 Actor-Critic 更新规则

**Actor 更新**（策略梯度）：
```
θ ← θ + α * ∇log π(a|s; θ) * A(s, a)
```

**Critic 更新**（TD 学习）：
```
w ← w + β * (r + γ * V(s'; w) - V(s; w)) * ∇V(s; w)
```

## 3. 算法变体

### 3.1 A2C (Advantage Actor-Critic)

A2C 是 Actor-Critic 的同步版本：
- 使用多个环境并行收集数据
- 同步更新所有环境的梯度
- 更稳定，易于实现

### 3.2 A3C (Asynchronous Advantage Actor-Critic)

A3C 是 Actor-Critic 的异步版本：
- 多个 worker 在不同环境异步训练
- 每个 worker 独立更新全局网络
- 更高效，但实现更复杂

### 3.3 GAE (Generalized Advantage Estimation)

GAE 通过引入 λ 参数平衡偏差和方差：

```
A_t^GAE = Σ_{l=0}^{∞} (γλ)^l * δ_{t+l}
```

其中 δ_t = r_t + γ * V(s_{t+1}) - V(s_t)

## 4. 与 CartPole 环境

### 4.1 环境描述

CartPole 是经典的控制问题：
- **状态空间**：4 维连续空间 [车位置, 车速度, 杆角度, 杆角速度]
- **动作空间**：2 个离散动作 [向左推, 向右推]
- **奖励**：每步 +1，最大 500 步
- **终止条件**：杆倾斜 >15° 或车超出边界

### 4.2 解决标准

在 CartPole-v1 中，连续 100 个回合平均得分 ≥ 475 即为解决。

## 5. 参考资料

1. Sutton, R. S., & Barto, A. G. (2018). Reinforcement Learning: An Introduction.
2. Mnih, V., et al. (2016). Asynchronous Methods for Deep Reinforcement Learning.
3. Schulman, J., et al. (2016). High-Dimensional Continuous Control Using Generalized Advantage Estimation.
