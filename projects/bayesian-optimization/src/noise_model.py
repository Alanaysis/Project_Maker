"""
Noise model for Gaussian Process regression.

In practice, observations are noisy: y = f(x) + epsilon, where
epsilon ~ N(0, sigma_n^2). The noise model accounts for this by
adding sigma_n^2 to the diagonal of the covariance matrix:

    K_noisy = K + sigma_n^2 * I

This prevents overfitting and ensures numerical stability.

We also support heteroscedastic noise (varying noise levels) and
noise hyperparameter optimization.
"""

import numpy as np
from typing import Optional


class NoiseModel:
    """Noise model for GP observations.

    Handles observation noise in the GP framework. The key insight is
    that noise only affects the diagonal of the covariance matrix:

        K(y, y) = K(f, f) + diag(sigma_n^2)

    This means noise increases the uncertainty at training points,
    preventing the GP from trying to interpolate through noisy data.
    """

    def __init__(self, noise_variance: float = 0.01):
        """Initialize noise model.

        Args:
            noise_variance: Observation noise variance sigma_n^2
        """
        self.noise_variance = noise_variance
        self._noise_levels: Optional[np.ndarray] = None

    @property
    def noise_variance(self) -> float:
        """Current noise variance."""
        if self._noise_levels is not None:
            return float(np.mean(self._noise_levels))
        return self._noise_variance

    @noise_variance.setter
    def noise_variance(self, value: float):
        if value < 0:
            raise ValueError("Noise variance must be non-negative")
        self._noise_variance = value
        self._noise_levels = None

    def add_noise(self, K: np.ndarray) -> np.ndarray:
        """Add noise to a covariance matrix.

        For homoscedastic noise: K_noisy = K + sigma_n^2 * I
        For heteroscedastic noise: K_noisy = K + diag(sigma_n^2)

        Args:
            K: Covariance matrix of shape (n, n)

        Returns:
            Noisy covariance matrix
        """
        if self._noise_levels is not None:
            return K + np.diag(self._noise_levels)
        return K + self.noise_variance * np.eye(K.shape[0])

    def set_noise_levels(self, noise_levels: np.ndarray):
        """Set heteroscedastic noise levels for each observation.

        Args:
            noise_levels: Noise variance for each data point of shape (n,)
        """
        if np.any(noise_levels < 0):
            raise ValueError("Noise levels must be non-negative")
        self._noise_levels = noise_levels.copy()
        self._noise_variance = None

    def get_noise_covariance(self, n: int) -> np.ndarray:
        """Get the noise covariance matrix.

        Args:
            n: Number of data points

        Returns:
            Noise covariance matrix of shape (n, n)
        """
        if self._noise_levels is not None:
            return np.diag(self._noise_levels)
        return self.noise_variance * np.eye(n)

    def update_noise_estimate(self, residuals: np.ndarray):
        """Update noise estimate from residuals.

        Args:
            residuals: Model residuals (y_observed - y_predicted)
        """
        self._noise_variance = float(np.mean(residuals ** 2))
        self._noise_levels = None

    def __repr__(self):
        if self._noise_levels is not None:
            return f"NoiseModel(heteroscedastic, levels={self._noise_levels[:5]}...)"
        return f"NoiseModel(homoscedastic, variance={self.noise_variance:.4f})"


class AdaptiveNoiseModel(NoiseModel):
    """Adaptive noise model that estimates noise from data.

    Instead of fixing sigma_n^2, this model estimates it from the
    residuals of the GP fit. This is useful when the noise level
    is unknown or varies across the input space.

    The noise estimate is updated after each GP fit using:
        sigma_n^2 = (1/n) * sum((y_i - f(x_i))^2)
    """

    def __init__(self, initial_noise: float = 0.01, min_noise: float = 1e-6, max_noise: float = 1.0):
        """Initialize adaptive noise model.

        Args:
            initial_noise: Initial noise variance estimate
            min_noise: Minimum allowed noise variance
            max_noise: Maximum allowed noise variance
        """
        super().__init__(initial_noise)
        self.min_noise = min_noise
        self.max_noise = max_noise
        self.noise_history = []

    def estimate_from_residuals(self, residuals: np.ndarray) -> float:
        """Estimate noise variance from residuals.

        Args:
            residuals: y_observed - y_predicted

        Returns:
            Updated noise variance
        """
        # Use robust estimate (median absolute deviation)
        noise_var = float(np.mean(residuals ** 2))
        noise_var = max(self.min_noise, min(self.max_noise, noise_var))

        self._noise_variance = noise_var
        self.noise_history.append(noise_var)

        return noise_var

    def get_weighted_noise(self, n: int) -> np.ndarray:
        """Get weighted noise for each point (for heteroscedastic extension).

        Args:
            n: Number of data points

        Returns:
            Noise variances of shape (n,)
        """
        if self.noise_history:
            # Use recent noise estimate
            recent = self.noise_history[-10:] if len(self.noise_history) >= 10 else self.noise_history
            base = float(np.mean(recent))
        else:
            base = self.noise_variance

        return np.full(n, base)

    def __repr__(self):
        history_str = f", history={self.noise_history[-3:]}" if self.noise_history else ""
        return f"AdaptiveNoiseModel(variance={self.noise_variance:.4f}{history_str})"
