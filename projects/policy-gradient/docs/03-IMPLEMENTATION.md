# 策略梯度实现文档

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

## 模块实现

### 1. policy_network.py

**功能**：实现策略网络

**关键实现**：

```python
class PolicyNetwork(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dims, activation):
        # 构建 MLP 网络
        # 使用正交初始化

    def forward(self, state):
        # 返回对数概率

    def get_action(self, state):
        # 采样动作，返回 (action, log_prob)

    def get_log_prob(self, state, action):
        # 计算特定动作的对数概率

    def get_entropy(self, state):
        # 计算策略熵
```

**设计决策**：
1. 输出对数概率而非概率，提高数值稳定性
2. 使用正交初始化，避免梯度消失/爆炸
3. 支持自定义激活函数

### 2. baseline.py

**功能**：实现各种基线方法

**类层次**：
- `Baseline`：抽象基类
- `NoBaseline`：无基线（返回零）
- `ConstantBaseline`：常数基线
- `MovingAverageBaseline`：移动平均基线
- `ValueBaseline`：价值网络基线

**关键实现**：

```python
class MovingAverageBaseline:
    def __init__(self, alpha):
        self.alpha = alpha
        self.running_mean = 0
        self.initialized = False

    def get_baseline(self, returns):
        if not self.initialized:
            self.running_mean = returns.mean()
            self.initialized = True
        else:
            self.running_mean = (1 - self.alpha) * self.running_mean + self.alpha * returns.mean()
        return torch.full_like(returns, self.running_mean)
```

**设计决策**：
1. 使用抽象基类确保接口一致性
2. 移动平均基线不需要额外网络，简单高效
3. 价值网络基线需要额外训练，但更准确

### 3. reinforce.py

**功能**：实现 REINFORCE 算法

**关键实现**：

```python
class REINFORCE:
    def __init__(self, policy, optimizer, gamma, baseline, entropy_coef, max_grad_norm):
        # 初始化所有组件

    def compute_returns(self, rewards):
        # 从后往前计算折扣回报
        # G_t = r_t + γ * G_{t+1}

    def select_action(self, state):
        # 状态 → 对数概率 → 采样动作

    def collect_episode(self, env):
        # 采集完整轨迹

    def update(self, episode):
        # 计算回报
        # 计算优势（回报 - 基线）
        # 计算损失
        # 反向传播
        # 更新参数

    def train(self, env, num_episodes):
        # 训练循环
```

**设计决策**：
1. 分离采集和更新，便于理解和测试
2. 支持梯度裁剪，提高训练稳定性
3. 支持熵正则化，鼓励探索

## 算法实现细节

### 折扣回报计算

```python
def compute_returns(self, rewards):
    returns = []
    G = 0
    for reward in reversed(rewards):
        G = reward + self.gamma * G
        returns.insert(0, G)
    return torch.tensor(returns, dtype=torch.float32)
```

**为什么从后往前计算？**
- 利用递推关系 G_t = r_t + γ * G_{t+1}
- 只需要一次遍历，时间复杂度 O(T)
- 避免重复计算

### 策略梯度估计

```python
# 计算优势
advantages = returns - baseline

# 归一化优势（可选但推荐）
if len(advantages) > 1:
    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

# 计算策略损失
policy_loss = -(log_probs * advantages.detach()).mean()
```

**为什么要归一化优势？**
- 使不同 episode 的梯度量级一致
- 加速训练收敛
- 提高训练稳定性

### 熵正则化

```python
if self.entropy_coef > 0:
    entropy = self.policy.get_entropy(states).mean()
    entropy_loss = -self.entropy_coef * entropy
```

**为什么要使用熵正则化？**
- 防止策略过早收敛到确定性策略
- 鼓励探索
- 提高样本效率

## 关键技术点

### 1. 对数概率

使用对数概率而非概率：
- 避免数值下溢
- 便于计算梯度
- 与 KL 散度自然联系

### 2. 梯度裁剪

```python
if self.max_grad_norm is not None:
    torch.nn.utils.clip_grad_norm_(
        self.policy.parameters(),
        self.max_grad_norm
    )
```

**为什么需要梯度裁剪？**
- 防止梯度爆炸
- 稳定训练过程
- 使学习率选择更容易

### 3. 优势归一化

```python
advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
```

**为什么加 1e-8？**
- 防止除以零
- 数值稳定性考虑

## 常见问题

### Q1: 为什么 REINFORCE 方差大？

**原因**：
- 使用蒙特卡洛估计
- 每个 episode 都是独立采样
- 回报的随机性大

**解决方案**：
- 使用基线减法
- 使用优势函数
- 使用更高级的算法（如 PPO）

### Q2: 如何选择学习率？

**建议**：
- 从小学习率开始（如 0.001）
- 观察训练曲线
- 如果学习太慢，可以增大学习率
- 如果训练不稳定，可以减小学习率

### Q3: 如何判断训练是否成功？

**指标**：
- 平均回报是否上升
- 是否达到环境的目标分数
- 训练曲线是否稳定

## 性能优化

### 1. 批量采样

采集多个 episode 后再更新：

```python
episodes = [self.collect_episode(env) for _ in range(batch_size)]
all_returns = torch.cat([self.compute_returns(ep.rewards) for ep in episodes])
```

### 2. 并行环境

使用多个环境并行采集：

```python
envs = [make_env() for _ in range(num_workers)]
episodes = parallel_collect(envs, policy)
```

### 3. GPU 加速

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
policy = policy.to(device)
states = states.to(device)
```
