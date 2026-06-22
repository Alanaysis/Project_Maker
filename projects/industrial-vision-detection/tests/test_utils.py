"""
工具函数测试

测试工具函数相关的功能:
- 边界框操作
- 评估指标
"""

import pytest
import torch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.boxes import box_iou, box_nms, xywh_to_xyxy, xyxy_to_xywh
from src.utils.metrics import compute_iou, compute_ap, compute_map


class TestBoxOperations:
    """测试边界框操作"""

    def test_box_iou(self):
        """测试 IoU 计算"""
        box1 = torch.tensor([[0, 0, 10, 10], [5, 5, 15, 15]])
        box2 = torch.tensor([[5, 5, 15, 15], [0, 0, 10, 10]])

        iou = box_iou(box1, box2)

        assert iou.shape == (2, 2)
        assert iou[0, 0] > 0  # 应该有重叠
        assert iou[0, 1] == pytest.approx(iou[1, 0], abs=1e-6)  # 对称性

    def test_box_iou_no_overlap(self):
        """测试无重叠情况"""
        box1 = torch.tensor([[0, 0, 10, 10]])
        box2 = torch.tensor([[20, 20, 30, 30]])

        iou = box_iou(box1, box2)

        assert iou[0, 0] == pytest.approx(0.0, abs=1e-6)

    def test_box_iou_perfect_overlap(self):
        """测试完美重叠情况"""
        box1 = torch.tensor([[0, 0, 10, 10]])
        box2 = torch.tensor([[0, 0, 10, 10]])

        iou = box_iou(box1, box2)

        assert iou[0, 0] == pytest.approx(1.0, abs=1e-6)

    def test_box_nms(self):
        """测试 NMS"""
        boxes = torch.tensor([
            [10, 10, 50, 50],
            [15, 15, 55, 55],
            [100, 100, 150, 150]
        ]).float()
        scores = torch.tensor([0.9, 0.8, 0.7])

        keep = box_nms(boxes, scores, iou_threshold=0.5)

        assert len(keep) > 0
        assert len(keep) <= len(boxes)

    def test_xywh_to_xyxy(self):
        """测试格式转换: xywh -> xyxy"""
        boxes_xywh = torch.tensor([[10, 10, 20, 20]])
        boxes_xyxy = xywh_to_xyxy(boxes_xywh)

        assert boxes_xyxy[0, 0] == 0  # x1 = cx - w/2
        assert boxes_xyxy[0, 1] == 0  # y1 = cy - h/2
        assert boxes_xyxy[0, 2] == 20  # x2 = cx + w/2
        assert boxes_xyxy[0, 3] == 20  # y2 = cy + h/2

    def test_xyxy_to_xywh(self):
        """测试格式转换: xyxy -> xywh"""
        boxes_xyxy = torch.tensor([[0, 0, 20, 20]])
        boxes_xywh = xyxy_to_xywh(boxes_xyxy)

        assert boxes_xywh[0, 0] == 10  # cx
        assert boxes_xywh[0, 1] == 10  # cy
        assert boxes_xywh[0, 2] == 20  # w
        assert boxes_xywh[0, 3] == 20  # h

    def test_format_conversion_roundtrip(self):
        """测试格式转换往返"""
        original = torch.tensor([[10, 20, 30, 40]])
        converted = xywh_to_xyxy(original)
        back = xyxy_to_xywh(converted)

        assert torch.allclose(original, back, atol=1e-6)


class TestMetrics:
    """测试评估指标"""

    def test_compute_iou(self):
        """测试 IoU 计算"""
        box1 = torch.tensor([[0, 0, 10, 10]])
        box2 = torch.tensor([[5, 5, 15, 15]])

        iou = compute_iou(box1, box2)

        assert iou.shape == (1, 1)
        assert iou[0, 0] > 0

    def test_compute_ap(self):
        """测试 AP 计算"""
        predictions = [
            {
                'image_id': 0,
                'boxes': torch.tensor([[10, 10, 50, 50]]).float(),
                'scores': torch.tensor([0.9]),
                'labels': torch.tensor([0])
            }
        ]

        ground_truths = [
            {
                'image_id': 0,
                'boxes': torch.tensor([[12, 12, 52, 52]]).float(),
                'labels': torch.tensor([0])
            }
        ]

        aps = compute_ap(predictions, ground_truths, iou_threshold=0.5)

        assert 0 in aps
        assert aps[0] >= 0

    def test_compute_map(self):
        """测试 mAP 计算"""
        predictions = [
            {
                'image_id': 0,
                'boxes': torch.tensor([[10, 10, 50, 50]]).float(),
                'scores': torch.tensor([0.9]),
                'labels': torch.tensor([0])
            }
        ]

        ground_truths = [
            {
                'image_id': 0,
                'boxes': torch.tensor([[12, 12, 52, 52]]).float(),
                'labels': torch.tensor([0])
            }
        ]

        results = compute_map(predictions, ground_truths)

        assert 'mAP' in results
        assert 'mAP_50' in results
        assert results['mAP'] >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
