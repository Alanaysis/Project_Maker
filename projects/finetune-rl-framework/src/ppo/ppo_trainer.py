"""
PPO (Proximal Policy Optimization) 训练器

⭐ PPO 算法核心思想:
    PPO 是一种策略梯度方法，通过限制策略更新的幅度来保证训练稳定性。
    核心是 Clipped Surrogate Objective:

    L^{CLIP} = E[min(r_t * A_t, clip(r_t, 1-ε, 1+ε) * A_t)]

    其中:
    - r_t = π(a_t|s_t) / π_old(a_t|s_t) 是概率比
    - A_t 是优势估计（使用 GAE 计算）
    - ε 是裁剪范围（通常 0.1-0.3）

💡 为什么 PPO 适用于 RLHF?
    1. 稳定性: 裁剪机制防止策略更新过大
    2. 样本效率: 支持多轮优化同一批数据
    3. 简单: 实现相对简单，超参数易于调整
    4. KL 约束: 可以添加 KL 散度惩罚保持与原始模型的接近

参考论文:
    - "Proximal Policy Optimization Algorithms" (Schulman et al., 2017)
    - "Training language models to follow instructions" (Ouyang et al., 2022)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.nn.utils import clip_grad_norm_
from transformers import AutoModelForCausalLM, AutoTokenizer

from .value_head import ValueHead, add_value_head, get_value_head_output
from .reward_model import RewardModel


@dataclass
class PPOConfig:
    """PPO 训练配置"""

    # PPO 超参数
    learning_rate: float = 1.5e-5           # 学习率
    clip_range: float = 0.2                 # ⭐ PPO 裁剪范围
    kl_penalty: float = 0.1                 # KL 散度惩罚系数
    gamma: float = 1.0                      # 折扣因子
    lam: float = 0.95                       # GAE lambda
    ppo_epochs: int = 4                     # 每批数据的 PPO 更新轮数
    max_grad_norm: float = 0.5             # 梯度裁剪
    vf_coef: float = 0.5                   # 价值损失系数
    ent_coef: float = 0.01                 # 熵损失系数

    # 生成参数
    max_new_tokens: int = 128              # 最大生成长度
    temperature: float = 1.0               # 生成温度
    top_k: int = 50                        # Top-K 采样
    top_p: float = 0.9                     # Top-P 采样
    do_sample: bool = True                 # 是否采样

    # 训练参数
    batch_size: int = 16                   # 批大小
    mini_batch_size: int = 4               # 小批大小
    num_steps: int = 1000                  # 总训练步数
    save_steps: int = 100                  # 保存间隔
    logging_steps: int = 10                # 日志间隔

    # 其他
    output_dir: str = "./ppo_output"       # 输出目录
    device: str = "auto"                   # 设备


@dataclass
class PPOStats:
    """PPO 训练统计"""

    policy_loss: float = 0.0
    value_loss: float = 0.0
    entropy_loss: float = 0.0
    total_loss: float = 0.0
    kl_divergence: float = 0.0
    clip_fraction: float = 0.0
    mean_reward: float = 0.0
    mean_advantage: float = 0.0
    explained_variance: float = 0.0


class PPOTrainer:
    """
    PPO 训练器

    ⭐ PPO 训练流程:
    1. 使用策略模型生成回答
    2. 使用奖励模型评分
    3. 计算 KL 散度惩罚
    4. 使用 GAE 计算优势估计
    5. 使用 PPO 裁剪目标更新策略

    💡 关键组件:
    - Policy Model: 当前训练的模型（带 Value Head）
    - Reference Model: 原始预训练模型（冻结，用于 KL 计算）
    - Reward Model: 评分模型

    使用示例:
        config = PPOConfig(learning_rate=1.5e-5, clip_range=0.2)
        trainer = PPOTrainer(config)

        # 加载模型
        trainer.setup_models("gpt2")

        # 训练
        prompts = ["Tell me about AI", "What is deep learning?"]
        trainer.train(prompts)
    """

    def __init__(self, config: PPOConfig):
        self.config = config

        # 设备设置
        if config.device == "auto":
            self.device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            )
        else:
            self.device = torch.device(config.device)

        # 模型（延迟初始化）
        self.policy_model = None       # 策略模型（带 Value Head）
        self.ref_model = None          # 参考模型（冻结）
        self.reward_model = None       # 奖励模型
        self.tokenizer = None

        # 优化器
        self.optimizer = None

        # 训练状态
        self.global_step = 0
        self.stats_history = defaultdict(list)

    def setup_models(
        self,
        model_name: str,
        reward_model_name: Optional[str] = None,
    ):
        """
        设置所有模型

        ⭐ 需要三个模型:
        1. Policy Model: 当前策略，带 Value Head，参与训练
        2. Reference Model: 原始模型，冻结，用于 KL 计算
        3. Reward Model: 评分模型，冻结

        Args:
            model_name: 策略模型名称
            reward_model_name: 奖励模型名称（可选）
        """
        print(f"加载模型: {model_name}")

        # 加载分词器
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # 加载策略模型并添加 Value Head
        policy = AutoModelForCausalLM.from_pretrained(model_name)
        self.policy_model = add_value_head(policy).to(self.device)

        # 加载参考模型（冻结）
        ref = AutoModelForCausalLM.from_pretrained(model_name)
        self.ref_model = ref.to(self.device)
        self.ref_model.eval()
        for param in self.ref_model.parameters():
            param.requires_grad = False

        # 加载奖励模型
        if reward_model_name:
            self.reward_model = RewardModel.from_pretrained(
                reward_model_name,
                device=str(self.device),
            )
        else:
            # 使用默认的长度奖励函数
            from .reward_model import create_length_reward_fn
            self.reward_model = RewardModel.from_custom_fn(
                create_length_reward_fn()
            )

        # 设置优化器
        # ⭐ 只优化策略模型的参数（包括 Value Head）
        self.optimizer = AdamW(
            self.policy_model.parameters(),
            lr=self.config.learning_rate,
        )

        self._print_model_info()

    def _print_model_info(self):
        """打印模型信息"""
        policy_params = sum(p.numel() for p in self.policy_model.parameters())
        trainable_params = sum(
            p.numel() for p in self.policy_model.parameters()
            if p.requires_grad
        )
        print(f"策略模型参数量: {policy_params:,}")
        print(f"可训练参数量: {trainable_params:,}")
        print(f"设备: {self.device}")

    def train(self, prompts: List[str], num_steps: Optional[int] = None):
        """
        执行 PPO 训练

        ⭐ 训练循环:
        对每个训练步:
            1. 从提示词池中采样一批提示词
            2. 使用策略模型生成回答
            3. 计算奖励
            4. 计算 KL 散度
            5. 计算 GAE 优势估计
            6. 使用 PPO 更新策略

        Args:
            prompts: 提示词列表
            num_steps: 训练步数（覆盖配置）
        """
        if self.policy_model is None:
            raise ValueError("请先调用 setup_models() 设置模型")

        num_steps = num_steps or self.config.num_steps

        print(f"\n开始 PPO 训练，共 {num_steps} 步")
        print("=" * 60)

        for step in range(num_steps):
            # 采样一批提示词
            batch_prompts = self._sample_prompts(prompts, self.config.batch_size)

            # 执行一步 PPO 更新
            stats = self.step(batch_prompts)

            # 记录统计
            self._log_stats(stats)

            # 日志
            if step % self.config.logging_steps == 0:
                self._print_stats(step, stats)

            self.global_step += 1

        print("\n" + "=" * 60)
        print("PPO 训练完成!")

    def step(self, prompts: List[str]) -> PPOStats:
        """
        执行一步 PPO 更新

        ⭐ 这是 PPO 的核心训练步骤

        Args:
            prompts: 提示词列表

        Returns:
            PPOStats 训练统计
        """
        # ========== 阶段 1: 生成回答 ==========
        responses, old_logprobs = self._generate(prompts)

        # ========== 阶段 2: 计算奖励 ==========
        # 拼接 prompt + response
        texts = [p + r for p, r in zip(prompts, responses)]
        rewards = self.reward_model.score(texts).to(self.device)

        # ========== 阶段 3: 计算 KL 散度 ==========
        kl_div = self._compute_kl_divergence(prompts, responses)

        # KL 惩罚后的奖励
        total_rewards = rewards - self.config.kl_penalty * kl_div

        # ========== 阶段 4: 计算价值估计 ==========
        values = self._compute_values(prompts, responses)

        # ========== 阶段 5: 计算 GAE ==========
        # 对于单步 RL，简化 GAE 计算
        advantages, returns = self._compute_gae(total_rewards, values)

        # ========== 阶段 6: PPO 更新 ==========
        stats = self._ppo_update(
            prompts, responses, old_logprobs, advantages, returns, values
        )

        # 更新统计
        stats.mean_reward = rewards.mean().item()
        stats.kl_divergence = kl_div.mean().item()
        stats.mean_advantage = advantages.mean().item()

        return stats

    def _generate(
        self, prompts: List[str]
    ) -> Tuple[List[str], torch.Tensor]:
        """
        使用策略模型生成回答

        Args:
            prompts: 提示词列表

        Returns:
            (responses, logprobs): 回答列表和对数概率
        """
        self.policy_model.eval()

        # Tokenize 提示词
        inputs = self.tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
        ).to(self.device)

        prompt_length = inputs["input_ids"].shape[1]

        with torch.no_grad():
            # 生成回答
            outputs = self.policy_model.generate(
                **inputs,
                max_new_tokens=self.config.max_new_tokens,
                temperature=self.config.temperature,
                top_k=self.config.top_k,
                top_p=self.config.top_p,
                do_sample=self.config.do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
            )

            # 计算对数概率
            logits = self.policy_model(
                input_ids=outputs,
            ).logits

            # 只取生成部分的 logits
            gen_logits = logits[:, prompt_length - 1:-1, :]
            gen_tokens = outputs[:, prompt_length:]

            # 计算 log 概率
            logprobs = F.log_softmax(gen_logits, dim=-1)
            token_logprobs = logprobs.gather(
                2, gen_tokens.unsqueeze(-1)
            ).squeeze(-1)

        # 解码回答
        responses = self.tokenizer.batch_decode(
            gen_tokens,
            skip_special_tokens=True,
        )

        return responses, token_logprobs

    def _compute_kl_divergence(
        self,
        prompts: List[str],
        responses: List[str],
    ) -> torch.Tensor:
        """
        计算策略模型和参考模型之间的 KL 散度

        ⭐ KL 散度的作用:
        - 防止策略偏离原始模型太远
        - 保持生成质量的基本底线
        - 稳定训练过程

        KL(π || π_ref) = E[log π(a|s) - log π_ref(a|s)]
        """
        # 拼接 prompt + response
        texts = [p + r for p, r in zip(prompts, responses)]

        # Tokenize
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
        ).to(self.device)

        prompt_length = self.tokenizer(
            prompts[0],
            return_tensors="pt",
        )["input_ids"].shape[1]

        # 策略模型的 logits
        with torch.no_grad():
            policy_logits = self.policy_model(**inputs).logits
            ref_logits = self.ref_model(**inputs).logits

        # 只取生成部分
        policy_logits = policy_logits[:, prompt_length - 1:-1, :]
        ref_logits = ref_logits[:, prompt_length - 1:-1, :]

        # 计算 KL 散度
        policy_logprobs = F.log_softmax(policy_logits, dim=-1)
        ref_logprobs = F.log_softmax(ref_logits, dim=-1)

        # KL = sum(π * (log π - log π_ref))
        policy_probs = torch.exp(policy_logprobs)
        kl_div = (policy_probs * (policy_logprobs - ref_logprobs)).sum(dim=-1)

        # 返回平均 KL
        return kl_div.mean(dim=-1)

    def _compute_values(
        self,
        prompts: List[str],
        responses: List[str],
    ) -> torch.Tensor:
        """
        计算状态价值估计

        Returns:
            values: shape (batch_size,)
        """
        texts = [p + r for p, r in zip(prompts, responses)]

        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
        ).to(self.device)

        # 获取 Value Head 输出
        with torch.no_grad():
            values = get_value_head_output(
                self.policy_model,
                inputs["input_ids"],
                inputs["attention_mask"],
            )

        # 取最后一个 token 的价值作为序列价值
        return values[:, -1]

    def _compute_gae(
        self,
        rewards: torch.Tensor,
        values: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        计算 GAE (Generalized Advantage Estimation)

        ⭐ GAE 公式:
        A_t = Σ_{l=0}^{T-t} (γλ)^l * δ_{t+l}

        其中 δ_t = r_t + γ * V(s_{t+1}) - V(s_t) 是 TD 误差

        对于单步 RL（每个 episode 只有一个 action）:
        - A = R - V(s)
        - return = R

        Args:
            rewards: 奖励, shape (batch_size,)
            values: 价值估计, shape (batch_size,)

        Returns:
            (advantages, returns)
        """
        # 单步 RL 的简化计算
        advantages = rewards - values
        returns = rewards

        # 归一化优势
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        return advantages, returns

    def _ppo_update(
        self,
        prompts: List[str],
        responses: List[str],
        old_logprobs: torch.Tensor,
        advantages: torch.Tensor,
        returns: torch.Tensor,
        old_values: torch.Tensor,
    ) -> PPOStats:
        """
        执行 PPO 更新

        ⭐ PPO 裁剪目标:
        L^{CLIP} = E[min(r_t * A_t, clip(r_t, 1-ε, 1+ε) * A_t)]

        其中:
        - r_t = exp(log π_new - log π_old) 是概率比
        - A_t 是优势估计
        - ε 是裁剪范围

        如果 ratio 超出 [1-ε, 1+ε]，则被裁剪，防止策略更新过大。
        """
        self.policy_model.train()

        stats = PPOStats()

        for epoch in range(self.config.ppo_epochs):
            # 前向传播
            texts = [p + r for p, r in zip(prompts, responses)]
            inputs = self.tokenizer(
                texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
            ).to(self.device)

            prompt_length = self.tokenizer(
                prompts[0],
                return_tensors="pt",
            )["input_ids"].shape[1]

            # 计算当前策略的 logits 和价值
            outputs = self.policy_model(**inputs)
            logits = outputs.logits[:, prompt_length - 1:-1, :]
            values = get_value_head_output(
                self.policy_model,
                inputs["input_ids"],
                inputs["attention_mask"],
            )[:, -1]

            # 计算 log 概率
            logprobs = F.log_softmax(logits, dim=-1)
            gen_tokens = inputs["input_ids"][:, prompt_length:]
            new_logprobs = logprobs.gather(
                2, gen_tokens.unsqueeze(-1)
            ).squeeze(-1)

            # ⭐ 计算概率比 r_t = exp(log π_new - log π_old)
            # 注意: old_logprobs 可能维度不匹配，需要处理
            min_len = min(new_logprobs.shape[1], old_logprobs.shape[1])
            new_lp = new_logprobs[:, :min_len].mean(dim=-1)
            old_lp = old_logprobs[:, :min_len].mean(dim=-1)
            ratio = torch.exp(new_lp - old_lp)

            # ⭐ PPO 裁剪目标
            pg_loss1 = -advantages * ratio
            pg_loss2 = -advantages * torch.clamp(
                ratio,
                1 - self.config.clip_range,
                1 + self.config.clip_range,
            )
            policy_loss = torch.max(pg_loss1, pg_loss2).mean()

            # 价值损失
            value_loss = F.mse_loss(values, returns)

            # 熵损失（鼓励探索）
            entropy = -(torch.exp(logprobs) * logprobs).sum(dim=-1).mean()
            entropy_loss = -entropy

            # 总损失
            loss = (
                policy_loss
                + self.config.vf_coef * value_loss
                + self.config.ent_coef * entropy_loss
            )

            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()
            clip_grad_norm_(
                self.policy_model.parameters(),
                self.config.max_grad_norm,
            )
            self.optimizer.step()

            # 记录统计
            with torch.no_grad():
                clip_fraction = (
                    torch.abs(ratio - 1) > self.config.clip_range
                ).float().mean().item()

            stats.policy_loss = policy_loss.item()
            stats.value_loss = value_loss.item()
            stats.entropy_loss = entropy_loss.item()
            stats.total_loss = loss.item()
            stats.clip_fraction = clip_fraction

        return stats

    def _sample_prompts(
        self, prompts: List[str], batch_size: int
    ) -> List[str]:
        """从提示词池中随机采样"""
        import random
        return random.choices(prompts, k=batch_size)

    def _log_stats(self, stats: PPOStats):
        """记录训练统计"""
        self.stats_history["policy_loss"].append(stats.policy_loss)
        self.stats_history["value_loss"].append(stats.value_loss)
        self.stats_history["total_loss"].append(stats.total_loss)
        self.stats_history["kl_divergence"].append(stats.kl_divergence)
        self.stats_history["mean_reward"].append(stats.mean_reward)
        self.stats_history["clip_fraction"].append(stats.clip_fraction)

    def _print_stats(self, step: int, stats: PPOStats):
        """打印训练统计"""
        print(
            f"Step {step:4d} | "
            f"Loss: {stats.total_loss:.4f} | "
            f"Policy: {stats.policy_loss:.4f} | "
            f"Value: {stats.value_loss:.4f} | "
            f"Reward: {stats.mean_reward:.4f} | "
            f"KL: {stats.kl_divergence:.4f} | "
            f"Clip: {stats.clip_fraction:.2%}"
        )

    def generate(self, prompts: List[str]) -> List[str]:
        """
        使用策略模型生成回答

        Args:
            prompts: 提示词列表

        Returns:
            回答列表
        """
        responses, _ = self._generate(prompts)
        return responses

    def save(self, path: str):
        """保存模型"""
        import os
        os.makedirs(path, exist_ok=True)
        self.policy_model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)
        print(f"模型已保存到: {path}")
