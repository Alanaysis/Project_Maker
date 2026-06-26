"""
Compare all optimizers on test functions.

Demonstrates how different optimizers converge on Sphere, Rosenbrock,
and Rastrigin functions.
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.sgd import SGDOptimizer
from src.adapters import AdaGradOptimizer, RMSpropOptimizer, AdamOptimizer, AdamWOptimizer
from src.lr_schedulers import StepLR, CosineLRScheduler, ExponentialLR, WarmupLR
from src.gradient_clipping import clip_by_norm
from src.convergence import ConvergenceMonitor
from src.test_functions import get_test_function
from src.utils import compute_loss, compute_loss_grad


def train_with_optimizer(optimizer, params, loss_fn, grad_fn,
                         n_epochs=500, X=None, y=None,
                         scheduler=None, clip_norm=None, monitor=None):
    """Train with a given optimizer and record history.

    Parameters
    ----------
    optimizer : optimizer instance
    params : list of np.ndarray
    loss_fn : callable
    grad_fn : callable
    n_epochs : int
    X, y : np.ndarray or None
    scheduler : scheduler instance or None
    clip_norm : float or None
    monitor : ConvergenceMonitor or None

    Returns
    -------
    dict with keys: 'loss_history', 'param_history', 'lr_history'
    """
    history = {
        'loss_history': [],
        'param_history': [],
        'lr_history': [],
    }

    for epoch in range(n_epochs):
        if X is not None:
            loss = compute_loss(params, X, y, loss_fn)
            _, grads = compute_loss_grad(params, X, y, loss_fn, grad_fn)
        else:
            loss = loss_fn(params)
            grads = grad_fn(params)

        # Gradient clipping
        if clip_norm is not None:
            grads, grad_norm = clip_by_norm(grads, clip_norm)
        else:
            grad_norm = np.sqrt(sum(np.sum(g ** 2) for g in grads))

        # Learning rate scheduling
        lr = optimizer.lr
        if scheduler is not None:
            lr = scheduler.step()

        # Apply learning rate
        scaled_grads = [g * lr / optimizer.lr for g in grads]

        # Store before update
        history['loss_history'].append(loss)
        history['lr_history'].append(lr)
        history['param_history'].append([p.copy() for p in params])

        # Update
        new_params = optimizer.step(params, scaled_grads)
        params = new_params

        # Convergence check
        if monitor is not None and monitor.update(loss, grad_norm, params):
            break

    # Final loss
    if X is not None:
        history['loss_history'].append(compute_loss(params, X, y, loss_fn))
    else:
        history['loss_history'].append(loss_fn(params))

    return history


def run_optimizer_comparison():
    """Run comparison of all optimizers on test functions."""
    print("=" * 70)
    print("Optimizer Comparison on Test Functions")
    print("=" * 70)

    test_functions = ['sphere', 'rosenbrock', 'rastrigin']
    optimizers = [
        ('SGD (lr=0.01)', SGDOptimizer(lr=0.01)),
        ('SGD+Momentum (lr=0.01, mu=0.9)', SGDOptimizer(lr=0.01, momentum=0.9)),
        ('Nesterov (lr=0.01, mu=0.9)', SGDOptimizer(lr=0.01, momentum=0.9, nesterov=True)),
        ('AdaGrad (lr=0.1)', AdaGradOptimizer(lr=0.1)),
        ('RMSprop (lr=0.01, rho=0.9)', RMSpropOptimizer(lr=0.01, rho=0.9)),
        ('Adam (lr=0.01)', AdamOptimizer(lr=0.01)),
        ('AdamW (lr=0.01, wd=0.01)', AdamWOptimizer(lr=0.01, weight_decay=0.01)),
    ]

    # Initialize parameters
    n_params = 10
    params_init = [np.array([[0.5]])]  # single parameter for visualization

    for func_name in test_functions:
        print(f"\n{'=' * 50}")
        print(f"Test function: {func_name}")
        print(f"{'=' * 50}")

        loss_fn, grad_fn = get_test_function(func_name)

        # Create fresh parameters for each function
        if func_name == 'sphere':
            params = [np.ones((n_params, 1)) * 5.0]
        elif func_name == 'rosenbrock':
            params = [np.array([[-1.2]]), np.array([[1.0]])]
        elif func_name == 'rastrigin':
            params = [np.ones((n_params, 1)) * 5.0]
        else:
            params = [np.ones((n_params, 1)) * 2.0]

        results = {}

        for opt_name, optimizer in optimizers:
            optimizer.reset()
            monitor = ConvergenceMonitor(patience=200, min_delta=1e-10)
            scheduler = CosineLRScheduler(initial_lr=optimizer.lr, T_max=500)

            history = train_with_optimizer(
                optimizer, params, loss_fn, grad_fn,
                n_epochs=500, scheduler=scheduler, monitor=monitor
            )

            final_loss = history['loss_history'][-1]
            n_iters = len(history['loss_history'])
            results[opt_name] = (final_loss, n_iters)

            print(f"  {opt_name:40s} -> loss={final_loss:.6e}, iters={n_iters}")

        # Find best optimizer
        best_opt = min(results, key=lambda k: results[k][0])
        print(f"\n  Best: {best_opt} (loss={results[best_opt][0]:.6e})")

    print("\n" + "=" * 70)
    print("Comparison complete!")
    print("=" * 70)


if __name__ == '__main__':
    run_optimizer_comparison()
