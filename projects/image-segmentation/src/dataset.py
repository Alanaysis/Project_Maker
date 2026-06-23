"""
Dataset utilities for image segmentation.

Provides a simple dataset class that loads images and their corresponding
segmentation masks. Supports both file-based and in-memory (synthetic)
datasets for testing and demonstration purposes.
"""

import os
from typing import Callable, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset


class SegmentationDataset(Dataset):
    """Dataset for image segmentation tasks.

    Supports two modes:
    1. File-based: Loads images and masks from directories.
    2. Synthetic: Generates synthetic data for testing (when length is specified).

    Args:
        images: List/array of images (N, C, H, W) or directory path.
        masks: List/array of masks (N, 1, H, W) or directory path.
        image_transform: Optional transform applied to images.
        mask_transform: Optional transform applied to masks.
    """

    def __init__(
        self,
        images: Optional[np.ndarray] = None,
        masks: Optional[np.ndarray] = None,
        image_transform: Optional[Callable] = None,
        mask_transform: Optional[Callable] = None,
    ):
        self.images = images
        self.masks = masks
        self.image_transform = image_transform
        self.mask_transform = mask_transform

    def __len__(self) -> int:
        """Return the number of samples in the dataset."""
        if self.images is not None:
            return len(self.images)
        return 0

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get a sample from the dataset.

        Args:
            idx: Index of the sample.

        Returns:
            Tuple of (image, mask) as torch.Tensor.
        """
        image = self.images[idx]
        mask = self.masks[idx]

        # Convert to tensors if needed
        if not isinstance(image, torch.Tensor):
            image = torch.from_numpy(image).float()
        if not isinstance(mask, torch.Tensor):
            mask = torch.from_numpy(mask).float()

        # Apply transforms
        if self.image_transform is not None:
            image = self.image_transform(image)
        if self.mask_transform is not None:
            mask = self.mask_transform(mask)

        return image, mask


def create_synthetic_dataset(
    n_samples: int = 100,
    image_size: int = 128,
    n_channels: int = 3,
    n_classes: int = 1,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """Create a synthetic segmentation dataset for testing.

    Generates random images with simple geometric shapes as segmentation targets.
    Useful for testing the training pipeline without real data.

    Args:
        n_samples: Number of samples to generate.
        image_size: Height and width of the images.
        n_channels: Number of image channels.
        n_classes: Number of segmentation classes.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (images, masks) as numpy arrays.
        - images: (n_samples, n_channels, image_size, image_size)
        - masks: (n_samples, n_classes, image_size, image_size) with values 0 or 1
    """
    np.random.seed(seed)

    images = np.random.randn(n_samples, n_channels, image_size, image_size).astype(np.float32) * 0.1
    masks = np.zeros((n_samples, n_classes, image_size, image_size), dtype=np.float32)

    for i in range(n_samples):
        # Create a simple circular mask in the center
        center_x = np.random.randint(image_size // 4, 3 * image_size // 4)
        center_y = np.random.randint(image_size // 4, 3 * image_size // 4)
        radius = np.random.randint(image_size // 8, image_size // 4)

        y_grid, x_grid = np.ogrid[:image_size, :image_size]
        dist = np.sqrt((x_grid - center_x) ** 2 + (y_grid - center_y) ** 2)

        for c in range(n_classes):
            # Different radius per class
            r = radius + c * 10
            mask = (dist <= r).astype(np.float32)
            masks[i, c] = mask

            # Make the image region brighter where the mask is
            for ch in range(n_channels):
                images[i, ch] += mask * (0.5 + 0.1 * c)

    return images, masks
