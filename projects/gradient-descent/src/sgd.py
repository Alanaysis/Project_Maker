"""
Vanilla Stochastic Gradient Descent (SGD) and Mini-batch SGD.

SGD updates parameters by moving in the opposite direction of the gradient:
    theta = theta - lr * gradient

Mini-batch SGD uses a subset of data for each update to reduce variance
while maintaining computational efficiency.
"""

import numpy as np


class SGDOptimizer:
    """Stochastic Gradient Descent optimizer.

    The simplest optimization algorithm:
        theta_{t+1} = theta_t - lr * f'(theta_t)

    Parameters
    ----------
    lr : float
        Learning rate (step size).
    momentum : float, optional
        Momentum coefficient (0.0 = disabled). Default 0.0.
    nesterov : bool, optional
        Use Nesterov momentum. Default False.
    """

    def __init__(self, lr: float = 0.01, momentum: float = 0.0, nesterov: bool = False):
        self.lr = lr
        self.momentum = momentum
        self.nesterov = nesterov
        self.velocity = None

    def reset(self):
        """Reset optimizer state."""
        self.velocity = None

    def step(self, params, grads):
        """Perform a single SGD update step.

        Parameters
        ----------
        params : list of np.ndarray
            Current parameters (will not be modified in-place by this optimizer).
        grads : list of np.ndarray
            Gradients with respect to each parameter.

        Returns
        -------
        list of np.ndarray
            Updated parameters.
        """
        if self.momentum > 0.0:
            if self.velocity is None:
                self.velocity = [np.zeros_like(p) for p in params]

            new_params = []
            for p, g, v in zip(params, grads, self.velocity):
                if self.nesterov:
                    # Nesterov: compute gradient at theta - mu*v
                    nesterov_grad = g + self.momentum * v
                    v_new = self.momentum * v - self.lr * nesterov_grad
                else:
                    v_new = self.momentum * v - self.lr * g
                    nesterov_grad = g

                new_params.append(p + v_new)
            self.velocity = [v_new if self.momentum > 0 else np.zeros_like(p)
                             for p, v_new in zip(params, self.velocity)]
            return new_params
        else:
            return [p - self.lr * g for p, g in zip(params, grads)]

    def get_state(self):
        """Return optimizer state dict (for serialization)."""
        return {
            "lr": self.lr,
            "momentum": self.momentum,
            "nesterov": self.nesterov,
            "velocity": self.velocity,
        }

    def set_state(self, state):
        """Restore optimizer state from dict."""
        self.lr = state["lr"]
        self.momentum = state["momentum"]
        self.nesterov = state["nesterov"]
        self.velocity = state["velocity"]


class MiniBatchSGD:
    """Mini-batch SGD with data shuffling and batching.

    Core loop:
        1. Shuffle dataset
        2. Split into mini-batches
        3. Compute batch gradient
        4. Update parameters via SGD
    """

    def __init__(self, base_optimizer: SGDOptimizer, batch_size: int = 32):
        self.base_optimizer = base_optimizer
        self.batch_size = batch_size

    def create_batches(self, X, y):
        """Split data into mini-batches.

        Parameters
        ----------
        X : np.ndarray
            Input features, shape (n_samples, n_features).
        y : np.ndarray
            Target values, shape (n_samples,).

        Returns
        -------
        list of tuple
            List of (X_batch, y_batch) mini-batches.
        """
        n_samples = X.shape[0]
        indices = np.arange(n_samples)
        np.random.shuffle(indices)

        batches = []
        for start in range(0, n_samples, self.batch_size):
            end = min(start + self.batch_size, n_samples)
            batch_idx = indices[start:end]
            batches.append((X[batch_idx], y[batch_idx]))
        return batches

    def train_step(self, X_batch, y_batch, params, loss_fn, grad_fn):
        """Perform one mini-batch training step.

        Parameters
        ----------
        X_batch : np.ndarray
            Mini-batch input features.
        y_batch : np.ndarray
            Mini-batch targets.
        params : list of np.ndarray
            Current parameters.
        loss_fn : callable
            Loss function f(params, X, y) -> scalar.
        grad_fn : callable
            Gradient function grad(params, X, y) -> list of arrays.

        Returns
        -------
        float
            Loss value on the mini-batch.
        list of np.ndarray
            Updated parameters.
        """
        loss = loss_fn(params, X_batch, y_batch)
        grads = grad_fn(params, X_batch, y_batch)
        new_params = self.base_optimizer.step(params, grads)
        return loss, new_params
