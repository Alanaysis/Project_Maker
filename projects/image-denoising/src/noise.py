"""Noise utilities for image denoising.

Implements various noise models commonly used in image denoising:
- Gaussian noise
- Salt & pepper noise
- Poisson noise
- Speckle noise

These noise models are used for:
1. Training data augmentation (adding noise to clean images)
2. Noise level estimation
3. Benchmarking denoising algorithms
"""

from typing import Optional, Tuple, Union
import numpy as np
import torch


def add_gaussian_noise(
    image: Union[np.ndarray, torch.Tensor],
    sigma: float = 25.0,
    clip: bool = True,
) -> Tuple[Union[np.ndarray, torch.Tensor], Union[np.ndarray, torch.Tensor]]:
    """Add Gaussian noise to image.

    Gaussian noise model: y = x + n, where n ~ N(0, sigma^2)

    Args:
        image: Clean input image (values in [0, 1] or [0, 255])
        sigma: Noise standard deviation (in [0, 255] scale)
        clip: Whether to clip output to valid range

    Returns:
        Tuple of (noisy_image, noise)
    """
    if isinstance(image, torch.Tensor):
        noise = torch.randn_like(image) * (sigma / 255.0)
        noisy = image + noise
        if clip:
            noisy = torch.clamp(noisy, 0.0, 1.0)
        return noisy, noise
    else:
        noise = np.random.randn(*image.shape).astype(image.dtype) * (sigma / 255.0)
        noisy = image + noise
        if clip:
            noisy = np.clip(noisy, 0.0, 1.0)
        return noisy, noise


def add_salt_pepper_noise(
    image: Union[np.ndarray, torch.Tensor],
    amount: float = 0.05,
    salt_vs_pepper: float = 0.5,
) -> Tuple[Union[np.ndarray, torch.Tensor], Union[np.ndarray, torch.Tensor]]:
    """Add salt and pepper noise to image.

    Salt & pepper noise randomly sets pixels to 0 (pepper) or 1 (salt).

    Args:
        image: Clean input image (values in [0, 1])
        amount: Proportion of pixels to corrupt
        salt_vs_pepper: Ratio of salt vs pepper noise

    Returns:
        Tuple of (noisy_image, noise_mask)
    """
    if isinstance(image, torch.Tensor):
        noisy = image.clone()
        # Create noise mask
        noise_mask = torch.zeros_like(image)

        # Salt noise (set to 1)
        salt_mask = torch.rand_like(image) < (amount * salt_vs_pepper)
        noisy[salt_mask] = 1.0
        noise_mask[salt_mask] = 1.0

        # Pepper noise (set to 0)
        pepper_mask = torch.rand_like(image) < (amount * (1 - salt_vs_pepper))
        noisy[pepper_mask] = 0.0
        noise_mask[pepper_mask] = -1.0

        return noisy, noise_mask
    else:
        noisy = image.copy()
        noise_mask = np.zeros_like(image)

        # Salt noise
        salt_mask = np.random.random(image.shape) < (amount * salt_vs_pepper)
        noisy[salt_mask] = 1.0
        noise_mask[salt_mask] = 1.0

        # Pepper noise
        pepper_mask = np.random.random(image.shape) < (amount * (1 - salt_vs_pepper))
        noisy[pepper_mask] = 0.0
        noise_mask[pepper_mask] = -1.0

        return noisy, noise_mask


def add_poisson_noise(
    image: Union[np.ndarray, torch.Tensor],
    peak: float = 1.0,
) -> Tuple[Union[np.ndarray, torch.Tensor], Union[np.ndarray, torch.Tensor]]:
    """Add Poisson noise to image.

    Poisson noise is signal-dependent noise, common in low-light imaging.

    Args:
        image: Clean input image (values in [0, 1])
        peak: Peak value for Poisson scaling

    Returns:
        Tuple of (noisy_image, estimated_noise)
    """
    if isinstance(image, torch.Tensor):
        # Scale image to Poisson range
        scaled = image * peak
        # Generate Poisson samples
        noisy = torch.poisson(scaled) / peak
        noise = noisy - image
        return noisy, noise
    else:
        scaled = image * peak
        noisy = np.random.poisson(scaled).astype(image.dtype) / peak
        noise = noisy - image
        return noisy, noise


def add_speckle_noise(
    image: Union[np.ndarray, torch.Tensor],
    variance: float = 0.05,
) -> Tuple[Union[np.ndarray, torch.Tensor], Union[np.ndarray, torch.Tensor]]:
    """Add speckle (multiplicative) noise to image.

    Speckle noise model: y = x + x * n, where n ~ N(0, variance)

    Args:
        image: Clean input image (values in [0, 1])
        variance: Noise variance

    Returns:
        Tuple of (noisy_image, noise)
    """
    if isinstance(image, torch.Tensor):
        noise = torch.randn_like(image) * variance
        noisy = image + image * noise
        noisy = torch.clamp(noisy, 0.0, 1.0)
        return noisy, noise
    else:
        noise = np.random.randn(*image.shape).astype(image.dtype) * variance
        noisy = image + image * noise
        noisy = np.clip(noisy, 0.0, 1.0)
        return noisy, noise


