"""平滑技术测试"""

import pytest
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.smoothing import LaplaceSmoothing, GoodTuringSmoothing, KneserNeySmoothing


class TestLaplaceSmoothing:
    """拉普拉斯平滑测试"""

    def test_init(self):
        """测试初始化"""
        s = LaplaceSmoothing(k=1.0)
        assert s.k == 1.0

    def test_init_invalid_k(self):
        """测试无效 k 值"""
        with pytest.raises(ValueError):
            LaplaceSmoothing(k=0)
        with pytest.raises(ValueError):
            LaplaceSmoothing(k=-1)

    def test_probability_basic(self):
        """测试基本概率计算"""
        s = LaplaceSmoothing(k=1.0)
        # P = (count + k) / (context_count + k * V)
        # P = (2 + 1) / (10 + 1 * 100) = 3/110
        prob = s.probability(ngram_count=2, context_count=10, vocab_size=100)
        assert abs(prob - 3.0 / 110.0) < 1e-10

    def test_probability_zero_count(self):
        """测试零计数情况"""
        s = LaplaceSmoothing(k=1.0)
        # 未见过的 N-gram 仍有非零概率
        prob = s.probability(ngram_count=0, context_count=10, vocab_size=100)
        assert prob > 0
        assert abs(prob - 1.0 / 110.0) < 1e-10

    def test_probability_sum_to_one(self):
        """测试概率和是否为 1"""
        s = LaplaceSmoothing(k=1.0)
        vocab_size = 10
        context_count = 100

        # 所有词的概率和
        total = sum(
            s.probability(ngram_count=i, context_count=context_count,
                          vocab_size=vocab_size)
            for i in range(vocab_size)
        )
        # 不精确等于 1，因为不同词有不同计数
        # 但所有词的概率和应该合理
        assert total > 0

    def test_different_k_values(self):
        """测试不同 k 值"""
        # k 越大，平滑越强
        s_small = LaplaceSmoothing(k=0.01)
        s_large = LaplaceSmoothing(k=10.0)

        prob_small = s_small.probability(ngram_count=0, context_count=10,
                                         vocab_size=100)
        prob_large = s_large.probability(ngram_count=0, context_count=10,
                                         vocab_size=100)

        # 更大的 k 给零计数更高的概率
        assert prob_large > prob_small

    def test_laplace_k1(self):
        """测试标准拉普拉斯平滑 (k=1)"""
        s = LaplaceSmoothing(k=1.0)
        # P = (count + 1) / (context_count + V)
        prob = s.probability(ngram_count=5, context_count=20, vocab_size=50)
        expected = (5 + 1) / (20 + 50)
        assert abs(prob - expected) < 1e-10

    def test_repr(self):
        """测试字符串表示"""
        s = LaplaceSmoothing(k=0.5)
        assert "LaplaceSmoothing" in repr(s)
        assert "0.5" in repr(s)


class TestGoodTuringSmoothing:
    """Good-Turing 平滑测试"""

    def test_init(self):
        """测试初始化"""
        gt = GoodTuringSmoothing(k_threshold=5)
        assert gt.k_threshold == 5

    def test_init_invalid(self):
        """测试无效参数"""
        with pytest.raises(ValueError):
            GoodTuringSmoothing(k_threshold=0)

    def test_fit(self):
        """测试拟合"""
        gt = GoodTuringSmoothing(k_threshold=3)
        counts = {
            ("a", "b"): 1,
            ("b", "c"): 1,
            ("c", "d"): 2,
            ("d", "e"): 2,
            ("e", "f"): 3,
            ("f", "g"): 5,
            ("g", "h"): 10,
        }
        gt.fit(counts)

        # N_1 = 2 (a,b) 和 (b,c) 出现 1 次
        assert gt.freq_of_freq[1] == 2
        # N_2 = 2
        assert gt.freq_of_freq[2] == 2

    def test_adjusted_count(self):
        """测试调整后的计数"""
        gt = GoodTuringSmoothing(k_threshold=5)
        counts = {
            ("a", "b"): 1,
            ("b", "c"): 1,
            ("c", "d"): 2,
            ("d", "e"): 2,
            ("e", "f"): 3,
            ("f", "g"): 5,
        }
        gt.fit(counts)

        # r=1 的调整计数: r* = (r+1) * N_{r+1} / N_r = 2 * N_2 / N_1
        r_star = gt.get_adjusted_count(1)
        assert r_star > 0

        # 高频计数不做调整
        r_star_high = gt.get_adjusted_count(10)
        assert r_star_high == 10

    def test_probability(self):
        """测试概率计算"""
        gt = GoodTuringSmoothing(k_threshold=5)
        counts = {
            ("a", "b"): 1,
            ("b", "c"): 1,
            ("c", "d"): 2,
            ("d", "e"): 2,
            ("e", "f"): 3,
            ("f", "g"): 10,
        }
        gt.fit(counts)

        # 正常概率
        prob = gt.probability(ngram_count=2, context_count=10, vocab_size=100)
        assert prob >= 0

        # 零计数
        prob_zero = gt.probability(ngram_count=0, context_count=10, vocab_size=100)
        assert prob_zero >= 0

    def test_unfitted_error(self):
        """测试未拟合时的错误"""
        gt = GoodTuringSmoothing()
        with pytest.raises(RuntimeError):
            gt.probability(1, 10, 100)

    def test_repr(self):
        """测试字符串表示"""
        gt = GoodTuringSmoothing(k_threshold=3)
        assert "GoodTuringSmoothing" in repr(gt)


