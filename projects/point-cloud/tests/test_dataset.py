"""
数据集测试
"""

import pytest
import numpy as np
import torch

from src.dataset import (
    generate_random_pointcloud,
    generate_segmentation_data,
    PointCloudDataset,
    PointCloudAugmentation,
)


class TestGenerateRandomPointcloud:
    """随机点云生成测试"""

    def test_shape(self):
        """测试生成形状"""
        points, labels = generate_random_pointcloud(
            num_points=512, num_classes=10, num_samples=100
        )

        assert points.shape == (100, 512, 3)
        assert labels.shape == (100,)

    def test_label_range(self):
        """测试标签范围"""
        num_classes = 5
        _, labels = generate_random_pointcloud(num_classes=num_classes, num_samples=1000)

        assert labels.min() >= 0
        assert labels.max() < num_classes

    def test_dtype(self):
        """测试数据类型"""
        points, labels = generate_random_pointcloud()

        assert points.dtype == np.float32
        assert labels.dtype == np.int64 or labels.dtype == np.int32


class TestGenerateSegmentationData:
    """分割数据生成测试"""

    def test_shape(self):
        """测试生成形状"""
        points, seg_labels = generate_segmentation_data(
            num_points=512, num_parts=4, num_samples=100
        )

        assert points.shape == (100, 512, 3)
        assert seg_labels.shape == (100, 512)

    def test_label_range(self):
        """测试标签范围"""
        num_parts = 4
        _, seg_labels = generate_segmentation_data(num_parts=num_parts)

        assert seg_labels.min() >= 0
        assert seg_labels.max() < num_parts


class TestPointCloudDataset:
    """点云数据集测试"""

    def test_classification_dataset(self):
        """测试分类数据集"""
        points = np.random.randn(50, 256, 3).astype(np.float32)
        labels = np.random.randint(0, 10, size=50)

        dataset = PointCloudDataset(points, labels, task="classification")

        assert len(dataset) == 50

        points_out, label_out = dataset[0]
        assert points_out.shape == (3, 256)  # 转置后的形状
        assert label_out.dim() == 0  # 标量

    def test_segmentation_dataset(self):
        """测试分割数据集"""
        points = np.random.randn(50, 256, 3).astype(np.float32)
        seg_labels = np.random.randint(0, 4, size=(50, 256))

        dataset = PointCloudDataset(points, seg_labels, task="segmentation")

        assert len(dataset) == 50

        points_out, labels_out = dataset[0]
        assert points_out.shape == (3, 256)
        assert labels_out.shape == (256,)

    def test_with_transform(self):
        """测试带数据增强"""
        points = np.random.randn(10, 128, 3).astype(np.float32)
        labels = np.random.randint(0, 5, size=10)

        augmentation = PointCloudAugmentation()
        dataset = PointCloudDataset(points, labels, transform=augmentation)

        points_out, _ = dataset[0]
        assert points_out.shape == (3, 128)

    def test_dataloader_compatibility(self):
        """测试与 DataLoader 的兼容性"""
        from torch.utils.data import DataLoader

        points = np.random.randn(20, 64, 3).astype(np.float32)
        labels = np.random.randint(0, 5, size=20)

        dataset = PointCloudDataset(points, labels)
        dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

        batch_points, batch_labels = next(iter(dataloader))
        assert batch_points.shape == (4, 3, 64)
        assert batch_labels.shape == (4,)


class TestPointCloudAugmentation:
    """数据增强测试"""

    def test_rotation(self):
        """测试旋转"""
        augmentation = PointCloudAugmentation(rotation_range=90)
        points = torch.randn(100, 3)

        augmented = augmentation(points)

        assert augmented.shape == points.shape
        # 旋转后数据应该不同
        assert not torch.allclose(points, augmented, atol=1e-6)

    def test_scale(self):
        """测试缩放"""
        augmentation = PointCloudAugmentation(
            scale_range=(2.0, 2.0), rotation_range=0,
            translate_range=0, jitter_std=0
        )
        points = torch.randn(100, 3)

        augmented = augmentation(points)

        # 缩放 2 倍
        assert torch.allclose(augmented, points * 2, atol=1e-5)

    def test_jitter(self):
        """测试抖动"""
        augmentation = PointCloudAugmentation(
            rotation_range=0, scale_range=(1.0, 1.0),
            translate_range=0, jitter_std=0.1
        )
        points = torch.randn(100, 3)

        augmented = augmentation(points)

        # 仅抖动，形状相同但值不同
        assert augmented.shape == points.shape

    def test_preserves_shape(self):
        """测试保持形状"""
        augmentation = PointCloudAugmentation()

        for num_points in [64, 256, 1024]:
            points = torch.randn(num_points, 3)
            augmented = augmentation(points)
            assert augmented.shape == points.shape


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
