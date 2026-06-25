"""
Noise Scheduler for Diffusion Models

Implements the noise scheduling for forward diffusion process.
Based on the DDPM paper: https://arxiv.org/abs/2006.11239
"""

import torch
import numpy as np
from typing import Tuple


class NoiseScheduler:
    """
    Noise scheduler for DDPM (Denoising Diffusion Probabilistic Models).

    Controls the forward diffusion process by adding Gaussian noise to images
    according to a predefined schedule.

    The forward process is defined as:
        q(x_t | x_0) = N(x_t; sqrt(alpha_t) * x_0, (1 - alpha_t) * I)

    where alpha_t = prod(delta_s) for s=1 to t, and delta_s = 1 - beta_s.
    """

    def __init__(
        self,
        num_timesteps: int = 1000,
        beta_start: float = 0.0001,
        beta_end: float = 0.02,
        schedule_type: str = "linear"
    ):
        """
        Initialize noise scheduler.

        Args:
            num_timesteps: Number of diffusion steps (T)
            beta_start: Starting noise level
            beta_end: Ending noise level
            schedule_type: Type of noise schedule ("linear" or "cosine")
        """
        self.num_timesteps = num_timesteps
        self.beta_start = beta_start
        self.beta_end = beta_end
        self.schedule_type = schedule_type

        # Compute beta schedule
        if schedule_type == "linear":
            self.betas = self._linear_schedule()
        elif schedule_type == "cosine":
            self.betas = self._cosine_schedule()
        else:
            raise ValueError(f"Unknown schedule type: {schedule_type}")

        # Compute alpha and related quantities
        self.alphas = 1.0 - self.betas
        self.alphas_cumprod = torch.cumprod(self.alphas, dim=0)
        self.alphas_cumprod_prev = torch.cat([torch.tensor([1.0]), self.alphas_cumprod[:-1]])

        # Pre-compute values for forward process
        self.sqrt_alphas_cumprod = torch.sqrt(self.alphas_cumprod)
        self.sqrt_one_minus_alphas_cumprod = torch.sqrt(1.0 - self.alphas_cumprod)

        # Pre-compute values for reverse process
        self.sqrt_recip_alphas = torch.sqrt(1.0 / self.alphas)
        self.posterior_variance = (
            self.betas * (1.0 - self.alphas_cumprod_prev) / (1.0 - self.alphas_cumprod)
        )

    def _linear_schedule(self) -> torch.Tensor:
        """Create linear beta schedule."""
        return torch.linspace(self.beta_start, self.beta_end, self.num_timesteps)

    def _cosine_schedule(self) -> torch.Tensor:
        """
        Create cosine beta schedule.
        From: https://arxiv.org/abs/2102.09672
        """
        steps = self.num_timesteps + 1
        x = torch.linspace(0, self.num_timesteps, steps)
        alphas_cumprod = torch.cos(((x / self.num_timesteps) + 0.008) / 1.008 * torch.pi * 0.5) ** 2
        alphas_cumprod = alphas_cumprod / alphas_cumprod[0]
        betas = 1 - (alphas_cumprod[1:] / alphas_cumprod[:-1])
        return torch.clip(betas, 0.0001, 0.9999)

    def add_noise(
        self,
        x_0: torch.Tensor,
        t: torch.Tensor,
        noise: torch.Tensor = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward diffusion process: add noise to clean image.

        Args:
            x_0: Clean images [B, C, H, W]
            t: Timestep indices [B]
            noise: Optional pre-generated noise

        Returns:
            Tuple of (noisy_images, noise_added)
        """
        if noise is None:
            noise = torch.randn_like(x_0)

        # Get schedule values for timestep t
        sqrt_alpha = self.sqrt_alphas_cumprod[t].view(-1, 1, 1, 1)
        sqrt_one_minus_alpha = self.sqrt_one_minus_alphas_cumprod[t].view(-1, 1, 1, 1)

        # Forward process: x_t = sqrt(alpha_t) * x_0 + sqrt(1 - alpha_t) * epsilon
        x_t = sqrt_alpha * x_0 + sqrt_one_minus_alpha * noise

        return x_t, noise

    def sample_timestep(self, batch_size: int, device: torch.device) -> torch.Tensor:
        """Sample random timesteps for training."""
        return torch.randint(0, self.num_timesteps, (batch_size,), device=device)

    def to(self, device: torch.device):
        """Move all tensors to device."""
        self.betas = self.betas.to(device)
        self.alphas = self.alphas.to(device)
        self.alphas_cumprod = self.alphas_cumprod.to(device)
        self.alphas_cumprod_prev = self.alphas_cumprod_prev.to(device)
        self.sqrt_alphas_cumprod = self.sqrt_alphas_cumprod.to(device)
        self.sqrt_one_minus_alphas_cumprod = self.sqrt_one_minus_alphas_cumprod.to(device)
        self.sqrt_recip_alphas = self.sqrt_recip_alphas.to(device)
        self.posterior_variance = self.posterior_variance.to(device)
        return self
