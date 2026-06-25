"""
点云数据集

支持加载和生成点云数据，用于分类和分割任务。
"""

import numpy as np
import torch
from torch.utils.data import Dataset


def generate_random_pointcloud(num_points=1024, num_classes=10, num_samples=1000):
    """
    生成随机点云数据集

    用于快速测试和原型验证。

    Args:
        num_points: 每个点云的点数
        num_classes: 类别数
        num_samples: 样本数

    Returns:
        points: (num_samples, num_points, 3) 点云坐标
        labels: (num_samples,) 分类标签
    """
    points = np.random.randn(num_samples, num_points, 3).astype(np.float32)
    labels = np.random.randint(0, num_classes, size=num_samples)

    # 为不同类别添加不同的形状特征
    for i in range(num_samples):
        class_id = labels[i]
        # 简单的形状偏移
        points[i, :, 0] += class_id * 0.5
        points[i, :, 1] += class_id * 0.3
        points[i, :, 2] += class_id * 0.2

    return points, labels


def generate_segmentation_data(num_points=1024, num_parts=4, num_samples=1000):
    """
    生成分割数据集

    每个点有一个部件标签。

    Args:
        num_points: 每个点云的点数
        num_parts: 部件数
        num_samples: 样本数

    Returns:
        points: (num_samples, num_points, 3) 点云坐标
        seg_labels: (num_samples, num_points) 逐点标签
    """
    points = np.random.randn(num_samples, num_points, 3).astype(np.float32)
    seg_labels = np.zeros((num_samples, num_points), dtype=np.int64)

    for i in range(num_samples):
        # 根据 z 坐标分配部件标签
        z = points[i, :, 2]
        thresholds = np.linspace(z.min(), z.max(), num_parts + 1)
        for j in range(num_parts):
            mask = (z >= thresholds[j]) & (z < thresholds[j + 1])
            seg_labels[i, mask] = j

    return points, seg_labels


class PointCloudDataset(Dataset):
    """
    点云数据集

    支持分类和分割两种模式。
    """

    def __init__(self, points, labels, task="classification", transform=None):
        """
        Args:
            points: (N, num_points, 3) 点云坐标
            labels: 分类标签 (N,) 或分割标签 (N, num_points)
            task: "classification" 或 "segmentation"
            transform: 可选的数据增强
        """
        self.points = torch.FloatTensor(points)
        self.task = task

        if task == "classification":
            self.labels = torch.LongTensor(labels)
        else:
            self.labels = torch.LongTensor(labels)

        self.transform = transform

    def __len__(self):
        return len(self.points)

    def __getitem__(self, idx):
        points = self.points[idx]
        labels = self.labels[idx]

        # 数据增强
        if self.transform is not None:
            points = self.transform(points)

        # 转置为 (3, num_points) 以适应 Conv1d 输入
        points = points.transpose(0, 1)

        return points, labels


class PointCloudAugmentation:
    """
    点云数据增强

    包括随机旋转、缩放、平移和抖动。
    """

    def __init__(self, rotation_range=360, scale_range=(0.8, 1.2),
                 translate_range=0.1, jitter_std=0.01):
        self.rotation_range = rotation_range
        self.scale_range = scale_range
        self.translate_range = translate_range
        self.jitter_std = jitter_std

    def __call__(self, points):
        """
        Args:
            points: (num_points, 3) 点云

        Returns:
            augmented_points: (num_points, 3) 增强后的点云
        """
        points = points.clone()

        # 随机旋转 (绕 z 轴)
        angle = np.random.uniform(0, self.rotation_range) * np.pi / 180
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        rotation_matrix = torch.FloatTensor([
            [cos_a, -sin_a, 0],
            [sin_a, cos_a, 0],
            [0, 0, 1]
        ])
        points = torch.mm(points, rotation_matrix)

        # 随机缩放
        scale = np.random.uniform(*self.scale_range)
        points = points * scale

        # 随机平移
        translate = torch.FloatTensor(3).uniform_(-self.translate_range, self.translate_range)
        points = points + translate

        # 随机抖动
        jitter = torch.randn_like(points) * self.jitter_std
        points = points + jitter

        return points
