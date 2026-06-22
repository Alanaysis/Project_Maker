"""
词汇表管理模块

负责构建词汇表、词频统计、词索引映射
"""

from typing import List, Dict, Tuple, Optional
from collections import Counter
import numpy as np


class Vocabulary:
    """词汇表管理类

    Attributes:
        min_count: 最小词频阈值
        word2idx: 词到索引的映射
        idx2word: 索引到词的映射
        word_freq: 词频字典
        total_words: 总词数
    """

    def __init__(self, min_count: int = 5):
        """初始化词汇表

        Args:
            min_count: 最小词频，低于此频率的词将被过滤
        """
        self.min_count = min_count
        self.word2idx: Dict[str, int] = {}
        self.idx2word: Dict[int, str] = {}
        self.word_freq: Dict[str, int] = {}
        self.total_words: int = 0
        self._neg_table: Optional[np.ndarray] = None

    def build(self, corpus: List[List[str]]) -> None:
        """构建词汇表

        Args:
            corpus: 分词后的语料，每个元素是一个句子的词列表
        """
        # 统计词频
        counter = Counter()
        for sentence in corpus:
            counter.update(sentence)

        # 过滤低频词并建立映射
        self.word_freq = {}
        self.word2idx = {}
        self.idx2word = {}

        idx = 0
        for word, freq in counter.most_common():
            if freq >= self.min_count:
                self.word2idx[word] = idx
                self.idx2word[idx] = word
                self.word_freq[word] = freq
                idx += 1

        self.total_words = sum(self.word_freq.values())

    def __len__(self) -> int:
        """返回词汇表大小"""
        return len(self.word2idx)

    def __contains__(self, word: str) -> bool:
        """检查词是否在词汇表中"""
        return word in self.word2idx

    def get_idx(self, word: str) -> Optional[int]:
        """获取词的索引

        Args:
            word: 输入词

        Returns:
            词的索引，如果词不在词汇表中返回 None
        """
        return self.word2idx.get(word)

    def get_word(self, idx: int) -> Optional[str]:
        """获取索引对应的词

        Args:
            idx: 词索引

        Returns:
            对应的词，如果索引无效返回 None
        """
        return self.idx2word.get(idx)

    def get_freq(self, word: str) -> int:
        """获取词频

        Args:
            word: 输入词

        Returns:
            词频，如果词不在词汇表中返回 0
        """
        return self.word_freq.get(word, 0)

    def get_neg_table(self, table_size: int = 1000000) -> np.ndarray:
        """获取负采样查找表

        Args:
            table_size: 查找表大小

        Returns:
            负采样查找表
        """
        if self._neg_table is not None and len(self._neg_table) == table_size:
            return self._neg_table

        self._neg_table = self._build_neg_table(table_size)
        return self._neg_table

    def _build_neg_table(self, table_size: int) -> np.ndarray:
        """构建负采样查找表

        使用词频的 3/4 次方作为采样概率

        Args:
            table_size: 查找表大小

        Returns:
            负采样查找表
        """
        vocab_size = len(self)
        table = np.zeros(table_size, dtype=np.int32)

        # 计算采样概率
        freqs = np.zeros(vocab_size)
        for word, idx in self.word2idx.items():
            freqs[idx] = self.word_freq[word]

        # 使用 3/4 次方
        powered = np.power(freqs, 0.75)
        powered /= powered.sum()

        # 构建累积分布
        cumsum = np.cumsum(powered)

        # 填充查找表
        j = 0
        for i in range(table_size):
            while j < len(cumsum) - 1 and i / table_size > cumsum[j]:
                j += 1
            table[i] = j

        return table

    def get_word_freqs_array(self) -> np.ndarray:
        """获取词频数组（按索引顺序）

        Returns:
            词频数组
        """
        freqs = np.zeros(len(self))
        for word, idx in self.word2idx.items():
            freqs[idx] = self.word_freq[word]
        return freqs
