"""
Tests for Model Architecture
"""

import sys
import os
import torch
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.model.backbone import VGGBackbone, LightBackbone, ConvBNReLU
from src.model.neck import UNetNeck, FPNNeck
from src.model.head import EASTHead, DBHead


class TestConvBNReLU:
    """Test ConvBNReLU block."""

    def test_forward_shape(self):
        """Test output shape."""
        block = ConvBNReLU(3, 16)
        x = torch.randn(1, 3, 32, 32)
        out = block(x)
        assert out.shape == (1, 16, 32, 32)

    def test_different_kernel(self):
        """Test with different kernel size."""
        block = ConvBNReLU(3, 16, kernel_size=1, padding=0)
        x = torch.randn(1, 3, 32, 32)
        out = block(x)
        assert out.shape == (1, 16, 32, 32)


class TestVGGBackbone:
    """Test VGG-like backbone."""

    def test_output_shapes(self):
        """Test multi-scale output shapes."""
        backbone = VGGBackbone()
        x = torch.randn(1, 3, 256, 256)

        f1, f2, f3, f4, f5 = backbone(x)

        assert f1.shape == (1, 64, 128, 128)     # /2
        assert f2.shape == (1, 128, 64, 64)      # /4
        assert f3.shape == (1, 256, 32, 32)      # /8
        assert f4.shape == (1, 512, 16, 16)      # /16
        assert f5.shape == (1, 512, 8, 8)        # /32

    def test_batch_size(self):
        """Test with different batch sizes."""
        backbone = VGGBackbone()
        for bs in [1, 2, 4]:
            x = torch.randn(bs, 3, 128, 128)
            f1, f2, f3, f4, f5 = backbone(x)
            assert f1.shape[0] == bs

    def test_gradient_flow(self):
        """Test gradients flow through backbone."""
        backbone = VGGBackbone()
        x = torch.randn(1, 3, 64, 64, requires_grad=True)
        f1, f2, f3, f4, f5 = backbone(x)
        loss = f5.sum()
        loss.backward()
        assert x.grad is not None


class TestLightBackbone:
    """Test lightweight backbone."""

    def test_output_shapes(self):
        """Test multi-scale output shapes."""
        backbone = LightBackbone()
        x = torch.randn(1, 3, 256, 256)

        f1, f2, f3, f4, f5 = backbone(x)

        assert f1.shape == (1, 32, 128, 128)     # /2
        assert f2.shape == (1, 64, 64, 64)       # /4
        assert f3.shape == (1, 128, 32, 32)      # /8
        assert f4.shape == (1, 256, 16, 16)      # /16
        assert f5.shape == (1, 256, 8, 8)        # /32

    def test_fewer_parameters(self):
        """Test that light backbone has fewer parameters."""
        vgg = VGGBackbone()
        light = LightBackbone()

        vgg_params = sum(p.numel() for p in vgg.parameters())
        light_params = sum(p.numel() for p in light.parameters())

        assert light_params < vgg_params


class TestUNetNeck:
    """Test U-Net neck."""

    def test_output_shape(self):
        """Test neck output shape."""
        neck = UNetNeck(
            in_channels_list=[64, 128, 256, 512, 512],
            out_channels=32
        )

        # Create feature maps
        f1 = torch.randn(1, 64, 64, 64)
        f2 = torch.randn(1, 128, 32, 32)
        f3 = torch.randn(1, 256, 16, 16)
        f4 = torch.randn(1, 512, 8, 8)
        f5 = torch.randn(1, 512, 4, 4)

        out = neck([f1, f2, f3, f4, f5])
        assert out.shape == (1, 32, 64, 64)  # Same as f1

    def test_gradient_flow(self):
        """Test gradients flow through neck."""
        neck = UNetNeck(
            in_channels_list=[16, 32, 64],
            out_channels=8
        )

        f1 = torch.randn(1, 16, 16, 16, requires_grad=True)
        f2 = torch.randn(1, 32, 8, 8, requires_grad=True)
        f3 = torch.randn(1, 64, 4, 4, requires_grad=True)

        out = neck([f1, f2, f3])
        loss = out.sum()
        loss.backward()

        assert f1.grad is not None
        assert f2.grad is not None
        assert f3.grad is not None


class TestFPNNeck:
    """Test FPN neck."""

    def test_output_shape(self):
        """Test FPN output shape."""
        neck = FPNNeck(
            in_channels_list=[64, 128, 256, 512, 512],
            out_channels=32
        )

        f1 = torch.randn(1, 64, 64, 64)
        f2 = torch.randn(1, 128, 32, 32)
        f3 = torch.randn(1, 256, 16, 16)
        f4 = torch.randn(1, 512, 8, 8)
        f5 = torch.randn(1, 512, 4, 4)

        out = neck([f1, f2, f3, f4, f5])
        assert out.shape == (1, 32, 64, 64)


class TestEASTHead:
    """Test EAST detection head."""

    def test_rbox_output(self):
        """Test RBOX output shape."""
        head = EASTHead(in_channels=32, geo_type='rbox')
        x = torch.randn(1, 32, 64, 64)

        score, geo = head(x)

        assert score.shape == (1, 1, 64, 64)
        assert geo.shape == (1, 5, 64, 64)

    def test_quad_output(self):
        """Test QUAD output shape."""
        head = EASTHead(in_channels=32, geo_type='quad')
        x = torch.randn(1, 32, 64, 64)

        score, geo = head(x)

        assert score.shape == (1, 1, 64, 64)
        assert geo.shape == (1, 8, 64, 64)

    def test_score_range(self):
        """Test score output is in [0, 1]."""
        head = EASTHead(in_channels=16, geo_type='rbox')
        x = torch.randn(4, 16, 32, 32)

        score, _ = head(x)

        assert score.min() >= 0
        assert score.max() <= 1

    def test_geo_range(self):
        """Test geometry output is in [0, 1] (sigmoid)."""
        head = EASTHead(in_channels=16, geo_type='rbox')
        x = torch.randn(4, 16, 32, 32)

        _, geo = head(x)

        assert geo.min() >= 0
        assert geo.max() <= 1


class TestDBHead:
    """Test DBNet detection head."""

    def test_output_shapes(self):
        """Test DB head output shapes."""
        head = DBHead(in_channels=32, k=50)
        x = torch.randn(1, 32, 16, 16)

        prob, thresh, binary = head(x)

        assert prob.shape == (1, 1, 64, 64)    # Upsampled 4x
        assert thresh.shape == (1, 1, 64, 64)
        assert binary.shape == (1, 1, 64, 64)

    def test_prob_range(self):
        """Test probability output is in [0, 1]."""
        head = DBHead(in_channels=16, k=50)
        x = torch.randn(4, 16, 8, 8)

        prob, _, _ = head(x)

        assert prob.min() >= 0
        assert prob.max() <= 1

    def test_binary_range(self):
        """Test binary output is in [0, 1]."""
        head = DBHead(in_channels=16, k=50)
        x = torch.randn(4, 16, 8, 8)

        _, _, binary = head(x)

        assert binary.min() >= 0
        assert binary.max() <= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
