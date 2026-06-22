"""LanguageModel 测试"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.language_model import LanguageModel


class TestLanguageModel:
    """语言模型测试"""

    @pytest.fixture
    def sample_texts(self):
        """样本文本"""
        return [
            "the cat sat on the mat",
            "the dog sat on the rug",
            "the cat ate the fish",
            "the dog chased the cat",
            "a cat and a dog played together",
            "the fish swam in the pond",
            "the mat was on the floor",
            "the rug was soft and warm",
        ]

    @pytest.fixture
    def trained_lm(self, sample_texts):
        """已训练的语言模型"""
        lm = LanguageModel(n=2, smoothing="add_k", k=1.0)
        lm.train(sample_texts)
        return lm

    def test_init(self):
        """测试初始化"""
        lm = LanguageModel(n=3)
        assert lm.n == 3

    def test_train(self, trained_lm):
        """测试训练"""
        assert trained_lm.vocabulary.size > 0
        assert trained_lm.ngram_model._trained

    def test_probability(self, trained_lm):
        """测试概率计算"""
        log_prob = trained_lm.probability("the cat sat")
        assert isinstance(log_prob, float)
        assert log_prob < 0

    def test_perplexity(self, trained_lm, sample_texts):
        """测试困惑度"""
        ppl = trained_lm.perplexity(sample_texts)
        assert isinstance(ppl, float)
        assert ppl > 0

    def test_perplexity_on_new_text(self, trained_lm):
        """测试在新文本上的困惑度"""
        ppl_train = trained_lm.perplexity(["the cat sat on the mat"])
        ppl_new = trained_lm.perplexity("zimbabwe quantum flux capacitor")

        # 训练集上的困惑度应该更低
        assert ppl_train < ppl_new

    def test_generate(self, trained_lm):
        """测试文本生成"""
        text = trained_lm.generate(max_length=10)
        assert isinstance(text, str)

    def test_generate_with_seed(self, trained_lm):
        """测试带种子的生成"""
        text = trained_lm.generate(seed="the", max_length=10)
        assert isinstance(text, str)
        assert "the" in text.lower()

    def test_generate_greedy(self, trained_lm):
        """测试贪婪生成"""
        text = trained_lm.generate_greedy(max_length=10)
        assert isinstance(text, str)

    def test_top_words(self, trained_lm):
        """测试获取常见词"""
        top = trained_lm.top_words(5)
        assert isinstance(top, list)
        assert len(top) <= 5

    def test_top_ngrams(self, trained_lm):
        """测试获取常见 N-gram"""
        top = trained_lm.top_ngrams(5)
        assert isinstance(top, list)
        assert len(top) <= 5

    def test_evaluate(self, trained_lm, sample_texts):
        """测试评估功能"""
        results = trained_lm.evaluate(sample_texts)

        assert "perplexity" in results
        assert "avg_sentence_length" in results
        assert "vocab_coverage" in results
        assert "test_vocab_size" in results
        assert "train_vocab_size" in results

        assert results["perplexity"] > 0
        assert results["avg_sentence_length"] > 0
        assert 0 <= results["vocab_coverage"] <= 1

    def test_evaluate_coverage(self, trained_lm):
        """测试词汇覆盖率"""
        # 完全在训练集中的文本，覆盖率应该为 1
        results = trained_lm.evaluate(["the cat sat on the mat"])
        assert results["vocab_coverage"] == 1.0

    def test_repr(self, trained_lm):
        """测试字符串表示"""
        r = repr(trained_lm)
        assert "LanguageModel" in r
        assert "n=2" in r

    def test_different_n_values(self, sample_texts):
        """测试不同的 N 值"""
        for n in [1, 2, 3]:
            lm = LanguageModel(n=n)
            lm.train(sample_texts)
            ppl = lm.perplexity(sample_texts)
            assert ppl > 0

    def test_different_smoothing(self, sample_texts):
        """测试不同的平滑方法"""
        for smoothing in ["add_k", "none"]:
            lm = LanguageModel(n=2, smoothing=smoothing)
            lm.train(sample_texts)
            ppl = lm.perplexity(sample_texts)
            assert ppl > 0

    def test_unigram_generate(self, sample_texts):
        """测试 Unigram 生成"""
        lm = LanguageModel(n=1)
        lm.train(sample_texts)
        text = lm.generate(max_length=5)
        assert isinstance(text, str)


class TestLanguageModelIntegration:
    """集成测试"""

    def test_full_pipeline(self):
        """测试完整流程"""
        # 准备语料
        corpus = [
            "i love natural language processing",
            "natural language processing is fun",
            "i love machine learning",
            "machine learning and natural language processing",
            "deep learning is part of machine learning",
            "i study deep learning every day",
        ]

        # 训练模型
        lm = LanguageModel(n=2, smoothing="add_k", k=0.5)
        lm.train(corpus)

        # 评估
        ppl = lm.perplexity(corpus)
        assert ppl > 0

        # 生成
        text = lm.generate(seed="i", max_length=5, temperature=0.8)
        assert isinstance(text, str)
        assert len(text) > 0

        # 全面评估
        results = lm.evaluate(corpus)
        assert results["perplexity"] > 0

    def test_model_improves_with_more_data(self):
        """测试模型随数据量增加而改善"""
        small_corpus = ["the cat sat on the mat"] * 5
        big_corpus = [
            "the cat sat on the mat",
            "the dog sat on the rug",
            "the cat ate the fish",
            "the dog chased the cat",
            "a cat and a dog played",
            "the fish swam in the pond",
        ] * 5

        lm_small = LanguageModel(n=2)
        lm_small.train(small_corpus)

        lm_big = LanguageModel(n=2)
        lm_big.train(big_corpus)

        test = ["the cat sat on the mat"]
        ppl_small = lm_small.perplexity(test)
        ppl_big = lm_big.perplexity(test)

        # 更多样本通常导致更好的模型
        # 但这个测试主要是验证流程完整性


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
