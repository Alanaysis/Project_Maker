"""
深度估计数据集

提供合成数据集用于测试和学习:
- SyntheticDepthDataset: 生成带有深度信息的合成图像
- 支持多种场景模式 (平面、斜面、阶梯、球体等)
"""

import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import Tuple, Optional, List


class SyntheticDepthDataset(Dataset):
    """
    合成深度估计数据集

    生成带有对应深度图的合成图像，用于测试深度估计模型。
    支持多种场景模式，每种模式生成不同的深度分布。

    Args:
        num_samples: 样本数量
        image_size: 图像尺寸 (H, W)
        scene_types: 场景类型列表，可选值: 'plane', 'slope', 'stairs', 'sphere', 'random'
        depth_range: 深度范围 (min_depth, max_depth)
        add_noise: 是否添加噪声
        transform: 图像变换

    Example:
        >>> dataset = SyntheticDepthDataset(num_samples=100, image_size=(128, 128))
        >>> image, depth, mask = dataset[0]
        >>> print(image.shape)  # (3, 128, 128)
        >>> print(depth.shape)  # (1, 128, 128)
    """

    SCENE_TYPES = ["plane", "slope", "stairs", "sphere", "random"]

    def __init__(
        self,
        num_samples: int = 1000,
        image_size: Tuple[int, int] = (128, 128),
        scene_types: Optional[List[str]] = None,
        depth_range: Tuple[float, float] = (0.1, 10.0),
        add_noise: bool = True,
        noise_std: float = 0.05,
    ):
        super().__init__()
        self.num_samples = num_samples
        self.image_size = image_size
        self.depth_range = depth_range
        self.add_noise = add_noise
        self.noise_std = noise_std

        if scene_types is None:
            self.scene_types = self.SCENE_TYPES
        else:
            self.scene_types = scene_types

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        获取样本

        Args:
            idx: 样本索引

        Returns:
            (image, depth, valid_mask) 元组
        """
        # 随机选择场景类型
        scene_type = self.scene_types[idx % len(self.scene_types)]
        if scene_type == "random":
            scene_type = np.random.choice(self.SCENE_TYPES[:4])

        # 生成深度图
        depth = self._generate_depth(scene_type)

        # 生成对应的图像
        image = self._generate_image(depth)

        # 添加噪声
        if self.add_noise:
            depth = depth + torch.randn_like(depth) * self.noise_std
            depth = torch.clamp(depth, min=self.depth_range[0])

        # 有效掩码 (深度值在有效范围内)
        valid_mask = ((depth > self.depth_range[0]) & (depth < self.depth_range[1])).float()

        return image, depth, valid_mask

    def _generate_depth(self, scene_type: str) -> torch.Tensor:
        """
        生成深度图

        Args:
            scene_type: 场景类型

        Returns:
            深度图 (1, H, W)
        """
        h, w = self.image_size
        y, x = torch.meshgrid(
            torch.linspace(-1, 1, h),
            torch.linspace(-1, 1, w),
            indexing="ij",
        )

        min_d, max_d = self.depth_range

        if scene_type == "plane":
            # 平面: 均匀深度
            depth_value = np.random.uniform(min_d, max_d)
            depth = torch.full((1, h, w), depth_value)

        elif scene_type == "slope":
            # 斜面: 深度随位置线性变化
            angle = np.random.uniform(0, 2 * np.pi)
            slope_dir = torch.cos(torch.tensor(angle)) * x + torch.sin(torch.tensor(angle)) * y
            depth = min_d + (max_d - min_d) * (slope_dir + 1) / 2
            depth = depth.unsqueeze(0)

        elif scene_type == "stairs":
            # 阶梯: 多个深度层级
            num_steps = np.random.randint(3, 8)
            step_size = (max_d - min_d) / num_steps
            step_width = w // num_steps

            depth = torch.zeros(1, h, w)
            for i in range(num_steps):
                start_x = i * step_width
                end_x = min((i + 1) * step_width, w)
                depth[0, :, start_x:end_x] = min_d + i * step_size

        elif scene_type == "sphere":
            # 球体: 中心近，边缘远
            cx = np.random.uniform(-0.5, 0.5)
            cy = np.random.uniform(-0.5, 0.5)
            radius = np.random.uniform(0.3, 0.8)

            dist = torch.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            depth = min_d + (max_d - min_d) * (dist / radius)
            depth = torch.clamp(depth, max=max_d)
            depth = depth.unsqueeze(0)

        else:
            # 默认: 随机深度
            depth = torch.rand(1, h, w) * (max_d - min_d) + min_d

        return depth

    def _generate_image(self, depth: torch.Tensor) -> torch.Tensor:
        """
        根据深度图生成合成图像

        使用深度信息生成带有颜色和纹理的合成图像:
        - 近处物体偏暖色调
        - 远处物体偏冷色调
        - 添加一些纹理

        Args:
            depth: 深度图 (1, H, W)

        Returns:
            合成图像 (3, H, W)
        """
        # 归一化深度到 [0, 1]
        depth_norm = (depth - self.depth_range[0]) / (self.depth_range[1] - self.depth_range[0])
        depth_norm = torch.clamp(depth_norm, 0, 1)

        # 生成颜色通道
        # R: 近处更红
        r = 1.0 - 0.5 * depth_norm
        # G: 中间距离更绿
        g = 0.5 + 0.3 * torch.sin(depth_norm * np.pi)
        # B: 远处更蓝
        b = 0.3 + 0.7 * depth_norm

        # 合成图像
        image = torch.cat([r, g, b], dim=0)

        # 添加纹理
        h, w = depth.shape[1], depth.shape[2]
        texture = torch.rand(3, h, w) * 0.2
        image = image + texture

        # 添加条纹模式
        stripe_freq = np.random.uniform(5, 20)
        y_coords = torch.linspace(0, stripe_freq * np.pi, h).unsqueeze(1).expand(h, w)
        stripe = torch.sin(y_coords).unsqueeze(0) * 0.1
        image = image + stripe

        image = torch.clamp(image, 0, 1)

        return image


def create_dataloader(
    dataset: Dataset,
    batch_size: int = 16,
    shuffle: bool = True,
    num_workers: int = 0,
) -> DataLoader:
    """
    创建数据加载器

    Args:
        dataset: 数据集
        batch_size: 批量大小
        shuffle: 是否打乱
        num_workers: 工作进程数

    Returns:
        DataLoader 对象
    """
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True,
    )


def generate_random_batch(
    batch_size: int = 4,
    image_size: Tuple[int, int] = (128, 128),
    depth_range: Tuple[float, float] = (0.1, 10.0),
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    生成随机批量数据 (用于快速测试)

    Args:
        batch_size: 批量大小
        image_size: 图像尺寸
        depth_range: 深度范围

    Returns:
        (images, depths, masks) 元组
    """
    h, w = image_size

    # 生成随机图像
    images = torch.rand(batch_size, 3, h, w)

    # 生成随机深度图
    min_d, max_d = depth_range
    depths = torch.rand(batch_size, 1, h, w) * (max_d - min_d) + min_d

    # 生成掩码
    masks = torch.ones(batch_size, 1, h, w)

    return images, depths, masks
