"""
数据集模块

提供 VQA 数据集类和示例数据生成工具。
"""

import torch
from torch.utils.data import Dataset, DataLoader
from typing import List, Dict, Tuple, Optional
import random


class Vocab:
    """
    简单词汇表

    Args:
        max_size: 最大词汇表大小
    """

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.word2idx = {'<pad>': 0, '<unk>': 1, '<sos>': 2, '<eos>': 3}
        self.idx2word = {0: '<pad>', 1: '<unk>', 2: '<sos>', 3: '<eos>'}
        self.word_count = {}
        self.next_idx = 4

    def add_word(self, word: str):
        """添加单词"""
        if word not in self.word2idx:
            self.word_count[word] = self.word_count.get(word, 0) + 1
            if self.next_idx < self.max_size:
                self.word2idx[word] = self.next_idx
                self.idx2word[self.next_idx] = word
                self.next_idx += 1

    def encode(self, text: str, max_len: int = 20) -> List[int]:
        """编码文本为 token IDs"""
        tokens = text.lower().split()
        ids = [self.word2idx.get(t, self.word2idx['<unk>']) for t in tokens[:max_len]]
        # 填充到 max_len
        ids = ids + [self.word2idx['<pad>']] * (max_len - len(ids))
        return ids

    def decode(self, ids: List[int]) -> str:
        """解码 token IDs 为文本"""
        tokens = []
        for idx in ids:
            if idx == self.word2idx['<pad>']:
                break
            tokens.append(self.idx2word.get(idx, '<unk>'))
        return ' '.join(tokens)

    def __len__(self):
        return self.next_idx


class VQADataset(Dataset):
    """
    VQA 数据集

    Args:
        questions: 问题列表
        image_ids: 图像 ID 列表
        answers: 答案列表（可选）
        vocab: 词汇表
        image_features: 预提取的图像特征字典（可选）
        max_question_len: 最大问题长度
        feature_dim: 图像特征维度（用于生成随机特征）
    """

    def __init__(
        self,
        questions: List[str],
        image_ids: List[str],
        answers: Optional[List[str]] = None,
        vocab: Optional[Vocab] = None,
        image_features: Optional[Dict[str, torch.Tensor]] = None,
        max_question_len: int = 20,
        feature_dim: int = 512,
    ):
        self.questions = questions
        self.image_ids = image_ids
        self.answers = answers
        self.image_features = image_features or {}
        self.max_question_len = max_question_len
        self.feature_dim = feature_dim

        # 创建或使用词汇表
        if vocab is None:
            self.vocab = Vocab()
            for q in questions:
                for word in q.lower().split():
                    self.vocab.add_word(word)
        else:
            self.vocab = vocab

        # 答案到索引的映射
        if answers is not None:
            unique_answers = sorted(set(answers))
            self.answer2idx = {a: i for i, a in enumerate(unique_answers)}
            self.idx2answer = {i: a for a, i in self.answer2idx.items()}
            self.num_answers = len(unique_answers)
        else:
            self.answer2idx = {}
            self.idx2answer = {}
            self.num_answers = 0

    def __len__(self) -> int:
        return len(self.questions)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """获取单个样本"""
        item = {
            'question': self.questions[idx],
            'image_id': self.image_ids[idx],
            'question_ids': torch.tensor(
                self.vocab.encode(self.questions[idx], self.max_question_len),
                dtype=torch.long,
            ),
        }

        # 图像特征
        img_id = self.image_ids[idx]
        if img_id in self.image_features:
            item['image_features'] = self.image_features[img_id]
        else:
            # 随机特征（用于测试）
            item['image_features'] = torch.randn(self.feature_dim)

        # 答案
        if self.answers is not None:
            item['answer'] = self.answers[idx]
            item['answer_idx'] = torch.tensor(
                self.answer2idx[self.answers[idx]],
                dtype=torch.long,
            )

        return item


def create_sample_data(
    num_samples: int = 100,
    num_images: int = 20,
    num_answers: int = 50,
) -> Tuple[List[str], List[str], List[str], Vocab]:
    """
    创建示例数据

    Args:
        num_samples: 样本数量
        num_images: 图像数量
        num_answers: 答案数量

    Returns:
        (问题列表, 图像ID列表, 答案列表, 词汇表)
    """
    # 示例问题模板
    question_templates = [
        "what color is the {}",
        "is there a {} in the image",
        "how many {} are there",
        "what is the {} doing",
        "where is the {}",
        "what is this",
        "what animal is this",
        "what sport is being played",
    ]

    # 示例对象
    objects = [
        'cat', 'dog', 'car', 'tree', 'person', 'bird', 'flower',
        'building', 'table', 'chair', 'book', 'cup', 'ball', 'hat',
    ]

    # 示例答案
    answer_pool = [
        'yes', 'no', 'red', 'blue', 'green', 'yellow', 'white', 'black',
        'one', 'two', 'three', 'many', 'none',
        'cat', 'dog', 'bird', 'car', 'tree',
        'sitting', 'standing', 'running', 'flying',
        'left', 'right', 'center', 'top', 'bottom',
    ][:num_answers]

    questions = []
    image_ids = []
    answers = []

    for i in range(num_samples):
        # 随机选择模板和对象
        template = random.choice(question_templates)
        obj = random.choice(objects)
        question = template.format(obj) if '{}' in template else template

        questions.append(question)
        image_ids.append(f"image_{i % num_images:04d}")
        answers.append(random.choice(answer_pool))

    # 创建词汇表
    vocab = Vocab()
    for q in questions:
        for word in q.lower().split():
            vocab.add_word(word)

    return questions, image_ids, answers, vocab


def create_dataloader(
    questions: List[str],
    image_ids: List[str],
    answers: Optional[List[str]] = None,
    vocab: Optional[Vocab] = None,
    batch_size: int = 32,
    shuffle: bool = True,
) -> Tuple[DataLoader, Vocab]:
    """
    创建数据加载器

    Args:
        questions: 问题列表
        image_ids: 图像 ID 列表
        answers: 答案列表（可选）
        vocab: 词汇表（可选）
        batch_size: 批次大小
        shuffle: 是否打乱

    Returns:
        (数据加载器, 词汇表)
    """
    # 创建词汇表
    if vocab is None:
        vocab = Vocab()
        for q in questions:
            for word in q.lower().split():
                vocab.add_word(word)

    # 创建数据集
    dataset = VQADataset(
        questions=questions,
        image_ids=image_ids,
        answers=answers,
        vocab=vocab,
    )

    # 创建数据加载器
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        collate_fn=collate_fn,
    )

    return dataloader, vocab


def collate_fn(batch: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
    """
    自定义批次整理函数

    Args:
        batch: 样本列表

    Returns:
        整理后的批次
    """
    result = {
        'question_ids': torch.stack([item['question_ids'] for item in batch]),
        'image_features': torch.stack([item['image_features'] for item in batch]),
    }

    if 'answer_idx' in batch[0]:
        result['answer_idx'] = torch.stack([item['answer_idx'] for item in batch])

    return result
