"""
损失函数测试
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.loss import SetCriterion, sigmoid_focal_loss
from src.matcher import build_matcher


class TestLoss:
    """损失函数测试类"""

    def test_set_criterion_forward(self):
        """测试集合预测损失"""
        num_classes = 5
        matcher = build_matcher(cost_class=1, cost_bbox=5, cost_giou=2)
        weight_dict = {'loss_ce': 1, 'loss_bbox': 5, 'loss_giou': 2}
        criterion = SetCriterion(num_classes, matcher, weight_dict, eos_coef=0.1,
                                losses=['labels', 'boxes'])

        # 模拟输出
        outputs = {
            'pred_logits': torch.randn(2, 100, num_classes + 1),
            'pred_boxes': torch.rand(2, 100, 4) * 0.5 + 0.25
        }

        targets = [
            {
                'labels': torch.tensor([1, 2, 3]),
                'boxes': torch.tensor([[0.5, 0.5, 0.2, 0.2],
                                      [0.3, 0.3, 0.1, 0.1],
                                      [0.7, 0.7, 0.15, 0.15]])
            },
            {
                'labels': torch.tensor([4, 0]),
                'boxes': torch.tensor([[0.4, 0.4, 0.2, 0.2],
                                      [0.6, 0.6, 0.1, 0.1]])
            }
        ]

        losses = criterion(outputs, targets)

        assert 'loss_ce' in losses
        assert 'loss_bbox' in losses
        assert 'loss_giou' in losses
        assert all(isinstance(v.item(), float) for v in losses.values())

    def test_sigmoid_focal_loss(self):
        """测试Sigmoid Focal Loss"""
        inputs = torch.randn(10, 5)
        targets = torch.zeros(10, 5)
        targets[:, 0] = 1  # 第一个类别为正样本

        loss = sigmoid_focal_loss(inputs, targets, num_boxes=10)
        assert loss.item() > 0

    def test_loss_gradient(self):
        """测试损失函数梯度"""
        num_classes = 5
        matcher = build_matcher()
        weight_dict = {'loss_ce': 1, 'loss_bbox': 5, 'loss_giou': 2}
        criterion = SetCriterion(num_classes, matcher, weight_dict, eos_coef=0.1,
                                losses=['labels', 'boxes'])

        outputs = {
            'pred_logits': torch.randn(1, 10, num_classes + 1, requires_grad=True),
            'pred_boxes': torch.rand(1, 10, 4, requires_grad=True)
        }

        targets = [{
            'labels': torch.tensor([1, 2]),
            'boxes': torch.tensor([[0.5, 0.5, 0.2, 0.2], [0.3, 0.3, 0.1, 0.1]])
        }]

        losses = criterion(outputs, targets)
        total_loss = sum(losses.values())
        total_loss.backward()

        assert outputs['pred_logits'].grad is not None
        assert outputs['pred_boxes'].grad is not None

    def test_loss_with_aux_outputs(self):
        """测试带辅助输出的损失"""
        num_classes = 5
        matcher = build_matcher()
        weight_dict = {'loss_ce': 1, 'loss_bbox': 5, 'loss_giou': 2}
        criterion = SetCriterion(num_classes, matcher, weight_dict, eos_coef=0.1,
                                losses=['labels', 'boxes'])

        # 主输出
        outputs = {
            'pred_logits': torch.randn(1, 10, num_classes + 1),
            'pred_boxes': torch.rand(1, 10, 4),
            'aux_outputs': [
                {
                    'pred_logits': torch.randn(1, 10, num_classes + 1),
                    'pred_boxes': torch.rand(1, 10, 4)
                }
            ]
        }

        targets = [{
            'labels': torch.tensor([1, 2]),
            'boxes': torch.tensor([[0.5, 0.5, 0.2, 0.2], [0.3, 0.3, 0.1, 0.1]])
        }]

        losses = criterion(outputs, targets)
        assert 'loss_ce' in losses


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
