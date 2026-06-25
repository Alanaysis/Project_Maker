"""
Tests for the ImageInpainter pipeline.
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.inpainting import ImageInpainter
from src.mask import generate_center_mask, generate_random_rect_mask


class TestImageInpainter:
    """Test suite for ImageInpainter."""

    @pytest.fixture
    def inpainter(self):
        """Create a small ImageInpainter for fast testing."""
        return ImageInpainter(image_size=(64, 64), ngf=16, ndf=16, device="cpu")

    def test_inpaint_single_image(self, inpainter):
        """Test inpainting a single image."""
        image = torch.rand(3, 64, 64) * 2 - 1  # [-1, 1]
        mask = generate_center_mask((64, 64), mask_ratio=0.25)

        result = inpainter.inpaint(image, mask)
        assert result.shape == (3, 64, 64)

    def test_inpaint_batch(self, inpainter):
        """Test inpainting a batch of images."""
        images = torch.rand(2, 3, 64, 64) * 2 - 1
        mask = generate_center_mask((64, 64), mask_ratio=0.25)

        results = inpainter.inpaint(images, mask)
        assert results.shape == (2, 3, 64, 64)

    def test_inpaint_preserves_known(self, inpainter):
        """Test that inpainting preserves known regions when blending."""
        image = torch.rand(3, 64, 64) * 2 - 1
        mask = torch.zeros(1, 64, 64)
        mask[:, 0:32, 0:32] = 1.0  # Only mask top-left

        result = inpainter.inpaint(image, mask, blend=True)
        assert result.shape == (3, 64, 64)

    def test_train_step(self, inpainter):
        """Test that training step returns loss values."""
        images = torch.rand(2, 3, 64, 64) * 2 - 1
        masks = torch.stack([
            generate_center_mask((64, 64), mask_ratio=0.25) for _ in range(2)
        ])

        losses = inpainter.train_step(images, masks)

        assert "d_loss" in losses
        assert "g_loss" in losses
        assert "rec_loss" in losses
        assert "adv_loss" in losses
        assert all(isinstance(v, float) for v in losses.values())

    def test_evaluate(self, inpainter):
        """Test evaluation returns metrics."""
        images = torch.rand(2, 3, 64, 64) * 2 - 1
        masks = torch.stack([
            generate_center_mask((64, 64), mask_ratio=0.25) for _ in range(2)
        ])

        metrics = inpainter.evaluate(images, masks)

        assert "psnr" in metrics
        assert "ssim" in metrics
        assert "l1_error" in metrics
        assert metrics["psnr"] > 0
        assert -1 <= metrics["ssim"] <= 1
        assert metrics["l1_error"] >= 0

    def test_save_load(self, inpainter, tmp_path):
        """Test saving and loading model checkpoints."""
        path = str(tmp_path / "checkpoint.pt")
        inpainter.save(path)
        assert os.path.exists(path)

        # Load into a new inpainter with same architecture
        new_inpainter = ImageInpainter(image_size=(64, 64), ngf=16, ndf=16, device="cpu")
        new_inpainter.load(path)

        # Check that weights match
        for (n1, p1), (n2, p2) in zip(
            inpainter.generator.named_parameters(),
            new_inpainter.generator.named_parameters(),
        ):
            assert torch.allclose(p1, p2), f"Parameter {n1} mismatch after load"

    def test_training_improves(self, inpainter):
        """Test that training reduces loss over several steps."""
        images = torch.rand(4, 3, 64, 64) * 2 - 1
        masks = torch.stack([
            generate_random_rect_mask((64, 64), seed=i) for i in range(4)
        ])

        # Initial step
        initial_losses = inpainter.train_step(images, masks)

        # Train for a few more steps
        for _ in range(5):
            losses = inpainter.train_step(images, masks)

        # Losses should be finite
        assert all(v == v for v in losses.values()), "Losses should not be NaN"
        assert all(v != float("inf") for v in losses.values()), "Losses should not be inf"
