"""Skip-gram 模型测试"""

import pytest
import numpy as np
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.skipgram import SkipGramModel, sigmoid


class TestSigmoid:
    """Sigmoid 函数测试"""

    def test_sigmoid_zero(self):
        """测试 sigmoid(0) = 0.5"""
        assert sigmoid(np.array([0.0]))[0] == pytest.approx(0.5)

    def test_sigmoid_positive(self):
        """测试正数输入"""
        result = sigmoid(np.array([100.0]))[0]
        assert result == pytest.approx(1.0, abs=1e-5)

    def test_sigmoid_negative(self):
        """测试负数输入"""
        result = sigmoid(np.array([-100.0]))[0]
        assert result == pytest.approx(0.0, abs=1e-5)

    def test_sigmoid_range(self):
        """测试输出范围"""
        x = np.array([-10, -1, 0, 1, 10])
        result = sigmoid(x)
        assert all(0 <= r <= 1 for r in result)


class TestSkipGramModel:
    """Skip-gram 模型测试"""

    def test_init(self):
        """测试模型初始化"""
        model = SkipGramModel(vocab_size=100, vector_size=50)
        assert model.W_in.shape == (100, 50)
        assert model.W_out.shape == (100, 50)

    def test_forward(self):
        """测试前向传播"""
        model = SkipGramModel(vocab_size=100, vector_size=50)
        loss, v_center, v_context, v_neg, pos_sig, neg_sig = \
            model.forward(0, 1, np.array([2, 3, 4]))

        assert isinstance(loss, float)
        assert loss > 0
        assert v_center.shape == (50,)
        assert v_context.shape == (50,)
        assert v_neg.shape == (3, 50)

    def test_backward_updates(self):
        """测试反向传播更新参数"""
        model = SkipGramModel(vocab_size=100, vector_size=50)

        # 初始化 W_out 为非零值（否则梯度为零）
        model.W_out = np.random.randn(100, 50) * 0.01

        W_in_before = model.W_in.copy()
        W_out_before = model.W_out.copy()

        # 前向传播
        loss, v_center, v_context, v_neg, pos_sig, neg_sig = \
            model.forward(0, 1, np.array([2, 3, 4]))

        # 反向传播
        model.backward(0, 1, np.array([2, 3, 4]),
                      v_center, v_context, v_neg,
                      pos_sig, neg_sig, 0.025)

        # 检查参数是否更新
        assert not np.array_equal(W_in_before, model.W_in)
        assert not np.array_equal(W_out_before, model.W_out)

    def test_get_vector(self):
        """测试获取词向量"""
        model = SkipGramModel(vocab_size=100, vector_size=50)
        vec = model.get_vector(0)
        assert vec.shape == (50,)
        # 应该是副本
        vec[0] = 999
        assert model.W_in[0, 0] != 999

    def test_get_similarity(self):
        """测试相似度计算"""
        model = SkipGramModel(vocab_size=100, vector_size=50)

        # 相同词应该相似度为1
        sim = model.get_similarity(0, 0)
        assert sim == pytest.approx(1.0)

        # 不同词相似度应该在[-1, 1]之间
        sim = model.get_similarity(0, 1)
        assert -1 <= sim <= 1

    def test_normalize(self):
        """测试向量归一化"""
        model = SkipGramModel(vocab_size=100, vector_size=50)
        model.normalize()

        # 检查所有向量范数为1
        norms = np.linalg.norm(model.W_in, axis=1)
        assert all(abs(n - 1.0) < 1e-5 for n in norms if n > 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
