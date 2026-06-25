"""
降采样（Subsampling）模块

高频词（如 "the", "a", "is"）在语料中出现次数远多于低频词，
但它们携带的语义信息较少。降采样通过概率性地丢弃高频词来：
1. 加速训练
2. 提升低频词的表示质量
3. 平衡词频差异

采样概率公式（来自原始论文）：
P(keep) = sqrt(t / f(w)) + t / f(w)

其中 f(w) 是词频（归一化），t 是阈值（通常 1e-3 到 1e-5）。
"""

import numpy as np
from typing import List, Dict


class SubSampler:
    """降采样器

    根据词频概率性地丢弃高频词

    Attributes:
        threshold: 降采样阈值
        keep_probs: 保留概率字典
    """

    def __init__(self, word_freq: Dict[str, int], total_words: int,
                 threshold: float = 1e-3):
        """初始化降采样器

        Args:
            word_freq: 词频字典
            total_words: 总词数
            threshold: 降采样阈值，越大丢弃越多
        """
        self.threshold = threshold
        self.keep_probs: Dict[str, float] = {}

        if total_words == 0 or threshold <= 0:
            # 不降采样
            for word in word_freq:
                self.keep_probs[word] = 1.0
            return

        for word, freq in word_freq.items():
            # 归一化频率
            f = freq / total_words

            # 计算保留概率
            # P(keep) = sqrt(t/f) + t/f
            # 简化：P(keep) = min(1, (sqrt(f/t) + 1) * t/f)
            # 原始论文公式：
            prob = (np.sqrt(f / threshold) + 1) * (threshold / f)
            self.keep_probs[word] = min(1.0, prob)

    def should_keep(self, word: str) -> bool:
        """判断是否保留该词

        Args:
            word: 输入词

        Returns:
            是否保留
        """
        if word not in self.keep_probs:
            return True  # 未知词保留

        return np.random.random() < self.keep_probs[word]

    def subsample_sentence(self, sentence: List[str]) -> List[str]:
        """对句子进行降采样

        Args:
            sentence: 分词后的句子

        Returns:
            降采样后的句子
        """
        return [word for word in sentence if self.should_keep(word)]

    def subsample_corpus(self, corpus: List[List[str]]) -> List[List[str]]:
        """对整个语料进行降采样

        Args:
            corpus: 分词后的语料

        Returns:
            降采样后的语料（移除空句子）
        """
        result = []
        for sentence in corpus:
            subsampled = self.subsample_sentence(sentence)
            if len(subsampled) > 0:
                result.append(subsampled)
        return result

    def get_keep_probability(self, word: str) -> float:
        """获取词的保留概率

        Args:
            word: 输入词

        Returns:
            保留概率
        """
        return self.keep_probs.get(word, 1.0)
