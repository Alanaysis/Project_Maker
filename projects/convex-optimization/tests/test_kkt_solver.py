"""
Tests for KKT solver module.
"""

import sys
import os
import unittest
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.kkt_solver import (
    check_kkt_conditions,
    KKTResult,
)


class TestKKTConditions(unittest.TestCase):
    """Tests for KKT condition checking."""

    def test_kkt_unconstrained_minimum(self):
        """KKT conditions at unconstrained minimum."""
        def f(x):
            return x[0] ** 2 + x[1] ** 2

        def grad_f(x):
            return np.array([2 * x[0], 2 * x[1]])

        x = np.array([0.0, 0.0])
        nu = np.array([])
        lam = np.array([])

        satisfied, details = check_kkt_conditions(
            f, grad_f, [], [], x, nu, lam
        )

        self.assertTrue(satisfied)
        self.assertAlmostEqual(details['stationarity'], 0.0, places=6)

    def test_kkt_with_equality_constraint(self):
        """KKT conditions with equality constraint."""
        def f(x):
            return x[0] ** 2 + x[1] ** 2

        def grad_f(x):
            return np.array([2 * x[0], 2 * x[1]])

        def h(x):
            return x[0] + x[1] - 1

        # At optimum: x = (0.5, 0.5), nu = -1
        x = np.array([0.5, 0.5])
        nu = np.array([-1.0])
        lam = np.array([])

        satisfied, details = check_kkt_conditions(
            f, grad_f, [h], [], x, nu, lam
        )

        # Stationarity: grad_f + nu * grad_h = [1, 1] + [-1, -1] = [0, 0]
        self.assertAlmostEqual(details['stationarity'], 0.0, places=5)

    def test_kkt_result_structure(self):
        """Test KKTResult has expected attributes."""
        result = KKTResult()

        self.assertIsNone(result.x_opt)
        self.assertIsNone(result.lambda_opt)
        self.assertIsNone(result.nu_opt)
        self.assertIsNone(result.f_opt)
        self.assertFalse(result.converged)
        self.assertEqual(result.n_iter, 0)


class TestKKTResult(unittest.TestCase):
    """Tests for KKTResult container."""

    def test_kkt_result_default_values(self):
        """Test default values of KKTResult."""
        result = KKTResult()
        self.assertIsNone(result.x_opt)
        self.assertIsNone(result.f_opt)
        self.assertFalse(result.converged)
        self.assertEqual(result.n_iter, 0)


if __name__ == "__main__":
    unittest.main()
