"""
Tests for convergence detection module.
"""

import sys
import os
import unittest
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.convergence import (
    ConvergenceDetector,
    detect_convergence,
)


class TestConvergenceDetector(unittest.TestCase):
    """Tests for ConvergenceDetector class."""

    def test_gradient_convergence(self):
        """Detector should converge when gradient norm is small."""
        detector = ConvergenceDetector(tol=1e-6, min_iter=1)

        detector.add_point(np.array([0.0, 0.0]), 0.0, grad=np.array([1e-8, 1e-8]))
        converged = detector.check_convergence()
        self.assertTrue(converged)

    def test_step_convergence(self):
        """Detector should converge when step size is small."""
        detector = ConvergenceDetector(tol=1e-6, min_iter=1)

        detector.add_point(np.array([0.0, 0.0]), 0.0, step=np.array([1e-8, 1e-8]))
        converged = detector.check_convergence()
        self.assertTrue(converged)

    def test_function_convergence(self):
        """Detector should converge when function change is small."""
        detector = ConvergenceDetector(tol=1e-6, min_iter=2, relative_tol=False)

        detector.add_point(np.array([0.0]), 1.0)
        detector.add_point(np.array([0.0]), 1.0 + 1e-8)
        converged = detector.check_convergence()
        self.assertTrue(converged)

    def test_not_converged_early(self):
        """Detector should not converge before min_iter."""
        detector = ConvergenceDetector(tol=1e-6, min_iter=10)

        detector.add_point(np.array([0.0]), 1.0)
        converged = detector.check_convergence()
        self.assertFalse(converged)

    def test_get_summary(self):
        """Test summary generation."""
        detector = ConvergenceDetector(tol=1e-6)

        for i in range(10):
            detector.add_point(
                np.array([float(i) * 0.1]),
                1.0 / (i + 1),
                grad=np.array([-1.0 / ((i + 1) ** 2)]),
                step=np.array([0.1]),
            )

        summary = detector.get_summary()
        self.assertEqual(summary['n_iterations'], 10)
        self.assertAlmostEqual(summary['f_initial'], 1.0)
        self.assertGreater(summary['f_improvement'], 0)

    def test_convergence_rate_analysis(self):
        """Test convergence rate estimation."""
        detector = ConvergenceDetector(tol=1e-6)

        # Simulate quadratic convergence
        f_opt = 0.0
        for i in range(10):
            f_val = f_opt + 10 ** (-2 ** i)
            detector.add_point(np.array([0.0]), f_val)

        rate_info = detector.analyze_convergence_rate()
        self.assertIn(rate_info.get('rate', ''), ['superlinear', 'linear', 'slow'])


class TestDetectConvergence(unittest.TestCase):
    """Tests for static detect_convergence function."""

    def test_gradient_convergence(self):
        """Test gradient-based convergence detection."""
        f_history = [1.0, 0.5, 0.1, 0.01, 0.001]
        grad_norm_history = [1.0, 0.5, 0.1, 0.01, 1e-9]

        converged, info = detect_convergence(
            f_history, grad_norm_history=grad_norm_history
        )
        self.assertTrue(converged)

    def test_no_convergence(self):
        """Test non-convergence detection."""
        f_history = [1.0, 0.9, 0.8, 0.7, 0.6]
        grad_norm_history = [1.0, 0.9, 0.8, 0.7, 0.6]

        converged, info = detect_convergence(
            f_history, grad_norm_history=grad_norm_history,
            tol=1e-6, min_iter=2
        )
        self.assertFalse(converged)


if __name__ == "__main__":
    unittest.main()
