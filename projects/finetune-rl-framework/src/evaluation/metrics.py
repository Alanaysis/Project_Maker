"""
评估指标模块

本模块提供用于评估大模型训练效果的指标。

⭐ 常用评估指标:
    1. Perplexity (困惑度): 衡量语言模型的预测能力
    2. BLEU: 衡量生成文本与参考文本的相似度
    3. ROUGE: 衡量生成文本的召回率
    4. KL 散度: 衡量策略偏离程度
    5. 奖励统计: 衡量 RLHF 训练效果
"""

from typing import Dict, List, Optional, Union
from collections import Counter
import math

import torch
import torch.nn.functional as F


def compute_perplexity(
    model,
    tokenizer,
    texts: List[str],
    max_length: int = 512,
    device: str = "cpu",
) -> float:
    """
    计算困惑度 (Perplexity)

    ⭐ 困惑度是衡量语言模型质量的核心指标
    PPL = exp(-1/N * Σ log P(x_t | x_<t))

    困惑度越低，模型的预测能力越强

    Args:
        model: 语言模型
        tokenizer: 分词器
        texts: 文本列表
        max_length: 最大序列长度
        device: 设备

    Returns:
        平均困惑度
    """
    model.eval()
    total_loss = 0.0
    total_tokens = 0

    with torch.no_grad():
        for text in texts:
            # Tokenize
            inputs = tokenizer(
                text,
                return_tensors="pt",
                max_length=max_length,
                truncation=True,
            ).to(device)

            # 前向传播
            outputs = model(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                labels=inputs["input_ids"],
            )

            # 累加损失
            total_loss += outputs.loss.item() * inputs["input_ids"].numel()
            total_tokens += inputs["input_ids"].numel()

    # 计算平均困惑度
    avg_loss = total_loss / total_tokens
    perplexity = math.exp(avg_loss)

    return perplexity


def compute_bleu(
    predictions: List[str],
    references: List[str],
    max_n: int = 4,
) -> Dict[str, float]:
    """
    计算 BLEU 分数

    ⭐ BLEU (Bilingual Evaluation Understudy) 是机器翻译的标准评估指标
    BLEU = BP * exp(Σ w_n * log p_n)

    其中:
    - BP 是长度惩罚因子
    - p_n 是 n-gram 精度
    - w_n 是权重（通常均匀分布）

    Args:
        predictions: 预测文本列表
        references: 参考文本列表
        max_n: 最大 n-gram

    Returns:
        BLEU 分数字典
    """
    scores = {}

    for n in range(1, max_n + 1):
        total_matches = 0
        total_count = 0

        for pred, ref in zip(predictions, references):
            pred_ngrams = _get_ngrams(pred, n)
            ref_ngrams = _get_ngrams(ref, n)

            # 计算匹配的 n-gram 数量
            matches = 0
            for ngram, count in pred_ngrams.items():
                matches += min(count, ref_ngrams.get(ngram, 0))

            total_matches += matches
            total_count += sum(pred_ngrams.values())

        # 计算精度
        if total_count > 0:
            precision = total_matches / total_count
        else:
            precision = 0.0

        scores[f"bleu-{n}"] = precision

    # 计算几何平均
    if all(s > 0 for s in scores.values()):
        geometric_mean = math.exp(
            sum(math.log(s) for s in scores.values()) / len(scores)
        )
    else:
        geometric_mean = 0.0

    # 长度惩罚
    pred_len = sum(len(p.split()) for p in predictions)
    ref_len = sum(len(r.split()) for r in references)

    if pred_len > 0:
        bp = min(1.0, math.exp(1 - ref_len / pred_len))
    else:
        bp = 0.0

    scores["bleu"] = bp * geometric_mean

    return scores


def _get_ngrams(text: str, n: int) -> Counter:
    """获取文本的 n-gram 计数"""
    words = text.split()
    ngrams = Counter()
    for i in range(len(words) - n + 1):
        ngram = tuple(words[i:i + n])
        ngrams[ngram] += 1
    return ngrams


