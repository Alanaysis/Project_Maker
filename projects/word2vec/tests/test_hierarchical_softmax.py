"""层次 Softmax 测试"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.hierarchical_softmax import HierarchicalSoftmax, HuffmanNode


class TestHuffmanNode:
    """Huffman 节点测试"""

    def test_init(self):
        """测试节点初始化"""
        node = HuffmanNode(freq=10, word_idx=5)
        assert node.freq == 10
        assert node.word_idx == 5
        assert node.left is None
        assert node.right is None
        assert node.parent is None


class TestHierarchicalSoftmax:
    """层次 Softmax 测试类"""

    def test_init(self):
        """测试初始化"""
        word_freqs = np.array([100, 50, 20, 10, 5])
        hs = HierarchicalSoftmax(vocab_size=5, vector_size=10, word_freqs=word_freqs)

        assert hs.vocab_size == 5
        assert hs.vector_size == 10
        assert len(hs.word_paths) == 5

    def test_huffman_tree_structure(self):
        """测试 Huffman 树结构"""
        word_freqs = np.array([100, 50, 20, 10, 5])
        hs = HierarchicalSoftmax(vocab_size=5, vector_size=10, word_freqs=word_freqs)

        # 每个词都应该有路径
        for word_idx in range(5):
            assert word_idx in hs.word_paths
            path = hs.word_paths[word_idx]
            assert len(path) > 0

    def test_high_freq_shorter_path(self):
        """测试高频词路径更短"""
        word_freqs = np.array([1000, 10, 1])
        hs = HierarchicalSoftmax(vocab_size=3, vector_size=10, word_freqs=word_freqs)

        # 高频词 (freq=1000) 应该有更短的路径
        len_0 = len(hs.word_paths[0])
        len_2 = len(hs.word_paths[2])
        assert len_0 <= len_2

    def test_inner_nodes_count(self):
        """测试内部节点数量"""
        word_freqs = np.array([100, 50, 20, 10, 5])
        hs = HierarchicalSoftmax(vocab_size=5, vector_size=10, word_freqs=word_freqs)

        # n 个叶节点 -> n-1 个内部节点
        assert len(hs.inner_nodes) == 4

    def test_forward_backward(self):
        """测试前向+反向传播"""
        word_freqs = np.array([100, 50, 20, 10, 5])
        hs = HierarchicalSoftmax(vocab_size=5, vector_size=10, word_freqs=word_freqs)

        context_vector = np.random.randn(10)
        loss = hs.forward_backward(context_vector, center_idx=0, lr=0.01)

        assert isinstance(loss, float)
        assert loss >= 0

    def test_forward_backward_updates_params(self):
        """测试前向+反向传播更新参数"""
        word_freqs = np.array([100, 50, 20, 10, 5])
        hs = HierarchicalSoftmax(vocab_size=5, vector_size=10, word_freqs=word_freqs)

        W_before = hs.W_inner.copy()

        context_vector = np.random.randn(10)
        hs.forward_backward(context_vector, center_idx=0, lr=0.01)

        # 参数应该更新
        assert not np.array_equal(W_before, hs.W_inner)

    def test_convergence(self):
        """测试收敛"""
        word_freqs = np.array([100, 50, 20, 10, 5])
        hs = HierarchicalSoftmax(vocab_size=5, vector_size=10, word_freqs=word_freqs)

        context_vector = np.random.randn(10)

        initial_loss = hs.forward_backward(context_vector, center_idx=0, lr=0.01)

        # 多次更新后损失应该下降
        for _ in range(100):
            loss = hs.forward_backward(context_vector, center_idx=0, lr=0.01)

        final_loss = hs.forward_backward(context_vector, center_idx=0, lr=0.01)
        assert final_loss < initial_loss

    def test_get_probabilities(self):
        """测试概率计算"""
        word_freqs = np.array([100, 50, 20, 10, 5])
        hs = HierarchicalSoftmax(vocab_size=5, vector_size=10, word_freqs=word_freqs)

        context_vector = np.random.randn(10)
        probs = hs.get_probabilities(context_vector)

        assert probs.shape == (5,)
        assert all(p >= 0 for p in probs)
        assert abs(sum(probs) - 1.0) < 0.01  # 概率和应该接近1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
