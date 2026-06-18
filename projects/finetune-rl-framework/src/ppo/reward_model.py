"""
奖励模型模块

⭐ 奖励模型在 RLHF 中的作用:
    奖励模型是 RLHF 训练的核心组件之一。
    它接收一个文本（通常是 prompt + response），
    输出一个标量分数，表示这个回答的质量。

💡 奖励模型的设计选择:
    1. 使用预训练的情感分析模型（简单但有效）
    2. 使用微调后的分类模型
    3. 使用 LLM 本身进行评分（Self-Rewarding）
    4. 使用规则和启发式方法

本模块提供:
    - 基于情感分析的简单奖励模型
    - 自定义奖励函数的接口
"""

from typing import Callable, Optional, Union, List

import torch
import torch.nn as nn
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class RewardModel:
    """
    奖励模型

    ⭐ 设计原则:
    1. 提供统一的评分接口
    2. 支持多种奖励信号来源
    3. 奖励归一化以稳定训练

    使用示例:
        # 使用预训练的情感模型
        reward_model = RewardModel.from_pretrained("lvwerra/distilbert-imdb")

        # 评分
        scores = reward_model.score(["This is great!", "This is terrible."])
    """

    def __init__(
        self,
        model: nn.Module,
        tokenizer,
        reward_fn: Optional[Callable] = None,
        normalize_rewards: bool = True,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.reward_fn = reward_fn
        self.normalize_rewards = normalize_rewards

        # 奖励统计（用于归一化）
        self.reward_mean = 0.0
        self.reward_std = 1.0
        self.reward_buffer = []

    @classmethod
    def from_pretrained(
        cls,
        model_name: str,
        normalize_rewards: bool = True,
        device: str = "auto",
    ) -> "RewardModel":
        """
        从预训练模型创建奖励模型

        Args:
            model_name: Hugging Face 模型名称
            normalize_rewards: 是否归一化奖励
            device: 设备

        Returns:
            RewardModel 实例
        """
        # 设备设置
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"

        # 加载分词器
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # 加载模型
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=1,  # 输出单个分数
        )
        model = model.to(device)
        model.eval()

        return cls(model, tokenizer, normalize_rewards=normalize_rewards)

    @classmethod
    def from_custom_fn(
        cls,
        reward_fn: Callable[[str], float],
        normalize_rewards: bool = True,
    ) -> "RewardModel":
        """
        使用自定义奖励函数创建奖励模型

        ⭐ 自定义奖励函数示例:
            - 长度惩罚: 短回答奖励高
            - 关键词奖励: 包含特定关键词奖励高
            - 格式奖励: 符合特定格式奖励高

        Args:
            reward_fn: 自定义奖励函数，输入文本，输出分数
            normalize_rewards: 是否归一化奖励

        Returns:
            RewardModel 实例
        """
        return cls(
            model=None,
            tokenizer=None,
            reward_fn=reward_fn,
            normalize_rewards=normalize_rewards,
        )

    def score(self, texts: Union[str, List[str]]) -> torch.Tensor:
        """
        对文本进行评分

        ⭐ 评分流程:
            1. Tokenize 输入文本
            2. 通过模型获取 logits
            3. 归一化奖励（可选）

        Args:
            texts: 输入文本或文本列表

        Returns:
            奖励分数, shape (batch_size,)
        """
        if isinstance(texts, str):
            texts = [texts]

        # 使用自定义奖励函数
        if self.reward_fn is not None:
            scores = torch.tensor(
                [self.reward_fn(text) for text in texts],
                dtype=torch.float32,
            )
        else:
            # 使用模型评分
            scores = self._model_score(texts)

        # 归一化
        if self.normalize_rewards:
            scores = self._normalize_rewards(scores)

        return scores

    def _model_score(self, texts: List[str]) -> torch.Tensor:
        """
        使用模型进行评分

        Args:
            texts: 文本列表

        Returns:
            奖励分数
        """
        # Tokenize
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        )
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        # 推理
        with torch.no_grad():
            outputs = self.model(**inputs)
            scores = outputs.logits.squeeze(-1)

        return scores

    def _normalize_rewards(self, rewards: torch.Tensor) -> torch.Tensor:
        """
        归一化奖励

        ⭐ 为什么要归一化?
            - 稳定训练: 避免奖励尺度变化过大
            - 改善收敛: 归一化后的奖励更易于优化

        使用运行均值和标准差进行归一化
        """
        # 更新奖励统计
        self.reward_buffer.extend(rewards.cpu().tolist())

        # 使用最近的奖励计算统计量
        if len(self.reward_buffer) > 100:
            self.reward_buffer = self.reward_buffer[-100:]

        self.reward_mean = sum(self.reward_buffer) / len(self.reward_buffer)
        self.reward_std = (
            sum((x - self.reward_mean) ** 2 for x in self.reward_buffer)
            / len(self.reward_buffer)
        ) ** 0.5 + 1e-8

        # 归一化
        return (rewards - self.reward_mean) / self.reward_std

    def update_stats(self, rewards: torch.Tensor):
        """更新奖励统计量"""
        self.reward_buffer.extend(rewards.cpu().tolist())
        if len(self.reward_buffer) > 1000:
            self.reward_buffer = self.reward_buffer[-1000:]

        self.reward_mean = sum(self.reward_buffer) / len(self.reward_buffer)
        self.reward_std = (
            sum((x - self.reward_mean) ** 2 for x in self.reward_buffer)
            / len(self.reward_buffer)
        ) ** 0.5 + 1e-8


def create_length_reward_fn(
    min_length: int = 20,
    max_length: int = 200,
) -> Callable[[str], float]:
    """
    创建基于长度的奖励函数

    💡 设计思路:
    - 太短的回答惩罚（不完整）
    - 中等长度的回答奖励（完整且简洁）
    - 太长的回答轻微惩罚（冗余）

    Args:
        min_length: 最小理想长度
        max_length: 最大理想长度

    Returns:
        奖励函数
    """
    def reward_fn(text: str) -> float:
        length = len(text.split())

        if length < min_length:
            # 太短，惩罚
            return -1.0 + (length / min_length)
        elif length <= max_length:
            # 理想长度，奖励
            return 1.0
        else:
            # 太长，轻微惩罚
            excess = (length - max_length) / max_length
            return max(0.0, 1.0 - excess * 0.5)

    return reward_fn


def create_keyword_reward_fn(
    positive_keywords: List[str],
    negative_keywords: List[str],
) -> Callable[[str], float]:
    """
    创建基于关键词的奖励函数

    Args:
        positive_keywords: 正面关键词列表
        negative_keywords: 负面关键词列表

    Returns:
        奖励函数
    """
    def reward_fn(text: str) -> float:
        text_lower = text.lower()
        score = 0.0

        for keyword in positive_keywords:
            if keyword.lower() in text_lower:
                score += 1.0

        for keyword in negative_keywords:
            if keyword.lower() in text_lower:
                score -= 1.0

        # 归一化到 [-1, 1] 范围
        max_score = len(positive_keywords) + len(negative_keywords)
        if max_score > 0:
            score = score / max_score

        return score

    return reward_fn
