# DQN 学习笔记

## 项目概述

本项目实现了深度 Q 网络（DQN）算法，用于解决强化学习问题。通过实现 DQN，我深入理解了强化学习的核心概念和深度学习的应用。

## 学习目标

1. **理解 DQN 原理**: 掌握 Q-learning 与深度网络的结合
2. **经验回放**: 理解为什么需要以及如何实现经验回放
3. **目标网络**: 理解目标网络如何稳定训练过程

## 核心概念

### 1. 强化学习基础

强化学习是机器学习的一个分支，智能体通过与环境交互来学习最优策略。

**核心要素：**
- **状态 (State)**: 环境的描述
- **动作 (Action)**: 智能体可以执行的操作
- **奖励 (Reward)**: 环境对动作的反馈
- **策略 (Policy)**: 从状态到动作的映射

**学习过程：**
```
智能体观察状态 → 选择动作 → 环境返回奖励和新状态 → 更新策略
```

### 2. Q-Learning 算法

Q-Learning 是一种无模型的强化学习算法，通过学习 Q 值函数来找到最优策略。

**Q 值函数：**
```
Q(s, a) = E[Σ γ^t * r_t | s_0=s, a_0=a]
```

**更新规则：**
```
Q(s, a) ← Q(s, a) + α[r + γ max_a' Q(s', a') - Q(s, a)]
```

**特点：**
- 离策略（Off-policy）：行为策略和目标策略可以不同
- 使用 ε-greedy 策略进行探索

### 3. 深度 Q 网络 (DQN)

DQN 使用深度神经网络近似 Q 值函数，解决了传统 Q-Learning 无法处理高维状态空间的问题。

**核心创新：**

#### 3.1 经验回放 (Experience Replay)

**问题：**
- 相邻样本高度相关
- 样本分布随策略变化而变化

**解决方案：**
- 存储经验到缓冲区
- 随机采样打破相关性
- 复用数据提高效率

**实现要点：**
- 使用循环缓冲区（deque）
- 存储完整经验 (state, action, reward, next_state, done)
- 随机均匀采样

#### 3.2 目标网络 (Target Network)

**问题：**
- Q 值更新不稳定
- 容易发散

**解决方案：**
- 使用目标网络计算目标 Q 值
- 定期更新目标网络参数

**实现要点：**
- 复制策略网络作为目标网络
- 定期同步参数
- 使用 `torch.no_grad()` 避免计算梯度

### 4. ε-Greedy 策略

ε-greedy 策略平衡探索和利用：

**策略：**
- 以概率 ε 随机选择动作（探索）
- 以概率 1-ε 选择 Q 值最大的动作（利用）

**衰减：**
- 初始 ε 较大，鼓励探索
- 随训练进行，ε 逐渐减小
- 最终 ε 趋近于 0，主要利用

## 实现细节

### 1. 神经网络架构

```python
class DQN(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)

    def forward(self, state):
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        return self.fc3(x)
```

**设计决策：**
- 2 层全连接网络
- ReLU 激活函数
- 隐藏层维度 128

### 2. 经验回放缓冲区

```python
class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)
```

**设计决策：**
- 使用 deque 实现循环缓冲区
- 容量 10000
- 随机均匀采样

### 3. DQN 代理

```python
class DQNAgent:
    def __init__(self, ...):
        self.policy_net = DQN(...)  # 当前网络
        self.target_net = DQN(...)  # 目标网络
        self.replay_buffer = ReplayBuffer(...)
        self.optimizer = Adam(...)

    def train(self):
        # 采样批次
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(...)

        # 计算当前 Q 值
        q_values = self.policy_net(states)
        q_values = q_values.gather(1, actions)

        # 计算目标 Q 值
        with torch.no_grad():
            target_q = self.target_net(next_states)
            target_values = rewards + gamma * target_q.max() * (1 - dones)

        # 计算损失
        loss = nn.MSELoss()(q_values, target_values)

        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # 更新目标网络
        if step % target_update_freq == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
```

