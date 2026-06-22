import unittest
import numpy as np
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.decision_tree import DecisionTreeClassifier, TreeNode

class TestTreeNode(unittest.TestCase):
    """测试TreeNode类"""

    def test_leaf_node(self):
        """测试叶节点"""
        node = TreeNode(value=0)
        self.assertTrue(node.is_leaf_node())
        self.assertEqual(node.value, 0)
        self.assertIsNone(node.feature_index)
        self.assertIsNone(node.threshold)
        self.assertIsNone(node.left)
        self.assertIsNone(node.right)

    def test_internal_node(self):
        """测试内部节点"""
        left = TreeNode(value=0)
        right = TreeNode(value=1)
        node = TreeNode(feature_index=0, threshold=0.5, left=left, right=right)

        self.assertFalse(node.is_leaf_node())
        self.assertEqual(node.feature_index, 0)
        self.assertEqual(node.threshold, 0.5)
        self.assertEqual(node.left.value, 0)
        self.assertEqual(node.right.value, 1)

class TestDecisionTreeClassifier(unittest.TestCase):
    """测试DecisionTreeClassifier类"""

    def setUp(self):
        """测试前准备"""
        # 创建简单数据集
        self.X = np.array([
            [0, 0],
            [0, 1],
            [1, 0],
            [1, 1]
        ])
        self.y = np.array([0, 0, 1, 1])

        # 创建更复杂的数据集
        np.random.seed(42)
        n_samples = 100
        self.X_complex = np.random.randn(n_samples, 2)
        self.y_complex = (self.X_complex[:, 0] + self.X_complex[:, 1] > 0).astype(int)

    def test_initialization(self):
        """测试初始化"""
        dt = DecisionTreeClassifier(max_depth=5, min_samples_split=10)
        self.assertEqual(dt.max_depth, 5)
        self.assertEqual(dt.min_samples_split, 10)
        self.assertEqual(dt.min_samples_leaf, 1)
        self.assertEqual(dt.criterion, 'entropy')

    def test_fit(self):
        """测试训练"""
        dt = DecisionTreeClassifier(max_depth=3)
        dt.fit(self.X, self.y)

        # 检查模型是否已训练
        self.assertIsNotNone(dt.root)
        self.assertEqual(dt.n_features, 2)
        self.assertEqual(dt.n_classes, 2)
        self.assertEqual(len(dt.classes), 2)

    def test_predict(self):
        """测试预测"""
        dt = DecisionTreeClassifier(max_depth=3)
        dt.fit(self.X, self.y)

        predictions = dt.predict(self.X)
        self.assertEqual(len(predictions), len(self.y))
        self.assertTrue(all(pred in [0, 1] for pred in predictions))

    def test_predict_before_fit(self):
        """测试在训练前预测"""
        dt = DecisionTreeClassifier()
        with self.assertRaises(ValueError):
            dt.predict(self.X)

    def test_score(self):
        """测试评分"""
        dt = DecisionTreeClassifier(max_depth=3)
        dt.fit(self.X, self.y)

        accuracy = dt.score(self.X, self.y)
        self.assertGreaterEqual(accuracy, 0)
        self.assertLessEqual(accuracy, 1)

    def test_simple_dataset(self):
        """测试简单数据集"""
        dt = DecisionTreeClassifier(max_depth=3)
        dt.fit(self.X, self.y)

        # 对于这个简单的数据集，应该能达到100%准确率
        accuracy = dt.score(self.X, self.y)
        self.assertEqual(accuracy, 1.0)

    def test_complex_dataset(self):
        """测试复杂数据集"""
        dt = DecisionTreeClassifier(max_depth=5)
        dt.fit(self.X_complex, self.y_complex)

        accuracy = dt.score(self.X_complex, self.y_complex)
        self.assertGreater(accuracy, 0.5)  # 应该比随机猜测好

    def test_max_depth(self):
        """测试最大深度限制"""
        # 创建应该需要更深树的数据集
        np.random.seed(42)
        X = np.random.randn(100, 2)
        y = (X[:, 0] > 0).astype(int)

        # 测试不同深度
        for max_depth in [1, 2, 3, 5]:
            dt = DecisionTreeClassifier(max_depth=max_depth)
            dt.fit(X, y)
            accuracy = dt.score(X, y)
            self.assertGreaterEqual(accuracy, 0)
            self.assertLessEqual(accuracy, 1)

    def test_min_samples_split(self):
        """测试最小分裂样本数"""
        dt = DecisionTreeClassifier(min_samples_split=50)
        dt.fit(self.X_complex, self.y_complex)

        accuracy = dt.score(self.X_complex, self.y_complex)
        self.assertGreaterEqual(accuracy, 0)

    def test_min_samples_leaf(self):
        """测试最小叶节点样本数"""
        dt = DecisionTreeClassifier(min_samples_leaf=10)
        dt.fit(self.X_complex, self.y_complex)

        accuracy = dt.score(self.X_complex, self.y_complex)
        self.assertGreaterEqual(accuracy, 0)

    def test_criterion_gini(self):
        """测试基尼指数标准"""
        dt = DecisionTreeClassifier(criterion='gini', max_depth=3)
        dt.fit(self.X, self.y)

        accuracy = dt.score(self.X, self.y)
        self.assertEqual(accuracy, 1.0)

    def test_criterion_entropy(self):
        """测试熵标准"""
        dt = DecisionTreeClassifier(criterion='entropy', max_depth=3)
        dt.fit(self.X, self.y)

        accuracy = dt.score(self.X, self.y)
        self.assertEqual(accuracy, 1.0)

    def test_invalid_criterion(self):
        """测试无效的分裂标准"""
        dt = DecisionTreeClassifier(criterion='invalid')
        # 应该抛出异常或使用默认值
        # 这里我们测试它是否能正常处理
        dt.fit(self.X, self.y)
        self.assertIsNotNone(dt.root)

    def test_input_validation(self):
        """测试输入验证"""
        dt = DecisionTreeClassifier()

        # 测试一维X
        with self.assertRaises(ValueError):
            dt.fit(np.array([1, 2, 3]), self.y)

        # 测试二维y
        with self.assertRaises(ValueError):
            dt.fit(self.X, np.array([[0, 1], [1, 0]]))

        # 测试样本数不匹配
        with self.assertRaises(ValueError):
            dt.fit(self.X, np.array([0, 1]))

    def test_print_tree(self):
        """测试打印决策树"""
        dt = DecisionTreeClassifier(max_depth=3)
        dt.fit(self.X, self.y)

        # 这个方法应该不抛出异常
        dt.print_tree()

    def test_get_params(self):
        """测试获取参数"""
        dt = DecisionTreeClassifier(max_depth=5, min_samples_split=10, criterion='gini')
        params = dt.get_params()

        self.assertEqual(params['max_depth'], 5)
        self.assertEqual(params['min_samples_split'], 10)
        self.assertEqual(params['criterion'], 'gini')

    def test_large_dataset(self):
        """测试大数据集"""
        np.random.seed(42)
        X = np.random.randn(1000, 10)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)

        dt = DecisionTreeClassifier(max_depth=10)
        dt.fit(X, y)

        accuracy = dt.score(X, y)
        self.assertGreater(accuracy, 0.7)

    def test_multiclass(self):
        """测试多分类问题"""
        np.random.seed(42)
        X = np.random.randn(150, 4)
        y = np.array([0]*50 + [1]*50 + [2]*50)

        dt = DecisionTreeClassifier(max_depth=5)
        dt.fit(X, y)

        accuracy = dt.score(X, y)
        self.assertGreater(accuracy, 0.3)

    def test_binary_split(self):
        """测试二叉分裂"""
        # 创建一个需要多次分裂的数据集
        np.random.seed(42)
        X = np.array([
            [0, 0, 0],
            [0, 0, 1],
            [0, 1, 0],
            [0, 1, 1],
            [1, 0, 0],
            [1, 0, 1],
            [1, 1, 0],
            [1, 1, 1]
        ])
        y = np.array([0, 0, 0, 1, 0, 1, 1, 1])

        dt = DecisionTreeClassifier(max_depth=3)
        dt.fit(X, y)

        predictions = dt.predict(X)
        np.testing.assert_array_equal(predictions, y)

if __name__ == '__main__':
    unittest.main()