# 开发手册

## 1. 环境搭建

### 1.1 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| Python | 3.10+ | 3.11 |
| PyTorch | 2.0+ | 2.1+ |
| GPU | 1x 8GB VRAM | 1x 16GB+ VRAM |
| 内存 | 16GB | 32GB+ |
| 磁盘 | 10GB | 50GB+ |

### 1.2 安装步骤

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 2. 安装 PyTorch (根据 CUDA 版本选择)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 3. 安装项目依赖
pip install -r requirements.txt

# 4. 安装项目（开发模式）
pip install -e .
```

### 1.3 依赖说明

```
torch>=2.0.0          # 深度学习框架
transformers>=4.30.0  # 预训练模型加载
peft>=0.5.0           # 参数高效微调（参考）
accelerate>=0.21.0    # 分布式训练
datasets>=2.14.0      # 数据集处理
pyyaml>=6.0           # 配置文件
tqdm>=4.65.0          # 进度条
numpy>=1.24.0         # 数值计算
```

## 2. 项目结构说明

```
src/
├── __init__.py
├── lora/                    # LoRA 核心实现
│   ├── __init__.py
│   ├── layer.py             # LoRA 层（最核心）
│   ├── model.py             # LoRA 模型包装
│   └── trainer.py           # LoRA 训练器
├── ppo/                     # PPO 核心实现
│   ├── __init__.py
│   ├── ppo_trainer.py       # PPO 训练器
│   ├── reward_model.py      # 奖励模型
│   └── value_head.py        # Value Head
├── data/                    # 数据处理
│   ├── __init__.py
│   └── dataset.py           # 数据集类
├── evaluation/              # 评估模块
│   ├── __init__.py
│   └── metrics.py           # 评估指标
└── utils/                   # 工具模块
    ├── __init__.py
    ├── distributed.py       # 分布式工具
    └── logging_utils.py     # 日志工具
```

## 3. 核心模块解析

### 3.1 LoRA 层实现 (`src/lora/layer.py`)

**⭐ 重点难点**: 理解低秩分解的数学原理和实现细节

```python
class LoRALinear(nn.Module):
    """
    LoRA 低秩适配层

    核心思想: 将权重更新 ΔW 分解为低秩矩阵 BA
    W' = W + ΔW = W + BA
    其中 B ∈ R^{d×r}, A ∈ R^{r×k}, r << min(d,k)

    关键参数:
    - rank: 低秩维度，越大表达能力越强
    - alpha: 缩放因子，控制 LoRA 更新的幅度
    - scaling: 实际缩放 = alpha / rank
    """
```

**关键设计决策**:
1. A 矩阵使用 Kaiming 均匀分布初始化
2. B 矩阵使用零初始化（确保训练开始时 ΔW = 0）
3. scaling = alpha / rank，确保不同 rank 下更新幅度一致

### 3.2 PPO 训练器 (`src/ppo/ppo_trainer.py`)

**⭐⭐ 重点难点**: 理解 PPO 的裁剪机制和 GAE 优势估计

核心训练循环:
```python
def step(self, batch):
    # 1. 生成回答
    responses = self.generate(batch["prompts"])

    # 2. 计算奖励
    rewards = self.compute_reward(responses)

    # 3. 计算 KL 惩罚
    kl_penalty = self.compute_kl_penalty(responses)

    # 4. 计算总奖励
    total_rewards = rewards - self.config.kl_penalty * kl_penalty

    # 5. 计算 GAE
    advantages, returns = compute_gae(total_rewards, values, dones)

    # 6. PPO 更新
    for epoch in range(self.config.ppo_epochs):
        for mini_batch in get_mini_batches(batch):
            loss = compute_ppo_loss(...)
            loss.backward()
            clip_grad_norm_(self.policy.parameters(), self.config.max_grad_norm)
            self.optimizer.step()
```

### 3.3 奖励模型 (`src/ppo/reward_model.py`)

**💡 值得思考**: 奖励模型的质量直接决定 RLHF 的效果

设计选择:
- 使用预训练的 sentiment 模型作为简单奖励
- 支持自定义奖励函数
- 奖励归一化以稳定训练

## 4. 开发流程

### 4.1 添加新功能

1. 在相应的模块中添加代码
2. 编写单元测试
3. 更新文档
4. 运行测试确认通过
5. 更新示例（如需要）

### 4.2 代码风格

- 遵循 PEP 8
- 使用 type hints
- 函数和类必须有 docstring
- 重要逻辑必须有注释
- 变量命名清晰，避免缩写

### 4.3 测试要求

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_lora.py -v

# 运行带覆盖率的测试
python -m pytest tests/ -v --cov=src
```

## 5. 常见问题

### Q1: CUDA 内存不足怎么办？

```bash
# 方案 1: 减小 batch size
# 方案 2: 使用梯度累积
# 方案 3: 使用更小的模型
# 方案 4: 使用 LoRA（降低可训练参数量）
```

### Q2: PPO 训练不稳定怎么办？

```bash
# 方案 1: 降低学习率
# 方案 2: 增大 clip_range
# 方案 3: 增大 KL 惩罚系数
# 方案 4: 减小 PPO epochs
# 方案 5: 使用梯度裁剪
```

### Q3: 如何调试训练过程？

```python
# 1. 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 2. 监控关键指标
print(f"KL divergence: {kl_div:.4f}")
print(f"Mean reward: {reward:.4f}")
print(f"Policy loss: {loss:.4f}")

# 3. 使用小数据集快速验证
```

## 6. 性能优化建议

| 优化项 | 方法 | 效果 |
|--------|------|------|
| 混合精度训练 | 使用 `torch.cuda.amp` | 2x 训练加速 |
| 梯度累积 | `gradient_accumulation_steps` | 模拟更大 batch |
| Flash Attention | 安装 `flash-attn` | 注意力计算加速 |
| 梯度检查点 | `model.gradient_checkpointing_enable()` | 降低内存占用 |

## 7. 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交代码和测试
4. 确保所有测试通过
5. 提交 Pull Request
