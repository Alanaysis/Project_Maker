# DQN - Deep Q-Network

强化学习项目：实现 DQN 及其变体算法

## 项目概述

本项目实现了 Deep Q-Network (DQN) 及其多种高级变体，用于解决强化学习问题。支持 CartPole 和简化的 Atari 游戏环境。

## 核心特性

### 1. DQN 基础实现
- **Q 网络**: 使用深度神经网络近似 Q 函数
- **目标网络**: 稳定训练的目标网络机制
- **经验回放**: 打破数据相关性的经验存储机制

### 2. Double DQN
- 解决标准 DQN 的过估计问题
- 分离动作选择和动作评估

### 3. Dueling DQN
- 价值流 (Value Stream): 估计状态价值 V(s)
- 优势流 (Advantage Stream): 估计动作优势 A(s,a)
- 架构改进：Q(s,a) = V(s) + A(s,a)

### 4. Prioritized Experience Replay
- 基于 TD 误差的优先级采样
- 重要经验被更频繁地回放
- 支持优先级比例 (proportional) 和排名 (rank-based) 两种方式

### 5. 支持环境
- **CartPole**: 经典控制问题
- **Atari 游戏**: 简化的 Atari 环境 (Pong, Breakout 等)

### 6. 可视化工具
- 奖励曲线绘制
- Q 值变化监控
- 训练进度实时显示

## 目录结构

```
dqn/
├── src/
│   ├── __init__.py
│   ├── dqn.py                    # DQN 核心实现
│   ├── double_dqn.py             # Double DQN 变体
│   ├── dueling_dqn.py            # Dueling DQN 变体
│   ├── replay_buffer.py          # 基础经验回放缓冲区
│   ├── prioritized_replay_buffer.py  # 优先经验回放缓冲区
│   ├── env_wrapper.py            # 环境封装器
│   ├── agent.py                  # DQN Agent
│   ├── train.py                  # 训练脚本
│   └── visualization.py          # 可视化工具
├── tests/
│   ├── __init__.py
│   ├── test_dqn.py
│   ├── test_replay_buffer.py
│   └── test_agent.py
├── examples/
│   ├── cartpole_train.py
│   └── atari_train.py
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── requirements.txt
└── README.md
```

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### CartPole 训练示例
```bash
python examples/cartpole_train.py --algorithm double_dqn --episodes 500
```

### Atari 训练示例
```bash
python examples/atari_train.py --game Pong --algorithm dueling_dqn --episodes 1000
```

## 算法对比

| 算法 | 优势 | 适用场景 |
|------|------|----------|
| DQN | 基础算法，简单易懂 | 入门学习 |
| Double DQN | 减少过估计 | 需要稳定训练 |
| Dueling DQN | 更好的状态价值估计 | 状态空间大 |
| PER | 提高样本效率 | 训练数据有限 |

## 参考文献

1. Mnih, V., et al. (2015). Human-level control through deep reinforcement learning. Nature.
2. Van Hasselt, H., et al. (2016). Deep Reinforcement Learning with Double Q-learning. AAAI.
3. Wang, Z., et al. (2016). Dueling Network Architectures for Deep Reinforcement Learning. ICML.
4. Schaul, T., et al. (2016). Prioritized Experience Replay. ICLR.

## 许可证

MIT License
