"""测试工具函数"""

import pytest
import numpy as np
import cv2
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import (
    resize_image, order_points, crop_text_region,
    compute_iou, nms, create_test_image
)


class TestResizeImage:
    """测试图像缩放"""

    def test_resize_normal(self):
        """正常缩放"""
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        resized = resize_image(image, max_size=100)
        assert resized.shape[0] <= 100
        assert resized.shape[1] <= 100

    def test_resize_small_image(self):
        """小图像不缩放"""
        image = np.zeros((50, 50, 3), dtype=np.uint8)
        resized = resize_image(image, max_size=100)
        assert resized.shape == image.shape

    def test_resize_preserve_ratio(self):
        """保持宽高比"""
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        resized = resize_image(image, max_size=100)
        ratio_orig = 200 / 100
        ratio_resized = resized.shape[1] / resized.shape[0]
        assert abs(ratio_orig - ratio_resized) < 0.1

    def test_resize_exact_size(self):
        """精确大小"""
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        resized = resize_image(image, max_size=50)
        assert max(resized.shape[0], resized.shape[1]) == 50


class TestOrderPoints:
    """测试点排序"""

    def test_order_square(self):
        """正方形点排序"""
        pts = np.array([[10, 10], [10, 0], [0, 0], [0, 10]], dtype=np.float32)
        ordered = order_points(pts)
        # 左上、右上、右下、左下
        assert ordered[0][0] < ordered[1][0]  # 左上.x < 右上.x
        assert ordered[0][1] < ordered[3][1]  # 左上.y < 左下.y

    def test_order_rectangle(self):
        """矩形点排序"""
        pts = np.array([[100, 50], [0, 50], [0, 0], [100, 0]], dtype=np.float32)
        ordered = order_points(pts)
        assert ordered[0][0] < ordered[1][0]

    def test_order_points_shape(self):
        """输出形状"""
        pts = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.float32)
        ordered = order_points(pts)
        assert ordered.shape == (4, 2)


class TestComputeIoU:
    """测试 IoU 计算"""

    def test_iou_no_overlap(self):
        """无重叠"""
        box1 = np.array([0, 0, 10, 10])
        box2 = np.array([20, 20, 30, 30])
        assert compute_iou(box1, box2) == 0

    def test_iou_full_overlap(self):
        """完全重叠"""
        box1 = np.array([0, 0, 10, 10])
        box2 = np.array([0, 0, 10, 10])
        assert compute_iou(box1, box2) == 1.0

    def test_iou_partial_overlap(self):
        """部分重叠"""
        box1 = np.array([0, 0, 10, 10])
        box2 = np.array([5, 5, 15, 15])
        iou = compute_iou(box1, box2)
        assert 0 < iou < 1

    def test_iou_corner_touch(self):
        """角点接触"""
        box1 = np.array([0, 0, 10, 10])
        box2 = np.array([10, 10, 20, 20])
        assert compute_iou(box1, box2) == 0


class TestNMS:
    """测试 NMS"""

    def test_nms_empty(self):
        """空输入"""
        boxes = np.array([]).reshape(0, 4)
        scores = np.array([])
        assert nms(boxes, scores) == []

    def test_nms_no_overlap(self):
        """无重叠框"""
        boxes = np.array([
            [0, 0, 10, 10],
            [20, 20, 30, 30]
        ])
        scores = np.array([0.9, 0.8])
        keep = nms(boxes, scores, threshold=0.5)
        assert len(keep) == 2

    def test_nms_overlap(self):
        """重叠框"""
        boxes = np.array([
            [0, 0, 10, 10],
            [1, 1, 11, 11],
            [20, 20, 30, 30]
        ])
        scores = np.array([0.9, 0.8, 0.7])
        keep = nms(boxes, scores, threshold=0.5)
        assert len(keep) == 2

    def test_nms_scores_order(self):
        """按分数排序"""
        boxes = np.array([
            [0, 0, 10, 10],
            [1, 1, 11, 11]
        ])
        scores = np.array([0.7, 0.9])
        keep = nms(boxes, scores, threshold=0.5)
        assert len(keep) == 1
        assert keep[0] == 1  # 保留分数高的


class TestCreateTestImage:
    """测试创建测试图像"""

    def test_create_default(self):
        """默认创建"""
        image = create_test_image()
        assert image.shape == (200, 600, 3)

    def test_create_custom_text(self):
        """自定义文本"""
        image = create_test_image(text="Test")
        assert image.shape == (200, 600, 3)

    def test_create_custom_size(self):
        """自定义大小"""
        image = create_test_image(size=(100, 300))
        assert image.shape == (100, 300, 3)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])