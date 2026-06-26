"""Tests for noise model."""

import numpy as np
import pytest
from src.noise_model import NoiseModel, AdaptiveNoiseModel


class TestNoiseModel:
    """Test suite for NoiseModel."""

    def test_homoscedastic_noise(self):
        """Homoscedastic noise should add constant to diagonal."""
        model = NoiseModel(noise_variance=0.5)
        K = np.eye(5)
        K_noisy = model.add_noise(K)
        assert np.allclose(np.diag(K_noisy), 1.5)
        assert np.allclose(K_noisy - np.diag(np.diag(K_noisy)), K - np.eye(5))

    def test_noise_covariance(self):
        """Noise covariance should be sigma_n^2 * I."""
        model = NoiseModel(noise_variance=0.3)
        n = 10
        cov = model.get_noise_covariance(n)
        assert np.allclose(cov, 0.3 * np.eye(n))

    def test_noise_variance_setter(self):
        """Noise variance setter should validate."""
        model = NoiseModel()
        with pytest.raises(ValueError):
            model.noise_variance = -0.1

    def test_update_noise_estimate(self):
        """Noise estimate should update from residuals."""
        model = NoiseModel(noise_variance=0.01)
        residuals = np.array([0.1, 0.2, 0.3, 0.4])
        model.update_noise_estimate(residuals)
        expected = np.mean(residuals ** 2)
        assert abs(model.noise_variance - expected) < 1e-10

    def test_repr_homoscedastic(self):
        """Repr should show noise type."""
        model = NoiseModel(noise_variance=0.01)
        assert "homoscedastic" in repr(model)
        assert "0.0100" in repr(model)


class TestAdaptiveNoiseModel:
    """Test suite for AdaptiveNoiseModel."""

    def test_estimate_from_residuals(self):
        """Should estimate noise from residuals."""
        model = AdaptiveNoiseModel(initial_noise=0.01)
        residuals = np.array([0.1, 0.2, 0.3])
        estimated = model.estimate_from_residuals(residuals)
        expected = np.mean(residuals ** 2)
        assert abs(estimated - expected) < 1e-10

    def test_min_max_clamping(self):
        """Should clamp noise estimate to [min, max]."""
        model = AdaptiveNoiseModel(initial_noise=0.5, min_noise=0.1, max_noise=0.3)
        # Very large residuals
        residuals = np.ones(10) * 100.0
        estimated = model.estimate_from_residuals(residuals)
        assert estimated <= 0.3

        model2 = AdaptiveNoiseModel(initial_noise=0.1, min_noise=0.5, max_noise=1.0)
        # Very small residuals
        residuals = np.zeros(10)
        estimated = model2.estimate_from_residuals(residuals)
        assert estimated >= 0.5

    def test_noise_history(self):
        """Should track noise history."""
        model = AdaptiveNoiseModel()
        model.estimate_from_residuals(np.array([0.1]))
        model.estimate_from_residuals(np.array([0.2]))
        assert len(model.noise_history) == 2

    def test_weighted_noise(self):
        """Should return uniform noise when no history."""
        model = AdaptiveNoiseModel()
        n = 5
        noise = model.get_weighted_noise(n)
        assert noise.shape == (n,)
        assert np.allclose(noise, noise[0])  # All same when no history

    def test_repr_with_history(self):
        """Repr should show history when available."""
        model = AdaptiveNoiseModel()
        model.estimate_from_residuals(np.array([0.1]))
        model.estimate_from_residuals(np.array([0.2]))
        assert "history" in repr(model)
