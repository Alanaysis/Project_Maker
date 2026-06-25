"""
模型架构测试。

测试 PoseEstimationNet, SimplePoseNet, LightweightBackbone 等模块。
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.model import (
    PoseEstimationNet,
    SimplePoseNet,
    LightweightBackbone,
    ConvBlock,
    ResidualBlock,
    HeatmapHead,
)


class TestConvBlock:
    """ConvBlock 测试。"""

    def test_output_shape(self):
        """测试输出形状。"""
        block = ConvBlock(3, 64)
        x = torch.randn(2, 3, 32, 32)
        out = block(x)
        assert out.shape == (2, 64, 32, 32)

    def test_stride(self):
        """测试步长。"""
        block = ConvBlock(3, 64, stride=2)
        x = torch.randn(2, 3, 64, 64)
        out = block(x)
        assert out.shape == (2, 64, 32, 32)

    def test_different_channels(self):
        """测试不同通道数。"""
        for in_ch, out_ch in [(1, 16), (3, 32), (64, 128), (128, 256)]:
            block = ConvBlock(in_ch, out_ch)
            x = torch.randn(1, in_ch, 16, 16)
            out = block(x)
            assert out.shape[1] == out_ch


class TestResidualBlock:
    """ResidualBlock 测试。"""

    def test_output_shape(self):
        """测试输出形状。"""
        block = ResidualBlock(64)
        x = torch.randn(2, 64, 32, 32)
        out = block(x)
        assert out.shape == (2, 64, 32, 32)

    def test_residual_connection(self):
        """测试残差连接。"""
        block = ResidualBlock(32)
        x = torch.randn(1, 32, 16, 16)
        out = block(x)
        # 输出应该不为零（残差连接保证梯度流）
        assert out.abs().sum() > 0


class TestLightweightBackbone:
    """LightweightBackbone 测试。"""

    def test_output_shape(self):
        """测试输出形状。"""
        backbone = LightweightBackbone(3)
        x = torch.randn(2, 3, 256, 256)
        out = backbone(x)
        # 输出应该是输入的 1/4
        assert out.shape == (2, 256, 64, 64)

    def test_different_input_sizes(self):
        """测试不同输入尺寸。"""
        backbone = LightweightBackbone(3)
        for size in [128, 256, 384]:
            x = torch.randn(1, 3, size, size)
            out = backbone(x)
            assert out.shape[1] == 256
            assert out.shape[2] == size // 4
            assert out.shape[3] == size // 4

    def test_gradient_flow(self):
        """测试梯度流。"""
        backbone = LightweightBackbone(3)
        x = torch.randn(1, 3, 128, 128, requires_grad=True)
        out = backbone(x)
        loss = out.sum()
        loss.backward()
        assert x.grad is not None
        assert x.grad.abs().sum() > 0


class TestHeatmapHead:
    """HeatmapHead 测试。"""

    def test_output_shape(self):
        """测试输出形状。"""
        head = HeatmapHead(in_channels=256, num_keypoints=17)
        x = torch.randn(2, 256, 64, 64)
        out = head(x)
        assert out.shape[0] == 2
        assert out.shape[1] == 17

    def test_different_keypoints(self):
        """测试不同关键点数量。"""
        for num_kp in [5, 10, 17, 25]:
            head = HeatmapHead(in_channels=128, num_keypoints=num_kp)
            x = torch.randn(1, 128, 32, 32)
            out = head(x)
            assert out.shape[1] == num_kp


class TestPoseEstimationNet:
    """PoseEstimationNet 测试。"""

    def test_output_shape(self):
        """测试输出形状。"""
        model = PoseEstimationNet(num_keypoints=17, input_size=256, heatmap_size=64)
        x = torch.randn(2, 3, 256, 256)
        out = model(x)
        assert out.shape[0] == 2
        assert out.shape[1] == 17
        assert out.shape[2] == 64
        assert out.shape[3] == 64

    def test_different_num_keypoints(self):
        """测试不同关键点数量。"""
        for num_kp in [5, 10, 17]:
            model = PoseEstimationNet(num_keypoints=num_kp, input_size=128, heatmap_size=32)
            x = torch.randn(1, 3, 128, 128)
            out = model(x)
            assert out.shape[1] == num_kp

    def test_predict_keypoints(self):
        """测试关键点预测。"""
        model = PoseEstimationNet(num_keypoints=17, input_size=128, heatmap_size=32)
        x = torch.randn(2, 3, 128, 128)
        keypoints, confidence = model.predict_keypoints(x)
        assert keypoints.shape == (2, 17, 2)
        assert confidence.shape == (2, 17)
        # 坐标应该在 [0, 1] 范围内
        assert keypoints.min() >= 0.0
        assert keypoints.max() <= 1.0

    def test_gradient_flow(self):
        """测试梯度流。"""
        model = PoseEstimationNet(num_keypoints=17, input_size=128, heatmap_size=32)
        x = torch.randn(1, 3, 128, 128, requires_grad=True)
        out = model(x)
        loss = out.sum()
        loss.backward()
        assert x.grad is not None


class TestSimplePoseNet:
    """SimplePoseNet 测试。"""

    def test_output_shape(self):
        """测试输出形状。"""
        model = SimplePoseNet(num_keypoints=17, input_size=128)
        x = torch.randn(2, 3, 128, 128)
        out = model(x)
        assert out.shape[0] == 2
        assert out.shape[1] == 17

    def test_single_batch(self):
        """测试单样本批次。"""
        model = SimplePoseNet(num_keypoints=10, input_size=64)
        x = torch.randn(1, 3, 64, 64)
        out = model(x)
        assert out.shape[0] == 1
        assert out.shape[1] == 10

    def test_parameter_count(self):
        """测试参数量。"""
        model = SimplePoseNet(num_keypoints=17, input_size=128)
        num_params = sum(p.numel() for p in model.parameters())
        # 简化版模型参数量应该相对较少
        assert num_params < 10_000_000  # < 10M
