# 技术设计文档

## 1. 架构概览

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户接口层                             │
│         (Examples / Config Files / CLI)                  │
├─────────────────────────────────────────────────────────┤
│                    训练器层                               │
│    ┌──────────────┐    ┌──────────────┐                 │
│    │ LoRA Trainer │    │ PPO Trainer  │                 │
│    └──────┬───────┘    └──────┬───────┘                 │
├───────────┼───────────────────┼─────────────────────────┤
│           │    核心算法层       │                         │
│    ┌──────┴───────┐    ┌──────┴───────┐                 │
│    │  LoRA Layer  │    │ Reward Model │                 │
│    │  LoRA Model  │    │ Value Head   │                 │
│    │  LoRA Merge  │    │ PPO Loss     │                 │
│    └──────┬───────┘    └──────┬───────┘                 │
├───────────┼───────────────────┼─────────────────────────┤
│           │    基础设施层       │                         │
│    ┌──────┴───────────────────┴───────┐                 │
│    │  Data Processing │ Evaluation    │                 │
│    │  Distributed     │ Logging       │                 │
│    └──────────────────────────────────┘                 │
├─────────────────────────────────────────────────────────┤
│                    外部依赖                               │
│         PyTorch / Transformers / PEFT / Accelerate       │
└─────────────────────────────────────────────────────────┘
```

### 1.2 模块依赖关系

```
LoRA Trainer
  ├── lora.layer (LoRA 层)
  ├── lora.model (LoRA 模型)
  ├── data.dataset (数据加载)
  └── utils.logging (日志)

PPO Trainer
  ├── ppo.reward_model (奖励模型)
  ├── ppo.value_head (价值头)
  ├── data.dataset (数据加载)
  ├── evaluation.metrics (评估)
  └── utils.distributed (分布式)
```

## 2. 核心数据结构

### 2.1 LoRA 层参数

```python
class LoRALayer:
    # 低秩分解矩阵
    lora_A: nn.Parameter  # shape: (in_features, rank)
    lora_B: nn.Parameter  # shape: (rank, out_features)

    # 超参数
    rank: int             # 低秩维度
    alpha: float          # 缩放因子
    scaling: float        # = alpha / rank
    dropout: nn.Dropout   # Dropout 层

    # 原始权重（冻结）
    base_weight: nn.Parameter  # 不参与梯度更新
```

### 2.2 PPO 训练状态

```python
class PPOStats:
    # 每步统计
    policy_loss: float        # 策略损失
    value_loss: float         # 价值损失
    entropy_loss: float       # 熵损失
    kl_divergence: float      # KL 散度
    clip_fraction: float      # 裁剪比例

    # 每批统计
    mean_reward: float        # 平均奖励
    mean_advantage: float     # 平均优势
    explained_variance: float # 解释方差
```

### 2.3 训练配置

```python
@dataclass
class LoRAConfig:
    rank: int = 8
    alpha: float = 16.0
    dropout: float = 0.05
    target_modules: List[str] = ["q_proj", "v_proj"]
    learning_rate: float = 2e-4
    num_epochs: int = 3
    batch_size: int = 4

@dataclass
class PPOConfig:
    learning_rate: float = 1.5e-5
    clip_range: float = 0.2
    kl_penalty: float = 0.1
    gamma: float = 1.0
    lam: float = 0.95
    batch_size: int = 16
    mini_batch_size: int = 4
    ppo_epochs: int = 4
    max_grad_norm: float = 0.5
```

## 3. 核心算法设计

### 3.1 LoRA 前向传播

```python
def lora_forward(self, x: torch.Tensor) -> torch.Tensor:
    """
    LoRA 前向传播: output = base_output + scaling * (x @ A @ B)

    数学原理:
    - 原始: h = Wx
    - LoRA: h = Wx + (α/r) * BAx
    - 其中 B ∈ R^{d×r}, A ∈ R^{r×k}, r << min(d,k)

    Args:
        x: 输入张量, shape (batch, seq_len, in_features)

    Returns:
        输出张量, shape (batch, seq_len, out_features)
    """
    # 基础模型的前向传播（权重冻结）
    base_output = F.linear(x, self.base_weight)

    # LoRA 分支
    lora_output = self.lora_dropout(x)
    lora_output = lora_output @ self.lora_A    # (batch, seq, rank)
    lora_output = lora_output @ self.lora_B    # (batch, seq, out)
    lora_output = lora_output * self.scaling   # 缩放

    return base_output + lora_output
