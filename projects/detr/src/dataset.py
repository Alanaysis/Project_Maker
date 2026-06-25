"""
数据集模块
用于目标检测任务的数据集和数据增强
"""

import torch
import torch.utils.data as data
import numpy as np
from typing import Dict, List, Tuple, Optional
import random


class SimpleDetectionDataset(data.Dataset):
    """
    简单目标检测数据集
    用于演示和测试
    """
    def __init__(self, num_samples=1000, image_size=320, num_classes=5, max_objects=5):
        """
        Args:
            num_samples: 样本数量
            image_size: 图像尺寸
            num_classes: 类别数量
            max_objects: 每张图像的最大对象数量
        """
        self.num_samples = num_samples
        self.image_size = image_size
        self.num_classes = num_classes
        self.max_objects = max_objects

        # 预生成一些数据
        self.data = self._generate_data()

    def _generate_data(self):
        """
        生成模拟数据
        """
        data_list = []
        for _ in range(self.num_samples):
            num_objects = random.randint(1, self.max_objects)
            image, boxes, labels = self._generate_sample(num_objects)
            data_list.append({
                'image': image,
                'boxes': boxes,
                'labels': labels
            })
        return data_list

    def _generate_sample(self, num_objects):
        """
        生成单个样本

        Returns:
            image: (3, H, W) 图像
            boxes: (N, 4) 边界框 [cx, cy, w, h] (归一化坐标)
            labels: (N,) 类别标签
        """
        # 生成背景图像
        image = torch.rand(3, self.image_size, self.image_size)

        boxes = []
        labels = []

        for _ in range(num_objects):
            # 随机生成边界框
            cx = random.uniform(0.2, 0.8)
            cy = random.uniform(0.2, 0.8)
            w = random.uniform(0.1, 0.3)
            h = random.uniform(0.1, 0.3)

            boxes.append([cx, cy, w, h])
            labels.append(random.randint(0, self.num_classes - 1))

            # 在图像上绘制矩形（简单模拟）
            x1 = int((cx - w/2) * self.image_size)
            y1 = int((cy - h/2) * self.image_size)
            x2 = int((cx + w/2) * self.image_size)
            y2 = int((cy + h/2) * self.image_size)

            x1 = max(0, min(x1, self.image_size-1))
            y1 = max(0, min(y1, self.image_size-1))
            x2 = max(0, min(x2, self.image_size-1))
            y2 = max(0, min(y2, self.image_size-1))

            # 用随机颜色填充区域
            color = torch.rand(3, 1, 1)
            image[:, y1:y2, x1:x2] = color * 0.5 + image[:, y1:y2, x1:x2] * 0.5

        return image, torch.tensor(boxes, dtype=torch.float32), torch.tensor(labels, dtype=torch.int64)

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        return self.data[idx]


def collate_fn(batch):
    """
    自定义批处理函数
    处理不同数量的目标
    """
    images = torch.stack([item['image'] for item in batch])
    targets = [{'boxes': item['boxes'], 'labels': item['labels']} for item in batch]
    return images, targets


def create_simple_dataset(num_samples=1000, image_size=320, num_classes=5, max_objects=5):
    """
    创建简单数据集
    """
    dataset = SimpleDetectionDataset(num_samples, image_size, num_classes, max_objects)
    return dataset
