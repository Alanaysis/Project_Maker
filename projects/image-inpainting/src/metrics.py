"""
Image Quality Metrics for Inpainting Evaluation.

This module implements standard image quality assessment metrics used
to evaluate inpainting results:

1. **PSNR (Peak Signal-to-Noise Ratio)**:
   - Measures the ratio between the maximum signal and noise
   - Higher is better (typically 20-40 dB for good results)
   - Formula: PSNR = 10 * log10(MAX^2 / MSE)
   - Limitation: Doesn't correlate well with perceived quality

2. **SSIM (Structural Similarity Index Measure)**:
   - Measures structural similarity between two images
   - Range: [-1, 1], higher is better (1 = identical)
   - Considers luminance, contrast, and structure
   - Better correlation with human perception than PSNR

3. **L1 Error**:
   - Mean absolute error between inpainted and ground truth
   - Lower is better
   - Simple and interpretable

Key Concepts:
- PSNR is easy to compute but doesn't capture perceptual quality well
- SSIM is more perceptually meaningful but computationally more expensive
- For inpainting, metrics should be computed only in the masked region
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Optional


def compute_psnr(
    predicted: torch.Tensor,
    target: torch.Tensor,
    mask: Optional[torch.Tensor] = None,
    max_val: float = 1.0,
) -> float:
    """Compute Peak Signal-to-Noise Ratio (PSNR).

    PSNR = 10 * log10(MAX^2 / MSE)

    Args:
        predicted: Predicted image (C, H, W) or (B, C, H, W), range [0, max_val].
        target: Ground truth image, same shape as predicted.
        mask: Optional binary mask (1, H, W) or (B, 1, H, W).
            If provided, PSNR is computed only in masked regions.
        max_val: Maximum pixel value (1.0 for normalized images, 255 for uint8).

    Returns:
        PSNR value in decibels (dB). Higher is better.
        Returns float('inf') if MSE is 0 (identical images).

    Example:
        >>> pred = torch.rand(3, 128, 128)
        >>> target = torch.rand(3, 128, 128)
        >>> psnr = compute_psnr(pred, target)
    """
    # Ensure tensors are on the same device
    predicted = predicted.to(target.device)

    # Compute MSE
    mse = _compute_mse(predicted, target, mask)

    if mse == 0:
        return float("inf")

    psnr = 10.0 * np.log10(max_val ** 2 / mse)
    return float(psnr)


def compute_ssim(
    predicted: torch.Tensor,
    target: torch.Tensor,
    mask: Optional[torch.Tensor] = None,
    window_size: int = 11,
    k1: float = 0.01,
    k2: float = 0.03,
) -> float:
    """Compute Structural Similarity Index Measure (SSIM).

    SSIM considers three components:
    1. Luminance: How similar the mean intensities are
    2. Contrast: How similar the variances are
    3. Structure: How similar the normalized signals are

    SSIM(x, y) = (2*mu_x*mu_y + C1)(2*sigma_xy + C2) /
                 ((mu_x^2 + mu_y^2 + C1)(sigma_x^2 + sigma_y^2 + C2))

    Args:
        predicted: Predicted image (C, H, W) or (B, C, H, W).
        target: Ground truth image, same shape.
        mask: Optional binary mask. If provided, SSIM is computed only in
            masked regions by zeroing out non-masked regions.
        window_size: Size of the Gaussian window (must be odd).
        k1: Stability constant for luminance (default: 0.01).
        k2: Stability constant for contrast (default: 0.03).

    Returns:
        SSIM value in range [-1, 1]. Higher is better (1 = identical).

    Note:
        This is a simplified SSIM implementation using uniform windows.
        For production use, consider using skimage.metrics.structural_similarity
        which uses proper Gaussian weighting.
    """
    predicted = predicted.to(target.device)

    # Add batch dimension if needed
    if predicted.dim() == 3:
        predicted = predicted.unsqueeze(0)
        target = target.unsqueeze(0)

    if mask is not None:
        # Apply mask: zero out non-masked regions
        if mask.dim() == 3:
            mask = mask.unsqueeze(0)
        predicted = predicted * mask
        target = target * mask

    C1 = (k1 * 1.0) ** 2  # 1.0 = dynamic range for normalized images
    C2 = (k2 * 1.0) ** 2

    # Use a simple uniform window for convolution
    channel = predicted.size(1)
    window = _create_uniform_window(window_size, channel).to(predicted.device)

    # Compute means
    mu_x = F.conv2d(predicted, window, padding=window_size // 2, groups=channel)
    mu_y = F.conv2d(target, window, padding=window_size // 2, groups=channel)

    # Compute variances and covariance
    mu_x_sq = mu_x ** 2
    mu_y_sq = mu_y ** 2
    mu_xy = mu_x * mu_y

    sigma_x_sq = F.conv2d(predicted ** 2, window, padding=window_size // 2, groups=channel) - mu_x_sq
    sigma_y_sq = F.conv2d(target ** 2, window, padding=window_size // 2, groups=channel) - mu_y_sq
    sigma_xy = F.conv2d(predicted * target, window, padding=window_size // 2, groups=channel) - mu_xy

    # SSIM formula
    numerator = (2 * mu_xy + C1) * (2 * sigma_xy + C2)
    denominator = (mu_x_sq + mu_y_sq + C1) * (sigma_x_sq + sigma_y_sq + C2)

    ssim_map = numerator / (denominator + 1e-8)

    return float(ssim_map.mean())


def compute_l1_error(
    predicted: torch.Tensor,
    target: torch.Tensor,
    mask: Optional[torch.Tensor] = None,
) -> float:
    """Compute mean L1 (absolute) error.

    Args:
        predicted: Predicted image (C, H, W) or (B, C, H, W).
        target: Ground truth image, same shape.
        mask: Optional binary mask. If provided, error is computed only in
            masked regions.

    Returns:
        Mean L1 error (lower is better).

    Example:
        >>> pred = torch.rand(3, 128, 128)
        >>> target = torch.rand(3, 128, 128)
        >>> l1 = compute_l1_error(pred, target)
    """
    predicted = predicted.to(target.device)
    l1 = torch.abs(predicted - target)

    if mask is not None:
        if mask.dim() == 3 and l1.dim() == 3:
            mask_expanded = mask.expand_as(l1)
        elif mask.dim() == 3 and l1.dim() == 4:
            mask_expanded = mask.unsqueeze(0).expand_as(l1)
        else:
            mask_expanded = mask.expand_as(l1)

        l1 = l1 * mask_expanded
        num_masked = mask_expanded.sum()
        if num_masked > 0:
            return float(l1.sum() / num_masked)
        return 0.0

    return float(l1.mean())


def _compute_mse(
    predicted: torch.Tensor,
    target: torch.Tensor,
    mask: Optional[torch.Tensor] = None,
) -> float:
    """Compute Mean Squared Error, optionally in masked region."""
    mse = (predicted - target) ** 2

    if mask is not None:
        # Ensure mask is broadcastable with mse
        if mse.dim() == 4 and mask.dim() == 3:
            # mse is (B, C, H, W), mask is (1, H, W) -> add batch dim
            mask = mask.unsqueeze(0)
        # For 3D mse (C, H, W) with 3D mask (1, H, W), already broadcastable

        mse = mse * mask
        num_masked = mask.sum()
        if num_masked > 0:
            return float(mse.sum() / num_masked)
        return 0.0

    return float(mse.mean())


def _create_uniform_window(window_size: int, channels: int) -> torch.Tensor:
    """Create a uniform window for SSIM computation.

    Args:
        window_size: Size of the window (must be odd).
        channels: Number of channels.

    Returns:
        Window tensor of shape (channels, 1, window_size, window_size).
    """
    window = torch.ones(1, 1, window_size, window_size) / (window_size ** 2)
    return window.expand(channels, 1, -1, -1).contiguous()
