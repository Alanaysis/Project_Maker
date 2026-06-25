"""神经语言模型测试"""

import pytest
import sys
import os
import math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.neural_lm import (
    ActivationFunction,
    FeedforwardNeuralLM,
    RNNLanguageModel,
    LSTMLanguageModel,
)


class TestActivationFunction:
    """激活函数测试"""

    def test_sigmoid(self):
        """测试 Sigmoid"""
        assert abs(ActivationFunction.sigmoid(np.array([0.0])) - 0.5) < 1e-6
        assert ActivationFunction.sigmoid(np.array([100.0])) > 0.99
        assert ActivationFunction.sigmoid(np.array([-100.0])) < 0.01

    def test_sigmoid_derivative(self):
        """测试 Sigmoid 导数"""
        x = np.array([0.0])
        d = ActivationFunction.sigmoid_derivative(x)
        assert abs(d - 0.25) < 1e-6

    def test_tanh(self):
        """测试 Tanh"""
        assert abs(ActivationFunction.tanh(np.array([0.0]))) < 1e-6
        assert ActivationFunction.tanh(np.array([10.0])) > 0.99
        assert ActivationFunction.tanh(np.array([-10.0])) < -0.99

    def test_tanh_derivative(self):
        """测试 Tanh 导数"""
        d = ActivationFunction.tanh_derivative(np.array([0.0]))
        assert abs(d - 1.0) < 1e-6

    def test_softmax(self):
        """测试 Softmax"""
        x = np.array([1.0, 2.0, 3.0])
        s = ActivationFunction.softmax(x)
        assert abs(sum(s) - 1.0) < 1e-6
        assert s[2] > s[1] > s[0]  # 单调递增

    def test_softmax_numerical_stability(self):
        """测试 Softmax 数值稳定性"""
        x = np.array([1000.0, 1001.0, 1002.0])
        s = ActivationFunction.softmax(x)
        assert not np.any(np.isnan(s))
        assert abs(sum(s) - 1.0) < 1e-6

    def test_relu(self):
        """测试 ReLU"""
        x = np.array([-1.0, 0.0, 1.0])
        y = ActivationFunction.relu(x)
        assert y[0] == 0.0
        assert y[1] == 0.0
        assert y[2] == 1.0

    def test_relu_derivative(self):
        """测试 ReLU 导数"""
        x = np.array([-1.0, 0.0, 1.0])
        d = ActivationFunction.relu_derivative(x)
        assert d[0] == 0.0
        assert d[1] == 0.0
        assert d[2] == 1.0


class TestFeedforwardNeuralLM:
    """前馈神经网络语言模型测试"""

    @pytest.fixture
    def small_model(self):
        """小型模型"""
        return FeedforwardNeuralLM(
            vocab_size=10,
            embedding_dim=8,
            hidden_dim=16,
            context_size=2,
            learning_rate=0.01,
        )

    def test_init(self, small_model):
        """测试初始化"""
        assert small_model.vocab_size == 10
        assert small_model.embedding_dim == 8
        assert small_model.hidden_dim == 16
        assert small_model.context_size == 2

    def test_forward(self, small_model):
        """测试前向传播"""
        context_ids = np.array([[0, 1], [2, 3]])
        probs, cache = small_model._forward(context_ids)

        assert probs.shape == (2, 10)
        assert np.all(probs >= 0)
        assert np.allclose(np.sum(probs, axis=1), 1.0, atol=1e-6)

    def test_predict_proba(self, small_model):
        """测试预测"""
        context_ids = np.array([0, 1])
        probs = small_model.predict_proba(context_ids)

        assert probs.shape == (10,)
        assert np.all(probs >= 0)
        assert abs(np.sum(probs) - 1.0) < 1e-6

    def test_train_step(self, small_model):
        """测试训练步骤"""
        context_ids = np.array([[0, 1], [2, 3], [1, 0]])
        target_ids = np.array([5, 6, 7])

        loss = small_model.train_step(context_ids, target_ids)
        assert isinstance(loss, float)
        assert loss > 0
        assert small_model._trained

    def test_loss_decreases(self, small_model):
        """测试损失下降"""
        context_ids = np.array([[0, 1]] * 20)
        target_ids = np.array([5] * 20)

        losses = []
        for _ in range(50):
            loss = small_model.train_step(context_ids, target_ids)
            losses.append(loss)

        # 损失应该下降
        assert losses[-1] < losses[0]

    def test_perplexity(self, small_model):
        """测试困惑度"""
        context_ids = np.array([[0, 1], [2, 3]])
        target_ids = np.array([5, 6])

        # 先训练几步
        for _ in range(10):
            small_model.train_step(context_ids, target_ids)

        ppl = small_model.perplexity(context_ids, target_ids)
        assert ppl > 0
        assert ppl < float('inf')

    def test_get_embedding(self, small_model):
        """测试获取词嵌入"""
        emb = small_model.get_embedding(0)
        assert emb.shape == (8,)

    def test_repr(self, small_model):
        """测试字符串表示"""
        r = repr(small_model)
        assert "FeedforwardNeuralLM" in r
        assert "10" in r


