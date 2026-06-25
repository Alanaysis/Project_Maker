"""
工具函数测试
"""

import pytest
import numpy as np
import torch

from src.utils import (
    normalize_pointcloud,
    farthest_point_sample,
    random_sample_points,
    compute_point_cloud_distance,
    voxel_downsample,
)


class TestNormalizePointcloud:
    """归一化测试"""

    def test_numpy_input(self):
        """测试 NumPy 输入"""
        points = np.random.randn(100, 3).astype(np.float32)
        normalized = normalize_pointcloud(points)

        # 检查中心在原点
        centroid = np.mean(normalized, axis=0)
        np.testing.assert_allclose(centroid, 0, atol=1e-6)

        # 检查在单位球内
        max_dist = np.max(np.sqrt(np.sum(normalized ** 2, axis=1)))
        assert max_dist <= 1.0 + 1e-6

    def test_torch_input(self):
        """测试 PyTorch 输入"""
        points = torch.randn(100, 3)
        normalized = normalize_pointcloud(points)

        centroid = torch.mean(normalized, dim=0)
        assert torch.allclose(centroid, torch.zeros(3), atol=1e-6)

    def test_batch_input(self):
        """测试批量输入"""
        points = np.random.randn(10, 100, 3).astype(np.float32)
        normalized = normalize_pointcloud(points)

        assert normalized.shape == points.shape

        # 每个点云都应归一化
        for i in range(10):
            max_dist = np.max(np.sqrt(np.sum(normalized[i] ** 2, axis=1)))
            assert max_dist <= 1.0 + 1e-6


class TestFarthestPointSample:
    """最远点采样测试"""

    def test_output_shape(self):
        """测试输出形状"""
        batch_size = 4
        num_points = 1024
        num_samples = 128

        points = torch.randn(batch_size, num_points, 3)
        indices = farthest_point_sample(points, num_samples)

        assert indices.shape == (batch_size, num_samples)

    def test_unique_indices(self):
        """测试索引唯一性"""
        points = torch.randn(2, 512, 3)
        indices = farthest_point_sample(points, 64)

        # 每个批次的索引应该唯一
        for i in range(2):
            unique_indices = torch.unique(indices[i])
            assert len(unique_indices) == 64

    def test_valid_range(self):
        """测试索引范围"""
        num_points = 256
        points = torch.randn(2, num_points, 3)
        indices = farthest_point_sample(points, 32)

        assert indices.min() >= 0
        assert indices.max() < num_points


class TestRandomSamplePoints:
    """随机采样测试"""

    def test_downsample(self):
        """测试降采样"""
        points = np.random.randn(1000, 3)
        sampled = random_sample_points(points, 500)

        assert sampled.shape == (500, 3)

    def test_upsample(self):
        """测试上采样"""
        points = np.random.randn(100, 3)
        sampled = random_sample_points(points, 500)

        assert sampled.shape == (500, 3)


class TestComputePointCloudDistance:
    """点云距离测试"""

    def test_self_distance(self):
        """测试自身距离"""
        points = torch.randn(100, 3)
        dist = compute_point_cloud_distance(points, points)

        np.testing.assert_allclose(dist, 0, atol=1e-6)

    def test_symmetry(self):
        """测试对称性"""
        source = torch.randn(50, 3)
        target = torch.randn(50, 3)

        dist1 = compute_point_cloud_distance(source, target)
        dist2 = compute_point_cloud_distance(target, source)

        np.testing.assert_allclose(dist1, dist2, atol=1e-6)

    def test_numpy_input(self):
        """测试 NumPy 输入"""
        source = np.random.randn(50, 3).astype(np.float32)
        target = np.random.randn(50, 3).astype(np.float32)

        dist = compute_point_cloud_distance(source, target)
        assert isinstance(dist, float)
        assert dist >= 0


class TestVoxelDownsample:
    """体素下采样测试"""

    def test_reduces_size(self):
        """测试减少点数"""
        points = np.random.randn(1000, 3)
        downsampled = voxel_downsample(points, voxel_size=0.5)

        assert len(downsampled) < len(points)

    def test_preserves_bounds(self):
        """测试保持边界"""
        points = np.random.randn(500, 3)
        downsampled = voxel_downsample(points, voxel_size=0.1)

        # 下采样后的点应该在原始点的范围内
        assert downsampled.min() >= points.min() - 0.1
        assert downsampled.max() <= points.max() + 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
