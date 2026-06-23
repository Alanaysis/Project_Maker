"""
Tests for utility functions.
"""

import pytest
import torch
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils import (
    compute_iou,
    xywh_to_xyxy,
    xyxy_to_xywh,
    decode_predictions,
    grid_to_absolute,
)


class TestBoxConversions:
    """Test bounding box format conversions."""

    def test_xywh_to_xyxy_basic(self):
        """Test basic conversion from center format to corner format."""
        boxes = torch.tensor([[10.0, 20.0, 6.0, 8.0]])  # cx, cy, w, h
        result = xywh_to_xyxy(boxes)
        expected = torch.tensor([[7.0, 16.0, 13.0, 24.0]])  # x1, y1, x2, y2
        assert torch.allclose(result, expected), f"Expected {expected}, got {result}"

    def test_xywh_to_xyxy_batch(self):
        """Test conversion with multiple boxes."""
        boxes = torch.tensor([
            [10.0, 20.0, 6.0, 8.0],
            [0.0, 0.0, 10.0, 10.0],
            [5.0, 5.0, 4.0, 4.0],
        ])
        result = xywh_to_xyxy(boxes)
        assert result.shape == (3, 4)
        # First box
        assert torch.allclose(result[0], torch.tensor([7.0, 16.0, 13.0, 24.0]))
        # Second box
        assert torch.allclose(result[1], torch.tensor([-5.0, -5.0, 5.0, 5.0]))

    def test_xyxy_to_xywh_basic(self):
        """Test basic conversion from corner format to center format."""
        boxes = torch.tensor([[7.0, 16.0, 13.0, 24.0]])  # x1, y1, x2, y2
        result = xyxy_to_xywh(boxes)
        expected = torch.tensor([[10.0, 20.0, 6.0, 8.0]])  # cx, cy, w, h
        assert torch.allclose(result, expected), f"Expected {expected}, got {result}"

    def test_roundtrip_conversion(self):
        """Test that converting back and forth preserves values."""
        original = torch.tensor([[10.0, 20.0, 6.0, 8.0]])
        converted = xyxy_to_xywh(xywh_to_xyxy(original))
        assert torch.allclose(original, converted)

    def test_zero_size_box(self):
        """Test conversion with zero-size box."""
        boxes = torch.tensor([[5.0, 5.0, 0.0, 0.0]])
        result = xywh_to_xyxy(boxes)
        assert torch.allclose(result, torch.tensor([[5.0, 5.0, 5.0, 5.0]]))


class TestIoU:
    """Test IoU computation."""

    def test_iou_identical_boxes(self):
        """Test IoU of identical boxes is 1.0."""
        boxes = torch.tensor([[10.0, 10.0, 20.0, 20.0]])
        iou = compute_iou(boxes, boxes, format="xyxy")
        assert torch.allclose(iou, torch.tensor([[1.0]]))

    def test_iou_no_overlap(self):
        """Test IoU of non-overlapping boxes is 0.0."""
        box1 = torch.tensor([[0.0, 0.0, 10.0, 10.0]])
        box2 = torch.tensor([[20.0, 20.0, 30.0, 30.0]])
        iou = compute_iou(box1, box2, format="xyxy")
        assert torch.allclose(iou, torch.tensor([[0.0]]))

    def test_iou_partial_overlap(self):
        """Test IoU of partially overlapping boxes."""
        box1 = torch.tensor([[0.0, 0.0, 10.0, 10.0]])  # area = 100
        box2 = torch.tensor([[5.0, 5.0, 15.0, 15.0]])  # area = 100
        iou = compute_iou(box1, box2, format="xyxy")
        # Intersection: 5x5 = 25, Union: 100 + 100 - 25 = 175
        expected = 25.0 / 175.0
        assert torch.allclose(iou, torch.tensor([[expected]]), atol=1e-5)

    def test_iou_contained(self):
        """Test IoU when one box contains the other."""
        outer = torch.tensor([[0.0, 0.0, 20.0, 20.0]])  # area = 400
        inner = torch.tensor([[5.0, 5.0, 15.0, 15.0]])  # area = 100
        iou = compute_iou(outer, inner, format="xyxy")
        # Intersection: 10x10 = 100, Union: 400
        expected = 100.0 / 400.0
        assert torch.allclose(iou, torch.tensor([[expected]]), atol=1e-5)

    def test_iou_multiple_boxes(self):
        """Test IoU with multiple boxes."""
        boxes1 = torch.tensor([
            [0.0, 0.0, 10.0, 10.0],
            [20.0, 20.0, 30.0, 30.0],
        ])
        boxes2 = torch.tensor([
            [5.0, 5.0, 15.0, 15.0],
            [25.0, 25.0, 35.0, 35.0],
        ])
        iou = compute_iou(boxes1, boxes2, format="xyxy")
        assert iou.shape == (2, 2)
        # Diagonal should have higher IoU
        assert iou[0, 0] > iou[0, 1]
        assert iou[1, 1] > iou[1, 0]

    def test_iou_xywh_format(self):
        """Test IoU with xywh format input."""
        box1 = torch.tensor([[5.0, 5.0, 10.0, 10.0]])  # center at (5,5), size 10x10
        box2 = torch.tensor([[10.0, 10.0, 10.0, 10.0]])  # center at (10,10), size 10x10
        iou = compute_iou(box1, box2, format="xywh")
        # box1: (0,0)-(10,10), box2: (5,5)-(15,15)
        # Intersection: 5x5 = 25, Union: 100 + 100 - 25 = 175
        expected = 25.0 / 175.0
        assert torch.allclose(iou, torch.tensor([[expected]]), atol=1e-5)


