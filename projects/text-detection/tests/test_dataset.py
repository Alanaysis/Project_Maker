"""
Tests for Dataset and Transforms
"""

import sys
import os
import torch
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data.dataset import TextDetectionDataset, SyntheticTextGenerator
from src.data.transforms import (
    TextDetectionTransform, RandomRotate, RandomCrop, ColorJitter
)


class TestTextDetectionDataset:
    """Test text detection dataset."""

    def test_dataset_length(self):
        """Test dataset length."""
        dataset = TextDetectionDataset(num_samples=100)
        assert len(dataset) == 100

    def test_getitem(self):
        """Test getting an item from dataset."""
        dataset = TextDetectionDataset(num_samples=10, img_size=256)
        img, score_map, geo_map, mask = dataset[0]

        assert img.shape == (3, 256, 256)
        assert score_map.shape == (1, 64, 64)  # 256/4
        assert geo_map.shape == (5, 64, 64)
        assert mask.shape == (1, 64, 64)

    def test_image_normalization(self):
        """Test image is properly normalized."""
        dataset = TextDetectionDataset(num_samples=10, img_size=128)
        img, _, _, _ = dataset[0]

        # Should be roughly normalized
        assert img.min() > -5
        assert img.max() < 5

    def test_score_map_range(self):
        """Test score map values are in [0, 1]."""
        dataset = TextDetectionDataset(num_samples=10, img_size=128)
        _, score_map, _, _ = dataset[0]

        assert score_map.min() >= 0
        assert score_map.max() <= 1

    def test_deterministic_with_seed(self):
        """Test deterministic generation with same seed."""
        dataset = TextDetectionDataset(num_samples=10, img_size=128)
        img1, s1, g1, m1 = dataset[0]
        img2, s2, g2, m2 = dataset[0]

        assert torch.allclose(img1, img2)
        assert torch.allclose(s1, s2)

    def test_batch_collation(self):
        """Test dataset works with DataLoader."""
        from torch.utils.data import DataLoader

        dataset = TextDetectionDataset(num_samples=10, img_size=128)
        loader = DataLoader(dataset, batch_size=4, shuffle=False)

        batch = next(iter(loader))
        imgs, scores, geos, masks = batch

        assert imgs.shape == (4, 3, 128, 128)
        assert scores.shape == (4, 1, 32, 32)


class TestSyntheticTextGenerator:
    """Test synthetic text generator."""

    def test_generate_sample(self):
        """Test sample generation."""
        gen = SyntheticTextGenerator(img_size=256)
        img, boxes = gen.generate_sample(num_texts=3)

        assert img.shape == (256, 256, 3)
        assert len(boxes) == 3

    def test_box_format(self):
        """Test box format [x1, y1, x2, y2]."""
        gen = SyntheticTextGenerator(img_size=256)
        img, boxes = gen.generate_sample(num_texts=5)

        for box in boxes:
            x1, y1, x2, y2 = box
            assert x2 > x1
            assert y2 > y1

    def test_generate_batch(self):
        """Test batch generation."""
        gen = SyntheticTextGenerator(img_size=256)
        images, batch_boxes = gen.generate_batch(batch_size=4, num_texts=3)

        assert images.shape == (4, 256, 256, 3)
        assert len(batch_boxes) == 4


class TestTextDetectionTransform:
    """Test text detection transforms."""

    def test_transform_image_only(self):
        """Test transform with image only."""
        transform = TextDetectionTransform(img_size=256)
        img = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)

        result = transform(img)

        assert isinstance(result, torch.Tensor)
        assert result.shape == (3, 256, 256)

    def test_transform_with_maps(self):
        """Test transform with score and geo maps."""
        transform = TextDetectionTransform(img_size=256)
        img = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        score_map = np.random.rand(64, 64).astype(np.float32)
        geo_map = np.random.rand(5, 64, 64).astype(np.float32)

        img_t, score_t, geo_t = transform(img, score_map, geo_map)

        assert img_t.shape == (3, 256, 256)
        assert score_t.shape == (1, 64, 64)
        assert geo_t.shape == (5, 64, 64)


class TestColorJitter:
    """Test color jitter augmentation."""

    def test_brightness(self):
        """Test brightness augmentation."""
        jitter = ColorJitter(brightness=0.5)
        img = np.ones((100, 100, 3), dtype=np.uint8) * 128

        result = jitter(img)

        assert result.shape == img.shape
        assert result.dtype == np.uint8

    def test_contrast(self):
        """Test contrast augmentation."""
        jitter = ColorJitter(contrast=0.5)
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        result = jitter(img)

        assert result.shape == img.shape


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
