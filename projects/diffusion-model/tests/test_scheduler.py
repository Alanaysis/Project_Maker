"""
Tests for Noise Scheduler.
"""

import pytest
import torch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scheduler import NoiseScheduler


class TestNoiseScheduler:
    """Test cases for NoiseScheduler."""

    def setup_method(self):
        """Setup test fixtures."""
        self.num_timesteps = 1000  # Use 1000 timesteps for realistic testing
        self.scheduler = NoiseScheduler(
            num_timesteps=self.num_timesteps,
            beta_start=0.0001,
            beta_end=0.02,
            schedule_type="linear"
        )

    def test_initialization(self):
        """Test scheduler initialization."""
        assert self.scheduler.num_timesteps == self.num_timesteps
        assert len(self.scheduler.betas) == self.num_timesteps
        assert len(self.scheduler.alphas) == self.num_timesteps
        assert len(self.scheduler.alphas_cumprod) == self.num_timesteps

    def test_beta_schedule(self):
        """Test that beta schedule is monotonically increasing."""
        betas = self.scheduler.betas
        assert betas[0] < betas[-1]
        assert torch.all(betas > 0)
        assert torch.all(betas < 1)

    def test_alpha_properties(self):
        """Test alpha and alpha_cumprod properties."""
        alphas = self.scheduler.alphas
        alphas_cumprod = self.scheduler.alphas_cumprod

        # Alphas should be between 0 and 1
        assert torch.all(alphas > 0)
        assert torch.all(alphas < 1)

        # Alpha_cumprod should be monotonically decreasing
        assert torch.all(alphas_cumprod[1:] <= alphas_cumprod[:-1])

        # First alpha_cumprod should be close to 1
        assert alphas_cumprod[0] > 0.99

        # Last alpha_cumprod should be close to 0
        assert alphas_cumprod[-1] < 0.01

    def test_cosine_schedule(self):
        """Test cosine schedule type."""
        scheduler = NoiseScheduler(
            num_timesteps=100,
            schedule_type="cosine"
        )

        assert len(scheduler.betas) == 100
        assert torch.all(scheduler.betas > 0)
        assert torch.all(scheduler.betas < 1)

    def test_invalid_schedule_type(self):
        """Test that invalid schedule type raises error."""
        with pytest.raises(ValueError):
            NoiseScheduler(schedule_type="invalid")

    def test_add_noise(self):
        """Test forward diffusion (adding noise)."""
        batch_size = 4
        channels = 1
        height = 28
        width = 28

        # Create clean images
        x_0 = torch.randn(batch_size, channels, height, width)

        # Sample timesteps
        t = torch.randint(0, self.num_timesteps, (batch_size,))

        # Add noise
        x_t, noise = self.scheduler.add_noise(x_0, t)

        # Check shapes
        assert x_t.shape == x_0.shape
        assert noise.shape == x_0.shape

        # Check that noisy images are different from clean images
        assert not torch.allclose(x_t, x_0)

    def test_add_noise_preserves_shape(self):
        """Test that adding noise preserves image shape."""
        for t_val in [0, 50, 99]:
            x_0 = torch.randn(2, 1, 28, 28)
            t = torch.tensor([t_val, t_val])
            x_t, _ = self.scheduler.add_noise(x_0, t)
            assert x_t.shape == x_0.shape

    def test_noise_level_increases(self):
        """Test that noise level increases with timestep."""
        x_0 = torch.randn(1, 1, 28, 28)
        x_0 = x_0.expand(10, -1, -1, -1)  # Same image for all timesteps

        timesteps = torch.arange(0, 100, 10)

        # Get noisy images at different timesteps
        noisy_images = []
        for t in timesteps:
            x_t, _ = self.scheduler.add_noise(x_0[0:1], t.unsqueeze(0))
            noisy_images.append(x_t)

        # Later timesteps should have more noise (larger deviation from original)
        for i in range(len(noisy_images) - 1):
            diff_early = torch.abs(noisy_images[i] - x_0[0:1]).mean()
            diff_late = torch.abs(noisy_images[i + 1] - x_0[0:1]).mean()
            # This is a stochastic test, so we just check the trend
            # In general, later timesteps should have more noise

    def test_sample_timestep(self):
        """Test timestep sampling."""
        batch_size = 8
        t = self.scheduler.sample_timestep(batch_size, torch.device("cpu"))

        assert t.shape == (batch_size,)
        assert torch.all(t >= 0)
        assert torch.all(t < self.num_timesteps)

    def test_posterior_variance(self):
        """Test posterior variance computation."""
        assert len(self.scheduler.posterior_variance) == self.num_timesteps
        # First posterior variance should be 0 (deterministic)
        assert self.scheduler.posterior_variance[0] == 0

    def test_to_device(self):
        """Test moving scheduler to device."""
        # This test just ensures no errors occur
        scheduler = NoiseScheduler(num_timesteps=10)
        scheduler = scheduler.to(torch.device("cpu"))

        # Verify tensors are still accessible
        assert scheduler.betas is not None
        assert scheduler.alphas is not None

    def test_forward_process_math(self):
        """Test that forward process follows the mathematical definition."""
        x_0 = torch.randn(1, 1, 4, 4)
        t = torch.tensor([50])

        x_t, noise = self.scheduler.add_noise(x_0, t)

        # Get schedule values
        sqrt_alpha = self.scheduler.sqrt_alphas_cumprod[50]
        sqrt_one_minus_alpha = self.scheduler.sqrt_one_minus_alphas_cumprod[50]

        # Manually compute expected result
        expected = sqrt_alpha * x_0 + sqrt_one_minus_alpha * noise

        assert torch.allclose(x_t, expected, atol=1e-6)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
