# 03 - 实现细节

## DQN 核心实现

### 1. 神经网络实现 (`dqn.py`)

#### 网络结构

```python
class DQN(nn.Module):
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        super(DQN, self).__init__()

        # 全连接层
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        # 前向传播
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        return self.fc3(x)
```

**关键点：**
- 使用 ReLU 激活函数
- 没有最后的激活函数（输出 Q 值）
- 使用标准全连接层

#### 动作选择

```python
def get_action(self, state: torch.Tensor, epsilon: float = 0.0) -> int:
    if torch.rand(1).item() < epsilon:
        # 随机探索
        return torch.randint(0, self.fc3.out_features, (1,)).item()
    else:
        # 贪婪选择
        with torch.no_grad():
            q_values = self.forward(state.unsqueeze(0))
            return q_values.argmax(dim=1).item()
```

**关键点：**
- 使用 `torch.no_grad()` 避免计算梯度
- 使用 `unsqueeze(0)` 添加批次维度
- 使用 `argmax` 选择最大 Q 值对应的动作

### 2. 经验回放缓冲区 (`replay_buffer.py`)

#### 数据结构

```python
class ReplayBuffer:
    def __init__(self, capacity: int):
        self.buffer: deque = deque(maxlen=capacity)
```

**关键点：**
- 使用 `deque` 实现循环缓冲区
- `maxlen` 参数自动处理容量限制
- 当缓冲区满时，自动移除最旧的经验

#### 添加经验

```python
def push(self, state, action, reward, next_state, done):
    self.buffer.append((state, action, reward, next_state, done))
```

**关键点：**
- 存储完整的经验元组
- 使用 `append` 添加到缓冲区末尾

#### 采样批次

```python
def sample(self, batch_size: int) -> Tuple[np.ndarray, ...]:
    batch = random.sample(self.buffer, batch_size)

    states = np.array([t[0] for t in batch])
    actions = np.array([t[1] for t in batch])
    rewards = np.array([t[2] for t in batch])
    next_states = np.array([t[3] for t in batch])
    dones = np.array([t[4] for t in batch])

    return states, actions, rewards, next_states, dones
```

**关键点：**
- 使用 `random.sample` 随机采样
- 将批次数据转换为 numpy 数组
- 返回分离的各个组件

### 3. DQN 代理 (`agent.py`)

#### 初始化

```python
class DQNAgent:
    def __init__(self, ...):
        # 设备
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 当前网络
        self.policy_net = DQN(state_dim, action_dim, hidden_dim).to(self.device)

        # 目标网络（复制当前网络）
        self.target_net = copy.deepcopy(self.policy_net).to(self.device)
        self.target_net.eval()

        # 优化器
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)

        # 经验回放缓冲区
        self.replay_buffer = ReplayBuffer(buffer_size)
```

**关键点：**
- 自动检测 GPU 可用性
- 使用 `copy.deepcopy` 复制目标网络
- 目标网络设置为评估模式（`eval()`）
- 使用 Adam 优化器

#### 动作选择

```python
def select_action(self, state: np.ndarray, training: bool = True) -> int:
    if training and np.random.random() < self.epsilon:
        # 探索：随机选择动作
        return np.random.randint(self.action_dim)
    else:
        # 利用：选择 Q 值最大的动作
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.policy_net(state_tensor)
        return q_values.argmax(dim=1).item()
```

**关键点：**
- 训练模式下使用 epsilon-greedy 策略
- 评估模式下使用贪婪策略
- 转换状态为张量并移动到设备

#### 训练逻辑

