# Finetune-RL Framework

> 一个支持 LoRA 微调和 PPO 强化学习的大模型后训练框架

## 项目简介

本项目是一个学习导向的大模型后训练框架，旨在帮助开发者深入理解：
- **LoRA**（Low-Rank Adaptation）低秩适配的原理与实现
- **PPO**（Proximal Policy Optimization）强化学习算法在 LLM 对齐中的应用
- 分布式训练与梯度同步机制

## 学习目标

### 核心知识点
1. **LoRA 低秩适配原理** ⭐
   - 理解为什么低秩分解可以有效微调大模型
   - 掌握 LoRA 的数学原理：`W' = W + BA`，其中 `B ∈ R^{d×r}`, `A ∈ R^{r×k}`, `r << min(d,k)`
   - 学习 rank、alpha、dropout 等超参数的影响

2. **PPO 强化学习算法** ⭐⭐
   - 理解策略梯度的基本框架
   - 掌握 clipped surrogate objective 的设计动机
   - 学习 GAE（Generalized Advantage Estimation）的实现
   - 理解 KL penalty 在 RLHF 中的作用

3. **分布式训练** ⭐
   - 数据并行 vs 模型并行
   - 梯度同步与 AllReduce
   - DeepSpeed ZeRO 优化策略

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| Python 3.10+ | 主语言 | ★☆☆ |
| PyTorch 2.0+ | 深度学习框架 | ★★☆ |
| Transformers | 模型加载与推理 | ★★☆ |
| PEFT | 参数高效微调 | ★★☆ |
| Accelerate | 分布式训练 | ★★★ |

## 核心流程

### LoRA 微调流程
```
基础模型 → 注入 LoRA 层 → 前向传播 → 损失计算 → 反向传播 → 更新 LoRA 参数 → 评估
```

### PPO 强化学习流程
```
提示词 → 策略模型生成 → 奖励模型评分 → 计算优势 → PPO 裁剪更新 → KL 散度约束
```

## 重点难点

### ⭐ 重点
1. **LoRA 的秩选择**：rank 越大表达能力越强，但参数量也越大。如何平衡？
2. **PPO 的裁剪机制**：为什么要裁剪？裁剪范围如何影响训练稳定性？
3. **奖励模型的设计**：奖励信号的质量直接决定 RLHF 的效果

### ⭐⭐ 难点
1. **PPO 训练的不稳定性**：学习率、clip_range、KL 惩罚系数的调优
2. **多模型协作**：PPO 需要同时维护 policy、reference、reward、value 四个模型
3. **分布式梯度同步**：确保多卡训练时梯度的一致性

## 值得思考 💡

1. LoRA 为什么有效？低秩假设在什么情况下会失效？
2. PPO vs DPO：各自的优劣势？什么场景下选择哪个？
3. 奖励模型能否被 LLM 自身替代？（Self-Rewarding 的思路）
4. 如何在保持基座模型能力的同时进行对齐？（Alignment Tax）
5. QLoRA 的量化是否会损失信息？精度-效率的 trade-off 如何权衡？

## 项目结构

```
finetune-rl-framework/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记模板
├── requirements.txt             # 依赖
├── setup.py                     # 安装配置
├── configs/                     # 配置文件
│   ├── lora_config.yaml
│   └── ppo_config.yaml
├── docs/                        # 文档
│   ├── 01-RESEARCH.md
│   ├── 02-REQUIREMENTS.md
│   ├── 03-DESIGN.md
│   ├── 04-PRODUCT.md
│   └── 05-DEVELOPMENT.md
├── src/                         # 源代码
│   ├── __init__.py
│   ├── lora/                    # LoRA 实现
│   │   ├── __init__.py
│   │   ├── layer.py             # LoRA 层实现
│   │   ├── model.py             # LoRA 模型包装
│   │   └── trainer.py           # LoRA 训练器
│   ├── ppo/                     # PPO 实现
│   │   ├── __init__.py
│   │   ├── ppo_trainer.py       # PPO 训练器
│   │   ├── reward_model.py      # 奖励模型
│   │   └── value_head.py        # Value Head
│   ├── data/                    # 数据处理
│   │   ├── __init__.py
│   │   └── dataset.py           # 数据集处理
│   ├── evaluation/              # 评估
│   │   ├── __init__.py
│   │   └── metrics.py           # 评估指标
│   └── utils/                   # 工具
│       ├── __init__.py
│       ├── distributed.py       # 分布式工具
│       └── logging_utils.py     # 日志工具
├── tests/                       # 测试
│   ├── test_lora.py
│   ├── test_ppo.py
│   └── test_data.py
└── examples/                    # 示例
    ├── lora_finetune_example.py
    └── ppo_train_example.py
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# LoRA 微调示例
python examples/lora_finetune_example.py

# PPO 训练示例
python examples/ppo_train_example.py

# 运行测试
python -m pytest tests/
```

## 参考资源

- [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)
- [Proximal Policy Optimization Algorithms](https://arxiv.org/abs/1707.06347)
- [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155)
- [Direct Preference Optimization](https://arxiv.org/abs/2305.18290)
- [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314)
- [Hugging Face PEFT](https://github.com/huggingface/peft)
- [Hugging Face TRL](https://github.com/huggingface/trl)
- [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory)
- [DeepSpeed-Chat](https://github.com/microsoft/DeepSpeedExamples)

## License

MIT License - 仅供学习使用
