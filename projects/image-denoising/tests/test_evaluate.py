"""Tests for evaluation metrics."""

import pytest
import torch
import numpy as np

from src.evaluate import (
    calculate_mse,
    calculate_psnr,
    calculate_ssim,
    calculate_metrics,
    MetricTracker,
)


class TestMSE:
    """Test suite for MSE calculation."""

    def test_identical_images(self):
        """Test MSE is 0 for identical images."""
        image = np.random.rand(1, 64, 64).astype(np.float32)
        assert calculate_mse(image, image) == 0.0

    def test_known_mse(self):
        """Test MSE calculation with known values."""
        image1 = np.zeros((1, 10, 10), dtype=np.float32)
        image2 = np.ones((1, 10, 10), dtype=np.float32)
        assert calculate_mse(image1, image2) == 1.0

    def test_partial_difference(self):
        """Test MSE with partial differences."""
        image1 = np.zeros((1, 10, 10), dtype=np.float32)
        image2 = np.zeros((1, 10, 10), dtype=np.float32)
        image2[0, 0, 0] = 1.0
        expected_mse = 1.0 / 100  # One pixel differs by 1.0
        assert abs(calculate_mse(image1, image2) - expected_mse) < 1e-6


class TestPSNR:
    """Test suite for PSNR calculation."""

    def test_identical_images(self):
        """Test PSNR is infinity for identical images."""
        image = np.random.rand(1, 64, 64).astype(np.float32)
        psnr = calculate_psnr(image, image)
        assert psnr == float('inf')

    def test_known_psnr(self):
        """Test PSNR calculation with known MSE."""
        # PSNR = 10 * log10(1 / MSE)
        image1 = np.zeros((1, 10, 10), dtype=np.float32)
        image2 = np.full((1, 10, 10), 0.1, dtype=np.float32)
        expected_psnr = 10 * np.log10(1.0 / 0.01)  # MSE = 0.01
        psnr = calculate_psnr(image1, image2)
        assert abs(psnr - expected_psnr) < 0.01

    def test_higher_psnr_better(self):
        """Test higher PSNR indicates better quality."""
        clean = np.random.rand(1, 64, 64).astype(np.float32)
        noisy_small = clean + np.random.randn(*clean.shape).astype(np.float32) * 0.01
        noisy_large = clean + np.random.randn(*clean.shape).astype(np.float32) * 0.1

        psnr_small = calculate_psnr(clean, noisy_small)
        psnr_large = calculate_psnr(clean, noisy_large)

        assert psnr_small > psnr_large


class TestSSIM:
    """Test suite for SSIM calculation."""

    def test_identical_images(self):
        """Test SSIM is 1 for identical images."""
        image = np.random.rand(1, 64, 64).astype(np.float32)
        ssim = calculate_ssim(image, image)
        assert abs(ssim - 1.0) < 0.01

    def test_different_images(self):
        """Test SSIM is low for very different images."""
        image1 = np.zeros((1, 64, 64), dtype=np.float32)
        image2 = np.ones((1, 64, 64), dtype=np.float32)
        ssim = calculate_ssim(image1, image2)
        assert ssim < 0.5

    def test_ssim_range(self):
        """Test SSIM is in valid range."""
        image1 = np.random.rand(1, 64, 64).astype(np.float32)
        image2 = image1 + np.random.randn(*image1.shape).astype(np.float32) * 0.1
        image2 = np.clip(image2, 0, 1)
        ssim = calculate_ssim(image1, image2)
        assert -1 <= ssim <= 1

    def test_torch_input(self):
        """Test SSIM works with PyTorch tensors."""
        image1 = torch.rand(1, 64, 64)
        image2 = image1 + torch.randn_like(image1) * 0.05
        image2 = torch.clamp(image2, 0, 1)
        ssim = calculate_ssim(image1, image2)
        assert -1 <= ssim <= 1

    def test_higher_ssim_better(self):
        """Test higher SSIM indicates better quality."""
        clean = np.random.rand(1, 64, 64).astype(np.float32)
        noisy_small = clean + np.random.randn(*clean.shape).astype(np.float32) * 0.01
        noisy_large = clean + np.random.randn(*clean.shape).astype(np.float32) * 0.1

        ssim_small = calculate_ssim(clean, noisy_small)
        ssim_large = calculate_ssim(clean, noisy_large)

        assert ssim_small > ssim_large


class TestCalculateMetrics:
    """Test suite for combined metrics calculation."""

    def test_returns_all_metrics(self):
        """Test all metrics are returned."""
        image1 = np.random.rand(1, 64, 64).astype(np.float32)
        image2 = image1 + np.random.randn(*image1.shape).astype(np.float32) * 0.05
        image2 = np.clip(image2, 0, 1)

        metrics = calculate_metrics(image1, image2)
        assert 'mse' in metrics
        assert 'psnr' in metrics
        assert 'ssim' in metrics

    def test_metrics_types(self):
        """Test metric values are correct types."""
        image1 = np.random.rand(1, 32, 32).astype(np.float32)
        image2 = np.random.rand(1, 32, 32).astype(np.float32)

        metrics = calculate_metrics(image1, image2)
        assert isinstance(metrics['mse'], float)
        assert isinstance(metrics['psnr'], float)
        assert isinstance(metrics['ssim'], float)


class TestMetricTracker:
    """Test suite for MetricTracker."""

    def test_update(self):
        """Test metric tracking."""
        tracker = MetricTracker(window_size=5)
        tracker.update({'loss': 1.0, 'psnr': 20.0})
        assert tracker.get_current('loss') == 1.0
        assert tracker.get_current('psnr') == 20.0

    def test_moving_average(self):
        """Test moving average calculation."""
        tracker = MetricTracker(window_size=3)
        tracker.update({'loss': 1.0})
        tracker.update({'loss': 2.0})
        tracker.update({'loss': 3.0})

        avg = tracker.get_average('loss')
        assert abs(avg - 2.0) < 1e-6

    def test_window_size(self):
        """Test window size limit."""
        tracker = MetricTracker(window_size=2)
        tracker.update({'loss': 1.0})
        tracker.update({'loss': 2.0})
        tracker.update({'loss': 3.0})

        # Window should only contain last 2 values
        avg = tracker.get_average('loss')
        assert abs(avg - 2.5) < 1e-6  # (2 + 3) / 2

    def test_summary(self):
        """Test summary generation."""
        tracker = MetricTracker(window_size=5)
        tracker.update({'loss': 1.0, 'psnr': 20.0})

        summary = tracker.get_summary()
        assert 'loss_current' in summary
        assert 'loss_avg' in summary
        assert 'psnr_current' in summary
        assert 'psnr_avg' in summary

    def test_empty_tracker(self):
        """Test empty tracker returns 0."""
        tracker = MetricTracker()
        assert tracker.get_current('loss') == 0.0
        assert tracker.get_average('loss') == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
