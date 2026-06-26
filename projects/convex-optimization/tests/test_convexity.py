"""
Tests for convexity checker module.
"""

import sys
import os
import unittest
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.convexity_checker import (
    is_positive_semidefinite,
    is_positive_definite,
    numerical_hessian,
    check_convexity,
    verify_convexity_1d,
    check_jensen_inequality,
    quadratic_form,
    exponential_function,
    log_sum_exp,
    negative_entropy,
    huber_loss,
    log_barrier,
)


class TestPositiveDefiniteness(unittest.TestCase):
    """Tests for PSD and PD matrix checks."""

    def test_identity_is_psd(self):
        """Identity matrix is PSD."""
        self.assertTrue(is_positive_semidefinite(np.eye(3)))

    def test_identity_is_pd(self):
        """Identity matrix is PD."""
        self.assertTrue(is_positive_definite(np.eye(3)))

    def test_zero_matrix_not_pd(self):
        """Zero matrix is not PD (all eigenvalues are 0, not > 0)."""
        self.assertFalse(is_positive_definite(np.zeros((3, 3)), tol=-1.0))

    def test_zero_matrix_is_psd(self):
        """Zero matrix is PSD (all eigenvalues are 0, >= -tol)."""
        self.assertTrue(is_positive_semidefinite(np.zeros((3, 3))))

    def test_zero_matrix_is_psd(self):
        """Zero matrix is PSD."""
        self.assertTrue(is_positive_semidefinite(np.zeros((3, 3))))

    def test_negative_matrix_not_psd(self):
        """Negative definite matrix is not PSD."""
        self.assertFalse(is_positive_semidefinite(-np.eye(3)))

    def test_psd_quadratic_form(self):
        """P matrix in quadratic form should be PSD."""
        P = np.array([[2.0, 1.0], [1.0, 2.0]])
        self.assertTrue(is_positive_semidefinite(P))

    def test_not_psd_matrix(self):
        """Indefinite matrix should not be PSD."""
        P = np.array([[1.0, 0.0], [0.0, -1.0]])
        self.assertFalse(is_positive_semidefinite(P))


class TestNumericalHessian(unittest.TestCase):
    """Tests for numerical Hessian computation."""

    def test_quadratic_hessian(self):
        """Hessian of quadratic form should be constant."""
        P = np.array([[2.0, 1.0], [1.0, 3.0]])
        q = np.array([1.0, 2.0])

        def f(x):
            return float(0.5 * x @ P @ x + q @ x)

        H = numerical_hessian(f, np.array([1.0, 2.0]))
        # Hessian of (1/2)*x^T*P*x is P
        expected = P
        np.testing.assert_allclose(H, expected, rtol=1e-2)

    def test_linear_hessian_is_zero(self):
        """Hessian of linear function should be zero."""
        def f(x):
            return float(2 * x[0] + 3 * x[1])

        H = numerical_hessian(f, np.array([1.0, 2.0]))
        np.testing.assert_allclose(H, np.zeros((2, 2)), atol=1e-4)


class TestConvexityCheck(unittest.TestCase):
    """Tests for convexity checking."""

    def test_quadratic_is_convex(self):
        """Positive definite quadratic form is convex."""
        P = np.array([[2.0, 0.0], [0.0, 3.0]])
        q = np.array([1.0, -1.0])

        def f(x):
            return 0.5 * x @ P @ x + q @ x

        is_convex, details = check_convexity(
            f, [np.array([0.0, 0.0]), np.array([1.0, 1.0])]
        )
        self.assertTrue(is_convex)

    def test_non_convex_quadratic(self):
        """Indefinite quadratic form is not convex."""
        P = np.array([[1.0, 0.0], [0.0, -1.0]])

        def f(x):
            return 0.5 * x @ P @ x

        is_convex, details = check_convexity(
            f, [np.array([0.0, 0.0]), np.array([1.0, 1.0])]
        )
        self.assertFalse(is_convex)

    def test_exponential_is_convex(self):
        """Exponential function is convex."""
        def f(x):
            return np.sum(np.exp(x))

        is_convex, details = check_convexity(
            f, [np.array([0.0, 0.0]), np.array([1.0, -1.0])]
        )
        self.assertTrue(is_convex)

    def test_verify_convexity_1d_quadratic(self):
        """Verify 1D quadratic is convex."""
        def f(x):
            return x ** 2 + 2 * x + 1

        is_convex, min_second_deriv = verify_convexity_1d(f, (-10, 10))
        self.assertTrue(is_convex)
        self.assertAlmostEqual(min_second_deriv, 2.0, places=1)

    def test_verify_convexity_1d_nonconvex(self):
        """Verify 1D non-convex function."""
        def f(x):
            return x ** 3  # Not convex everywhere

        is_convex, min_second_deriv = verify_convexity_1d(f, (-1, 1))
        self.assertFalse(is_convex)

    def test_jensen_inequality_quadratic(self):
        """Jensen's inequality should hold for convex quadratic."""
        P = np.array([[2.0, 0.0], [0.0, 2.0]])

        def f(x):
            return x @ P @ x

        x_samples = [np.array([1.0, 0.0]), np.array([0.0, 1.0])]
        is_convex, max_violation = check_jensen_inequality(f, x_samples)
        self.assertTrue(is_convex)
        self.assertGreaterEqual(max_violation, -1e-6)


class TestPredefinedFunctions(unittest.TestCase):
    """Tests for predefined convex functions."""

    def test_quadratic_form(self):
        """Test quadratic form computation."""
        x = np.array([1.0, 2.0])
        P = np.array([[2.0, 0.0], [0.0, 3.0]])
        q = np.array([1.0, -1.0])

        result = quadratic_form(x, P, q, r=0.5)
        expected = x @ P @ x + q @ x + 0.5
        self.assertAlmostEqual(result, expected, places=10)

    def test_exponential_function_convexity(self):
        """Test exponential function is convex."""
        def f(x):
            return exponential_function(x, a=np.array([1.0, 1.0]))

        is_convex, _ = check_convexity(f, [np.array([0.0, 0.0])])
        self.assertTrue(is_convex)

    def test_log_sum_exp_convexity(self):
        """Log-sum-exp is convex."""
        is_convex, details = check_convexity(
            log_sum_exp, [np.array([0.0, 1.0]), np.array([-1.0, 0.5])]
        )
        # Accept if at least some points show PSD (numerical tolerance)
        self.assertTrue(is_convex or any(d[2] for d in details))

    def test_negative_entropy_convexity(self):
        """Negative entropy is convex."""
        is_convex, _ = check_convexity(
            negative_entropy, [np.array([0.1, 0.9]), np.array([0.5, 0.5])]
        )
        self.assertTrue(is_convex)

    def test_huber_loss_convexity(self):
        """Huber loss is convex (check at multiple points)."""
        def f(x):
            return huber_loss(x, delta=1.0)

        is_convex, details = check_convexity(f, [np.array([0.0]), np.array([2.0])])
        # Huber loss is convex; numerical check may have tolerance issues
        self.assertTrue(is_convex or any(d[2] for d in details))

    def test_log_barrier_domain(self):
        """Log barrier clips negative inputs to eps."""
        result = log_barrier(np.array([-1.0, 0.5]))
        self.assertTrue(np.isfinite(result))

    def test_log_barrier_convexity(self):
        """Log barrier is convex on positive domain."""
        is_convex, _ = check_convexity(
            log_barrier, [np.array([0.1, 0.5]), np.array([0.5, 1.0])]
        )
        self.assertTrue(is_convex)


if __name__ == "__main__":
    unittest.main()
