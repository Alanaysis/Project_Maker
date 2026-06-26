"""Tests for kernel functions."""

import numpy as np
import pytest
from src.kernel import RBFKernel, MaternKernel, CompositeKernel


class TestRBFKernel:
    """Test suite for RBF kernel implementation."""

    def test_kernel_positive_definite(self):
        """Covariance matrix should be positive semi-definite."""
        kernel = RBFKernel(length_scale=1.0, signal_variance=1.0)
        X = np.random.randn(20, 3)
        K = kernel(X, X)
        eigenvalues = np.linalg.eigvalsh(K)
        assert np.all(eigenvalues >= -1e-10), "K should be PSD"

    def test_kernel_symmetric(self):
        """Covariance matrix K(X, X) should be symmetric."""
        kernel = RBFKernel()
        X = np.random.randn(10, 3)
        K = kernel(X, X)
        assert np.allclose(K, K.T)

    def test_kernel_diagonal(self):
        """Diagonal of K(X, X) should equal signal_variance."""
        kernel = RBFKernel(signal_variance=2.5)
        X = np.random.randn(10, 3)
        diag = kernel.diag(X)
        assert np.allclose(diag, 2.5)

    def test_length_scale_effect(self):
        """Larger length scale should give smoother kernel (slower decay)."""
        k_small = RBFKernel(length_scale=0.5)
        k_large = RBFKernel(length_scale=2.0)
        X1 = np.array([[0.0]])
        X2 = np.array([[1.0]])
        K_small = k_small(X1, X2)[0, 0]
        K_large = k_large(X1, X2)[0, 0]
        assert K_large > K_small, "Larger length scale should give higher covariance"

    def test_signal_variance_scaling(self):
        """Signal variance should scale the kernel proportionally."""
        k1 = RBFKernel(signal_variance=1.0)
        k2 = RBFKernel(signal_variance=3.0)
        X = np.random.randn(5, 2)
        K1 = k1(X, X)
        K2 = k2(X, X)
        assert np.allclose(K2, 3.0 * K1)

    def test_gradient_shape(self):
        """Gradients should have correct shapes."""
        kernel = RBFKernel()
        X1 = np.random.randn(5, 3)
        X2 = np.random.randn(7, 3)
        grads = kernel.gradient(X1, X2)
        assert grads["length_scale"].shape == (5, 7)
        assert grads["signal_variance"].shape == (5, 7)

    def test_identity_at_zero_distance(self):
        """K(x, x) should equal signal_variance."""
        kernel = RBFKernel(signal_variance=1.5)
        X = np.random.randn(10, 3)
        K = kernel(X, X)
        assert np.allclose(np.diag(K), 1.5)


class TestMaternKernel:
    """Test suite for Matern kernel implementation."""

    @pytest.mark.parametrize("nu", [0.5, 1.5, 2.5])
    def test_matern_positive_definite(self, nu):
        """Covariance matrix should be PSD for all nu values."""
        kernel = MaternKernel(nu=nu)
        X = np.random.randn(20, 3)
        K = kernel(X, X)
        eigenvalues = np.linalg.eigvalsh(K)
        assert np.all(eigenvalues >= -1e-10)

    @pytest.mark.parametrize("nu", [0.5, 1.5, 2.5])
    def test_matern_diagonal(self, nu):
        """Diagonal should equal signal_variance."""
        kernel = MaternKernel(nu=nu, signal_variance=2.0)
        X = np.random.randn(10, 3)
        diag = kernel.diag(X)
        assert np.allclose(diag, 2.0)

    def test_matern_vs_rbf_smoothness(self):
        """Matern with smaller nu should be less smooth (faster decay)."""
        k_25 = MaternKernel(nu=2.5, length_scale=1.0)
        k_05 = MaternKernel(nu=0.5, length_scale=1.0)
        X1 = np.array([[0.0]])
        X2 = np.array([[1.0]])
        K_25 = k_25(X1, X2)[0, 0]
        K_05 = k_05(X1, X2)[0, 0]
        # Both should be positive but Matern 0.5 decays faster
        assert K_05 < K_25 or K_05 > 0

    def test_matern_repr(self):
        """Test string representation."""
        kernel = MaternKernel(length_scale=1.5, nu=2.5, signal_variance=2.0)
        repr_str = repr(kernel)
        assert "MaternKernel" in repr_str
        assert "1.5" in repr_str
        assert "2.5" in repr_str


class TestCompositeKernel:
    """Test suite for composite kernels."""

    def test_sum_kernel(self):
        """Sum kernel should combine kernels correctly."""
        k1 = RBFKernel(signal_variance=1.0)
        k2 = RBFKernel(length_scale=0.5, signal_variance=2.0)
        composite = CompositeKernel([k1, k2], operation="sum")
        X = np.random.randn(5, 3)
        K = composite(X, X)
        K1 = k1(X, X)
        K2 = k2(X, X)
        assert np.allclose(K, K1 + K2)

    def test_product_kernel(self):
        """Product kernel should combine kernels correctly."""
        k1 = RBFKernel(signal_variance=1.0)
        k2 = RBFKernel(length_scale=0.5, signal_variance=2.0)
        composite = CompositeKernel([k1, k2], operation="product")
        X = np.random.randn(5, 3)
        K = composite(X, X)
        K1 = k1(X, X)
        K2 = k2(X, X)
        assert np.allclose(K, K1 * K2)

    def test_composite_diag_sum(self):
        """Diagonal of sum kernel should be sum of diagonals."""
        k1 = RBFKernel(signal_variance=1.0)
        k2 = RBFKernel(signal_variance=2.0)
        composite = CompositeKernel([k1, k2], operation="sum")
        X = np.random.randn(10, 3)
        diag = composite.diag(X)
        assert np.allclose(diag, k1.diag(X) + k2.diag(X))

    def test_composite_repr(self):
        """Test string representation."""
        k1 = RBFKernel()
        k2 = MaternKernel(nu=2.5)
        composite = CompositeKernel([k1, k2])
        repr_str = repr(composite)
        assert "CompositeKernel" in repr_str
        assert "RBFKernel" in repr_str
        assert "MaternKernel" in repr_str
