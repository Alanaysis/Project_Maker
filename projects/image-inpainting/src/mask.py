"""
Mask Generation Utilities for Image Inpainting.

This module provides various mask generation strategies used to create
corrupted (masked) images for inpainting training and evaluation.

Mask Types:
1. **Center Mask**: A rectangular mask placed at the center of the image.
   Used in the original Context Encoder paper for simple evaluation.

2. **Random Rectangular Mask**: Randomly placed rectangular holes of varying
   sizes. Provides more diverse training data.

3. **Irregular Mask**: Free-form masks with irregular shapes, simulating
   real-world damage patterns (scratches, missing pieces, etc.).

The masks are binary tensors where:
- 1 = missing region (to be inpainted)
- 0 = known region (preserved from original image)
"""

import torch
import numpy as np
from typing import Tuple, Optional, List


def generate_center_mask(
    image_size: Tuple[int, int],
    mask_ratio: float = 0.25,
) -> torch.Tensor:
    """Generate a rectangular mask at the center of the image.

    This is the simplest mask type, commonly used for baseline evaluation.
    The mask covers a square region at the center whose side length is
    mask_ratio * min(H, W).

    Args:
        image_size: (height, width) of the image.
        mask_ratio: Ratio of mask size to the smaller image dimension.
            Default 0.25 means the mask covers 25% of the smaller dimension.

    Returns:
        Binary mask tensor of shape (1, H, W).
        1 = masked (missing) region, 0 = known region.

    Example:
        >>> mask = generate_center_mask((128, 128), mask_ratio=0.25)
        >>> mask.shape
        torch.Size([1, 128, 128])
    """
    h, w = image_size
    mask = torch.zeros(1, h, w)

    mask_h = int(h * mask_ratio)
    mask_w = int(w * mask_ratio)

    # Calculate center position
    y_start = (h - mask_h) // 2
    x_start = (w - mask_w) // 2

    mask[:, y_start:y_start + mask_h, x_start:x_start + mask_w] = 1.0
    return mask


def generate_random_rect_mask(
    image_size: Tuple[int, int],
    num_masks: int = 1,
    min_size_ratio: float = 0.1,
    max_size_ratio: float = 0.4,
    seed: Optional[int] = None,
) -> torch.Tensor:
    """Generate random rectangular masks at arbitrary positions.

    Creates one or more randomly placed rectangular holes in the mask.
    This provides more diverse training data than center masks.

    Args:
        image_size: (height, width) of the image.
        num_masks: Number of rectangular holes to generate.
        min_size_ratio: Minimum size of each hole as a ratio of image size.
        max_size_ratio: Maximum size of each hole as a ratio of image size.
        seed: Random seed for reproducibility.

    Returns:
        Binary mask tensor of shape (1, H, W).

    Example:
        >>> mask = generate_random_rect_mask((128, 128), num_masks=3)
        >>> mask.shape
        torch.Size([1, 128, 128])
    """
    if seed is not None:
        np.random.seed(seed)

    h, w = image_size
    mask = torch.zeros(1, h, w)

    for _ in range(num_masks):
        # Random size
        mask_h = np.random.randint(int(h * min_size_ratio), int(h * max_size_ratio) + 1)
        mask_w = np.random.randint(int(w * min_size_ratio), int(w * max_size_ratio) + 1)

        # Random position
        y_start = np.random.randint(0, h - mask_h + 1)
        x_start = np.random.randint(0, w - mask_w + 1)

        mask[:, y_start:y_start + mask_h, x_start:x_start + mask_w] = 1.0

    return mask


