# 02 - 架构设计

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     DQN 系统架构                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │  环境   │◄──►│  代理   │◄──►│  网络   │◄──►│  缓冲区 │  │
│  │ (Gym)   │    │ (Agent) │    │ (DQN)   │    │ (Buffer)│  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│       │              │              │              │        │
│       ▼              ▼              ▼              ▼        │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ 状态/   │    │ 动作   │    │ 前向   │    │ 采样   │  │
│  │ 奖励    │    │ 选择   │    │ 传播   │    │ 批次   │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. DQN 网络 (`dqn.py`)

**职责：**
- 近似 Q 值函数
- 前向传播计算 Q 值
- 支持动作选择

**类设计：**
```python
class DQN(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        # 全连接层
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)

    def forward(self, state):
        # 前向传播
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        return self.fc3(x)

    def get_action(self, state, epsilon=0.0):
        # epsilon-greedy 策略
        if random() < epsilon:
            return randint(action_dim)
        else:
            return self.forward(state).argmax()
```

#### 2. 经验回放缓冲区 (`replay_buffer.py`)

**职责：**
- 存储经验数据
- 随机采样批次
- 管理缓冲区容量

**数据结构：**
```python
class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        return unzip(batch)

    def __len__(self):
        return len(self.buffer)
```

#### 3. DQN 代理 (`agent.py`)

**职责：**
- 整合所有组件
- 实现训练逻辑
- 管理探索策略

**核心方法：**
```python
class DQNAgent:
    def __init__(self, ...):
        self.policy_net = DQN(...)  # 当前网络
        self.target_net = DQN(...)  # 目标网络
        self.replay_buffer = ReplayBuffer(...)
        self.optimizer = Adam(...)

    def select_action(self, state, training=True):
        # epsilon-greedy 策略
        pass

    def store_experience(self, state, action, reward, next_state, done):
        # 存储经验
        self.replay_buffer.push(...)

    def train(self):
        # 训练一步
        # 1. 采样批次
        # 2. 计算 Q 值
        # 3. 计算损失
        # 4. 反向传播
        # 5. 更新目标网络
        pass
```

### 数据流

#### 训练流程

```
1. 环境初始化
   └── 获取初始状态 s

2. 动作选择
   ├── 输入：状态 s
   ├── ε-greedy 策略
   └── 输出：动作 a

3. 环境交互
   ├── 输入：动作 a
   ├── 执行动作
   └── 输出：(s', r, done)

4. 经验存储
   └── 存储 (s, a, r, s', done) 到缓冲区

5. 训练更新
   ├── 从缓冲区采样批次
   ├── 计算当前 Q 值：Q(s, a)
   ├── 计算目标 Q 值：r + γ * max Q'(s', a')
   ├── 计算损失：MSE(Q, target)
   ├── 反向传播
   └── 更新目标网络（定期）

6. 循环
   └── 重复 2-5 直到结束
```

### 关键设计决策

#### 1. 网络架构

**选择：**
- 2 层全连接网络
- ReLU 激活函数
- 隐藏层维度 128

**原因：**
- CartPole 是简单问题，不需要复杂网络
- 2 层足够学习 Q 值函数
- 128 维在性能和效果之间平衡

#### 2. 经验回放

**选择：**
- 使用 deque 实现循环缓冲区
- 容量 10000
- 随机均匀采样

**原因：**
- deque 自动处理容量限制
- 10000 足够存储大量经验
- 均匀采样简单有效

#### 3. 目标网络

**选择：**
- 完全复制策略网络
- 每 10 步更新一次

**原因：**
- 完全复制简单稳定
- 10 步更新频率适中
- 平衡稳定性和学习速度

#### 4. 探索策略

**选择：**
- ε-greedy 策略
- ε 从 1.0 衰减到 0.01
- 衰减率 0.995

**原因：**
- ε-greedy 简单有效
- 初始高探索，后期高利用
- 衰减率适中，不会太快或太慢

### 性能考虑

#### 内存使用

- 经验回放缓冲区：约 10000 * (4+1+1+4+1) * 4 bytes ≈ 440 KB
- 网络参数：约 128*128*2 + 128*4 ≈ 33K 参数
- 总内存使用：< 10 MB

#### 计算复杂度

- 前向传播：O(batch_size * hidden_dim^2)
- 反向传播：O(batch_size * hidden_dim^2)
- 每步训练：O(batch_size * hidden_dim^2)

#### 优化建议

1. **GPU 加速**：使用 CUDA 加速训练
2. **批量大小**：32-128 之间选择
3. **学习率**：1e-3 到 1e-4 之间
4. **隐藏层维度**：64-256 之间
