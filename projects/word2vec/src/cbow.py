"""
CBOW (Continuous Bag of Words) 模型实现

CBOW 模型：给定上下文词，预测中心词
与 Skip-gram 相反，CBOW 通过平均上下文词向量来预测中心词
"""

import numpy as np
from typing import Tuple, List


def sigmoid(x: np.ndarray) -> np.ndarray:
    """数值稳定的 sigmoid 函数"""
    x = np.clip(x, -500, 500)
    return 1.0 / (1.0 + np.exp(-x))


class CBOWModel:
    """CBOW 模型

    使用负采样训练的 CBOW 模型。
    与 Skip-gram 不同，CBOW 将上下文词向量求平均后预测中心词。

    Attributes:
        vocab_size: 词汇表大小
        vector_size: 向量维度
        W_in: 输入词向量矩阵 (上下文词向量)
        W_out: 输出词向量矩阵 (中心词向量)
    """

    def __init__(self, vocab_size: int, vector_size: int):
        """初始化 CBOW 模型

        Args:
            vocab_size: 词汇表大小
            vector_size: 向量维度
        """
        self.vocab_size = vocab_size
        self.vector_size = vector_size

        # Xavier 初始化
        scale = np.sqrt(6.0 / (vocab_size + vector_size))
        self.W_in = np.random.uniform(-scale, scale, (vocab_size, vector_size)).astype(np.float64)
        self.W_out = np.random.uniform(-scale, scale, (vocab_size, vector_size)).astype(np.float64) * 0.01

    def forward(self, context_indices: np.ndarray, center_idx: int,
                neg_indices: np.ndarray) -> Tuple:
        """前向传播

        CBOW 的核心：将上下文词向量取平均作为隐藏层表示。

        Args:
            context_indices: 上下文词索引数组
            center_idx: 中心词索引
            neg_indices: 负样本索引数组

        Returns:
            (loss, h, v_center, v_neg, pos_sig, neg_sig)
        """
        # 上下文词向量平均 -> 隐藏层
        context_vectors = self.W_in[context_indices]  # (C, D)
        h = np.mean(context_vectors, axis=0)           # (D,)

        # 输出向量
        v_center = self.W_out[center_idx]   # (D,)
        v_neg = self.W_out[neg_indices]     # (K, D)

        # 计算得分
        pos_score = np.clip(np.dot(v_center, h), -20, 20)
        neg_scores = np.clip(np.dot(v_neg, h), -20, 20)  # (K,)

        # Sigmoid
        pos_sig = sigmoid(pos_score)
        neg_sig = sigmoid(-neg_scores)  # (K,)

        # 损失
        loss = -np.log(pos_sig + 1e-10) - np.sum(np.log(neg_sig + 1e-10))

        return loss, h, v_center, v_neg, pos_sig, neg_sig

    def backward(self, context_indices: np.ndarray, center_idx: int,
                 neg_indices: np.ndarray, h: np.ndarray,
                 v_center: np.ndarray, v_neg: np.ndarray,
                 pos_sig: float, neg_sig: np.ndarray, lr: float,
                 max_grad_norm: float = 5.0) -> None:
        """反向传播并更新参数

        梯度推导：
        L = -log(σ(v_c · h)) - Σ log(σ(-v_ni · h))

        dL/dh = (pos_sig - 1) * v_center + Σ (1 - neg_sig_i) * v_neg_i

        由于 h = mean(context_vectors)，
        dL/d(v_context_j) = dL/dh / C  (C 是上下文词数量)

        dL/d(v_center) = (pos_sig - 1) * h
        dL/d(v_neg_i) = (1 - neg_sig_i) * h

        Args:
            context_indices: 上下文词索引数组
            center_idx: 中心词索引
            neg_indices: 负样本索引数组
            h: 隐藏层向量
            v_center: 中心词输出向量
            v_neg: 负样本输出向量矩阵
            pos_sig: 正样本 sigmoid 输出
            neg_sig: 负样本 sigmoid 输出数组
            lr: 学习率
            max_grad_norm: 梯度裁剪阈值
        """
        n_context = len(context_indices)

        # 对隐藏层的梯度
        grad_h = (pos_sig - 1) * v_center + np.sum(
            (1 - neg_sig).reshape(-1, 1) * v_neg, axis=0
        )  # (D,)

        # 对输出层的梯度
        grad_center = (pos_sig - 1) * h       # (D,)
        grad_neg = (1 - neg_sig).reshape(-1, 1) * h  # (K, D)

        # 梯度裁剪
        grad_norm = np.linalg.norm(grad_h)
        if grad_norm > max_grad_norm:
            grad_h = grad_h * (max_grad_norm / grad_norm)

        # 更新输出层参数
        self.W_out[center_idx] -= lr * grad_center
        self.W_out[neg_indices] -= lr * grad_neg

        # 更新输入层参数（上下文词向量）
        grad_context_each = grad_h / n_context  # (D,)
        for idx in context_indices:
            self.W_in[idx] -= lr * grad_context_each

    def get_vector(self, idx: int) -> np.ndarray:
        """获取词向量

        Args:
            idx: 词索引

        Returns:
            词向量
        """
        return self.W_in[idx].copy()

    def get_similarity(self, idx1: int, idx2: int) -> float:
        """计算两个词的余弦相似度

        Args:
            idx1: 第一个词的索引
            idx2: 第二个词的索引

        Returns:
            余弦相似度
        """
        v1 = self.W_in[idx1]
        v2 = self.W_in[idx2]

        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)

    def normalize(self) -> None:
        """归一化词向量"""
        norms = np.linalg.norm(self.W_in, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        self.W_in = self.W_in / norms
