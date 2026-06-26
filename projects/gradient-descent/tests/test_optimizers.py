"""
Unit tests for the SGD optimizer.
"""

import sys
import os
import unittest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.sgd import SGDOptimizer, MiniBatchSGD
from src.adapters import AdaGradOptimizer, RMSpropOptimizer, AdamOptimizer, AdamWOptimizer
from src.lr_schedulers import StepLR, CosineLRScheduler, ExponentialLR, WarmupLR, CompositeScheduler
from src.gradient_clipping import clip_by_norm, clip_by_value, compute_gradient_norm
from src.convergence import ConvergenceMonitor, ConvergenceDetector
from src.test_functions import (
    sphere, sphere_grad, rosenbrock, rosenbrock_grad,
    rastrigin, rastrigin_grad, ackley, ackley_grad,
    get_test_function
)
from src.utils import numerical_gradient, gradient_check


class TestSGDOptimizer(unittest.TestCase):
    """Test basic SGD optimizer."""

    def test_sgd_initializes(self):
        opt = SGDOptimizer(lr=0.01)
        self.assertEqual(opt.lr, 0.01)
        self.assertEqual(opt.momentum, 0.0)
        self.assertIsNone(opt.velocity)

    def test_sgd_step_shape_preserved(self):
        opt = SGDOptimizer(lr=0.01)
        params = [np.array([[1.0, 2.0], [3.0, 4.0]]), np.array([0.5])]
        grads = [np.ones_like(p) * 0.1 for p in params]
        new_params = opt.step(params, grads)
        for p, new_p in zip(params, new_params):
            self.assertEqual(p.shape, new_p.shape)

    def test_sgd_reduces_quadratic(self):
        """SGD should reduce f(x) = x^2."""
        opt = SGDOptimizer(lr=0.1)
        params = [np.array([[5.0]])]
        for _ in range(100):
            loss = sphere(params)
            grads = sphere_grad(params)
            params = opt.step(params, grads)
        self.assertLess(sphere(params), 0.01)

    def test_momentum_sgd(self):
        opt = SGDOptimizer(lr=0.01, momentum=0.9)
        params = [np.array([[5.0]])]
        for _ in range(200):
            loss = sphere(params)
            grads = sphere_grad(params)
            params = opt.step(params, grads)
        # Momentum should converge faster than vanilla SGD
        self.assertLess(sphere(params), 0.1)

    def test_nesterov_sgd(self):
        opt = SGDOptimizer(lr=0.01, momentum=0.9, nesterov=True)
        params = [np.array([[5.0]])]
        for _ in range(200):
            loss = sphere(params)
            grads = sphere_grad(params)
            params = opt.step(params, grads)
        self.assertLess(sphere(params), 0.1)

    def test_sgd_reset(self):
        opt = SGDOptimizer(lr=0.01, momentum=0.9)
        params = [np.array([[1.0]])]
        grads = [np.array([[0.5]])]
        opt.step(params, grads)
        self.assertIsNotNone(opt.velocity)
        opt.reset()
        self.assertIsNone(opt.velocity)

    def test_sgd_state_serialization(self):
        opt = SGDOptimizer(lr=0.01, momentum=0.5)
        state = opt.get_state()
        self.assertEqual(state['lr'], 0.01)
        self.assertEqual(state['momentum'], 0.5)


class TestMiniBatchSGD(unittest.TestCase):
    """Test mini-batch SGD."""

    def test_create_batches(self):
        opt = MiniBatchSGD(SGDOptimizer(lr=0.01), batch_size=100)
        X = np.random.randn(500, 10)
        y = np.random.randn(500)
        batches = opt.create_batches(X, y)
        self.assertEqual(len(batches), 5)
        X_batch, y_batch = batches[0]
        self.assertEqual(X_batch.shape[0], 100)

    def test_create_batches_last_batch(self):
        opt = MiniBatchSGD(SGDOptimizer(lr=0.01), batch_size=100)
        X = np.random.randn(550, 10)
        y = np.random.randn(550)
        batches = opt.create_batches(X, y)
        self.assertEqual(len(batches), 6)
        X_last, y_last = batches[-1]
        self.assertEqual(X_last.shape[0], 50)

    def test_train_step_returns_loss(self):
        opt = MiniBatchSGD(SGDOptimizer(lr=0.01), batch_size=32)
        X = np.random.randn(64, 5)
        y = np.random.randn(64)
        params = [np.zeros((5, 1))]
        loss_fn = lambda p, X, y: float(np.mean((X @ p[0] - y.reshape(-1, 1)) ** 2))
        grad_fn = lambda p, X, y: [(2.0 / X.shape[0]) * X.T @ (X @ p[0] - y.reshape(-1, 1))]
        loss, new_params = opt.train_step(X, y, params, loss_fn, grad_fn)
        self.assertIsInstance(loss, float)
        self.assertEqual(len(new_params), 1)


