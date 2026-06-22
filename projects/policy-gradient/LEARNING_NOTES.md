# Policy Gradient 学习笔记

## 学习目标

1. 理解策略梯度的基本原理
2. 掌握 REINFORCE 算法
3. 学会基线减法技术

## 核心概念

### 策略梯度 vs 价值方法

| 特性 | 策略梯度 | 价值方法 |
|------|----------|----------|
| 优化目标 | 直接优化策略 π(a\|s) | 估计价值函数 Q(s,a) 或 V(s) |
| 动作空间 | 连续和离散 | 通常离散 |
| 收敛性 | 保证收敛到局部最优 | 可能不稳定 |
| 探索 | 自然探索（随机策略） | 需要探索策略（如 ε-greedy） |
| 方差 | 高方差 | 低方差 |

### 策略梯度定理

策略梯度定理是策略梯度方法的理论基础：

```
∇J(θ) = E_τ~πθ [∑_{t=0}^{T} ∇log π(a_t|s_t; θ) * G_t]
```

**直观理解**：
- 增大获得高回报的动作的概率
- 减小获得低回报的动作的概率
- 用回报 G_t 来加权每个动作的重要性

### REINFORCE 算法

REINFORCE 是最基本的策略梯度算法：

1. **采样**：从当前策略采样一条轨迹
2. **计算回报**：计算每个时间步的折扣回报 G_t
3. **估计梯度**：使用蒙特卡洛估计策略梯度
4. **更新参数**：θ ← θ + α * ∇J(θ)

**优点**：
- 无偏估计
- 可以处理连续动作空间
- 可以学习随机策略

**缺点**：
- 高方差
- 样本效率低
- 只能用于 episodic 任务

### 基线减法

基线减法是减少策略梯度方差的重要技术：

```
∇J(θ) = E[∑_t ∇log π(a_t|s_t; θ) * (G_t - b(s_t))]
```

**为什么基线不引入偏差？**

因为基线 b(s) 不依赖于动作 a，所以：

```
E[∇log π(a|s; θ) * b(s)] = b(s) * E[∇log π(a|s; θ)]
                           = b(s) * ∑_a π(a|s; θ) * ∇log π(a|s; θ)
                           = b(s) * ∑_a ∇π(a|s; θ)
                           = b(s) * ∇∑_a π(a|s; θ)
                           = b(s) * ∇1
                           = 0
```

**常用基线**：
1. **常数基线**：b = E[G_t]（回报的期望）
2. **状态依赖基线**：b = V(s_t)（状态价值函数）
3. **移动平均基线**：b = running_mean(G_t)

## 实现要点

### 1. 对数概率

使用对数概率而非概率：

```python
# 正确
log_probs = torch.log(probs)

# 错误
probs = torch.softmax(logits, dim=-1)
loss = -(probs * returns).mean()
```

**原因**：
- 避免数值下溢
- 便于计算梯度
- 与 KL 散度自然联系

### 2. 梯度裁剪

```python
if self.max_grad_norm is not None:
    torch.nn.utils.clip_grad_norm_(
        self.policy.parameters(),
        self.max_grad_norm
    )
```

**原因**：
- 防止梯度爆炸
- 稳定训练过程

### 3. 优势归一化

```python
advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
```

**原因**：
- 使不同 episode 的梯度量级一致
- 加速训练收敛

### 4. 熵正则化

```python
entropy = -sum(p * log(p))
loss = policy_loss - entropy_coef * entropy
```

**原因**：
- 防止策略过早收敛到确定性策略
- 鼓励探索

## 训练技巧

### 1. 学习率选择

- 从小学习率开始（如 0.001）
- 观察训练曲线
- 如果学习太慢，可以增大学习率
- 如果训练不稳定，可以减小学习率

### 2. 网络结构

- 对于简单任务，使用小网络
- 对于复杂任务，使用大网络
- 避免过拟合

### 3. 奖励设计

- 奖励应该清晰地反映目标
- 避免稀疏奖励
- 可以使用奖励塑形

### 4. 折扣因子选择

- γ = 0.99：长期回报
- γ = 0.9：中期回报
- γ = 0.5：短期回报

## 常见问题

### Q1: 为什么 REINFORCE 方差大？

**原因**：
- 使用蒙特卡洛估计
- 每个 episode 都是独立采样
- 回报的随机性大

**解决方案**：
- 使用基线减法
- 使用优势函数
- 使用更高级的算法（如 PPO）

### Q2: 如何判断训练是否成功？

**指标**：
- 平均回报是否上升
- 是否达到环境的目标分数
- 训练曲线是否稳定

### Q3: 什么时候使用策略梯度？

**适用场景**：
- 连续动作空间
- 需要随机策略
- 动作空间大

**不适用场景**：
- 离散动作空间且较小
- 需要确定性策略
- 样本效率要求高

## 学习资源

### 书籍

- [Sutton & Barto - Reinforcement Learning: An Introduction](http://incompleteideas.net/book/the-book-2nd.html)
- [Deep Reinforcement Learning Hands-On](https://www.packtpub.com/product/deep-reinforcement-learning-hands-on-second-edition/9781838826994)

### 论文

- [Simple Statistical Gradient-Following Algorithms for Connectionist Reinforcement Learning](https://link.springer.com/article/10.1007/BF00992696)
- [Policy Gradient Methods for Reinforcement Learning with Function Approximation](https://proceedings.neurips.cc/paper/1999/file/464d828b85b0bed98e80ade0a5c43b0f-Paper.pdf)

### 在线资源

- [OpenAI Spinning Up](https://spinningup.openai.com/)
- [Policy Gradient Algorithms (Lil'Log)](https://lilianweng.github.io/posts/2018-04-08-policy-gradient/)

## 学习心得

### 关键理解

1. **策略梯度直接优化策略**：与价值方法不同，策略梯度直接参数化策略并优化
2. **基线减法减少方差**：基线不改变期望，但可以显著减少方差
3. **REINFORCE 是蒙特卡洛方法**：需要完整的轨迹才能更新

### 困难点

1. **高方差问题**：REINFORCE 的高方差是主要挑战
2. **样本效率低**：每个 episode 只能使用一次
3. **超参数敏感**：学习率、网络结构等需要仔细调优

### 改进方向

1. **Actor-Critic**：结合价值方法减少方差
2. **PPO**：使用裁剪目标函数提高稳定性
3. **A3C**：使用异步更新提高效率
