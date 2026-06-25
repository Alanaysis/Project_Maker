"""
深度估计模型测试
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.model import (
    ConvBlock,
    ResidualBlock,
    DepthEncoder,
    DepthDecoder,
    DepthEstimationNet,
    SimpleDepthNet,
    MultiScaleDepthNet,
    count_parameters,
    model_summary,
)


class TestConvBlock:
    """ConvBlock 测试"""

    def test_output_shape(self):
        """测试输出形状"""
        block = ConvBlock(3, 64)
        x = torch.randn(2, 3, 32, 32)
        out = block(x)
        assert out.shape == (2, 64, 32, 32)

    def test_stride(self):
        """测试步长"""
        block = ConvBlock(3, 64, stride=2)
        x = torch.randn(2, 3, 32, 32)
        out = block(x)
        assert out.shape == (2, 64, 16, 16)


class TestResidualBlock:
    """ResidualBlock 测试"""

    def test_output_shape(self):
        """测试输出形状"""
        block = ResidualBlock(64)
        x = torch.randn(2, 64, 32, 32)
        out = block(x)
        assert out.shape == (2, 64, 32, 32)

    def test_residual_connection(self):
        """测试残差连接"""
        block = ResidualBlock(64)
        x = torch.randn(1, 64, 16, 16)
        out = block(x)
        # 残差连接确保输出不全为零
        assert out.abs().sum() > 0


class TestDepthEncoder:
    """DepthEncoder 测试"""

    def test_output_shapes(self):
        """测试各层输出形状"""
        encoder = DepthEncoder(in_channels=3, base_channels=32)
        x = torch.randn(2, 3, 128, 128)
        features = encoder(x)

        assert len(features) == 5
        # stem: 1/4
        assert features[0].shape == (2, 32, 32, 32)
        # layer1: 1/8
        assert features[1].shape == (2, 64, 16, 16)
        # layer2: 1/16
        assert features[2].shape == (2, 128, 8, 8)
        # layer3: 1/32
        assert features[3].shape == (2, 256, 4, 4)
        # layer4: 1/64
        assert features[4].shape == (2, 512, 2, 2)


class TestDepthDecoder:
    """DepthDecoder 测试"""

    def test_output_shape(self):
        """测试输出形状"""
        encoder = DepthEncoder(in_channels=3, base_channels=32)
        decoder = DepthDecoder(base_channels=32)

        x = torch.randn(2, 3, 128, 128)
        features = encoder(x)
        depth = decoder(features)

        assert depth.shape[0] == 2
        assert depth.shape[1] == 1
        assert depth.shape[2] == 128
        assert depth.shape[3] == 128

    def test_output_range(self):
        """测试输出范围 [0, 1]"""
        encoder = DepthEncoder(in_channels=3, base_channels=32)
        decoder = DepthDecoder(base_channels=32)

        x = torch.randn(2, 3, 128, 128)
        features = encoder(x)
        depth = decoder(features)

        assert depth.min() >= 0
        assert depth.max() <= 1


class TestDepthEstimationNet:
    """DepthEstimationNet 测试"""

    def test_forward(self):
        """测试前向传播"""
        model = DepthEstimationNet(in_channels=3, base_channels=32)
        x = torch.randn(2, 3, 128, 128)
        depth = model(x)

        assert depth.shape == (2, 1, 128, 128)

    def test_output_range(self):
        """测试输出范围"""
        model = DepthEstimationNet(in_channels=3, base_channels=32)
        x = torch.randn(2, 3, 128, 128)
        depth = model(x)

        assert depth.min() >= 0
        assert depth.max() <= 1

    def test_gradient_flow(self):
        """测试梯度流"""
        model = DepthEstimationNet(in_channels=3, base_channels=32)
        x = torch.randn(2, 3, 128, 128)
        depth = model(x)
        loss = depth.mean()
        loss.backward()

        # 检查编码器梯度
        for param in model.encoder.parameters():
            if param.requires_grad:
                assert param.grad is not None

        # 检查解码器梯度
        for param in model.decoder.parameters():
            if param.requires_grad:
                assert param.grad is not None


class TestSimpleDepthNet:
    """SimpleDepthNet 测试"""

    def test_forward(self):
        """测试前向传播"""
        model = SimpleDepthNet()
        x = torch.randn(2, 3, 128, 128)
        depth = model(x)

        assert depth.shape == (2, 1, 128, 128)

    def test_output_range(self):
        """测试输出范围"""
        model = SimpleDepthNet()
        x = torch.randn(2, 3, 128, 128)
        depth = model(x)

        assert depth.min() >= 0
        assert depth.max() <= 1

    def test_different_sizes(self):
        """测试不同输入尺寸"""
        model = SimpleDepthNet()
        for size in [64, 96, 128]:
            x = torch.randn(1, 3, size, size)
            depth = model(x)
            assert depth.shape == (1, 1, size, size)


class TestMultiScaleDepthNet:
    """MultiScaleDepthNet 测试"""

    def test_output_scales(self):
        """测试多尺度输出"""
        model = MultiScaleDepthNet(in_channels=3, base_channels=32, num_scales=3)
        x = torch.randn(2, 3, 128, 128)
        depths = model(x)

        assert len(depths) == 3
        for depth in depths:
            assert depth.shape == (2, 1, 128, 128)

    def test_output_range(self):
        """测试输出范围"""
        model = MultiScaleDepthNet(in_channels=3, base_channels=32, num_scales=3)
        x = torch.randn(2, 3, 128, 128)
        depths = model(x)

        for depth in depths:
            assert depth.min() >= 0
            assert depth.max() <= 1


class TestUtilities:
    """工具函数测试"""

    def test_count_parameters(self):
        """测试参数计数"""
        model = SimpleDepthNet()
        params = count_parameters(model)
        assert params > 0

    def test_model_summary(self):
        """测试模型摘要"""
        model = SimpleDepthNet()
        summary = model_summary(model, input_size=(1, 3, 64, 64))
        assert "输入尺寸" in summary
        assert "参数量" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