**设计决策：**
- 使用 Adam 优化器
- 使用 MSE 损失
- 定期更新目标网络

## 训练过程

### 1. 环境设置

```python
env = gym.make("CartPole-v1")
state_dim = env.observation_space.shape[0]  # 4
action_dim = env.action_space.n  # 2
```

### 2. 训练循环

```python
for episode in range(num_episodes):
    state = env.reset()

    for step in range(max_steps):
        # 选择动作
        action = agent.select_action(state)

        # 执行动作
        next_state, reward, done, _ = env.step(action)

        # 存储经验
        agent.store_experience(state, action, reward, next_state, done)

        # 训练
        loss = agent.train()

        state = next_state
        if done:
            break
```

### 3. 训练结果

- **训练轮数**: 300-500 轮
- **收敛奖励**: 平均 475+ 奖励
- **训练时间**: 约 5-10 分钟（CPU）

## 关键问题与解决

### 1. 训练不稳定

**问题：**
- 奖励波动大
- 损失不稳定

**解决：**
- 使用目标网络
- 增大缓冲区容量
- 减小学习率
- 增加目标网络更新频率

### 2. 过估计问题

**问题：**
- Q 值被高估
- 策略次优

**解决：**
- 使用 Double DQN
- 使用优先经验回放
- 使用 Dueling DQN

### 3. 探索不足

**问题：**
- 过早收敛到次优策略
- 无法找到最优策略

**解决：**
- 增大初始探索率
- 减慢探索率衰减
- 使用噪声网络

## 学习收获

### 1. 强化学习理解

- 理解了强化学习的基本框架
- 掌握了 Q-learning 算法
- 理解了探索与利用的平衡

### 2. 深度学习应用

- 学会了使用 PyTorch 构建神经网络
- 理解了梯度下降和反向传播
- 掌握了模型训练和评估

### 3. 工程实践

- 学会了模块化设计
- 掌握了单元测试
- 理解了代码重构

### 4. 问题解决

- 学会了调试技巧
- 掌握了性能优化
- 理解了常见问题的解决方案

## 扩展方向

### 1. Double DQN

使用当前网络选择动作，目标网络评估动作，减少过估计。

### 2. Dueling DQN

将 Q 值分解为状态价值和动作优势，提高学习效率。

### 3. 优先经验回放

根据 TD 误差优先采样重要经验，提高学习效率。

### 4. Rainbow DQN

结合多种改进技术，提高性能。

### 5. 连续动作空间

使用 DDPG、SAC 等算法处理连续动作空间。

## 参考资源

### 论文

1. Mnih, V., et al. (2015). Human-level control through deep reinforcement learning. Nature.
2. Van Hasselt, H., et al. (2016). Deep Reinforcement Learning with Double Q-learning. AAAI.
3. Schaul, T., et al. (2016). Prioritized Experience Replay. ICLR.

### 教程

1. OpenAI Spinning Up: https://spinningup.openai.com/
2. PyTorch 官方教程: https://pytorch.org/tutorials/
3. Gymnasium 文档: https://gymnasium.farama.org/

### 代码

1. OpenAI Baselines: https://github.com/openai/baselines
2. Stable Baselines3: https://github.com/DLR-RM/stable-baselines3
3. CleanRL: https://github.com/vwxyzjn/cleanrl

## 总结

通过实现 DQN 项目，我深入理解了强化学习的核心概念和深度学习的应用。DQN 是深度强化学习的基础算法，掌握它对于理解更复杂的算法非常重要。

**关键收获：**
1. 理解了强化学习的基本框架
2. 掌握了 DQN 的核心创新
3. 学会了使用 PyTorch 实现神经网络
4. 理解了训练过程中的常见问题和解决方案

**下一步：**
1. 实现 Double DQN
2. 尝试更复杂的环境
3. 学习其他强化学习算法
4. 探索连续动作空间
