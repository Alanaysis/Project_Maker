"""
Basic Image Inpainting Example.

This example demonstrates the core image inpainting workflow:
1. Create a synthetic image
2. Generate a mask to corrupt it
3. Run the context encoder to inpaint the masked region
4. Evaluate the result

Usage:
    python examples/basic_inpainting.py
"""

import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import (
    ImageInpainter,
    generate_center_mask,
    generate_random_rect_mask,
    generate_irregular_mask,
    apply_mask,
    compute_psnr,
    compute_ssim,
)


def create_synthetic_image(size: int = 128) -> torch.Tensor:
    """Create a simple synthetic image with geometric patterns.

    This creates a test image with:
    - A gradient background
    - Circular and rectangular patterns
    - Multiple color channels

    Args:
        size: Image size (size x size).

    Returns:
        Image tensor in [-1, 1] range, shape (3, size, size).
    """
    image = torch.zeros(3, size, size)

    # Create coordinate grids
    y = torch.linspace(-1, 1, size).unsqueeze(1).expand(size, size)
    x = torch.linspace(-1, 1, size).unsqueeze(0).expand(size, size)

    # Red channel: vertical gradient
    image[0] = (y + 1) / 2  # [0, 1]

    # Green channel: horizontal gradient
    image[1] = (x + 1) / 2  # [0, 1]

    # Blue channel: circular pattern
    r = torch.sqrt(x ** 2 + y ** 2)
    image[2] = torch.cos(r * 3.14159 * 3) * 0.5 + 0.5

    # Add a bright rectangle in the center
    cx, cy = size // 2, size // 2
    s = size // 6
    image[:, cy - s:cy + s, cx - s:cx + s] = 1.0

    # Scale to [-1, 1]
    image = image * 2 - 1
    return image


def main():
    """Run the basic inpainting example."""
    print("=" * 60)
    print("Image Inpainting - Basic Example")
    print("=" * 60)

    # Step 1: Create a synthetic image
    print("\n[1/5] Creating synthetic image...")
    image = create_synthetic_image(128)
    print(f"  Image shape: {image.shape}")
    print(f"  Value range: [{image.min():.2f}, {image.max():.2f}]")

    # Step 2: Generate different types of masks
    print("\n[2/5] Generating masks...")

    center_mask = generate_center_mask((128, 128), mask_ratio=0.25)
    print(f"  Center mask - masked pixels: {center_mask.sum().int().item()}")

    rect_mask = generate_random_rect_mask((128, 128), num_masks=2, seed=42)
    print(f"  Random rect mask - masked pixels: {rect_mask.sum().int().item()}")

    irregular_mask = generate_irregular_mask((128, 128), num_strokes=8, seed=42)
    print(f"  Irregular mask - masked pixels: {irregular_mask.sum().int().item()}")

    # Step 3: Apply mask to create corrupted image
    print("\n[3/5] Applying mask to image...")
    masked_image = apply_mask(image, center_mask, mask_value=0.0)
    print(f"  Masked image shape: {masked_image.shape}")

    # Step 4: Create inpainter and perform inpainting
    print("\n[4/5] Running inpainting (untrained model)...")
    inpainter = ImageInpainter(
        image_size=(128, 128),
        ngf=32,  # Smaller for demo speed
        ndf=32,
        device="cpu",
    )

    # Note: This uses a randomly initialized model, so results will be noise.
    # In practice, you would load a pre-trained model or train on your dataset.
    result = inpainter.inpaint(image, center_mask, blend=True)
    print(f"  Result shape: {result.shape}")
    print(f"  Result range: [{result.min():.2f}, {result.max():.2f}]")

    # Step 5: Evaluate
    print("\n[5/5] Evaluating quality...")
    # Convert to [0, 1] for metrics
    pred_normalized = (result + 1) / 2
    target_normalized = (image + 1) / 2

    psnr = compute_psnr(pred_normalized, target_normalized, center_mask)
    ssim = compute_ssim(pred_normalized, target_normalized, center_mask)
    print(f"  PSNR: {psnr:.2f} dB")
    print(f"  SSIM: {ssim:.4f}")

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)
    print("\nNote: Results are from an untrained model.")
    print("For meaningful results, train the model on a real dataset.")
    print("See examples/train_context_encoder.py for training.")


if __name__ == "__main__":
    main()
