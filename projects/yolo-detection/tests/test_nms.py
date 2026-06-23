"""
Tests for Non-Maximum Suppression.
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.nms import (
    non_max_suppression,
    batched_nms,
    soft_nms,
    compute_iou_matrix,
)


class TestComputeIoUMatrix:
    """Test IoU matrix computation."""

    def test_iou_matrix_shape(self):
        """Test IoU matrix shape."""
        boxes = torch.tensor([
            [0.0, 0.0, 10.0, 10.0],
            [5.0, 5.0, 15.0, 15.0],
            [20.0, 20.0, 30.0, 30.0],
        ])
        iou = compute_iou_matrix(boxes)
        assert iou.shape == (3, 3)

    def test_iou_matrix_diagonal(self):
        """Test that diagonal is 1.0 (box with itself)."""
        boxes = torch.tensor([
            [0.0, 0.0, 10.0, 10.0],
            [5.0, 5.0, 15.0, 15.0],
        ])
        iou = compute_iou_matrix(boxes)
        assert torch.allclose(iou.diag(), torch.ones(2))

    def test_iou_matrix_symmetry(self):
        """Test that IoU matrix is symmetric."""
        boxes = torch.tensor([
            [0.0, 0.0, 10.0, 10.0],
            [5.0, 5.0, 15.0, 15.0],
        ])
        iou = compute_iou_matrix(boxes)
        assert torch.allclose(iou, iou.T)

    def test_iou_matrix_no_overlap(self):
        """Test IoU for non-overlapping boxes."""
        boxes = torch.tensor([
            [0.0, 0.0, 10.0, 10.0],
            [20.0, 20.0, 30.0, 30.0],
        ])
        iou = compute_iou_matrix(boxes)
        assert iou[0, 1] == 0.0
        assert iou[1, 0] == 0.0


class TestNonMaxSuppression:
    """Test NMS implementation."""

    def test_nms_empty(self):
        """Test NMS with empty input."""
        boxes = torch.zeros(0, 4)
        scores = torch.zeros(0)
        keep_boxes, keep_scores = non_max_suppression(boxes, scores)
        assert len(keep_boxes) == 0
        assert len(keep_scores) == 0

    def test_nms_single_box(self):
        """Test NMS with single box."""
        boxes = torch.tensor([[10.0, 10.0, 50.0, 50.0]])
        scores = torch.tensor([0.9])
        keep_boxes, keep_scores = non_max_suppression(boxes, scores, score_threshold=0.1)
        assert len(keep_boxes) == 1
        assert keep_scores[0] == 0.9

    def test_nms_no_overlap(self):
        """Test NMS with non-overlapping boxes."""
        boxes = torch.tensor([
            [10.0, 10.0, 50.0, 50.0],
            [100.0, 100.0, 150.0, 150.0],
        ])
        scores = torch.tensor([0.9, 0.8])
        keep_boxes, keep_scores = non_max_suppression(boxes, scores, iou_threshold=0.5)
        assert len(keep_boxes) == 2

    def test_nms_high_overlap(self):
        """Test NMS with highly overlapping boxes."""
        boxes = torch.tensor([
            [10.0, 10.0, 50.0, 50.0],
            [12.0, 12.0, 52.0, 52.0],  # Very similar to first
        ])
        scores = torch.tensor([0.9, 0.8])
        keep_boxes, keep_scores = non_max_suppression(boxes, scores, iou_threshold=0.5)
        # Should keep only the highest scoring box
        assert len(keep_boxes) == 1
        assert keep_scores[0] == 0.9

    def test_nms_partial_overlap(self):
        """Test NMS with partially overlapping boxes."""
        boxes = torch.tensor([
            [10.0, 10.0, 50.0, 50.0],
            [30.0, 30.0, 70.0, 70.0],  # Partial overlap
            [100.0, 100.0, 150.0, 150.0],  # No overlap
        ])
        scores = torch.tensor([0.9, 0.8, 0.7])
        keep_boxes, keep_scores = non_max_suppression(boxes, scores, iou_threshold=0.3)
        # Depending on IoU, may keep 2 or 3
        assert len(keep_boxes) >= 2

    def test_nms_score_threshold(self):
        """Test NMS score threshold filtering."""
        boxes = torch.tensor([
            [10.0, 10.0, 50.0, 50.0],
            [100.0, 100.0, 150.0, 150.0],
        ])
        scores = torch.tensor([0.9, 0.05])  # Second box below threshold
        keep_boxes, keep_scores = non_max_suppression(boxes, scores, score_threshold=0.1)
        assert len(keep_boxes) == 1

    def test_nms_max_detections(self):
        """Test NMS max detections limit."""
        # Create many non-overlapping boxes
        boxes = torch.tensor([[i * 100.0, 0, i * 100 + 50, 50] for i in range(10)])
        scores = torch.tensor([0.9 - i * 0.05 for i in range(10)])
        keep_boxes, keep_scores = non_max_suppression(
            boxes, scores, max_detections=3, score_threshold=0.1
        )
        assert len(keep_boxes) <= 3

    def test_nms_preserves_order(self):
        """Test that NMS preserves score ordering."""
        boxes = torch.tensor([
            [10.0, 10.0, 50.0, 50.0],
            [100.0, 100.0, 150.0, 150.0],
            [200.0, 200.0, 250.0, 250.0],
        ])
        scores = torch.tensor([0.7, 0.9, 0.8])
        keep_boxes, keep_scores = non_max_suppression(boxes, scores)
        # Scores should be in descending order
        assert keep_scores[0] >= keep_scores[1] if len(keep_scores) > 1 else True


class TestBatchedNMS:
    """Test batched (per-class) NMS."""

    def test_batched_nms_empty(self):
        """Test batched NMS with empty input."""
        boxes = torch.zeros(0, 4)
        scores = torch.zeros(0)
        labels = torch.zeros(0, dtype=torch.long)
        keep_boxes, keep_scores, keep_labels = batched_nms(boxes, scores, labels)
        assert len(keep_boxes) == 0

    def test_batched_nms_different_classes(self):
        """Test that NMS is applied per class."""
        # Two overlapping boxes of different classes
        boxes = torch.tensor([
            [10.0, 10.0, 50.0, 50.0],
            [12.0, 12.0, 52.0, 52.0],
        ])
        scores = torch.tensor([0.9, 0.8])
        labels = torch.tensor([0, 1])  # Different classes

        keep_boxes, keep_scores, keep_labels = batched_nms(
            boxes, scores, labels, iou_threshold=0.5
        )
        # Both should be kept since they're different classes
        assert len(keep_boxes) == 2

    def test_batched_nms_same_class(self):
        """Test NMS within same class."""
        # Two overlapping boxes of same class
        boxes = torch.tensor([
            [10.0, 10.0, 50.0, 50.0],
            [12.0, 12.0, 52.0, 52.0],
        ])
        scores = torch.tensor([0.9, 0.8])
        labels = torch.tensor([0, 0])  # Same class

        keep_boxes, keep_scores, keep_labels = batched_nms(
            boxes, scores, labels, iou_threshold=0.5
        )
        # Only highest scoring should be kept
        assert len(keep_boxes) == 1
        assert keep_scores[0] == 0.9


class TestSoftNMS:
    """Test Soft-NMS implementation."""

    def test_soft_nms_empty(self):
        """Test soft NMS with empty input."""
        boxes = torch.zeros(0, 4)
        scores = torch.zeros(0)
        keep_boxes, keep_scores = soft_nms(boxes, scores)
        assert len(keep_boxes) == 0

    def test_soft_nms_single_box(self):
        """Test soft NMS with single box."""
        boxes = torch.tensor([[10.0, 10.0, 50.0, 50.0]])
        scores = torch.tensor([0.9])
        keep_boxes, keep_scores = soft_nms(boxes, scores)
        assert len(keep_boxes) == 1

    def test_soft_nms_decays_scores(self):
        """Test that soft NMS decays scores instead of removing."""
        boxes = torch.tensor([
            [10.0, 10.0, 50.0, 50.0],
            [12.0, 12.0, 52.0, 52.0],
        ])
        scores = torch.tensor([0.9, 0.8])
        keep_boxes, keep_scores = soft_nms(boxes, scores, score_threshold=0.01)
        # Both boxes should be kept (with decayed scores)
        assert len(keep_boxes) == 2
        # Second box's score should be decayed
        assert keep_scores[1] < 0.8

    def test_soft_nms_gaussian_method(self):
        """Test soft NMS with gaussian method."""
        boxes = torch.tensor([
            [10.0, 10.0, 50.0, 50.0],
            [12.0, 12.0, 52.0, 52.0],
        ])
        scores = torch.tensor([0.9, 0.8])
        keep_boxes, keep_scores = soft_nms(
            boxes, scores, method="gaussian", sigma=0.5, score_threshold=0.01
        )
        assert len(keep_boxes) == 2

    def test_soft_nms_linear_method(self):
        """Test soft NMS with linear method."""
        boxes = torch.tensor([
            [10.0, 10.0, 50.0, 50.0],
            [12.0, 12.0, 52.0, 52.0],
        ])
        scores = torch.tensor([0.9, 0.8])
        keep_boxes, keep_scores = soft_nms(
            boxes, scores, method="linear", iou_threshold=0.3, score_threshold=0.01
        )
        assert len(keep_boxes) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
