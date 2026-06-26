"""
Unit tests for schedulers, gradient clipping, and convergence.
"""

import sys
import os
import unittest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.lr_schedulers import StepLR, CosineLRScheduler, ExponentialLR, WarmupLR, CompositeScheduler
from src.gradient_clipping import clip_by_norm, clip_by_value, compute_gradient_norm
from src.convergence import ConvergenceMonitor, ConvergenceDetector
from src.test_functions import make_linear_data, make_moon_data, make_spiral_data, sphere, sphere_grad
from src.utils import numerical_gradient, gradient_check


class TestSchedulers(unittest.TestCase):
    """Test learning rate schedulers."""

    def test_step_lr_decay(self):
        sched = StepLR(initial_lr=1.0, step_size=10, gamma=0.5)
        for _ in range(25):
            sched.step()
        # 25 // 10 = 2, lr = 1.0 * 0.5^2 = 0.25
        self.assertAlmostEqual(sched.get_lr(), 0.25, places=6)

    def test_cosine_lr_full_cycle(self):
        sched = CosineLRScheduler(initial_lr=1.0, T_max=10, eta_min=0.0)
        for _ in range(10):
            sched.step()
        # At T_max, cosine = cos(pi) = -1, lr = 0 + 0.5 * 1.0 * 0 = 0
        self.assertAlmostEqual(sched.get_lr(), 0.0, places=4)

    def test_cosine_lr_half_cycle(self):
        sched = CosineLRScheduler(initial_lr=1.0, T_max=10, eta_min=0.0)
        for _ in range(5):
            sched.step()
        # At T/2, cosine = cos(pi/2) = 0, lr = 0.5
        self.assertAlmostEqual(sched.get_lr(), 0.5, places=4)

    def test_exponential_lr(self):
        sched = ExponentialLR(initial_lr=1.0, gamma=0.5)
        for _ in range(3):
            sched.step()
        # lr = 1.0 * 0.5^3 = 0.125
        self.assertAlmostEqual(sched.get_lr(), 0.125, places=6)

    def test_warmup_linear(self):
        sched = WarmupLR(initial_lr=0.1, warmup_steps=10)
        for _ in range(5):
            sched.step()
        self.assertAlmostEqual(sched.get_lr(), 0.05, places=6)

    def test_warmup_complete(self):
        sched = WarmupLR(initial_lr=0.1, warmup_steps=10)
        for _ in range(15):
            sched.step()
        self.assertAlmostEqual(sched.get_lr(), 0.1, places=6)

    def test_composite_scheduler(self):
        warmup = WarmupLR(initial_lr=0.1, warmup_steps=5)
        cosine = CosineLRScheduler(initial_lr=0.1, T_max=10, eta_min=0.0)
        comp = CompositeScheduler(warmup, cosine)

        # During warmup
        for _ in range(3):
            comp.step()
        lr_during_warmup = comp.get_lr()

        # After warmup
        for _ in range(10):
            comp.step()
        lr_after_warmup = comp.get_lr()

        self.assertLess(lr_during_warmup, 0.1)
        self.assertGreater(lr_after_warmup, 0)


class TestGradientClipping(unittest.TestCase):
    """Test gradient clipping."""

    def test_clip_norm_preserves_direction(self):
        grads = [np.array([[3.0, 4.0]]), np.array([[0.0, 0.0]])]
        clipped, norm = clip_by_norm(grads, max_norm=1.0)
        original_norm = compute_gradient_norm(grads)
        self.assertAlmostEqual(original_norm, 5.0, places=3)
        # norm returns the ORIGINAL gradient norm before clipping
        self.assertAlmostEqual(norm, 5.0, places=3)

    def test_clip_value(self):
        grads = [np.array([[-5.0, 10.0, -3.0]])]
        clipped = clip_by_value(grads, clip_value=2.0)
        np.testing.assert_array_almost_equal(clipped[0], np.array([[-2.0, 2.0, -2.0]]))

    def test_compute_gradient_norm_zero(self):
        grads = [np.zeros((3, 3)), np.zeros((3, 3))]
        norm = compute_gradient_norm(grads)
        self.assertAlmostEqual(norm, 0.0, places=10)

    def test_compute_gradient_norm_single(self):
        grads = [np.array([[3.0, 4.0]])]
        norm = compute_gradient_norm(grads)
        self.assertAlmostEqual(norm, 5.0, places=3)


