"""
Example 4: Hyperparameter tuning for a simple ML model.

This example demonstrates BO applied to a practical problem: tuning
hyperparameters of a simple neural network (from scratch) on a small
classification task.

We optimize:
- Learning rate (log scale)
- Network width (hidden layer size)
- Regularization strength

The objective function trains a simple network and returns validation error.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from typing import Tuple

from src.bo_loop import BayesianOptimization


def generate_data(n_samples: int = 200, n_features: int = 4, seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """Generate synthetic classification data (spirals).

    Args:
        n_samples: Number of samples
        n_features: Number of features
        seed: Random seed

    Returns:
        Tuple of (X, y) where X is (n_samples, n_features) and y is (n_samples,)
    """
    rng = np.random.RandomState(seed)
    n_per_class = n_samples // 3

    # Generate three-class spiral data
    X = np.zeros((n_samples, n_features))
    y = np.zeros(n_samples, dtype=int)

    for cls in range(3):
        start = cls * n_per_class
        end = start + n_per_class
        t = np.linspace(0, 2 * np.pi, n_per_class)
        r = t + cls * np.pi / 3

        for j in range(n_features):
            X[start:end, j] = r * np.cos(t + j * 0.5) + rng.randn(n_per_class) * 0.3
            if j > 0:
                X[start:end, j] += 0.1 * rng.randn(n_per_class)

        y[start:end] = cls

    return X, y


def train_simple_network(X_train, y_train, X_val, y_val, lr: float, width: int, reg: float) -> float:
    """Train a simple 2-layer neural network and return validation error.

    This is a minimal implementation for demonstration purposes.
    The network has:
    - One hidden layer with 'width' neurons
    - ReLU activation
    - Softmax output for 3 classes
    - L2 regularization with strength 'reg'

    Args:
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        lr: Learning rate
        width: Hidden layer width
        reg: L2 regularization strength

    Returns:
        Validation error (misclassification rate)
    """
    n_features = X_train.shape[1]
    n_classes = 3
    n_train = X_train.shape[0]

    # Initialize weights
    rng = np.random.RandomState(42)
    W1 = rng.randn(n_features, width) * np.sqrt(2.0 / n_features)
    b1 = np.zeros(width)
    W2 = rng.randn(width, n_classes) * np.sqrt(2.0 / width)
    b2 = np.zeros(n_classes)

    # Training loop
    n_epochs = 50
    for epoch in range(n_epochs):
        # Forward pass
        z1 = X_train @ W1 + b1
        a1 = np.maximum(0, z1)  # ReLU
        z2 = a1 @ W2 + b2

        # Softmax
        exp_z2 = np.exp(z2 - np.max(z2, axis=1, keepdims=True))
        probs = exp_z2 / np.sum(exp_z2, axis=1, keepdims=True)

        # Backward pass
        dz2 = probs.copy()
        dz2[np.arange(n_train), y_train] -= 1
        dz2 /= n_train

        dW2 = a1.T @ dz2 + reg * W2
        db2 = np.sum(dz2, axis=0)
        da1 = dz2 @ W2.T
        dz1 = da1 * (z1 > 0).astype(float)
        dW1 = X_train.T @ dz1 + reg * W1
        db1 = np.sum(dz1, axis=0)

        # Gradient clipping
        grad_norm = np.sqrt(np.sum(dW1 ** 2) + np.sum(dW2 ** 2))
        if grad_norm > 5.0:
            dW1 *= 5.0 / grad_norm
            dW2 *= 5.0 / grad_norm

        # Update
        W1 -= lr * dW1
        b1 -= lr * db1
        W2 -= lr * dW2
        b2 -= lr * db2

    # Validation
    z1 = X_val @ W1 + b1
    a1 = np.maximum(0, z1)
    z2 = a1 @ W2 + b2
    y_pred = np.argmax(z2, axis=1)

    return float(np.mean(y_pred != y_val))


def objective_fn(params: np.ndarray) -> float:
    """BO objective: validation error of a simple network.

    Parameters:
        params[0]: log10(learning rate)
        params[1]: log10(hidden width)
        params[2]: log10(regularization)

    Returns:
        Validation error
    """
    lr = 10 ** params[0]
    width = max(2, int(10 ** params[1]))
    reg = 10 ** params[2]

    # Generate data
    X, y = generate_data(n_samples=150, n_features=4)
    X_train, X_val = X[:100], X[100:]
    y_train, y_val = y[:100], y[100:]

    # Train and evaluate
    error = train_simple_network(X_train, y_train, X_val, y_val, lr, width, reg)

    return error


def main():
    """Run BO for hyperparameter tuning."""
    bounds = np.array([
        [-3.0, -1.0],   # log10(lr) in [0.001, 0.1]
        [0.0, 2.0],     # log10(width) in [1, 100]
        [-5.0, -1.0],   # log10(reg) in [0.00001, 0.1]
    ])

    print("=== Hyperparameter Tuning with BO ===")
    print("Optimizing: learning rate, network width, regularization")
    print(f"Bounds: {bounds.T}")
    print()

    bo = BayesianOptimization(
        bounds=bounds,
        acquisition="ei",
        xi=0.01,
        n_initial=8,
        n_opt_restarts=15,
        random_state=42,
    )

    result = bo.run(objective_fn, n_iter=15, verbose=True)

    lr_best = 10 ** result["best_x"][0]
    width_best = int(10 ** result["best_x"][1])
    reg_best = 10 ** result["best_x"][2]

    print(f"\nBest hyperparameters:")
    print(f"  Learning rate: {lr_best:.6f}")
    print(f"  Network width: {width_best}")
    print(f"  Regularization: {reg_best:.6f}")
    print(f"  Validation error: {result['best_y']:.4f}")

    # Plot convergence
    _plot_hparam_convergence(result)


def _plot_hparam_convergence(result):
    """Plot hyperparameter tuning convergence."""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(result["best_y_history"], "b-o", linewidth=2, markersize=8)
    ax.set_xlabel("BO Iteration", fontsize=12)
    ax.set_ylabel("Validation Error", fontsize=12)
    ax.set_title("Hyperparameter Tuning Convergence", fontsize=14)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("examples/output_hparam_tuning.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\nSaved: examples/output_hparam_tuning.png")


if __name__ == "__main__":
    main()
