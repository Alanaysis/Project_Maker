"""
点云处理模块测试
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.data.point_cloud import PointCloud


class TestPointCloud:
    """点云类测试"""

    def setup_method(self):
        """测试前准备"""
        self.points = np.random.rand(1000, 4).astype(np.float32)
        self.pc = PointCloud(self.points)

    def test_init(self):
        """测试初始化"""
        assert self.pc.points.shape == (1000, 4)
        assert self.pc.points.dtype == np.float32

    def test_num_points(self):
        """测试点数属性"""
        assert self.pc.num_points == 1000

    def test_num_features(self):
        """测试特征维度属性"""
        assert self.pc.num_features == 4

    def test_filter_by_range(self):
        """测试范围过滤"""
        x_range = (-10, 10)
        y_range = (-10, 10)
        z_range = (-3, 1)

        # 创建在范围内的点云
        points_in_range = np.random.rand(100, 4).astype(np.float32)
        points_in_range[:, 0] = points_in_range[:, 0] * 20 - 10  # [-10, 10]
        points_in_range[:, 1] = points_in_range[:, 1] * 20 - 10  # [-10, 10]
        points_in_range[:, 2] = points_in_range[:, 2] * 4 - 3    # [-3, 1]

        pc = PointCloud(points_in_range)
        filtered = pc.filter_by_range(x_range, y_range, z_range)

        # 验证过滤后的点在范围内
        assert np.all(filtered.points[:, 0] >= x_range[0])
        assert np.all(filtered.points[:, 0] <= x_range[1])
        assert np.all(filtered.points[:, 1] >= y_range[0])
        assert np.all(filtered.points[:, 1] <= y_range[1])
        assert np.all(filtered.points[:, 2] >= z_range[0])
        assert np.all(filtered.points[:, 2] <= z_range[1])

    def test_downsample(self):
        """测试降采样"""
        voxel_size = 0.1
        downsampled = self.pc.downsample(voxel_size)

        # 验证降采样后点数减少
        assert downsampled.points.shape[0] <= self.pc.points.shape[0]

    def test_remove_ground(self):
        """测试地面点去除"""
        # 创建包含地面点的点云
        ground_points = np.random.rand(100, 4).astype(np.float32)
        ground_points[:, 2] = -1.5  # 地面高度

        object_points = np.random.rand(100, 4).astype(np.float32)
        object_points[:, 2] = 0.5  # 物体高度

        all_points = np.vstack([ground_points, object_points])
        pc = PointCloud(all_points)

        non_ground = pc.remove_ground()

        # 验证地面点被去除
        assert non_ground.points.shape[0] < all_points.shape[0]
        assert np.all(non_ground.points[:, 2] > -1.5)

    def test_translate(self):
        """测试平移"""
        translation = np.array([1.0, 2.0, 3.0])
        translated = self.pc.translate(translation)

        # 验证平移后的坐标
        expected = self.points[:, :3] + translation
        np.testing.assert_array_almost_equal(translated.points[:, :3], expected)

    def test_rotate(self):
        """测试旋转"""
        # 创建 90 度旋转矩阵
        rotation_matrix = np.array([
            [0, -1, 0],
            [1, 0, 0],
            [0, 0, 1]
        ])

        rotated = self.pc.rotate(rotation_matrix)

        # 验证旋转后的坐标
        expected = self.points[:, :3] @ rotation_matrix.T
        np.testing.assert_array_almost_equal(rotated.points[:, :3], expected)

    def test_scale(self):
        """测试缩放"""
        scale_factor = 2.0
        scaled = self.pc.scale(scale_factor)

        # 验证缩放后的坐标
        expected = self.points[:, :3] * scale_factor
        np.testing.assert_array_almost_equal(scaled.points[:, :3], expected)

    def test_get_bounding_box(self):
        """测试获取边界框"""
        min_point, max_point = self.pc.get_bounding_box()

        # 验证边界框
        assert np.all(min_point <= max_point)
        assert np.all(min_point == self.points[:, :3].min(axis=0))
        assert np.all(max_point == self.points[:, :3].max(axis=0))

    def test_get_centroid(self):
        """测试获取质心"""
        centroid = self.pc.get_centroid()

        # 验证质心
        expected = self.points[:, :3].mean(axis=0)
        np.testing.assert_array_almost_equal(centroid, expected)

    def test_len(self):
        """测试长度"""
        assert len(self.pc) == 1000

    def test_repr(self):
        """测试字符串表示"""
        repr_str = repr(self.pc)
        assert 'PointCloud' in repr_str
        assert '1000' in repr_str
        assert '4' in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
