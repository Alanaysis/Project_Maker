"""
Tests for gradient descent module.
"""

import sys
import os
import unittest
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gradient_descent import (
    numerical_gradient,
    gradient_descent,
    momentum_gradient_descent,
    adagrad_gradient_descent,
)


class TestNumericalGradient(unittest.TestCase):
    """Tests for numerical gradient computation."""

    def test_linear_gradient(self):
        """Gradient of linear function should be constant."""
        def f(x):
            return 2 * x[0] + 3 * x[1]

        grad = numerical_gradient(f, np.array([1.0, 2.0]))
        np.testing.assert_allclose(grad, np.array([2.0, 3.0]), atol=1e-5)

    def test_quadratic_gradient(self):
        """Gradient of x^2 should be 2x."""
        def f(x):
            return x[0] ** 2

        grad = numerical_gradient(f, np.array([3.0, 0.0]))
        np.testing.assert_allclose(grad, np.array([6.0, 0.0]), atol=1e-4)

    def test_gradient_zero_at_origin(self):
        """Gradient of x^2 + y^2 at origin should be zero."""
        def f(x):
            return x[0] ** 2 + x[1] ** 2

        grad = numerical_gradient(f, np.array([0.0, 0.0]))
        np.testing.assert_allclose(grad, np.array([0.0, 0.0]), atol=1e-6)


class TestGradientDescent(unittest.TestCase):
    """Tests for gradient descent optimizer."""

    def test_minimize_quadratic(self):
        """Gradient descent should find minimum of quadratic."""
        def f(x):
            return (x[0] - 3) ** 2 + (x[1] - 4) ** 2

        result = gradient_descent(
            f, np.array([0.0, 0.0]),
            max_iter=5000,
            tol=1e-10,
            step_size=0.1,
            line_search=True,
        )

        self.assertTrue(result.converged)
        self.assertAlmostEqual(result.f_opt, 0.0, places=5)
        np.testing.assert_allclose(result.x_opt, [3.0, 4.0], atol=0.01)

    def test_minimize_rosenbrock(self):
        """Gradient descent should approach Rosenbrock minimum."""
        def f(x):
            return (1 - x[0]) ** 2 + 100 * (x[1] - x[0] ** 2) ** 2

        result = gradient_descent(
            f, np.array([-1.0, 1.0]),
            max_iter=10000,
            tol=1e-6,
            step_size=0.001,
            line_search=True,
        )

        # Should get closer to minimum
        self.assertLess(result.f_opt, f(np.array([-1.0, 1.0])))

    def test_convergence_history(self):
        """History should record function values."""
        def f(x):
            return x[0] ** 2 + x[1] ** 2

        result = gradient_descent(
            f, np.array([5.0, 5.0]),
            max_iter=100,
            tol=1e-8,
            step_size=0.1,
            line_search=True,
        )

        self.assertGreater(len(result.history['f']), 0)
        # Function values should be non-increasing (with line search)
        f_history = result.history['f']
        for i in range(1, len(f_history)):
            self.assertLessEqual(f_history[i], f_history[i-1] + 1e-10)

    def test_momentum_gradient_descent(self):
        """Momentum gradient descent should converge."""
        def f(x):
            return (x[0] - 2) ** 2 + (x[1] - 3) ** 2

        result = momentum_gradient_descent(
            f, np.array([0.0, 0.0]),
            max_iter=2000,
            tol=1e-8,
            step_size=0.1,
            momentum=0.9,
            line_search=True,
        )

        self.assertTrue(result.converged)
        np.testing.assert_allclose(result.x_opt, [2.0, 3.0], atol=0.05)

    def test_adagrad_gradient_descent(self):
        """AdaGrad should converge for simple quadratic."""
        def f(x):
            return x[0] ** 2 + 100 * x[1] ** 2  # Ill-conditioned

        result = adagrad_gradient_descent(
            f, np.array([1.0, 1.0]),
            max_iter=3000,
            tol=1e-6,
            step_size=0.1,
            line_search=True,
        )

        self.assertLess(result.f_opt, 0.01)


if __name__ == "__main__":
    unittest.main()
