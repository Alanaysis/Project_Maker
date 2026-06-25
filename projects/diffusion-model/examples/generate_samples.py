"""
Generate samples from a trained diffusion model.

This script loads a trained DDPM model and generates new MNIST digits.

Usage:
    python examples/generate_samples.py --checkpoint ./checkpoints/best_model.pt

The generation process:
    1. Loads trained model from checkpoint
    2. Starts from pure Gaussian noise
    3. Iteratively denoises using the reverse diffusion process
    4. Saves generated images
"""

import torch
import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.diffusion import DiffusionModel
from src.utils import get_device, save_images, visualize_reverse_process


def load_model(
    checkpoint_path: str,
    image_size: int = 32,
    num_timesteps: int = 1000,
    device: torch.device = None
) -> DiffusionModel:
    """
    Load a trained diffusion model from checkpoint.

    Args:
        checkpoint_path: Path to model checkpoint
        image_size: Size of images
        num_timesteps: Number of diffusion steps
        device: Device to load model on

    Returns:
        Loaded DiffusionModel
    """
    if device is None:
        device = get_device()

    # Create model
    model = DiffusionModel(
        image_size=image_size,
        in_channels=1,
        num_timesteps=num_timesteps,
        model_type="simple"
    )

    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])

    # Move to device
    model = model.to(device)
    model.scheduler = model.scheduler.to(device)

    print(f"Model loaded from {checkpoint_path}")
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    return model


def generate_samples(
    model: DiffusionModel,
    num_samples: int = 16,
    device: torch.device = None,
    save_path: str = None,
    use_ddim: bool = False,
    ddim_steps: int = 50
):
    """
    Generate new samples from the model.

    Args:
        model: Trained diffusion model
        num_samples: Number of samples to generate
        device: Device to use
        save_path: Path to save generated images
        use_ddim: Whether to use DDIM sampling
        ddim_steps: Number of DDIM steps (if using DDIM)
    """
    if device is None:
        device = next(model.parameters()).device

    print(f"\nGenerating {num_samples} samples...")
    print(f"Using {'DDIM' if use_ddim else 'DDPM'} sampling")

    # Generate samples
    model.eval()
    with torch.no_grad():
        if use_ddim:
            samples = model.sample_ddim(
                batch_size=num_samples,
                device=device,
                ddim_steps=ddim_steps
            )
        else:
            samples = model.sample(
                batch_size=num_samples,
                device=device
            )

    # Denormalize from [-1, 1] to [0, 1]
    samples = (samples + 1) / 2
    samples = samples.clamp(0, 1)

    # Save samples
    if save_path:
        save_images(samples, save_path, nrow=int(num_samples ** 0.5))
        print(f"Samples saved to {save_path}")

    return samples


def generate_with_visualization(
    model: DiffusionModel,
    device: torch.device = None,
    save_dir: str = "./generated"
):
    """
    Generate samples with visualization of the reverse process.

    Args:
        model: Trained diffusion model
        device: Device to use
        save_dir: Directory to save visualizations
    """
    if device is None:
        device = next(model.parameters()).device

    os.makedirs(save_dir, exist_ok=True)

    print("\nGenerating samples with reverse process visualization...")

    # Generate with intermediates
    model.eval()
    with torch.no_grad():
        samples, intermediates = model.sample(
            batch_size=8,
            device=device,
            return_intermediates=True
        )

    # Denormalize
    samples = (samples + 1) / 2
    samples = samples.clamp(0, 1)

    # Save final samples
    save_path = os.path.join(save_dir, "generated_samples.png")
    save_images(samples, save_path, nrow=4)
    print(f"Final samples saved to {save_path}")

    # Visualize reverse process
    print("Visualizing reverse diffusion process...")
    visualize_reverse_process(
        model=model,
        scheduler=model.scheduler,
        device=device,
        image_size=model.image_size,
        num_samples=4,
        save_path=os.path.join(save_dir, "reverse_process.png")
    )


def interpolate_latent(
    model: DiffusionModel,
    device: torch.device = None,
    num_interpolations: int = 10,
    save_path: str = None
):
    """
    Generate interpolations between two random noise vectors.

    This demonstrates the smooth latent space of diffusion models.

    Args:
        model: Trained diffusion model
        device: Device to use
        num_interpolations: Number of interpolation steps
        save_path: Path to save interpolations
    """
    if device is None:
        device = next(model.parameters()).device

    print(f"\nGenerating {num_interpolations} interpolations...")

    # Generate two random noise vectors
    z1 = torch.randn(1, 1, model.image_size, model.image_size).to(device)
    z2 = torch.randn(1, 1, model.image_size, model.image_size).to(device)

    # Interpolate
    interpolations = []
    for alpha in torch.linspace(0, 1, num_interpolations):
        z = (1 - alpha) * z1 + alpha * z2
        interpolations.append(z)

    # Generate images from interpolated noise
    model.eval()
    generated_images = []
    with torch.no_grad():
        for z in interpolations:
            # Use fewer steps for faster generation
            img = model.sample_ddim(
                batch_size=1,
                device=device,
                ddim_steps=50
            )
            generated_images.append(img)

    # Concatenate and save
    all_images = torch.cat(generated_images, dim=0)
    all_images = (all_images + 1) / 2
    all_images = all_images.clamp(0, 1)

    if save_path:
        save_images(all_images, save_path, nrow=num_interpolations)
        print(f"Interpolations saved to {save_path}")

    return all_images


def main():
    """Main entry point for generation script."""
    parser = argparse.ArgumentParser(description="Generate samples from trained DDPM")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--num-samples", type=int, default=16, help="Number of samples to generate")
    parser.add_argument("--image-size", type=int, default=32, help="Image size")
    parser.add_argument("--timesteps", type=int, default=1000, help="Number of diffusion steps")
    parser.add_argument("--save-dir", type=str, default="./generated", help="Save directory")
    parser.add_argument("--use-ddim", action="store_true", help="Use DDIM sampling")
    parser.add_argument("--ddim-steps", type=int, default=50, help="Number of DDIM steps")
    parser.add_argument("--visualize", action="store_true", help="Visualize reverse process")
    parser.add_argument("--interpolate", action="store_true", help="Generate interpolations")

    args = parser.parse_args()

    # Setup
    device = get_device()
    print(f"Using device: {device}")

    # Create save directory
    os.makedirs(args.save_dir, exist_ok=True)

    # Load model
    model = load_model(
        args.checkpoint,
        image_size=args.image_size,
        num_timesteps=args.timesteps,
        device=device
    )

    # Generate samples
    save_path = os.path.join(args.save_dir, "samples.png")
    generate_samples(
        model=model,
        num_samples=args.num_samples,
        device=device,
        save_path=save_path,
        use_ddim=args.use_ddim,
        ddim_steps=args.ddim_steps
    )

    # Visualize reverse process
    if args.visualize:
        generate_with_visualization(
            model=model,
            device=device,
            save_dir=args.save_dir
        )

    # Generate interpolations
    if args.interpolate:
        interpolate_path = os.path.join(args.save_dir, "interpolations.png")
        interpolate_latent(
            model=model,
            device=device,
            num_interpolations=10,
            save_path=interpolate_path
        )

    print("\nGeneration completed!")


if __name__ == "__main__":
    main()
