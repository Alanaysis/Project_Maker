"""评估模块测试"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.evaluation import WordSimilarityEvaluator, AnalogyEvaluator, TSNEVisualizer, WordClustering


class TestWordSimilarityEvaluator:
    """词相似度评估器测试"""

    @pytest.fixture
    def evaluator(self):
        """创建评估器实例"""
        vectors = np.random.randn(10, 50)
        word2idx = {f"word{i}": i for i in range(10)}
        return WordSimilarityEvaluator(vectors, word2idx)

    def test_cosine_similarity_self(self, evaluator):
        """测试自身相似度"""
        sim = evaluator.cosine_similarity("word0", "word0")
        assert sim == pytest.approx(1.0, abs=1e-5)

    def test_cosine_similarity_range(self, evaluator):
        """测试相似度范围"""
        sim = evaluator.cosine_similarity("word0", "word1")
        assert -1 <= sim <= 1

    def test_cosine_similarity_unknown(self, evaluator):
        """测试未知词相似度"""
        sim = evaluator.cosine_similarity("unknown", "word0")
        assert sim == 0.0

    def test_evaluate(self, evaluator):
        """测试评估"""
        word_pairs = [
            ("word0", "word1", 0.8),
            ("word2", "word3", 0.3),
            ("word4", "word5", 0.5),
        ]
        rho = evaluator.evaluate(word_pairs)
        assert -1 <= rho <= 1

    def test_spearman_correlation(self):
        """测试 Spearman 相关系数"""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.1, 2.2, 2.8, 4.1, 5.0]
        rho = WordSimilarityEvaluator._spearman_correlation(x, y)
        assert rho > 0.9  # 应该高度相关


class TestAnalogyEvaluator:
    """词类比评估器测试"""

    @pytest.fixture
    def evaluator(self):
        """创建评估器实例"""
        # 创建有语义关系的向量
        vectors = np.random.randn(10, 50)
        word2idx = {f"word{i}": i for i in range(10)}
        idx2word = {i: f"word{i}" for i in range(10)}
        return AnalogyEvaluator(vectors, word2idx, idx2word)

    def test_analogy(self, evaluator):
        """测试类比"""
        results = evaluator.analogy("word0", "word1", "word2", topn=3)
        assert len(results) <= 3
        assert all(isinstance(w, str) for w, _ in results)

    def test_analogy_unknown(self, evaluator):
        """测试未知词类比"""
        results = evaluator.analogy("unknown", "word1", "word2")
        assert results == []

    def test_evaluate(self, evaluator):
        """测试评估"""
        analogy_pairs = [
            ("word0", "word1", "word2", "word3"),
            ("word4", "word5", "word6", "word7"),
        ]
        accuracy = evaluator.evaluate(analogy_pairs)
        assert 0 <= accuracy <= 1


class TestTSNEVisualizer:
    """t-SNE 可视化器测试"""

    def test_pca_reduce(self):
        """测试 PCA 降维"""
        vectors = np.random.randn(20, 50)
        reduced = TSNEVisualizer.pca_reduce(vectors, n_components=2)
        assert reduced.shape == (20, 2)

    def test_pca_reduce_3d(self):
        """测试 PCA 降到 3 维"""
        vectors = np.random.randn(20, 50)
        reduced = TSNEVisualizer.pca_reduce(vectors, n_components=3)
        assert reduced.shape == (20, 3)

    def test_tsne_reduce(self):
        """测试 t-SNE 降维"""
        vectors = np.random.randn(10, 20)
        reduced = TSNEVisualizer.tsne_reduce(vectors, n_components=2,
                                              perplexity=3.0, n_iter=100)
        assert reduced.shape == (10, 2)

    def test_tsne_reduce_single(self):
        """测试单个向量 t-SNE"""
        vectors = np.random.randn(1, 20)
        reduced = TSNEVisualizer.tsne_reduce(vectors, n_components=2)
        assert reduced.shape == (1, 2)


class TestWordClustering:
    """词聚类测试"""

    def test_kmeans(self):
        """测试 K-Means 聚类"""
        # 创建明显的聚类
        cluster1 = np.random.randn(10, 5) + np.array([10, 0, 0, 0, 0])
        cluster2 = np.random.randn(10, 5) + np.array([0, 10, 0, 0, 0])
        vectors = np.vstack([cluster1, cluster2])

        labels, centroids = WordClustering.kmeans(vectors, k=2)
        assert len(labels) == 20
        assert centroids.shape == (2, 5)

    def test_get_clusters(self):
        """测试获取聚类结果"""
        words = ["a", "b", "c", "d"]
        labels = np.array([0, 0, 1, 1])
        clusters = WordClustering.get_clusters(words, labels, k=2)

        assert 0 in clusters
        assert 1 in clusters
        assert "a" in clusters[0]
        assert "c" in clusters[1]

    def test_evaluate_clustering(self):
        """测试聚类评估"""
        # 完美聚类
        cluster1 = np.random.randn(10, 5) + np.array([100, 0, 0, 0, 0])
        cluster2 = np.random.randn(10, 5) + np.array([0, 100, 0, 0, 0])
        vectors = np.vstack([cluster1, cluster2])

        labels, centroids = WordClustering.kmeans(vectors, k=2)
        score = WordClustering.evaluate_clustering(vectors, labels, centroids)

        # 良好聚类应该有正的轮廓系数
        assert score > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
