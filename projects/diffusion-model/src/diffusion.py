"""
Diffusion Model - Core Implementation

Implements the DDPM (Denoising Diffusion Probabilistic Model) algorithm.
Based on: https://arxiv.org/abs/2006.11239

This module contains the main DiffusionModel class that combines:
- UNet for noise prediction
- NoiseScheduler for forward/reverse processes
- Training loop
- Sampling (generation) procedure
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Adam
from torch.utils.data import DataLoader
from typing import Optional, Tuple, List
import numpy as np
from tqdm import tqdm

from .unet import UNet, SimpleUNet
from .scheduler import NoiseScheduler


class DiffusionModel(nn.Module):
    """
    DDPM (Denoising Diffusion Probabilistic Model)

    Implements the complete diffusion model including:
    - Forward diffusion process (adding noise)
    - Reverse denoising process (removing noise)
    - Training procedure
    - Sampling (image generation)

    The model learns to predict the noise added at each timestep,
    allowing it to iteratively denoise and generate new images.
    """

    def __init__(
        self,
        model: Optional[nn.Module] = None,
        image_size: int = 28,
        in_channels: int = 1,
        num_timesteps: int = 1000,
        beta_start: float = 0.0001,
        beta_end: float = 0.02,
        schedule_type: str = "linear",
        model_type: str = "simple"
    ):
        """
        Initialize diffusion model.

        Args:
            model: Optional pre-built model (UNet or SimpleUNet)
            image_size: Size of input images
            in_channels: Number of image channels (1 for grayscale)
            num_timesteps: Number of diffusion steps
            beta_start: Starting noise level
            beta_end: Ending noise level
            schedule_type: Type of noise schedule
            model_type: Type of model to use ("simple" or "full")
        """
        super().__init__()

        self.image_size = image_size
        self.in_channels = in_channels
        self.num_timesteps = num_timesteps

        # Initialize noise scheduler
        self.scheduler = NoiseScheduler(
            num_timesteps=num_timesteps,
            beta_start=beta_start,
            beta_end=beta_end,
            schedule_type=schedule_type
        )

        # Initialize model
        if model is not None:
            self.model = model
        elif model_type == "simple":
            self.model = SimpleUNet(
                in_channels=in_channels,
                out_channels=in_channels
            )
        else:
            self.model = UNet(
                in_channels=in_channels,
                out_channels=in_channels,
                hidden_channels=[64, 128, 256],
                attention=True
            )

    def forward(self, x: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        """
        Predict noise for given noisy image and timestep.

        Args:
            x: Noisy images [B, C, H, W]
            t: Timestep indices [B]

        Returns:
            Predicted noise [B, C, H, W]
        """
        return self.model(x, t)

    def training_loss(
        self,
        x_0: torch.Tensor,
        noise: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Calculate training loss for a batch of clean images.

        The training objective is to predict the noise added to the image.
        Loss = MSE(predicted_noise, actual_noise)

        Args:
            x_0: Clean images [B, C, H, W]
            noise: Optional pre-generated noise

        Returns:
            MSE loss
        """
        batch_size = x_0.shape[0]
        device = x_0.device

        # Sample random timesteps
        t = self.scheduler.sample_timestep(batch_size, device)

        # Sample noise
        if noise is None:
            noise = torch.randn_like(x_0)

        # Add noise to images (forward process)
        x_t, noise = self.scheduler.add_noise(x_0, t, noise)

        # Predict noise
        noise_pred = self.model(x_t, t)

        # MSE loss between predicted and actual noise
        loss = F.mse_loss(noise_pred, noise)

        return loss

    @torch.no_grad()
    def sample(
        self,
        batch_size: int = 16,
        device: Optional[torch.device] = None,
        return_intermediates: bool = False
    ) -> torch.Tensor:
        """
        Generate new images using the reverse diffusion process.

        Starting from pure noise, iteratively denoise to generate images.

        Args:
            batch_size: Number of images to generate
            device: Device to use for generation
            return_intermediates: Whether to return intermediate results

        Returns:
            Generated images [B, C, H, W]
            If return_intermediates is True, also returns list of intermediate states
        """
        if device is None:
            device = next(self.parameters()).device

        self.eval()

        # Start from pure noise
        x = torch.randn(batch_size, self.in_channels, self.image_size, self.image_size).to(device)

        intermediates = [x.clone()]

        # Reverse diffusion process
        for t in tqdm(reversed(range(self.num_timesteps)), total=self.num_timesteps, desc="Sampling"):
            t_batch = torch.full((batch_size,), t, device=device, dtype=torch.long)

            # Predict noise
            noise_pred = self.model(x, t_batch)

            # Get scheduler values
            alpha = self.scheduler.alphas[t]
            alpha_cumprod = self.scheduler.alphas_cumprod[t]
            beta = self.scheduler.betas[t]

            # Compute mean of p(x_{t-1} | x_t)
            mean = self.scheduler.sqrt_recip_alphas[t] * (
                x - beta / self.scheduler.sqrt_one_minus_alphas_cumprod[t] * noise_pred
            )

            # Add noise (except for the last step)
            if t > 0:
                noise = torch.randn_like(x)
                variance = torch.sqrt(self.scheduler.posterior_variance[t])
                x = mean + variance * noise
            else:
                x = mean

            # Store intermediate results
            if return_intermediates and t % (self.num_timesteps // 10) == 0:
                intermediates.append(x.clone())

        if return_intermediates:
            return x, intermediates

        return x

    @torch.no_grad()
    def sample_ddim(
        self,
        batch_size: int = 16,
        device: Optional[torch.device] = None,
        ddim_steps: int = 50,
        eta: float = 0.0
    ) -> torch.Tensor:
        """
        Generate images using DDIM (Denoising Diffusion Implicit Models) sampling.

        DDIM allows for faster sampling by using fewer steps.
        Based on: https://arxiv.org/abs/2010.02502

        Args:
            batch_size: Number of images to generate
            device: Device to use
            ddim_steps: Number of DDIM steps (less than num_timesteps)
            eta: Controls stochasticity (0 = deterministic, 1 = DDPM)

        Returns:
            Generated images [B, C, H, W]
        """
        if device is None:
            device = next(self.parameters()).device

        self.eval()

        # Create timestep sequence for DDIM
        step_size = self.num_timesteps // ddim_steps
        timesteps = list(range(0, self.num_timesteps, step_size))
        timesteps = list(reversed(timesteps))

        # Start from pure noise
        x = torch.randn(batch_size, self.in_channels, self.image_size, self.image_size).to(device)

        for i, t in enumerate(tqdm(timesteps, desc="DDIM Sampling")):
            t_batch = torch.full((batch_size,), t, device=device, dtype=torch.long)

            # Predict noise
            noise_pred = self.model(x, t_batch)

            # Get alpha values
            alpha_cumprod = self.scheduler.alphas_cumprod[t]
            alpha_cumprod_prev = self.scheduler.alphas_cumprod_prev[t] if t > 0 else torch.tensor(1.0)

            # Predict x_0
            pred_x0 = (x - torch.sqrt(1 - alpha_cumprod) * noise_pred) / torch.sqrt(alpha_cumprod)
            pred_x0 = torch.clamp(pred_x0, -1, 1)

            # Compute variance
            sigma = eta * torch.sqrt((1 - alpha_cumprod_prev) / (1 - alpha_cumprod)) * torch.sqrt(1 - alpha_cumprod / alpha_cumprod_prev)

            # Direction pointing to x_t
            pred_dir = torch.sqrt(1 - alpha_cumprod_prev - sigma ** 2) * noise_pred

            # Compute x_{t-1}
            x = torch.sqrt(alpha_cumprod_prev) * pred_x0 + pred_dir

            if eta > 0 and i < len(timesteps) - 1:
                noise = torch.randn_like(x)
                x = x + sigma * noise

        return x


class DiffusionTrainer:
    """
    Trainer class for Diffusion Models.

    Handles the training loop, logging, and checkpointing.
    """

    def __init__(
        self,
        model: DiffusionModel,
        learning_rate: float = 2e-4,
        device: Optional[torch.device] = None
    ):
        """
        Initialize trainer.

        Args:
            model: Diffusion model to train
            learning_rate: Learning rate for optimizer
            device: Device to use for training
        """
        self.model = model
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)

        # Move scheduler to device
        self.model.scheduler = self.model.scheduler.to(self.device)

        # Optimizer
        self.optimizer = Adam(self.model.parameters(), lr=learning_rate)

        # Training history
        self.losses = []

    def train_epoch(self, dataloader: DataLoader) -> float:
        """
        Train for one epoch.

        Args:
            dataloader: DataLoader for training data

        Returns:
            Average loss for the epoch
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch in tqdm(dataloader, desc="Training"):
            # Get images (handle both tuple and tensor formats)
            if isinstance(batch, (list, tuple)):
                images = batch[0]
            else:
                images = batch

            images = images.to(self.device)

            # Normalize to [-1, 1] if needed
            if images.min() >= 0 and images.max() <= 1:
                images = images * 2 - 1

            # Forward pass and compute loss
            loss = self.model.training_loss(images)

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()

            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)

            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches
        self.losses.append(avg_loss)

        return avg_loss

    def train(
        self,
        dataloader: DataLoader,
        num_epochs: int = 100,
        sample_interval: int = 10,
        save_path: Optional[str] = None
    ) -> List[float]:
        """
        Train the model for multiple epochs.

        Args:
            dataloader: DataLoader for training data
            num_epochs: Number of training epochs
            sample_interval: Interval for generating samples
            save_path: Path to save model checkpoints

        Returns:
            List of losses for each epoch
        """
        print(f"Training on {self.device}")
        print(f"Model parameters: {sum(p.numel() for p in self.model.parameters()):,}")

        for epoch in range(num_epochs):
            # Train one epoch
            avg_loss = self.train_epoch(dataloader)

            # Print progress
            print(f"Epoch {epoch + 1}/{num_epochs}, Loss: {avg_loss:.6f}")

            # Generate samples
            if (epoch + 1) % sample_interval == 0:
                self._generate_samples(epoch + 1)

            # Save checkpoint
            if save_path and (epoch + 1) % 10 == 0:
                self.save_checkpoint(f"{save_path}/checkpoint_{epoch + 1}.pt")

        return self.losses

    @torch.no_grad()
    def _generate_samples(self, epoch: int, num_samples: int = 16):
        """Generate and display samples during training."""
        self.model.eval()
        samples = self.model.sample(batch_size=num_samples, device=self.device)

        # Denormalize
        samples = (samples + 1) / 2
        samples = samples.clamp(0, 1)

        print(f"\nGenerated samples at epoch {epoch}")
        print(f"Sample shape: {samples.shape}")
        print(f"Sample range: [{samples.min():.3f}, {samples.max():.3f}]")

        self.model.train()

    def save_checkpoint(self, path: str):
        """Save model checkpoint."""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'losses': self.losses
        }, path)
        print(f"Checkpoint saved to {path}")

    def load_checkpoint(self, path: str):
        """Load model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.losses = checkpoint['losses']
        print(f"Checkpoint loaded from {path}")