class TestAdaGrad(unittest.TestCase):
    """Test AdaGrad optimizer."""

    def test_adagrad_reduces_quadratic(self):
        opt = AdaGradOptimizer(lr=0.5)
        params = [np.array([[5.0]])]
        for _ in range(200):
            loss = sphere(params)
            grads = sphere_grad(params)
            params = opt.step(params, grads)
        self.assertLess(sphere(params), 0.5)

    def test_adagrad_state(self):
        opt = AdaGradOptimizer(lr=0.01)
        state = opt.get_state()
        self.assertEqual(state['lr'], 0.01)
        self.assertEqual(state['eps'], 1e-8)
        self.assertIsNone(state['G'])


class TestRMSprop(unittest.TestCase):
    """Test RMSprop optimizer."""

    def test_rmsprop_reduces_quadratic(self):
        opt = RMSpropOptimizer(lr=0.1, rho=0.9)
        params = [np.array([[5.0]])]
        for _ in range(100):
            loss = sphere(params)
            grads = sphere_grad(params)
            params = opt.step(params, grads)
        self.assertLess(sphere(params), 0.5)

    def test_rmsprop_state(self):
        opt = RMSpropOptimizer(lr=0.01, rho=0.9)
        state = opt.get_state()
        self.assertEqual(state['rho'], 0.9)


class TestAdam(unittest.TestCase):
    """Test Adam optimizer."""

    def test_adam_reduces_quadratic(self):
        opt = AdamOptimizer(lr=0.1)
        params = [np.array([[5.0]])]
        for _ in range(100):
            loss = sphere(params)
            grads = sphere_grad(params)
            params = opt.step(params, grads)
        self.assertLess(sphere(params), 0.01)

    def test_adam_rosenbrock(self):
        """Adam should make progress on Rosenbrock."""
        opt = AdamOptimizer(lr=0.01)
        params = [np.array([[-1.2]]), np.array([[1.0]])]
        for _ in range(500):
            loss = rosenbrock(params)
            grads = rosenbrock_grad(params)
            params = opt.step(params, grads)
        self.assertLess(rosenbrock(params), 1.0)

    def test_adam_state(self):
        opt = AdamOptimizer(lr=0.001, beta1=0.9, beta2=0.999)
        state = opt.get_state()
        self.assertEqual(state['beta1'], 0.9)
        self.assertEqual(state['beta2'], 0.999)
        self.assertEqual(state['t'], 0)


class TestAdamW(unittest.TestCase):
    """Test AdamW optimizer."""

    def test_adamw_reduces_quadratic(self):
        opt = AdamWOptimizer(lr=0.1, weight_decay=0.01)
        params = [np.array([[5.0]])]
        for _ in range(100):
            loss = sphere(params)
            grads = sphere_grad(params)
            params = opt.step(params, grads)
        self.assertLess(sphere(params), 0.1)

    def test_adamw_state(self):
        opt = AdamWOptimizer(lr=0.001, weight_decay=0.01)
        state = opt.get_state()
        self.assertEqual(state['weight_decay'], 0.01)


class TestSchedulers(unittest.TestCase):
    """Test learning rate schedulers."""

    def test_step_lr(self):
        sched = StepLR(initial_lr=0.1, step_size=100, gamma=0.1)
        for _ in range(250):
            lr = sched.step()
        self.assertAlmostEqual(lr, 0.001, places=6)

    def test_cosine_lr(self):
        sched = CosineLRScheduler(initial_lr=0.1, T_max=100, eta_min=0.0)
        for _ in range(100):
            lr = sched.step()
        self.assertAlmostEqual(lr, 0.0, places=4)

    def test_exponential_lr(self):
        sched = ExponentialLR(initial_lr=1.0, gamma=0.5)
        lr = sched.step()
        self.assertAlmostEqual(lr, 0.5, places=6)

    def test_warmup_lr(self):
        sched = WarmupLR(initial_lr=0.1, warmup_steps=10)
        # After 5 warmup steps, lr should be 0.05
        for _ in range(5):
            sched.step()
        self.assertAlmostEqual(sched.get_lr(), 0.05, places=6)
        # After warmup, lr should be 0.1
        for _ in range(10):
            sched.step()
        self.assertAlmostEqual(sched.get_lr(), 0.1, places=6)


