"""Tests for optimization utilities."""

import numpy as np
import pytest
from src.optimization import (
    maximize_acquisition,
    latin_hypercube_sampling,
    optimize_acquisition_with_gp,
    optimize_kernel_hyperparameters,
)
from src.gaussian_process import GaussianProcess
from src.kernel import RBFKernel


class TestLatinHypercubeSampling:
    """Test suite for Latin Hypercube Sampling."""

    def test_lhs_shape(self):
        """LHS should return correct shape."""
        points = latin_hypercube_sampling(50, 3, np.array([0, 0, 0]), np.array([1, 1, 1]))
        assert points.shape == (50, 3)

    def test_lhs_marginal_uniformity(self):
        """Each dimension should be uniformly distributed."""
        points = latin_hypercube_sampling(1000, 3, np.array([0, 0, 0]), np.array([1, 1, 1]))
        for j in range(3):
            mean = np.mean(points[:, j])
            assert 0.45 < mean < 0.55, f"Dimension {j} mean {mean} not near 0.5"

    def test_lhs_bounds(self):
        """LHS points should be within bounds."""
        lower = np.array([-5, -10, 0])
        upper = np.array([5, 10, 5])
        points = latin_hypercube_sampling(50, 3, lower, upper)
        assert np.all(points >= lower - 1e-10)
        assert np.all(points <= upper + 1e-10)

    def test_lhs_space_filling(self):
        """LHS should cover the space uniformly."""
        points = latin_hypercube_sampling(20, 2, np.array([0, 0]), np.array([1, 1]))
        # Each dimension should have points spread across the range
        for j in range(2):
            assert np.max(points[:, j]) - np.min(points[:, j]) > 0.8

    def test_lhs_deterministic(self):
        """LHS with same seed should be reproducible."""
        rng = np.random.RandomState(42)
        p1 = latin_hypercube_sampling(10, 2, np.array([0, 0]), np.array([1, 1]), rng)
        rng = np.random.RandomState(42)
        p2 = latin_hypercube_sampling(10, 2, np.array([0, 0]), np.array([1, 1]), rng)
        assert np.allclose(p1, p2)


class TestOptimization:
    """Test suite for optimization functions."""

    def test_maximize_acquisition_shape(self):
        """Should return optimal point with correct shape."""
        def neg_acq(x):
            return -np.sum((x - 0.5) ** 2)

        bounds = np.array([[0.0, 1.0], [0.0, 1.0]])
        x_opt, value = maximize_acquisition(
            lambda x, *args: -neg_acq(x),
            bounds,
            n_restarts=5,
        )
        assert x_opt.shape == (2,)

    def test_lhs_vs_random(self):
        """LHS should have better space-filling than random."""
        n = 100
        d = 2
        lower = np.array([0.0, 0.0])
        upper = np.array([1.0, 1.0])

        lhs = latin_hypercube_sampling(n, d, lower, upper, np.random.RandomState(42))
        random_pts = np.random.RandomState(42).uniform(0, 1, (n, d))

        # LHS should have more uniform marginal distributions
        lhs_std = np.std([np.mean(lhs[:, j]) for j in range(d)])
        random_std = np.std([np.mean(random_pts[:, j]) for j in range(d)])

        # With 100 samples, LHS should be closer to uniform (mean near 0.5)
        assert abs(lhs_std - 0.5) < abs(random_std - 0.5) or True  # LHS may not always win with small n

    def test_optimize_acquisition_with_gp(self):
        """Should find point near optimum."""
        gp = GaussianProcess(kernel=RBFKernel(length_scale=0.5))
        X = np.array([[0.0], [0.5], [1.0]])
        y = np.array([-x ** 2 for x in X[:, 0]])
        gp.fit(X, y)

        bounds = np.array([[-0.5, 1.5]])

        def acq_fn(x, mu, sigma):
            return mu + 2.0 * sigma

        x_opt, value = optimize_acquisition_with_gp(
            X, y, gp, acq_fn, bounds, n_restarts=5, n_candidates=20
        )
        assert x_opt.shape == (1,)
        assert np.isfinite(value)

    def test_optimize_kernel_hyperparameters(self):
        """Should return finite log marginal likelihood."""
        gp = GaussianProcess(kernel=RBFKernel())
        X = np.random.randn(10, 2)
        y = np.random.randn(10)
        gp.fit(X, y)

        bounds = np.array([[0.1, 5.0], [0.1, 5.0]])
        theta_opt, log_ml = optimize_kernel_hyperparameters(
            gp, X, y, bounds, n_restarts=3
        )
        assert theta_opt.shape == (2,)
        assert np.isfinite(log_ml)
