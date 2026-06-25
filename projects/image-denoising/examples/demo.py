#!/usr/bin/env python3
"""Image Denoising Demo

This demo shows how to:
1. Create a DnCNN model
2. Add noise to images
3. Train the denoising model
4. Evaluate denoising performance
5. Denoise new images

Usage:
    python demo.py
"""

import os
import sys
import numpy as np
import torch
import matplotlib.pyplot as plt

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model import DnCNN, create_model
from src.noise import add_gaussian_noise, NoiseGenerator
from src.dataset import DenoisingDataset, create_dataloaders
from src.train import Trainer
from src.evaluate import calculate_psnr, calculate_ssim, calculate_metrics
from src.inference import Denoiser


def create_sample_image(size: int = 256) -> np.ndarray:
    """Create a sample image with various features for testing.

    Args:
        size: Image size

    Returns:
        Sample image [1, H, W] in [0, 1] range
    """
    # Create base patterns
    x = np.linspace(0, 1, size)
    y = np.linspace(0, 1, size)
    xx, yy = np.meshgrid(x, y)

    # Combine patterns
    # 1. Gradient
    gradient = (xx + yy) / 2

    # 2. Circles
    cx, cy = 0.5, 0.5
    r = np.sqrt((xx - cx)**2 + (yy - cy)**2)
    circles = (np.sin(r * 20) + 1) / 2

    # 3. Edges
    edges = np.zeros_like(xx)
    edges[size//4:3*size//4, size//4:3*size//4] = 1.0

    # Blend patterns
    image = 0.3 * gradient + 0.4 * circles + 0.3 * edges
    image = (image - image.min()) / (image.max() - image.min())

    return image[np.newaxis, :].astype(np.float32)


def demo_noise_addition():
    """Demonstrate different noise types."""
    print("\n" + "=" * 60)
    print("Demo 1: Noise Addition")
    print("=" * 60)

    # Create sample image
    clean = create_sample_image(128)

    # Add different noise types
    noise_configs = [
        ("Gaussian (σ=15)", lambda img: add_gaussian_noise(img, sigma=15)),
        ("Gaussian (σ=25)", lambda img: add_gaussian_noise(img, sigma=25)),
        ("Gaussian (σ=50)", lambda img: add_gaussian_noise(img, sigma=50)),
    ]

    print("\nNoise addition results:")
    for name, noise_fn in noise_configs:
        noisy, noise = noise_fn(clean)
        psnr = calculate_psnr(clean, noisy)
        ssim = calculate_ssim(clean, noisy)
        print(f"  {name}:")
        print(f"    PSNR: {psnr:.2f} dB, SSIM: {ssim:.4f}")


def demo_model_creation():
    """Demonstrate model creation and architecture."""
    print("\n" + "=" * 60)
    print("Demo 2: Model Architecture")
    print("=" * 60)

    # Create models with different configurations
    configs = [
        ("DnCNN-5 (light)", {"depth": 5, "num_features": 32}),
        ("DnCNN-17 (standard)", {"depth": 17, "num_features": 64}),
    ]

    for name, config in configs:
        model = DnCNN(in_channels=1, **config)
        params = sum(p.numel() for p in model.parameters())

        # Test forward pass
        x = torch.randn(1, 1, 64, 64)
        noise_pred = model(x)
        denoised = model.denoise(x)

        print(f"\n{name}:")
        print(f"  Parameters: {params:,}")
        print(f"  Input shape: {x.shape}")
        print(f"  Output shape: {noise_pred.shape}")
        print(f"  Denoised shape: {denoised.shape}")


def demo_training(num_epochs: int = 3):
    """Demonstrate training pipeline.

    Args:
        num_epochs: Number of training epochs (reduced for demo)
    """
    print("\n" + "=" * 60)
    print("Demo 3: Training Pipeline")
    print("=" * 60)

    # Create dataloaders with synthetic data
    print("\nCreating synthetic training data...")
    train_loader, val_loader = create_dataloaders(
        batch_size=4,
        patch_size=64,
        num_workers=0,
        noise_sigma_range=(10, 30),
    )

    print(f"  Training batches: {len(train_loader)}")
    print(f"  Validation batches: {len(val_loader)}")

    # Create model (small for demo)
    model = create_model("dncnn", in_channels=1, depth=5, num_features=32)

    # Create trainer
    trainer = Trainer(
        model=model,
        device="cpu",
        learning_rate=1e-3,
    )

    # Train for a few epochs
    print(f"\nTraining for {num_epochs} epochs...")
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=num_epochs,
        save_dir="/tmp/denoising_demo_checkpoints",
        save_every=1,
        early_stopping_patience=10,
    )

    # Print final metrics
    print("\nFinal training metrics:")
    for key, values in history.items():
        if values:
            print(f"  {key}: {values[-1]:.4f}")

    return model


