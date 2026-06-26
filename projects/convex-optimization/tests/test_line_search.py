"""
Tests for line search module.
"""

import sys
import os
import unittest
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.line_search import (
    backtracking_line_search,
    wolfe_line_search,
    adamijo_strong_wolfe_line_search,
    LineSearchResult,
)


class TestBacktrackingLineSearch(unittest.TestCase):
    """Tests for backtracking line search."""

    def test_backtracking_quadratic(self):
        """Backtracking should find valid step for quadratic."""
        def f(x):
            return x[0] ** 2 + x[1] ** 2

        def grad_f(x):
            return np.array([2 * x[0], 2 * x[1]])

        x = np.array([1.0, 1.0])
        d = np.array([-1.0, -1.0])  # Descent direction

        alpha = backtracking_line_search(f, x, d, grad_f)

        self.assertGreater(alpha, 0)
        self.assertLessEqual(alpha, 1.0)

        # Verify Armijo condition
        f_new = f(x + alpha * d)
        f_old = f(x)
        slope = np.dot(grad_f(x), d)
        self.assertLessEqual(f_new, f_old + 1e-4 * alpha * slope)

    def test_backtracking_no_descent(self):
        """Backtracking should return init alpha for non-descent direction."""
        def f(x):
            return x[0] ** 2

        def grad_f(x):
            return np.array([2 * x[0]])

        x = np.array([1.0])
        d = np.array([1.0])  # Ascent direction

        alpha = backtracking_line_search(f, x, d, grad_f)
        self.assertEqual(alpha, 1.0)

    def test_backtracking_history(self):
        """Backtracking should reduce alpha until Armijo satisfied."""
        def f(x):
            return x[0] ** 2 + 100 * x[1] ** 2

        def grad_f(x):
            return np.array([2 * x[0], 200 * x[1]])

        x = np.array([1.0, 1.0])
        d = np.array([-1.0, -1.0])

        alpha = backtracking_line_search(f, x, d, grad_f)
        self.assertGreater(alpha, 0)


class TestWolfeLineSearch(unittest.TestCase):
    """Tests for Wolfe line search."""

    def test_wolfe_quadratic(self):
        """Wolfe line search should find valid step."""
        def f(x):
            return x[0] ** 2 + x[1] ** 2

        def grad_f(x):
            return np.array([2 * x[0], 2 * x[1]])

        x = np.array([1.0, 2.0])
        d = np.array([-1.0, -1.0])

        result = wolfe_line_search(f, x, d, grad_f)

        self.assertTrue(result.success)
        self.assertGreater(result.alpha, 0)


class TestLineSearchResult(unittest.TestCase):
    """Tests for LineSearchResult container."""

    def test_default_values(self):
        """Test default values of LineSearchResult."""
        result = LineSearchResult()
        self.assertIsNone(result.alpha)
        self.assertIsNone(result.f_new)
        self.assertEqual(result.evaluations, 0)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "")


if __name__ == "__main__":
    unittest.main()
