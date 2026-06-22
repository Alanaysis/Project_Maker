"""特征值分解模块测试"""

import numpy as np
import pytest

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.eigen import (
    power_iteration,
    eigen_decomposition_power,
    qr_algorithm,
    eigen_decomposition,
    deflate,
)


class TestPowerIteration:
    """测试幂迭代法。"""

    def test_simple_matrix(self):
        """测试简单矩阵的最大特征值。"""
        # 对角矩阵，最大特征值为 5
        A = np.diag([1.0, 5.0, 3.0])
        eigenvalue, eigenvector = power_iteration(A)

        np.testing.assert_almost_equal(eigenvalue, 5.0, decimal=6)

    def test_known_symmetric_matrix(self):
        """测试已知对称矩阵。"""
        A = np.array([[2, 1], [1, 2]], dtype=np.float64)
        eigenvalue, eigenvector = power_iteration(A)

        # 特征值应为 3 或 1
        assert abs(eigenvalue - 3.0) < 1e-6 or abs(eigenvalue - 1.0) < 1e-6

    def test_eigenvector_normalized(self):
        """测试返回的特征向量是单位向量。"""
        np.random.seed(42)
        A = np.random.randn(3, 3)
        A = A + A.T  # 对称化

        _, eigenvector = power_iteration(A)

        np.testing.assert_almost_equal(np.linalg.norm(eigenvector), 1.0)

    def test_eigenvalue_equation(self):
        """测试特征值方程 A*v = lambda*v。"""
        A = np.array([[4, 2], [2, 3]], dtype=np.float64)
        eigenvalue, eigenvector = power_iteration(A)

        # A*v 应该等于 lambda*v（同方向）
        Av = A @ eigenvector
        lambda_v = eigenvalue * eigenvector

        np.testing.assert_array_almost_equal(Av, lambda_v)


class TestDeflation:
    """测试矩阵压缩。"""

    def test_removes_eigenvalue(self):
        """测试压缩后移除了最大特征值。"""
        A = np.diag([5.0, 3.0, 1.0])
        A_deflated = deflate(A, 5.0, np.array([1, 0, 0], dtype=np.float64))

        # 压缩后第一个特征值应为0
        np.testing.assert_almost_equal(A_deflated[0, 0], 0.0)


class TestQRAlgorithm:
    """测试 QR 算法。"""

    def test_diagonal_matrix(self):
        """测试对角矩阵的特征值分解。"""
        A = np.diag([5.0, 3.0, 1.0])
        eigenvalues, eigenvectors = qr_algorithm(A)

        # 特征值应为 [5, 3, 1]
        np.testing.assert_array_almost_equal(sorted(eigenvalues, reverse=True), [5.0, 3.0, 1.0])

    def test_known_symmetric(self):
        """测试已知对称矩阵。"""
        A = np.array([[2, 1], [1, 2]], dtype=np.float64)
        eigenvalues, eigenvectors = qr_algorithm(A)

        # 特征值应为 3 和 1
        np.testing.assert_array_almost_equal(sorted(eigenvalues, reverse=True), [3.0, 1.0])

    def test_matches_numpy(self):
        """测试与 numpy 特征值分解结果一致。"""
        np.random.seed(42)
        A = np.random.randn(4, 4)
        A = A + A.T  # 对称化

        eigenvalues_ours, eigenvectors_ours = qr_algorithm(A)
        eigenvalues_np, eigenvectors_np = np.linalg.eigh(A)

        # 按降序排列 numpy 结果
        idx = np.argsort(eigenvalues_np)[::-1]
        eigenvalues_np = eigenvalues_np[idx]

        np.testing.assert_array_almost_equal(
            sorted(eigenvalues_ours, reverse=True),
            eigenvalues_np,
            decimal=6,
        )

    def test_eigenvectors_orthogonal(self):
        """测试特征向量正交性。"""
        np.random.seed(123)
        A = np.random.randn(3, 3)
        A = A + A.T

        _, eigenvectors = qr_algorithm(A)

        # V^T * V 应接近单位矩阵
        orthogonality = eigenvectors.T @ eigenvectors
        np.testing.assert_array_almost_equal(orthogonality, np.eye(3), decimal=6)


class TestEigenDecomposition:
    """测试特征值分解接口。"""

    def test_qr_method(self):
        """测试 QR 方法。"""
        A = np.diag([4.0, 2.0, 1.0])
        eigenvalues, eigenvectors = eigen_decomposition(A, method="qr")

        np.testing.assert_array_almost_equal(eigenvalues, [4.0, 2.0, 1.0])

    def test_power_method(self):
        """测试幂迭代方法。"""
        A = np.diag([4.0, 2.0, 1.0])
        eigenvalues, eigenvectors = eigen_decomposition(A, n_components=2, method="power")

        assert len(eigenvalues) == 2
        np.testing.assert_array_almost_equal(eigenvalues, [4.0, 2.0])

    def test_n_components(self):
        """测试保留指定数量的特征值。"""
        A = np.diag([4.0, 3.0, 2.0, 1.0])
        eigenvalues, eigenvectors = eigen_decomposition(A, n_components=2)

        assert len(eigenvalues) == 2
        assert eigenvectors.shape == (4, 2)

    def test_invalid_input(self):
        """测试非方阵输入。"""
        A = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float64)
        with pytest.raises(ValueError, match="方阵"):
            eigen_decomposition(A)

    def test_invalid_method(self):
        """测试未知方法。"""
        A = np.eye(3)
        with pytest.raises(ValueError, match="未知"):
            eigen_decomposition(A, method="invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