class TestConvergence(unittest.TestCase):
    """Test convergence detection."""

    def test_monitor_converges_on_small_gradient(self):
        monitor = ConvergenceMonitor(gradient_threshold=1e-10)
        converged = monitor.update(1.0, 1e-11)
        self.assertTrue(converged)
        self.assertTrue(monitor.converged)

    def test_monitor_patience_expires(self):
        monitor = ConvergenceMonitor(patience=5, min_delta=0.01)
        losses = [1.0, 0.99, 0.985, 0.98, 0.975, 0.97]
        for loss in losses:
            converged = monitor.update(loss, 0.1)
        self.assertTrue(monitor.converged)

    def test_monitor_does_not_converge_on_improvement(self):
        monitor = ConvergenceMonitor(patience=10, min_delta=0.01)
        losses = [1.0, 0.90, 0.80, 0.70, 0.60, 0.50, 0.40, 0.30, 0.20, 0.10, 0.01]
        for loss in losses:
            converged = monitor.update(loss, 0.1)
        self.assertFalse(monitor.converged)

    def test_detector_gradient_threshold(self):
        detector = ConvergenceDetector(gradient_threshold=1e-10)
        converged, info = detector.check(1.0, 1e-11, [np.array([[1.0]])])
        self.assertTrue(converged)

    def test_detector_param_change(self):
        detector = ConvergenceDetector(param_rel_change=1e-10)
        params = [np.array([[1.0]])]
        old_params = [np.array([[1.0]])]  # identical
        converged, info = detector.check(1.0, 0.1, params, old_params)
        self.assertTrue(converged)

    def test_loss_tracking_variance(self):
        detector = ConvergenceDetector(window_size=5, loss_rel_change=0.01)
        # Constant loss should trigger convergence
        for loss in [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]:
            detector.track_loss(loss)
        self.assertTrue(detector.track_loss(1.0))


class TestDataGeneration(unittest.TestCase):
    """Test synthetic data generation."""

    def test_linear_data_shape(self):
        X, y, w_true = make_linear_data(n_samples=100, n_features=5)
        self.assertEqual(X.shape, (100, 5))
        self.assertEqual(y.shape, (100,))
        self.assertEqual(w_true.shape, (5,))

    def test_linear_data_reproducibility(self):
        X1, y1, _ = make_linear_data(n_samples=100, n_features=5, seed=42)
        X2, y2, _ = make_linear_data(n_samples=100, n_features=5, seed=42)
        np.testing.assert_array_almost_equal(X1, X2)
        np.testing.assert_array_almost_equal(y1, y2)

    def test_moon_data_shape(self):
        X, y = make_moon_data(n_samples=200)
        self.assertEqual(X.shape, (200, 2))
        self.assertEqual(y.shape, (200,))
        self.assertEqual(len(np.unique(y)), 2)

    def test_spiral_data_shape(self):
        X, y = make_spiral_data(n_samples=200)
        self.assertEqual(X.shape, (200, 2))
        self.assertEqual(y.shape, (200,))
        self.assertEqual(len(np.unique(y)), 2)


class TestNumericalGradient(unittest.TestCase):
    """Test numerical gradient computation."""

    def test_numerical_gradient_sphere(self):
        params = [np.array([[1.0, 2.0]])]
        num_grads = numerical_gradient(params, lambda p: sphere(p))
        ana_grads = sphere_grad(params)
        for ng, ag in zip(num_grads, ana_grads):
            np.testing.assert_array_almost_equal(ng, ag, decimal=3)

    def test_gradient_check_passes(self):
        params = [np.array([[1.0, 2.0]])]
        grads = sphere_grad(params)
        passed = gradient_check(params, grads, lambda p: sphere(p))[1]
        self.assertTrue(passed)


if __name__ == '__main__':
    unittest.main()
