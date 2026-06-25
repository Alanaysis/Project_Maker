"""
热力图生成与处理测试。
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.heatmap import (
    generate_heatmaps,
    heatmaps_to_keypoints,
    soft_argmax,
    decode_heatmap_batch,
    resize_heatmaps,
)


class TestGenerateHeatmaps:
    """测试高斯热力图生成。"""

    def test_output_shape(self):
        """测试输出形状。"""
        batch_size, num_kp = 4, 17
        keypoints = torch.rand(batch_size, num_kp, 2)
        weights = torch.ones(batch_size, num_kp)
        heatmap_size = (64, 64)

        heatmaps = generate_heatmaps(keypoints, weights, heatmap_size)
        assert heatmaps.shape == (4, 17, 64, 64)

    def test_peak_location(self):
        """测试热力图峰值位置。"""
        # 创建单个关键点在中心
        keypoints = torch.tensor([[[0.5, 0.5]]])  # (1, 1, 2)
        weights = torch.ones(1, 1)
        heatmap_size = (64, 64)

        heatmaps = generate_heatmaps(keypoints, weights, heatmap_size, sigma=2.0)
        assert heatmaps.shape == (1, 1, 64, 64)

        # 峰值应该在中心附近
        flat = heatmaps.view(1, 1, -1)
        _, max_idx = flat.max(dim=2)
        y = max_idx.item() // 64
        x = max_idx.item() % 64
        # 应该在中心附近 (32, 32)
        assert abs(y - 32) <= 1
        assert abs(x - 32) <= 1

    def test_invisible_keypoint(self):
        """测试不可见关键点的热力图为全零。"""
        keypoints = torch.tensor([[[0.5, 0.5]]])
        weights = torch.tensor([[0.0]])  # 不可见
        heatmap_size = (32, 32)

        heatmaps = generate_heatmaps(keypoints, weights, heatmap_size)
        assert heatmaps.sum() == 0.0

    def test_multiple_keypoints(self):
        """测试多个关键点。"""
        keypoints = torch.tensor([[[0.2, 0.3], [0.7, 0.8]]])
        weights = torch.ones(1, 2)
        heatmap_size = (32, 32)

        heatmaps = generate_heatmaps(keypoints, weights, heatmap_size)
        assert heatmaps.shape == (1, 2, 32, 32)

        # 两个热力图的峰值位置应该不同
        flat0 = heatmaps[0, 0].view(-1)
        flat1 = heatmaps[0, 1].view(-1)
        _, idx0 = flat0.max(dim=0)
        _, idx1 = flat1.max(dim=0)
        assert idx0 != idx1

    def test_sigma_effect(self):
        """测试不同 sigma 值的效果。"""
        # 使用精确像素对齐的关键点位置，避免网格对齐问题
        keypoints = torch.tensor([[[32 / 63, 32 / 63]]])  # 精确对齐到像素 (32, 32)
        weights = torch.ones(1, 1)
        heatmap_size = (64, 64)

        hm_small = generate_heatmaps(keypoints, weights, heatmap_size, sigma=1.0)
        hm_large = generate_heatmaps(keypoints, weights, heatmap_size, sigma=5.0)

        # sigma 越大，峰值越高（高斯函数在中心的值更大，因为归一化常数不同）
        # 但更重要的是，sigma 越大，热力图覆盖范围越广
        assert (hm_large > 0.01).sum() > (hm_small > 0.01).sum()

    def test_values_range(self):
        """测试热力图值范围。"""
        keypoints = torch.rand(4, 17, 2)
        weights = torch.ones(4, 17)
        heatmap_size = (32, 32)

        heatmaps = generate_heatmaps(keypoints, weights, heatmap_size)

        # 高斯热力图值应该在 [0, 1] 范围内
        assert heatmaps.min() >= 0.0
        assert heatmaps.max() <= 1.0


class TestHeatmapsToKeypoints:
    """测试从热力图提取关键点。"""

    def test_output_shape(self):
        """测试输出形状。"""
        heatmaps = torch.rand(4, 17, 64, 64)
        keypoints, confidence = heatmaps_to_keypoints(heatmaps)
        assert keypoints.shape == (4, 17, 2)
        assert confidence.shape == (4, 17)

    def test_coordinate_range(self):
        """测试坐标范围。"""
        heatmaps = torch.rand(2, 10, 32, 32)
        keypoints, _ = heatmaps_to_keypoints(heatmaps)
        assert keypoints.min() >= 0.0
        assert keypoints.max() <= 1.0

    def test_roundtrip(self):
        """测试生成热力图后提取关键点的精度。"""
        # 创建已知关键点
        original_kp = torch.tensor([[[0.3, 0.6]]])  # (1, 1, 2)
        weights = torch.ones(1, 1)
        heatmap_size = (128, 128)

        # 生成热力图
        heatmaps = generate_heatmaps(original_kp, weights, heatmap_size, sigma=2.0)

        # 提取关键点
        extracted_kp, conf = heatmaps_to_keypoints(heatmaps)

        # 误差应该很小 (亚像素级别)
        error = (original_kp - extracted_kp).abs().max()
        assert error < 0.05  # 5% 误差


class TestSoftArgmax:
    """测试 Soft-Argmax。"""

    def test_output_shape(self):
        """测试输出形状。"""
        heatmaps = torch.rand(2, 17, 32, 32)
        keypoints, confidence = soft_argmax(heatmaps)
        assert keypoints.shape == (2, 17, 2)
        assert confidence.shape == (2, 17)

    def test_coordinate_range(self):
        """测试坐标范围。"""
        heatmaps = torch.rand(2, 10, 32, 32)
        keypoints, _ = soft_argmax(heatmaps)
        assert keypoints.min() >= 0.0
        assert keypoints.max() <= 1.0

    def test_differentiable(self):
        """测试可微性。"""
        heatmaps = torch.rand(1, 5, 32, 32, requires_grad=True)
        keypoints, _ = soft_argmax(heatmaps)
        loss = keypoints.sum()
        loss.backward()
        assert heatmaps.grad is not None
        assert heatmaps.grad.abs().sum() > 0

    def test_beta_effect(self):
        """测试温度参数的影响。"""
        # 创建有明确峰值的热力图
        heatmaps = torch.zeros(1, 1, 32, 32)
        heatmaps[0, 0, 16, 16] = 1.0

        kp_low, _ = soft_argmax(heatmaps, beta=10.0)
        kp_high, _ = soft_argmax(heatmaps, beta=1000.0)

        # 高 beta 应该更接近 argmax
        # 两者都应该在 (16/31, 16/31) 附近
        assert abs(kp_low[0, 0, 0].item() - 16 / 31) < 0.1
        assert abs(kp_high[0, 0, 0].item() - 16 / 31) < 0.05


class TestDecodeHeatmapBatch:
    """测试批量解码。"""

    def test_argmax_method(self):
        """测试 argmax 方法。"""
        heatmaps = torch.rand(2, 17, 32, 32)
        kp, conf = decode_heatmap_batch(heatmaps, method="argmax")
        assert kp.shape == (2, 17, 2)

    def test_soft_argmax_method(self):
        """测试 soft_argmax 方法。"""
        heatmaps = torch.rand(2, 17, 32, 32)
        kp, conf = decode_heatmap_batch(heatmaps, method="soft_argmax")
        assert kp.shape == (2, 17, 2)

    def test_invalid_method(self):
        """测试无效方法。"""
        heatmaps = torch.rand(2, 17, 32, 32)
        with pytest.raises(ValueError):
            decode_heatmap_batch(heatmaps, method="invalid")


class TestResizeHeatmaps:
    """测试热力图尺寸调整。"""

    def test_upsample(self):
        """测试上采样。"""
        heatmaps = torch.rand(2, 17, 32, 32)
        resized = resize_heatmaps(heatmaps, (64, 64))
        assert resized.shape == (2, 17, 64, 64)

    def test_downsample(self):
        """测试下采样。"""
        heatmaps = torch.rand(2, 17, 64, 64)
        resized = resize_heatmaps(heatmaps, (32, 32))
        assert resized.shape == (2, 17, 32, 32)
