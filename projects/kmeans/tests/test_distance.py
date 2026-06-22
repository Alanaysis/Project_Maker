"""
距离度量测试
"""

import unittest
import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.distance import euclidean_distance, manhattan_distance, cosine_distance, pairwise_distances


class TestEuclideanDistance(unittest.TestCase):
    """欧氏距离测试"""

    def test_single_vectors(self):
        """测试单个向量"""
        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])

        distance = euclidean_distance(x, y)
        expected = np.sqrt(9 + 9 + 9)

        self.assertAlmostEqual(distance, expected, places=10)

    def test_zero_distance(self):
        """测试零距离"""
        x = np.array([1, 2, 3])
        y = np.array([1, 2, 3])

        distance = euclidean_distance(x, y)
        self.assertAlmostEqual(distance, 0.0, places=10)

    def test_2d_to_1d(self):
        """测试矩阵到向量"""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([1, 2])

        distances = euclidean_distance(X, y)
        expected = np.array([0, np.sqrt(8), np.sqrt(32)])

        np.testing.assert_array_almost_equal(distances, expected, decimal=10)

    def test_1d_to_2d(self):
        """测试向量到矩阵"""
        x = np.array([1, 2])
        Y = np.array([[1, 2], [3, 4], [5, 6]])

        distances = euclidean_distance(x, Y)
        expected = np.array([0, np.sqrt(8), np.sqrt(32)])

        np.testing.assert_array_almost_equal(distances, expected, decimal=10)

    def test_2d_to_2d(self):
        """测试矩阵到矩阵"""
        X = np.array([[1, 2], [3, 4]])
        Y = np.array([[1, 2], [5, 6]])

        distances = euclidean_distance(X, Y)
        expected = np.array([[0, np.sqrt(32)], [np.sqrt(8), np.sqrt(8)]])

        np.testing.assert_array_almost_equal(distances, expected, decimal=10)

    def test_symmetry(self):
        """测试对称性"""
        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])

        d1 = euclidean_distance(x, y)
        d2 = euclidean_distance(y, x)

        self.assertAlmostEqual(d1, d2, places=10)


class TestManhattanDistance(unittest.TestCase):
    """曼哈顿距离测试"""

    def test_single_vectors(self):
        """测试单个向量"""
        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])

        distance = manhattan_distance(x, y)
        expected = 9

        self.assertAlmostEqual(distance, expected, places=10)

    def test_zero_distance(self):
        """测试零距离"""
        x = np.array([1, 2, 3])
        y = np.array([1, 2, 3])

        distance = manhattan_distance(x, y)
        self.assertAlmostEqual(distance, 0.0, places=10)

    def test_2d_to_1d(self):
        """测试矩阵到向量"""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([1, 2])

        distances = manhattan_distance(X, y)
        expected = np.array([0, 4, 8])

        np.testing.assert_array_almost_equal(distances, expected, decimal=10)

    def test_symmetry(self):
        """测试对称性"""
        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])

        d1 = manhattan_distance(x, y)
        d2 = manhattan_distance(y, x)

        self.assertAlmostEqual(d1, d2, places=10)


class TestCosineDistance(unittest.TestCase):
    """余弦距离测试"""

    def test_same_direction(self):
        """测试相同方向"""
        x = np.array([1, 2, 3])
        y = np.array([2, 4, 6])

        distance = cosine_distance(x, y)
        self.assertAlmostEqual(distance, 0.0, places=10)

    def test_orthogonal(self):
        """测试正交向量"""
        x = np.array([1, 0, 0])
        y = np.array([0, 1, 0])

        distance = cosine_distance(x, y)
        self.assertAlmostEqual(distance, 1.0, places=10)

    def test_opposite_direction(self):
        """测试相反方向"""
        x = np.array([1, 2, 3])
        y = np.array([-1, -2, -3])

        distance = cosine_distance(x, y)
        self.assertAlmostEqual(distance, 2.0, places=10)

    def test_zero_vector(self):
        """测试零向量"""
        x = np.array([0, 0, 0])
        y = np.array([1, 2, 3])

        distance = cosine_distance(x, y)
        self.assertAlmostEqual(distance, 1.0, places=10)

    def test_2d_to_1d(self):
        """测试矩阵到向量"""
        X = np.array([[1, 2], [3, 4]])
        y = np.array([1, 2])

        distances = cosine_distance(X, y)
        expected = np.array([0.0, cosine_distance(np.array([3, 4]), y)])

        np.testing.assert_array_almost_equal(distances, expected, decimal=10)


class TestPairwiseDistances(unittest.TestCase):
    """成对距离测试"""

    def test_euclidean_pairwise(self):
        """测试欧氏成对距离"""
        X = np.array([[1, 2], [3, 4]])
        Y = np.array([[1, 2], [5, 6]])

        distances = pairwise_distances(X, Y, metric='euclidean')
        expected = euclidean_distance(X, Y)

        np.testing.assert_array_almost_equal(distances, expected, decimal=10)

    def test_symmetric(self):
        """测试对称性"""
        X = np.array([[1, 2], [3, 4], [5, 6]])

        distances = pairwise_distances(X, metric='euclidean')

        # 应该是对称矩阵
        np.testing.assert_array_almost_equal(distances, distances.T, decimal=10)

    def test_diagonal_zero(self):
        """测试对角线为零"""
        X = np.array([[1, 2], [3, 4], [5, 6]])

        distances = pairwise_distances(X, metric='euclidean')

        # 对角线应该为零
        np.testing.assert_array_almost_equal(np.diag(distances), np.zeros(3), decimal=10)


if __name__ == '__main__':
    unittest.main()