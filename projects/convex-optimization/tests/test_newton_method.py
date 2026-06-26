"""
Tests for Newton's method module.
"""

import sys
import os
import unittest
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.newton_method import (
    numerical_hessian,
    newton_method,
    damped_newton_method,
)


class TestNumericalHessian(unittest.TestCase):
    """Tests for numerical Hessian."""

    def test_quadratic_hessian_exact(self):
        """Hessian of quadratic should be exact."""
        P = np.array([[3.0, 1.0], [1.0, 2.0]])

        def f(x):
            return 0.5 * x @ P @ x

        H = numerical_hessian(f, np.array([1.0, 2.0]))
        np.testing.assert_allclose(H, P, rtol=1e-3)

    def test_cubic_hessian_zero(self):
        """Hessian of x^3 at x=1 should be 6x."""
        def f(x):
            return x[0] ** 3

        H = numerical_hessian(f, np.array([1.0, 0.0]))
        # d²/dx²(x³) = 6x = 6 at x=1
        self.assertAlmostEqual(H[0, 0], 6.0, places=1)


class TestNewtonMethod(unittest.TestCase):
    """Tests for Newton's method."""

    def test_minimize_quadratic(self):
        """Newton's method should find quadratic minimum in 1 step."""
        def f(x):
            return (x[0] - 5) ** 2 + (x[1] - 7) ** 2

        def grad_f(x):
            return np.array([2 * (x[0] - 5), 2 * (x[1] - 7)])

        def hess_f(x):
            return np.array([[2.0, 0.0], [0.0, 2.0]])

        result = newton_method(
            f, np.array([0.0, 0.0]),
            grad=grad_f,
            hess=hess_f,
            max_iter=10,
            tol=1e-10,
            line_search=True,
        )

        self.assertTrue(result.converged)
        self.assertAlmostEqual(result.f_opt, 0.0, places=6)
        np.testing.assert_allclose(result.x_opt, [5.0, 7.0], atol=0.01)

    def test_convergence_history(self):
        """History should record Newton decrement."""
        def f(x):
            return x[0] ** 2 + x[1] ** 2

        def grad_f(x):
            return 2 * x

        def hess_f(x):
            return np.eye(2)

        result = newton_method(
            f, np.array([1.0, 1.0]),
            grad=grad_f,
            hess=hess_f,
            max_iter=10,
            tol=1e-8,
        )

        self.assertGreater(len(result.history['newton_dec']), 0)

    def test_damped_newton_method(self):
        """Damped Newton should converge for quadratic."""
        def f(x):
            return (x[0] - 3) ** 2 + 2 * (x[1] - 4) ** 2

        def grad_f(x):
            return np.array([2 * (x[0] - 3), 4 * (x[1] - 4)])

        def hess_f(x):
            return np.array([[2.0, 0.0], [0.0, 4.0]])

        result = damped_newton_method(
            f, np.array([0.0, 0.0]),
            grad=grad_f,
            hess=hess_f,
            max_iter=20,
            tol=1e-8,
        )

        self.assertTrue(result.converged)
        np.testing.assert_allclose(result.x_opt, [3.0, 4.0], atol=0.01)


if __name__ == "__main__":
    unittest.main()
