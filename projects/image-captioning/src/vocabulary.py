"""
Vocabulary - 词汇表管理

构建和管理图像描述任务的词汇表。
负责文本与索引之间的双向映射。

特殊标记：
- <pad>: 填充标记，用于批量处理时对齐序列长度
- <start>: 序列开始标记，指示解码器开始生成
- <end>: 序列结束标记，指示解码器停止生成
- <unk>: 未知词标记，处理词汇表外的词
"""

from collections import Counter
from typing import Optional


class Vocabulary:
    """词汇表，管理词到索引和索引到词的映射。"""

    # 特殊标记
    PAD_TOKEN = "<pad>"
    START_TOKEN = "<start>"
    END_TOKEN = "<end>"
    UNK_TOKEN = "<unk>"

    def __init__(self, min_freq: int = 1):
        """初始化词汇表。

        Args:
            min_freq: 最小词频，低于此频率的词将被忽略
        """
        self.min_freq = min_freq

        # 特殊标记固定在前4个位置
        self.word2idx: dict[str, int] = {
            self.PAD_TOKEN: 0,
            self.START_TOKEN: 1,
            self.END_TOKEN: 2,
            self.UNK_TOKEN: 3,
        }
        self.idx2word: dict[int, str] = {
            0: self.PAD_TOKEN,
            1: self.START_TOKEN,
            2: self.END_TOKEN,
            3: self.UNK_TOKEN,
        }
        self.word_freq: Counter = Counter()
        self._built = False

    def add_sentence(self, sentence: str) -> None:
        """添加一个句子中的所有词到词频统计。

        Args:
            sentence: 文本句子
        """
        for word in sentence.lower().split():
            self.word_freq[word] += 1

    def build(self) -> None:
        """根据词频统计构建词汇表。"""
        idx = len(self.word2idx)
        for word, freq in sorted(self.word_freq.items(), key=lambda x: -x[1]):
            if freq >= self.min_freq and word not in self.word2idx:
                self.word2idx[word] = idx
                self.idx2word[idx] = word
                idx += 1
        self._built = True

    def encode(self, sentence: str, max_length: Optional[int] = None) -> list[int]:
        """将句子编码为索引序列。

        Args:
            sentence: 文本句子
            max_length: 最大序列长度（可选，用于截断或填充）

        Returns:
            索引列表，包含 <start> 和 <end> 标记
        """
        tokens = [self.START_TOKEN]
        for word in sentence.lower().split():
            idx = self.word2idx.get(word, self.word2idx[self.UNK_TOKEN])
            tokens.append(self.idx2word.get(idx, self.UNK_TOKEN))
        tokens.append(self.END_TOKEN)

        indices = [self.word2idx[t] for t in tokens]

        if max_length is not None:
            indices = indices[:max_length]

        return indices

    def decode(self, indices: list[int], skip_special: bool = True) -> str:
        """将索引序列解码为文本。

        Args:
            indices: 索引列表
            skip_special: 是否跳过特殊标记

        Returns:
            解码后的文本字符串
        """
        special_indices = {
            self.word2idx[self.PAD_TOKEN],
            self.word2idx[self.START_TOKEN],
            self.word2idx[self.END_TOKEN],
        }

        words = []
        for idx in indices:
            word = self.idx2word.get(idx, self.UNK_TOKEN)
            if skip_special and idx in special_indices:
                continue
            words.append(word)

        return " ".join(words)

    def __len__(self) -> int:
        return len(self.word2idx)

    @property
    def pad_idx(self) -> int:
        return self.word2idx[self.PAD_TOKEN]

    @property
    def start_idx(self) -> int:
        return self.word2idx[self.START_TOKEN]

    @property
    def end_idx(self) -> int:
        return self.word2idx[self.END_TOKEN]

    @property
    def unk_idx(self) -> int:
        return self.word2idx[self.UNK_TOKEN]

    @classmethod
    def from_captions(cls, captions: list[str], min_freq: int = 1) -> "Vocabulary":
        """从描述列表构建词汇表。

        Args:
            captions: 描述文本列表
            min_freq: 最小词频

        Returns:
            构建好的词汇表实例
        """
        vocab = cls(min_freq=min_freq)
        for caption in captions:
            vocab.add_sentence(caption)
        vocab.build()
        return vocab
