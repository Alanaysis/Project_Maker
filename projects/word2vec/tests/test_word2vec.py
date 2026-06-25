"""Word2Vec 集成测试"""

import pytest
import numpy as np
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.word2vec import Word2Vec


class TestWord2Vec:
    """Word2Vec 测试类"""

    @pytest.fixture
    def simple_corpus(self):
        """简单测试语料"""
        return [
            ["the", "king", "loves", "the", "queen"],
            ["the", "queen", "loves", "the", "king"],
            ["the", "prince", "is", "the", "son", "of", "the", "king"],
            ["the", "princess", "is", "the", "daughter", "of", "the", "queen"],
            ["a", "king", "is", "a", "man"],
            ["a", "queen", "is", "a", "woman"],
            ["a", "prince", "is", "a", "boy"],
            ["a", "princess", "is", "a", "girl"]
        ]

    @pytest.fixture
    def trained_model(self, simple_corpus):
        """已训练的模型"""
        model = Word2Vec(vector_size=50, window=3, min_count=1, negative=3)
        model.train(simple_corpus * 10, epochs=20, verbose=False)
        return model

    def test_init(self):
        """测试初始化"""
        model = Word2Vec(vector_size=100, window=5, min_count=5)
        assert model.vector_size == 100
        assert model.window == 5
        assert model.min_count == 5
        assert not model.is_trained

    def test_train(self, simple_corpus):
        """测试训练"""
        model = Word2Vec(vector_size=50, window=3, min_count=1, negative=3)
        losses = model.train(simple_corpus * 5, epochs=10, verbose=False)

        assert model.is_trained
        assert len(losses) == 10
        assert all(isinstance(l, float) for l in losses)

    def test_get_vector(self, trained_model):
        """测试获取词向量"""
        vec = trained_model.get_vector("king")
        assert vec is not None
        assert len(vec) == 50

    def test_get_vector_unknown(self, trained_model):
        """测试获取未知词向量"""
        vec = trained_model.get_vector("unknown")
        assert vec is None

    def test_most_similar(self, trained_model):
        """测试相似词查询"""
        similar = trained_model.most_similar("king", topn=3)
        assert len(similar) <= 3
        assert all(isinstance(s, tuple) for s in similar)
        assert all(len(s) == 2 for s in similar)
        assert all(isinstance(s[0], str) for s in similar)
        assert all(isinstance(s[1], float) for s in similar)

    def test_similarity(self, trained_model):
        """测试词相似度计算"""
        sim = trained_model.similarity("king", "queen")
        assert -1 <= sim <= 1

    def test_similarity_unknown(self, trained_model):
        """测试未知词相似度"""
        sim = trained_model.similarity("king", "unknown")
        assert sim == 0.0

    def test_vocab_size(self, trained_model):
        """测试词汇表大小"""
        assert trained_model.vocab_size > 0

    def test_empty_corpus(self):
        """测试空语料"""
        model = Word2Vec(min_count=1)
        with pytest.raises(ValueError):
            model.train([])

    def test_low_min_count(self):
        """测试低词频阈值"""
        corpus = [["a", "b", "c"]] * 10
        model = Word2Vec(min_count=1, subsample_threshold=0)
        model.train(corpus, epochs=5, verbose=False)
        assert model.vocab_size == 3

    def test_high_min_count(self):
        """测试高词频阈值"""
        corpus = [["a", "b", "c"]]
        model = Word2Vec(min_count=10)
        with pytest.raises(ValueError):
            model.train(corpus, epochs=5, verbose=False)


class TestWord2VecIntegration:
    """Word2Vec 集成测试"""

    def test_analogy(self):
        """测试词类比功能"""
        # 生成更多语料以确保语义关系
        corpus = []
        for _ in range(50):
            corpus.append(["king", "is", "a", "man"])
            corpus.append(["queen", "is", "a", "woman"])
            corpus.append(["prince", "is", "a", "boy"])
            corpus.append(["princess", "is", "a", "girl"])
            corpus.append(["king", "and", "queen", "are", "royal"])
            corpus.append(["man", "and", "woman", "are", "people"])

        model = Word2Vec(vector_size=50, window=3, min_count=1, negative=3)
        model.train(corpus, epochs=30, verbose=False)

        # 测试类比
        result = model.analogy("king", "man", topn=5)
        # 由于训练数据有限，可能不会完美，但应该返回结果
        assert len(result) > 0

    def test_save_load(self, tmp_path):
        """测试保存和加载"""
        corpus = [["hello", "world"]] * 20
        model = Word2Vec(vector_size=50, min_count=1, subsample_threshold=0)
        model.train(corpus, epochs=10, verbose=False)

        # 保存
        filepath = str(tmp_path / "model")
        model.save(filepath)

        # 加载
        loaded = Word2Vec.load(filepath)
        assert loaded.is_trained
        assert loaded.vocab_size == model.vocab_size

        # 比较词向量
        vec1 = model.get_vector("hello")
        vec2 = loaded.get_vector("hello")
        assert np.allclose(vec1, vec2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
