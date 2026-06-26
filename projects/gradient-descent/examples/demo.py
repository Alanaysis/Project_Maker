"""
Interactive demo of gradient descent optimization.

Shows the optimization process step by step on a 2D function.
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.sgd import SGDOptimizer
from src.adapters import AdamOptimizer
from src.test_functions import sphere, sphere_grad


def demo_optimization_process():
    """Demonstrate the optimization loop."""
    print("=" * 60)
    print("Gradient Descent Optimization Process Demo")
    print("=" * 60)
    print()
    print("Core loop: parameters -> gradient -> update -> convergence")
    print()

    # Initialize
    params = [np.array([[3.0], [2.0]])]
    print(f"Initial position: x={params[0].flatten()}")
    print(f"Initial loss: {sphere(params):.6f}")
    print()

    # SGD
    print("-" * 40)
    print("SGD (lr=0.1)")
    print("-" * 40)
    sgd = SGDOptimizer(lr=0.1)
    params = [np.array([[3.0], [2.0]])]

    for i in range(20):
        loss = sphere(params)
        grads = sphere_grad(params)

        if i % 5 == 0 or i == 19:
            grad_norm = np.sqrt(sum(np.sum(g ** 2) for g in grads))
            print(f"  Step {i:3d}: pos={params[0].flatten()}, loss={loss:.6f}, |g|={grad_norm:.6f}")

        params = sgd.step(params, grads)

    print(f"  Final:  pos={params[0].flatten()}, loss={sphere(params):.6f}")
    print()

    # Adam
    print("-" * 40)
    print("Adam (lr=0.1)")
    print("-" * 40)
    adam = AdamOptimizer(lr=0.1)
    params = [np.array([[3.0], [2.0]])]

    for i in range(20):
        loss = sphere(params)
        grads = sphere_grad(params)

        if i % 5 == 0 or i == 19:
            grad_norm = np.sqrt(sum(np.sum(g ** 2) for g in grads))
            print(f"  Step {i:3d}: pos={params[0].flatten()}, loss={loss:.6f}, |g|={grad_norm:.6f}")

        params = adam.step(params, grads)

    print(f"  Final:  pos={params[0].flatten()}, loss={sphere(params):.6f}")
    print()

    # Convergence detection
    print("-" * 40)
    print("Convergence Detection")
    print("-" * 40)
    params = [np.array([[3.0], [2.0]])]
    adam = AdamOptimizer(lr=0.1)

    for i in range(1000):
        loss = sphere(params)
        grads = sphere_grad(params)
        grad_norm = np.sqrt(sum(np.sum(g ** 2) for g in grads))

        if grad_norm < 1e-6:
            print(f"  Converged at step {i}!")
            print(f"  Final position: {params[0].flatten()}")
            print(f"  Final loss: {loss:.10f}")
            break

        params = adam.step(params, grads)


if __name__ == '__main__':
    demo_optimization_process()
