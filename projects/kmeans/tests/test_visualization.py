"""
可视化测试
"""

import unittest
import numpy as np
import sys
import os
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.visualization import (plot_clusters, plot_elbow, plot_2d_clusters,
                               plot_3d_clusters, plot_cluster_distribution,
                               plot_convergence)
from src.utils import generate_clustered_data


class TestVisualization(unittest.TestCase):
    """可视化测试类"""

    def setUp(self):
        """测试前准备"""
        self.X, self.y = generate_clustered_data(
            n_samples=100, n_clusters=3, n_features=2, random_state=42
        )

        # 模拟聚类结果
        self.labels = self.y
        self.centroids = np.array([
            np.mean(self.X[self.labels == k], axis=0)
            for k in range(3)
        ])

    def test_plot_clusters_2d(self):
        """测试 2D 聚类绘图"""
        fig = plot_clusters(self.X, self.labels, self.centroids, title="Test 2D")

        # 检查返回的是 Figure 对象
        self.assertIsNotNone(fig)

        # 清理
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_clusters_3d(self):
        """测试 3D 聚类绘图"""
        X_3d = np.random.randn(100, 3)
        labels_3d = np.random.randint(0, 3, 100)
        centroids_3d = np.random.randn(3, 3)

        fig = plot_clusters(X_3d, labels_3d, centroids_3d, title="Test 3D")

        # 检查返回的是 Figure 对象
        self.assertIsNotNone(fig)

        # 清理
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_2d_clusters(self):
        """测试 2D 聚类绘图函数"""
        fig = plot_2d_clusters(self.X, self.labels, self.centroids, title="Test 2D Clusters")

        self.assertIsNotNone(fig)

        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_3d_clusters(self):
        """测试 3D 聚类绘图函数"""
        X_3d = np.random.randn(100, 3)
        labels_3d = np.random.randint(0, 3, 100)
        centroids_3d = np.random.randn(3, 3)

        fig = plot_3d_clusters(X_3d, labels_3d, centroids_3d, title="Test 3D Clusters")

        self.assertIsNotNone(fig)

        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_elbow(self):
        """测试肘部法则图"""
        k_range = [1, 2, 3, 4, 5]
        wcss_list = [1000, 500, 200, 150, 140]

        fig = plot_elbow(wcss_list, k_range, title="Test Elbow")

        self.assertIsNotNone(fig)

        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_cluster_distribution(self):
        """测试簇分布图"""
        labels = np.random.randint(0, 3, 100)

        fig = plot_cluster_distribution(labels, title="Test Distribution")

        self.assertIsNotNone(fig)

        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_convergence(self):
        """测试收敛历史图"""
        inertia_history = [1000, 500, 300, 200, 150, 140, 135]

        fig = plot_convergence(inertia_history, title="Test Convergence")

        self.assertIsNotNone(fig)

        import matplotlib.pyplot as plt
        plt.close(fig)


class TestVisualizationEdgeCases(unittest.TestCase):
    """可视化边界情况测试"""

    def test_single_cluster(self):
        """测试单个簇"""
        X = np.random.randn(50, 2)
        labels = np.zeros(50, dtype=int)
        centroids = np.mean(X, axis=0).reshape(1, -1)

        fig = plot_clusters(X, labels, centroids, title="Single Cluster")

        self.assertIsNotNone(fig)

        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_many_clusters(self):
        """测试多个簇"""
        X = np.random.randn(100, 2)
        labels = np.random.randint(0, 10, 100)
        centroids = np.random.randn(10, 2)

        fig = plot_clusters(X, labels, centroids, title="Many Clusters")

        self.assertIsNotNone(fig)

        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_custom_figsize(self):
        """测试自定义图表大小"""
        X = np.random.randn(50, 2)
        labels = np.random.randint(0, 3, 50)
        centroids = np.random.randn(3, 2)

        fig = plot_clusters(X, labels, centroids, figsize=(12, 10))

        self.assertIsNotNone(fig)

        import matplotlib.pyplot as plt
        plt.close(fig)


if __name__ == '__main__':
    unittest.main()