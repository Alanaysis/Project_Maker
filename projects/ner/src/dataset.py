"""
数据处理模块
============

处理 NER 数据集:
1. Vocabulary: 词表管理
2. TagVocabulary: 标签表管理
3. NERDataset: NER 数据集类

支持的数据格式:
- CoNLL 格式: 每行一个 token + 标签，空行分隔句子
  ```
  John B-PER
  lives O
  in O
  New B-LOC
  York I-LOC
  ```

BIO 标注方案:
- B-XXX: 实体 XXX 的开始
- I-XXX: 实体 XXX 的内部
- O: 非实体
"""

from typing import List, Tuple, Optional, Dict
import torch
from torch.utils.data import Dataset


class Vocabulary:
    """
    词表管理

    功能:
    - token 到 index 的映射
    - index 到 token 的映射
    - 处理未知词 (UNK) 和填充 (PAD)
    """

    PAD = "<PAD>"
    UNK = "<UNK>"

    def __init__(self, min_freq: int = 1):
        self.min_freq = min_freq
        self.token2idx: Dict[str, int] = {}
        self.idx2token: Dict[int, str] = {}
        self.token_counts: Dict[str, int] = {}

        # 特殊标记
        self.pad_idx = 0
        self.unk_idx = 1
        self.token2idx[self.PAD] = self.pad_idx
        self.token2idx[self.UNK] = self.unk_idx
        self.idx2token[self.pad_idx] = self.PAD
        self.idx2token[self.unk_idx] = self.UNK

    def build(self, sentences: List[List[str]]):
        """
        从句子列表构建词表

        参数:
            sentences: 句子列表，每个句子是 token 列表
        """
        # 统计词频
        for sentence in sentences:
            for token in sentence:
                self.token_counts[token] = self.token_counts.get(token, 0) + 1

        # 添加满足最小频率的词
        idx = len(self.token2idx)
        for token, count in sorted(self.token_counts.items()):
            if count >= self.min_freq and token not in self.token2idx:
                self.token2idx[token] = idx
                self.idx2token[idx] = token
                idx += 1

    def __len__(self) -> int:
        return len(self.token2idx)

    def __contains__(self, token: str) -> bool:
        return token in self.token2idx

    def __getitem__(self, token: str) -> int:
        return self.token2idx.get(token, self.unk_idx)

    def get_token(self, idx: int) -> str:
        return self.idx2token.get(idx, self.UNK)


class TagVocabulary:
    """
    标签表管理

    功能:
    - 标签到 index 的映射
    - index 到标签的映射
    - O 标签索引为 0
    """

    def __init__(self):
        self.tag2idx: Dict[str, int] = {}
        self.idx2tag: Dict[int, str] = {}

        # O 标签索引为 0
        self.tag2idx["O"] = 0
        self.idx2tag[0] = "O"

    def build(self, sentences: List[List[str]]):
        """
        从标签序列构建标签表

        参数:
            sentences: 标签序列列表
        """
        idx = len(self.tag2idx)
        for sentence in sentences:
            for tag in sentence:
                if tag not in self.tag2idx:
                    self.tag2idx[tag] = idx
                    self.idx2tag[idx] = tag
                    idx += 1

    def __len__(self) -> int:
        return len(self.tag2idx)

    def __contains__(self, tag: str) -> bool:
        return tag in self.tag2idx

    def __getitem__(self, tag: str) -> int:
        return self.tag2idx[tag]

    def get_tag(self, idx: int) -> str:
        return self.idx2tag.get(idx, "O")


class NERDataset(Dataset):
    """
    NER 数据集

    参数:
        sentences: token 序列列表
        tags: 标签序列列表
        vocab: 词表
        tag_vocab: 标签表
        max_len: 最大序列长度
    """

    def __init__(self, sentences: List[List[str]], tags: List[List[str]],
                 vocab: Vocabulary, tag_vocab: TagVocabulary,
                 max_len: int = 128):
        self.sentences = sentences
        self.tags = tags
        self.vocab = vocab
        self.tag_vocab = tag_vocab
        self.max_len = max_len

    def __len__(self) -> int:
        return len(self.sentences)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor,
                                               torch.Tensor]:
        """
        返回:
            tokens: token IDs (max_len,)
            tag_ids: 标签 IDs (max_len,)
            mask: 掩码 (max_len,)
        """
        sentence = self.sentences[idx][:self.max_len]
        tag_seq = self.tags[idx][:self.max_len]

        # 转换为索引
        token_ids = [self.vocab[token] for token in sentence]
        tag_ids = [self.tag_vocab[tag] for tag in tag_seq]

        seq_len = len(token_ids)
        pad_len = self.max_len - seq_len

        # 填充
        token_ids = token_ids + [self.vocab.pad_idx] * pad_len
        tag_ids = tag_ids + [0] * pad_len
        mask = [1] * seq_len + [0] * pad_len

        return (torch.tensor(token_ids, dtype=torch.long),
                torch.tensor(tag_ids, dtype=torch.long),
                torch.tensor(mask, dtype=torch.float32))


