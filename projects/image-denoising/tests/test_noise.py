"""Tests for noise utilities."""

import pytest
import torch
import numpy as np

from src.noise import (
    add_gaussian_noise,
    add_salt_pepper_noise,
    add_poisson_noise,
    add_speckle_noise,
    NoiseGenerator,
)


class TestGaussianNoise:
    """Test suite for Gaussian noise."""

    def test_numpy_input(self):
        """Test Gaussian noise with numpy input."""
        image = np.random.rand(1, 64, 64).astype(np.float32)
        noisy, noise = add_gaussian_noise(image, sigma=25)

        assert noisy.shape == image.shape
        assert noise.shape == image.shape
        assert noisy.dtype == image.dtype

    def test_torch_input(self):
        """Test Gaussian noise with PyTorch input."""
        image = torch.rand(1, 64, 64)
        noisy, noise = add_gaussian_noise(image, sigma=25)

        assert noisy.shape == image.shape
        assert noise.shape == image.shape

    def test_noise_level(self):
        """Test noise level matches specified sigma."""
        image = np.zeros((1, 1000, 1000), dtype=np.float32)
        sigma = 25.0
        _, noise = add_gaussian_noise(image, sigma=sigma)

        # Check noise statistics (sigma is in [0, 255] scale, so divide by 255)
        expected_std = sigma / 255.0
        actual_std = noise.std()
        assert abs(actual_std - expected_std) < 0.01

    def test_clipping(self):
        """Test output is clipped to [0, 1]."""
        image = np.ones((1, 10, 10), dtype=np.float32) * 0.99
        noisy, _ = add_gaussian_noise(image, sigma=50, clip=True)
        assert noisy.min() >= 0.0
        assert noisy.max() <= 1.0

    def test_no_clipping(self):
        """Test output without clipping."""
        image = np.ones((1, 10, 10), dtype=np.float32) * 0.99
        noisy, _ = add_gaussian_noise(image, sigma=50, clip=False)
        # Without clipping, values may exceed [0, 1]
        assert noisy.max() > 1.0  # Should have some values > 1


class TestSaltPepperNoise:
    """Test suite for salt and pepper noise."""

    def test_numpy_input(self):
        """Test salt & pepper noise with numpy input."""
        image = np.random.rand(1, 64, 64).astype(np.float32)
        noisy, mask = add_salt_pepper_noise(image, amount=0.05)

        assert noisy.shape == image.shape
        assert mask.shape == image.shape

    def test_torch_input(self):
        """Test salt & pepper noise with PyTorch input."""
        image = torch.rand(1, 64, 64)
        noisy, mask = add_salt_pepper_noise(image, amount=0.05)

        assert noisy.shape == image.shape
        assert mask.shape == image.shape

    def test_noise_amount(self):
        """Test noise amount matches specified proportion."""
        image = np.random.rand(1, 1000, 1000).astype(np.float32)
        amount = 0.1
        noisy, mask = add_salt_pepper_noise(image, amount=amount)

        # Count corrupted pixels (salt + pepper)
        salt_count = np.sum(mask == 1.0)
        pepper_count = np.sum(mask == -1.0)
        total_corrupted = (salt_count + pepper_count) / image.size
        # Allow larger tolerance due to randomness
        assert abs(total_corrupted - amount) < 0.05

    def test_salt_pepper_values(self):
        """Test salt and pepper are set to correct values."""
        image = np.full((1, 100, 100), 0.5, dtype=np.float32)
        noisy, mask = add_salt_pepper_noise(image, amount=0.2)

        # Salt should be 1.0
        salt_mask = mask == 1.0
        if salt_mask.any():
            assert np.all(noisy[salt_mask] == 1.0)

        # Pepper should be 0.0
        pepper_mask = mask == -1.0
        if pepper_mask.any():
            assert np.all(noisy[pepper_mask] == 0.0)


class TestSpeckleNoise:
    """Test suite for speckle noise."""

    def test_basic_functionality(self):
        """Test speckle noise basic functionality."""
        image = np.random.rand(1, 64, 64).astype(np.float32)
        noisy, noise = add_speckle_noise(image, variance=0.05)

        assert noisy.shape == image.shape
        assert noise.shape == image.shape

    def test_multiplicative_nature(self):
        """Test speckle noise is multiplicative."""
        # Uniform image should have uniform noise variance
        image = np.full((1, 1000, 1000), 0.5, dtype=np.float32)
        _, noise = add_speckle_noise(image, variance=0.1)

        # The raw noise values should have std ≈ variance
        # (noise = randn * variance, so std ≈ variance)
        assert abs(noise.std() - 0.1) < 0.02


class TestNoiseGenerator:
    """Test suite for NoiseGenerator."""

    def test_default_gaussian(self):
        """Test default Gaussian noise generator."""
        gen = NoiseGenerator(noise_type="gaussian")
        image = np.random.rand(1, 64, 64).astype(np.float32)
        noisy, noise = gen(image)

        assert noisy.shape == image.shape

    def test_fixed_sigma(self):
        """Test noise generator with fixed sigma."""
        gen = NoiseGenerator(noise_type="gaussian", fixed_sigma=25.0)
        sigma = gen.get_random_sigma()
        assert sigma == 25.0

    def test_random_sigma_range(self):
        """Test random sigma is within specified range."""
        gen = NoiseGenerator(noise_type="gaussian", sigma_range=(10, 50))
        for _ in range(100):
            sigma = gen.get_random_sigma()
            assert 10 <= sigma <= 50

    def test_invalid_noise_type(self):
        """Test error on invalid noise type."""
        with pytest.raises(ValueError):
            NoiseGenerator(noise_type="invalid")

    def test_all_noise_types(self):
        """Test all supported noise types."""
        image = np.random.rand(1, 32, 32).astype(np.float32)
        for noise_type in ["gaussian", "salt_pepper", "poisson", "speckle"]:
            gen = NoiseGenerator(noise_type=noise_type)
            noisy, noise = gen(image)
            assert noisy.shape == image.shape


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
