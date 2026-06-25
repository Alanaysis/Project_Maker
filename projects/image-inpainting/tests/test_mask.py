"""
Tests for mask generation utilities.
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.mask import (
    generate_center_mask,
    generate_random_rect_mask,
    generate_irregular_mask,
    apply_mask,
)


class TestCenterMask:
    """Test suite for center mask generation."""

    def test_output_shape(self):
        """Test that center mask has correct shape."""
        mask = generate_center_mask((128, 128), mask_ratio=0.25)
        assert mask.shape == (1, 128, 128)

    def test_different_sizes(self):
        """Test center mask with different image sizes."""
        for h, w in [(64, 64), (128, 256), (256, 128)]:
            mask = generate_center_mask((h, w))
            assert mask.shape == (1, h, w)

    def test_mask_ratio(self):
        """Test that mask ratio controls mask size."""
        mask = generate_center_mask((100, 100), mask_ratio=0.5)
        # Mask should cover 50x50 = 2500 pixels
        assert mask.sum() == 50 * 50

    def test_binary_values(self):
        """Test that mask contains only 0s and 1s."""
        mask = generate_center_mask((128, 128))
        assert ((mask == 0) | (mask == 1)).all()

    def test_centered_position(self):
        """Test that mask is centered in the image."""
        mask = generate_center_mask((100, 100), mask_ratio=0.2)
        # Find bounding box of masked region
        rows = mask[0].any(dim=1).nonzero()
        cols = mask[0].any(dim=0).nonzero()
        # Should be centered at (50, 50)
        center_y = (rows[0] + rows[-1]) / 2
        center_x = (cols[0] + cols[-1]) / 2
        assert abs(center_y - 49.5) < 1, "Mask should be vertically centered"
        assert abs(center_x - 49.5) < 1, "Mask should be horizontally centered"


class TestRandomRectMask:
    """Test suite for random rectangular mask generation."""

    def test_output_shape(self):
        """Test output shape."""
        mask = generate_random_rect_mask((128, 128))
        assert mask.shape == (1, 128, 128)

    def test_reproducibility(self):
        """Test that same seed produces same mask."""
        mask1 = generate_random_rect_mask((128, 128), seed=42)
        mask2 = generate_random_rect_mask((128, 128), seed=42)
        assert torch.allclose(mask1, mask2)

    def test_different_seeds(self):
        """Test that different seeds produce different masks."""
        mask1 = generate_random_rect_mask((128, 128), seed=42)
        mask2 = generate_random_rect_mask((128, 128), seed=123)
        assert not torch.allclose(mask1, mask2)

    def test_multiple_masks(self):
        """Test generating multiple rectangular holes."""
        mask = generate_random_rect_mask((128, 128), num_masks=5, seed=42)
        # With 5 masks, more area should be covered than with 1
        mask_single = generate_random_rect_mask((128, 128), num_masks=1, seed=42)
        # This isn't guaranteed, but is very likely
        assert mask.sum() >= mask_single.sum()

    def test_binary_values(self):
        """Test that mask contains only 0s and 1s."""
        mask = generate_random_rect_mask((128, 128), seed=42)
        assert ((mask == 0) | (mask == 1)).all()


class TestIrregularMask:
    """Test suite for irregular mask generation."""

    def test_output_shape(self):
        """Test output shape."""
        mask = generate_irregular_mask((128, 128))
        assert mask.shape == (1, 128, 128)

    def test_reproducibility(self):
        """Test reproducibility with seed."""
        mask1 = generate_irregular_mask((128, 128), seed=42)
        mask2 = generate_irregular_mask((128, 128), seed=42)
        assert torch.allclose(mask1, mask2)

    def test_nonzero_mask(self):
        """Test that the mask actually contains masked pixels."""
        mask = generate_irregular_mask((128, 128), num_strokes=10, seed=42)
        assert mask.sum() > 0, "Irregular mask should have some masked pixels"

    def test_binary_values(self):
        """Test that mask contains only 0s and 1s."""
        mask = generate_irregular_mask((128, 128), seed=42)
        assert ((mask == 0) | (mask == 1)).all()

    def test_more_strokes_more_coverage(self):
        """Test that more strokes lead to more coverage on average."""
        mask_few = generate_irregular_mask((128, 128), num_strokes=3, seed=42)
        mask_many = generate_irregular_mask((128, 128), num_strokes=20, seed=42)
        assert mask_many.sum() >= mask_few.sum()


class TestApplyMask:
    """Test suite for the apply_mask function."""

    def test_basic_application(self):
        """Test basic mask application."""
        image = torch.ones(3, 64, 64)
        mask = torch.zeros(1, 64, 64)
        mask[:, 16:48, 16:48] = 1.0

        masked = apply_mask(image, mask, mask_value=0.0)

        # Known regions should be unchanged
        assert (masked[:, 0, 0] == 1.0).all()
        # Masked regions should be 0
        assert (masked[:, 32, 32] == 0.0).all()

    def test_mask_value(self):
        """Test custom mask fill value."""
        image = torch.ones(3, 64, 64)
        mask = torch.ones(1, 64, 64)  # Mask everything

        masked = apply_mask(image, mask, mask_value=-1.0)
        assert (masked == -1.0).all()

    def test_preserves_known_regions(self):
        """Test that known (unmasked) regions are preserved."""
        image = torch.randn(3, 64, 64)
        mask = torch.zeros(1, 64, 64)
        mask[:, 0:32, 0:32] = 1.0  # Only mask top-left quadrant

        masked = apply_mask(image, mask, mask_value=0.0)

        # Bottom-right quadrant should be unchanged
        assert torch.allclose(masked[:, 32:, 32:], image[:, 32:, 32:])

    def test_batch_support(self):
        """Test batched mask application."""
        image = torch.ones(2, 3, 64, 64)
        mask = torch.zeros(1, 64, 64)
        mask[:, 16:48, 16:48] = 1.0

        masked = apply_mask(image, mask)
        assert masked.shape == (2, 3, 64, 64)
