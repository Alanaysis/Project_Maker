"""CBOW 模型测试"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.cbow import CBOWModel, sigmoid


class TestCBOWModel:
    """CBOW 模型测试类"""

    def test_init(self):
        """测试模型初始化"""
        model = CBOWModel(vocab_size=100, vector_size=50)
        assert model.W_in.shape == (100, 50)
        assert model.W_out.shape == (100, 50)
        assert model.vocab_size == 100
        assert model.vector_size == 50

    def test_forward(self):
        """测试前向传播"""
        model = CBOWModel(vocab_size=100, vector_size=50)
        context_indices = np.array([0, 1, 2, 3])
        loss, h, v_center, v_neg, pos_sig, neg_sig = \
            model.forward(context_indices, 5, np.array([6, 7, 8]))

        assert isinstance(loss, float)
        assert loss > 0
        assert h.shape == (50,)
        assert v_center.shape == (50,)
        assert v_neg.shape == (3, 50)

    def test_forward_hidden_layer(self):
        """测试隐藏层是上下文向量的平均"""
        model = CBOWModel(vocab_size=10, vector_size=5)
        context_indices = np.array([0, 1, 2])

        # 手动计算平均
        expected_h = np.mean(model.W_in[context_indices], axis=0)

        _, h, _, _, _, _ = model.forward(context_indices, 5, np.array([6, 7]))
        np.testing.assert_allclose(h, expected_h, rtol=1e-5)

    def test_backward_updates(self):
        """测试反向传播更新参数"""
        model = CBOWModel(vocab_size=100, vector_size=50)
        model.W_out = np.random.randn(100, 50) * 0.01

        W_in_before = model.W_in.copy()
        W_out_before = model.W_out.copy()

        context_indices = np.array([0, 1, 2, 3])
        loss, h, v_center, v_neg, pos_sig, neg_sig = \
            model.forward(context_indices, 5, np.array([6, 7, 8]))

        model.backward(context_indices, 5, np.array([6, 7, 8]),
                       h, v_center, v_neg, pos_sig, neg_sig, 0.025)

        # 检查参数是否更新
        assert not np.array_equal(W_in_before[0], model.W_in[0])
        assert not np.array_equal(W_out_before[5], model.W_out[5])

    def test_backward_updates_all_context(self):
        """测试反向传播更新所有上下文词向量"""
        model = CBOWModel(vocab_size=100, vector_size=50)
        model.W_out = np.random.randn(100, 50) * 0.01

        context_indices = np.array([0, 1, 2])
        W_in_before = model.W_in.copy()

        loss, h, v_center, v_neg, pos_sig, neg_sig = \
            model.forward(context_indices, 5, np.array([6, 7]))

        model.backward(context_indices, 5, np.array([6, 7]),
                       h, v_center, v_neg, pos_sig, neg_sig, 0.025)

        # 所有上下文词向量都应该更新
        for idx in context_indices:
            assert not np.array_equal(W_in_before[idx], model.W_in[idx])

    def test_get_vector(self):
        """测试获取词向量"""
        model = CBOWModel(vocab_size=100, vector_size=50)
        vec = model.get_vector(0)
        assert vec.shape == (50,)
        # 应该是副本
        vec[0] = 999
        assert model.W_in[0, 0] != 999

    def test_get_similarity(self):
        """测试相似度计算"""
        model = CBOWModel(vocab_size=100, vector_size=50)

        # 相同词应该相似度为1
        sim = model.get_similarity(0, 0)
        assert sim == pytest.approx(1.0)

        # 不同词相似度应该在[-1, 1]之间
        sim = model.get_similarity(0, 1)
        assert -1 <= sim <= 1

    def test_normalize(self):
        """测试向量归一化"""
        model = CBOWModel(vocab_size=100, vector_size=50)
        model.normalize()

        # 检查所有向量范数为1
        norms = np.linalg.norm(model.W_in, axis=1)
        for n in norms:
            if n > 0:
                assert abs(n - 1.0) < 1e-5

    def test_training_convergence(self):
        """测试训练收敛"""
        model = CBOWModel(vocab_size=10, vector_size=5)
        model.W_out = np.random.randn(10, 5) * 0.01

        # 多次前向-反向传播，损失应该下降
        context_indices = np.array([0, 1, 2])
        center_idx = 5
        neg_indices = np.array([6, 7])

        initial_loss, h, v_center, v_neg, pos_sig, neg_sig = \
            model.forward(context_indices, center_idx, neg_indices)

        for _ in range(100):
            loss, h, v_center, v_neg, pos_sig, neg_sig = \
                model.forward(context_indices, center_idx, neg_indices)
            model.backward(context_indices, center_idx, neg_indices,
                           h, v_center, v_neg, pos_sig, neg_sig, 0.01)

        final_loss, _, _, _, _, _ = \
            model.forward(context_indices, center_idx, neg_indices)

        # 损失应该下降
        assert final_loss < initial_loss


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
