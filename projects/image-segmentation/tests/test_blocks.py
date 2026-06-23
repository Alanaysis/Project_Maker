"""
Tests for U-Net building blocks (DoubleConv, Down, Up).
"""

import sys
import os

import pytest
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.blocks import DoubleConv, Down, Up


class TestDoubleConv:
    """Test suite for DoubleConv block."""

    def test_output_shape(self):
        """DoubleConv should preserve spatial dimensions."""
        block = DoubleConv(3, 64)
        x = torch.randn(1, 3, 128, 128)
        out = block(x)
        assert out.shape == (1, 64, 128, 128)

    def test_batch_dimension(self):
        """DoubleConv should handle batch dimension correctly."""
        block = DoubleConv(3, 32)
        x = torch.randn(4, 3, 64, 64)
        out = block(x)
        assert out.shape[0] == 4

    def test_custom_mid_channels(self):
        """DoubleConv should support custom intermediate channels."""
        block = DoubleConv(3, 64, mid_channels=32)
        x = torch.randn(1, 3, 64, 64)
        out = block(x)
        assert out.shape == (1, 64, 64, 64)

    def test_no_batch_norm(self):
        """DoubleConv should work without batch normalization."""
        block = DoubleConv(3, 64, use_batch_norm=False)
        x = torch.randn(1, 3, 64, 64)
        out = block(x)
        assert out.shape == (1, 64, 64, 64)

    def test_gradient_flow(self):
        """DoubleConv should allow gradients to flow."""
        block = DoubleConv(3, 16)
        x = torch.randn(1, 3, 32, 32, requires_grad=True)
        out = block(x)
        loss = out.sum()
        loss.backward()
        assert x.grad is not None
        assert x.grad.shape == x.shape


class TestDown:
    """Test suite for Down (encoder) block."""

    def test_output_shape(self):
        """Down should halve spatial dimensions and change channels."""
        block = Down(64, 128)
        x = torch.randn(1, 64, 128, 128)
        out = block(x)
        assert out.shape == (1, 128, 64, 64)

    def test_spatial_reduction(self):
        """Down should reduce spatial size by exactly 2x."""
        block = Down(32, 64)
        x = torch.randn(1, 32, 256, 256)
        out = block(x)
        assert out.shape[2] == 128
        assert out.shape[3] == 128

    def test_batch_handling(self):
        """Down should handle batch dimension correctly."""
        block = Down(16, 32)
        x = torch.randn(8, 16, 64, 64)
        out = block(x)
        assert out.shape[0] == 8


class TestUp:
    """Test suite for Up (decoder) block."""

    def test_bilinear_upsampling(self):
        """Up with bilinear should double spatial dimensions."""
        # in_channels=256 from lower level, out_channels=128, skip_channels=128
        # After bilinear upsample: 256 channels
        # After concat with skip: 256 + 128 = 384 channels -> DoubleConv -> 128
        block = Up(256, 128, skip_channels=128, use_bilinear=True)
        x = torch.randn(1, 256, 32, 32)
        skip = torch.randn(1, 128, 64, 64)
        out = block(x, skip)
        assert out.shape == (1, 128, 64, 64)

    def test_transpose_conv_upsampling(self):
        """Up with ConvTranspose2d should double spatial dimensions."""
        # in_channels=256, after ConvTranspose2d: 128 channels
        # After concat with skip: 128 + 128 = 256 channels -> DoubleConv -> 128
        block = Up(256, 128, skip_channels=128, use_bilinear=False)
        x = torch.randn(1, 256, 32, 32)
        skip = torch.randn(1, 128, 64, 64)
        out = block(x, skip)
        assert out.shape == (1, 128, 64, 64)

    def test_size_mismatch_padding(self):
        """Up should handle odd-dimension inputs with padding."""
        block = Up(256, 128, skip_channels=128, use_bilinear=True)
        x = torch.randn(1, 256, 33, 33)
        skip = torch.randn(1, 128, 65, 65)
        out = block(x, skip)
        assert out.shape == (1, 128, 65, 65)

    def test_gradient_flow(self):
        """Up should allow gradients to flow through both paths."""
        block = Up(128, 64, skip_channels=64, use_bilinear=True)
        x = torch.randn(1, 128, 16, 16, requires_grad=True)
        skip = torch.randn(1, 64, 32, 32, requires_grad=True)
        out = block(x, skip)
        loss = out.sum()
        loss.backward()
        assert x.grad is not None
        assert skip.grad is not None

    def test_no_skip(self):
        """Up should work with skip_channels=0."""
        block = Up(128, 64, skip_channels=0, use_bilinear=True)
        x = torch.randn(1, 128, 16, 16)
        skip = torch.randn(1, 0, 32, 32)
        out = block(x, skip)
        assert out.shape == (1, 64, 32, 32)
