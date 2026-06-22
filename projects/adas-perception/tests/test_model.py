"""
模型模块测试
"""

import pytest
import torch
import numpy as np
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.models.pointpillars import PointPillars, PillarEncoder, Backbone2D, FPN, DetectionHead
from src.models.backbone import ResNet18, ResNet18WithSE, VGG16, MobileNetV2


class TestPillarEncoder:
    """Pillar 编码器测试"""

    def setup_method(self):
        """测试前准备"""
        self.voxel_size = [0.16, 0.16, 4]
        self.point_cloud_range = [-40, -40, -3, 40, 40, 1]
        self.encoder = PillarEncoder(
            voxel_size=self.voxel_size,
            point_cloud_range=self.point_cloud_range,
            max_points_per_pillar=32,
            max_pillars=12000
        )

    def test_init(self):
        """测试初始化"""
        assert self.encoder.voxel_size == self.voxel_size
        assert self.encoder.point_cloud_range == self.point_cloud_range
        assert self.encoder.max_points_per_pillar == 32
        assert self.encoder.max_pillars == 12000

    def test_forward(self):
        """测试前向传播"""
        # 创建模拟输入
        batch_size = 2
        num_points = 1000
        points = torch.randn(batch_size, num_points, 4)

        # 前向传播
        output = self.encoder(points)

        # 验证输出形状
        assert output.shape[0] == batch_size
        assert output.shape[1] == 64  # out_channels


class TestBackbone2D:
    """2D 骨干网络测试"""

    def setup_method(self):
        """测试前准备"""
        self.backbone = Backbone2D(in_channels=64)

    def test_forward(self):
        """测试前向传播"""
        # 创建模拟输入
        x = torch.randn(2, 64, 200, 176)

        # 前向传播
        outputs = self.backbone(x)

        # 验证输出
        assert len(outputs) == 3  # 三个尺度的特征图

        # 验证特征图尺寸
        assert outputs[0].shape[1] == 64
        assert outputs[1].shape[1] == 128
        assert outputs[2].shape[1] == 256

        # 验证分辨率
        assert outputs[0].shape[2] == x.shape[2] // 2
        assert outputs[1].shape[2] == x.shape[2] // 4
        assert outputs[2].shape[2] == x.shape[2] // 8


class TestFPN:
    """特征金字塔网络测试"""

    def setup_method(self):
        """测试前准备"""
        self.fpn = FPN(
            in_channels_list=[64, 128, 256],
            out_channels=64
        )

    def test_forward(self):
        """测试前向传播"""
        # 创建模拟输入
        features = [
            torch.randn(2, 64, 200, 176),
            torch.randn(2, 128, 100, 88),
            torch.randn(2, 256, 50, 44)
        ]

        # 前向传播
        outputs = self.fpn(features)

        # 验证输出
        assert len(outputs) == 3

        # 验证输出通道数
        for output in outputs:
            assert output.shape[1] == 64

        # 验证分辨率
        assert outputs[0].shape[2] == 200
        assert outputs[1].shape[2] == 100
        assert outputs[2].shape[2] == 50


class TestDetectionHead:
    """检测头测试"""

    def setup_method(self):
        """测试前准备"""
        self.head = DetectionHead(
            in_channels=64,
            num_classes=3,
            num_anchors_per_location=2
        )

    def test_forward(self):
        """测试前向传播"""
        # 创建模拟输入
        x = torch.randn(2, 64, 200, 176)

        # 前向传播
        cls_score, bbox_pred, dir_pred = self.head(x)

        # 验证输出形状
        assert cls_score.shape[1] == 2 * 3  # num_anchors * num_classes
        assert bbox_pred.shape[1] == 2 * 7  # num_anchors * 7
        assert dir_pred.shape[1] == 2 * 2   # num_anchors * 2


class TestPointPillars:
    """PointPillars 模型测试"""

    def setup_method(self):
        """测试前准备"""
        self.model = PointPillars(
            voxel_size=[0.16, 0.16, 4],
            point_cloud_range=[-40, -40, -3, 40, 40, 1],
            num_classes=3,
            num_anchors_per_location=2
        )

    def test_model_init(self):
        """测试模型初始化"""
        assert self.model is not None
        assert isinstance(self.model, PointPillars)

    def test_forward(self):
        """测试前向传播"""
        # 创建模拟输入
        batch_size = 2
        num_points = 1000
        points = torch.randn(batch_size, num_points, 4)

        # 前向传播
        output = self.model(points)

        # 验证输出
        assert 'cls_score' in output
        assert 'bbox_pred' in output
        assert 'dir_pred' in output

    def test_parameters(self):
        """测试模型参数"""
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(
            p.numel() for p in self.model.parameters() if p.requires_grad
        )

        # 验证参数数量合理
        assert total_params > 0
        assert trainable_params > 0

    def test_model_structure(self):
        """测试模型结构"""
        # 验证子模块
        assert hasattr(self.model, 'pillar_encoder')
        assert hasattr(self.model, 'backbone')
        assert hasattr(self.model, 'fpn')
        assert hasattr(self.model, 'detection_head')


class TestBackbone:
    """骨干网络测试"""

    def test_resnet18(self):
        """测试 ResNet-18"""
        backbone = ResNet18(in_channels=64)

        # 创建模拟输入
        x = torch.randn(2, 64, 200, 176)

        # 前向传播
        outputs = backbone(x)

        # 验证输出
        assert len(outputs) == 4
        assert outputs[0].shape[1] == 64
        assert outputs[1].shape[1] == 128
        assert outputs[2].shape[1] == 256
        assert outputs[3].shape[1] == 512

    def test_resnet18_se(self):
        """测试带 SE 模块的 ResNet-18"""
        backbone = ResNet18WithSE(in_channels=64)

        # 创建模拟输入
        x = torch.randn(2, 64, 200, 176)

        # 前向传播
        outputs = backbone(x)

        # 验证输出
        assert len(outputs) == 4

    def test_vgg16(self):
        """测试 VGG-16"""
        backbone = VGG16(in_channels=64)

        # 创建模拟输入
        x = torch.randn(2, 64, 200, 176)

        # 前向传播
        output = backbone(x)

        # 验证输出形状
        assert output.shape[1] == 512
        assert output.shape[2] == 200 // 32
        assert output.shape[3] == 176 // 32

    def test_mobilenet_v2(self):
        """测试 MobileNetV2"""
        backbone = MobileNetV2(in_channels=64)

        # 创建模拟输入
        x = torch.randn(2, 64, 200, 176)

        # 前向传播
        output = backbone(x)

        # 验证输出形状
        assert output.shape[1] == 1280


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