def demo_evaluation(model: torch.nn.Module):
    """Demonstrate model evaluation.

    Args:
        model: Trained model to evaluate
    """
    print("\n" + "=" * 60)
    print("Demo 4: Model Evaluation")
    print("=" * 60)

    # Create test images
    test_images = [create_sample_image(128) for _ in range(3)]

    # Evaluate at different noise levels
    noise_levels = [15, 25, 50]
    print("\nEvaluating model at different noise levels...")

    for sigma in noise_levels:
        psnr_values = []
        ssim_values = []

        for clean in test_images:
            # Add noise
            noisy, _ = add_gaussian_noise(clean, sigma=sigma)

            # Convert to tensor
            noisy_tensor = torch.from_numpy(noisy).float().unsqueeze(0)

            # Denoise
            model.eval()
            with torch.no_grad():
                noise_pred = model(noisy_tensor)
                denoised = noisy_tensor - noise_pred

            # Calculate metrics
            denoised_np = denoised.squeeze().numpy()
            psnr = calculate_psnr(clean, denoised_np)
            ssim = calculate_ssim(clean, denoised_np)

            psnr_values.append(psnr)
            ssim_values.append(ssim)

        print(f"\n  σ = {sigma}:")
        print(f"    PSNR: {np.mean(psnr_values):.2f} ± {np.std(psnr_values):.2f} dB")
        print(f"    SSIM: {np.mean(ssim_values):.4f} ± {np.std(ssim_values):.4f}")


def demo_inference(model: torch.nn.Module):
    """Demonstrate image denoising inference.

    Args:
        model: Trained model
    """
    print("\n" + "=" * 60)
    print("Demo 5: Image Denoising")
    print("=" * 60)

    # Create denoiser
    denoiser = Denoiser(model=model, device="cpu", tile_size=None)

    # Create and noise an image
    clean = create_sample_image(128)
    noisy, _ = add_gaussian_noise(clean, sigma=25)

    # Denoise
    denoised = denoiser.denoise_image(noisy)

    # Calculate metrics
    psnr_noisy = calculate_psnr(clean, noisy)
    ssim_noisy = calculate_ssim(clean, noisy)
    psnr_denoised = calculate_psnr(clean, denoised)
    ssim_denoised = calculate_ssim(clean, denoised)

    print("\nDenoising results:")
    print(f"  Noisy image:")
    print(f"    PSNR: {psnr_noisy:.2f} dB")
    print(f"    SSIM: {ssim_noisy:.4f}")
    print(f"  Denoised image:")
    print(f"    PSNR: {psnr_denoised:.2f} dB")
    print(f"    SSIM: {ssim_denoised:.4f}")
    print(f"  Improvement:")
    print(f"    PSNR: +{psnr_denoised - psnr_noisy:.2f} dB")
    print(f"    SSIM: +{ssim_denoised - ssim_noisy:.4f}")


def main():
    """Run all demos."""
    print("Image Denoising Demo")
    print("=" * 60)
    print("This demo demonstrates the DnCNN image denoising pipeline.")
    print("Note: Using synthetic data and small model for quick demonstration.")

    # Set random seed for reproducibility
    np.random.seed(42)
    torch.manual_seed(42)

    # Run demos
    demo_noise_addition()
    demo_model_creation()
    model = demo_training(num_epochs=3)
    demo_evaluation(model)
    demo_inference(model)

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
