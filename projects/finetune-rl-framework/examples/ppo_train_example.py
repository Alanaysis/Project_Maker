"""
PPO 训练示例

⭐ 本示例展示 PPO 强化学习的基本流程

运行方式:
    python examples/ppo_train_example.py

💡 学习要点:
1. PPO 的训练循环
2. 奖励模型的作用
3. KL 散度惩罚的意义
4. 价值函数的作用

注意: 本示例使用简化模型，仅用于演示 PPO 的核心逻辑
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import torch
import torch.nn as nn
import torch.nn.functional as F

from src.ppo.value_head import ValueHead
from src.ppo.reward_model import RewardModel, create_length_reward_fn


def main():
    """PPO 训练示例"""

    print("=" * 60)
    print("PPO 训练示例")
    print("=" * 60)

    # ========== 1. 创建简单模型 ==========
    print("\n1. 创建模型...")

    class SimplePolicyModel(nn.Module):
        """简单的策略模型（用于演示）"""

        def __init__(self, vocab_size=100, hidden_size=64):
            super().__init__()
            self.embedding = nn.Embedding(vocab_size, hidden_size)
            self.linear = nn.Linear(hidden_size, hidden_size)
            self.output_head = nn.Linear(hidden_size, vocab_size)
            self.value_head = ValueHead(hidden_size)

        def forward(self, input_ids):
            x = self.embedding(input_ids)
            x = F.relu(self.linear(x))
            logits = self.output_head(x)
            values = self.value_head(x)
            return logits, values

        def generate(self, input_ids, max_new_tokens=10):
            """简单的生成函数"""
            generated = input_ids.clone()

            for _ in range(max_new_tokens):
                logits, _ = self.forward(generated)
                next_token_logits = logits[:, -1, :]

                # 贪心解码
                next_token = torch.argmax(next_token_logits, dim=-1, keepdim=True)
                generated = torch.cat([generated, next_token], dim=1)

            return generated

    policy_model = SimplePolicyModel()
    ref_model = SimplePolicyModel()  # 参考模型

    # 复制权重作为参考模型
    ref_model.load_state_dict(policy_model.state_dict())

    # 冻结参考模型
    for param in ref_model.parameters():
        param.requires_grad = False

    print(f"策略模型参数量: {sum(p.numel() for p in policy_model.parameters()):,}")
    print(f"参考模型参数量: {sum(p.numel() for p in ref_model.parameters()):,}")

    # ========== 2. 创建奖励模型 ==========
    print("\n2. 创建奖励模型...")

    reward_model = RewardModel.from_custom_fn(
        create_length_reward_fn(min_length=5, max_length=20),
        normalize_rewards=False,
    )

    print("奖励模型已创建（基于长度的奖励函数）")

    # ========== 3. 设置训练参数 ==========
    print("\n3. 设置训练参数...")

    # PPO 超参数
    learning_rate = 1e-4
    clip_range = 0.2
    kl_penalty = 0.1
    ppo_epochs = 4
    batch_size = 4
    num_steps = 10

    # 优化器
    optimizer = torch.optim.Adam(policy_model.parameters(), lr=learning_rate)

    print(f"学习率: {learning_rate}")
    print(f"裁剪范围: {clip_range}")
    print(f"KL 惩罚系数: {kl_penalty}")

    # ========== 4. 训练循环 ==========
    print("\n4. 开始训练...")

    # 提示词
    prompts = [
        torch.tensor([[1, 2, 3]]),  # 简单的 token 序列
        torch.tensor([[4, 5, 6]]),
        torch.tensor([[7, 8, 9]]),
        torch.tensor([[10, 11, 12]]),
    ]

    for step in range(num_steps):
        step_rewards = []
        step_losses = []

        for prompt in prompts:
            # ===== 阶段 1: 生成回答 =====
            with torch.no_grad():
                generated = policy_model.generate(prompt, max_new_tokens=10)
                old_logits, old_values = policy_model(generated)
                old_logprobs = F.log_softmax(old_logits, dim=-1)

                # 参考模型的 logits
                ref_logits, _ = ref_model(generated)
                ref_logprobs = F.log_softmax(ref_logits, dim=-1)

            # ===== 阶段 2: 计算奖励 =====
            # 使用生成长度作为简单奖励
            gen_length = generated.shape[1] - prompt.shape[1]
            reward = max(0, min(1.0, gen_length / 10.0))
            step_rewards.append(reward)

            # ===== 阶段 3: 计算 KL 散度 =====
            with torch.no_grad():
                policy_probs = torch.exp(old_logprobs)
                kl_div = (policy_probs * (old_logprobs - ref_logprobs)).sum(dim=-1).mean()

            # ===== 阶段 4: 计算总奖励 =====
            total_reward = reward - kl_penalty * kl_div.item()

            # ===== 阶段 5: PPO 更新 =====
            for _ in range(ppo_epochs):
                # 前向传播
                new_logits, new_values = policy_model(generated)
                new_logprobs = F.log_softmax(new_logits, dim=-1)

                # 计算概率比
                # 只取生成部分
                gen_start = prompt.shape[1]
                new_lp = new_logprobs[:, gen_start - 1:-1, :].mean(dim=-1)
                old_lp = old_logprobs[:, gen_start - 1:-1, :].mean(dim=-1)

                # 简化：使用平均 log 概率
                ratio = torch.exp(new_lp.mean() - old_lp.mean())

                # 优势估计
                advantage = total_reward - old_values[:, -1].mean()

                # PPO 裁剪
                pg_loss1 = -advantage * ratio
                pg_loss2 = -advantage * torch.clamp(ratio, 1 - clip_range, 1 + clip_range)
                policy_loss = torch.max(pg_loss1, pg_loss2)

                # 价值损失
                value_loss = F.mse_loss(new_values[:, -1].mean(), torch.tensor(total_reward))

                # 总损失
                loss = policy_loss + 0.5 * value_loss

                # 反向传播
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(policy_model.parameters(), 1.0)
                optimizer.step()

                step_losses.append(loss.item())

        # 打印统计
        avg_reward = sum(step_rewards) / len(step_rewards)
        avg_loss = sum(step_losses) / len(step_losses)

        if step % 2 == 0:
            print(
                f"Step {step:3d} | "
                f"Reward: {avg_reward:.4f} | "
                f"Loss: {avg_loss:.4f} | "
                f"KL: {kl_div.item():.4f}"
            )

    print("\n" + "=" * 60)
    print("训练完成!")
    print("=" * 60)

    # ========== 5. 测试生成 ==========
    print("\n5. 测试生成...")

    test_prompt = torch.tensor([[1, 2, 3]])
    generated = policy_model.generate(test_prompt, max_new_tokens=15)

    print(f"输入: {test_prompt.tolist()}")
    print(f"生成: {generated.tolist()}")
    print(f"生成长度: {generated.shape[1] - test_prompt.shape[1]} tokens")


if __name__ == "__main__":
    main()
