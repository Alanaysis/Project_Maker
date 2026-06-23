"""
Tests for dataset and training utilities.
"""

import sys
import os

import pytest
import torch
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dataset import SegmentationDataset, create_synthetic_dataset
from src.train import compute_iou, compute_dice_coefficient, Trainer
from src.unet import UNet


class TestSegmentationDataset:
    """Test suite for SegmentationDataset."""

    def test_numpy_input(self):
        """Dataset should accept numpy arrays."""
        images = np.random.randn(10, 3, 32, 32).astype(np.float32)
        masks = np.random.randint(0, 2, (10, 1, 32, 32)).astype(np.float32)
        dataset = SegmentationDataset(images=images, masks=masks)
        assert len(dataset) == 10

    def test_tensor_input(self):
        """Dataset should accept torch tensors."""
        images = torch.randn(5, 3, 32, 32)
        masks = torch.randint(0, 2, (5, 1, 32, 32)).float()
        dataset = SegmentationDataset(images=images, masks=masks)
        assert len(dataset) == 5

    def test_getitem_returns_tensors(self):
        """Dataset should return torch tensors."""
        images = np.random.randn(5, 3, 32, 32).astype(np.float32)
        masks = np.random.randint(0, 2, (5, 1, 32, 32)).astype(np.float32)
        dataset = SegmentationDataset(images=images, masks=masks)
        img, mask = dataset[0]
        assert isinstance(img, torch.Tensor)
        assert isinstance(mask, torch.Tensor)

    def test_empty_dataset(self):
        """Empty dataset should have length 0."""
        dataset = SegmentationDataset()
        assert len(dataset) == 0


class TestSyntheticDataset:
    """Test suite for create_synthetic_dataset."""

    def test_default_generation(self):
        """Default parameters should generate correct shapes."""
        images, masks = create_synthetic_dataset()
        assert images.shape == (100, 3, 128, 128)
        assert masks.shape == (100, 1, 128, 128)

    def test_custom_parameters(self):
        """Custom parameters should be respected."""
        images, masks = create_synthetic_dataset(
            n_samples=10, image_size=64, n_channels=1, n_classes=2
        )
        assert images.shape == (10, 1, 64, 64)
        assert masks.shape == (10, 2, 64, 64)

    def test_reproducibility(self):
        """Same seed should produce same data."""
        imgs1, masks1 = create_synthetic_dataset(seed=42)
        imgs2, masks2 = create_synthetic_dataset(seed=42)
        np.testing.assert_array_equal(imgs1, imgs2)
        np.testing.assert_array_equal(masks1, masks2)

    def test_mask_values(self):
        """Masks should contain only 0 and 1."""
        _, masks = create_synthetic_dataset(n_samples=10)
        unique = np.unique(masks)
        assert set(unique).issubset({0.0, 1.0})

    def test_image_dtype(self):
        """Images should be float32."""
        images, _ = create_synthetic_dataset(n_samples=5)
        assert images.dtype == np.float32


class TestMetrics:
    """Test suite for IoU and Dice metrics."""

    def test_perfect_iou(self):
        """Perfect prediction should give IoU of 1.0."""
        pred = torch.full((1, 1, 8, 8), 10.0)
        target = torch.ones(1, 1, 8, 8)
        iou = compute_iou(pred, target)
        assert abs(iou - 1.0) < 0.01

    def test_zero_iou(self):
        """Completely wrong prediction should give IoU near 0."""
        pred = torch.full((1, 1, 8, 8), -10.0)
        target = torch.ones(1, 1, 8, 8)
        iou = compute_iou(pred, target)
        assert iou < 0.01

    def test_perfect_dice(self):
        """Perfect prediction should give Dice of 1.0."""
        pred = torch.full((1, 1, 8, 8), 10.0)
        target = torch.ones(1, 1, 8, 8)
        dice = compute_dice_coefficient(pred, target)
        assert abs(dice - 1.0) < 0.01

    def test_iou_range(self):
        """IoU should be in [0, 1]."""
        pred = torch.randn(4, 1, 16, 16)
        target = torch.randint(0, 2, (4, 1, 16, 16)).float()
        iou = compute_iou(pred, target)
        assert 0.0 <= iou <= 1.0

    def test_dice_range(self):
        """Dice should be in [0, 1]."""
        pred = torch.randn(4, 1, 16, 16)
        target = torch.randint(0, 2, (4, 1, 16, 16)).float()
        dice = compute_dice_coefficient(pred, target)
        assert 0.0 <= dice <= 1.0


class TestTrainer:
    """Test suite for Trainer."""

    @pytest.fixture
    def small_model_and_data(self):
        """Create a small model and synthetic data for testing."""
        model = UNet(in_channels=3, out_channels=1, base_channels=8, n_levels=2)
        images, masks = create_synthetic_dataset(n_samples=8, image_size=32, seed=42)
        dataset = SegmentationDataset(images=images, masks=masks)
        loader = torch.utils.data.DataLoader(dataset, batch_size=4, shuffle=False)
        return model, loader

    def test_train_epoch(self, small_model_and_data):
        """Trainer should complete one training epoch."""
        model, loader = small_model_and_data
        trainer = Trainer(model, learning_rate=1e-3)
        loss = trainer.train_epoch(loader)
        assert isinstance(loss, float)
        assert loss > 0

    def test_validate(self, small_model_and_data):
        """Trainer should compute validation metrics."""
        model, loader = small_model_and_data
        trainer = Trainer(model)
        metrics = trainer.validate(loader)
        assert "loss" in metrics
        assert "iou" in metrics
        assert "dice" in metrics

    def test_fit(self, small_model_and_data):
        """Trainer.fit should run multiple epochs and return history."""
        model, loader = small_model_and_data
        trainer = Trainer(model, learning_rate=1e-3)
        history = trainer.fit(loader, n_epochs=3, verbose=False)
        assert len(history["train_losses"]) == 3
        # Loss should generally decrease
        assert history["train_losses"][-1] <= history["train_losses"][0] * 2

    def test_fit_with_validation(self, small_model_and_data):
        """Trainer.fit with validation should track val metrics."""
        model, loader = small_model_and_data
        trainer = Trainer(model, learning_rate=1e-3)
        history = trainer.fit(loader, val_loader=loader, n_epochs=2, verbose=False)
        assert len(history["val_losses"]) == 2
        assert len(history["val_ious"]) == 2

    def test_training_reduces_loss(self, small_model_and_data):
        """Training should generally reduce loss over epochs."""
        model, loader = small_model_and_data
        trainer = Trainer(model, learning_rate=1e-2)
        history = trainer.fit(loader, n_epochs=10, verbose=False)
        # With enough epochs and a reasonable lr, loss should decrease
        assert history["train_losses"][-1] < history["train_losses"][0]
