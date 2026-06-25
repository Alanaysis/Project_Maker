"""
可视化与工具函数测试。
"""

import pytest
import torch
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils import (
    draw_skeleton,
    visualize_pose,
    normalize_keypoints,
    denormalize_keypoints,
    compute_oks,
    get_keypoint_names,
    get_skeleton_connections,
)
from src.keypoints import KEYPOINT_NAMES, SKELETON_CONNECTIONS


class TestDrawSkeleton:
    """测试骨骼绘制。"""

    def test_output_shape(self):
        """测试输出形状。"""
        img = np.zeros((256, 256, 3), dtype=np.uint8)
        kp = np.random.rand(17, 2) * 200
        result = draw_skeleton(img, kp)
        assert result.shape == (256, 256, 3)

    def test_does_not_modify_input(self):
        """测试不修改输入图像。"""
        img = np.zeros((128, 128, 3), dtype=np.uint8)
        img_copy = img.copy()
        kp = np.random.rand(17, 2) * 100
        draw_skeleton(img, kp)
        assert np.array_equal(img, img_copy)

    def test_with_confidence(self):
        """测试带置信度的绘制。"""
        img = np.zeros((128, 128, 3), dtype=np.uint8)
        kp = np.random.rand(17, 2) * 100
        conf = np.random.rand(17)
        result = draw_skeleton(img, kp, confidence=conf, confidence_threshold=0.5)
        assert result.shape == (128, 128, 3)

    def test_custom_colors(self):
        """测试自定义颜色。"""
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        kp = np.array([[32, 32]])
        result = draw_skeleton(
            img, kp,
            keypoint_color=(255, 0, 0),
            line_color=(0, 255, 0),
            connections=[],
        )
        assert result.shape == (64, 64, 3)


class TestVisualizePose:
    """测试姿态可视化。"""

    def test_tensor_input(self):
        """测试张量输入。"""
        img = torch.rand(3, 128, 128)
        kp = torch.rand(17, 2) * 64
        conf = torch.rand(17)
        result = visualize_pose(img, kp, conf)
        assert result.shape == (128, 128, 3)

    def test_numpy_input(self):
        """测试 numpy 输入。"""
        img = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
        kp = np.random.rand(17, 2) * 100
        result = visualize_pose(img, kp)
        assert result.shape == (128, 128, 3)

    def test_normalized_coordinates(self):
        """测试归一化坐标。"""
        img = torch.rand(3, 256, 256)
        kp = torch.rand(17, 2)  # [0, 1]
        result = visualize_pose(img, kp, image_size=(256, 256))
        assert result.shape == (256, 256, 3)


class TestNormalizeKeypoints:
    """测试关键点归一化。"""

    def test_basic(self):
        """测试基本归一化。"""
        kp = torch.tensor([[128.0, 64.0]])
        normalized = normalize_keypoints(kp, (256, 256))
        assert abs(normalized[0, 0].item() - 0.5) < 1e-5
        assert abs(normalized[0, 1].item() - 0.25) < 1e-5

    def test_range(self):
        """测试值范围。"""
        kp = torch.rand(17, 2) * 256
        normalized = normalize_keypoints(kp, (256, 256))
        assert normalized.min() >= 0.0
        assert normalized.max() <= 1.0


class TestDenormalizeKeypoints:
    """测试关键点反归一化。"""

    def test_basic(self):
        """测试基本反归一化。"""
        kp = torch.tensor([[0.5, 0.25]])
        denormalized = denormalize_keypoints(kp, (256, 256))
        assert abs(denormalized[0, 0].item() - 128.0) < 1e-3
        assert abs(denormalized[0, 1].item() - 64.0) < 1e-3

    def test_roundtrip(self):
        """测试往返转换。"""
        original = torch.rand(17, 2) * 200
        normalized = normalize_keypoints(original, (256, 256))
        restored = denormalize_keypoints(normalized, (256, 256))
        assert torch.allclose(original, restored, atol=1e-3)


class TestComputeOKS:
    """测试 OKS 计算。"""

    def test_perfect_match(self):
        """测试完美匹配的 OKS。"""
        pred = torch.rand(2, 17, 2)
        gt = pred.clone()
        areas = torch.ones(2) * 10000
        visibility = torch.ones(2, 17)

        oks = compute_oks(pred, gt, areas, visibility)
        assert oks.min() > 0.99  # 应该接近 1

    def test_output_shape(self):
        """测试输出形状。"""
        pred = torch.rand(4, 17, 2)
        gt = torch.rand(4, 17, 2)
        areas = torch.ones(4) * 10000
        visibility = torch.ones(4, 17)

        oks = compute_oks(pred, gt, areas, visibility)
        assert oks.shape == (4,)

    def test_range(self):
        """测试值范围。"""
        pred = torch.rand(4, 17, 2)
        gt = torch.rand(4, 17, 2)
        areas = torch.ones(4) * 10000
        visibility = torch.ones(4, 17)

        oks = compute_oks(pred, gt, areas, visibility)
        assert oks.min() >= 0.0
        assert oks.max() <= 1.0


class TestUtilityFunctions:
    """测试工具函数。"""

    def test_get_keypoint_names(self):
        """测试获取关键点名称。"""
        names = get_keypoint_names()
        assert len(names) == 17
        assert names == KEYPOINT_NAMES

    def test_get_skeleton_connections(self):
        """测试获取骨骼连接。"""
        connections = get_skeleton_connections()
        assert len(connections) == 16
        assert connections == SKELETON_CONNECTIONS