class TestDecodePredictions:
    """Test prediction decoding."""

    def test_decode_shape(self):
        """Test that decoded predictions have correct shapes."""
        batch_size = 2
        grid_size = 7
        num_boxes = 2
        num_classes = 20
        output_size = num_boxes * 5 + num_classes

        predictions = torch.randn(batch_size, grid_size, grid_size, output_size)
        results = decode_predictions(predictions, grid_size=grid_size, num_classes=num_classes)

        assert len(results) == batch_size
        for result in results:
            assert "boxes" in result
            assert "scores" in result
            assert "labels" in result

    def test_decode_high_confidence(self):
        """Test that high confidence predictions are kept."""
        grid_size = 7
        num_boxes = 2
        num_classes = 3
        output_size = num_boxes * 5 + num_classes

        predictions = torch.zeros(1, grid_size, grid_size, output_size)

        # Set high confidence for one cell
        predictions[0, 3, 3, 4] = 5.0  # High objectness score for box 0
        predictions[0, 3, 3, 0] = 0.5   # x
        predictions[0, 3, 3, 1] = 0.5   # y
        predictions[0, 3, 3, 2] = 0.3   # w
        predictions[0, 3, 3, 3] = 0.3   # h
        predictions[0, 3, 3, 10] = 5.0  # High class score

        results = decode_predictions(
            predictions,
            grid_size=grid_size,
            num_boxes=num_boxes,
            num_classes=num_classes,
            confidence_threshold=0.1,
        )

        # Should have at least one detection
        assert len(results[0]["boxes"]) >= 1

    def test_decode_low_confidence(self):
        """Test that low confidence predictions are filtered."""
        grid_size = 7
        predictions = torch.zeros(1, grid_size, grid_size, 30)  # 2*5 + 20
        results = decode_predictions(predictions, confidence_threshold=0.5)
        assert len(results[0]["boxes"]) == 0


class TestGridToAbsolute:
    """Test grid-to-absolute coordinate conversion."""

    def test_grid_to_absolute_basic(self):
        """Test basic grid to absolute conversion."""
        grid_size = 7
        image_size = 448
        cell_size = image_size / grid_size  # 64

        predictions = torch.zeros(1, grid_size, grid_size, 30)
        # Set box at cell (0, 0) with relative coords (0.5, 0.5)
        predictions[0, 0, 0, 0] = 0.5  # x
        predictions[0, 0, 0, 1] = 0.5  # y

        result = grid_to_absolute(predictions, grid_size=grid_size, image_size=image_size)

        # x should be (0 + 0.5) * 64 = 32
        assert torch.allclose(result[0, 0, 0, 0], torch.tensor(32.0))
        # y should be (0 + 0.5) * 64 = 32
        assert torch.allclose(result[0, 0, 0, 1], torch.tensor(32.0))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
