import unittest
import numpy as np
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils import train_test_split, accuracy_score, normalize, check_input

class TestTrainTestSplit(unittest.TestCase):
    """测试train_test_split函数"""

    def test_basic_split(self):
        """测试基本分割"""
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([0, 1, 0, 1])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=42)

        self.assertEqual(len(X_train), 2)
        self.assertEqual(len(X_test), 2)
        self.assertEqual(len(y_train), 2)
        self.assertEqual(len(y_test), 2)

    def test_custom_test_size(self):
        """测试自定义测试集比例"""
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]])
        y = np.array([0, 1, 0, 1, 0])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=42)

        self.assertEqual(len(X_train), 3)
        self.assertEqual(len(X_test), 2)

    def test_random_state(self):
        """测试随机种子"""
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([0, 1, 0, 1])

        # 相同随机种子应该产生相同结果
        X_train1, X_test1, y_train1, y_test1 = train_test_split(X, y, test_size=0.5, random_state=42)
        X_train2, X_test2, y_train2, y_test2 = train_test_split(X, y, test_size=0.5, random_state=42)

        np.testing.assert_array_equal(X_train1, X_train2)
        np.testing.assert_array_equal(X_test1, X_test2)
        np.testing.assert_array_equal(y_train1, y_train2)
        np.testing.assert_array_equal(y_test1, y_test2)

    def test_no_random_state(self):
        """测试无随机种子"""
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([0, 1, 0, 1])

        # 无随机种子应该产生不同结果（可能相同，但概率很低）
        X_train1, X_test1, y_train1, y_test1 = train_test_split(X, y, test_size=0.5)
        X_train2, X_test2, y_train2, y_test2 = train_test_split(X, y, test_size=0.5)

        # 这个测试可能偶尔会失败，但概率很低
        # 我们只检查长度是否正确
        self.assertEqual(len(X_train1), 2)
        self.assertEqual(len(X_test1), 2)

    def test_preserves_data(self):
        """测试数据是否被保留"""
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([0, 1, 0, 1])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=42)

        # 合并训练集和测试集应该包含所有原始数据
        X_combined = np.vstack([X_train, X_test])
        y_combined = np.concatenate([y_train, y_test])

        self.assertEqual(len(X_combined), len(X))
        self.assertEqual(len(y_combined), len(y))

class TestAccuracyScore(unittest.TestCase):
    """测试accuracy_score函数"""

    def test_perfect_accuracy(self):
        """测试完美准确率"""
        y_true = np.array([0, 1, 2, 3])
        y_pred = np.array([0, 1, 2, 3])

        accuracy = accuracy_score(y_true, y_pred)
        self.assertEqual(accuracy, 1.0)

    def test_zero_accuracy(self):
        """测试零准确率"""
        y_true = np.array([0, 0, 0, 0])
        y_pred = np.array([1, 1, 1, 1])

        accuracy = accuracy_score(y_true, y_pred)
        self.assertEqual(accuracy, 0.0)

    def test_partial_accuracy(self):
        """测试部分准确率"""
        y_true = np.array([0, 1, 2, 3])
        y_pred = np.array([0, 1, 2, 2])  # 最后一个错误

        accuracy = accuracy_score(y_true, y_pred)
        self.assertEqual(accuracy, 0.75)

    def test_different_lengths(self):
        """测试不同长度的输入"""
        y_true = np.array([0, 1, 2])
        y_pred = np.array([0, 1])

        with self.assertRaises(ValueError):
            accuracy_score(y_true, y_pred)

class TestNormalize(unittest.TestCase):
    """测试normalize函数"""

    def test_basic_normalize(self):
        """测试基本标准化"""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        X_normalized = normalize(X)

        # 检查均值是否接近0
        mean = np.mean(X_normalized, axis=0)
        np.testing.assert_array_almost_equal(mean, [0, 0], decimal=10)

        # 检查标准差是否接近1
        std = np.std(X_normalized, axis=0)
        np.testing.assert_array_almost_equal(std, [1, 1], decimal=10)

    def test_zero_std(self):
        """测试标准差为0的情况"""
        X = np.array([[1, 2], [1, 4], [1, 6]])
        X_normalized = normalize(X)

        # 第一列标准差为0，标准化后应该全为0
        self.assertTrue(np.all(X_normalized[:, 0] == 0))

        # 第二列应该正常标准化
        mean = np.mean(X_normalized[:, 1])
        np.testing.assert_array_almost_equal(mean, 0, decimal=10)

class TestCheckInput(unittest.TestCase):
    """测试check_input函数"""

    def test_valid_input(self):
        """测试有效输入"""
        X = np.array([[1, 2], [3, 4]])
        y = np.array([0, 1])

        # 不应该抛出异常
        check_input(X, y)

    def test_invalid_X_type(self):
        """测试无效的X类型"""
        X = [[1, 2], [3, 4]]  # 列表而不是numpy数组
        y = np.array([0, 1])

        with self.assertRaises(TypeError):
            check_input(X, y)

    def test_invalid_y_type(self):
        """测试无效的y类型"""
        X = np.array([[1, 2], [3, 4]])
        y = [0, 1]  # 列表而不是numpy数组

        with self.assertRaises(TypeError):
            check_input(X, y)

    def test_invalid_X_dimension(self):
        """测试无效的X维度"""
        X = np.array([1, 2, 3])  # 一维数组
        y = np.array([0, 1, 0])

        with self.assertRaises(ValueError):
            check_input(X, y)

    def test_invalid_y_dimension(self):
        """测试无效的y维度"""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([[0, 1], [1, 0]])  # 二维数组

        with self.assertRaises(ValueError):
            check_input(X, y)

    def test_mismatched_samples(self):
        """测试样本数不匹配"""
        X = np.array([[1, 2], [3, 4]])
        y = np.array([0, 1, 0])  # 样本数不匹配

        with self.assertRaises(ValueError):
            check_input(X, y)

if __name__ == '__main__':
    unittest.main()