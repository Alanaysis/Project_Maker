"""应用模块测试"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.applications import TextClassifier, SentimentAnalyzer, WordClusterer


class TestTextClassifier:
    """文本分类器测试"""

    @pytest.fixture
    def classifier(self):
        """创建分类器实例"""
        vectors = np.random.randn(20, 50)
        word2idx = {f"word{i}": i for i in range(20)}
        return TextClassifier(vectors, word2idx)

    def test_sentence_vector(self, classifier):
        """测试句子向量计算"""
        words = ["word0", "word1", "word2"]
        vec = classifier._sentence_vector(words)
        assert vec is not None
        assert vec.shape == (50,)

    def test_sentence_vector_unknown(self, classifier):
        """测试未知词句子向量"""
        words = ["unknown1", "unknown2"]
        vec = classifier._sentence_vector(words)
        assert vec is None

    def test_train_and_predict(self, classifier):
        """测试训练和预测"""
        sentences = [
            ["word0", "word1"],
            ["word2", "word3"],
            ["word4", "word5"],
            ["word6", "word7"],
        ]
        labels = [0, 0, 1, 1]

        classifier.train(sentences, labels)
        assert classifier.trained

        pred = classifier.predict(["word0", "word1"])
        assert pred is not None
        assert pred in [0, 1]

    def test_predict_batch(self, classifier):
        """测试批量预测"""
        sentences = [
            ["word0", "word1"],
            ["word2", "word3"],
        ]
        labels = [0, 1]

        classifier.train(sentences, labels)
        predictions = classifier.predict_batch([["word0"], ["word2"]])
        assert len(predictions) == 2

    def test_evaluate(self, classifier):
        """测试评估"""
        sentences = [
            ["word0", "word1"],
            ["word2", "word3"],
        ]
        labels = [0, 1]

        classifier.train(sentences, labels)
        metrics = classifier.evaluate(sentences, labels)

        assert 'accuracy' in metrics
        assert 'total' in metrics
        assert 'correct' in metrics
        assert 0 <= metrics['accuracy'] <= 1


class TestSentimentAnalyzer:
    """情感分析器测试"""

    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        vectors = np.random.randn(20, 50)
        word2idx = {f"word{i}": i for i in range(20)}
        return SentimentAnalyzer(vectors, word2idx)

    def test_build_lexicon(self, analyzer):
        """测试构建情感词典"""
        positive = ["word0", "word1", "word2"]
        negative = ["word3", "word4", "word5"]

        analyzer.build_sentiment_lexicon(positive, negative)

        assert len(analyzer.positive_words) == 3
        assert len(analyzer.negative_words) == 3
        assert analyzer.positive_centroid is not None
        assert analyzer.negative_centroid is not None

    def test_analyze(self, analyzer):
        """测试情感分析"""
        positive = ["word0", "word1"]
        negative = ["word3", "word4"]
        analyzer.build_sentiment_lexicon(positive, negative)

        result = analyzer.analyze(["word0", "word1"])

        assert 'sentiment' in result
        assert 'positive_score' in result
        assert 'negative_score' in result
        # sentiment = pos_score - neg_score, 可能略超出 [-1, 1]
        assert -2 <= result['sentiment'] <= 2

    def test_analyze_unknown(self, analyzer):
        """测试未知词情感分析"""
        result = analyzer.analyze(["unknown1", "unknown2"])

        assert result['sentiment'] == 0.0
        assert result['positive_score'] == 0.0
        assert result['negative_score'] == 0.0

    def test_analyze_batch(self, analyzer):
        """测试批量情感分析"""
        positive = ["word0", "word1"]
        negative = ["word3", "word4"]
        analyzer.build_sentiment_lexicon(positive, negative)

        sentences = [["word0"], ["word3"]]
        results = analyzer.analyze_batch(sentences)

        assert len(results) == 2

    def test_evaluate(self, analyzer):
        """测试评估"""
        positive = ["word0", "word1"]
        negative = ["word3", "word4"]
        analyzer.build_sentiment_lexicon(positive, negative)

        sentences = [["word0"], ["word3"]]
        labels = [1, -1]

        metrics = analyzer.evaluate(sentences, labels)

        assert 'accuracy' in metrics
        assert 0 <= metrics['accuracy'] <= 1


class TestWordClusterer:
    """词聚类器测试"""

    @pytest.fixture
    def clusterer(self):
        """创建聚类器实例"""
        vectors = np.random.randn(20, 50)
        word2idx = {f"word{i}": i for i in range(20)}
        idx2word = {i: f"word{i}" for i in range(20)}
        return WordClusterer(vectors, word2idx, idx2word)

    def test_cluster(self, clusterer):
        """测试聚类"""
        words = [f"word{i}" for i in range(10)]
        clusters = clusterer.cluster(words, k=3)

        assert len(clusters) <= 3
        total_words = sum(len(v) for v in clusters.values())
        assert total_words == 10

    def test_cluster_unknown_words(self, clusterer):
        """测试包含未知词的聚类"""
        words = ["word0", "word1", "unknown1", "unknown2"]
        clusters = clusterer.cluster(words, k=2)

        # 只有已知词被聚类
        total_words = sum(len(v) for v in clusters.values())
        assert total_words == 2

    def test_cluster_summary(self, clusterer):
        """测试聚类摘要"""
        clusters = {0: ["a", "b"], 1: ["c", "d"]}
        summary = clusterer.get_cluster_summary(clusters)

        assert "Cluster 0" in summary
        assert "Cluster 1" in summary
        assert "a" in summary
        assert "c" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