def read_conll_file(filepath: str) -> Tuple[List[List[str]], List[List[str]]]:
    """
    读取 CoNLL 格式文件

    文件格式:
    ```
    John B-PER
    lives O
    in O
    New B-LOC
    York I-LOC

    Mary B-PER
    ...
    ```

    返回:
        sentences: token 序列列表
        tags: 标签序列列表
    """
    sentences = []
    tags = []
    current_tokens = []
    current_tags = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                # 空行表示句子结束
                if current_tokens:
                    sentences.append(current_tokens)
                    tags.append(current_tags)
                    current_tokens = []
                    current_tags = []
            else:
                parts = line.split()
                if len(parts) >= 2:
                    current_tokens.append(parts[0])
                    current_tags.append(parts[1])

    # 最后一个句子
    if current_tokens:
        sentences.append(current_tokens)
        tags.append(current_tags)

    return sentences, tags


def create_sample_data() -> Tuple[List[List[str]], List[List[str]]]:
    """
    创建示例 NER 数据

    包含三种实体类型:
    - PER: 人名
    - LOC: 地点
    - ORG: 组织
    """
    sentences = [
        ["John", "works", "at", "Google", "in", "New", "York"],
        ["Mary", "lives", "in", "Beijing", "and", "works", "at", "Tsinghua"],
        ["Apple", "is", "in", "Cupertino"],
        ["Barack", "Obama", "visited", "France", "last", "year"],
        ["The", "United", "Nations", "is", "in", "New", "York"],
        ["Elon", "Musk", "founded", "Tesla", "in", "Palo", "Alto"],
        ["Amazon", "is", "in", "Seattle"],
        ["Bill", "Gates", "started", "Microsoft", "in", "Redmond"],
        ["Google", "and", "Apple", "are", "tech", "companies"],
        ["Xi", "Jinping", "leads", "China"],
        ["Sundar", "Pichai", "is", "CEO", "of", "Google"],
        ["Tim", "Cook", "runs", "Apple", "in", "California"],
        ["London", "is", "in", "the", "United", "Kingdom"],
        ["Shanghai", "is", "a", "big", "city", "in", "China"],
        ["Paris", "is", "the", "capital", "of", "France"],
        ["Tokyo", "is", "in", "Japan"],
        ["Berlin", "is", "in", "Germany"],
        ["Rome", "is", "in", "Italy"],
        ["Madrid", "is", "in", "Spain"],
        ["Sydney", "is", "in", "Australia"],
    ]

    tags = [
        ["B-PER", "O", "O", "B-ORG", "O", "B-LOC", "I-LOC"],
        ["B-PER", "O", "O", "B-LOC", "O", "O", "O", "B-ORG"],
        ["B-ORG", "O", "O", "B-LOC"],
        ["B-PER", "I-PER", "O", "B-LOC", "O", "O"],
        ["O", "B-ORG", "I-ORG", "O", "O", "B-LOC", "I-LOC"],
        ["B-PER", "I-PER", "O", "B-ORG", "O", "B-LOC", "I-LOC"],
        ["B-ORG", "O", "O", "B-LOC"],
        ["B-PER", "I-PER", "O", "B-ORG", "O", "B-LOC"],
        ["B-ORG", "O", "B-ORG", "O", "O", "O"],
        ["B-PER", "I-PER", "O", "B-LOC"],
        ["B-PER", "I-PER", "O", "O", "O", "B-ORG"],
        ["B-PER", "I-PER", "O", "B-ORG", "O", "B-LOC"],
        ["B-LOC", "O", "O", "O", "B-LOC", "I-LOC"],
        ["B-LOC", "O", "O", "O", "O", "O", "B-LOC"],
        ["B-LOC", "O", "O", "O", "O", "B-LOC"],
        ["B-LOC", "O", "O", "B-LOC"],
        ["B-LOC", "O", "O", "B-LOC"],
        ["B-LOC", "O", "O", "B-LOC"],
        ["B-LOC", "O", "O", "B-LOC"],
        ["B-LOC", "O", "O", "B-LOC"],
    ]

    return sentences, tags


def save_conll_file(filepath: str, sentences: List[List[str]],
                    tags: List[List[str]]):
    """
    保存 CoNLL 格式文件

    参数:
        filepath: 文件路径
        sentences: token 序列列表
        tags: 标签序列列表
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        for tokens, tag_seq in zip(sentences, tags):
            for token, tag in zip(tokens, tag_seq):
                f.write(f"{token} {tag}\n")
            f.write("\n")  # 空行分隔句子
