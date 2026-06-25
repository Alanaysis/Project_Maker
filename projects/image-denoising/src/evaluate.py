"""Evaluation metrics for image denoising.

Implements standard image quality metrics:
- PSNR (Peak Signal-to-Noise Ratio)
- SSIM (Structural Similarity Index)
- MSE (Mean Squared Error)

These metrics are used to evaluate denoising performance.
"""

from typing import Optional, Tuple, Dict, List
import numpy as np
import torch
import torch.nn as nn
from scipy.ndimage import uniform_filter


def calculate_mse(image1: np.ndarray, image2: np.ndarray) -> float:
    """Calculate Mean Squared Error between two images.

    MSE = (1/N) * sum((image1 - image2)^2)

    Args:
        image1: First image [C, H, W] or [H, W]
        image2: Second image [C, H, W] or [H, W]

    Returns:
        MSE value
    """
    return float(np.mean((image1 - image2) ** 2))


def calculate_psnr(
    image1: np.ndarray,
    image2: np.ndarray,
    data_range: float = 1.0,
) -> float:
    """Calculate Peak Signal-to-Noise Ratio.

    PSNR = 10 * log10(MAX^2 / MSE)

    Higher PSNR indicates better quality (less distortion).

    Args:
        image1: Reference image [C, H, W] or [H, W]
        image2: Test image [C, H, W] or [H, W]
        data_range: Maximum pixel value (1.0 for [0,1], 255 for [0,255])

    Returns:
        PSNR value in dB
    """
    mse = calculate_mse(image1, image2)
    if mse == 0:
        return float('inf')
    return float(10 * np.log10(data_range ** 2 / mse))


def calculate_ssim(
    image1: np.ndarray,
    image2: np.ndarray,
    data_range: float = 1.0,
    window_size: int = 7,
    k1: float = 0.01,
    k2: float = 0.03,
) -> float:
    """Calculate Structural Similarity Index.

    SSIM measures the similarity between two images based on:
    - Luminance comparison
    - Contrast comparison
    - Structure comparison

    SSIM values range from -1 to 1, where 1 indicates identical images.

    Args:
        image1: Reference image [C, H, W] or [H, W]
        image2: Test image [C, H, W] or [H, W]
        data_range: Dynamic range of the images
        window_size: Size of the sliding window
        k1: Algorithm constant (default: 0.01)
        k2: Algorithm constant (default: 0.03)

    Returns:
        SSIM value
    """
    # Stability constants
    c1 = (k1 * data_range) ** 2
    c2 = (k2 * data_range) ** 2

    # Ensure images are numpy arrays
    if isinstance(image1, torch.Tensor):
        image1 = image1.numpy()
    if isinstance(image2, torch.Tensor):
        image2 = image2.numpy()

    # Handle multi-channel images
    if image1.ndim == 3:
        # Average SSIM over channels
        ssim_values = []
        for c in range(image1.shape[0]):
            ssim_c = _calculate_ssim_single(
                image1[c], image2[c], c1, c2, window_size
            )
            ssim_values.append(ssim_c)
        return float(np.mean(ssim_values))
    else:
        return float(_calculate_ssim_single(image1, image2, c1, c2, window_size))


def _calculate_ssim_single(
    image1: np.ndarray,
    image2: np.ndarray,
    c1: float,
    c2: float,
    window_size: int,
) -> float:
    """Calculate SSIM for a single channel.

    Args:
        image1: Single channel image [H, W]
        image2: Single channel image [H, W]
        c1, c2: Stability constants
        window_size: Sliding window size

    Returns:
        SSIM value
    """
    # Calculate means
    mu1 = uniform_filter(image1, size=window_size)
    mu2 = uniform_filter(image2, size=window_size)

    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2

    # Calculate variances and covariance
    sigma1_sq = uniform_filter(image1 ** 2, size=window_size) - mu1_sq
    sigma2_sq = uniform_filter(image2 ** 2, size=window_size) - mu2_sq
    sigma12 = uniform_filter(image1 * image2, size=window_size) - mu1_mu2

    # SSIM formula
    numerator = (2 * mu1_mu2 + c1) * (2 * sigma12 + c2)
    denominator = (mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2)

    ssim_map = numerator / denominator

    # Calculate mean SSIM
    # Crop borders where the filter is not fully valid
    pad = window_size // 2
    if pad > 0:
        ssim_map = ssim_map[pad:-pad, pad:-pad]

    return float(np.mean(ssim_map))


def calculate_metrics(
    clean: np.ndarray,
    denoised: np.ndarray,
    data_range: float = 1.0,
) -> Dict[str, float]:
    """Calculate all evaluation metrics.

    Args:
        clean: Clean reference image
        denoised: Denoised test image
        data_range: Maximum pixel value

    Returns:
        Dictionary of metric values
    """
    return {
        'mse': calculate_mse(clean, denoised),
        'psnr': calculate_psnr(clean, denoised, data_range),
        'ssim': calculate_ssim(clean, denoised, data_range),
    }


