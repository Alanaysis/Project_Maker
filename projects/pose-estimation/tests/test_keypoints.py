"""
关键点检测与处理测试。
"""

import pytest
import torch
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.keypoints import (
    KEYPOINT_NAMES,
    SKELETON_CONNECTIONS,
    extract_keypoints,
    extract_keypoints_with_subpixel,
    decode_predictions,
    compute_pck,
    compute_pck_per_keypoint,
)


class TestConstants:
    """测试常量定义。"""

    def test_keypoint_names_count(self):
        """测试关键点数量。"""
        assert len(KEYPOINT_NAMES) == 17

    def test_keypoint_names_unique(self):
        """测试关键点名称唯一。"""
        assert len(KEYPOINT_NAMES) == len(set(KEYPOINT_NAMES))

    def test_skeleton_connections_valid(self):
        """测试骨骼连接的有效性。"""
        for i, j in SKELETON_CONNECTIONS:
            assert 0 <= i < 17
            assert 0 <= j < 17
            assert i != j

    def test_keypoint_names_format(self):
        """测试关键点名称格式。"""
        for name in KEYPOINT_NAMES:
            assert isinstance(name, str)
            assert len(name) > 0


class TestExtractKeypoints:
    """测试关键点提取。"""

    def test_output_shape(self):
        """测试输出形状。"""
        heatmaps = torch.rand(4, 17, 64, 64)
        keypoints, confidence = extract_keypoints(heatmaps)
        assert keypoints.shape == (4, 17, 2)
        assert confidence.shape == (4, 17)

    def test_coordinate_range(self):
        """测试坐标范围。"""
        heatmaps = torch.rand(2, 17, 32, 32)
        keypoints, _ = extract_keypoints(heatmaps)
        assert keypoints.min() >= 0.0
        assert keypoints.max() <= 1.0

    def test_confidence_range(self):
        """测试置信度范围。"""
        heatmaps = torch.rand(2, 17, 32, 32)
        _, confidence = extract_keypoints(heatmaps)
        assert confidence.min() >= 0.0

    def test_threshold_effect(self):
        """测试阈值效果。"""
        heatmaps = torch.rand(2, 17, 32, 32)
        kp_low, conf_low = extract_keypoints(heatmaps, threshold=0.01)
        kp_high, conf_high = extract_keypoints(heatmaps, threshold=0.9)

        # 高阈值应该有更多零坐标
        zero_count_high = (kp_high == 0).sum().item()
        zero_count_low = (kp_low == 0).sum().item()
        assert zero_count_high >= zero_count_low

    def test_single_peak(self):
        """测试单峰热力图。"""
        heatmaps = torch.zeros(1, 1, 32, 32)
        heatmaps[0, 0, 16, 16] = 1.0

        keypoints, confidence = extract_keypoints(heatmaps, threshold=0.5)

        # 关键点应该在 (16/31, 16/31) 附近
        assert abs(keypoints[0, 0, 0].item() - 16 / 31) < 0.05
        assert abs(keypoints[0, 0, 1].item() - 16 / 31) < 0.05
        assert confidence[0, 0].item() > 0.9


class TestExtractKeypointsWithSubpixel:
    """测试亚像素关键点提取。"""

    def test_output_shape(self):
        """测试输出形状。"""
        heatmaps = torch.rand(2, 17, 32, 32)
        keypoints, confidence = extract_keypoints_with_subpixel(heatmaps)
        assert keypoints.shape == (2, 17, 2)
        assert confidence.shape == (2, 17)

    def test_coordinate_range(self):
        """测试坐标范围。"""
        heatmaps = torch.rand(2, 10, 32, 32)
        keypoints, _ = extract_keypoints_with_subpixel(heatmaps)
        assert keypoints.min() >= 0.0
        assert keypoints.max() <= 1.0


class TestDecodePredictions:
    """测试预测解码。"""

    def test_output_keys(self):
        """测试输出字典的键。"""
        heatmaps = torch.rand(2, 17, 32, 32)
        result = decode_predictions(heatmaps, image_size=(256, 256))
        assert "keypoints_norm" in result
        assert "keypoints_img" in result
        assert "confidence" in result
        assert "num_keypoints" in result

    def test_normalized_coordinates(self):
        """测试归一化坐标。"""
        heatmaps = torch.rand(2, 17, 32, 32)
        result = decode_predictions(heatmaps, image_size=(256, 256))
        kp_norm = result["keypoints_norm"]
        assert kp_norm.min() >= 0.0
        assert kp_norm.max() <= 1.0

    def test_image_coordinates(self):
        """测试图像坐标。"""
        heatmaps = torch.rand(2, 17, 32, 32)
        result = decode_predictions(heatmaps, image_size=(256, 256))
        kp_img = result["keypoints_img"]
        assert kp_img.max() <= 256.0

    def test_num_keypoints(self):
        """测试关键点数量。"""
        heatmaps = torch.rand(2, 10, 32, 32)
        result = decode_predictions(heatmaps, image_size=(128, 128))
        assert result["num_keypoints"] == 10

    def test_subpixel_method(self):
        """测试亚像素方法。"""
        heatmaps = torch.rand(2, 17, 32, 32)
        result = decode_predictions(heatmaps, image_size=(256, 256), method="subpixel")
        assert result["keypoints_norm"].shape == (2, 17, 2)


class TestPCK:
    """测试 PCK 评估指标。"""

    def test_perfect_prediction(self):
        """测试完美预测的 PCK 为 1。"""
        pred = torch.rand(4, 17, 2) * 0.5 + 0.25
        target = pred.clone()
        pck = compute_pck(pred, target, threshold=0.01)
        assert pck == 1.0

    def test_pck_range(self):
        """测试 PCK 范围。"""
        pred = torch.rand(4, 17, 2)
        target = torch.rand(4, 17, 2)
        pck = compute_pck(pred, target)
        assert 0.0 <= pck <= 1.0

    def test_threshold_effect(self):
        """测试阈值对 PCK 的影响。"""
        pred = torch.rand(4, 17, 2)
        target = torch.rand(4, 17, 2)

        pck_tight = compute_pck(pred, target, threshold=0.05)
        pck_loose = compute_pck(pred, target, threshold=0.5)

        # 更宽松的阈值应该有更高的 PCK
        assert pck_loose >= pck_tight


class TestPCKPerKeypoint:
    """测试每个关键点的 PCK。"""

    def test_output_shape(self):
        """测试输出形状。"""
        pred = torch.rand(4, 17, 2)
        target = torch.rand(4, 17, 2)
        pck_list = compute_pck_per_keypoint(pred, target)
        assert len(pck_list) == 17

    def test_values_range(self):
        """测试值范围。"""
        pred = torch.rand(4, 17, 2)
        target = torch.rand(4, 17, 2)
        pck_list = compute_pck_per_keypoint(pred, target)
        for p in pck_list:
            assert 0.0 <= p <= 1.0
