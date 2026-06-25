"""
Training script for DDPM on MNIST dataset.

This script demonstrates how to train a diffusion model on the MNIST dataset.
The model learns to generate handwritten digits through the diffusion process.

Usage:
    python examples/train_mnist.py

The training process:
    1. Loads MNIST dataset
    2. Trains the diffusion model to predict noise
    3. Saves checkpoints and generates samples during training
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.diffusion import DiffusionModel, DiffusionTrainer
from src.unet import SimpleUNet
from src.utils import get_device, save_images


def get_mnist_dataloader(
    data_dir: str = "./data",
    batch_size: int = 128,
    num_workers: int = 4
) -> DataLoader:
    """
    Get MNIST dataloader with appropriate transforms.

    Args:
        data_dir: Directory to store MNIST data
        batch_size: Batch size for training
        num_workers: Number of data loading workers

    Returns:
        DataLoader for MNIST dataset
    """
    # Transform: convert to tensor and normalize to [-1, 1]
    transform = transforms.Compose([
        transforms.Resize(32),  # Resize to 32x32 for better UNet architecture
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))  # Normalize to [-1, 1]
    ])

    # Download and load MNIST dataset
    dataset = datasets.MNIST(
        root=data_dir,
        train=True,
        download=True,
        transform=transform
    )

    # Create dataloader
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )

    return dataloader


def train_diffusion_model(
    num_epochs: int = 50,
    batch_size: int = 128,
    learning_rate: float = 2e-4,
    num_timesteps: int = 1000,
    image_size: int = 32,
    save_dir: str = "./checkpoints",
    sample_interval: int = 5
):
    """
    Train a diffusion model on MNIST.

    Args:
        num_epochs: Number of training epochs
        batch_size: Batch size for training
        learning_rate: Learning rate for optimizer
        num_timesteps: Number of diffusion steps
        image_size: Size of images (MNIST resized to this)
        save_dir: Directory to save checkpoints
        sample_interval: Interval for generating samples
    """
    # Setup
    device = get_device()
    print(f"Using device: {device}")

    # Create save directory
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(os.path.join(save_dir, "samples"), exist_ok=True)

    # Get dataloader
    print("Loading MNIST dataset...")
    dataloader = get_mnist_dataloader(batch_size=batch_size)

    # Create model
    print("Creating diffusion model...")
    model = DiffusionModel(
        image_size=image_size,
        in_channels=1,
        num_timesteps=num_timesteps,
        model_type="simple"  # Use SimpleUNet for MNIST
    )

    # Print model info
    num_params = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {num_params:,}")

    # Create trainer
    trainer = DiffusionTrainer(
        model=model,
        learning_rate=learning_rate,
        device=device
    )

    # Training loop
    print(f"\nStarting training for {num_epochs} epochs...")
    print("=" * 50)

    best_loss = float('inf')

    for epoch in range(num_epochs):
        # Train one epoch
        avg_loss = trainer.train_epoch(dataloader)

        # Print progress
        print(f"Epoch [{epoch + 1}/{num_epochs}], Loss: {avg_loss:.6f}")

        # Save best model
        if avg_loss < best_loss:
            best_loss = avg_loss
            trainer.save_checkpoint(os.path.join(save_dir, "best_model.pt"))

        # Generate samples
        if (epoch + 1) % sample_interval == 0:
            print(f"\nGenerating samples at epoch {epoch + 1}...")

            # Generate samples
            model.eval()
            with torch.no_grad():
                samples = model.sample(
                    batch_size=16,
                    device=device
                )

                # Denormalize from [-1, 1] to [0, 1]
                samples = (samples + 1) / 2
                samples = samples.clamp(0, 1)

                # Save samples
                sample_path = os.path.join(save_dir, "samples", f"samples_epoch_{epoch + 1}.png")
                save_images(samples, sample_path, nrow=4)
                print(f"Samples saved to {sample_path}")

        # Save checkpoint every 10 epochs
        if (epoch + 1) % 10 == 0:
            trainer.save_checkpoint(
                os.path.join(save_dir, f"checkpoint_epoch_{epoch + 1}.pt")
            )

    # Save final model
    trainer.save_checkpoint(os.path.join(save_dir, "final_model.pt"))

    # Plot training loss
    plot_training_loss(trainer.losses, save_dir)

    print("\n" + "=" * 50)
    print("Training completed!")
    print(f"Best loss: {best_loss:.6f}")
    print(f"Checkpoints saved to: {save_dir}")


def plot_training_loss(losses: list, save_dir: str):
    """
    Plot training loss curve.

    Args:
        losses: List of losses per epoch
        save_dir: Directory to save plot
    """
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 6))
    plt.plot(losses, label='Training Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('DDPM Training Loss')
    plt.legend()
    plt.grid(True)

    plot_path = os.path.join(save_dir, "training_loss.png")
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Training loss plot saved to {plot_path}")


def main():
    """Main entry point for training script."""
    parser = argparse.ArgumentParser(description="Train DDPM on MNIST")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=128, help="Batch size")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--timesteps", type=int, default=1000, help="Number of diffusion steps")
    parser.add_argument("--image-size", type=int, default=32, help="Image size")
    parser.add_argument("--save-dir", type=str, default="./checkpoints", help="Save directory")
    parser.add_argument("--sample-interval", type=int, default=5, help="Sample generation interval")

    args = parser.parse_args()

    # Train model
    train_diffusion_model(
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        num_timesteps=args.timesteps,
        image_size=args.image_size,
        save_dir=args.save_dir,
        sample_interval=args.sample_interval
    )


if __name__ == "__main__":
    main()
