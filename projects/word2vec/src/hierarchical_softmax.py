"""
层次 Softmax 实现

使用 Huffman 树将 Softmax 的计算复杂度从 O(V) 降到 O(log V)。
每个词对应树中的一条从根到叶的路径，每一步是一个二分类决策。
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from collections import Counter


def sigmoid(x: np.ndarray) -> np.ndarray:
    """数值稳定的 sigmoid 函数"""
    x = np.clip(x, -500, 500)
    return 1.0 / (1.0 + np.exp(-x))


class HuffmanNode:
    """Huffman 树节点"""

    def __init__(self, freq: int = 0, word_idx: int = -1,
                 left: Optional['HuffmanNode'] = None,
                 right: Optional['HuffmanNode'] = None,
                 parent: Optional['HuffmanNode'] = None):
        self.freq = freq
        self.word_idx = word_idx  # -1 表示非叶节点
        self.left = left
        self.right = right
        self.parent = parent
        self.code = 0   # 0=左, 1=右
        self.path: List[int] = []  # 从根到此节点的路径（每步的 code）


class HierarchicalSoftmax:
    """层次 Softmax

    使用 Huffman 树实现高效的 Softmax 近似。
    高频词路径短（靠近根节点），低频词路径长。

    Attributes:
        vocab_size: 词汇表大小
        vector_size: 向量维度
        tree: Huffman 树的非叶节点参数矩阵
        word_paths: 每个词的路径信息
    """

    def __init__(self, vocab_size: int, vector_size: int, word_freqs: np.ndarray):
        """初始化层次 Softmax

        Args:
            vocab_size: 词汇表大小
            vector_size: 向量维度
            word_freqs: 词频数组（按索引顺序）
        """
        self.vocab_size = vocab_size
        self.vector_size = vector_size

        # 构建 Huffman 树
        self.root, self.word_nodes = self._build_huffman_tree(word_freqs)

        # 非叶节点参数（最多 vocab_size - 1 个）
        self.inner_nodes: List[HuffmanNode] = []
        self._collect_inner_nodes(self.root)

        # 内部节点参数矩阵
        self.W_inner = np.zeros((len(self.inner_nodes), vector_size), dtype=np.float64)

        # 为每个内部节点分配索引
        self.node_to_idx: Dict[int, int] = {}
        for i, node in enumerate(self.inner_nodes):
            self.node_to_idx[id(node)] = i

        # 预计算每个词的路径
        self.word_paths: Dict[int, List[Tuple[int, int]]] = {}
        self._precompute_paths()

    def _build_huffman_tree(self, word_freqs: np.ndarray) -> Tuple[HuffmanNode, Dict[int, HuffmanNode]]:
        """构建 Huffman 树

        Args:
            word_freqs: 词频数组

        Returns:
            (根节点, 词索引到叶节点的映射)
        """
        # 创建叶节点
        leaves = []
        word_nodes: Dict[int, HuffmanNode] = {}
        for idx in range(len(word_freqs)):
            node = HuffmanNode(freq=int(word_freqs[idx]), word_idx=idx)
            leaves.append(node)
            word_nodes[idx] = node

        # 使用优先队列构建 Huffman 树
        import heapq
        heap = [(node.freq, id(node), node) for node in leaves]
        heapq.heapify(heap)

        while len(heap) > 1:
            # 取出频率最小的两个节点
            freq1, _, left = heapq.heappop(heap)
            freq2, _, right = heapq.heappop(heap)

            # 创建新的内部节点
            parent = HuffmanNode(freq=freq1 + freq2, left=left, right=right)
            left.parent = parent
            left.code = 0  # 左 = 0
            right.parent = parent
            right.code = 1  # 右 = 1

            heapq.heappush(heap, (parent.freq, id(parent), parent))

        # 根节点
        root = heap[0][2] if heap else HuffmanNode()
        return root, word_nodes

    def _collect_inner_nodes(self, node: HuffmanNode) -> None:
        """收集所有内部节点"""
        if node is None or node.word_idx >= 0:
            return
        self.inner_nodes.append(node)
        self._collect_inner_nodes(node.left)
        self._collect_inner_nodes(node.right)

    def _precompute_paths(self) -> None:
        """预计算每个词的路径"""
        for word_idx, leaf in self.word_nodes.items():
            path = []
            current = leaf
            while current.parent is not None:
                parent = current.parent
                parent_idx = self.node_to_idx[id(parent)]
                path.append((parent_idx, current.code))
                current = parent
            # 反转，使其从根到叶
            path.reverse()
            self.word_paths[word_idx] = path

    def forward_backward(self, context_vector: np.ndarray, center_idx: int,
                         lr: float) -> float:
        """前向+反向传播

        对于 CBOW 中的层次 Softmax：
        - context_vector 是上下文词向量的平均（隐藏层）
        - center_idx 是要预测的中心词

        对于 Skip-gram 中的层次 Softmax：
        - context_vector 是中心词向量
        - center_idx 是要预测的上下文词

        Args:
            context_vector: 输入向量 (D,)
            center_idx: 目标词索引
            lr: 学习率

        Returns:
            损失值
        """
        if center_idx not in self.word_paths:
            return 0.0

        path = self.word_paths[center_idx]
        loss = 0.0

        for node_idx, code in path:
            # 内部节点向量
            w = self.W_inner[node_idx]

            # 计算得分
            score = np.clip(np.dot(w, context_vector), -20, 20)
            sig = sigmoid(score)

            # code: 0=左(负类), 1=右(正类)
            # 损失: -log P(correct direction)
            if code == 1:
                loss -= np.log(sig + 1e-10)
                grad = (sig - 1) * context_vector
            else:
                loss -= np.log(1 - sig + 1e-10)
                grad = sig * context_vector

            # 梯度裁剪
            grad_norm = np.linalg.norm(grad)
            if grad_norm > 5.0:
                grad = grad * (5.0 / grad_norm)

            # 更新内部节点参数
            self.W_inner[node_idx] -= lr * grad

        return loss

    def get_probabilities(self, context_vector: np.ndarray) -> np.ndarray:
        """计算所有词的概率（用于调试/分析）

        Args:
            context_vector: 输入向量

        Returns:
            概率数组
        """
        probs = np.zeros(self.vocab_size)

        for word_idx in range(self.vocab_size):
            if word_idx not in self.word_paths:
                continue

            path = self.word_paths[word_idx]
            log_prob = 0.0

            for node_idx, code in path:
                w = self.W_inner[node_idx]
                score = np.dot(w, context_vector)
                sig = sigmoid(score)

                if code == 1:
                    log_prob += np.log(sig + 1e-10)
                else:
                    log_prob += np.log(1 - sig + 1e-10)

            probs[word_idx] = np.exp(log_prob)

        # 归一化
        total = probs.sum()
        if total > 0:
            probs /= total

        return probs
