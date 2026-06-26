"""
Gaussian Process regression implementation.

A Gaussian Process (GP) is a collection of random variables, any finite
number of which have a joint Gaussian distribution. In Bayesian Optimization,
we use a GP as a prior over functions:

    f(x) ~ GP(m(x), k(x, x'))

where m(x) is the mean function (often 0) and k(x, x') is the kernel.

After observing data D = {(x_i, y_i)}, the posterior distribution over f(x*)
at a new point x* is:

    p(f* | D, x*) = N(mu*, sigma*^2)

    mu* = k_*^T (K + sigma_n^2 * I)^{-1} y     (predictive mean)
    sigma*^2 = k** - k_*^T (K + sigma_n^2 * I)^{-1} k_*   (predictive variance)

where:
    K = k(X, X) + sigma_n^2 * I  (noisy covariance matrix)
    k_* = k(x*, X)  (covariance between test and training points)
    k** = k(x*, x*)  (test point variance)

To avoid directly inverting K (O(n^3) and numerically unstable), we use
Cholesky decomposition: K = L * L^T, then solve via forward/backward substitution.
"""

import numpy as np
from scipy.linalg import cho_factor, cho_solve, cholesky
from typing import Tuple, Optional
from .kernel import Kernel, RBFKernel


class GaussianProcess:
    """Gaussian Process regression model.

    Implements GP regression with Cholesky decomposition for numerically
    stable inference. The key computational steps are:

    1. Cholesky decomposition: K + sigma_n^2 * I = L * L^T
    2. Solve L * alpha = y  (forward substitution)
    3. Solve L^T * alpha = alpha  (backward substitution)
    4. Predict: mu = k_* @ alpha, var = k** - k_* @ L^{-T} L^{-1} k_*
    """

    def __init__(
        self,
        kernel: Optional[Kernel] = None,
        noise_variance: float = 1e-6,
        likelihood_noise: float = 0.01,
    ):
        """Initialize GP regressor.

        Args:
            kernel: The covariance kernel function. Defaults to RBFKernel.
            noise_variance: Numerical regularization added to diagonal.
            likelihood_noise: Observation noise variance (sigma_n^2).
        """
        self.kernel = kernel or RBFKernel()
        self.noise_variance = noise_variance
        self.likelihood_noise = likelihood_noise

        # Training data (stored for prediction)
        self.X_train: Optional[np.ndarray] = None
        self.y_train: Optional[np.ndarray] = None

        # Cholesky factor and alpha for fast prediction
        self.L: Optional[np.ndarray] = None
        self.alpha: Optional[np.ndarray] = None

        # Log marginal likelihood tracking
        self.log_marginal_likelihood: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GaussianProcess":
        """Fit GP to training data by computing Cholesky decomposition.

        This is the key computational step. We decompose:
            K = k(X, X) + sigma_n^2 * I + eps * I = L * L^T

        where eps is small regularization for numerical stability.

        Args:
            X: Training inputs of shape (n, d)
            y: Training outputs of shape (n,)

        Returns:
            self for chaining
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64).reshape(-1)

        n = X.shape[0]
        self.X_train = X.copy()
        self.y_train = y.copy()

        # Compute covariance matrix K = k(X, X)
        K = self.kernel(X, X)

        # Add noise regularization: K + sigma_n^2 * I
        K += (self.likelihood_noise + self.noise_variance) * np.eye(n)

        # Cholesky decomposition: K = L * L^T
        # This is more numerically stable than direct inversion
        try:
            self.L = cholesky(K, lower=True)
        except np.linalg.LinAlgError:
            # Add more regularization if decomposition fails
            K += 1e-4 * np.eye(n)
            self.L = cholesky(K, lower=True)

        # Solve L * alpha = y  (via Cholesky solve)
        # Equivalent to alpha = K^{-1} y but more stable
        self.alpha = cho_solve((self.L, True), y)

        # Compute log marginal likelihood:
        # log p(y|X) = -0.5 * y^T * K^{-1} * y - sum(log(diag(L))) - n/2 * log(2*pi)
        self.log_marginal_likelihood = self._compute_log_marginal_likelihood(y)

        return self

    def predict(
        self, X_test: np.ndarray, return_variance: bool = True
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Predict GP posterior at test points.

        For test points X_test, compute:
            mu* = k_* @ alpha  (predictive mean)
            var* = k** - k_* @ L^{-T} L^{-1} k_*  (predictive variance)

        The predictive variance captures our uncertainty about the function
        at unobserved locations. This is crucial for acquisition functions
        which balance exploration (high uncertainty) and exploitation
        (high predicted value).

        Args:
            X_test: Test inputs of shape (m, d)
            return_variance: Whether to return predictive variance

        Returns:
            If return_variance: (mu, var) where mu is (m,) and var is (m,)
            If not: mu of shape (m,)
        """
        X_test = np.asarray(X_test, dtype=np.float64)

        if self.L is None or self.alpha is None:
            raise RuntimeError("GP has not been fitted. Call fit() first.")

        # k_* = k(X_test, X_train)  (m x n)
        k_star = self.kernel(X_test, self.X_train)

        # mu* = k_* @ alpha
        mu = k_star @ self.alpha

        if not return_variance:
            return mu

        # Predictive variance: var = k** - k_* @ L^{-T} L^{-1} k_*
        # First solve L^T @ v = k_*^T  =>  v = L^{-T} @ k_*^T
        v = cho_solve((self.L, False), k_star.T)  # (n, m)

        # k** = diag(K(X_test, X_test))
        k_ss = self.kernel.diag(X_test)  # (m,)

        # var = k** - k_*^T @ L^{-1} @ L^{-T} @ k_* = k** - sum(v^2)
        var = k_ss - np.sum(v * k_star.T, axis=0)

        # Clamp variance to be non-negative (numerical errors)
        var = np.maximum(var, 0.0)

        return mu, var

    def _compute_log_marginal_likelihood(self, y: np.ndarray) -> float:
        """Compute log marginal likelihood: log p(y | X, theta).

        This is used for hyperparameter optimization. The log marginal
        likelihood balances model fit (data term) and model complexity
        (complexity penalty):

            log p(y|X) = -0.5 * y^T K^{-1} y - 0.5 * log|K| - n/2 log(2pi)

        The first term rewards good fit, the second penalizes complexity.
        Maximizing this (marginal likelihood) is equivalent to type-II
        maximum likelihood estimation of kernel hyperparameters.

        Args:
            y: Training outputs

        Returns:
            Log marginal likelihood value
        """
        n = y.shape[0]

        # y^T K^{-1} y = y^T alpha
        data_fit = y @ self.alpha

        # log|K| = 2 * sum(log(diag(L)))
        log_det = 2.0 * np.sum(np.log(np.diag(self.L)))

        # Full log marginal likelihood
        log_ml = -0.5 * data_fit - 0.5 * log_det - 0.5 * n * np.log(2.0 * np.pi)

        return log_ml

    def get_log_marginal_likelihood(self) -> float:
        """Get the current log marginal likelihood."""
        if self.y_train is None:
            raise RuntimeError("GP has not been fitted.")
        return self.log_marginal_likelihood

    def sample(self, X_test: np.ndarray, n_samples: int = 1, random_state: Optional[int] = None) -> np.ndarray:
        """Sample functions from the GP posterior.

        Generates samples from the posterior Gaussian distribution
        N(mu, K_star_star) at test points. Useful for visualizing
        the uncertainty in the GP model.

        Args:
            X_test: Test inputs of shape (m, d)
            n_samples: Number of samples to draw
            random_state: Random seed

        Returns:
            Samples of shape (n_samples, m)
        """
        if self.L is None or self.alpha is None:
            raise RuntimeError("GP has not been fitted. Call fit() first.")

        rng = np.random.RandomState(random_state)
        X_test = np.asarray(X_test, dtype=np.float64)

        # Get predictive mean
        k_star = self.kernel(X_test, self.X_train)
        mu = k_star @ self.alpha

        # Get Cholesky of predictive covariance: K** - K*^T K^{-1} K*
        # First solve L^T @ V = K*  =>  V = L^{-T} K*
        V = cho_solve((self.L, False), k_star.T)  # (n, m)

        # Covariance of samples: K_s = k_ss - V^T K*  (m x m)
        k_ss = self.kernel.diag(X_test)
        K_s = np.diag(k_ss) - V.T @ k_star.T  # (m, m)

        # Clamp to ensure PSD (add regularization)
        K_s += 1e-6 * np.eye(X_test.shape[0])

        # Ensure symmetry
        K_s = 0.5 * (K_s + K_s.T)

        # Sample from N(mu, K_s)
        try:
            L_s = cholesky(K_s, lower=True)
        except np.linalg.LinAlgError:
            # If still not PSD, use diagonal
            K_s = np.diag(np.maximum(np.diag(K_s), 1e-6))
            L_s = cholesky(K_s, lower=True)
        Z = rng.randn(n_samples, X_test.shape[0])
        samples = mu[np.newaxis, :] + Z @ L_s.T

        return samples

    def update(self, X_new: np.ndarray, y_new: np.ndarray) -> "GaussianProcess":
        """Incrementally update GP with new data points.

        Instead of refitting from scratch, this adds new points to
        the existing training set and recomputes the Cholesky factor.

        For large datasets, consider using sparse GP approximations.

        Args:
            X_new: New inputs of shape (k, d)
            y_new: New outputs of shape (k,)

        Returns:
            self for chaining
        """
        if self.X_train is None:
            return self.fit(X_new, y_new)

        # Concatenate with existing data
        X_combined = np.vstack([self.X_train, X_new])
        y_combined = np.concatenate([self.y_train, y_new])

        return self.fit(X_combined, y_combined)

    def __repr__(self):
        if self.X_train is not None:
            return f"GP(kernel={self.kernel}, n_train={self.X_train.shape[0]}, noise={self.likelihood_noise:.2e})"
        return f"GP(kernel={self.kernel}, noise={self.likelihood_noise:.2e})"
