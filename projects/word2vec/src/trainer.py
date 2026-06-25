"""
训练器模块

负责管理训练流程、生成训练数据、执行训练循环。
支持 Skip-gram 和 CBOW 模型，以及负采样和层次 Softmax 优化。
"""

import numpy as np
from typing import List, Tuple, Optional, Union
from .vocabulary import Vocabulary
from .skipgram import SkipGramModel
from .cbow import CBOWModel
from .negative_sampling import NegativeSampler
from .hierarchical_softmax import HierarchicalSoftmax


class Trainer:
    """训练器

    管理 Word2Vec 模型的训练过程

    Attributes:
        model: 模型（Skip-gram 或 CBOW）
        vocab: 词汇表
        optimizer: 优化器（NegativeSampler 或 HierarchicalSoftmax）
        window: 上下文窗口大小
        lr: 学习率
        negative: 负样本数量
        model_type: 模型类型
        use_hs: 是否使用层次 Softmax
    """

    def __init__(self, model: Union[SkipGramModel, CBOWModel],
                 vocabulary: Vocabulary,
                 optimizer: Union[NegativeSampler, HierarchicalSoftmax],
                 window: int = 5,
                 learning_rate: float = 0.025,
                 negative: int = 5,
                 model_type: str = 'skipgram',
                 use_hs: bool = False):
        """初始化训练器

        Args:
            model: 模型实例
            vocabulary: 词汇表
            optimizer: 优化器（NegativeSampler 或 HierarchicalSoftmax）
            window: 上下文窗口大小
            learning_rate: 学习率
            negative: 负样本数量（仅负采样模式）
            model_type: 模型类型 ('skipgram' 或 'cbow')
            use_hs: 是否使用层次 Softmax
        """
        self.model = model
        self.vocab = vocabulary
        self.optimizer = optimizer
        self.window = window
        self.lr = learning_rate
        self.negative = negative
        self.model_type = model_type
        self.use_hs = use_hs

    def generate_pairs(self, corpus: List[List[str]]) -> List[Tuple[int, int]]:
        """生成训练对（Skip-gram 模式）

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

    def generate_cbow_data(self, corpus: List[List[str]]) -> List[Tuple[np.ndarray, int]]:
        """生成训练数据（CBOW 模式）

        Args:
            corpus: 分词后的语料

        Returns:
            训练数据列表，每个元素是 (context_indices, center_idx)
        """
        data = []

        for sentence in corpus:
            # 将句子转换为索引
            indices = []
            for word in sentence:
                idx = self.vocab.get_idx(word)
                if idx is not None:
                    indices.append(idx)

            # 生成 CBOW 训练数据
            for i, center in enumerate(indices):
                # 动态窗口大小
                actual_window = np.random.randint(1, self.window + 1)

                # 收集上下文词
                context = []
                start = max(0, i - actual_window)
                end = min(len(indices), i + actual_window + 1)

                for j in range(start, end):
                    if i != j:
                        context.append(indices[j])

                if len(context) > 0:
                    data.append((np.array(context), center))

        return data

    def train_epoch(self, pairs=None, data=None, lr: float = None) -> float:
        """训练一个 epoch

        Args:
            pairs: Skip-gram 训练对列表
            data: CBOW 训练数据列表
            lr: 学习率

        Returns:
            平均损失
        """
        if lr is None:
            lr = self.lr

        if self.model_type == 'skipgram':
            return self._train_epoch_skipgram(pairs, lr)
        else:
            return self._train_epoch_cbow(data, lr)

    def _train_epoch_skipgram(self, pairs: List[Tuple[int, int]], lr: float) -> float:
        """Skip-gram 训练一个 epoch

        Args:
            pairs: 训练对列表
            lr: 学习率

        Returns:
            平均损失
        """
        if len(pairs) == 0:
            return 0.0

        total_loss = 0.0

        # 随机打乱训练对
        np.random.shuffle(pairs)

        for center, context in pairs:
            if self.use_hs:
                # 层次 Softmax
                v_center = self.model.W_in[center]
                loss = self.optimizer.forward_backward(v_center, context, lr)

                # 更新输入向量
                # 计算梯度并更新
                path = self.optimizer.word_paths.get(context, [])
                grad = np.zeros(self.model.vector_size)
                for node_idx, code in path:
                    w = self.optimizer.W_inner[node_idx]
                    from .skipgram import sigmoid
                    score = np.clip(np.dot(w, v_center), -20, 20)
                    sig = sigmoid(score)
                    if code == 1:
                        grad += (sig - 1) * w
                    else:
                        grad += sig * w

                grad_norm = np.linalg.norm(grad)
                if grad_norm > 5.0:
                    grad = grad * (5.0 / grad_norm)
                self.model.W_in[center] -= lr * grad
            else:
                # 负采样
                negatives = self.optimizer.sample(context, self.negative)

                # 前向传播
                loss, v_center, v_context, v_neg, pos_sig, neg_sig = \
                    self.model.forward(center, context, negatives)

                # 反向传播并更新参数
                self.model.backward(center, context, negatives,
                                   v_center, v_context, v_neg,
                                   pos_sig, neg_sig, lr)

            total_loss += loss

        return total_loss / len(pairs)

    def _train_epoch_cbow(self, data: List[Tuple[np.ndarray, int]], lr: float) -> float:
        """CBOW 训练一个 epoch

        Args:
            data: 训练数据列表
            lr: 学习率

        Returns:
            平均损失
        """
        if len(data) == 0:
            return 0.0

        total_loss = 0.0

        # 随机打乱
        np.random.shuffle(data)

        for context_indices, center in data:
            if self.use_hs:
                # 层次 Softmax + CBOW
                context_vectors = self.model.W_in[context_indices]
                h = np.mean(context_vectors, axis=0)

                loss = self.optimizer.forward_backward(h, center, lr)

                # 更新输入向量
                path = self.optimizer.word_paths.get(center, [])
                grad_h = np.zeros(self.model.vector_size)
                for node_idx, code in path:
                    w = self.optimizer.W_inner[node_idx]
                    from .cbow import sigmoid
                    score = np.clip(np.dot(w, h), -20, 20)
                    sig = sigmoid(score)
                    if code == 1:
                        grad_h += (sig - 1) * w
                    else:
                        grad_h += sig * w

                grad_norm = np.linalg.norm(grad_h)
                if grad_norm > 5.0:
                    grad_h = grad_h * (5.0 / grad_norm)

                n_context = len(context_indices)
                grad_each = grad_h / n_context
                for idx in context_indices:
                    self.model.W_in[idx] -= lr * grad_each
            else:
                # 负采样 + CBOW
                negatives = self.optimizer.sample(center, self.negative)

                # 前向传播
                loss, h, v_center, v_neg, pos_sig, neg_sig = \
                    self.model.forward(context_indices, center, negatives)

                # 反向传播并更新参数
                self.model.backward(context_indices, center, negatives,
                                   h, v_center, v_neg,
                                   pos_sig, neg_sig, lr)

            total_loss += loss

        return total_loss / len(data)

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
        # 生成训练数据
        if self.model_type == 'skipgram':
            pairs = self.generate_pairs(corpus)
            data = None
            if verbose:
                print(f"Training pairs: {len(pairs)}")
        else:
            pairs = None
            data = self.generate_cbow_data(corpus)
            if verbose:
                print(f"Training samples: {len(data)}")

        losses = []

        for epoch in range(epochs):
            # 学习率衰减
            current_lr = self.lr * (1 - epoch / epochs)
            current_lr = max(current_lr, self.lr * 0.01)

            # 训练一个 epoch
            loss = self.train_epoch(pairs=pairs, data=data, lr=current_lr)
            losses.append(loss)

            if verbose and (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch + 1}/{epochs}, Loss: {loss:.4f}, LR: {current_lr:.6f}")

        return losses
