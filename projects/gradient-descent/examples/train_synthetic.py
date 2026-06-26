"""
Train on a synthetic dataset.

Demonstrates training linear regression and classification models
using different optimizers on synthetic data.
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.sgd import SGDOptimizer, MiniBatchSGD
from src.adapters import AdaGradOptimizer, RMSpropOptimizer, AdamOptimizer, AdamWOptimizer
from src.lr_schedulers import StepLR, CosineLRScheduler, WarmupLR
from src.convergence import ConvergenceMonitor
from src.test_functions import make_linear_data, make_moon_data
from src.utils import compute_loss, compute_loss_grad


def mean_squared_error(params, X, y):
    """Mean squared error loss for linear regression.

    params[0] = weights (n_features, 1)
    params[1] = bias (1, 1)
    """
    w, b = params[0], params[1]
    y_pred = X @ w + b
    return float(np.mean((y_pred.flatten() - y) ** 2))


def mse_grad(params, X, y):
    """Gradient of MSE loss."""
    w, b = params[0], params[1]
    y_pred = X @ w + b
    n = X.shape[0]
    dw = (2.0 / n) * X.T @ (y_pred - y.reshape(-1, 1))
    db = (2.0 / n) * np.sum(y_pred - y.reshape(-1, 1))
    return [dw, db]


def sigmoid(z):
    """Sigmoid activation function."""
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))


def binary_cross_entropy(params, X, y):
    """Binary cross-entropy loss for classification.

    params[0] = weights, params[1] = bias
    """
    w, b = params[0], params[1]
    z = X @ w + b
    p = sigmoid(z)
    p = np.clip(p, 1e-15, 1 - 1e-15)
    loss = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    return float(loss)


def bce_grad(params, X, y):
    """Gradient of binary cross-entropy loss."""
    w, b = params[0], params[1]
    z = X @ w + b
    p = sigmoid(z)
    n = X.shape[0]
    dw = (1.0 / n) * X.T @ (p - y.reshape(-1, 1))
    db = (1.0 / n) * np.sum(p - y.reshape(-1, 1))
    return [dw, db]


def train_linear_regression():
    """Train linear regression with different optimizers."""
    print("=" * 60)
    print("Linear Regression on Synthetic Data")
    print("=" * 60)

    X, y, w_true = make_linear_data(n_samples=1000, n_features=5, noise=0.5)
    print(f"True weights: {w_true.flatten()}")

    # Add bias term
    X_bias = np.column_stack([X, np.ones(X.shape[0])])
    n_features = X_bias.shape[1]

    optimizers = [
        ('SGD (lr=0.001)', SGDOptimizer(lr=0.001)),
        ('SGD+Momentum', SGDOptimizer(lr=0.001, momentum=0.9)),
        ('AdaGrad', AdaGradOptimizer(lr=0.01)),
        ('RMSprop', RMSpropOptimizer(lr=0.001)),
        ('Adam', AdamOptimizer(lr=0.001)),
        ('AdamW', AdamWOptimizer(lr=0.001, weight_decay=0.001)),
    ]

    for opt_name, optimizer in optimizers:
        params = [np.zeros((n_features, 1)), np.zeros((1, 1))]
        optimizer.reset()
        monitor = ConvergenceMonitor(patience=100)
        scheduler = CosineLRScheduler(initial_lr=optimizer.lr, T_max=1000)

        loss_history = []
        for epoch in range(1000):
            loss = compute_loss(params, X_bias, y, binary_cross_entropy if hasattr(y, '__len__') and y.max() > 1 else mean_squared_error,
                                mse_grad)
            _, grads = compute_loss_grad(params, X_bias, y, lambda p, X, y: mean_squared_error(p, X, y), mse_grad)

            lr = scheduler.step()
            scaled_grads = [g * lr / optimizer.lr for g in grads]

            params = optimizer.step(params, scaled_grads)
            loss_history.append(loss)

            if monitor.update(loss, np.sqrt(sum(np.sum(g ** 2) for g in grads)), params):
                break

        final_loss = loss_history[-1]
        print(f"  {opt_name:20s} -> final MSE={final_loss:.6f}, epochs={len(loss_history)}")

    return X_bias, y


def train_classification():
    """Train logistic regression on two-moons data."""
    print("\n" + "=" * 60)
    print("Classification on Two-Moons Data")
    print("=" * 60)

    X, y = make_moon_data(n_samples=500, noise=0.15)

    # Add polynomial features for better decision boundary
    X_poly = np.column_stack([
        X,
        X[:, 0] ** 2,
        X[:, 1] ** 2,
        X[:, 0] * X[:, 1],
        np.ones(X.shape[0])
    ])

    optimizers = [
        ('SGD', SGDOptimizer(lr=0.01)),
        ('Adam', AdamOptimizer(lr=0.01)),
        ('AdamW', AdamWOptimizer(lr=0.01, weight_decay=0.001)),
    ]

    for opt_name, optimizer in optimizers:
        n_features = X_poly.shape[1]
        params = [np.zeros((n_features, 1)), np.zeros((1, 1))]
        optimizer.reset()
        scheduler = CosineLRScheduler(initial_lr=optimizer.lr, T_max=2000)

        loss_history = []
        for epoch in range(2000):
            loss = binary_cross_entropy(params, X_poly, y)
            grads = bce_grad(params, X_poly, y)

            lr = scheduler.step()
            scaled_grads = [g * lr / optimizer.lr for g in grads]

            params = optimizer.step(params, scaled_grads)
            loss_history.append(loss)

        # Compute final accuracy
        w, b = params[0].flatten(), params[1].flatten()
        z = X_poly @ w + b
        preds = (sigmoid(z) >= 0.5).astype(float)
        accuracy = np.mean(preds == y)

        print(f"  {opt_name:20s} -> final BCE={loss_history[-1]:.6f}, accuracy={accuracy:.4f}")


def train_with_mini_batch():
    """Demonstrate mini-batch SGD training."""
    print("\n" + "=" * 60)
    print("Mini-Batch SGD Training")
    print("=" * 60)

    X, y, w_true = make_linear_data(n_samples=2000, n_features=5, noise=0.3)
    X_bias = np.column_stack([X, np.ones(X.shape[0])])

    batch_size = 64
    base_optimizer = SGDOptimizer(lr=0.001, momentum=0.9)
    mini_batch_sgd = MiniBatchSGD(base_optimizer, batch_size=batch_size)

    params = [np.zeros((X_bias.shape[1], 1)), np.zeros((1, 1))]
    scheduler = StepLR(initial_lr=0.001, step_size=300, gamma=0.5)

    loss_history = []
    for epoch in range(500):
        batches = mini_batch_sgd.create_batches(X_bias, y)
        epoch_losses = []

        for X_batch, y_batch in batches:
            loss, params = mini_batch_sgd.train_step(
                X_batch, y_batch, params, mean_squared_error, mse_grad
            )
            epoch_losses.append(loss)

        avg_loss = np.mean(epoch_losses)
        loss_history.append(avg_loss)

        if (epoch + 1) % 100 == 0:
            lr = scheduler.step()
            print(f"  Epoch {epoch + 1:4d} | Loss: {avg_loss:.6f} | LR: {lr:.6f}")

    print(f"  Final MSE: {loss_history[-1]:.6f}")
    print(f"  True weights: {w_true.flatten()}")
    print(f"  Learned weights: {params[0].flatten()}")


if __name__ == '__main__':
    train_linear_regression()
    train_classification()
    train_with_mini_batch()
