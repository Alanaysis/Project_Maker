# Actor-Critic 学习笔记

## 核心概念

### 1. Actor-Critic 架构

Actor-Critic 是一种结合策略梯度和价值函数的强化学习方法：

- **Actor（演员）**：学习策略 π(a|s)，决定采取什么动作
- **Critic（评论家）**：学习价值函数 V(s)，评估状态好坏

### 2. 核心循环

```
状态 → Actor → 动作 → Critic → 优势 → 更新
```

1. **状态**：环境当前状态 s_t
2. **Actor**：根据策略 π(a|s) 选择动作 a_t
3. **动作**：执行动作，获得奖励 r_t 和新状态 s_{t+1}
4. **Critic**：计算状态价值 V(s_t) 和 V(s_{t+1})
5. **优势**：计算优势函数 A_t = r_t + γV(s_{t+1}) - V(s_t)
6. **更新**：使用优势更新 Actor 和 Critic

### 3. 优势函数

优势函数 A(s, a) 衡量动作 a 相对于平均水平的优势：

```
A(s, a) = Q(s, a) - V(s)
```

在实际实现中，使用 TD 误差近似：

```
A_t ≈ r_t + γ * V(s_{t+1}) - V(s_t)
```

**为什么需要优势函数？**
- 减少方差：直接使用回报 G_t 方差大
- 提供基线：减去 V(s) 作为基线，降低方差
- 保持无偏：E[A] = 0，梯度估计仍然无偏

## 关键实现细节

### 1. 网络设计

**Actor 网络**：
- 输入：状态向量
- 输出：动作 logits（未归一化的概率）
- 使用 softmax 转换为概率

**Critic 网络**：
- 输入：状态向量
- 输出：标量价值估计

### 2. 损失函数

**Actor 损失**：
```python
actor_loss = -log_prob * advantage.detach()
```
- 使用负号因为要最大化回报
- detach() 防止梯度回传到 Critic

**Critic 损失**：
```python
critic_loss = MSE(predicted_value, target_return)
```

**熵正则化**：
```python
entropy_loss = -entropy.mean()
total_loss = actor_loss + entropy_coef * entropy_loss
```

### 3. 训练流程

```python
for episode in range(num_episodes):
    state = env.reset()

    # 收集数据
    for step in range(max_steps):
        action = agent.select_action(state)
        next_state, reward, done, _ = env.step(action)
        agent.store_reward(reward)
        state = next_state
        if done:
            break

    # 更新网络
    losses = agent.update()
```

## A2C vs A3C

### A2C (Advantage Actor-Critic)

- **同步**：所有环境同步收集数据，同步更新
- **优点**：实现简单，稳定
- **缺点**：可能受最慢环境限制

### A3C (Asynchronous Advantage Actor-Critic)

- **异步**：多个 worker 异步训练，独立更新全局网络
- **优点**：更高效，探索更多样
- **缺点**：实现复杂，可能有竞争条件

## GAE (Generalized Advantage Estimation)

GAE 通过 λ 参数平衡偏差和方差：

```
A_t^GAE = Σ_{l=0}^{∞} (γλ)^l * δ_{t+l}
```

其中 δ_t = r_t + γ * V(s_{t+1}) - V(s_t)

- **λ = 0**：A_t = δ_t（高偏差，低方差）
- **λ = 1**：A_t = G_t - V(s_t)（低偏差，高方差）
- **λ = 0.95**：常见选择，平衡偏差和方差

## CartPole 环境

### 环境描述

- **状态空间**：4 维连续 [位置, 速度, 角度, 角速度]
- **动作空间**：2 个离散 [左推, 右推]
- **奖励**：每步 +1
- **终止**：杆倾斜 >15° 或车超出边界

### 解决标准

连续 100 个回合平均得分 ≥ 475

## 常见问题

### Q1: 为什么 Actor 和 Critic 使用不同的学习率？

**A**：Critic 需要更快地拟合价值函数，为 Actor 提供准确的梯度估计。Actor 学习率较慢，确保策略更新稳定。

### Q2: 为什么需要熵正则化？

**A**：熵正则化鼓励探索，防止策略过早收敛到局部最优。没有熵正则化，策略可能快速收敛到次优策略。

### Q3: 为什么使用 advantage.detach()？

**A**：防止 Critic 的梯度通过 advantage 回传到 Actor。Actor 和 Critic 应该独立更新。

### Q4: 什么时候使用 GAE？

**A**：当训练不稳定或方差大时，使用 GAE（λ < 1.0）可以降低方差，但可能增加偏差。

## 学习资源

1. **书籍**：Sutton & Barto《Reinforcement Learning: An Introduction》
2. **课程**：David Silver's RL Course
3. **代码**：OpenAI Spinning Up
4. **论文**：Mnih et al. (2016) "Asynchronous Methods for Deep Reinforcement Learning"
