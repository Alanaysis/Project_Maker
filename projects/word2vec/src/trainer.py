"""
训练器模块

负责管理训练流程、生成训练数据、执行训练循环
"""

import numpy as np
from typing import List, Tuple, Optional
from .vocabulary import Vocabulary
from .skipgram import SkipGramModel
from .negative_sampling import NegativeSampler


class Trainer:
    """训练器

    管理 Word2Vec 模型的训练过程

    Attributes:
        model: Skip-gram 模型
        vocab: 词汇表
        neg_sampler: 负采样器
        window: 上下文窗口大小
        lr: 学习率
        negative: 负样本数量
    """

    def __init__(self, model: SkipGramModel, vocabulary: Vocabulary,
                 neg_sampler: NegativeSampler, window: int = 5,
                 learning_rate: float = 0.025, negative: int = 5):
        """初始化训练器

        Args:
            model: Skip-gram 模型
            vocabulary: 词汇表
            neg_sampler: 负采样器
            window: 上下文窗口大小
            learning_rate: 学习率
            negative: 负样本数量
        """
        self.model = model
        self.vocab = vocabulary
        self.neg_sampler = neg_sampler
        self.window = window
        self.lr = learning_rate
        self.negative = negative

    def generate_pairs(self, corpus: List[List[str]]) -> List[Tuple[int, int]]:
        """生成训练对

        Args:
            corpus: 分词后的语料

        Returns:
            训练对列表，每个元素是 (center_idx, context_idx)
        """
        pairs = []

        for sentence in corpus:
            # 将句子转换为索引
            indices = []
            for word in sentence:
                idx = self.vocab.get_idx(word)
                if idx is not None:
                    indices.append(idx)

            # 生成训练对
            for i, center in enumerate(indices):
                # 动态窗口大小
                actual_window = np.random.randint(1, self.window + 1)

                # 遍历上下文窗口
                start = max(0, i - actual_window)
                end = min(len(indices), i + actual_window + 1)

                for j in range(start, end):
                    if i != j:
                        pairs.append((center, indices[j]))

        return pairs

    def train_epoch(self, pairs: List[Tuple[int, int]], lr: float = None) -> float:
        """训练一个 epoch

        Args:
            pairs: 训练对列表
            lr: 学习率，如果为 None 则使用默认学习率

        Returns:
            平均损失
        """
        if len(pairs) == 0:
            return 0.0

        if lr is None:
            lr = self.lr

        total_loss = 0.0
        num_batches = 0

        # 随机打乱训练对
        np.random.shuffle(pairs)

        for center, context in pairs:
            # 负采样
            negatives = self.neg_sampler.sample(context, self.negative)

            # 前向传播
            loss, v_center, v_context, v_neg, pos_sig, neg_sig = \
                self.model.forward(center, context, negatives)

            # 反向传播并更新参数
            self.model.backward(center, context, negatives,
                              v_center, v_context, v_neg,
                              pos_sig, neg_sig, lr)

            total_loss += loss
            num_batches += 1

        return total_loss / num_batches

    def train(self, corpus: List[List[str]], epochs: int = 100,
              verbose: bool = True) -> List[float]:
        """训练模型

        Args:
            corpus: 分词后的语料
            epochs: 训练轮数
            verbose: 是否打印训练信息

        Returns:
            每个 epoch 的损失列表
        """
        # 生成训练对
        pairs = self.generate_pairs(corpus)

        if verbose:
            print(f"Training pairs: {len(pairs)}")

        losses = []

        for epoch in range(epochs):
            # 学习率衰减
            current_lr = self.lr * (1 - epoch / epochs)
            current_lr = max(current_lr, self.lr * 0.01)

            # 训练一个 epoch
            loss = self.train_epoch(pairs, lr=current_lr)
            losses.append(loss)

            if verbose and (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch + 1}/{epochs}, Loss: {loss:.4f}, LR: {current_lr:.6f}")

        return losses