```python
def train(self) -> Optional[float]:
    # 检查缓冲区是否有足够样本
    if len(self.replay_buffer) < self.batch_size:
        return None

    # 采样批次数据
    states, actions, rewards, next_states, dones = self.replay_buffer.sample(
        self.batch_size
    )

    # 转换为张量
    states = torch.FloatTensor(states).to(self.device)
    actions = torch.LongTensor(actions).to(self.device)
    rewards = torch.FloatTensor(rewards).to(self.device)
    next_states = torch.FloatTensor(next_states).to(self.device)
    dones = torch.FloatTensor(dones).to(self.device)

    # 计算当前 Q 值
    q_values = self.policy_net(states)
    q_values = q_values.gather(1, actions.unsqueeze(1)).squeeze(1)

    # 计算目标 Q 值
    with torch.no_grad():
        next_q_values = self.target_net(next_states)
        next_q_values = next_q_values.max(dim=1)[0]
        target_q_values = rewards + self.gamma * next_q_values * (1 - dones)

    # 计算损失
    loss = nn.MSELoss()(q_values, target_q_values)

    # 反向传播
    self.optimizer.zero_grad()
    loss.backward()
    self.optimizer.step()

    # 更新探索率
    self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

    # 更新目标网络
    self.train_step += 1
    if self.train_step % self.target_update_freq == 0:
        self.target_net.load_state_dict(self.policy_net.state_dict())

    return loss.item()
```

**关键点：**
- 检查缓冲区大小，不足时返回 None
- 将 numpy 数组转换为张量并移动到设备
- 使用 `gather` 选择特定动作的 Q 值
- 使用目标网络计算目标 Q 值
- 使用 MSE 损失
- 定期更新目标网络

### 4. 训练脚本 (`train.py`)

#### 环境初始化

```python
env = gym.make("CartPole-v1", render_mode="human" if render else None)
state_dim = env.observation_space.shape[0]
action_dim = env.action_space.n
```

**关键点：**
- 使用 Gymnasium 创建环境
- 获取状态和动作维度
- 支持渲染模式

#### 训练循环

```python
for episode in range(num_episodes):
    state, _ = env.reset()
    episode_reward = 0

    for step in range(max_steps):
        # 选择动作
        action = agent.select_action(state, training=True)

        # 执行动作
        next_state, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated

        # 存储经验
        agent.store_experience(state, action, reward, next_state, done)

        # 训练
        loss = agent.train()

        # 更新状态
        state = next_state
        episode_reward += reward

        if done:
            break
```

**关键点：**
- 每轮开始时重置环境
- 使用 `terminated` 和 `truncated` 判断结束
- 每步存储经验并训练
- 累积奖励

#### 模型保存

```python
def save(self, path: str) -> None:
    torch.save(
        {
            "policy_net": self.policy_net.state_dict(),
            "target_net": self.target_net.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "epsilon": self.epsilon,
            "train_step": self.train_step,
        },
        path,
    )
```

**关键点：**
- 保存所有必要的状态
- 使用字典组织保存内容
- 包含网络参数、优化器状态和训练状态

## 常见问题及解决方案

### 1. 训练不稳定

**问题：**
- 奖励波动大
- 损失不稳定

**解决方案：**
- 使用目标网络
- 增大缓冲区容量
- 减小学习率
- 增加目标网络更新频率

### 2. 过估计问题

**问题：**
- Q 值被高估
- 策略次优

**解决方案：**
- 使用 Double DQN
- 使用优先经验回放
- 使用 Dueling DQN

### 3. 探索不足

**问题：**
- 过早收敛到次优策略
- 无法找到最优策略

**解决方案：**
- 增大初始探索率
- 减慢探索率衰减
- 使用噪声网络

### 4. 内存不足

**问题：**
- 缓冲区过大
- 内存溢出

**解决方案：**
- 减小缓冲区容量
- 使用优先经验回放
- 定期清理缓冲区

## 性能优化

### 1. GPU 加速

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
```

### 2. 批量处理

```python
# 批量前向传播
states = torch.FloatTensor(states).to(device)
q_values = model(states)
```

### 3. 梯度裁剪

```python
loss.backward()
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
optimizer.step()
```

### 4. 学习率调度

```python
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=100, gamma=0.9)
```
