"""
深度估计工具函数测试
"""

import pytest
import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils import (
    normalize_depth,
    colorize_depth,
    visualize_depth,
    compute_depth_metrics,
    depth_to_disparity,
    disparity_to_depth,
    depth_stats,
)


class TestNormalizeDepth:
    """深度归一化测试"""

    def test_basic(self):
        """测试基本功能"""
        depth = torch.tensor([[[[1.0, 2.0], [3.0, 4.0]]]])
        normalized = normalize_depth(depth)
        assert normalized.min() == pytest.approx(0.0)
        assert normalized.max() == pytest.approx(1.0)

    def test_custom_range(self):
        """测试自定义范围"""
        depth = torch.tensor([[[[5.0, 10.0], [15.0, 20.0]]]])
        normalized = normalize_depth(depth, min_depth=5.0, max_depth=20.0)
        assert normalized.min() == pytest.approx(0.0)
        assert normalized.max() == pytest.approx(1.0)


class TestColorizeDepth:
    """深度着色测试"""

    def test_basic(self):
        """测试基本功能"""
        depth = torch.rand(8, 8)
        colored = colorize_depth(depth)
        assert colored.shape == (3, 8, 8)

    def test_with_batch(self):
        """测试带批次维度"""
        depth = torch.rand(1, 8, 8)
        colored = colorize_depth(depth)
        assert colored.shape == (3, 8, 8)

    def test_range(self):
        """测试输出范围"""
        depth = torch.rand(8, 8)
        colored = colorize_depth(depth)
        assert colored.min() >= 0
        assert colored.max() <= 1

    def test_different_colormaps(self):
        """测试不同颜色映射"""
        depth = torch.rand(8, 8)
        for cmap in ["jet", "viridis", "plasma"]:
            colored = colorize_depth(depth, colormap=cmap)
            assert colored.shape == (3, 8, 8)


class TestVisualizeDepth:
    """深度可视化测试"""

    def test_without_target(self):
        """测试无目标深度"""
        image = torch.rand(3, 8, 8)
        pred = torch.rand(1, 8, 8)
        result = visualize_depth(image, pred)
        assert result.shape[0] == 3
        assert result.shape[2] == 16  # 8 + 8

    def test_with_target(self):
        """测试有目标深度"""
        image = torch.rand(3, 8, 8)
        pred = torch.rand(1, 8, 8)
        target = torch.rand(1, 8, 8)
        result = visualize_depth(image, pred, target)
        assert result.shape[0] == 3
        assert result.shape[2] == 24  # 8 + 8 + 8


class TestComputeDepthMetrics:
    """深度指标测试"""

    def test_perfect_prediction(self):
        """测试完美预测"""
        pred = torch.rand(2, 1, 8, 8) * 10 + 0.1
        metrics = compute_depth_metrics(pred, pred)

        assert metrics["abs_rel"] == pytest.approx(0.0, abs=1e-5)
        assert metrics["rmse"] == pytest.approx(0.0, abs=1e-5)
        assert metrics["delta1"] == pytest.approx(1.0)

    def test_metrics_range(self):
        """测试指标范围"""
        pred = torch.rand(2, 1, 8, 8) * 10 + 0.1
        target = torch.rand(2, 1, 8, 8) * 10 + 0.1
        metrics = compute_depth_metrics(pred, target)

        assert metrics["abs_rel"] >= 0
        assert metrics["rmse"] >= 0
        assert 0 <= metrics["delta1"] <= 1
        assert 0 <= metrics["delta2"] <= 1
        assert 0 <= metrics["delta3"] <= 1

    def test_with_mask(self):
        """测试带掩码"""
        pred = torch.rand(2, 1, 8, 8) * 10 + 0.1
        target = torch.rand(2, 1, 8, 8) * 10 + 0.1
        mask = torch.ones(2, 1, 8, 8)
        mask[:, :, :4, :] = 0
        metrics = compute_depth_metrics(pred, target, mask)

        assert "abs_rel" in metrics
        assert "rmse" in metrics


class TestDepthDisparityConversion:
    """深度-视差转换测试"""

    def test_roundtrip(self):
        """测试往返转换"""
        depth = torch.rand(2, 1, 8, 8) * 10 + 0.1
        baseline = 0.1
        focal = 500.0

        disparity = depth_to_disparity(depth, baseline, focal)
        depth_recovered = disparity_to_depth(disparity, baseline, focal)

        assert torch.allclose(depth, depth_recovered, atol=1e-3)


class TestDepthStats:
    """深度统计测试"""

    def test_basic(self):
        """测试基本功能"""
        depth = torch.rand(1, 8, 8) * 10
        stats = depth_stats(depth)

        assert "min" in stats
        assert "max" in stats
        assert "mean" in stats
        assert "std" in stats
        assert "median" in stats

    def test_values(self):
        """测试统计值"""
        depth = torch.tensor([[[[1.0, 2.0, 3.0, 4.0, 5.0]]]])
        stats = depth_stats(depth)

        assert stats["min"] == pytest.approx(1.0)
        assert stats["max"] == pytest.approx(5.0)
        assert stats["mean"] == pytest.approx(3.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
