"""
模型测试

测试模型相关的功能:
- Backbone 前向传播
- Neck 前向传播
- Head 前向传播
- YOLO 模型完整测试
"""

import pytest
import torch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.backbone import CSPDarknet
from src.models.neck import PANet
from src.models.head import DetectHead
from src.models.yolo import YOLOv8Tiny


class TestBackbone:
    """测试骨干网络"""

    def test_forward(self):
        """测试前向传播"""
        model = CSPDarknet(depth_multiple=0.33, width_multiple=0.25)
        x = torch.randn(2, 3, 640, 640)

        with torch.no_grad():
            outputs = model(x)

        assert len(outputs) == 3
        assert outputs[0].shape == (2, 64, 80, 80)
        assert outputs[1].shape == (2, 128, 40, 40)
        assert outputs[2].shape == (2, 256, 20, 20)

    def test_parameter_count(self):
        """测试参数量"""
        model = CSPDarknet(depth_multiple=0.33, width_multiple=0.25)
        params = sum(p.numel() for p in model.parameters())
        assert params > 0
        assert params < 10_000_000  # 参数量应该小于 10M


class TestNeck:
    """测试特征融合网络"""

    def test_forward(self):
        """测试前向传播"""
        neck = PANet(
            in_channels_list=[128, 256, 512],
            out_channels_list=[128, 256, 512],
            depth_multiple=0.33
        )

        p3 = torch.randn(2, 128, 80, 80)
        p4 = torch.randn(2, 256, 40, 40)
        p5 = torch.randn(2, 512, 20, 20)

        with torch.no_grad():
            outputs = neck([p3, p4, p5])

        assert len(outputs) == 3
        assert outputs[0].shape == (2, 128, 80, 80)
        assert outputs[1].shape == (2, 256, 40, 40)
        assert outputs[2].shape == (2, 512, 20, 20)


class TestHead:
    """测试检测头"""

    def test_forward_train(self):
        """测试训练模式前向传播"""
        head = DetectHead(
            in_channels_list=[128, 256, 512],
            num_classes=5,
            reg_max=16
        )

        head.train()
        features = [
            torch.randn(2, 128, 80, 80),
            torch.randn(2, 256, 40, 40),
            torch.randn(2, 512, 20, 20)
        ]

        with torch.no_grad():
            outputs = head(features)

        assert 'cls_pred' in outputs
        assert 'reg_pred' in outputs
        assert 'obj_pred' in outputs

    def test_forward_eval(self):
        """测试推理模式前向传播"""
        head = DetectHead(
            in_channels_list=[128, 256, 512],
            num_classes=5,
            reg_max=16
        )

        head.eval()
        features = [
            torch.randn(2, 128, 80, 80),
            torch.randn(2, 256, 40, 40),
            torch.randn(2, 512, 20, 20)
        ]

        with torch.no_grad():
            outputs = head(features)

        assert 'boxes' in outputs
        assert 'scores' in outputs


class TestYOLO:
    """测试 YOLO 模型"""

    def test_forward_train(self):
        """测试训练模式"""
        model = YOLOv8Tiny(num_classes=5)
        model.train()

        images = torch.randn(2, 3, 640, 640)
        targets = [
            {
                'boxes': torch.tensor([[100, 100, 200, 200]]),
                'labels': torch.tensor([0])
            }
            for _ in range(2)
        ]

        with torch.no_grad():
            outputs = model(images, targets)

        assert 'total_loss' in outputs
        assert 'cls_loss' in outputs

    def test_forward_eval(self):
        """测试推理模式"""
        model = YOLOv8Tiny(num_classes=5)
        model.eval()

        images = torch.randn(2, 3, 640, 640)

        with torch.no_grad():
            outputs = model(images)

        assert 'boxes' in outputs
        assert 'scores' in outputs

    def test_predict(self):
        """测试单张预测"""
        model = YOLOv8Tiny(num_classes=5)

        image = torch.randn(3, 640, 640)
        result = model.predict(image, conf_threshold=0.1)

        assert 'boxes' in result
        assert 'scores' in result
        assert 'labels' in result

    def test_parameter_count(self):
        """测试参数量"""
        model = YOLOv8Tiny(num_classes=5)
        params = sum(p.numel() for p in model.parameters())
        assert params > 0
        print(f"YOLOv8-Tiny 参数量: {params:,}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