class NoiseGenerator:
    """Configurable noise generator for training data augmentation.

    Supports multiple noise types and random noise level selection.

    Args:
        noise_type: Type of noise ("gaussian", "salt_pepper", "poisson", "speckle")
        sigma_range: Range of noise levels for Gaussian noise
        fixed_sigma: Fixed noise level (overrides sigma_range if set)
    """

    NOISE_FUNCTIONS = {
        "gaussian": add_gaussian_noise,
        "salt_pepper": add_salt_pepper_noise,
        "poisson": add_poisson_noise,
        "speckle": add_speckle_noise,
    }

    def __init__(
        self,
        noise_type: str = "gaussian",
        sigma_range: Tuple[float, float] = (0.0, 50.0),
        fixed_sigma: Optional[float] = None,
    ):
        if noise_type not in self.NOISE_FUNCTIONS:
            raise ValueError(f"Unknown noise type: {noise_type}. Available: {list(self.NOISE_FUNCTIONS.keys())}")

        self.noise_type = noise_type
        self.sigma_range = sigma_range
        self.fixed_sigma = fixed_sigma
        self._noise_fn = self.NOISE_FUNCTIONS[noise_type]

    def __call__(
        self,
        image: Union[np.ndarray, torch.Tensor],
        sigma: Optional[float] = None,
    ) -> Tuple[Union[np.ndarray, torch.Tensor], Union[np.ndarray, torch.Tensor]]:
        """Apply noise to image.

        Args:
            image: Clean input image
            sigma: Noise level (random from range if not specified)

        Returns:
            Tuple of (noisy_image, noise)
        """
        if sigma is None:
            sigma = self.fixed_sigma if self.fixed_sigma is not None else \
                np.random.uniform(*self.sigma_range)

        if self.noise_type == "gaussian":
            return self._noise_fn(image, sigma=sigma)
        elif self.noise_type == "salt_pepper":
            return self._noise_fn(image, amount=sigma / 100.0)
        elif self.noise_type == "poisson":
            return self._noise_fn(image, peak=sigma)
        elif self.noise_type == "speckle":
            return self._noise_fn(image, variance=sigma / 100.0)
        else:
            return self._noise_fn(image)

    def get_random_sigma(self) -> float:
        """Get a random noise level from the configured range."""
        if self.fixed_sigma is not None:
            return self.fixed_sigma
        return np.random.uniform(*self.sigma_range)


def estimate_noise_sigma(image: Union[np.ndarray, torch.Tensor]) -> float:
    """Estimate noise standard deviation from image using Median Absolute Deviation (MAD).

    Based on the robust estimator: sigma = MAD / 0.6745

    This works well for Gaussian noise estimation.

    Args:
        image: Input image (assumed to be noisy)

    Returns:
        Estimated noise standard deviation
    """
    if isinstance(image, torch.Tensor):
        image = image.numpy()

    # Use Laplacian-based method for noise estimation
    # High-pass filter to isolate noise
    from scipy.ndimage import laplace
    high_freq = laplace(image.astype(np.float64))

    # MAD estimator
    mad = np.median(np.abs(high_freq - np.median(high_freq)))
    sigma = mad / 0.6745

    return float(sigma)


if __name__ == "__main__":
    # Demo noise addition
    print("Noise Utilities Demo")
    print("=" * 40)

    # Create a test image (gradient)
    x = np.linspace(0, 1, 256).reshape(1, 256)
    image = np.tile(x, (256, 1))
    image = image[np.newaxis, :]  # [1, H, W]

    print(f"Original image shape: {image.shape}")
    print(f"Original image range: [{image.min():.3f}, {image.max():.3f}]")

    # Test each noise type
    for noise_name, noise_fn in [
        ("Gaussian (sigma=25)", lambda img: add_gaussian_noise(img, sigma=25)),
        ("Salt & Pepper (5%)", lambda img: add_salt_pepper_noise(img, amount=0.05)),
        ("Speckle (var=0.05)", lambda img: add_speckle_noise(img, variance=0.05)),
    ]:
        noisy, noise = noise_fn(image)
        print(f"\n{noise_name}:")
        print(f"  Noisy range: [{noisy.min():.3f}, {noisy.max():.3f}]")
        print(f"  Noise std: {noise.std():.4f}")

    # Test NoiseGenerator
    print("\nNoiseGenerator with random levels:")
    gen = NoiseGenerator(noise_type="gaussian", sigma_range=(10, 50))
    for i in range(5):
        sigma = gen.get_random_sigma()
        print(f"  Random sigma: {sigma:.1f}")
