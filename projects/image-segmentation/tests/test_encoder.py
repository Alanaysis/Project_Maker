"""
Tests for the U-Net Encoder module.
"""

import sys
import os

import pytest
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.encoder import Encoder


class TestEncoder:
    """Test suite for Encoder."""

    def test_default_config_output_shapes(self):
        """Encoder with default config should produce correct shapes."""
        encoder = Encoder(in_channels=3, base_channels=64, n_levels=4)
        x = torch.randn(1, 3, 256, 256)
        skips, bottleneck = encoder(x)

        assert len(skips) == 4
        assert skips[0].shape == (1, 64, 256, 256)
        assert skips[1].shape == (1, 128, 128, 128)
        assert skips[2].shape == (1, 256, 64, 64)
        assert skips[3].shape == (1, 512, 32, 32)
        assert bottleneck.shape == (1, 1024, 16, 16)

    def test_two_level_encoder(self):
        """Encoder with 2 levels should produce 2 skip connections."""
        encoder = Encoder(in_channels=3, base_channels=32, n_levels=2)
        x = torch.randn(1, 3, 64, 64)
        skips, bottleneck = encoder(x)

        assert len(skips) == 2
        assert skips[0].shape == (1, 32, 64, 64)
        assert skips[1].shape == (1, 64, 32, 32)
        assert bottleneck.shape == (1, 128, 16, 16)

    def test_three_level_encoder(self):
        """Encoder with 3 levels should produce 3 skip connections."""
        encoder = Encoder(in_channels=1, base_channels=16, n_levels=3)
        x = torch.randn(1, 1, 128, 128)
        skips, bottleneck = encoder(x)

        assert len(skips) == 3
        assert skips[0].shape == (1, 16, 128, 128)
        assert skips[1].shape == (1, 32, 64, 64)
        assert skips[2].shape == (1, 64, 32, 32)
        assert bottleneck.shape == (1, 128, 16, 16)

    def test_single_channel_input(self):
        """Encoder should handle single-channel (grayscale) input."""
        encoder = Encoder(in_channels=1, base_channels=32, n_levels=2)
        x = torch.randn(1, 1, 64, 64)
        skips, bottleneck = encoder(x)
        assert skips[0].shape[1] == 32

    def test_batch_handling(self):
        """Encoder should handle batch dimension correctly."""
        encoder = Encoder(in_channels=3, base_channels=16, n_levels=2)
        x = torch.randn(4, 3, 64, 64)
        skips, bottleneck = encoder(x)
        assert skips[0].shape[0] == 4
        assert bottleneck.shape[0] == 4

    def test_skip_channels_property(self):
        """Encoder.skip_channels should return correct channel list."""
        encoder = Encoder(in_channels=3, base_channels=64, n_levels=4)
        assert encoder.skip_channels == [64, 128, 256, 512]

    def test_no_batch_norm(self):
        """Encoder should work without batch normalization."""
        encoder = Encoder(in_channels=3, base_channels=32, n_levels=2, use_batch_norm=False)
        x = torch.randn(1, 3, 64, 64)
        skips, bottleneck = encoder(x)
        assert len(skips) == 2

    def test_gradient_flow(self):
        """Encoder should allow gradients to flow."""
        encoder = Encoder(in_channels=3, base_channels=16, n_levels=2)
        x = torch.randn(1, 3, 64, 64, requires_grad=True)
        skips, bottleneck = encoder(x)
        loss = bottleneck.sum()
        for skip in skips:
            loss += skip.sum()
        loss.backward()
        assert x.grad is not None