def generate_irregular_mask(
    image_size: Tuple[int, int],
    num_strokes: int = 10,
    max_brush_width: int = 20,
    max_vertex: int = 12,
    seed: Optional[int] = None,
) -> torch.Tensor:
    """Generate an irregular free-form mask using random strokes.

    Simulates real-world damage patterns by drawing random curved strokes.
    Each stroke is defined by a series of control points connected by lines
    with varying brush widths.

    This method is inspired by the "Irregular Mask Dataset" used in
    "Image Inpainting for Irregular Holes Using Partial Convolutions"
    (Liu et al., 2018).

    Args:
        image_size: (height, width) of the image.
        num_strokes: Number of random strokes to draw.
        max_brush_width: Maximum width of the brush stroke in pixels.
        max_vertex: Maximum number of vertices (control points) per stroke.
        seed: Random seed for reproducibility.

    Returns:
        Binary mask tensor of shape (1, H, W).

    Example:
        >>> mask = generate_irregular_mask((128, 128), num_strokes=8)
        >>> mask.shape
        torch.Size([1, 128, 128])
    """
    if seed is not None:
        np.random.seed(seed)

    h, w = image_size
    mask = np.zeros((h, w), dtype=np.float32)

    for _ in range(num_strokes):
        # Number of vertices for this stroke
        num_vertices = np.random.randint(3, max_vertex + 1)

        # Start position
        start_x = np.random.randint(0, w)
        start_y = np.random.randint(0, h)

        # Brush width for this stroke
        brush_width = np.random.randint(2, max_brush_width + 1)

        # Generate vertices with random offsets
        vertices_x = [start_x]
        vertices_y = [start_y]

        for _ in range(num_vertices - 1):
            dx = np.random.randint(-30, 31)
            dy = np.random.randint(-30, 31)
            new_x = np.clip(vertices_x[-1] + dx, 0, w - 1)
            new_y = np.clip(vertices_y[-1] + dy, 0, h - 1)
            vertices_x.append(new_x)
            vertices_y.append(new_y)

        # Draw the stroke using Bresenham-like line segments
        for i in range(len(vertices_x) - 1):
            _draw_line(
                mask,
                vertices_x[i], vertices_y[i],
                vertices_x[i + 1], vertices_y[i + 1],
                brush_width,
            )

    return torch.from_numpy(mask).unsqueeze(0)


def _draw_line(
    mask: np.ndarray,
    x0: int, y0: int,
    x1: int, y1: int,
    width: int,
) -> None:
    """Draw a thick line on the mask array using Bresenham's algorithm.

    Args:
        mask: 2D numpy array to draw on (modified in place).
        x0, y0: Start point coordinates.
        x1, y1: End point coordinates.
        width: Width of the line in pixels.
    """
    h, w = mask.shape
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        # Draw a filled circle at the current point
        y_lo = max(0, y0 - width // 2)
        y_hi = min(h, y0 + width // 2 + 1)
        x_lo = max(0, x0 - width // 2)
        x_hi = min(w, x0 + width // 2 + 1)
        mask[y_lo:y_hi, x_lo:x_hi] = 1.0

        if x0 == x1 and y0 == y1:
            break

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def apply_mask(
    image: torch.Tensor,
    mask: torch.Tensor,
    mask_value: float = 0.0,
) -> torch.Tensor:
    """Apply a mask to an image, filling masked regions with a constant value.

    Args:
        image: Input image tensor of shape (C, H, W) or (B, C, H, W).
        mask: Binary mask tensor of shape (1, H, W) or (B, 1, H, W).
            1 = masked region, 0 = known region.
        mask_value: Value to fill in the masked regions.

    Returns:
        Masked image tensor with the same shape as input.

    Example:
        >>> image = torch.randn(3, 128, 128)
        >>> mask = generate_center_mask((128, 128))
        >>> masked = apply_mask(image, mask)
    """
    # Ensure mask is broadcastable
    if image.dim() == 3 and mask.dim() == 3:
        # Both (C, H, W) and (1, H, W) - already broadcastable
        pass
    elif image.dim() == 4 and mask.dim() == 3:
        # (B, C, H, W) and (1, H, W) -> (B, 1, H, W)
        mask = mask.unsqueeze(0).expand(image.size(0), -1, -1, -1)
    elif image.dim() == 4 and mask.dim() == 4:
        pass  # Already batched
    else:
        raise ValueError(f"Unsupported dimensions: image {image.dim()}D, mask {mask.dim()}D")

    masked_image = image * (1 - mask) + mask_value * mask
    return masked_image
