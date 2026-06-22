"""
Skip-gram 模型实现

Skip-gram 模型：给定中心词，预测上下文词
"""

import numpy as np
from typing import Tuple


def sigmoid(x: np.ndarray) -> np.ndarray:
    """数值稳定的 sigmoid 函数

    Args:
        x: 输入数组

    Returns:
        sigmoid 输出
    """
    # 防止数值溢出
    x = np.clip(x, -500, 500)
    return 1.0 / (1.0 + np.exp(-x))


class SkipGramModel:
    """Skip-gram 模型

    使用负采样训练的 Skip-gram 模型

    Attributes:
        vocab_size: 词汇表大小
        vector_size: 向量维度
        W_in: 输入词向量矩阵
        W_out: 输出词向量矩阵
    """

    def __init__(self, vocab_size: int, vector_size: int):
        """初始化 Skip-gram 模型

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

    def forward(self, center_idx: int, context_idx: int, neg_indices: np.ndarray) -> Tuple:
        """前向传播

        Args:
            center_idx: 中心词索引
            context_idx: 上下文词索引
            neg_indices: 负样本索引数组

        Returns:
            (loss, v_center, v_context, v_neg, pos_sig, neg_sig)
        """
        # 获取词向量
        v_center = self.W_in[center_idx]      # (D,)
        v_context = self.W_out[context_idx]   # (D,)
        v_neg = self.W_out[neg_indices]       # (K, D)

        # 计算得分（裁剪以防止溢出）
        pos_score = np.clip(np.dot(v_context, v_center), -20, 20)
        neg_scores = np.clip(np.dot(v_neg, v_center), -20, 20)

        # Sigmoid 激活
        pos_sig = sigmoid(pos_score)
        neg_sig = sigmoid(-neg_scores)

        # 计算损失
        loss = -np.log(pos_sig + 1e-10) - np.sum(np.log(neg_sig + 1e-10))

        return loss, v_center, v_context, v_neg, pos_sig, neg_sig

    def backward(self, center_idx: int, context_idx: int, neg_indices: np.ndarray,
                 v_center: np.ndarray, v_context: np.ndarray, v_neg: np.ndarray,
                 pos_sig: float, neg_sig: np.ndarray, lr: float,
                 max_grad_norm: float = 5.0) -> None:
        """反向传播并更新参数

        梯度推导（最小化损失 L）：
        L = -log(σ(s_pos)) - Σ log(σ(-s_neg_i))
        其中 s_pos = v_context · v_center, s_neg_i = v_neg_i · v_center
        neg_sig_i = σ(-s_neg_i)

        dL/d(v_center) = (σ(s_pos) - 1) * v_context + Σ (1 - σ(-s_neg_i)) * v_neg_i
                        = (pos_sig - 1) * v_context + Σ (1 - neg_sig_i) * v_neg_i

        dL/d(v_context) = (σ(s_pos) - 1) * v_center = (pos_sig - 1) * v_center

        dL/d(v_neg_i) = (1 - σ(-s_neg_i)) * v_center = (1 - neg_sig_i) * v_center

        Args:
            center_idx: 中心词索引
            context_idx: 上下文词索引
            neg_indices: 负样本索引数组
            v_center: 中心词向量
            v_context: 上下文词向量
            v_neg: 负样本词向量矩阵
            pos_sig: 正样本 sigmoid 输出
            neg_sig: 负样本 sigmoid 输出数组
            lr: 学习率
            max_grad_norm: 梯度裁剪阈值
        """
        # 计算梯度
        # 对中心词的梯度
        grad_center = (pos_sig - 1) * v_context + np.sum((1 - neg_sig).reshape(-1, 1) * v_neg, axis=0)

        # 对上下文词的梯度
        grad_context = (pos_sig - 1) * v_center

        # 对负样本的梯度
        grad_neg = (1 - neg_sig).reshape(-1, 1) * v_center  # (K, D)

        # 梯度裁剪
        grad_norm = np.linalg.norm(grad_center)
        if grad_norm > max_grad_norm:
            grad_center = grad_center * (max_grad_norm / grad_norm)

        grad_norm = np.linalg.norm(grad_context)
        if grad_norm > max_grad_norm:
            grad_context = grad_context * (max_grad_norm / grad_norm)

        # 更新参数
        self.W_in[center_idx] -= lr * grad_center
        self.W_out[context_idx] -= lr * grad_context
        self.W_out[neg_indices] -= lr * grad_neg

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

    def get_vector(self, idx: int) -> np.ndarray:
        """获取词向量

        Args:
            idx: 词索引

        Returns:
            词向量
        """
        return self.W_in[idx].copy()

    def normalize(self) -> None:
        """归一化词向量（用于余弦相似度计算）"""
        norms = np.linalg.norm(self.W_in, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        self.W_in = self.W_in / norms
