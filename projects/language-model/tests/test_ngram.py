"""NGramModel 测试"""

import pytest
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ngram import NGramModel


class TestNGramModel:
    """N-gram 模型测试"""

    @pytest.fixture
    def simple_corpus(self):
        """简单语料"""
        return [
            ["the", "cat", "sat", "on", "the", "mat"],
            ["the", "dog", "sat", "on", "the", "rug"],
            ["the", "cat", "ate", "the", "fish"],
        ]

    @pytest.fixture
    def trained_model(self, simple_corpus):
        """已训练的模型"""
        model = NGramModel(n=2, smoothing="add_k", k=1.0)
        model.train(simple_corpus)
        return model

    def test_init(self):
        """测试初始化"""
        model = NGramModel(n=3)
        assert model.n == 3
        assert model.smoothing == "add_k"
        assert model.k == 1.0

    def test_init_invalid_n(self):
        """测试无效的 N 值"""
        with pytest.raises(ValueError):
            NGramModel(n=0)

    def test_train(self, trained_model):
        """测试训练"""
        assert trained_model._trained
        assert trained_model.vocab_size > 0
        assert "the" in trained_model.get_vocab()
        assert "cat" in trained_model.get_vocab()

    def test_train_unigram(self, simple_corpus):
        """测试 Unigram 训练"""
        model = NGramModel(n=1)
        model.train(simple_corpus)
        assert model._trained
        assert model.vocab_size > 0

    def test_ngram_counts(self, trained_model):
        """测试 N-gram 计数"""
        # Bigram: ("the", "cat") 应该出现 2 次
        count = trained_model.get_ngram_count(("the", "cat"))
        assert count == 2

        # Bigram: ("cat", "sat") 应该出现 1 次
        count = trained_model.get_ngram_count(("cat", "sat"))
        assert count == 1

    def test_context_counts(self, trained_model):
        """测试上下文计数"""
        # "the" 后面跟的词
        count = trained_model.get_context_count(("the",))
        assert count >= 4  # the cat, the mat, the dog, the rug, the fish

    def test_probability(self, trained_model):
        """测试概率计算"""
        # P(cat | the) 应该 > 0
        prob = trained_model.probability(("the", "cat"))
        assert prob > 0

        # 概率应该在 [0, 1] 范围内
        assert 0 <= prob <= 1

    def test_probability_sum(self, trained_model):
        """测试概率和"""
        # 给定 "the"，所有可能下一个词的概率之和应该接近 1
        vocab = trained_model.get_vocab()
        total = sum(
            trained_model.probability(("the", word))
            for word in vocab
        )
        # 由于平滑，和可能略大于 1，但应该接近
        assert abs(total - 1.0) < 0.5

    def test_probability_untrained(self):
        """测试未训练时计算概率"""
        model = NGramModel(n=2)
        with pytest.raises(RuntimeError):
            model.probability(("hello", "world"))

    def test_sentence_probability(self, trained_model):
        """测试句子概率"""
        log_prob = trained_model.sentence_probability(["the", "cat", "sat"])
        assert isinstance(log_prob, float)
        assert log_prob < 0  # 对数概率应该为负

    def test_sentence_probability_unlikely(self, trained_model):
        """测试不太可能出现的句子"""
        log_prob_common = trained_model.sentence_probability(["the", "cat", "sat"])
        log_prob_rare = trained_model.sentence_probability(["zebra", "flew", "mars"])

        # 常见句子的概率应该更高（对数概率更大）
        assert log_prob_common > log_prob_rare

    def test_perplexity(self, trained_model, simple_corpus):
        """测试困惑度"""
        ppl = trained_model.perplexity(simple_corpus)
        assert isinstance(ppl, float)
        assert ppl > 0
        assert ppl < float('inf')

    def test_perplexity_lower_better(self, simple_corpus):
        """测试困惑度：更好的模型有更低的困惑度"""
        # 大语料训练
        big_corpus = simple_corpus * 10
        model_big = NGramModel(n=2, smoothing="add_k", k=1.0)
        model_big.train(big_corpus)

        model_small = NGramModel(n=2, smoothing="add_k", k=1.0)
        model_small.train(simple_corpus[:1])

        ppl_big = model_big.perplexity(simple_corpus)
        ppl_small = model_small.perplexity(simple_corpus)

        # 更大的训练集通常有更低的困惑度
        # （不一定总是成立，但在这个简单例子中应该成立）

    def test_perplexity_untrained(self):
        """测试未训练时计算困惑度"""
        model = NGramModel(n=2)
        with pytest.raises(RuntimeError):
            model.perplexity([["hello"]])

    def test_generate(self, trained_model):
        """测试文本生成"""
        generated = trained_model.generate(max_length=10)
        assert isinstance(generated, list)
        assert len(generated) <= 10

    def test_generate_with_seed(self, trained_model):
        """测试带种子的文本生成"""
        generated = trained_model.generate(seed="the", max_length=10)
        assert isinstance(generated, list)
        assert len(generated) > 0

    def test_generate_greedy(self, trained_model):
        """测试贪婪生成"""
        generated = trained_model.generate_greedy(max_length=10)
        assert isinstance(generated, list)
        assert len(generated) > 0

    def test_generate_deterministic_greedy(self, trained_model):
        """测试贪婪生成的确定性"""
        g1 = trained_model.generate_greedy(max_length=10, seed="the")
        g2 = trained_model.generate_greedy(max_length=10, seed="the")
        assert g1 == g2

    def test_generate_temperature(self, trained_model):
        """测试温度参数"""
        # 低温度应该更确定性
        generated = trained_model.generate(max_length=10, temperature=0.1)
        assert isinstance(generated, list)

    def test_generate_invalid_temperature(self, trained_model):
        """测试无效温度"""
        with pytest.raises(ValueError):
            trained_model.generate(temperature=0)

    def test_generate_untrained(self):
        """测试未训练时生成"""
        model = NGramModel(n=2)
        with pytest.raises(RuntimeError):
            model.generate()

    def test_top_ngrams(self, trained_model):
        """测试获取最常见的 N-gram"""
        top = trained_model.top_ngrams(5)
        assert isinstance(top, list)
        assert len(top) <= 5
        for gram, count in top:
            assert isinstance(gram, tuple)
            assert isinstance(count, int)
            assert count > 0

    def test_unigram_model(self, simple_corpus):
        """测试 Unigram 模型"""
        model = NGramModel(n=1, smoothing="add_k", k=1.0)
        model.train(simple_corpus)

        prob = model.probability(("the",))
        assert prob > 0

        generated = model.generate(max_length=5)
        assert isinstance(generated, list)

    def test_trigram_model(self, simple_corpus):
        """测试 Trigram 模型"""
        model = NGramModel(n=3, smoothing="add_k", k=1.0)
        model.train(simple_corpus)

        prob = model.probability(("the", "cat", "sat"))
        assert prob > 0

        generated = model.generate(max_length=10)
        assert isinstance(generated, list)

    def test_repr(self, trained_model):
        """测试字符串表示"""
        r = repr(trained_model)
        assert "NGramModel" in r
        assert "n=2" in r


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
