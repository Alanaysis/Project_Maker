"""
匈牙利匹配测试
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.matcher import (
    HungarianMatcher, build_matcher,
    box_cxcywh_to_xyxy, box_iou, generalized_box_iou
)


class TestMatcher:
    """匈牙利匹配测试类"""

    def test_matcher_basic(self):
        """测试基本匹配功能"""
        matcher = HungarianMatcher(cost_class=1, cost_bbox=1, cost_giou=1)

        # 模拟输出
        outputs = {
            'pred_logits': torch.randn(2, 100, 91),  # (batch, queries, classes)
            'pred_boxes': torch.rand(2, 100, 4) * 0.5 + 0.25  # (batch, queries, 4)
        }

        # 模拟目标
        targets = [
            {
                'labels': torch.tensor([1, 2, 3]),
                'boxes': torch.tensor([[0.5, 0.5, 0.2, 0.2],
                                      [0.3, 0.3, 0.1, 0.1],
                                      [0.7, 0.7, 0.15, 0.15]])
            },
            {
                'labels': torch.tensor([4, 5]),
                'boxes': torch.tensor([[0.4, 0.4, 0.2, 0.2],
                                      [0.6, 0.6, 0.1, 0.1]])
            }
        ]

        indices = matcher(outputs, targets)

        assert len(indices) == 2  # 批次大小为2
        for pred_idx, target_idx in indices:
            assert len(pred_idx) == len(target_idx)

    def test_box_conversion(self):
        """测试边界框格式转换"""
        boxes = torch.tensor([[0.5, 0.5, 0.2, 0.4]])  # cx, cy, w, h
        xyxy = box_cxcywh_to_xyxy(boxes)

        expected = torch.tensor([[0.4, 0.3, 0.6, 0.7]])  # x1, y1, x2, y2
        assert torch.allclose(xyxy, expected, atol=1e-6)

    def test_box_iou(self):
        """测试IoU计算"""
        boxes1 = torch.tensor([[0.0, 0.0, 1.0, 1.0]])
        boxes2 = torch.tensor([[0.5, 0.5, 1.5, 1.5]])

        iou, inter = box_iou(boxes1, boxes2)

        # 交集区域：[0.5, 0.5] to [1.0, 1.0] = 0.25
        # 并集区域：1.0 + 1.0 - 0.25 = 1.75
        # IoU = 0.25 / 1.75 ≈ 0.1429
        assert iou.shape == (1, 1)
        assert iou.item() > 0
        assert iou.item() < 1

    def test_generalized_box_iou(self):
        """测试广义IoU计算"""
        boxes1 = torch.tensor([[0.0, 0.0, 1.0, 1.0]])
        boxes2 = torch.tensor([[0.5, 0.5, 1.5, 1.5]])

        giou = generalized_box_iou(boxes1, boxes2)
        assert giou.shape == (1, 1)
        # GIoU应该小于等于IoU
        iou, _ = box_iou(boxes1, boxes2)
        assert giou.item() <= iou.item() + 1e-6

    def test_build_matcher(self):
        """测试构建匹配器"""
        matcher = build_matcher(cost_class=2, cost_bbox=5, cost_giou=2)
        assert matcher.cost_class == 2
        assert matcher.cost_bbox == 5
        assert matcher.cost_giou == 2

    def test_matcher_perfect_match(self):
        """测试完美匹配情况"""
        matcher = HungarianMatcher(cost_class=1, cost_bbox=10, cost_giou=1)

        # 预测与目标完全匹配
        outputs = {
            'pred_logits': torch.tensor([[[10.0, 0.0], [0.0, 10.0]]]),
            'pred_boxes': torch.tensor([[[0.5, 0.5, 0.2, 0.2], [0.3, 0.3, 0.1, 0.1]]])
        }

        targets = [{
            'labels': torch.tensor([1, 0]),
            'boxes': torch.tensor([[0.5, 0.5, 0.2, 0.2], [0.3, 0.3, 0.1, 0.1]])
        }]

        indices = matcher(outputs, targets)
        pred_idx, target_idx = indices[0]

        # 应该匹配到正确的索引
        assert len(pred_idx) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
