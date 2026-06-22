# Policy Gradient

实现策略梯度算法，包括 REINFORCE 和基线减法。

## 学习目标

- 理解策略梯度的基本原理
- 掌握 REINFORCE 算法
- 学会基线减法技术

## 项目结构

```
policy-gradient/
├── README.md              # 项目说明
├── LEARNING_NOTES.md      # 学习笔记
├── requirements.txt       # 依赖
├── docs/                  # 文档
│   ├── 01-RESEARCH.md    # 研究笔记
│   ├── 02-DESIGN.md      # 设计文档
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md     # 测试文档
│   └── 05-DEVELOPMENT.md # 开发文档
├── src/                   # 源代码
│   ├── __init__.py
│   ├── policy_network.py # 策略网络
│   ├── reinforce.py      # REINFORCE 算法
│   └── baseline.py       # 基线实现
└── tests/                 # 测试
    ├── __init__.py
    ├── test_policy_network.py
    ├── test_reinforce.py
    └── test_baseline.py
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
pytest tests/
```

### 使用示例

```python
import gymnasium as gym
from src import PolicyNetwork, REINFORCE, MovingAverageBaseline

# 创建环境
env = gym.make("CartPole-v1")

# 创建策略网络
policy = PolicyNetwork(
    state_dim=env.observation_space.shape[0],
    action_dim=env.action_space.n,
    hidden_dims=[128, 64],
)

# 创建优化器
optimizer = torch.optim.Adam(policy.parameters(), lr=0.01)

# 创建基线
baseline = MovingAverageBaseline(alpha=0.01)

# 创建 REINFORCE 智能体
agent = REINFORCE(
    policy=policy,
    optimizer=optimizer,
    gamma=0.99,
    baseline=baseline,
)

# 训练
history = agent.train(
    env=env,
    num_episodes=1000,
    verbose=True,
)

# 评估
avg_reward = agent.evaluate(env, num_episodes=100)
print(f"Average Reward: {avg_reward:.2f}")
```

## 核心组件

### PolicyNetwork

策略网络，将状态映射到动作概率分布。

```python
policy = PolicyNetwork(
    state_dim=4,
    action_dim=2,
    hidden_dims=[128, 64],
    activation="relu",
)

# 前向传播
log_probs = policy(state)

# 选择动作
action, log_prob = policy.get_action(state)
```

### Baseline

基线类，用于减少策略梯度的方差。

```python
# 无基线
baseline = NoBaseline()

# 常数基线
baseline = ConstantBaseline(value=2.0)

# 移动平均基线
baseline = MovingAverageBaseline(alpha=0.01)

# 价值网络基线
baseline = ValueBaseline(
    value_network=value_network,
    optimizer=value_optimizer,
)
```

### REINFORCE

REINFORCE 算法实现。

```python
agent = REINFORCE(
    policy=policy,
    optimizer=optimizer,
    gamma=0.99,
    baseline=baseline,
    entropy_coef=0.01,
    max_grad_norm=1.0,
)

# 训练
history = agent.train(env, num_episodes=1000)

# 评估
avg_reward = agent.evaluate(env, num_episodes=100)

# 保存模型
agent.save("model.pt")

# 加载模型
agent.load("model.pt")
```

## 技术栈

- **Python**: 3.8+
- **PyTorch**: 2.0+
- **Gymnasium**: 0.29+
- **NumPy**: 1.24+
- **Matplotlib**: 3.7+

## 文档

- [研究笔记](docs/01-RESEARCH.md)
- [设计文档](docs/02-DESIGN.md)
- [实现文档](docs/03-IMPLEMENTATION.md)
- [测试文档](docs/04-TESTING.md)
- [开发文档](docs/05-DEVELOPMENT.md)
- [学习笔记](LEARNING_NOTES.md)

## 许可证

MIT License
