# DQN - 深度 Q 网络

> 实现深度 Q 网络（Deep Q-Network）强化学习算法

## 项目概述

本项目实现了深度 Q 网络（DQN）算法，用于解决强化学习问题。DQN 结合了 Q-learning 和深度神经网络，能够处理高维状态空间的问题。

## 核心特性

- **DQN 算法**: 实现标准 DQN 和 Double DQN
- **经验回放**: 使用循环缓冲区存储和采样经验
- **目标网络**: 稳定训练的目标网络机制
- **CartPole 环境**: 在 OpenAI Gym CartPole-v1 上训练

## 技术栈

- **语言**: Python 3.8+
- **深度学习**: PyTorch
- **强化学习环境**: OpenAI Gym

## 项目结构

```
dqn/
├── src/
│   ├── __init__.py
│   ├── dqn.py            # DQN 神经网络模型
│   ├── replay_buffer.py   # 经验回放缓冲区
│   ├── agent.py           # DQN 代理实现
│   └── train.py           # 训练脚本
├── tests/
│   └── test_dqn.py        # 单元测试
├── docs/
│   ├── 01-RESEARCH.md     # 研究笔记
│   ├── 02-ARCHITECTURE.md # 架构设计
│   ├── 03-IMPLEMENTATION.md # 实现细节
│   ├── 04-TESTING.md      # 测试说明
│   └── 05-DEVELOPMENT.md  # 开发指南
├── README.md
└── LEARNING_NOTES.md
```

## 快速开始

### 安装依赖

```bash
pip install torch gymnasium numpy matplotlib
```

### 运行训练

```bash
cd projects/dqn
python src/train.py
```

### 运行测试

```bash
cd projects/dqn
python -m pytest tests/
```

## 学习目标

1. **理解 DQN 原理**: 掌握 Q-learning 与深度网络的结合
2. **经验回放**: 理解为什么需要以及如何实现经验回放
3. **目标网络**: 理解目标网络如何稳定训练过程

## 核心算法

### DQN 更新规则

```
L(θ) = E[(r + γ max_a' Q(s', a'; θ⁻) - Q(s, a; θ))²]
```

其中：
- θ: 当前网络参数
- θ⁻: 目标网络参数
- γ: 折扣因子
- r: 即时奖励

## 参考文献

1. Mnih, V., et al. (2015). Human-level control through deep reinforcement learning. Nature.
2. Van Hasselt, H., et al. (2016). Deep Reinforcement Learning with Double Q-learning. AAAI.
