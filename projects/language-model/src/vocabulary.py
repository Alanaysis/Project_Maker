"""词汇表模块 - 处理分词和词汇映射"""

from typing import List, Dict, Optional
from collections import Counter


class Vocabulary:
    """词汇表，管理词到ID的映射"""

    # 特殊标记
    PAD = "<PAD>"  # 填充标记
    UNK = "<UNK>"  # 未知词标记
    BOS = "<BOS>"  # 句子开始标记
    EOS = "<EOS>"  # 句子结束标记

    SPECIAL_TOKENS = [PAD, UNK, BOS, EOS]

    def __init__(self, min_freq: int = 1):
        """
        初始化词汇表

        Args:
            min_freq: 最小词频，低于此频率的词将被映射为 UNK
        """
        self.min_freq = min_freq
        self._token2id: Dict[str, int] = {}
        self._id2token: Dict[int, str] = {}
        self._token_freq: Counter = Counter()
        self._built = False

        # 初始化特殊标记
        for i, token in enumerate(self.SPECIAL_TOKENS):
            self._token2id[token] = i
            self._id2token[i] = token

    @property
    def pad_id(self) -> int:
        return self._token2id[self.PAD]

    @property
    def unk_id(self) -> int:
        return self._token2id[self.UNK]

    @property
    def bos_id(self) -> int:
        return self._token2id[self.BOS]

    @property
    def eos_id(self) -> int:
        return self._token2id[self.EOS]

    @property
    def size(self) -> int:
        """词汇表大小"""
        return len(self._token2id)

    def build(self, corpus: List[List[str]]) -> "Vocabulary":
        """
        从语料库构建词汇表

        Args:
            corpus: 分词后的语料库，每个元素是一个词列表

        Returns:
            self，支持链式调用
        """
        # 统计词频
        self._token_freq = Counter()
        for sentence in corpus:
            self._token_freq.update(sentence)

        # 清空非特殊标记的映射
        self._token2id = {}
        self._id2token = {}
        for i, token in enumerate(self.SPECIAL_TOKENS):
            self._token2id[token] = i
            self._id2token[i] = token

        # 按词频排序，添加到词汇表
        idx = len(self.SPECIAL_TOKENS)
        for token, freq in self._token_freq.most_common():
            if freq >= self.min_freq and token not in self._token2id:
                self._token2id[token] = idx
                self._id2token[idx] = token
                idx += 1

        self._built = True
        return self

    def encode(self, tokens: List[str]) -> List[int]:
        """
        将词列表转换为ID列表

        Args:
            tokens: 词列表

        Returns:
            ID列表
        """
        unk_id = self.unk_id
        token2id = self._token2id
        return [token2id.get(t, unk_id) for t in tokens]

    def decode(self, ids: List[int]) -> List[str]:
        """
        将ID列表转换为词列表

        Args:
            ids: ID列表

        Returns:
            词列表
        """
        id2token = self._id2token
        unk = self.UNK
        return [id2token.get(i, unk) for i in ids]

    def get_id(self, token: str) -> int:
        """获取词的ID，未知词返回 UNK ID"""
        return self._token2id.get(token, self.unk_id)

    def get_token(self, idx: int) -> str:
        """获取ID对应的词"""
        return self._id2token.get(idx, self.UNK)

    def get_freq(self, token: str) -> int:
        """获取词的频率"""
        return self._token_freq.get(token, 0)

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        简单分词：按空格分割，转换为小写

        Args:
            text: 输入文本

        Returns:
            词列表
        """
        return text.lower().split()
