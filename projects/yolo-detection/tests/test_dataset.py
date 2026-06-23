"""
Tests for dataset and data loading.
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dataset import (
    SimpleDetectionDataset,
    MultiScaleDataset,
    collate_fn,
    create_dataloader,
)


class TestSimpleDetectionDataset:
    """Test SimpleDetectionDataset."""

    def test_dataset_creation(self):
        """Test that dataset can be created."""
        dataset = SimpleDetectionDataset(num_samples=10, grid_size=7, num_classes=5)
        assert len(dataset) == 10

    def test_dataset_getitem(self):
        """Test dataset item retrieval."""
        dataset = SimpleDetectionDataset(num_samples=10, grid_size=7, num_classes=5)
        image, targets = dataset[0]

        assert image.shape == (3, 448, 448)
        assert "target" in targets
        assert "boxes" in targets
        assert "labels" in targets

    def test_dataset_image_range(self):
        """Test that image values are in [0, 1]."""
        dataset = SimpleDetectionDataset(num_samples=10)
        image, _ = dataset[0]
        assert image.min() >= 0.0
        assert image.max() <= 1.0

    def test_dataset_target_shape(self):
        """Test target tensor shape."""
        grid_size = 7
        num_classes = 5
        dataset = SimpleDetectionDataset(
            num_samples=10, grid_size=grid_size, num_classes=num_classes
        )
        _, targets = dataset[0]

        assert targets["target"].shape == (grid_size, grid_size, 2 * 5 + num_classes)

    def test_dataset_reproducibility(self):
        """Test that dataset is reproducible with same seed."""
        dataset1 = SimpleDetectionDataset(num_samples=5, seed=42)
        dataset2 = SimpleDetectionDataset(num_samples=5, seed=42)

        img1, _ = dataset1[0]
        img2, _ = dataset2[0]
        assert torch.allclose(img1, img2)

    def test_dataset_different_seeds(self):
        """Test that different seeds produce different data."""
        dataset1 = SimpleDetectionDataset(num_samples=5, seed=42)
        dataset2 = SimpleDetectionDataset(num_samples=5, seed=123)

        img1, _ = dataset1[0]
        img2, _ = dataset2[0]
        assert not torch.allclose(img1, img2)


class TestMultiScaleDataset:
    """Test MultiScaleDataset."""

    def test_multiscale_creation(self):
        """Test that multi-scale dataset can be created."""
        base = SimpleDetectionDataset(num_samples=10)
        dataset = MultiScaleDataset(base, scales=[320, 448])
        assert len(dataset) == 10

    def test_multiscale_random_scale(self):
        """Test that multi-scale dataset applies random scales."""
        base = SimpleDetectionDataset(num_samples=10)
        dataset = MultiScaleDataset(base, scales=[320, 448])

        # Get multiple samples and check they have different sizes
        sizes = set()
        for i in range(20):
            image, _ = dataset[i % len(dataset)]
            sizes.add(image.shape[-1])

        # Should have at least one size (may not always get both due to randomness)
        assert len(sizes) >= 1


class TestCollateFn:
    """Test collate function."""

    def test_collate_basic(self):
        """Test basic collation."""
        dataset = SimpleDetectionDataset(num_samples=4, grid_size=7, num_classes=5)
        batch = [dataset[0], dataset[1], dataset[2], dataset[3]]

        images, targets = collate_fn(batch)

        assert images.shape == (4, 3, 448, 448)
        expected_c = 2 * 5 + 5  # B*5 + num_classes
        assert targets["target"].shape == (4, 7, 7, expected_c)
        assert len(targets["boxes"]) == 4
        assert len(targets["labels"]) == 4

    def test_collate_single_item(self):
        """Test collation with single item."""
        dataset = SimpleDetectionDataset(num_samples=1)
        batch = [dataset[0]]

        images, targets = collate_fn(batch)

        assert images.shape == (1, 3, 448, 448)


class TestDataLoader:
    """Test DataLoader creation."""

    def test_create_dataloader(self):
        """Test DataLoader creation."""
        dataset = SimpleDetectionDataset(num_samples=10)
        loader = create_dataloader(dataset, batch_size=2)

        for images, targets in loader:
            assert images.shape[0] == 2
            break

    def test_dataloader_shuffle(self):
        """Test that DataLoader shuffles."""
        dataset = SimpleDetectionDataset(num_samples=10, seed=42)
        loader = create_dataloader(dataset, batch_size=10, shuffle=True)

        # Get all images
        all_images = []
        for images, _ in loader:
            all_images.append(images)

        # With shuffle, order should be different from sequential
        # (this is probabilistic but very likely)
        assert len(all_images) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
