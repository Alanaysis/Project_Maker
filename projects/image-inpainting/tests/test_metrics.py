"""
Tests for image quality metrics.
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.metrics import compute_psnr, compute_ssim, compute_l1_error


class TestPSNR:
    """Test suite for PSNR metric."""

    def test_identical_images(self):
        """Test that identical images give infinite PSNR."""
        x = torch.rand(3, 64, 64)
        psnr = compute_psnr(x, x.clone())
        assert psnr == float("inf")

    def test_known_psnr(self):
        """Test PSNR with known MSE."""
        # Create images with known MSE = 0.01
        pred = torch.ones(3, 64, 64) * 0.5
        target = pred + 0.1  # MSE = 0.01
        psnr = compute_psnr(pred, target, max_val=1.0)
        # PSNR = 10 * log10(1.0 / 0.01) = 10 * 2 = 20 dB
        assert abs(psnr - 20.0) < 0.1

    def test_higher_is_better(self):
        """Test that more similar images have higher PSNR."""
        target = torch.rand(3, 64, 64)
        pred_good = target + 0.01
        pred_bad = target + 0.1

        psnr_good = compute_psnr(pred_good, target)
        psnr_bad = compute_psnr(pred_bad, target)

        assert psnr_good > psnr_bad

    def test_with_mask(self):
        """Test PSNR computation with mask."""
        pred = torch.rand(3, 64, 64)
        target = torch.rand(3, 64, 64)
        mask = torch.zeros(1, 64, 64)
        mask[:, 16:48, 16:48] = 1.0

        psnr = compute_psnr(pred, target, mask)
        assert isinstance(psnr, float)
        assert psnr > 0


class TestSSIM:
    """Test suite for SSIM metric."""

    def test_identical_images(self):
        """Test that identical images have SSIM close to 1."""
        x = torch.rand(3, 64, 64)
        ssim = compute_ssim(x, x.clone())
        assert ssim > 0.99, f"SSIM for identical images should be ~1, got {ssim}"

    def test_different_images(self):
        """Test that very different images have lower SSIM."""
        x = torch.zeros(3, 64, 64)
        y = torch.ones(3, 64, 64)
        ssim = compute_ssim(x, y)
        assert ssim < 0.5, f"SSIM for very different images should be low, got {ssim}"

    def test_ssim_range(self):
        """Test that SSIM is in valid range."""
        x = torch.rand(3, 64, 64)
        y = torch.rand(3, 64, 64)
        ssim = compute_ssim(x, y)
        assert -1.0 <= ssim <= 1.0, f"SSIM should be in [-1, 1], got {ssim}"

    def test_batch_input(self):
        """Test SSIM with batched input."""
        x = torch.rand(2, 3, 64, 64)
        y = torch.rand(2, 3, 64, 64)
        ssim = compute_ssim(x, y)
        assert isinstance(ssim, float)


class TestL1Error:
    """Test suite for L1 error metric."""

    def test_identical_images(self):
        """Test that identical images have L1 error of 0."""
        x = torch.rand(3, 64, 64)
        l1 = compute_l1_error(x, x.clone())
        assert l1 < 1e-6

    def test_known_error(self):
        """Test L1 error with known difference."""
        pred = torch.ones(3, 4, 4) * 0.5
        target = torch.zeros(3, 4, 4)
        l1 = compute_l1_error(pred, target)
        assert abs(l1 - 0.5) < 1e-6

    def test_with_mask(self):
        """Test L1 error with mask."""
        pred = torch.ones(3, 8, 8)
        target = torch.zeros(3, 8, 8)
        mask = torch.zeros(1, 8, 8)
        mask[:, 0:4, 0:4] = 1.0

        l1 = compute_l1_error(pred, target, mask)
        assert abs(l1 - 1.0) < 1e-6  # Only masked region matters