class TestRNNLanguageModel:
    """RNN 语言模型测试"""

    @pytest.fixture
    def small_rnn(self):
        """小型 RNN 模型"""
        return RNNLanguageModel(
            vocab_size=10,
            embedding_dim=8,
            hidden_dim=16,
            learning_rate=0.005,
        )

    def test_init(self, small_rnn):
        """测试初始化"""
        assert small_rnn.vocab_size == 10
        assert small_rnn.embedding_dim == 8
        assert small_rnn.hidden_dim == 16

    def test_forward(self, small_rnn):
        """测试前向传播"""
        word_ids = [0, 1, 2]
        h_prev = np.zeros(16)
        caches, h_final, outputs = small_rnn._forward(word_ids, h_prev)

        assert len(outputs) == 3
        assert h_final.shape == (16,)
        for out in outputs:
            assert out.shape == (10,)
            assert abs(np.sum(out) - 1.0) < 1e-6

    def test_predict_proba(self, small_rnn):
        """测试预测"""
        word_ids = [0, 1, 2]
        probs, h = small_rnn.predict_proba(word_ids)

        assert probs.shape == (10,)
        assert abs(np.sum(probs) - 1.0) < 1e-6

    def test_train_step(self, small_rnn):
        """测试训练步骤"""
        word_ids = [0, 1, 2, 3]
        target_ids = [1, 2, 3, 4]

        loss, h = small_rnn.train_step(word_ids, target_ids)
        assert isinstance(loss, float)
        assert loss > 0
        assert small_rnn._trained

    def test_loss_decreases(self, small_rnn):
        """测试损失下降"""
        word_ids = [0, 1, 2]
        target_ids = [1, 2, 3]

        losses = []
        for _ in range(50):
            loss, _ = small_rnn.train_step(word_ids, target_ids)
            losses.append(loss)

        # 损失应该下降
        assert losses[-1] < losses[0]

    def test_repr(self, small_rnn):
        """测试字符串表示"""
        r = repr(small_rnn)
        assert "RNNLanguageModel" in r


class TestLSTMLanguageModel:
    """LSTM 语言模型测试"""

    @pytest.fixture
    def small_lstm(self):
        """小型 LSTM 模型"""
        return LSTMLanguageModel(
            vocab_size=10,
            embedding_dim=8,
            hidden_dim=16,
            learning_rate=0.005,
        )

    def test_init(self, small_lstm):
        """测试初始化"""
        assert small_lstm.vocab_size == 10
        assert small_lstm.embedding_dim == 8
        assert small_lstm.hidden_dim == 16

    def test_lstm_step(self, small_lstm):
        """测试 LSTM 单步计算"""
        x = np.random.randn(8)
        h_prev = np.zeros(16)
        c_prev = np.zeros(16)

        h_new, c_new, cache = small_lstm._lstm_step(x, h_prev, c_prev)

        assert h_new.shape == (16,)
        assert c_new.shape == (16,)
        assert 'f_gate' in cache
        assert 'i_gate' in cache
        assert 'o_gate' in cache

    def test_gate_range(self, small_lstm):
        """测试门控值范围"""
        x = np.random.randn(8)
        h_prev = np.zeros(16)
        c_prev = np.zeros(16)

        _, _, cache = small_lstm._lstm_step(x, h_prev, c_prev)

        # 遗忘门、输入门、输出门应在 [0, 1]
        assert np.all(cache['f_gate'] >= 0) and np.all(cache['f_gate'] <= 1)
        assert np.all(cache['i_gate'] >= 0) and np.all(cache['i_gate'] <= 1)
        assert np.all(cache['o_gate'] >= 0) and np.all(cache['o_gate'] <= 1)

        # 候选值应在 [-1, 1] (tanh)
        assert np.all(cache['g_gate'] >= -1) and np.all(cache['g_gate'] <= 1)

    def test_forward(self, small_lstm):
        """测试前向传播"""
        word_ids = [0, 1, 2]
        h_prev = np.zeros(16)
        c_prev = np.zeros(16)

        caches, h_final, c_final, outputs = small_lstm._forward(
            word_ids, h_prev, c_prev)

        assert len(outputs) == 3
        assert h_final.shape == (16,)
        assert c_final.shape == (16,)
        for out in outputs:
            assert out.shape == (10,)
            assert abs(np.sum(out) - 1.0) < 1e-6

    def test_predict_proba(self, small_lstm):
        """测试预测"""
        word_ids = [0, 1, 2]
        probs, h, c = small_lstm.predict_proba(word_ids)

        assert probs.shape == (10,)
        assert abs(np.sum(probs) - 1.0) < 1e-6

    def test_train_step(self, small_lstm):
        """测试训练步骤"""
        word_ids = [0, 1, 2, 3]
        target_ids = [1, 2, 3, 4]

        loss, h, c = small_lstm.train_step(word_ids, target_ids)
        assert isinstance(loss, float)
        assert loss > 0
        assert small_lstm._trained

    def test_loss_decreases(self, small_lstm):
        """测试损失下降"""
        word_ids = [0, 1, 2]
        target_ids = [1, 2, 3]

        losses = []
        for _ in range(50):
            loss, _, _ = small_lstm.train_step(word_ids, target_ids)
            losses.append(loss)

        # 损失应该下降
        assert losses[-1] < losses[0]

    def test_perplexity(self, small_lstm):
        """测试困惑度"""
        test_sequences = [
            ([0, 1, 2], [1, 2, 3]),
            ([3, 4, 5], [4, 5, 6]),
        ]

        # 先训练
        for _ in range(20):
            small_lstm.train_step([0, 1, 2], [1, 2, 3])

        ppl = small_lstm.perplexity(test_sequences)
        assert ppl > 0
        assert ppl < float('inf')

    def test_forget_gate_bias(self, small_lstm):
        """测试遗忘门偏置初始化为 1"""
        # 遗忘门偏置应初始化为 1，帮助学习长期依赖
        h = small_lstm.hidden_dim
        assert np.allclose(small_lstm.b[h:2*h], 1.0)

    def test_repr(self, small_lstm):
        """测试字符串表示"""
        r = repr(small_lstm)
        assert "LSTMLanguageModel" in r
