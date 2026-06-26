"""Tests for Gaussian Process regression."""

import numpy as np
import pytest
from src.gaussian_process import GaussianProcess
from src.kernel import RBFKernel, MaternKernel


class TestGaussianProcess:
    """Test suite for GP regression."""

    def test_gp_fit_predict(self):
        """GP should fit and predict without errors."""
        gp = GaussianProcess(kernel=RBFKernel())
        X = np.random.randn(20, 3)
        y = np.sum(X ** 2, axis=1)
        gp.fit(X, y)
        X_test = np.random.randn(5, 3)
        mu, var = gp.predict(X_test)
        assert mu.shape == (5,)
        assert var.shape == (5,)

    def test_gp_predict_variance_positive(self):
        """Predictive variance should be non-negative."""
        gp = GaussianProcess(kernel=RBFKernel())
        X = np.random.randn(20, 3)
        y = np.sum(X ** 2, axis=1)
        gp.fit(X, y)
        X_test = np.random.randn(10, 3)
        mu, var = gp.predict(X_test)
        assert np.all(var >= 0)

    def test_gp_variance_decreases_near_data(self):
        """Variance should be lower near training points."""
        gp = GaussianProcess(kernel=RBFKernel(length_scale=1.0))
        X = np.random.randn(10, 2)
        y = np.sin(X[:, 0])
        gp.fit(X, y)

        # Points close to training data
        X_near = X[:3] + np.random.randn(3, 2) * 0.01
        # Points far from training data
        X_far = np.random.randn(3, 2) * 10

        _, var_near = gp.predict(X_near)
        _, var_far = gp.predict(X_far)

        assert np.mean(var_near) < np.mean(var_far), \
            "Variance should be lower near training points"

    def test_gp_chaining(self):
        """fit() should return self for chaining."""
        gp = GaussianProcess()
        X = np.random.randn(10, 2)
        y = np.random.randn(10)
        assert gp.fit(X, y) is gp

    def test_gp_repr(self):
        """GP string representation should be informative."""
        gp = GaussianProcess(kernel=RBFKernel())
        repr_str = repr(gp)
        assert "GP" in repr_str

    def test_gp_repr_after_fit(self):
        """GP representation should include training count after fit."""
        gp = GaussianProcess()
        X = np.random.randn(15, 2)
        y = np.random.randn(15)
        gp.fit(X, y)
        repr_str = repr(gp)
        assert "n_train=15" in repr_str

    def test_gp_unfitted_raises(self):
        """Predict should raise error if GP not fitted."""
        gp = GaussianProcess()
        X_test = np.random.randn(5, 2)
        with pytest.raises(RuntimeError):
            gp.predict(X_test)

    def test_gp_log_marginal_likelihood(self):
        """Log marginal likelihood should be finite."""
        gp = GaussianProcess()
        X = np.random.randn(10, 2)
        y = np.random.randn(10)
        gp.fit(X, y)
        lml = gp.get_log_marginal_likelihood()
        assert np.isfinite(lml)
        assert lml < 0  # Log probability should be negative

    def test_gp_update(self):
        """GP should update with new data points."""
        gp = GaussianProcess()
        X1 = np.random.randn(5, 2)
        y1 = np.random.randn(5)
        gp.fit(X1, y1)

        X2 = np.random.randn(3, 2)
        y2 = np.random.randn(3)
        gp.update(X2, y2)

        assert gp.X_train.shape[0] == 8
        assert gp.y_train.shape[0] == 8

    def test_gp_sample(self):
        """GP should sample from posterior."""
        gp = GaussianProcess()
        X_train = np.random.randn(10, 2)
        y_train = np.sin(X_train[:, 0])
        gp.fit(X_train, y_train)

        X_test = np.linspace(-2, 2, 20).reshape(-1, 1)
        X_test = np.hstack([X_test, np.zeros((20, 1))])
        samples = gp.sample(X_test, n_samples=5)
        assert samples.shape == (5, 20)

    def test_gp_different_kernels(self):
        """GP should work with different kernel types."""
        X = np.random.randn(15, 2)
        y = np.sin(X[:, 0]) + 0.1 * np.random.randn(15)

        for kernel in [RBFKernel(), MaternKernel(nu=2.5)]:
            gp = GaussianProcess(kernel=kernel)
            gp.fit(X, y)
            mu, var = gp.predict(X[:3])
            assert mu.shape == (3,)
            assert np.all(var >= 0)

    def test_gp_noise_regularization(self):
        """Higher noise should increase predictive variance at new points."""
        X = np.random.randn(10, 2)
        y = np.sin(X[:, 0])

        gp_low = GaussianProcess(likelihood_noise=0.001)
        gp_low.fit(X, y)

        gp_high = GaussianProcess(likelihood_noise=0.1)
        gp_high.fit(X, y)

        # Test at points far from training data
        X_test = np.random.randn(3, 2) * 5
        _, var_low = gp_low.predict(X_test)
        _, var_high = gp_high.predict(X_test)

        assert np.mean(var_high) > np.mean(var_low), \
            f"Higher noise should increase variance: {np.mean(var_high)} vs {np.mean(var_low)}"


class TestGaussianProcessInterpolation:
    """Test GP interpolation properties."""

    def test_gp_interpolates_training_data(self):
        """GP should approximately interpolate noiseless training data."""
        gp = GaussianProcess(likelihood_noise=1e-10)
        X = np.linspace(-1, 1, 20).reshape(-1, 1)
        y = np.sin(X[:, 0])
        gp.fit(X, y)

        mu, _ = gp.predict(X)
        # At training points, prediction should be very close to observation
        assert np.max(np.abs(mu - y)) < 0.01

    def test_gp_uncertainty_grows_with_distance(self):
        """GP uncertainty should grow as we move away from training data."""
        gp = GaussianProcess(kernel=RBFKernel(length_scale=0.5))
        X = np.array([[0.0], [1.0], [2.0]])
        y = np.sin(X[:, 0])
        gp.fit(X, y)

        # Test at various distances
        distances = [0.1, 0.5, 1.0, 2.0, 5.0]
        variances = []
        for d in distances:
            X_test = np.array([[d]])
            _, var = gp.predict(X_test)
            variances.append(var[0])

        # Variance should generally increase with distance
        assert variances[-1] > variances[0], \
            "Variance should increase with distance from training data"
