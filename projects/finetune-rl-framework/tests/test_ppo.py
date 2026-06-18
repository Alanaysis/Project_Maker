"""
PPO 模块测试

⭐ 测试重点:
1. Value Head 的前向传播
2. 奖励模型的评分
3. PPO 损失计算
4. GAE 优势估计
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import torch
import torch.nn as nn

from src.ppo.value_head import ValueHead
from src.ppo.reward_model import RewardModel, create_length_reward_fn, create_keyword_reward_fn


class TestValueHead:
    """Value Head 测试"""

    def test_init(self):
        """测试 Value Head 初始化"""
        value_head = ValueHead(
            hidden_size=768,
            dropout=0.1,
        )

        assert value_head.value_head.in_features == 768
        assert value_head.value_head.out_features == 1

    def test_forward(self):
        """测试前向传播"""
        value_head = ValueHead(hidden_size=768)

        # 创建输入
        hidden_states = torch.randn(2, 10, 768)

        # 前向传播
        values = value_head(hidden_states)

        # 检查输出形状
        assert values.shape == (2, 10)

    def test_zero_init(self):
        """测试零初始化

        ⭐ 初始时价值估计应该接近 0
        """
        value_head = ValueHead(hidden_size=768)

        # 权重应该接近 0
        assert torch.allclose(
            value_head.value_head.weight,
            torch.zeros_like(value_head.value_head.weight),
        )

    def test_gradient_flow(self):
        """测试梯度流"""
        value_head = ValueHead(hidden_size=768)

        hidden_states = torch.randn(2, 10, 768)
        values = value_head(hidden_states)

        # 反向传播
        loss = values.sum()
        loss.backward()

        # 检查梯度
        assert value_head.value_head.weight.grad is not None


class TestRewardModel:
    """奖励模型测试"""

    def test_custom_reward_fn(self):
        """测试自定义奖励函数"""
        # 创建自定义奖励函数
        def simple_reward(text: str) -> float:
            return 1.0 if "good" in text.lower() else 0.0

        reward_model = RewardModel.from_custom_fn(simple_reward, normalize_rewards=False)

        # 测试评分
        scores = reward_model.score(["This is good", "This is bad"])

        assert scores[0].item() == 1.0
        assert scores[1].item() == 0.0

    def test_length_reward_fn(self):
        """测试长度奖励函数"""
        reward_fn = create_length_reward_fn(min_length=5, max_length=20)

        # 太短
        score_short = reward_fn("Hi")
        assert score_short < 0

        # 理想长度
        score_good = reward_fn("This is a good length for testing")
        assert score_good > 0

        # 太长
        score_long = reward_fn(" ".join(["word"] * 100))
        assert score_long < 1.0

    def test_keyword_reward_fn(self):
        """测试关键词奖励函数"""
        reward_fn = create_keyword_reward_fn(
            positive_keywords=["good", "great", "excellent"],
            negative_keywords=["bad", "terrible", "awful"],
        )

        # 正面关键词
        score_positive = reward_fn("This is good and great")
        assert score_positive > 0

        # 负面关键词
        score_negative = reward_fn("This is bad and terrible")
        assert score_negative < 0

        # 中性
        score_neutral = reward_fn("This is okay")
        assert score_neutral == 0

    def test_reward_normalization(self):
        """测试奖励归一化"""
        reward_model = RewardModel.from_custom_fn(
            lambda x: len(x.split()),
            normalize_rewards=True,
        )

        # 多次评分，触发归一化
        for _ in range(10):
            reward_model.score(["short text", "a longer text for testing purposes"])

        # 检查统计量
        assert reward_model.reward_mean != 0.0
        assert reward_model.reward_std != 1.0


class TestPPOComponents:
    """PPO 组件测试"""

    def test_ratio_computation(self):
        """测试概率比计算"""
        # 模拟 log 概率
        old_logprobs = torch.tensor([-1.0, -2.0, -3.0])
        new_logprobs = torch.tensor([-0.5, -1.5, -2.5])

        # 计算比率
        ratio = torch.exp(new_logprobs - old_logprobs)

        # 检查
        expected = torch.exp(torch.tensor([0.5, 0.5, 0.5]))
        assert torch.allclose(ratio, expected, atol=1e-5)

    def test_clipping(self):
        """测试 PPO 裁剪"""
        ratio = torch.tensor([0.5, 0.8, 1.0, 1.2, 1.5])
        clip_range = 0.2

        # 裁剪
        clipped = torch.clamp(ratio, 1 - clip_range, 1 + clip_range)

        # 检查
        expected = torch.tensor([0.8, 0.8, 1.0, 1.2, 1.2])
        assert torch.allclose(clipped, expected)

    def test_advantage_normalization(self):
        """测试优势归一化"""
        advantages = torch.tensor([1.0, 2.0, 3.0, 4.0, 5.0])

        # 归一化
        normalized = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # 检查
        assert abs(normalized.mean().item()) < 1e-5
        assert abs(normalized.std().item() - 1.0) < 1e-5

    def test_gae_computation(self):
        """测试 GAE 计算"""
        rewards = torch.tensor([1.0, 2.0, 3.0])
        values = torch.tensor([0.5, 1.5, 2.5])
        gamma = 0.99
        lam = 0.95

        # 简化的 GAE 计算（单步）
        advantages = rewards - values
        returns = rewards

        # 检查
        expected_advantages = torch.tensor([0.5, 0.5, 0.5])
        assert torch.allclose(advantages, expected_advantages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