def compute_rouge(
    predictions: List[str],
    references: List[str],
) -> Dict[str, float]:
    """
    计算 ROUGE 分数

    ⭐ ROUGE (Recall-Oriented Understudy for Gisting Evaluation)
    主要用于文本摘要评估

    ROUGE-N: 基于 n-gram 的召回率
    ROUGE-L: 基于最长公共子序列

    Args:
        predictions: 预测文本列表
        references: 参考文本列表

    Returns:
        ROUGE 分数字典
    """
    rouge_1_scores = []
    rouge_2_scores = []
    rouge_l_scores = []

    for pred, ref in zip(predictions, references):
        # ROUGE-1
        rouge_1 = _compute_rouge_n(pred, ref, n=1)
        rouge_1_scores.append(rouge_1)

        # ROUGE-2
        rouge_2 = _compute_rouge_n(pred, ref, n=2)
        rouge_2_scores.append(rouge_2)

        # ROUGE-L
        rouge_l = _compute_rouge_l(pred, ref)
        rouge_l_scores.append(rouge_l)

    return {
        "rouge-1": sum(rouge_1_scores) / len(rouge_1_scores),
        "rouge-2": sum(rouge_2_scores) / len(rouge_2_scores),
        "rouge-l": sum(rouge_l_scores) / len(rouge_l_scores),
    }


def _compute_rouge_n(prediction: str, reference: str, n: int) -> float:
    """计算 ROUGE-N 分数"""
    pred_ngrams = _get_ngrams(prediction, n)
    ref_ngrams = _get_ngrams(reference, n)

    if not ref_ngrams:
        return 0.0

    # 计算匹配数
    matches = 0
    for ngram, count in ref_ngrams.items():
        matches += min(count, pred_ngrams.get(ngram, 0))

    # 召回率
    recall = matches / sum(ref_ngrams.values())

    return recall


def _compute_rouge_l(prediction: str, reference: str) -> float:
    """计算 ROUGE-L 分数（基于最长公共子序列）"""
    pred_words = prediction.split()
    ref_words = reference.split()

    # 计算 LCS 长度
    lcs_length = _lcs_length(pred_words, ref_words)

    if not ref_words:
        return 0.0

    # 召回率
    recall = lcs_length / len(ref_words)

    return recall


def _lcs_length(x: List, y: List) -> int:
    """计算最长公共子序列长度"""
    m, n = len(x), len(y)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]


def compute_kl_divergence(
    policy_logprobs: torch.Tensor,
    ref_logprobs: torch.Tensor,
) -> torch.Tensor:
    """
    计算 KL 散度

    ⭐ KL(π || π_ref) = E[log π(a|s) - log π_ref(a|s)]

    用于衡量策略模型与参考模型的偏离程度

    Args:
        policy_logprobs: 策略模型的对数概率
        ref_logprobs: 参考模型的对数概率

    Returns:
        KL 散度
    """
    # KL = sum(π * (log π - log π_ref))
    policy_probs = torch.exp(policy_logprobs)
    kl = (policy_probs * (policy_logprobs - ref_logprobs)).sum(dim=-1)

    return kl.mean()


def compute_reward_stats(
    rewards: torch.Tensor,
) -> Dict[str, float]:
    """
    计算奖励统计信息

    Args:
        rewards: 奖励张量

    Returns:
        统计信息字典
    """
    return {
        "mean_reward": rewards.mean().item(),
        "std_reward": rewards.std().item(),
        "min_reward": rewards.min().item(),
        "max_reward": rewards.max().item(),
        "median_reward": rewards.median().item(),
    }


def compute_explained_variance(
    y_pred: torch.Tensor,
    y_true: torch.Tensor,
) -> float:
    """
    计算解释方差

    ⭐ 解释方差衡量价值函数的预测质量
    EV = 1 - Var(y_true - y_pred) / Var(y_true)

    值越接近 1，价值函数预测越准确

    Args:
        y_pred: 预测值
        y_true: 真实值

    Returns:
        解释方差
    """
    var_true = y_true.var()
    if var_true == 0:
        return 0.0

    return 1.0 - (y_true - y_pred).var() / var_true
