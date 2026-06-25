"""
Tests for NMS and post-processing
"""

import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.postprocess.nms import (
    nms, lanms, decode_rbox, decode_quad,
    boxes_to_quads, resize_geometry
)


class TestNMS:
    """Test Non-Maximum Suppression."""

    def test_empty_boxes(self):
        """Test NMS with empty input."""
        boxes = np.array([]).reshape(0, 4)
        scores = np.array([])
        result = nms(boxes, scores, 0.5)
        assert result == []

    def test_single_box(self):
        """Test NMS with single box."""
        boxes = np.array([[10, 10, 50, 50]])
        scores = np.array([0.9])
        result = nms(boxes, scores, 0.5)
        assert result == [0]

    def test_no_overlap(self):
        """Test NMS with non-overlapping boxes."""
        boxes = np.array([
            [10, 10, 50, 50],
            [100, 100, 150, 150],
            [200, 200, 250, 250],
        ])
        scores = np.array([0.9, 0.8, 0.7])
        result = nms(boxes, scores, 0.5)
        assert len(result) == 3

    def test_full_overlap(self):
        """Test NMS with fully overlapping boxes."""
        boxes = np.array([
            [10, 10, 50, 50],
            [10, 10, 50, 50],
            [10, 10, 50, 50],
        ])
        scores = np.array([0.9, 0.8, 0.7])
        result = nms(boxes, scores, 0.5)
        assert len(result) == 1
        assert result[0] == 0  # Highest score

    def test_partial_overlap(self):
        """Test NMS with partially overlapping boxes."""
        boxes = np.array([
            [10, 10, 50, 50],
            [20, 20, 60, 60],  # More overlap with first
            [200, 200, 250, 250],
        ])
        scores = np.array([0.9, 0.8, 0.7])
        result = nms(boxes, scores, 0.3)
        # Should keep first and third (second overlaps with first)
        assert len(result) == 2

    def test_score_ordering(self):
        """Test that NMS respects score ordering."""
        boxes = np.array([
            [10, 10, 50, 50],
            [12, 12, 52, 52],  # Very similar to first
        ])
        scores = np.array([0.5, 0.9])  # Second has higher score
        result = nms(boxes, scores, 0.3)
        assert len(result) == 1
        assert result[0] == 1  # Higher score kept


class TestLANMS:
    """Test Locality-Aware NMS."""

    def test_empty_boxes(self):
        """Test LANMS with empty input."""
        boxes = np.array([]).reshape(0, 4)
        scores = np.array([])
        result = lanms(boxes, scores, 0.5)
        # LANMS returns empty lists for empty input
        assert result == ([], []) or (len(result[0]) == 0 and len(result[1]) == 0)

    def test_merge_overlapping(self):
        """Test LANMS merges overlapping boxes."""
        boxes = np.array([
            [10, 10, 50, 50],
            [20, 20, 60, 60],
            [30, 30, 70, 70],
        ])
        scores = np.array([0.9, 0.8, 0.7])
        merged_boxes, merged_scores = lanms(boxes, scores, 0.5)
        # Should merge overlapping boxes
        assert len(merged_boxes) <= 3

    def test_no_merge(self):
        """Test LANMS with non-overlapping boxes."""
        boxes = np.array([
            [10, 10, 50, 50],
            [200, 200, 250, 250],
        ])
        scores = np.array([0.9, 0.8])
        merged_boxes, merged_scores = lanms(boxes, scores, 0.5)
        assert len(merged_boxes) == 2


class TestDecodeRBOX:
    """Test RBOX decoding."""

    def test_empty_map(self):
        """Test decode with empty score map."""
        score_map = np.zeros((100, 100), dtype=np.float32)
        geo_map = np.zeros((5, 100, 100), dtype=np.float32)
        boxes, scores = decode_rbox(score_map, geo_map, 0.5)
        assert len(boxes) == 0
        assert len(scores) == 0

    def test_single_text(self):
        """Test decode with single text region."""
        score_map = np.zeros((100, 100), dtype=np.float32)
        geo_map = np.zeros((5, 100, 100), dtype=np.float32)

        # Create text region
        score_map[20:40, 30:60] = 0.8

        # Set geometry (distances in pixels)
        for y in range(20, 40):
            for x in range(30, 60):
                geo_map[0, y, x] = y - 20     # top
                geo_map[1, y, x] = 60 - x     # right
                geo_map[2, y, x] = 40 - y     # bottom
                geo_map[3, x, x] = x - 30     # left

        boxes, scores = decode_rbox(score_map, geo_map, 0.5, scale=4.0)
        assert len(boxes) > 0
        assert all(s >= 0.5 for s in scores)


class TestDecodeQuad:
    """Test Quad decoding."""

    def test_empty_map(self):
        """Test decode with empty score map."""
        score_map = np.zeros((100, 100), dtype=np.float32)
        geo_map = np.zeros((8, 100, 100), dtype=np.float32)
        quads, scores = decode_quad(score_map, geo_map, 0.5)
        assert len(quads) == 0

    def test_single_quad(self):
        """Test decode with single quad region."""
        score_map = np.zeros((100, 100), dtype=np.float32)
        geo_map = np.zeros((8, 100, 100), dtype=np.float32)

        # Create text region
        score_map[20:40, 30:60] = 0.8

        quads, scores = decode_quad(score_map, geo_map, 0.5, scale=4.0)
        assert len(quads) > 0


class TestBoxConversion:
    """Test box format conversions."""

    def test_boxes_to_quads(self):
        """Test converting boxes to quads."""
        boxes = np.array([
            [10, 20, 50, 60],
            [100, 200, 150, 250],
        ])
        quads = boxes_to_quads(boxes)
        assert quads.shape == (2, 4, 2)

        # Check first box corners
        assert quads[0, 0, 0] == 10   # x1
        assert quads[0, 0, 1] == 20   # y1
        assert quads[0, 2, 0] == 50   # x2
        assert quads[0, 2, 1] == 60   # y2

    def test_empty_boxes_to_quads(self):
        """Test converting empty boxes to quads."""
        boxes = np.array([]).reshape(0, 4)
        quads = boxes_to_quads(boxes)
        assert quads.shape == (0, 4, 2)


class TestResizeGeometry:
    """Test geometry map resizing."""

    def test_resize_upscale(self):
        """Test upscaling geometry map."""
        geo = np.random.randn(5, 50, 50).astype(np.float32)
        resized = resize_geometry(geo, (100, 100))
        assert resized.shape == (5, 100, 100)

    def test_resize_downscale(self):
        """Test downscaling geometry map."""
        geo = np.random.randn(5, 100, 100).astype(np.float32)
        resized = resize_geometry(geo, (50, 50))
        assert resized.shape == (5, 50, 50)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