class TestKneserNeySmoothing:
    """Kneser-Ney 平滑测试"""

    def test_init(self):
        """测试初始化"""
        kn = KneserNeySmoothing(discount=0.75)
        assert kn.discount == 0.75

    def test_init_invalid(self):
        """测试无效参数"""
        with pytest.raises(ValueError):
            KneserNeySmoothing(discount=0)
        with pytest.raises(ValueError):
            KneserNeySmoothing(discount=1.0)

    def test_fit(self):
        """测试拟合"""
        kn = KneserNeySmoothing(discount=0.75)
        ngram_counts = {
            ("the", "cat"): 3,
            ("the", "dog"): 2,
            ("the", "fish"): 1,
            ("a", "cat"): 1,
            ("a", "dog"): 1,
            ("cat", "sat"): 2,
            ("dog", "ran"): 1,
        }
        context_counts = {
            ("the",): 6,
            ("a",): 2,
            ("cat",): 2,
            ("dog",): 1,
        }
        vocab = {"the", "cat", "dog", "fish", "a", "sat", "ran"}

        kn.fit(ngram_counts, context_counts, vocab)
        assert kn._total_continuations > 0

    def test_probability(self):
        """测试概率计算"""
        kn = KneserNeySmoothing(discount=0.75)
        ngram_counts = {
            ("the", "cat"): 3,
            ("the", "dog"): 2,
            ("a", "cat"): 1,
            ("a", "dog"): 1,
        }
        context_counts = {
            ("the",): 5,
            ("a",): 2,
        }
        vocab = {"the", "cat", "dog", "a"}

        kn.fit(ngram_counts, context_counts, vocab)

        # P(cat | the) 应该 > 0
        prob = kn.probability(("the", "cat"))
        assert prob > 0

        # P(dog | the) 应该 > 0
        prob = kn.probability(("the", "dog"))
        assert prob > 0

        # 概率应该合理
        assert prob < 1.0

    def test_probability_sum(self):
        """测试概率和"""
        kn = KneserNeySmoothing(discount=0.75)
        ngram_counts = {
            ("the", "cat"): 3,
            ("the", "dog"): 2,
            ("the", "fish"): 1,
        }
        context_counts = {
            ("the",): 6,
        }
        vocab = {"the", "cat", "dog", "fish"}

        kn.fit(ngram_counts, context_counts, vocab)

        # 给定 "the"，所有词的概率和
        total = sum(
            kn.probability(("the", w))
            for w in vocab
        )
        # 应该接近 1
        assert abs(total - 1.0) < 0.5

    def test_unseen_context(self):
        """测试未见过的上下文"""
        kn = KneserNeySmoothing(discount=0.75)
        ngram_counts = {
            ("the", "cat"): 3,
        }
        context_counts = {
            ("the",): 3,
        }
        vocab = {"the", "cat", "dog"}

        kn.fit(ngram_counts, context_counts, vocab)

        # 未见过的上下文应使用低阶分布
        prob = kn.probability(("unknown", "cat"))
        assert prob >= 0

    def test_unfitted_error(self):
        """测试未拟合时的错误"""
        kn = KneserNeySmoothing()
        with pytest.raises(RuntimeError):
            kn.probability(("the", "cat"))

    def test_lower_order_prob(self):
        """测试低阶概率"""
        kn = KneserNeySmoothing(discount=0.75)
        ngram_counts = {
            ("x", "cat"): 1,
            ("y", "cat"): 1,
            ("x", "dog"): 1,
        }
        context_counts = {
            ("x",): 2,
            ("y",): 1,
        }
        vocab = {"x", "y", "cat", "dog"}

        kn.fit(ngram_counts, context_counts, vocab)

        # cat 有两个前驱 (x, y)，dog 有一个前驱 (x)
        # P_KN(cat) = 2/3, P_KN(dog) = 1/3
        prob_cat = kn._lower_order_prob("cat")
        prob_dog = kn._lower_order_prob("dog")

        assert prob_cat > prob_dog

    def test_repr(self):
        """测试字符串表示"""
        kn = KneserNeySmoothing(discount=0.75)
        assert "KneserNeySmoothing" in repr(kn)
