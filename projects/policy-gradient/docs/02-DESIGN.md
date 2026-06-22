# 策略梯度设计文档

## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    REINFORCE Agent                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────┐  │
│  │ PolicyNetwork │    │   Baseline   │    │  Trainer │  │
│  │              │    │              │    │          │  │
│  │ state → logits│    │ returns → b  │    │ collect  │  │
│  │              │    │              │    │ update   │  │
│  └──────────────┘    └──────────────┘    └──────────┘  │
│         │                   │                   │        │
│         └───────────────────┴───────────────────┘        │
│                             │                            │
│                      ┌──────▼──────┐                     │
│                      │   Policy    │                     │
│                      │   Update    │                     │
│                      └─────────────┘                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 核心组件设计

### 1. PolicyNetwork

**职责**：将状态映射到动作概率分布

**设计要点**：
- 输入：状态向量
- 输出：动作的对数概率
- 使用 Softmax 确保概率和为 1
- 支持自定义网络结构

**接口**：
```python
class PolicyNetwork(nn.Module):
    def forward(state) -> log_probs
    def get_action(state) -> (action, log_prob)
    def get_log_prob(state, action) -> log_prob
    def get_entropy(state) -> entropy
```

### 2. Baseline

**职责**：提供基线值以减少方差

**层次结构**：
```
Baseline (ABC)
├── NoBaseline          # 无基线
├── ConstantBaseline    # 常数基线
├── MovingAverageBaseline  # 移动平均基线
└── ValueBaseline       # 价值网络基线
```

**接口**：
```python
class Baseline(ABC):
    def get_baseline(returns) -> baseline_values
    def compute_advantage(returns) -> advantages
```

### 3. REINFORCE

**职责**：实现 REINFORCE 算法

**核心方法**：
- `collect_episode()`：采集轨迹
- `compute_returns()`：计算折扣回报
- `update()`：更新策略
- `train()`：训练循环
- `evaluate()`：评估性能

## 数据流

### 训练流程

```
1. 初始化
   ├── 创建策略网络
   ├── 创建优化器
   └── 创建基线（可选）

2. 采集轨迹
   ├── 环境重置
   ├── 循环直到完成
   │   ├── 状态 → 策略网络 → 动作概率
   │   ├── 采样动作
   │   ├── 执行动作 → 获得奖励和新状态
   │   └── 记录 (state, action, reward, log_prob)
   └── 返回完整轨迹

3. 计算回报
   ├── 从后往前计算折扣回报
   │   G_t = r_t + γ * G_{t+1}
   └── 返回回报张量

4. 更新策略
   ├── 计算优势 = 回报 - 基线
   ├── 计算策略损失 = -mean(log_prob * advantage)
   ├── 计算熵损失（可选）
   ├── 反向传播
   └── 更新参数

5. 评估（可选）
   ├── 采样多个 episode
   └── 计算平均回报
```

### 数据结构

```python
@dataclass
class TrajectoryStep:
    state: np.ndarray    # 环境状态
    action: int          # 执行的动作
    reward: float        # 获得的奖励
    log_prob: Tensor     # 动作的对数概率

@dataclass
class EpisodeResult:
    steps: List[TrajectoryStep]  # 所有步骤
    total_reward: float          # 总奖励
    length: int                  # 步数
```

## 算法细节

### 折扣回报计算

使用递推关系高效计算：

```python
def compute_returns(rewards, gamma):
    returns = []
    G = 0
    for r in reversed(rewards):
        G = r + gamma * G
        returns.insert(0, G)
    return returns
```

时间复杂度：O(T)，空间复杂度：O(T)

### 策略梯度估计

REINFORCE 的梯度估计：

```python
# 无基线
loss = -mean(log_probs * returns)

# 有基线
advantages = returns - baseline
loss = -mean(log_probs * advantages)
```

### 熵正则化

鼓励探索，防止策略过早收敛：

```python
entropy = -sum(p * log(p))
loss = policy_loss - entropy_coef * entropy
```

## 配置参数

### 超参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| gamma | 0.99 | 折扣因子 |
| lr | 0.01 | 学习率 |
| entropy_coef | 0.0 | 熵正则化系数 |
| max_grad_norm | None | 梯度裁剪阈值 |
| hidden_dims | [128, 64] | 隐藏层维度 |

### 环境配置

| 参数 | 说明 |
|------|------|
| state_dim | 状态空间维度 |
| action_dim | 动作空间维度 |
| max_steps | 最大步数 |

## 扩展点

### 1. 自定义策略网络

```python
class CustomPolicy(PolicyNetwork):
    def __init__(self):
        # 自定义网络结构
        self.cnn = nn.Conv2d(...)
        self.lstm = nn.LSTM(...)
```

### 2. 自定义基线

```python
class CustomBaseline(Baseline):
    def get_baseline(self, returns):
        # 自定义基线逻辑
        return baseline_values
```

### 3. 自定义环境

```python
class CustomEnv:
    def reset(self) -> state
    def step(action) -> (state, reward, done, info)
```

## 性能优化

### 1. 批量处理

将多个 episode 的数据合并处理：

```python
all_states = torch.cat([ep.states for ep in episodes])
all_returns = torch.cat([ep.returns for ep in episodes])
```

### 2. 并行采样

使用多个环境并行采集：

```python
envs = [make_env() for _ in range(num_workers)]
episodes = parallel_collect(envs, policy)
```

### 3. GPU 加速

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
policy = policy.to(device)
```
