# 01 - 研究笔记

## DQN 核心概念

### 1. 强化学习基础

强化学习是机器学习的一个分支，智能体通过与环境交互来学习最优策略。

**核心要素：**
- **状态 (State)**: 环境的描述
- **动作 (Action)**: 智能体可以执行的操作
- **奖励 (Reward)**: 环境对动作的反馈
- **策略 (Policy)**: 从状态到动作的映射

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

**实现：**
```python
class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)
```

#### 3.2 目标网络 (Target Network)

**问题：**
- Q 值更新不稳定
- 容易发散

**解决方案：**
- 使用目标网络计算目标 Q 值
- 定期更新目标网络参数

**实现：**
```python
# 计算目标 Q 值
with torch.no_grad():
    target_q = target_net(next_state)
    target_value = reward + gamma * target_q.max()

# 定期更新目标网络
if step % target_update_freq == 0:
    target_net.load_state_dict(policy_net.state_dict())
```

### 4. Double DQN

**问题：**
- 标准 DQN 会高估 Q 值
- max 操作导致过估计

**解决方案：**
- 使用当前网络选择动作
- 使用目标网络评估动作

**更新规则：**
```
target = r + γ * Q_target(s', argmax_a' Q_policy(s', a'))
```

## CartPole 环境

### 环境描述

CartPole 是一个经典的控制问题：
- **状态空间**: 4 维连续空间
  - 购物车位置
  - 购物车速度
  - 杆子角度
  - 杆子角速度
- **动作空间**: 2 个离散动作
  - 0: 向左推
  - 1: 向右推
- **奖励**: 每步 +1，直到杆子倒下或购物车出界
- **结束条件**:
  - 杆子角度 > 12°
  - 购物车位置 > 2.4
  - 步数 > 500

### 训练目标

- 解决环境：平均奖励 ≥ 475（500 步中的 475 步）
- 训练轮数：通常 300-500 轮

## 参考文献

1. **Mnih, V., et al. (2015)**. Human-level control through deep reinforcement learning. Nature, 518(7540), 529-533.

2. **Van Hasselt, H., et al. (2016)**. Deep Reinforcement Learning with Double Q-learning. AAAI.

3. **Schaul, T., et al. (2016)**. Prioritized Experience Replay. ICLR.

4. **Wang, Z., et al. (2016)**. Dueling Network Architectures for Deep Reinforcement Learning. ICML.
