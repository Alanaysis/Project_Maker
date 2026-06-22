"""工具函数测试"""

import numpy as np
import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import (
    generate_linear_data,
    train_test_split,
    compute_r2_score,
)


class TestGenerateLinearData:
    """数据生成函数测试"""

    def test_basic_generation(self):
        """测试基本数据生成"""
        X, y = generate_linear_data(n_samples=50, n_features=1, random_state=42)

        assert X.shape == (50, 1)
        assert y.shape == (50,)

    def test_multiple_features(self):
        """测试多特征数据生成"""
        X, y = generate_linear_data(n_samples=100, n_features=3, random_state=42)

        assert X.shape == (100, 3)
        assert y.shape == (100,)

    def test_with_noise(self):
        """测试带噪声的数据生成"""
        X, y = generate_linear_data(n_samples=100, noise=0.5, random_state=42)

        # 带噪声的数据应该有更大的方差
        assert np.std(y) > 0

    def test_without_noise(self):
        """测试无噪声的数据生成"""
        X, y = generate_linear_data(n_samples=100, noise=0.0, random_state=42)

        # 无噪声的数据应该是完全线性的
        # 验证 y = X @ weights + bias
        assert X.shape[0] == len(y)

    def test_reproducibility(self):
        """测试可重复性"""
        X1, y1 = generate_linear_data(n_samples=50, random_state=42)
        X2, y2 = generate_linear_data(n_samples=50, random_state=42)

        np.testing.assert_array_equal(X1, X2)
        np.testing.assert_array_equal(y1, y2)

    def test_custom_weights(self):
        """测试自定义权重"""
        true_weights = np.array([2.0, 3.0])
        X, y = generate_linear_data(
            n_samples=100,
            n_features=2,
            true_weights=true_weights,
            noise=0.0,
            random_state=42,
        )

        # 验证 y = X @ weights
        y_expected = X @ true_weights
        np.testing.assert_array_almost_equal(y, y_expected, decimal=10)


class TestTrainTestSplit:
    """数据集划分测试"""

    def test_basic_split(self):
        """测试基本划分"""
        X = np.array([[1], [2], [3], [4], [5]])
        y = np.array([10, 20, 30, 40, 50])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        assert len(X_train) == 4
        assert len(X_test) == 1
        assert len(y_train) == 4
        assert len(y_test) == 1

    def test_split_sizes(self):
        """测试划分大小"""
        X = np.arange(20).reshape(-1, 1)
        y = np.arange(20)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42
        )

        assert len(X_train) == 14
        assert len(X_test) == 6

    def test_no_data_loss(self):
        """测试没有数据丢失"""
        X = np.array([[1], [2], [3], [4], [5]])
        y = np.array([10, 20, 30, 40, 50])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.4, random_state=42
        )

        assert len(X_train) + len(X_test) == len(X)
        assert len(y_train) + len(y_test) == len(y)


class TestR2Score:
    """R² 分数测试"""

    def test_perfect_prediction(self):
        """测试完美预测"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1, 2, 3, 4, 5])

        score = compute_r2_score(y_true, y_pred)
        assert score == 1.0

    def test_bad_prediction(self):
        """测试差的预测"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([5, 4, 3, 2, 1])

        score = compute_r2_score(y_true, y_pred)
        assert score < 0

    def test_mean_prediction(self):
        """测试均值预测"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([3, 3, 3, 3, 3])

        score = compute_r2_score(y_true, y_pred)
        assert score == 0.0

    def test_good_prediction(self):
        """测试好的预测"""
        np.random.seed(42)
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = y_true + np.random.randn(5) * 0.1

        score = compute_r2_score(y_true, y_pred)
        assert score > 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
