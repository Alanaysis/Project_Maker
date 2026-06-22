"""
K-Means 核心算法测试
"""

import unittest
import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kmeans import KMeans
from src.utils import generate_clustered_data


class TestKMeans(unittest.TestCase):
    """K-Means 算法测试类"""

    def setUp(self):
        """测试前准备"""
        self.X, self.y = generate_clustered_data(
            n_samples=300, n_clusters=4, n_features=2, random_state=42
        )

    def test_basic_clustering(self):
        """测试基本聚类功能"""
        kmeans = KMeans(n_clusters=4, random_state=42)
        labels = kmeans.fit_predict(self.X)

        # 检查返回的标签形状
        self.assertEqual(labels.shape, (300,))

        # 检查簇的数量
        unique_labels = np.unique(labels)
        self.assertEqual(len(unique_labels), 4)

        # 检查标签范围
        self.assertTrue(all(0 <= label < 4 for label in labels))

    def test_fit_predict_consistency(self):
        """测试 fit 和 predict 的一致性"""
        kmeans = KMeans(n_clusters=4, random_state=42)

        # 先 fit 再 predict
        kmeans.fit(self.X)
        labels1 = kmeans.labels_
        labels2 = kmeans.predict(self.X)

        # 结果应该一致
        np.testing.assert_array_equal(labels1, labels2)

    def test_cluster_centers_shape(self):
        """测试簇中心的形状"""
        kmeans = KMeans(n_clusters=4, random_state=42)
        kmeans.fit(self.X)

        self.assertEqual(kmeans.cluster_centers_.shape, (4, 2))

    def test_inertia_calculation(self):
        """测试 WCSS 计算"""
        kmeans = KMeans(n_clusters=4, random_state=42)
        kmeans.fit(self.X)

        # WCSS 应该是正数
        self.assertGreater(kmeans.inertia_, 0)

        # 手动计算 WCSS
        wcss = 0
        for k in range(4):
            cluster_points = self.X[kmeans.labels_ == k]
            center = kmeans.cluster_centers_[k]
            distances = np.sqrt(np.sum((cluster_points - center) ** 2, axis=1))
            wcss += np.sum(distances ** 2)

        self.assertAlmostEqual(kmeans.inertia_, wcss, places=10)

    def test_convergence(self):
        """测试收敛性"""
        kmeans = KMeans(n_clusters=4, max_iter=100, tol=1e-4, random_state=42)
        kmeans.fit(self.X)

        # 应该在最大迭代次数内收敛
        self.assertLessEqual(kmeans.n_iter_, 100)

    def test_different_k_values(self):
        """测试不同的 K 值"""
        for k in [2, 3, 4, 5]:
            kmeans = KMeans(n_clusters=k, random_state=42)
            kmeans.fit(self.X)

            # 检查结果
            self.assertEqual(kmeans.cluster_centers_.shape[0], k)
            self.assertEqual(len(np.unique(kmeans.labels_)), k)

    def test_distance_metrics(self):
        """测试不同的距离度量"""
        for distance in ['euclidean', 'manhattan']:
            kmeans = KMeans(n_clusters=4, distance=distance, random_state=42)
            kmeans.fit(self.X)

            # 检查结果
            self.assertEqual(kmeans.cluster_centers_.shape, (4, 2))
            self.assertEqual(len(np.unique(kmeans.labels_)), 4)

    def test_init_methods(self):
        """测试不同的初始化方法"""
        for init in ['random', 'kmeans++']:
            kmeans = KMeans(n_clusters=4, init=init, random_state=42)
            kmeans.fit(self.X)

            # 检查结果
            self.assertEqual(kmeans.cluster_centers_.shape, (4, 2))
            self.assertEqual(len(np.unique(kmeans.labels_)), 4)

    def test_random_state_reproducibility(self):
        """测试随机种子的可重复性"""
        kmeans1 = KMeans(n_clusters=4, random_state=42)
        labels1 = kmeans1.fit_predict(self.X)

        kmeans2 = KMeans(n_clusters=4, random_state=42)
        labels2 = kmeans2.fit_predict(self.X)

        # 结果应该完全一致
        np.testing.assert_array_equal(labels1, labels2)
        np.testing.assert_array_equal(kmeans1.cluster_centers_, kmeans2.cluster_centers_)

    def test_input_validation(self):
        """测试输入验证"""
        # 测试无效的 K 值
        with self.assertRaises(ValueError):
            kmeans = KMeans(n_clusters=0, random_state=42)
            kmeans.fit(self.X)

        # 测试 K 值大于样本数
        with self.assertRaises(ValueError):
            kmeans = KMeans(n_clusters=400, random_state=42)
            kmeans.fit(self.X)

        # 测试无效的距离函数
        with self.assertRaises(ValueError):
            kmeans = KMeans(n_clusters=4, distance='invalid', random_state=42)
            kmeans.fit(self.X)

        # 测试无效的初始化方法
        with self.assertRaises(ValueError):
            kmeans = KMeans(n_clusters=4, init='invalid', random_state=42)
            kmeans.fit(self.X)

    def test_nan_handling(self):
        """测试 NaN 处理"""
        X_with_nan = self.X.copy()
        X_with_nan[0, 0] = np.nan

        with self.assertRaises(ValueError):
            kmeans = KMeans(n_clusters=4, random_state=42)
            kmeans.fit(X_with_nan)

    def test_1d_data(self):
        """测试一维数据"""
        X_1d = np.random.randn(100)
        kmeans = KMeans(n_clusters=3, random_state=42)
        kmeans.fit(X_1d)

        # 检查结果
        self.assertEqual(kmeans.cluster_centers_.shape, (3, 1))
        self.assertEqual(len(np.unique(kmeans.labels_)), 3)

    def test_3d_data(self):
        """测试三维数据"""
        X_3d = np.random.randn(100, 3)
        kmeans = KMeans(n_clusters=3, random_state=42)
        kmeans.fit(X_3d)

        # 检查结果
        self.assertEqual(kmeans.cluster_centers_.shape, (3, 3))
        self.assertEqual(len(np.unique(kmeans.labels_)), 3)

    def test_score_method(self):
        """测试 score 方法"""
        kmeans = KMeans(n_clusters=4, random_state=42)
        kmeans.fit(self.X)

        score = kmeans.score(self.X)

        # score 应该是负数
        self.assertLess(score, 0)

        # score 的绝对值应该等于 WCSS
        self.assertAlmostEqual(abs(score), kmeans.inertia_, places=10)

    def test_get_set_params(self):
        """测试参数获取和设置"""
        kmeans = KMeans(n_clusters=4, random_state=42)

        # 获取参数
        params = kmeans.get_params()
        self.assertEqual(params['n_clusters'], 4)
        self.assertEqual(params['random_state'], 42)

        # 设置参数
        kmeans.set_params(n_clusters=5)
        self.assertEqual(kmeans.n_clusters, 5)


class TestKMeansEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def test_single_cluster(self):
        """测试单个簇"""
        X = np.random.randn(50, 2)
        kmeans = KMeans(n_clusters=1, random_state=42)
        kmeans.fit(X)

        self.assertEqual(kmeans.cluster_centers_.shape, (1, 2))
        self.assertTrue(all(label == 0 for label in kmeans.labels_))

    def test_two_clusters(self):
        """测试两个簇"""
        X = np.vstack([
            np.random.randn(50, 2) + [0, 0],
            np.random.randn(50, 2) + [5, 5]
        ])
        kmeans = KMeans(n_clusters=2, random_state=42)
        kmeans.fit(X)

        self.assertEqual(kmeans.cluster_centers_.shape, (2, 2))
        self.assertEqual(len(np.unique(kmeans.labels_)), 2)

    def test_large_k(self):
        """测试较大的 K 值"""
        X = np.random.randn(100, 2)
        kmeans = KMeans(n_clusters=10, random_state=42)
        kmeans.fit(X)

        self.assertEqual(kmeans.cluster_centers_.shape, (10, 2))

    def test_high_dimensional_data(self):
        """测试高维数据"""
        X = np.random.randn(100, 10)
        kmeans = KMeans(n_clusters=5, random_state=42)
        kmeans.fit(X)

        self.assertEqual(kmeans.cluster_centers_.shape, (5, 10))
        self.assertEqual(len(np.unique(kmeans.labels_)), 5)


if __name__ == '__main__':
    unittest.main()