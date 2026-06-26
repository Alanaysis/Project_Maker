"""
Convergence comparison chart.

Compare convergence speed and final loss of different optimizers
on the same problem, with visualization.
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.sgd import SGDOptimizer
from src.adapters import AdaGradOptimizer, RMSpropOptimizer, AdamOptimizer, AdamWOptimizer
from src.lr_schedulers import CosineLRScheduler
from src.gradient_clipping import clip_by_norm
from src.convergence import ConvergenceMonitor
from src.test_functions import get_test_function
from src.utils import compute_loss, compute_loss_grad


def compare_convergence():
    """Compare convergence of all optimizers on Rosenbrock function."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available, showing numerical results only")
        print_convergence_numerically()
        return

    print("=" * 70)
    print("Convergence Comparison on Rosenbrock Function")
    print("=" * 70)

    loss_fn, grad_fn = get_test_function('rosenbrock')

    optimizers = [
        ('SGD (lr=0.001)', SGDOptimizer(lr=0.001)),
        ('SGD+Momentum', SGDOptimizer(lr=0.001, momentum=0.9)),
        ('AdaGrad', AdaGradOptimizer(lr=0.1)),
        ('RMSprop', RMSpropOptimizer(lr=0.001)),
        ('Adam', AdamOptimizer(lr=0.001)),
        ('AdamW', AdamWOptimizer(lr=0.001, weight_decay=0.001)),
    ]

    params_init = [np.array([[-1.2]]), np.array([[1.0]])]
    n_epochs = 2000

    results = {}

    for opt_name, optimizer in optimizers:
        optimizer.reset()
        params = [p.copy() for p in params_init]
        scheduler = CosineLRScheduler(initial_lr=optimizer.lr, T_max=n_epochs)
        monitor = ConvergenceMonitor(patience=500)

        loss_history = []
        param_history = []

        for epoch in range(n_epochs):
            loss = loss_fn(params)
            grads = grad_fn(params)

            lr = scheduler.step()
            scaled_grads = [g * lr / optimizer.lr for g in grads]

            params = optimizer.step(params, scaled_grads)
            loss_history.append(loss)
            param_history.append([p.copy() for p in params])

            if (epoch + 1) % 500 == 0:
                print(f"  {opt_name:20s} | Epoch {epoch+1:4d} | Loss: {loss:.6f}")

            if monitor.update(loss, np.sqrt(sum(np.sum(g ** 2) for g in grads)), params):
                print(f"  {opt_name:20s} | Converged at epoch {epoch+1}")
                break

        results[opt_name] = loss_history

    # Plot convergence curves
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    # Loss convergence
    ax = axes[0]
    for opt_name, history in results.items():
        ax.semilogy(history, label=opt_name, linewidth=1.5)
    ax.set_title('Loss Convergence (log scale)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Gradient norm convergence
    ax = axes[1]
    for opt_name, optimizer in optimizers:
        optimizer.reset()
        params = [p.copy() for p in params_init]
        scheduler = CosineLRScheduler(initial_lr=optimizer.lr, T_max=n_epochs)
        grad_norms = []

        for epoch in range(n_epochs):
            loss = loss_fn(params)
            grads = grad_fn(params)
            lr = scheduler.step()
            scaled_grads = [g * lr / optimizer.lr for g in grads]
            params = optimizer.step(params, scaled_grads)
            norm = np.sqrt(sum(np.sum(g ** 2) for g in grad_fn(params)))
            grad_norms.append(norm)

        ax.semilogy(grad_norms, label=opt_name, linewidth=1.0, alpha=0.7)

    ax.set_title('Gradient Norm Convergence (log scale)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Gradient Norm')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), 'convergence_comparison.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nConvergence chart saved to: {output_path}")

    # Summary
    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    print(f"{'Optimizer':<25s} {'Final Loss':>12s} {'Epochs':>8s}")
    print("-" * 45)
    for opt_name, history in results.items():
        print(f"{opt_name:<25s} {history[-1]:>12.6e} {len(history):>8d}")


def print_convergence_numerically():
    """Print convergence data without visualization."""
    print("=" * 70)
    print("Convergence Comparison on Rosenbrock Function (Numerical)")
    print("=" * 70)

    loss_fn, grad_fn = get_test_function('rosenbrock')

    optimizers = [
        ('SGD (lr=0.001)', SGDOptimizer(lr=0.001)),
        ('SGD+Momentum', SGDOptimizer(lr=0.001, momentum=0.9)),
        ('AdaGrad', AdaGradOptimizer(lr=0.1)),
        ('RMSprop', RMSpropOptimizer(lr=0.001)),
        ('Adam', AdamOptimizer(lr=0.001)),
        ('AdamW', AdamWOptimizer(lr=0.001, weight_decay=0.001)),
    ]

    params_init = [np.array([[-1.2]]), np.array([[1.0]])]
    n_epochs = 2000

    print(f"\n{'Epoch':>8s} | ", end='')
    for opt_name, _ in optimizers:
        print(f'{opt_name:>18s} | ', end='')
    print()
    print("-" * 70)

    for opt_name, optimizer in optimizers:
        optimizer.reset()

    for epoch in range(0, n_epochs, 100):
        print(f'{epoch:>8d} | ', end='')
        for opt_name, optimizer in optimizers:
            params = [p.copy() for p in params_init]
            scheduler = CosineLRScheduler(initial_lr=optimizer.lr, T_max=n_epochs)

            for e in range(epoch + 1):
                loss = loss_fn(params)
                grads = grad_fn(params)
                lr = scheduler.step()
                scaled_grads = [g * lr / optimizer.lr for g in grads]
                params = optimizer.step(params, scaled_grads)

            final_loss = loss_fn(params)
            print(f'{final_loss:>18.6e} | ', end='')
        print()


if __name__ == '__main__':
    compare_convergence()
