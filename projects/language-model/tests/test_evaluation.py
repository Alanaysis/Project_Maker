"""评估模块测试"""

import pytest
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.evaluation import EvaluationMetrics


class TestPerplexity:
    """困惑度测试"""

    def test_perfect_prediction(self):
        """完美预测的困惑度应为 1"""
        # log P = 0 表示概率为 1
        ppl = EvaluationMetrics.perplexity([0.0, 0.0, 0.0])
        assert abs(ppl - 1.0) < 1e-6

    def test_uniform_distribution(self):
        """均匀分布的困惑度应等于词汇表大小"""
        # 对于 V=10 的均匀分布，P=0.1, log(P) = log(0.1)
        log_prob = math.log(0.1)
        ppl = EvaluationMetrics.perplexity([log_prob] * 10)
        assert abs(ppl - 10.0) < 0.1

    def test_empty(self):
        """空输入的困惑度"""
        ppl = EvaluationMetrics.perplexity([])
        assert ppl == float('inf')

    def test_single_word(self):
        """单个词的困惑度"""
        ppl = EvaluationMetrics.perplexity([math.log(0.5)])
        assert abs(ppl - 2.0) < 1e-6

    def test_higher_prob_lower_ppl(self):
        """更高概率应导致更低的困惑度"""
        ppl_good = EvaluationMetrics.perplexity([math.log(0.9)] * 10)
        ppl_bad = EvaluationMetrics.perplexity([math.log(0.1)] * 10)
        assert ppl_good < ppl_bad


class TestCrossEntropy:
    """交叉熵测试"""

    def test_cross_entropy_base2(self):
        """测试以 2 为底的交叉熵"""
        # P = 0.5, H = -log2(0.5) = 1
        ce = EvaluationMetrics.cross_entropy([math.log(0.5)], base=2.0)
        assert abs(ce - 1.0) < 1e-6

    def test_cross_entropy_natural(self):
        """测试自然对数交叉熵"""
        # P = 1/e, H = -ln(1/e) = 1
        ce = EvaluationMetrics.cross_entropy([math.log(1 / math.e)], base=math.e)
        assert abs(ce - 1.0) < 1e-6

    def test_empty(self):
        """空输入"""
        ce = EvaluationMetrics.cross_entropy([])
        assert ce == float('inf')

    def test_relationship_with_perplexity(self):
        """测试交叉熵和困惑度的关系: PPL = 2^H"""
        log_probs = [math.log(0.3), math.log(0.5), math.log(0.7)]

        ce = EvaluationMetrics.cross_entropy(log_probs, base=2.0)
        ppl = EvaluationMetrics.perplexity(log_probs)

        assert abs(ppl - 2 ** ce) < 1e-6

    def test_zero_prob(self):
        """测试概率为零的情况"""
        # log(0) 是 -inf，但实际中应该被平滑处理
        ce = EvaluationMetrics.cross_entropy_from_probs([0.0001, 0.9999])
        assert ce > 0


class TestBitsPerCharacter:
    """BPC 测试"""

    def test_bpc(self):
        """测试 BPC 计算"""
        # P = 0.5, BPC = 1
        bpc = EvaluationMetrics.bits_per_character([math.log(0.5)])
        assert abs(bpc - 1.0) < 1e-6

    def test_bpc_equals_cross_entropy(self):
        """BPC 应等于以 2 为底的交叉熵"""
        log_probs = [math.log(0.3), math.log(0.7)]
        bpc = EvaluationMetrics.bits_per_character(log_probs)
        ce = EvaluationMetrics.cross_entropy(log_probs, base=2.0)
        assert abs(bpc - ce) < 1e-10


class TestEntropy:
    """熵测试"""

    def test_entropy(self):
        """测试熵计算"""
        # H = -1/N * sum(log P)
        log_probs = [math.log(0.5), math.log(0.5)]
        h = EvaluationMetrics.entropy(log_probs)
        assert abs(h - (-math.log(0.5))) < 1e-6

    def test_empty(self):
        """空输入"""
        h = EvaluationMetrics.entropy([])
        assert h == float('inf')


