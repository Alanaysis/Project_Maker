"""
负采样模块

实现负采样优化，将多分类问题转化为二分类问题
"""

import numpy as np
from typing import List, Optional


class NegativeSampler:
    """负采样器

    使用词频的 3/4 次方作为噪声分布进行负采样

    Attributes:
        table_size: 查找表大小
        table: 负采样查找表
    """

    def __init__(self, vocab_size: int, word_freqs: np.ndarray, table_size: int = 1000000):
        """初始化负采样器

        Args:
            vocab_size: 词汇表大小
            word_freqs: 词频数组（按索引顺序）
            table_size: 查找表大小
        """
        self.table_size = table_size
        self.vocab_size = vocab_size
        self.table = self._build_table(word_freqs)

    def _build_table(self, word_freqs: np.ndarray) -> np.ndarray:
        """构建负采样查找表

        Args:
            word_freqs: 词频数组

        Returns:
            负采样查找表
        """
        table = np.zeros(self.table_size, dtype=np.int32)

        # 使用词频的 3/4 次方
        powered = np.power(word_freqs.astype(np.float64), 0.75)
        total = powered.sum()

        if total == 0:
            # 如果所有词频都是0，均匀分布
            powered = np.ones_like(word_freqs)
            total = powered.sum()

        powered /= total

        # 构建累积分布
        cumsum = np.cumsum(powered)

        # 填充查找表
        j = 0
        for i in range(self.table_size):
            while j < len(cumsum) - 1 and i / self.table_size > cumsum[j]:
                j += 1
            table[i] = j

        return table

    def sample(self, positive: int, k: int) -> np.ndarray:
        """采样 k 个负样本

        Args:
            positive: 正样本的索引
            k: 负样本数量

        Returns:
            负样本索引数组
        """
        negatives = []
        max_attempts = k * 10  # 防止无限循环
        attempts = 0

        while len(negatives) < k and attempts < max_attempts:
            # 从查找表中随机采样
            idx = np.random.randint(0, self.table_size)
            neg = int(self.table[idx])

            # 确保不是正样本且不重复
            if neg != positive and neg not in negatives:
                negatives.append(neg)
            attempts += 1

        # 如果无法获得足够的唯一负样本，允许重复
        while len(negatives) < k:
            idx = np.random.randint(0, self.table_size)
            neg = int(self.table[idx])
            if neg != positive:
                negatives.append(neg)

        return np.array(negatives, dtype=np.int32)

    def sample_batch(self, positives: np.ndarray, k: int) -> np.ndarray:
        """批量采样负样本

        Args:
            positives: 正样本索引数组
            k: 每个正样本的负样本数量

        Returns:
            负样本索引矩阵 (len(positives), k)
        """
        batch_size = len(positives)
        negatives = np.zeros((batch_size, k), dtype=np.int32)

        for i in range(batch_size):
            negatives[i] = self.sample(positives[i], k)

        return negatives
