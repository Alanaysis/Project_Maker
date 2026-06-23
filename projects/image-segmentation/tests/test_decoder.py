"""
Tests for the U-Net Decoder module.
"""

import sys
import os

import pytest
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.decoder import Decoder


class TestDecoder:
    """Test suite for Decoder."""

    def test_default_config_output_shape(self):
        """Decoder with default config should produce correct output shape."""
        decoder = Decoder(
            out_channels=1,
            skip_channels=[64, 128, 256, 512],
            base_channels=64,
            n_levels=4,
        )
        bottleneck = torch.randn(1, 1024, 16, 16)
        skips = [
            torch.randn(1, 64, 256, 256),
            torch.randn(1, 128, 128, 128),
            torch.randn(1, 256, 64, 64),
            torch.randn(1, 512, 32, 32),
        ]
        out = decoder(bottleneck, skips)
        assert out.shape == (1, 1, 256, 256)

    def test_two_level_decoder(self):
        """Decoder with 2 levels should upsample 2x."""
        decoder = Decoder(
            out_channels=1,
            skip_channels=[32, 64],
            base_channels=32,
            n_levels=2,
        )
        bottleneck = torch.randn(1, 128, 16, 16)
        skips = [
            torch.randn(1, 32, 64, 64),
            torch.randn(1, 64, 32, 32),
        ]
        out = decoder(bottleneck, skips)
        assert out.shape == (1, 1, 64, 64)

    def test_multi_class_output(self):
        """Decoder should support multiple output classes."""
        decoder = Decoder(
            out_channels=5,
            skip_channels=[64, 128],
            base_channels=64,
            n_levels=2,
        )
        bottleneck = torch.randn(1, 256, 16, 16)
        skips = [
            torch.randn(1, 64, 64, 64),
            torch.randn(1, 128, 32, 32),
        ]
        out = decoder(bottleneck, skips)
        assert out.shape == (1, 5, 64, 64)

    def test_bilinear_vs_transpose(self):
        """Both upsampling methods should produce correct shapes."""
        for use_bilinear in [True, False]:
            decoder = Decoder(
                out_channels=1,
                skip_channels=[32, 64],
                base_channels=32,
                n_levels=2,
                use_bilinear=use_bilinear,
            )
            bottleneck = torch.randn(1, 128, 16, 16)
            skips = [
                torch.randn(1, 32, 64, 64),
                torch.randn(1, 64, 32, 32),
            ]
            out = decoder(bottleneck, skips)
            assert out.shape == (1, 1, 64, 64), f"Failed for use_bilinear={use_bilinear}"

    def test_batch_handling(self):
        """Decoder should handle batch dimension correctly."""
        decoder = Decoder(
            out_channels=1,
            skip_channels=[32, 64],
            base_channels=32,
            n_levels=2,
        )
        bottleneck = torch.randn(4, 128, 16, 16)
        skips = [
            torch.randn(4, 32, 64, 64),
            torch.randn(4, 64, 32, 32),
        ]
        out = decoder(bottleneck, skips)
        assert out.shape[0] == 4

    def test_no_batch_norm(self):
        """Decoder should work without batch normalization."""
        decoder = Decoder(
            out_channels=1,
            skip_channels=[32, 64],
            base_channels=32,
            n_levels=2,
            use_batch_norm=False,
        )
        bottleneck = torch.randn(1, 128, 16, 16)
        skips = [
            torch.randn(1, 32, 64, 64),
            torch.randn(1, 64, 32, 32),
        ]
        out = decoder(bottleneck, skips)
        assert out.shape == (1, 1, 64, 64)

    def test_gradient_flow(self):
        """Decoder should allow gradients to flow through skip connections."""
        decoder = Decoder(
            out_channels=1,
            skip_channels=[32, 64],
            base_channels=32,
            n_levels=2,
        )
        bottleneck = torch.randn(1, 128, 16, 16, requires_grad=True)
        skips = [
            torch.randn(1, 32, 64, 64, requires_grad=True),
            torch.randn(1, 64, 32, 32, requires_grad=True),
        ]
        out = decoder(bottleneck, skips)
        loss = out.sum()
        loss.backward()
        assert bottleneck.grad is not None
        for skip in skips:
            assert skip.grad is not None
