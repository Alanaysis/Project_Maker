"""Tests for acquisition functions."""

import numpy as np
import pytest
from src.acquisition import (
    expected_improvement,
    upper_confidence_bound,
    probability_of_improvement,
    acquisition_function,
)


class TestExpectedImprovement:
    """Test suite for Expected Improvement acquisition function."""

    def test_ei_positive(self):
        """EI should be non-negative everywhere."""
        X = np.random.randn(10, 2)
        mu = np.random.randn(10)
        sigma = np.abs(np.random.randn(10)) + 0.1
        f_best = np.min(mu)

        ei = expected_improvement(X, mu, sigma, f_best)
        assert np.all(ei >= -1e-10), "EI should be non-negative"

    def test_ei_higher_mean(self):
        """EI should be higher where mean is closer to f_best from below (for minimization)."""
        X = np.random.randn(10, 2)
        mu = np.linspace(-1, 1, 10)
        sigma = np.ones(10) * 0.1
        f_best = 0.0

        ei = expected_improvement(X, mu, sigma, f_best)
        # For minimization: EI favors mu < f_best (improvement over current best)
        # mu[0]=-1.0 is below f_best=0, so should have higher EI
        assert ei[0] > ei[9], "EI should favor points with lower mean below f_best for minimization"

    def test_ei_with_exploration(self):
        """xi > 0 should increase EI (more exploration)."""
        X = np.random.randn(10, 2)
        mu = np.random.randn(10)
        sigma = np.ones(10) * 0.5
        f_best = np.max(mu)

        ei_no_xi = expected_improvement(X, mu, sigma, f_best, xi=0.0)
        ei_with_xi = expected_improvement(X, mu, sigma, f_best, xi=0.1)

        assert np.all(ei_with_xi >= ei_no_xi), "xi > 0 should increase EI"

    def test_ei_zero_sigma(self):
        """EI should handle sigma near zero."""
        X = np.random.randn(5, 2)
        mu = np.random.randn(5)
        sigma = np.array([1e-12, 0.5, 0.3, 0.1, 0.01])
        f_best = np.min(mu)

        ei = expected_improvement(X, mu, sigma, f_best)
        assert np.all(np.isfinite(ei))

    def test_ei_shape(self):
        """EI output shape should match input shape."""
        X = np.random.randn(15, 3)
        mu = np.random.randn(15)
        sigma = np.abs(np.random.randn(15)) + 0.1
        f_best = 0.0

        ei = expected_improvement(X, mu, sigma, f_best)
        assert ei.shape == (15,)


class TestUpperConfidenceBound:
    """Test suite for Upper Confidence Bound acquisition function."""

    def test_ucb_increases_with_uncertainty(self):
        """UCB should increase with sigma (exploration)."""
        X = np.random.randn(10, 2)
        mu = np.ones(10) * 0.5
        sigma_low = np.ones(10) * 0.1
        sigma_high = np.ones(10) * 1.0

        ucb_low = upper_confidence_bound(X, mu, sigma_low, beta=2.0)
        ucb_high = upper_confidence_bound(X, mu, sigma_high, beta=2.0)

        assert np.all(ucb_high >= ucb_low), "Higher sigma should give higher UCB"

    def test_ucb_increases_with_beta(self):
        """UCB should increase with beta (more exploration)."""
        X = np.random.randn(10, 2)
        mu = np.random.randn(10)
        sigma = np.ones(10) * 0.5

        ucb_low = upper_confidence_bound(X, mu, sigma, beta=1.0)
        ucb_high = upper_confidence_bound(X, mu, sigma, beta=3.0)

        assert np.all(ucb_high >= ucb_low), "Higher beta should give higher UCB"

    def test_ucb_shape(self):
        """UCB output shape should match input shape."""
        X = np.random.randn(8, 3)
        mu = np.random.randn(8)
        sigma = np.abs(np.random.randn(8)) + 0.1

        ucb = upper_confidence_bound(X, mu, sigma)
        assert ucb.shape == (8,)

    def test_ucb_with_zero_sigma(self):
        """UCB should handle sigma near zero."""
        X = np.random.randn(5, 2)
        mu = np.random.randn(5)
        sigma = np.array([1e-12, 0.5, 0.3, 0.1, 0.01])

        ucb = upper_confidence_bound(X, mu, sigma)
        assert np.all(np.isfinite(ucb))