@torch.no_grad()
def evaluate_model(
    model: nn.Module,
    test_images: List[np.ndarray],
    noise_levels: List[float] = [15, 25, 50],
    device: str = "cpu",
) -> Dict[str, Dict[str, float]]:
    """Evaluate model on test images with different noise levels.

    Args:
        model: Trained denoising model
        test_images: List of clean test images [C, H, W]
        noise_levels: List of noise standard deviations to test
        device: Device to use

    Returns:
        Dictionary of metrics for each noise level
    """
    from .noise import add_gaussian_noise

    model.eval()
    model = model.to(device)

    results = {}

    for sigma in noise_levels:
        psnr_values = []
        ssim_values = []
        mse_values = []

        for clean in test_images:
            # Add noise
            noisy, noise = add_gaussian_noise(clean, sigma=sigma)

            # Convert to tensor
            noisy_tensor = torch.from_numpy(noisy).float().unsqueeze(0).to(device)

            # Denoise
            noise_pred = model(noisy_tensor)
            denoised = noisy_tensor - noise_pred

            # Convert back to numpy
            denoised_np = denoised.cpu().squeeze().numpy()

            # Calculate metrics
            metrics = calculate_metrics(clean, denoised_np)
            psnr_values.append(metrics['psnr'])
            ssim_values.append(metrics['ssim'])
            mse_values.append(metrics['mse'])

        results[f'sigma_{sigma}'] = {
            'psnr': float(np.mean(psnr_values)),
            'psnr_std': float(np.std(psnr_values)),
            'ssim': float(np.mean(ssim_values)),
            'ssim_std': float(np.std(ssim_values)),
            'mse': float(np.mean(mse_values)),
            'mse_std': float(np.std(mse_values)),
        }

    return results


def print_evaluation_results(results: Dict[str, Dict[str, float]]):
    """Print evaluation results in a formatted table.

    Args:
        results: Results dictionary from evaluate_model
    """
    print("\n" + "=" * 60)
    print("Evaluation Results")
    print("=" * 60)
    print(f"{'Noise Level':<15} {'PSNR (dB)':<15} {'SSIM':<15} {'MSE':<15}")
    print("-" * 60)

    for noise_key, metrics in results.items():
        sigma = noise_key.replace('sigma_', '')
        print(f"σ = {sigma:<10} {metrics['psnr']:.2f} ± {metrics['psnr_std']:.2f}    "
              f"{metrics['ssim']:.4f} ± {metrics['ssim_std']:.4f}    "
              f"{metrics['mse']:.6f} ± {metrics['mse_std']:.6f}")

    print("=" * 60)


class MetricTracker:
    """Track metrics during training.

    Args:
        window_size: Size of the moving average window
    """

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.history = {}
        self._windows = {}

    def update(self, metrics: Dict[str, float]):
        """Update metrics with new values.

        Args:
            metrics: Dictionary of metric values
        """
        for name, value in metrics.items():
            if name not in self.history:
                self.history[name] = []
                self._windows[name] = []

            self.history[name].append(value)
            self._windows[name].append(value)

            # Keep only recent values in window
            if len(self._windows[name]) > self.window_size:
                self._windows[name].pop(0)

    def get_current(self, name: str) -> float:
        """Get the most recent value of a metric."""
        if name not in self.history or len(self.history[name]) == 0:
            return 0.0
        return self.history[name][-1]

    def get_average(self, name: str) -> float:
        """Get the moving average of a metric."""
        if name not in self._windows or len(self._windows[name]) == 0:
            return 0.0
        return float(np.mean(self._windows[name]))

    def get_summary(self) -> Dict[str, float]:
        """Get summary of all tracked metrics."""
        summary = {}
        for name in self.history:
            if len(self.history[name]) > 0:
                summary[f'{name}_current'] = self.get_current(name)
                summary[f'{name}_avg'] = self.get_average(name)
        return summary


if __name__ == "__main__":
    # Test metrics
    print("Testing Evaluation Metrics")
    print("=" * 40)

    # Create test images
    np.random.seed(42)
    clean = np.random.rand(1, 64, 64).astype(np.float32)

    # Add known noise
    noise = np.random.randn(*clean.shape).astype(np.float32) * 0.1
    noisy = clean + noise
    noisy = np.clip(noisy, 0, 1)

    # Test individual metrics
    print(f"MSE: {calculate_mse(clean, noisy):.6f}")
    print(f"PSNR: {calculate_psnr(clean, noisy):.2f} dB")
    print(f"SSIM: {calculate_ssim(clean, noisy):.4f}")

    # Test with perfect reconstruction
    print(f"\nPerfect reconstruction:")
    print(f"MSE: {calculate_mse(clean, clean):.6f}")
    print(f"PSNR: {calculate_psnr(clean, clean):.2f} dB")
    print(f"SSIM: {calculate_ssim(clean, clean):.4f}")

    # Test MetricTracker
    print("\nMetricTracker test:")
    tracker = MetricTracker(window_size=5)
    for i in range(10):
        tracker.update({'loss': 1.0 / (i + 1), 'psnr': 20 + i})

    summary = tracker.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value:.4f}")
