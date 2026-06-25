"""Dataset utilities for image denoising training.

Provides:
- DenoisingDataset: Pairs clean images with noisy versions
- Synthetic data generation for training without paired data
- Data augmentation specific to denoising tasks
"""

from typing import Optional, Tuple, List, Callable
import os
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image

from .noise import add_gaussian_noise, NoiseGenerator


class DenoisingDataset(Dataset):
    """Dataset for training image denoising models.

    Supports two modes:
    1. Paired mode: Uses clean images and adds noise on-the-fly
    2. Pre-paired mode: Loads pre-existing clean/noisy image pairs

    Args:
        clean_images: List of clean images or path to directory
        noise_generator: NoiseGenerator instance for adding noise
        patch_size: Size of random patches to extract (None for full image)
        augment: Whether to apply random augmentations
        transform: Optional additional transforms
    """

    def __init__(
        self,
        clean_images: Optional[List[np.ndarray]] = None,
        image_dir: Optional[str] = None,
        noise_generator: Optional[NoiseGenerator] = None,
        patch_size: Optional[int] = 128,
        augment: bool = True,
        transform: Optional[Callable] = None,
    ):
        super().__init__()

        self.patch_size = patch_size
        self.augment = augment
        self.transform = transform

        # Set up noise generator
        if noise_generator is None:
            self.noise_gen = NoiseGenerator(noise_type="gaussian", sigma_range=(5, 50))
        else:
            self.noise_gen = noise_generator

        # Load or store images
        if clean_images is not None:
            self.clean_images = clean_images
        elif image_dir is not None:
            self.clean_images = self._load_images(image_dir)
        else:
            # Generate synthetic training data
            self.clean_images = self._generate_synthetic_images(100)

    def _load_images(self, image_dir: str) -> List[np.ndarray]:
        """Load images from directory.

        Args:
            image_dir: Path to directory containing images

        Returns:
            List of images as numpy arrays [C, H, W] in [0, 1] range
        """
        images = []
        valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}

        if not os.path.exists(image_dir):
            print(f"Warning: Directory {image_dir} not found, using synthetic data")
            return self._generate_synthetic_images(100)

        for filename in sorted(os.listdir(image_dir)):
            ext = os.path.splitext(filename)[1].lower()
            if ext in valid_extensions:
                filepath = os.path.join(image_dir, filename)
                img = Image.open(filepath).convert('L')  # Grayscale
                img_array = np.array(img, dtype=np.float32) / 255.0
                img_array = img_array[np.newaxis, :]  # [1, H, W]
                images.append(img_array)

        if len(images) == 0:
            print(f"Warning: No images found in {image_dir}, using synthetic data")
            return self._generate_synthetic_images(100)

        return images

    def _generate_synthetic_images(self, num_images: int) -> List[np.ndarray]:
        """Generate synthetic images for training.

        Creates images with various patterns:
        - Gradients
        - Checkerboards
        - Circles
        - Random textures

        Args:
            num_images: Number of images to generate

        Returns:
            List of synthetic images
        """
        images = []
        size = 256

        for i in range(num_images):
            pattern_type = i % 4

            if pattern_type == 0:
                # Gradient
                x = np.linspace(0, 1, size).reshape(1, size)
                y = np.linspace(0, 1, size).reshape(size, 1)
                img = (x + y) / 2

            elif pattern_type == 1:
                # Checkerboard
                x, y = np.meshgrid(np.arange(size), np.arange(size))
                img = ((x // 32 + y // 32) % 2).astype(np.float32)

            elif pattern_type == 2:
                # Circles
                x, y = np.meshgrid(
                    np.linspace(-1, 1, size),
                    np.linspace(-1, 1, size)
                )
                r = np.sqrt(x**2 + y**2)
                img = (np.sin(r * 10) + 1) / 2

            else:
                # Random texture (smooth random field)
                from scipy.ndimage import gaussian_filter
                img = np.random.rand(size, size).astype(np.float32)
                img = gaussian_filter(img, sigma=5)

            # Normalize to [0, 1]
            img = (img - img.min()) / (img.max() - img.min() + 1e-8)
            images.append(img[np.newaxis, :].astype(np.float32))

        return images

    def _extract_patch(self, image: np.ndarray) -> np.ndarray:
        """Extract random patch from image.

        Args:
            image: Input image [C, H, W]

        Returns:
            Random patch [C, patch_size, patch_size]
        """
        if self.patch_size is None:
            return image

        _, h, w = image.shape
        if h < self.patch_size or w < self.patch_size:
            # Pad image if smaller than patch size
            pad_h = max(0, self.patch_size - h)
            pad_w = max(0, self.patch_size - w)
            image = np.pad(image, ((0, 0), (0, pad_h), (0, pad_w)), mode='reflect')
            _, h, w = image.shape

        # Random crop
        top = np.random.randint(0, h - self.patch_size + 1)
        left = np.random.randint(0, w - self.patch_size + 1)

        return image[:, top:top + self.patch_size, left:left + self.patch_size]

    def _augment(self, clean: np.ndarray, noisy: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Apply random augmentations to image pair.

        Args:
            clean: Clean image [C, H, W]
            noisy: Noisy image [C, H, W]

        Returns:
            Tuple of augmented (clean, noisy)
        """
        # Random horizontal flip
        if np.random.rand() > 0.5:
            clean = clean[:, :, ::-1].copy()
            noisy = noisy[:, :, ::-1].copy()

        # Random vertical flip
        if np.random.rand() > 0.5:
            clean = clean[:, ::-1, :].copy()
            noisy = noisy[:, ::-1, :].copy()

        # Random 90-degree rotation
        k = np.random.randint(0, 4)
        if k > 0:
            clean = np.rot90(clean, k, axes=(1, 2)).copy()
            noisy = np.rot90(noisy, k, axes=(1, 2)).copy()

        return clean, noisy

    def __len__(self) -> int:
        return len(self.clean_images)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Get a training sample.

        Args:
            idx: Index of sample

        Returns:
            Tuple of (noisy_image, clean_image, noise)
        """
        clean = self.clean_images[idx].copy()

        # Extract patch
        clean = self._extract_patch(clean)

        # Apply augmentations
        if self.augment:
            # We'll apply augmentation after adding noise
            pass

        # Add noise
        sigma = self.noise_gen.get_random_sigma()
        noisy, noise = self.noise_gen(clean, sigma=sigma)

        # Apply augmentations to both clean and noisy
        if self.augment:
            clean, noisy = self._augment(clean, noisy)
            noise = noisy - clean  # Recalculate noise after augmentation

        # Apply additional transforms
        if self.transform:
            clean = self.transform(clean)
            noisy = self.transform(noisy)

        # Convert to tensors
        clean_tensor = torch.from_numpy(clean).float()
        noisy_tensor = torch.from_numpy(noisy).float()
        noise_tensor = torch.from_numpy(noise).float()

        return noisy_tensor, clean_tensor, noise_tensor


class DenoisingValidationDataset(Dataset):
    """Validation dataset with fixed noise levels for consistent evaluation.

    Args:
        clean_images: List of clean images
        noise_levels: List of noise standard deviations to test
    """

    def __init__(
        self,
        clean_images: List[np.ndarray],
        noise_levels: List[float] = [15, 25, 50],
    ):
        self.clean_images = clean_images
        self.noise_levels = noise_levels

        # Create all combinations
        self.samples = []
        for img_idx, clean in enumerate(clean_images):
            for sigma in noise_levels:
                self.samples.append((img_idx, sigma))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, float]:
        """Get validation sample with fixed noise level.

        Returns:
            Tuple of (noisy_image, clean_image, noise, sigma)
        """
        img_idx, sigma = self.samples[idx]
        clean = self.clean_images[img_idx].copy()

        # Add fixed noise
        noisy, noise = add_gaussian_noise(clean, sigma=sigma)

        # Convert to tensors
        clean_tensor = torch.from_numpy(clean).float()
        noisy_tensor = torch.from_numpy(noisy).float()
        noise_tensor = torch.from_numpy(noise).float()

        return noisy_tensor, clean_tensor, noise_tensor, sigma


def create_dataloaders(
    train_images: Optional[List[np.ndarray]] = None,
    val_images: Optional[List[np.ndarray]] = None,
    train_dir: Optional[str] = None,
    val_dir: Optional[str] = None,
    batch_size: int = 16,
    patch_size: int = 128,
    num_workers: int = 4,
    noise_sigma_range: Tuple[float, float] = (5, 50),
) -> Tuple[DataLoader, DataLoader]:
    """Create training and validation dataloaders.

    Args:
        train_images: List of training images
        val_images: List of validation images
        train_dir: Directory containing training images
        val_dir: Directory containing validation images
        batch_size: Batch size
        patch_size: Size of training patches
        num_workers: Number of data loading workers
        noise_sigma_range: Range of noise levels for training

    Returns:
        Tuple of (train_loader, val_loader)
    """
    # Create noise generators
    train_noise_gen = NoiseGenerator(
        noise_type="gaussian",
        sigma_range=noise_sigma_range,
    )

    # Create datasets
    train_dataset = DenoisingDataset(
        clean_images=train_images,
        image_dir=train_dir,
        noise_generator=train_noise_gen,
        patch_size=patch_size,
        augment=True,
    )

    val_noise_gen = NoiseGenerator(noise_type="gaussian", fixed_sigma=25.0)
    val_dataset = DenoisingDataset(
        clean_images=val_images,
        image_dir=val_dir,
        noise_generator=val_noise_gen,
        patch_size=patch_size,
        augment=False,
    )

    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )

    return train_loader, val_loader


if __name__ == "__main__":
    # Test dataset creation
    print("Testing DenoisingDataset")
    print("=" * 40)

    # Create dataset with synthetic data
    dataset = DenoisingDataset(patch_size=64)
    print(f"Dataset size: {len(dataset)}")

    # Get a sample
    noisy, clean, noise = dataset[0]
    print(f"Sample shapes:")
    print(f"  Noisy: {noisy.shape}")
    print(f"  Clean: {clean.shape}")
    print(f"  Noise: {noise.shape}")

    # Create dataloaders
    train_loader, val_loader = create_dataloaders(
        batch_size=4,
        patch_size=64,
        num_workers=0,
    )

    print(f"\nTrain loader batches: {len(train_loader)}")
    print(f"Val loader batches: {len(val_loader)}")

    # Get a batch
    batch = next(iter(train_loader))
    noisy_batch, clean_batch, noise_batch = batch
    print(f"\nBatch shapes:")
    print(f"  Noisy: {noisy_batch.shape}")
    print(f"  Clean: {clean_batch.shape}")
    print(f"  Noise: {noise_batch.shape}")
