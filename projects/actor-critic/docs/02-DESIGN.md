# Actor-Critic 系统设计

## 1. 系统架构

### 1.1 模块划分

```
actor_critic/
├── agents/
│   └── actor_critic_agent.py    # 核心 Agent 实现
├── networks/
│   ├── actor_network.py         # Actor 策略网络
│   └── critic_network.py        # Critic 价值网络
└── utils/
    └── advantages.py            # 优势函数计算
```

### 1.2 数据流

```
┌─────────────────────────────────────────────────────────────┐
│                      Environment                            │
│                         │                                   │
│                         ▼                                   │
│                    state (s_t)                               │
│                         │                                   │
│            ┌────────────┼────────────┐                      │
│            ▼                         ▼                      │
│    ┌──────────────┐         ┌──────────────┐                │
│    │ Actor Network │         │ Critic Network│               │
│    │  π(a|s; θ)   │         │   V(s; w)     │               │
│    └──────┬───────┘         └──────┬───────┘                │
│           │                        │                        │
│           ▼                        ▼                        │
│    action probabilities      value estimate                 │
│           │                        │                        │
│           ▼                        │                        │
│    sample action a_t               │                        │
│           │                        │                        │
│           ▼                        │                        │
│    ┌──────────────┐                │                        │
│    │  Environment  │                │                        │
│    │  execute a_t  │                │                        │
│    └──────┬───────┘                │                        │
│           │                        │                        │
│           ▼                        │                        │
│    reward r_t, state s_{t+1}       │                        │
│           │                        │                        │
│           ▼                        ▼                        │
│    ┌────────────────────────────────────┐                   │
│    │         Compute Advantage          │                   │
│    │   A_t = r_t + γV(s_{t+1}) - V(s_t)│                   │
│    └────────────────┬───────────────────┘                   │
│                     │                                       │
│         ┌───────────┴───────────┐                           │
│         ▼                       ▼                           │
│  Actor Loss               Critic Loss                       │
│  -log π(a|s) * A_t        (A_t)^2                          │
│         │                       │                           │
│         ▼                       ▼                           │
│  Update θ                 Update w                          │
└─────────────────────────────────────────────────────────────┘
```

## 2. 类设计

### 2.1 ActorNetwork

```python
class ActorNetwork(nn.Module):
    """策略网络，输出动作概率分布"""

    def __init__(self, state_dim, action_dim, hidden_dim):
        # 3层全连接网络
        # state_dim -> hidden_dim -> hidden_dim -> action_dim

    def forward(self, state):
        # 返回动作 logits

    def get_action_probs(self, state):
        # 返回 softmax 后的动作概率

    def get_action(self, state):
        # 采样动作，返回 (action, log_prob)

    def evaluate_actions(self, state, action):
        # 评估动作，返回 (log_prob, entropy)
```

### 2.2 CriticNetwork

```python
class CriticNetwork(nn.Module):
    """价值网络，估计状态价值"""

    def __init__(self, state_dim, hidden_dim):
        # 3层全连接网络
        # state_dim -> hidden_dim -> hidden_dim -> 1

    def forward(self, state):
        # 返回状态价值估计

    def get_value(self, state):
        # 获取标量价值
```

### 2.3 ActorCriticAgent

```python
class ActorCriticAgent:
    """Actor-Critic 智能体"""

    def __init__(self, state_dim, action_dim, ...):
        # 初始化网络和优化器

    def select_action(self, state):
        # 根据策略选择动作

    def store_reward(self, reward):
        # 存储奖励

    def update(self):
        # 更新 Actor 和 Critic 网络

    def save(self, path):
        # 保存模型

    def load(self, path):
        # 加载模型
```

## 3. 损失函数设计

### 3.1 Actor Loss（策略损失）

```python
actor_loss = -log_prob * advantage.detach()
```

- 使用负号因为我们要最大化期望回报
- advantage.detach() 防止梯度回传到 Critic

### 3.2 Critic Loss（价值损失）

```python
critic_loss = MSE(predicted_value, target_return)
```

- 目标：最小化价值估计与实际回报的差距

### 3.3 熵正则化

```python
entropy_loss = -entropy.mean()
total_loss = actor_loss + entropy_coef * entropy_loss
```

- 鼓励探索，防止策略过早收敛

## 4. 训练流程

```python
for episode in range(num_episodes):
    state = env.reset()

    for step in range(max_steps):
        # 1. Actor 选择动作
        action = agent.select_action(state)

        # 2. 环境执行动作
        next_state, reward, done, _ = env.step(action)

        # 3. 存储奖励
        agent.store_reward(reward)

        state = next_state
        if done:
            break

    # 4. 更新网络
    losses = agent.update()
```

## 5. 超参数设计

| 参数 | 默认值 | 说明 |
|------|--------|------|
| hidden_dim | 128 | 隐藏层维度 |
| actor_lr | 3e-4 | Actor 学习率 |
| critic_lr | 1e-3 | Critic 学习率 |
| gamma | 0.99 | 折扣因子 |
| gae_lambda | 1.0 | GAE λ 参数 |
| entropy_coef | 0.01 | 熵系数 |