class TestPerplexityFromProbs:
    """从概率值计算困惑度"""

    def test_perplexity_from_probs(self):
        """测试从概率计算困惑度"""
        ppl = EvaluationMetrics.perplexity_from_probs([0.5, 0.5])
        assert abs(ppl - 2.0) < 1e-6

    def test_cross_entropy_from_probs(self):
        """测试从概率计算交叉熵"""
        ce = EvaluationMetrics.cross_entropy_from_probs([0.5, 0.5])
        assert abs(ce - (-math.log(0.5))) < 1e-6

    def test_empty(self):
        """空输入"""
        ppl = EvaluationMetrics.perplexity_from_probs([])
        assert ppl == float('inf')


class TestWordErrorRate:
    """词错误率测试"""

    def test_identical(self):
        """相同序列的 WER 应为 0"""
        wer = EvaluationMetrics.word_error_rate(
            ["hello", "world"], ["hello", "world"])
        assert wer == 0.0

    def test_one_substitution(self):
        """一个替换"""
        wer = EvaluationMetrics.word_error_rate(
            ["hello", "there"], ["hello", "world"])
        assert abs(wer - 0.5) < 1e-6

    def test_one_deletion(self):
        """一个删除"""
        wer = EvaluationMetrics.word_error_rate(
            ["hello"], ["hello", "world"])
        assert abs(wer - 0.5) < 1e-6

    def test_one_insertion(self):
        """一个插入"""
        wer = EvaluationMetrics.word_error_rate(
            ["hello", "beautiful", "world"], ["hello", "world"])
        assert abs(wer - 0.5) < 1e-6

    def test_empty_reference(self):
        """空参考"""
        wer = EvaluationMetrics.word_error_rate(["hello"], [])
        assert wer == 1.0

    def test_both_empty(self):
        """都为空"""
        wer = EvaluationMetrics.word_error_rate([], [])
        assert wer == 0.0


class TestBLEU:
    """BLEU 分数测试"""

    def test_perfect_match(self):
        """完美匹配的 BLEU 应为 1"""
        bleu = EvaluationMetrics.bleu_score(
            ["the", "cat", "sat"],
            [["the", "cat", "sat"]])
        assert abs(bleu - 1.0) < 1e-6

    def test_no_match(self):
        """完全不匹配的 BLEU 应为 0"""
        bleu = EvaluationMetrics.bleu_score(
            ["a", "b", "c"],
            [["the", "cat", "sat"]])
        assert bleu == 0.0

    def test_partial_match(self):
        """部分匹配 - BLEU 对零精度非常敏感"""
        # 有一个 unigram 不匹配 ("on" vs "sat")，trigram 精度为 0
        bleu = EvaluationMetrics.bleu_score(
            ["the", "cat", "on"],
            [["the", "cat", "sat"]])
        assert bleu == 0.0

        # 但使用 max_n=2 可以避免 trigram 精度为 0 的问题
        bleu2 = EvaluationMetrics.bleu_score(
            ["the", "cat", "on"],
            [["the", "cat", "sat"]],
            max_n=2)
        assert 0 < bleu2 < 1

    def test_empty(self):
        """空输入"""
        bleu = EvaluationMetrics.bleu_score([], [["the"]])
        assert bleu == 0.0

    def test_brevity_penalty(self):
        """测试短句惩罚"""
        # 过短的翻译应受惩罚
        bleu_short = EvaluationMetrics.bleu_score(
            ["the"],
            [["the", "cat", "sat", "on", "the", "mat"]])
        bleu_full = EvaluationMetrics.bleu_score(
            ["the", "cat", "sat", "on", "the", "mat"],
            [["the", "cat", "sat", "on", "the", "mat"]])
        assert bleu_short < bleu_full


class TestCompareModels:
    """模型比较测试"""

    def test_compare_models(self):
        """测试模型比较"""
        results = {
            "model_a": {"perplexity": 50.0, "cross_entropy": 5.6},
            "model_b": {"perplexity": 30.0, "cross_entropy": 4.9},
            "model_c": {"perplexity": 45.0, "cross_entropy": 5.4},
        }

        best = EvaluationMetrics.compare_models(results)
        assert best["perplexity"] == "model_b"
        assert best["cross_entropy"] == "model_b"