class TestGradientClipping(unittest.TestCase):
    """Test gradient clipping functions."""

    def test_clip_by_norm_no_clip(self):
        grads = [np.array([[1.0, 2.0]]), np.array([[3.0, 4.0]])]
        clipped, norm = clip_by_norm(grads, max_norm=100.0)
        self.assertAlmostEqual(norm, 5.477, places=2)
        for g, cg in zip(grads, clipped):
            np.testing.assert_array_almost_equal(g, cg)

    def test_clip_by_norm_clips(self):
        grads = [np.array([[10.0, 20.0]]), np.array([[30.0, 40.0]])]
        clipped, norm = clip_by_norm(grads, max_norm=1.0)
        self.assertAlmostEqual(norm, 54.77, places=1)
        total_norm = np.sqrt(sum(np.sum(c ** 2) for c in clipped))
        self.assertAlmostEqual(total_norm, 1.0, places=4)

    def test_clip_by_value(self):
        grads = [np.array([[-2.0, 3.0, -5.0]])]
        clipped = clip_by_value(grads, clip_value=1.0)
        np.testing.assert_array_almost_equal(clipped[0], np.array([[-1.0, 1.0, -1.0]]))

    def test_compute_gradient_norm(self):
        grads = [np.array([[3.0, 4.0]]), np.array([[0.0, 0.0]])]
        norm = compute_gradient_norm(grads)
        self.assertAlmostEqual(norm, 5.0, places=3)


class TestConvergenceMonitor(unittest.TestCase):
    """Test convergence monitoring."""

    def test_monitor_detects_gradient_convergence(self):
        monitor = ConvergenceMonitor(gradient_threshold=1e-10)
        converged = monitor.update(1.0, 1e-11)  # Should trigger early stop
        self.assertTrue(converged)
        self.assertTrue(monitor.converged)

    def test_monitor_patience(self):
        monitor = ConvergenceMonitor(patience=3, min_delta=0.1)
        for loss in [1.0, 0.95, 0.94, 0.93, 0.92]:
            should_stop = monitor.update(loss, 0.1)
        self.assertTrue(monitor.converged)

    def test_monitor_get_info(self):
        monitor = ConvergenceMonitor()
        monitor.update(1.0, 0.1)
        monitor.update(0.5, 0.05)
        info = monitor.get_convergence_info()
        self.assertEqual(info['total_epochs'], 2)
        self.assertEqual(info['best_loss'], 0.5)

    def test_monitor_reset(self):
        monitor = ConvergenceMonitor()
        monitor.update(1.0, 0.1)
        monitor.reset()
        self.assertEqual(len(monitor.loss_history), 0)
        self.assertFalse(monitor.converged)


class TestTestFunctions(unittest.TestCase):
    """Test test functions."""

    def test_sphere_minimum(self):
        params = [np.zeros((5, 1))]
        self.assertAlmostEqual(sphere(params), 0.0, places=6)

    def test_rosenbrock_minimum(self):
        params = [np.array([[1.0]]), np.array([[1.0]])]
        self.assertAlmostEqual(rosenbrock(params), 0.0, places=6)

    def test_rastrigin_minimum(self):
        params = [np.zeros((5, 1))]
        self.assertAlmostEqual(rastrigin(params), 0.0, places=6)

    def test_ackley_minimum(self):
        params = [np.zeros((5, 1))]
        self.assertAlmostEqual(ackley(params), 0.0, places=6)

    def test_get_test_function(self):
        fn, grad_fn = get_test_function('sphere')
        self.assertEqual(fn([np.array([[1.0]])]), 1.0)

    def test_gradient_shapes_match(self):
        params = [np.array([[1.0, 2.0]]), np.array([[3.0]])]
        grads = sphere_grad(params)
        for g, p in zip(grads, params):
            self.assertEqual(g.shape, p.shape)

    def test_gradient_check_sphere(self):
        params = [np.array([[1.0, 2.0]])]
        grads = sphere_grad(params)
        loss_fn = lambda p: sphere(p)
        error, passed = gradient_check(params, grads, loss_fn)
        self.assertTrue(passed, f"Gradient check failed with error {error}")


if __name__ == '__main__':
    unittest.main()
