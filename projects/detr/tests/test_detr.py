"""
DETR模型测试
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.detr import DETR, build_detr
from src.utils import nested_tensor_from_tensor_list, NestedTensor
from src.loss import SetCriterion
from src.matcher import build_matcher


class TestDETR:
    """DETR模型测试类"""

    def test_detr_forward(self):
        """测试DETR前向传播"""
        model = build_detr(
            num_classes=5,
            num_queries=50,
            backbone_model='resnet18',
            hidden_dim=128,
            nhead=4,
            num_encoder_layers=2,
            num_decoder_layers=2
        )

        # 创建输入
        images = torch.randn(2, 3, 320, 320)

        outputs = model(images)

        assert 'pred_logits' in outputs
        assert 'pred_boxes' in outputs
        assert outputs['pred_logits'].shape == (2, 50, 6)  # 5 classes + 1 background
        assert outputs['pred_boxes'].shape == (2, 50, 4)

    def test_detr_with_nested_tensor(self):
        """测试DETR使用嵌套张量"""
        model = build_detr(num_classes=5, num_queries=50, hidden_dim=64, nhead=4,
                          num_encoder_layers=1, num_decoder_layers=1)

        images = torch.randn(2, 3, 320, 320)
        samples = nested_tensor_from_tensor_list([images[0], images[1]])

        outputs = model(samples)
        assert outputs['pred_logits'].shape == (2, 50, 6)

    def test_detr_with_aux_loss(self):
        """测试DETR带辅助损失"""
        model = build_detr(
            num_classes=5,
            num_queries=50,
            aux_loss=True,
            hidden_dim=64,
            nhead=4,
            num_encoder_layers=2,
            num_decoder_layers=2
        )

        images = torch.randn(2, 3, 320, 320)
        outputs = model(images)

        assert 'aux_outputs' in outputs
        assert len(outputs['aux_outputs']) == 1  # 2 decoder layers -> 1 aux output

    def test_detr_loss_integration(self):
        """测试DETR与损失函数的集成"""
        model = build_detr(
            num_classes=5,
            num_queries=50,
            hidden_dim=64,
            nhead=4,
            num_encoder_layers=1,
            num_decoder_layers=1
        )

        matcher = build_matcher()
        weight_dict = {'loss_ce': 1, 'loss_bbox': 5, 'loss_giou': 2}
        criterion = SetCriterion(5, matcher, weight_dict, eos_coef=0.1,
                                losses=['labels', 'boxes'])

        images = torch.randn(2, 3, 320, 320)
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

        outputs = model(images)
        losses = criterion(outputs, targets)

        assert all(v.item() > 0 for v in losses.values())

    def test_build_detr_default(self):
        """测试构建默认DETR"""
        model = build_detr()
        assert model.num_queries == 100

    def test_detr_gradient_flow(self):
        """测试梯度流动"""
        model = build_detr(
            num_classes=5,
            num_queries=50,
            hidden_dim=64,
            nhead=4,
            num_encoder_layers=1,
            num_decoder_layers=1
        )

        images = torch.randn(1, 3, 320, 320, requires_grad=True)
        outputs = model(images)

        loss = outputs['pred_logits'].sum() + outputs['pred_boxes'].sum()
        loss.backward()

        assert images.grad is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
