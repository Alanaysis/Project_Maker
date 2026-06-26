"""
Tests for Lagrangian multiplier module.
"""

import sys
import os
import unittest
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.lagrangian import (
    lagrangian,
    lagrangian_gradient,
    augmented_lagrangian,
    method_of_lagrange_multipliers,
)


class TestLagrangian(unittest.TestCase):
    """Tests for Lagrangian functions."""

    def test_lagrangian_value(self):
        """Test Lagrangian value computation."""
        def f(x):
            return x[0] ** 2 + x[1] ** 2

        def h(x):
            return x[0] + x[1] - 1

        x = np.array([0.5, 0.5])
        nu = np.array([1.0])

        L = lagrangian(f, [h], [], x, nu=nu)
        expected = f(x) + nu[0] * h(x)
        self.assertAlmostEqual(L, expected, places=10)

    def test_lagrangian_gradient(self):
        """Test Lagrangian gradient computation."""
        def f(x):
            return x[0] ** 2 + x[1] ** 2

        def h(x):
            return x[0] + x[1] - 1

        x = np.array([0.5, 0.5])
        nu = np.array([1.0])

        grad_L = lagrangian_gradient(f, [h], [], x, nu=nu)

        # grad_L = [2x0 + nu, 2x1 + nu] = [2, 2]
        expected = np.array([2.0, 2.0])
        np.testing.assert_allclose(grad_L, expected, atol=1e-4)

    def test_augmented_lagrangian(self):
        """Test augmented Lagrangian value."""
        def f(x):
            return x[0] ** 2 + x[1] ** 2

        def h(x):
            return x[0] + x[1] - 1

        x = np.array([0.5, 0.5])
        nu = np.array([1.0])
        rho = 10.0

        L_A = augmented_lagrangian(f, [h], [], x, nu=nu, rho=rho)

        # L_A = f(x) + nu*h(x) + (rho/2)*h(x)^2
        h_val = h(x)
        expected = f(x) + nu[0] * h_val + (rho / 2) * h_val ** 2
        self.assertAlmostEqual(L_A, expected, places=10)


class TestMethodOfLagrangeMultipliers(unittest.TestCase):
    """Tests for the method of Lagrange multipliers."""

    def test_equality_constrained_min(self):
        """Test equality-constrained minimization."""
        # min x1^2 + x2^2
        # s.t. x1 + x2 = 1
        # Solution: x1 = x2 = 0.5

        def f(x):
            return x[0] ** 2 + x[1] ** 2

        def h(x):
            return x[0] + x[1] - 1

        result = method_of_lagrange_multipliers(
            f, [h], np.array([0.0, 0.0]),
            max_iter=100,
            tol=1e-4,
            rho=1.0,
            verbose=False,
        )

        # Should be close to (0.5, 0.5)
        self.assertIsNotNone(result.x_opt)
        np.testing.assert_allclose(
            result.x_opt, [0.5, 0.5], atol=0.1
        )

    def test_lagrangian_result_structure(self):
        """Test that LagrangianResult has expected attributes."""
        def f(x):
            return x[0] ** 2

        def h(x):
            return x[0] - 1

        result = method_of_lagrange_multipliers(
            f, [h], np.array([0.0]),
            max_iter=10,
            tol=1e-2,
            verbose=False,
        )

        self.assertIsNotNone(result.x_opt)
        self.assertIsNotNone(result.nu_opt)
        self.assertIsNotNone(result.f_opt)
        self.assertIsNotNone(result.n_iter)


if __name__ == "__main__":
    unittest.main()
