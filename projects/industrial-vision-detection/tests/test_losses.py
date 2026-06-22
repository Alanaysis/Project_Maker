"""
损失函数测试

测试损失函数相关的功能:
- Focal Loss
- CIoU Loss
- YOLO Loss
"""

import pytest
import torch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.losses import FocalLoss, CIoULoss, YOLOLoss


class TestFocalLoss:
    """测试 Focal Loss"""

    def test_forward(self):
        """测试前向传播"""
        loss_fn = FocalLoss(alpha=0.25, gamma=2.0)

        pred = torch.randn(4, 5)
        target = torch.randint(0, 2, (4, 5)).float()

        loss = loss_fn(pred, target)
        assert loss.dim() == 0  # 标量
        assert loss.item() >= 0

    def test_gradient(self):
        """测试梯度计算"""
        loss_fn = FocalLoss()

        pred = torch.randn(4, 5, requires_grad=True)
        target = torch.randint(0, 2, (4, 5)).float()

        loss = loss_fn(pred, target)
        loss.backward()

        assert pred.grad is not None
        assert pred.grad.shape == pred.shape

    def test_reduction(self):
        """测试不同的聚合方式"""
        pred = torch.randn(4, 5)
        target = torch.randint(0, 2, (4, 5)).float()

        # Mean reduction
        loss_mean = FocalLoss(reduction='mean')(pred, target)
        assert loss_mean.dim() == 0

        # Sum reduction
        loss_sum = FocalLoss(reduction='sum')(pred, target)
        assert loss_sum.dim() == 0

        # None reduction
        loss_none = FocalLoss(reduction='none')(pred, target)
        assert loss_none.shape == pred.shape


class TestCIoULoss:
    """测试 CIoU Loss"""

    def test_forward(self):
        """测试前向传播"""
        loss_fn = CIoULoss()

        pred_boxes = torch.tensor([[10, 10, 50, 50], [20, 20, 60, 60]]).float()
        target_boxes = torch.tensor([[15, 15, 55, 55], [25, 25, 65, 65]]).float()

        loss = loss_fn(pred_boxes, target_boxes)
        assert loss.dim() == 0
        assert loss.item() >= 0

    def test_gradient(self):
        """测试梯度计算"""
        loss_fn = CIoULoss()

        pred_boxes = torch.tensor([[10, 10, 50, 50]], requires_grad=True).float()
        target_boxes = torch.tensor([[15, 15, 55, 55]]).float()

        loss = loss_fn(pred_boxes, target_boxes)
        loss.backward()

        assert pred_boxes.grad is not None

    def test_perfect_overlap(self):
        """测试完美重叠的情况"""
        loss_fn = CIoULoss()

        boxes = torch.tensor([[10, 10, 50, 50]]).float()
        loss = loss_fn(boxes, boxes)

        assert loss.item() < 0.01  # 应该接近 0


class TestYOLOLoss:
    """测试 YOLO Loss"""

    def test_forward(self):
        """测试前向传播"""
        loss_fn = YOLOLoss(num_classes=5)

        # 创建模拟预测
        predictions = {
            'cls_pred': [torch.randn(2, 80, 80, 5) for _ in range(3)],
            'reg_pred': [torch.randn(2, 80, 80, 64) for _ in range(3)],
            'obj_pred': [torch.randn(2, 80, 80, 1) for _ in range(3)]
        }

        # 创建模拟目标
        targets = [
            {
                'boxes': torch.tensor([[100, 100, 200, 200]]),
                'labels': torch.tensor([0])
            }
            for _ in range(2)
        ]

        losses = loss_fn(predictions, targets)

        assert 'total_loss' in losses
        assert 'cls_loss' in losses
        assert 'box_loss' in losses
        assert 'obj_loss' in losses

    def test_loss_values(self):
        """测试损失值"""
        loss_fn = YOLOLoss(num_classes=5)

        predictions = {
            'cls_pred': [torch.randn(2, 80, 80, 5) for _ in range(3)],
            'reg_pred': [torch.randn(2, 80, 80, 64) for _ in range(3)],
            'obj_pred': [torch.randn(2, 80, 80, 1) for _ in range(3)]
        }

        targets = [
            {
                'boxes': torch.tensor([[100, 100, 200, 200]]),
                'labels': torch.tensor([0])
            }
            for _ in range(2)
        ]

        losses = loss_fn(predictions, targets)

        # 所有损失应该非负
        for key, value in losses.items():
            assert value.item() >= 0, f"{key} 应该非负"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
