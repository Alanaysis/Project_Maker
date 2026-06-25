"""
Context Encoder Training Example.

This example demonstrates how to train the context encoder for image inpainting
using synthetic data. In a real scenario, you would use a dataset like:
- CelebA (faces)
- Places2 (scenes)
- ImageNet

The training loop implements:
1. Load/prepare training data
2. For each batch:
   a. Generate random masks
   b. Apply masks to corrupt images
   c. Train discriminator (real vs fake)
   d. Train generator (reconstruction + adversarial loss)
3. Evaluate periodically

Usage:
    python examples/train_context_encoder.py
"""

import torch
import torch.utils.data as data
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import (
    ImageInpainter,
    generate_random_rect_mask,
    compute_psnr,
    compute_ssim,
)


class SyntheticDataset(data.Dataset):
    """A synthetic dataset for demonstration.

    Generates random images with simple patterns for training.
    In practice, replace this with a real dataset (CelebA, Places2, etc.).

    Args:
        num_samples: Number of samples in the dataset.
        image_size: Size of each image.
    """

    def __init__(self, num_samples: int = 100, image_size: int = 128):
        self.num_samples = num_samples
        self.image_size = image_size
        # Pre-generate some random images for consistency
        torch.manual_seed(42)
        self.images = torch.rand(num_samples, 3, image_size, image_size) * 2 - 1

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> torch.Tensor:
        return self.images[idx]


def train(
    num_epochs: int = 5,
    batch_size: int = 4,
    image_size: int = 128,
    num_samples: int = 40,
    learning_rate: float = 0.0002,
    log_interval: int = 5,
):
    """Train the context encoder on synthetic data.

    Args:
        num_epochs: Number of training epochs.
        batch_size: Batch size.
        image_size: Input image size.
        num_samples: Number of synthetic training samples.
        learning_rate: Learning rate.
        log_interval: Print losses every N steps.
    """
    print("=" * 60)
    print("Context Encoder Training")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Epochs: {num_epochs}")
    print(f"  Batch size: {batch_size}")
    print(f"  Image size: {image_size}x{image_size}")
    print(f"  Training samples: {num_samples}")
    print(f"  Learning rate: {learning_rate}")

    # Create dataset and dataloader
    dataset = SyntheticDataset(num_samples=num_samples, image_size=image_size)
    dataloader = data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Create inpainter
    inpainter = ImageInpainter(
        image_size=(image_size, image_size),
        ngf=32,
        ndf=32,
        lambda_rec=1.0,
        lambda_adv=0.001,
        learning_rate=learning_rate,
        device="cpu",
    )

    # Training loop
    print("\nStarting training...")
    step = 0
    for epoch in range(num_epochs):
        epoch_losses = {"d_loss": 0, "g_loss": 0, "rec_loss": 0, "adv_loss": 0}

        for batch_idx, images in enumerate(dataloader):
            B = images.size(0)

            # Generate random masks for this batch
            masks = torch.stack([
                generate_random_rect_mask(
                    (image_size, image_size),
                    num_masks=1,
                    min_size_ratio=0.15,
                    max_size_ratio=0.35,
                )
                for _ in range(B)
            ])

            # Training step
            losses = inpainter.train_step(images, masks)

            # Accumulate losses
            for key in epoch_losses:
                epoch_losses[key] += losses[key]

            step += 1
            if step % log_interval == 0:
                print(
                    f"  Step {step:4d} | "
                    f"D: {losses['d_loss']:.4f} | "
                    f"G: {losses['g_loss']:.4f} | "
                    f"Rec: {losses['rec_loss']:.4f} | "
                    f"Adv: {losses['adv_loss']:.6f}"
                )

        # Epoch summary
        n_batches = len(dataloader)
        print(f"\nEpoch {epoch + 1}/{num_epochs} summary:")
        for key in epoch_losses:
            epoch_losses[key] /= n_batches
            print(f"  Avg {key}: {epoch_losses[key]:.4f}")

    # Evaluation
    print("\n" + "=" * 60)
    print("Evaluation on training data")
    print("=" * 60)

    # Use a few samples for evaluation
    eval_images = dataset.images[:4]
    eval_masks = torch.stack([
        generate_random_rect_mask((image_size, image_size), seed=i)
        for i in range(4)
    ])

    metrics = inpainter.evaluate(eval_images, eval_masks)
    print(f"\nMetrics (masked region only):")
    print(f"  PSNR: {metrics['psnr']:.2f} dB")
    print(f"  SSIM: {metrics['ssim']:.4f}")
    print(f"  L1 Error: {metrics['l1_error']:.4f}")

    # Save model
    save_path = os.path.join(os.path.dirname(__file__), "..", "checkpoint.pt")
    inpainter.save(save_path)
    print(f"\nModel saved to: {save_path}")

    print("\nTraining completed!")


if __name__ == "__main__":
    train(
        num_epochs=3,
        batch_size=4,
        image_size=128,
        num_samples=20,
        learning_rate=0.0002,
        log_interval=2,
    )
