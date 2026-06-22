"""协方差矩阵计算模块测试"""

import numpy as np
import pytest

# 添加项目路径
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.covariance import compute_covariance_matrix, compute_covariance_matrix_manual, center_data


class TestCenterData:
    """测试数据中心化函数。"""

    def test_basic_centering(self):
        """测试基本的中心化功能。"""
        X = np.array([[1, 2], [3, 4], [5, 6]], dtype=np.float64)
        X_centered, mean = center_data(X)

        # 验证均值
        np.testing.assert_array_almost_equal(mean, [3.0, 4.0])

        # 验证中心化后的均值为0
        np.testing.assert_array_almost_equal(np.mean(X_centered, axis=0), [0.0, 0.0])

    def test_single_feature(self):
        """测试单特征数据的中心化。"""
        X = np.array([[1], [2], [3], [4]], dtype=np.float64)
        X_centered, mean = center_data(X)

        assert mean[0] == 2.5
        np.testing.assert_array_almost_equal(X_centered.flatten(), [-1.5, -0.5, 0.5, 1.5])

    def test_already_centered(self):
        """测试已中心化的数据。"""
        X = np.array([[-1, 0], [0, 0], [1, 0]], dtype=np.float64)
        X_centered, mean = center_data(X)

        np.testing.assert_array_almost_equal(mean, [0.0, 0.0])
        np.testing.assert_array_almost_equal(X_centered, X)


class TestCovarianceMatrix:
    """测试协方差矩阵计算。"""

    def test_known_covariance(self):
        """测试已知结果的协方差矩阵。"""
        # 简单数据：特征完全相关
        X = np.array([[1, 2], [2, 4], [3, 6], [4, 8]], dtype=np.float64)
        X_centered, _ = center_data(X)
        cov = compute_covariance_matrix(X_centered)

        # 形状检查
        assert cov.shape == (2, 2)

        # 对称性检查
        np.testing.assert_array_almost_equal(cov, cov.T)

        # 对角线应为正数（方差）
        assert cov[0, 0] > 0
        assert cov[1, 1] > 0

    def test_identity_covariance(self):
        """测试标准正态数据的协方差矩阵应接近单位矩阵。"""
        np.random.seed(42)
        X = np.random.randn(10000, 3)
        X_centered, _ = center_data(X)
        cov = compute_covariance_matrix(X_centered)

        # 大样本下应接近单位矩阵
        np.testing.assert_array_almost_equal(cov, np.eye(3), decimal=1)

    def test_matches_numpy(self):
        """测试与 numpy 内置函数的结果一致性。"""
        np.random.seed(123)
        X = np.random.randn(50, 4)
        X_centered, _ = center_data(X)

        cov_ours = compute_covariance_matrix(X_centered)
        cov_numpy = np.cov(X_centered, rowvar=False)

        np.testing.assert_array_almost_equal(cov_ours, cov_numpy)

    def test_invalid_input_1d(self):
        """测试1D输入应抛出异常。"""
        X = np.array([1, 2, 3], dtype=np.float64)
        with pytest.raises(ValueError, match="2D"):
            compute_covariance_matrix(X)

    def test_invalid_input_single_sample(self):
        """测试单样本应抛出异常。"""
        X = np.array([[1, 2, 3]], dtype=np.float64)
        with pytest.raises(ValueError, match="样本数"):
            compute_covariance_matrix(X)


class TestCovarianceMatrixManual:
    """测试手动计算的协方差矩阵。"""

    def test_matches_vectorized(self):
        """测试手动计算与向量化计算结果一致。"""
        np.random.seed(42)
        X = np.random.randn(20, 3)
        X_centered, _ = center_data(X)

        cov_vectorized = compute_covariance_matrix(X_centered)
        cov_manual = compute_covariance_matrix_manual(X_centered)

        np.testing.assert_array_almost_equal(cov_vectorized, cov_manual)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
