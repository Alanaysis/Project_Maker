# DQN 研究文档

## 1. 背景与动机

### 1.1 强化学习概述
强化学习 (Reinforcement Learning, RL) 是机器学习的一个分支，智能体通过与环境交互来学习最优策略。

### 1.2 从 Q-Learning 到 DQN
- **Q-Learning**: 表格型方法，维护 Q(s,a) 表格
- **Deep Q-Network**: 使用神经网络近似 Q 函数

## 2. 核心算法

### 2.1 DQN (2015)
**核心思想**:
- 使用深度神经网络作为函数逼近器
- 经验回放 (Experience Replay) 打破数据相关性
- 目标网络 (Target Network) 稳定训练

**损失函数**:
```
L(θ) = E[(r + γ max_a' Q(s', a'; θ⁻) - Q(s, a; θ))²]
```

**关键创新**:
1. 经验回放: 存储经验 (s, a, r, s') 到缓冲区，随机采样
2. 目标网络: 使用固定参数 θ⁻ 计算目标值，定期更新

### 2.2 Double DQN (2016)
**问题**: 标准 DQN 存在过估计 (overestimation) 问题

**解决方案**:
- 分离动作选择和动作评估
- 使用在线网络选择动作，目标网络评估动作

**目标计算**:
```
y = r + γ Q(s', argmax_a' Q(s', a'; θ); θ⁻)
```

### 2.3 Dueling DQN (2016)
**核心思想**:
- 将 Q 函数分解为状态价值和动作优势
- Q(s,a) = V(s) + A(s,a)

**网络架构**:
```
输入层 → 共享层 → 价值流 → V(s)
                   → 优势流 → A(s,a)
Q(s,a) = V(s) + A(s,a) - mean(A(s,a))
```

**优势**:
- 更好的状态价值估计
- 在动作空间大的场景更有效

### 2.4 Prioritized Experience Replay (2016)
**核心思想**:
- 重要经验应该被更频繁地回放
- 使用 TD 误差作为优先级

**两种方式**:
1. **Proportional**: 采样概率与优先级成正比
2. **Rank-based**: 采样概率与排名成正比

**重要性采样 (Importance Sampling)**:
```
w_i = (1/(N * P(i)))^β
```

## 3. 环境分析

### 3.1 CartPole
- **状态空间**: 4 维连续 (位置, 速度, 角度, 角速度)
- **动作空间**: 2 个离散动作 (左推, 右推)
- **奖励**: 每步 +1，最大 200 步
- **目标**: 保持杆子平衡

### 3.2 Atari 游戏
- **状态空间**: 210x160x3 像素图像
- **动作空间**: 离散动作 (通常 4-18 个)
- **预处理**:
  - 灰度化
  - 下采样 (84x84)
  - 帧堆叠 (4 帧)

## 4. 相关工作

### 4.1 Rainbow DQN (2017)
结合多种 DQN 改进：
- Double DQN
- Dueling DQN
- Prioritized Experience Replay
- Multi-step Learning
- Distributional RL
- Noisy Nets

### 4.2 Distributional RL
- 学习 Q 值的分布而非期望值
- C51, QR-DQN 等算法

### 4.3 Model-based RL
- 学习环境模型
- 使用模型进行规划

## 5. 研究问题

### 5.1 关键问题
1. 如何稳定 DQN 训练？
2. 如何减少过估计？
3. 如何提高样本效率？
4. 如何处理高维状态空间？

### 5.2 挑战
1. 训练不稳定
2. 样本效率低
3. 超参数敏感
4. 探索-利用平衡

## 6. 参考文献

1. Mnih, V., et al. (2015). Human-level control through deep reinforcement learning. Nature, 518(7540), 529-533.
2. Van Hasselt, H., Guez, A., & Silver, D. (2016). Deep Reinforcement Learning with Double Q-learning. AAAI.
3. Wang, Z., et al. (2016). Dueling Network Architectures for Deep Reinforcement Learning. ICML.
4. Schaul, T., et al. (2016). Prioritized Experience Replay. ICLR.
5. Hessel, M., et al. (2018). Rainbow: Combining Improvements in Deep Reinforcement Learning. AAAI.
