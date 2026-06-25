"""
Ball Tree 测试用例
"""

import pytest
import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ball_tree import BallTree, BallNode


class TestBallTree:
    """Ball Tree 测试类"""

    def test_initialization(self):
        """测试初始化"""
        tree = BallTree(metric='euclidean', leaf_size=10)
        assert tree.metric == 'euclidean'
        assert tree.leaf_size == 10
        assert tree.root is None

    def test_initialization_invalid_metric(self):
        """测试无效距离度量"""
        with pytest.raises(ValueError):
            BallTree(metric='invalid')

    def test_build_basic(self):
        """测试基本建树功能"""
        X = np.array([[2, 3], [5, 4], [9, 6], [4, 7], [8, 1], [7, 2]])
        y = np.array([0, 0, 1, 0, 1, 1])

        tree = BallTree(metric='euclidean', leaf_size=2)
        tree.build(X, y)

        assert tree.root is not None
        assert tree.n_features == 2
        assert tree.get_size() > 0

    def test_build_validation(self):
        """测试建树时输入验证"""
        tree = BallTree()

        # 一维 X
        with pytest.raises(ValueError):
            tree.build(np.array([1, 2, 3]), np.array([0, 1, 0]))

        # 样本数量不匹配
        with pytest.raises(ValueError):
            tree.build(np.array([[1], [2]]), np.array([0, 1, 0]))

        # 空数据
        with pytest.raises(ValueError):
            tree.build(np.array([]).reshape(0, 1), np.array([]))

    def test_query_basic(self):
        """测试基本查询功能"""
        X = np.array([[2, 3], [5, 4], [9, 6], [4, 7], [8, 1], [7, 2]])
        y = np.array([0, 0, 1, 0, 1, 1])

        tree = BallTree(metric='euclidean', leaf_size=2)
        tree.build(X, y)

        # 查询最近邻
        indices, distances = tree.query(np.array([3, 4]), k=1)

        assert len(indices) == 1
        assert len(distances) == 1
        assert distances[0] >= 0

    def test_query_k_nearest(self):
        """测试 K 近邻查询"""
        X = np.array([[0, 0], [1, 0], [0, 1], [1, 1], [2, 2]])
        y = np.array([0, 0, 0, 1, 1])

        tree = BallTree(metric='euclidean', leaf_size=2)
        tree.build(X, y)

        # 查询 3 个最近邻
        indices, distances = tree.query(np.array([0.5, 0.5]), k=3)

        assert len(indices) == 3
        assert len(distances) == 3

        # 验证距离排序
        assert distances[0] <= distances[1] <= distances[2]

    def test_query_before_build(self):
        """测试未建树时查询"""
        tree = BallTree()

        with pytest.raises(RuntimeError):
            tree.query(np.array([1, 2]), k=1)

    def test_query_feature_mismatch(self):
        """测试特征数量不匹配"""
        X = np.array([[1, 2], [3, 4]])
        y = np.array([0, 1])

        tree = BallTree()
        tree.build(X, y)

        with pytest.raises(ValueError):
            tree.query(np.array([1, 2, 3]), k=1)

    def test_query_same_point(self):
        """测试查询相同点"""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([0, 1, 0])

        tree = BallTree(metric='euclidean', leaf_size=2)
        tree.build(X, y)

        # 查询训练数据中的点
        indices, distances = tree.query(np.array([3, 4]), k=1)

        assert distances[0] == 0.0

    def test_query_radius_basic(self):
        """测试半径查询"""
        X = np.array([[0, 0], [1, 0], [0, 1], [1, 1], [2, 2]])
        y = np.array([0, 0, 0, 1, 1])

        tree = BallTree(metric='euclidean', leaf_size=2)
        tree.build(X, y)

        # 查询半径 1.0 内的点
        indices, distances = tree.query_radius(np.array([0, 0]), radius=1.0)

        assert len(indices) == 3  # (0,0), (1,0), (0,1)
        assert all(d <= 1.0 for d in distances)

    def test_query_radius_no_match(self):
        """测试半径查询无匹配"""
        X = np.array([[10, 10], [20, 20]])
        y = np.array([0, 1])

        tree = BallTree(metric='euclidean', leaf_size=2)
        tree.build(X, y)

        # 半径太小
        indices, distances = tree.query_radius(np.array([0, 0]), radius=1.0)

        assert len(indices) == 0

    def test_manhattan_metric(self):
        """测试曼哈顿距离"""
        X = np.array([[0, 0], [1, 1], [2, 2]])
        y = np.array([0, 1, 0])

        tree = BallTree(metric='manhattan', leaf_size=2)
        tree.build(X, y)

        indices, distances = tree.query(np.array([1, 0]), k=1)

        # 最近的是 (1,1)，曼哈顿距离 = 1
        assert abs(distances[0] - 1.0) < 1e-10

    def test_cosine_metric(self):
        """测试余弦距离"""
        X = np.array([[1, 0], [0, 1], [1, 1]])
        y = np.array([0, 1, 0])

        tree = BallTree(metric='cosine', leaf_size=2)
        tree.build(X, y)

        indices, distances = tree.query(np.array([1, 0]), k=1)

        # 最近的是 [1,0]，余弦距离 = 0
        assert distances[0] < 1e-10

    def test_1d_data(self):
        """测试一维数据"""
        X = np.array([[1], [3], [5], [7], [9]])
        y = np.array([0, 0, 1, 1, 1])

        tree = BallTree(metric='euclidean', leaf_size=2)
        tree.build(X, y)

        indices, distances = tree.query(np.array([4]), k=2)

        assert len(indices) == 2

    def test_3d_data(self):
        """测试三维数据"""
        np.random.seed(42)
        X = np.random.randn(50, 3)
        y = np.random.randint(0, 3, 50)

        tree = BallTree(metric='euclidean', leaf_size=5)
        tree.build(X, y)

        indices, distances = tree.query(np.array([0, 0, 0]), k=5)

        assert len(indices) == 5

    def test_leaf_size(self):
        """测试叶节点大小"""
        X = np.array([[1], [2], [3], [4], [5], [6], [7], [8]])
        y = np.array([0, 0, 0, 0, 1, 1, 1, 1])

        # 叶节点大小为 2
        tree = BallTree(metric='euclidean', leaf_size=2)
        tree.build(X, y)

        # 树应该有更多节点
        size_small = tree.get_size()

        # 叶节点大小为 4
        tree = BallTree(metric='euclidean', leaf_size=4)
        tree.build(X, y)

        size_large = tree.get_size()

        # 叶节点越小，树越大
        assert size_small >= size_large

    def test_tree_depth(self):
        """测试树深度"""
        X = np.array([[1], [2], [3], [4], [5], [6], [7]])
        y = np.array([0, 0, 0, 1, 1, 1, 1])

        tree = BallTree(metric='euclidean', leaf_size=2)
        tree.build(X, y)

        depth = tree.get_depth()
        assert depth > 0

    def test_tree_size(self):
        """测试树大小"""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([0, 1, 0])

        tree = BallTree(metric='euclidean', leaf_size=2)
        tree.build(X, y)

        assert tree.get_size() > 0

    def test_accuracy_vs_brute_force(self):
        """测试与暴力搜索的一致性"""
        np.random.seed(42)
        X = np.random.randn(100, 2)
        y = np.random.randint(0, 3, 100)

        tree = BallTree(metric='euclidean', leaf_size=10)
        tree.build(X, y)

        query_point = np.array([0.5, 0.5])
        k = 5

        # Ball Tree 查询
        tree_indices, tree_distances = tree.query(query_point, k=k)

        # 暴力搜索
        brute_distances = np.sqrt(np.sum((X - query_point) ** 2, axis=1))
        brute_indices = np.argsort(brute_distances)[:k]

        # 结果应该一致（索引可能不同，但距离应该相同）
        tree_distances_sorted = np.sort(tree_distances)
        brute_distances_sorted = brute_distances[brute_indices]

        np.testing.assert_allclose(tree_distances_sorted, brute_distances_sorted, atol=1e-10)

    def test_large_dataset(self):
        """测试大数据集"""
        np.random.seed(42)
        X = np.random.randn(1000, 5)
        y = np.random.randint(0, 5, 1000)

        tree = BallTree(metric='euclidean', leaf_size=20)
        tree.build(X, y)

        indices, distances = tree.query(np.array([0, 0, 0, 0, 0]), k=10)

        assert len(indices) == 10


class TestBallNode:
    """BallNode 测试类"""

    def test_node_creation(self):
        """测试节点创建"""
        center = np.array([1, 2])
        node = BallNode(center=center, radius=5.0)

        np.testing.assert_array_equal(node.center, center)
        assert node.radius == 5.0
        assert node.left is None
        assert node.right is None
        assert not node.is_leaf

    def test_node_repr(self):
        """测试节点字符串表示"""
        node = BallNode(center=np.array([1, 2]), radius=5.0)
        repr_str = repr(node)

        assert 'BallNode' in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
