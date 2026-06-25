"""
Utility functions for Diffusion Model.

Contains helper functions for visualization, device management, and image processing.
"""

import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Optional, Tuple


def get_device() -> torch.device:
    """Get the best available device."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    else:
        return torch.device("cpu")


def save_images(images: torch.Tensor, path: str, nrow: int = 8):
    """
    Save a grid of images.

    Args:
        images: Tensor of images [B, C, H, W]
        path: Path to save image
        nrow: Number of images per row
    """
    from torchvision.utils import make_grid

    grid = make_grid(images, nrow=nrow, normalize=True, value_range=(-1, 1))
    grid = grid.permute(1, 2, 0).cpu().numpy()

    plt.figure(figsize=(10, 10))
    plt.imshow(grid)
    plt.axis('off')
    plt.savefig(path, bbox_inches='tight', dpi=150)
    plt.close()


def visualize_diffusion_process(
    images: List[torch.Tensor],
    timesteps: List[int],
    save_path: Optional[str] = None
):
    """
    Visualize the forward diffusion process.

    Args:
        images: List of images at different timesteps
        timesteps: Corresponding timestep values
        save_path: Optional path to save visualization
    """
    fig, axes = plt.subplots(1, len(images), figsize=(3 * len(images), 3))

    for ax, img, t in zip(axes, images, timesteps):
        if img.dim() == 4:
            img = img[0]  # Take first image from batch
        img = (img + 1) / 2  # Denormalize from [-1, 1] to [0, 1]
        img = img.permute(1, 2, 0).cpu().numpy()
        img = np.clip(img, 0, 1)

        ax.imshow(img, cmap='gray' if img.shape[-1] == 1 else None)
        ax.set_title(f't={t}')
        ax.axis('off')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
    plt.show()
    plt.close()


def visualize_reverse_process(
    model: nn.Module,
    scheduler,
    device: torch.device,
    image_size: int = 28,
    num_samples: int = 8,
    save_path: Optional[str] = None
):
    """
    Visualize the reverse denoising process.

    Args:
        model: Trained diffusion model
        scheduler: Noise scheduler
        device: Device to use
        image_size: Size of generated images
        num_samples: Number of samples to generate
        save_path: Optional path to save visualization
    """
    model.eval()

    # Start from pure noise
    x = torch.randn(num_samples, 1, image_size, image_size).to(device)

    # Store intermediate results
    intermediates = [x.clone()]

    # Reverse diffusion
    for t in reversed(range(scheduler.num_timesteps)):
        t_batch = torch.full((num_samples,), t, device=device, dtype=torch.long)

        with torch.no_grad():
            noise_pred = model(x, t_batch)

        # Reverse step
        alpha = scheduler.alphas[t]
        alpha_cumprod = scheduler.alphas_cumprod[t]
        beta = scheduler.betas[t]

        mean = scheduler.sqrt_recip_alphas[t] * (
            x - beta / scheduler.sqrt_one_minus_alphas_cumprod[t] * noise_pred
        )

        if t > 0:
            noise = torch.randn_like(x)
            variance = torch.sqrt(scheduler.posterior_variance[t])
            x = mean + variance * noise
        else:
            x = mean

        # Store intermediate results
        if t % (scheduler.num_timesteps // 10) == 0:
            intermediates.append(x.clone())

    # Visualize
    fig, axes = plt.subplots(2, len(intermediates), figsize=(3 * len(intermediates), 6))

    for i, (img, t_val) in enumerate(zip(intermediates, [scheduler.num_timesteps] + list(range(scheduler.num_timesteps - 100, -1, -100)))):
        # Top row: full batch
        grid = (img[:8] + 1) / 2
        grid = grid.clamp(0, 1)
        grid = grid.permute(0, 2, 3, 1).cpu().numpy()

        # Create grid image
        grid_img = np.concatenate([grid[i] for i in range(min(4, len(grid)))], axis=1)

        axes[0, i].imshow(grid_img, cmap='gray')
        axes[0, i].set_title(f't={t_val}')
        axes[0, i].axis('off')

        # Bottom row: single image evolution
        single = (img[0] + 1) / 2
        single = single.clamp(0, 1).permute(1, 2, 0).cpu().numpy()
        axes[1, i].imshow(single, cmap='gray')
        axes[1, i].axis('off')

    plt.suptitle('Reverse Diffusion Process', fontsize=16)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
    plt.show()
    plt.close()


def calculate_fid(real_images: torch.Tensor, fake_images: torch.Tensor) -> float:
    """
    Calculate simplified FID score between real and fake images.
    Note: This is a simplified version for educational purposes.

    Args:
        real_images: Real images tensor
        fake_images: Generated images tensor

    Returns:
        FID score (lower is better)
    """
    # Flatten images
    real_flat = real_images.view(real_images.size(0), -1).float()
    fake_flat = fake_images.view(fake_images.size(0), -1).float()

    # Calculate statistics
    mu_real = torch.mean(real_flat, dim=0)
    mu_fake = torch.mean(fake_flat, dim=0)

    sigma_real = torch.cov(real_flat.T)
    sigma_fake = torch.cov(fake_flat.T)

    # Calculate FID
    diff = mu_real - mu_fake
    covmean = torch.sqrt(sigma_real @ sigma_fake)

    fid = diff @ diff + torch.trace(sigma_real + sigma_fake - 2 * covmean)

    return fid.item()


def count_parameters(model: nn.Module) -> int:
    """Count the number of trainable parameters in a model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