```

### 3.2 PPO 损失函数

```python
def compute_ppo_loss(
    logprobs: torch.Tensor,         # 当前策略的 log 概率
    old_logprobs: torch.Tensor,     # 旧策略的 log 概率
    advantages: torch.Tensor,       # 优势估计
    values: torch.Tensor,           # 状态价值
    returns: torch.Tensor,          # 折扣回报
    clip_range: float = 0.2
) -> Tuple[torch.Tensor, dict]:
    """
    PPO Clipped Surrogate Objective

    L^{CLIP} = E[min(r_t * A_t, clip(r_t, 1-ε, 1+ε) * A_t)]

    其中:
    - r_t = π(a_t|s_t) / π_old(a_t|s_t) = exp(logπ - logπ_old)
    - A_t 是优势估计
    - ε 是裁剪范围
    """
    # 计算概率比
    ratio = torch.exp(logprobs - old_logprobs)

    # 裁剪目标
    pg_loss1 = -advantages * ratio
    pg_loss2 = -advantages * torch.clamp(ratio, 1 - clip_range, 1 + clip_range)
    policy_loss = torch.max(pg_loss1, pg_loss2).mean()

    # 价值损失
    value_loss = F.mse_loss(values, returns)

    # 统计信息
    with torch.no_grad():
        clip_fraction = (torch.abs(ratio - 1) > clip_range).float().mean()

    return policy_loss + 0.5 * value_loss, {
        "policy_loss": policy_loss.item(),
        "value_loss": value_loss.item(),
        "clip_fraction": clip_fraction.item()
    }
```

### 3.3 GAE 优势估计

```python
def compute_gae(
    rewards: torch.Tensor,       # 奖励序列
    values: torch.Tensor,        # 价值估计
    dones: torch.Tensor,         # 结束标志
    gamma: float = 1.0,          # 折扣因子
    lam: float = 0.95            # GAE lambda
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Generalized Advantage Estimation (GAE)

    A_t = Σ_{l=0}^{T-t} (γλ)^l * δ_{t+l}

    其中 δ_t = r_t + γ * V(s_{t+1}) - V(s_t) 是 TD 误差
    """
    advantages = torch.zeros_like(rewards)
    last_gae = 0

    for t in reversed(range(len(rewards))):
        if t == len(rewards) - 1:
            next_value = 0
        else:
            next_value = values[t + 1]

        delta = rewards[t] + gamma * next_value * (1 - dones[t]) - values[t]
        advantages[t] = last_gae = delta + gamma * lam * (1 - dones[t]) * last_gae

    returns = advantages + values
    return advantages, returns
```

## 4. 接口设计

### 4.1 LoRA 训练器接口

```python
class LoRATrainer:
    def __init__(self, model, config: LoRAConfig):
        """初始化 LoRA 训练器"""

    def train(self, train_dataset, eval_dataset=None) -> Dict:
        """执行训练，返回训练指标"""

    def evaluate(self, dataset) -> Dict:
        """评估模型"""

    def save(self, path: str) -> None:
        """保存 LoRA 权重"""

    def load(self, path: str) -> None:
        """加载 LoRA 权重"""

    def merge_and_save(self, path: str) -> None:
        """合并 LoRA 权重并保存完整模型"""
```

### 4.2 PPO 训练器接口

```python
class PPOTrainer:
    def __init__(self, policy_model, ref_model, reward_model, config: PPOConfig):
        """初始化 PPO 训练器"""

    def train(self, prompts: List[str], num_steps: int) -> Dict:
        """执行 PPO 训练"""

    def generate(self, prompts: List[str]) -> List[str]:
        """使用策略模型生成回答"""

    def compute_reward(self, texts: List[str]) -> torch.Tensor:
        """计算奖励分数"""

    def step(self, batch: Dict) -> PPOStats:
        """执行一步 PPO 更新"""
```

### 4.3 奖励模型接口

```python
class RewardModel:
    def __init__(self, model_name: str):
        """初始化奖励模型"""

    def score(self, texts: List[str]) -> torch.Tensor:
        """对文本进行评分"""

    @classmethod
    def from_pretrained(cls, model_name: str) -> "RewardModel":
        """从预训练模型加载"""
```

## 5. 训练流程设计

### 5.1 LoRA 微调流程

```
1. 加载预训练模型
2. 注入 LoRA 层到目标模块
3. 冻结基础模型参数
4. 对每个 epoch:
   a. 对每个 batch:
      - 前向传播（带 LoRA）
      - 计算损失（交叉熵）
      - 反向传播（仅 LoRA 参数）
      - 更新 LoRA 参数
   b. 验证集评估
   c. 日志记录
5. 保存 LoRA 权重
```

### 5.2 PPO 训练流程

```
1. 加载策略模型、参考模型、奖励模型
2. 为策略模型添加 Value Head
3. 对每个训练步:
   a. 生成阶段:
      - 使用策略模型生成回答
      - 计算每步的 log 概率
   b. 评估阶段:
      - 使用奖励模型评分
      - 计算 KL 散度惩罚
      - 计算总奖励
   c. 优化阶段:
      - 计算 GAE 优势估计
      - 对每个 mini-batch:
        * 计算当前策略 log 概率
        * 计算 PPO 裁剪损失
        * 反向传播
        * 梯度裁剪
        * 参数更新
   d. 日志记录
4. 保存最终模型
```

## 6. 错误处理策略

| 错误类型 | 处理方式 |
|----------|----------|
| 模型加载失败 | 提供清晰的错误信息和解决方案 |
| 内存不足 | 建议减小 batch_size 或使用梯度累积 |
| 训练不收敛 | 检查学习率、KL 惩罚系数等超参数 |
| 数据格式错误 | 提供数据格式示例和验证工具 |
