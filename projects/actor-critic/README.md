# Actor-Critic

实现 Actor-Critic 算法，用于强化学习任务。

## 项目概述

本项目实现了经典的 Actor-Critic 强化学习算法，包含：
- **Actor 网络**：策略网络，输出动作概率
- **Critic 网络**：价值网络，评估状态价值
- **优势函数**：结合 Actor 和 Critic 进行策略更新
- **CartPole 环境训练**：在 OpenAI Gym 的 CartPole 环境上训练和评估

## 核心循环

```
状态 → Actor → 动作 → Critic → 优势 → 更新
```

## 项目结构

```
actor-critic/
├── src/
│   └── actor_critic/
│       ├── agents/
│       │   ├── __init__.py
│       │   └── actor_critic_agent.py
│       ├── networks/
│       │   ├── __init__.py
│       │   ├── actor_network.py
│       │   └── critic_network.py
│       └── utils/
│           ├── __init__.py
│           └── advantages.py
├── tests/
│   ├── __init__.py
│   ├── test_actor_network.py
│   ├── test_critic_network.py
│   └── test_agent.py
├── scripts/
│   ├── train.py
│   └── evaluate.py
├── configs/
│   └── default.yaml
├── docs/
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── LEARNING_NOTES.md
├── requirements.txt
└── setup.py
```

## 安装

```bash
cd projects/actor-critic
pip install -e .
```

## 使用

### 训练

```bash
python scripts/train.py
```

### 评估

```bash
python scripts/evaluate.py
```

### 运行测试

```bash
pytest tests/
```

## 学习目标

- 理解 Actor-Critic 算法原理
- 掌握 A2C/A3C 算法实现
- 学会优势函数（Advantage Function）的计算和应用

## 技术栈

- Python 3.8+
- PyTorch
- Gym / Gymnasium
- NumPy
