"""工具函数测试"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import generate_linear_data, generate_nonlinear_data, train_test_split


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
        assert np.std(y) > 0

    def test_without_noise(self):
        """测试无噪声的数据生成"""
        X, y = generate_linear_data(n_samples=100, noise=0.0, random_state=42)
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
            n_samples=100, n_features=2, true_weights=true_weights,
            noise=0.0, random_state=42,
        )
        y_expected = X @ true_weights
        np.testing.assert_array_almost_equal(y, y_expected, decimal=10)


class TestGenerateNonlinearData:
    """非线性数据生成测试"""

    def test_basic_generation(self):
        """测试基本生成"""
        X, y = generate_nonlinear_data(n_samples=100, random_state=42)
        assert X.shape == (100, 1)
        assert y.shape == (100,)

    def test_nonlinear_relationship(self):
        """测试非线性关系"""
        X, y = generate_nonlinear_data(n_samples=200, noise=0.0, random_state=42)
        # 线性模型拟合非线性数据应该效果不好
        from src.model import LinearRegression
        model = LinearRegression(learning_rate=0.01, n_iterations=1000)
        model.fit(X, y)
        r2 = model.score(X, y)
        # R2 应该不太高（非线性关系）
        assert r2 < 0.95


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
