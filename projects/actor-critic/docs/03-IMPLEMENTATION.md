# Actor-Critic 实现细节

## 1. 项目结构

```
actor-critic/
├── src/
│   └── actor_critic/
│       ├── __init__.py              # 包入口
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
│   ├── test_agent.py
│   └── test_advantages.py
├── scripts/
│   ├── train.py
│   └── evaluate.py
├── configs/
│   └── default.yaml
├── setup.py
└── requirements.txt
```

## 2. 核心实现

### 2.1 Actor 网络实现

```python
class ActorNetwork(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
        )

    def forward(self, state):
        return self.network(state)  # logits

    def get_action(self, state):
        probs = F.softmax(self.forward(state), dim=-1)
        dist = Categorical(probs)
        action = dist.sample()
        return action.item(), dist.log_prob(action)
```

**关键点**：
- 输出 logits 而非概率，数值更稳定
- 使用 PyTorch 的 `Categorical` 分布进行采样
- 返回 log_prob 用于后续策略梯度计算

### 2.2 Critic 网络实现

```python
class CriticNetwork(nn.Module):
    def __init__(self, state_dim, hidden_dim=128):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, state):
        return self.network(state)  # value estimate
```

**关键点**：
- 输出单个标量，表示状态价值
- 与 Actor 共享相同的隐藏层结构（可选）

### 2.3 优势函数计算

```python
def compute_advantages(rewards, values, gamma=0.99, gae_lambda=1.0):
    if gae_lambda == 1.0:
        # 简单优势：A_t = G_t - V(s_t)
        returns = compute_returns(rewards, gamma)
        return [ret - val for ret, val in zip(returns, values)]

    # GAE 计算
    advantages = []
    gae = 0
    next_value = 0
    for t in reversed(range(len(rewards))):
        delta = rewards[t] + gamma * next_value - values[t]
        gae = delta + gamma * gae_lambda * gae
        advantages.insert(0, gae)
        next_value = values[t]
    return advantages
```

**关键点**：
- 支持简单优势和 GAE 两种计算方式
- 逆序计算，正确处理时间依赖
- gae_lambda=1.0 时退化为简单优势

### 2.4 Agent 更新逻辑

```python
def update(self):
    # 1. 计算优势
    advantages = compute_advantages(self.rewards, self.values)
    advantages = normalize_advantages(advantages)

    # 2. 计算 Critic 损失
    values = self.critic(states).squeeze(-1)
    critic_loss = MSE(values, returns)

    # 3. 计算 Actor 损失
    log_probs, entropy = self.actor.evaluate_actions(states, actions)
    actor_loss = -(log_probs * advantages.detach()).mean()
    entropy_loss = -entropy.mean()

    # 4. 更新网络
    critic_optimizer.zero_grad()
    critic_loss.backward()
    critic_optimizer.step()

    actor_optimizer.zero_grad()
    (actor_loss + entropy_coef * entropy_loss).backward()
    actor_optimizer.step()
```

## 3. 训练流程实现

### 3.1 数据收集

```python
for step in range(max_steps):
    # 选择动作
    action = agent.select_action(state)

    # 执行动作
    next_state, reward, done, _ = env.step(action)

    # 存储数据
    agent.store_reward(reward)

    state = next_state
    if done:
        break
```

### 3.2 批量更新

```python
# 收集完整 episode 后更新
losses = agent.update()
```

**设计选择**：
- 使用完整 episode 更新（而非逐步更新）
- 简化实现，适合 CartPole 这类短 episode 任务

## 4. 超参数调优

### 4.1 学习率

- Actor LR: 3e-4（较慢，稳定策略更新）
- Critic LR: 1e-3（较快，快速拟合价值）

### 4.2 折扣因子

- gamma = 0.99（考虑长期回报）

### 4.3 熵系数

- entropy_coef = 0.01（平衡探索与利用）

## 5. 性能优化

### 5.1 梯度裁剪

```python
torch.nn.utils.clip_grad_norm_(self.actor.parameters(), max_norm=0.5)
```

### 5.2 优势归一化

```python
advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
```

### 5.3 目标网络（可选）

对于更稳定的训练，可以使用目标网络：
```python
self.target_critic = CriticNetwork(state_dim, hidden_dim)
self.target_critic.load_state_dict(self.critic.state_dict())
```
