"""
Kernel functions for Gaussian Process regression.

In Bayesian Optimization, the kernel (also called covariance function)
encodes our prior assumptions about the objective function:
- Smoothness: how quickly function values change with input distance
- Periodicity: whether the function has repeating patterns
- Length scale: characteristic distance over which values correlate

The kernel K(x, x') = E[f(x)f(x')] defines the covariance between
any two input points, forming the covariance matrix used in GP inference.
"""

import numpy as np
from abc import ABC, abstractmethod


class Kernel(ABC):
    """Abstract base class for all kernel functions."""

    @abstractmethod
    def __call__(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Compute the kernel matrix between X1 and X2.

        Args:
            X1: Array of shape (n1, d)
            X2: Array of shape (n2, d)

        Returns:
            Covariance matrix of shape (n1, n2)
        """

    @abstractmethod
    def diag(self, X: np.ndarray) -> np.ndarray:
        """Compute the diagonal of the kernel matrix K(X, X).

        For stationary kernels, this is typically a constant.

        Args:
            X: Array of shape (n, d)

        Returns:
            Diagonal elements of shape (n,)
        """

    @abstractmethod
    def gradient(self, X1: np.ndarray, X2: np.ndarray) -> dict:
        """Compute gradients of the kernel with respect to hyperparameters.

        Args:
            X1: Array of shape (n1, d)
            X2: Array of shape (n2, d)

        Returns:
            Dictionary mapping hyperparameter names to gradient arrays
        """


class RBFKernel(Kernel):
    """Radial Basis Function kernel (also called Squared Exponential).

    K(x, x') = sigma_f^2 * exp(-||x - x'||^2 / (2 * l^2))

    Properties:
        - Infinitely differentiable (very smooth functions)
        - Stationary (depends only on distance)
        - Characteristic length scale l controls smoothness

    The RBF kernel is the most commonly used kernel in BO because it
    provides a strong prior over smooth functions.
    """

    def __init__(self, length_scale: float = 1.0, signal_variance: float = 1.0):
        """Initialize RBF kernel.

        Args:
            length_scale: Characteristic length scale (l > 0)
            signal_variance: Signal variance (sigma_f^2 > 0)
        """
        assert length_scale > 0, "length_scale must be positive"
        assert signal_variance > 0, "signal_variance must be positive"
        self.length_scale = length_scale
        self.signal_variance = signal_variance

    def __call__(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Compute RBF covariance matrix between X1 and X2.

        Uses the squared Euclidean distance:
            r^2 = ||x_i||^2 + ||x_j||^2 - 2 * x_i . x_j
        """
        # Compute squared Euclidean distances efficiently
        # ||x - y||^2 = ||x||^2 + ||y||^2 - 2*x.y
        sq_X1 = np.sum(X1 ** 2, axis=1).reshape(-1, 1)  # (n1, 1)
        sq_X2 = np.sum(X2 ** 2, axis=1).reshape(1, -1)  # (1, n2)
        sq_dist = sq_X1 + sq_X2 - 2.0 * X1 @ X2.T
        # Clamp to avoid negative values from numerical errors
        sq_dist = np.maximum(sq_dist, 0.0)

        return self.signal_variance * np.exp(-sq_dist / (2.0 * self.length_scale ** 2))

    def diag(self, X: np.ndarray) -> np.ndarray:
        """Diagonal of K(X, X) is always signal_variance for RBF."""
        return np.full(X.shape[0], self.signal_variance)

    def gradient(self, X1: np.ndarray, X2: np.ndarray) -> dict:
        """Compute gradients w.r.t. length_scale and signal_variance."""
        sq_X1 = np.sum(X1 ** 2, axis=1).reshape(-1, 1)
        sq_X2 = np.sum(X2 ** 2, axis=1).reshape(1, -1)
        sq_dist = np.maximum(sq_X1 + sq_X2 - 2.0 * X1 @ X2.T, 0.0)

        K = self.signal_variance * np.exp(-sq_dist / (2.0 * self.length_scale ** 2))

        grad_length_scale = K * sq_dist / (self.length_scale ** 3)
        grad_signal_var = K / self.signal_variance

        return {
            "length_scale": grad_length_scale,
            "signal_variance": grad_signal_var,
        }

    def __repr__(self):
        return f"RBFKernel(length_scale={self.length_scale:.4f}, signal_variance={self.signal_variance:.4f})"


class MaternKernel(Kernel):
    """Matern kernel family.

    General Matern kernel:
        K(r) = sigma_f^2 * 2^(1-nu) / Gamma(nu) * (sqrt(2*nu)*r/l)^nu * K_nu(sqrt(2*nu)*r/l)

    where r = ||x - x'||, nu controls smoothness, K_nu is modified Bessel function.

    Special cases:
        nu = 1/2: K(r) = sigma_f^2 * exp(-r/l)  (very rough, not differentiable)
        nu = 3/2: K(r) = sigma_f^2 * (1+sqrt(3)*r/l) * exp(-sqrt(3)*r/l)  (once diff.)
        nu = 5/2: K(r) = sigma_f^2 * (1+sqrt(5)*r/l + 5*r^2/(3*l^2)) * exp(-sqrt(5)*r/l)  (twice diff.)
        nu -> inf: Reduces to RBF kernel

    The Matern kernel is more flexible than RBF because nu controls the
    smoothness of the function prior, which is important when the true
    function is not infinitely smooth.
    """

    def __init__(self, length_scale: float = 1.0, signal_variance: float = 1.0, nu: float = 2.5):
        """Initialize Matern kernel.

        Args:
            length_scale: Characteristic length scale (l > 0)
            signal_variance: Signal variance (sigma_f^2 > 0)
            nu: Smoothness parameter (0.5, 1.5, 2.5 recommended for closed form)
        """
        assert length_scale > 0, "length_scale must be positive"
        assert signal_variance > 0, "signal_variance must be positive"
        assert nu > 0, "nu must be positive"
        self.length_scale = length_scale
        self.signal_variance = signal_variance
        self.nu = nu

    def __call__(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Compute Matern covariance matrix between X1 and X2."""
        sq_X1 = np.sum(X1 ** 2, axis=1).reshape(-1, 1)
        sq_X2 = np.sum(X2 ** 2, axis=1).reshape(1, -1)
        sq_dist = np.maximum(sq_X1 + sq_X2 - 2.0 * X1 @ X2.T, 0.0)
        dist = np.sqrt(sq_dist)

        # Effective distance scaled by nu
        scaled_dist = dist * np.sqrt(2.0 * self.nu) / self.length_scale

        if self.nu == 0.5:
            # K(r) = sigma_f^2 * exp(-r)
            K = self.signal_variance * np.exp(-scaled_dist)
        elif self.nu == 1.5:
            # K(r) = sigma_f^2 * (1 + sqrt(3)*r) * exp(-sqrt(3)*r)
            K = self.signal_variance * (1.0 + scaled_dist) * np.exp(-scaled_dist)
        elif self.nu == 2.5:
            # K(r) = sigma_f^2 * (1 + sqrt(5)*r + 5*r^2/3) * exp(-sqrt(5)*r)
            K = self.signal_variance * (1.0 + scaled_dist + scaled_dist ** 2 / 3.0) * np.exp(-scaled_dist)
        else:
            # General case using Bessel function approximation
            from scipy.special import kv
            K = self.signal_variance * (2 ** (1 - self.nu)) / np.math.gamma(self.nu) * \
                (scaled_dist ** self.nu) * kv(self.nu, scaled_dist)
            # Handle zero distance (kv diverges at 0 for nu > 0)
            zero_mask = scaled_dist < 1e-10
            if np.any(zero_mask):
                if self.nu > 0:
                    K[zero_mask] = self.signal_variance

        return K

    def diag(self, X: np.ndarray) -> np.ndarray:
        """Diagonal of K(X, X) is always signal_variance for Matern."""
        return np.full(X.shape[0], self.signal_variance)

    def gradient(self, X1: np.ndarray, X2: np.ndarray) -> dict:
        """Compute gradients w.r.t. length_scale and signal_variance."""
        sq_X1 = np.sum(X1 ** 2, axis=1).reshape(-1, 1)
        sq_X2 = np.sum(X2 ** 2, axis=1).reshape(1, -1)
        sq_dist = np.maximum(sq_X1 + sq_X2 - 2.0 * X1 @ X2.T, 0.0)
        dist = np.sqrt(sq_dist)

        scaled_dist = dist * np.sqrt(2.0 * self.nu) / self.length_scale

        if self.nu == 0.5:
            K = self.signal_variance * np.exp(-scaled_dist)
            grad_ls = K * (scaled_dist / self.length_scale)
        elif self.nu == 1.5:
            K = self.signal_variance * (1.0 + scaled_dist) * np.exp(-scaled_dist)
            grad_ls = K * (scaled_dist / self.length_scale)
        elif self.nu == 2.5:
            K = self.signal_variance * (1.0 + scaled_dist + scaled_dist ** 2 / 3.0) * np.exp(-scaled_dist)
            grad_ls = K * (scaled_dist / self.length_scale)
        else:
            K = self.signal_variance * self.__call__(X1, X2)
            grad_ls = K * (scaled_dist / self.length_scale)

        grad_sv = K / self.signal_variance

        return {
            "length_scale": grad_ls,
            "signal_variance": grad_sv,
        }

    def __repr__(self):
        return f"MaternKernel(length_scale={self.length_scale:.4f}, nu={self.nu}, signal_variance={self.signal_variance:.4f})"


class CompositeKernel(Kernel):
    """Composite kernel combining multiple kernels (sum or product).

    Sum kernel: K = K1 + K2  (captures multiple length scales)
    Product kernel: K = K1 * K2  (captures interactions between features)

    Composite kernels allow modeling more complex function structures.
    For example, a sum of RBF kernels with different length scales can
    model both global trends and local variations.
    """

    def __init__(self, kernels: list, operation: str = "sum"):
        """Initialize composite kernel.

        Args:
            kernels: List of kernel objects
            operation: 'sum' or 'product'
        """
        assert len(kernels) >= 2, "Need at least 2 kernels"
        assert operation in ("sum", "product"), "operation must be 'sum' or 'product'"
        self.kernels = kernels
        self.operation = operation

    def __call__(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Compute composite kernel matrix."""
        result = None
        for k in self.kernels:
            ki = k(X1, X2)
            if result is None:
                result = ki
            elif self.operation == "sum":
                result += ki
            else:  # product
                result *= ki
        return result

    def diag(self, X: np.ndarray) -> np.ndarray:
        """Compute diagonal of composite kernel."""
        if self.operation == "sum":
            return sum(k.diag(X) for k in self.kernels)
        else:
            result = None
            for k in self.kernels:
                if result is None:
                    result = k.diag(X)
                else:
                    result *= k.diag(X)
            return result

    def gradient(self, X1: np.ndarray, X2: np.ndarray) -> dict:
        """Compute gradients for all kernels."""
        gradients = {}
        for i, k in enumerate(self.kernels):
            grad = k.gradient(X1, X2)
            for name, val in grad.items():
                key = f"k{i}_{name}"
                if self.operation == "sum":
                    gradients[key] = val
                else:
                    # Product rule: d(K1*K2)/dtheta = K1*dK2/dtheta + K2*dK1/dtheta
                    other_K = 1.0
                    for j, kj in enumerate(self.kernels):
                        if j != i:
                            other_K *= kj(X1, X2)
                    gradients[key] = val * other_K
        return gradients

    def __repr__(self):
        op = "+" if self.operation == "sum" else "*"
        kernels_str = op.join(f"({k})" for k in self.kernels)
        return f"CompositeKernel({kernels_str}, op='{self.operation}')"