class TestProbabilityOfImprovement:
    """Test suite for Probability of Improvement acquisition function."""

    def test_pi_range(self):
        """PI should be in [0, 1]."""
        X = np.random.randn(10, 2)
        mu = np.random.randn(10)
        sigma = np.abs(np.random.randn(10)) + 0.1
        f_best = np.min(mu)

        pi = probability_of_improvement(X, mu, sigma, f_best)
        assert np.all(pi >= 0) and np.all(pi <= 1), "PI should be in [0, 1]"

    def test_pi_higher_mean(self):
        """PI should be higher where mean is higher."""
        X = np.random.randn(10, 2)
        mu = np.linspace(-1, 1, 10)
        sigma = np.ones(10) * 0.1
        f_best = 0.0

        pi = probability_of_improvement(X, mu, sigma, f_best)
        assert pi[-1] > pi[0], "PI should favor higher mean"

    def test_pi_with_xi(self):
        """xi > 0 should increase PI argument (shifts threshold for maximization context)."""
        X = np.random.randn(10, 2)
        mu = np.linspace(-1, 1, 10)
        sigma = np.ones(10) * 0.5
        f_best = 0.0

        pi_no_xi = probability_of_improvement(X, mu, sigma, f_best, xi=0.0)
        pi_with_xi = probability_of_improvement(X, mu, sigma, f_best, xi=0.1)

        # xi adds to the argument of Phi: (mu - f_best + xi) / sigma
        # So PI with xi > 0 should be higher for mu > f_best points
        assert np.any(pi_with_xi > pi_no_xi), "xi > 0 should increase PI for mu > f_best"

    def test_pi_shape(self):
        """PI output shape should match input shape."""
        X = np.random.randn(7, 3)
        mu = np.random.randn(7)
        sigma = np.abs(np.random.randn(7)) + 0.1
        f_best = 0.0

        pi = probability_of_improvement(X, mu, sigma, f_best)
        assert pi.shape == (7,)


class TestAcquisitionFunctionDispatch:
    """Test acquisition function dispatch."""

    def test_dispatch_ei(self):
        """Dispatch should call EI correctly."""
        X = np.random.randn(5, 2)
        mu = np.random.randn(5)
        sigma = np.abs(np.random.randn(5)) + 0.1

        result = acquisition_function(X, mu, sigma, name="ei", f_best=0.0)
        assert result.shape == (5,)

    def test_dispatch_ucb(self):
        """Dispatch should call UCB correctly."""
        X = np.random.randn(5, 2)
        mu = np.random.randn(5)
        sigma = np.abs(np.random.randn(5)) + 0.1

        result = acquisition_function(X, mu, sigma, name="ucb", beta=2.0)
        assert result.shape == (5,)

    def test_dispatch_pi(self):
        """Dispatch should call PI correctly."""
        X = np.random.randn(5, 2)
        mu = np.random.randn(5)
        sigma = np.abs(np.random.randn(5)) + 0.1

        result = acquisition_function(X, mu, sigma, name="pi", f_best=0.0)
        assert result.shape == (5,)

    def test_dispatch_invalid(self):
        """Dispatch should raise error for invalid name."""
        X = np.random.randn(5, 2)
        mu = np.random.randn(5)
        sigma = np.abs(np.random.randn(5)) + 0.1

        with pytest.raises(ValueError, match="Unknown acquisition"):
            acquisition_function(X, mu, sigma, name="invalid")
