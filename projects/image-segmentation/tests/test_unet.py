"""
Tests for the full U-Net model.
"""

import sys
import os

import pytest
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.unet import UNet


class TestUNet:
    """Test suite for the full UNet model."""

    def test_default_config_output_shape(self):
        """UNet with default config should preserve spatial dimensions."""
        model = UNet(in_channels=3, out_channels=1, base_channels=64, n_levels=4)
        x = torch.randn(1, 3, 256, 256)
        out = model(x)
        assert out.shape == (1, 1, 256, 256)

    def test_small_input(self):
        """UNet should handle small input sizes."""
        model = UNet(in_channels=3, out_channels=1, base_channels=16, n_levels=2)
        x = torch.randn(1, 3, 64, 64)
        out = model(x)
        assert out.shape == (1, 1, 64, 64)

    def test_multi_class_output(self):
        """UNet should support multiple output classes."""
        model = UNet(in_channels=3, out_channels=5, base_channels=32, n_levels=3)
        x = torch.randn(1, 3, 128, 128)
        out = model(x)
        assert out.shape == (1, 5, 128, 128)

    def test_grayscale_input(self):
        """UNet should handle single-channel input."""
        model = UNet(in_channels=1, out_channels=1, base_channels=16, n_levels=2)
        x = torch.randn(1, 1, 64, 64)
        out = model(x)
        assert out.shape == (1, 1, 64, 64)

    def test_batch_processing(self):
        """UNet should handle batch dimension correctly."""
        model = UNet(in_channels=3, out_channels=1, base_channels=16, n_levels=2)
        x = torch.randn(4, 3, 64, 64)
        out = model(x)
        assert out.shape[0] == 4

    def test_predict_method(self):
        """UNet.predict should return binary masks."""
        model = UNet(in_channels=3, out_channels=1, base_channels=16, n_levels=2)
        x = torch.randn(1, 3, 64, 64)
        mask = model.predict(x)
        assert mask.shape == (1, 1, 64, 64)
        # Should be binary (0 or 1)
        assert mask.min() >= 0.0
        assert mask.max() <= 1.0
        unique_values = torch.unique(mask)
        assert len(unique_values) <= 2

    def test_predict_multiclass(self):
        """UNet.predict should work for multi-class output."""
        model = UNet(in_channels=3, out_channels=3, base_channels=16, n_levels=2)
        x = torch.randn(1, 3, 64, 64)
        mask = model.predict(x)
        assert mask.shape == (1, 3, 64, 64)

    def test_count_parameters(self):
        """UNet.count_parameters should return a positive integer."""
        model = UNet(in_channels=3, out_channels=1, base_channels=64, n_levels=4)
        n_params = model.count_parameters()
        assert isinstance(n_params, int)
        assert n_params > 0
        # U-Net with default config should have ~31M parameters
        assert n_params > 1_000_000

    def test_gradient_flow(self):
        """UNet should allow gradients to flow through the entire network."""
        model = UNet(in_channels=3, out_channels=1, base_channels=16, n_levels=2)
        x = torch.randn(1, 3, 64, 64, requires_grad=True)
        out = model(x)
        loss = out.sum()
        loss.backward()
        assert x.grad is not None
        assert x.grad.shape == x.shape

    def test_bilinear_vs_transpose(self):
        """Both upsampling methods should produce correct output."""
        for use_bilinear in [True, False]:
            model = UNet(
                in_channels=3,
                out_channels=1,
                base_channels=16,
                n_levels=2,
                use_bilinear=use_bilinear,
            )
            x = torch.randn(1, 3, 64, 64)
            out = model(x)
            assert out.shape == (1, 1, 64, 64), f"Failed for use_bilinear={use_bilinear}"

    def test_no_batch_norm(self):
        """UNet should work without batch normalization."""
        model = UNet(
            in_channels=3,
            out_channels=1,
            base_channels=16,
            n_levels=2,
            use_batch_norm=False,
        )
        x = torch.randn(1, 3, 64, 64)
        out = model(x)
        assert out.shape == (1, 1, 64, 64)

    def test_deterministic_output(self):
        """UNet should produce deterministic output in eval mode."""
        model = UNet(in_channels=3, out_channels=1, base_channels=16, n_levels=2)
        model.eval()
        x = torch.randn(1, 3, 64, 64)
        out1 = model(x)
        out2 = model(x)
        assert torch.allclose(out1, out2)

    def test_repr(self):
        """UNet should have a readable string representation."""
        model = UNet(in_channels=3, out_channels=1, base_channels=16, n_levels=2)
        repr_str = repr(model)
        assert "UNet" in repr_str
        assert "in_channels=3" in repr_str
        assert "out_channels=1" in repr_str
