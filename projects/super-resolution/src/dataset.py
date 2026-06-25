"""
超分辨率数据集

实现超分辨率训练和评估的数据集加载
"""

import os
import random
from typing import Tuple, Optional

import torch
from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image
import numpy as np


class SRDataset(Dataset):
    """
    超分辨率数据集

    用于训练和评估超分辨率模型。

    数据处理流程：
    1. 加载高分辨率图像
    2. 随机裁剪训练块
    3. 降采样生成低分辨率图像
    4. 数据增强（可选）

    Args:
        hr_dir (str): 高分辨率图像目录
        scale_factor (int): 缩放因子，默认 2
        patch_size (int): 训练块大小，默认 96
        is_training (bool): 是否为训练模式
        augment (bool): 是否进行数据增强
    """

    def __init__(
        self,
        hr_dir: str,
        scale_factor: int = 2,
        patch_size: int = 96,
        is_training: bool = True,
        augment: bool = True
    ):
        self.hr_dir = hr_dir
        self.scale_factor = scale_factor
        self.patch_size = patch_size
        self.is_training = is_training
        self.augment = augment

        # 获取所有图像文件
        self.hr_images = [
            os.path.join(hr_dir, f)
            for f in os.listdir(hr_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))
        ]

        if len(self.hr_images) == 0:
            raise ValueError(f"No images found in {hr_dir}")

        # 图像变换
        self.to_tensor = transforms.ToTensor()

    def __len__(self):
        return len(self.hr_images)

    def __getitem__(self, idx):
        """
        获取数据集中的一个样本

        Args:
            idx (int): 索引

        Returns:
            Tuple[torch.Tensor, torch.Tensor]: (低分辨率图像, 高分辨率图像)
        """
        # 加载高分辨率图像
        hr_image = Image.open(self.hr_images[idx]).convert('RGB')

        if self.is_training:
            # 训练模式：随机裁剪
            hr_image = self._random_crop(hr_image)

            # 数据增强
            if self.augment:
                hr_image = self._augment(hr_image)
        else:
            # 评估模式：确保图像尺寸可被 scale_factor 整除
            hr_image = self._adjust_size(hr_image)

        # 转换为张量
        hr_tensor = self.to_tensor(hr_image)

        # 生成低分辨率图像
        lr_tensor = self._downsample(hr_tensor)

        return lr_tensor, hr_tensor

    def _random_crop(self, image: Image.Image) -> Image.Image:
        """
        随机裁剪训练块

        Args:
            image (Image.Image): 输入图像

        Returns:
            Image.Image: 裁剪后的图像
        """
        w, h = image.size

        # 确保图像足够大
        if w < self.patch_size or h < self.patch_size:
            image = image.resize((self.patch_size, self.patch_size), Image.BICUBIC)
            w, h = image.size

        # 随机裁剪位置
        x = random.randint(0, w - self.patch_size)
        y = random.randint(0, h - self.patch_size)

        return image.crop((x, y, x + self.patch_size, y + self.patch_size))

    def _adjust_size(self, image: Image.Image) -> Image.Image:
        """
        调整图像尺寸，确保可被 scale_factor 整除

        Args:
            image (Image.Image): 输入图像

        Returns:
            Image.Image: 调整后的图像
        """
        w, h = image.size

        # 裁剪到 scale_factor 的整数倍
        new_w = (w // self.scale_factor) * self.scale_factor
        new_h = (h // self.scale_factor) * self.scale_factor

        return image.crop((0, 0, new_w, new_h))

    def _downsample(self, hr_tensor: torch.Tensor) -> torch.Tensor:
        """
        降采样生成低分辨率图像

        使用双三次插值进行降采样。

        Args:
            hr_tensor (torch.Tensor): 高分辨率图像张量

        Returns:
            torch.Tensor: 低分辨率图像张量
        """
        # 获取高分辨率图像尺寸
        c, h, w = hr_tensor.shape

        # 计算低分辨率尺寸
        lr_h = h // self.scale_factor
        lr_w = w // self.scale_factor

        # 使用双三次插值降采样
        lr_tensor = torch.nn.functional.interpolate(
            hr_tensor.unsqueeze(0),
            size=(lr_h, lr_w),
            mode='bicubic',
            align_corners=False
        ).squeeze(0)

        return lr_tensor

    def _augment(self, image: Image.Image) -> Image.Image:
        """
        数据增强

        Args:
            image (Image.Image): 输入图像

        Returns:
            Image.Image: 增强后的图像
        """
        # 随机水平翻转
        if random.random() > 0.5:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)

        # 随机垂直翻转
        if random.random() > 0.5:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)

        # 随机旋转 90 度
        if random.random() > 0.5:
            image = image.transpose(Image.ROTATE_90)

        return image


class SRTestDataset(Dataset):
    """
    超分辨率测试数据集

    用于评估超分辨率模型。

    Args:
        hr_dir (str): 高分辨率图像目录
        lr_dir (str): 低分辨率图像目录（可选）
        scale_factor (int): 缩放因子，默认 2
    """

    def __init__(
        self,
        hr_dir: str,
        lr_dir: Optional[str] = None,
        scale_factor: int = 2
    ):
        self.hr_dir = hr_dir
        self.lr_dir = lr_dir
        self.scale_factor = scale_factor

        # 获取所有图像文件
        self.hr_images = sorted([
            os.path.join(hr_dir, f)
            for f in os.listdir(hr_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))
        ])

        if lr_dir:
            self.lr_images = sorted([
                os.path.join(lr_dir, f)
                for f in os.listdir(lr_dir)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))
            ])
        else:
            self.lr_images = None

        # 图像变换
        self.to_tensor = transforms.ToTensor()

    def __len__(self):
        return len(self.hr_images)

    def __getitem__(self, idx):
        """
        获取数据集中的一个样本

        Args:
            idx (int): 索引

        Returns:
            Tuple[torch.Tensor, torch.Tensor]: (低分辨率图像, 高分辨率图像)
        """
        # 加载高分辨率图像
        hr_image = Image.open(self.hr_images[idx]).convert('RGB')

        # 调整尺寸
        hr_image = self._adjust_size(hr_image)

        # 转换为张量
        hr_tensor = self.to_tensor(hr_image)

        # 生成或加载低分辨率图像
        if self.lr_images:
            lr_image = Image.open(self.lr_images[idx]).convert('RGB')
            lr_tensor = self.to_tensor(lr_image)
        else:
            lr_tensor = self._downsample(hr_tensor)

        return lr_tensor, hr_tensor

    def _adjust_size(self, image: Image.Image) -> Image.Image:
        """调整图像尺寸"""
        w, h = image.size
        new_w = (w // self.scale_factor) * self.scale_factor
        new_h = (h // self.scale_factor) * self.scale_factor
        return image.crop((0, 0, new_w, new_h))

    def _downsample(self, hr_tensor: torch.Tensor) -> torch.Tensor:
        """降采样"""
        c, h, w = hr_tensor.shape
        lr_h = h // self.scale_factor
        lr_w = w // self.scale_factor

        lr_tensor = torch.nn.functional.interpolate(
            hr_tensor.unsqueeze(0),
            size=(lr_h, lr_w),
            mode='bicubic',
            align_corners=False
        ).squeeze(0)

        return lr_tensor


def create_synthetic_dataset(
    output_dir: str,
    num_images: int = 100,
    image_size: int = 256
):
    """
    创建合成数据集用于测试

    Args:
        output_dir (str): 输出目录
        num_images (int): 图像数量
        image_size (int): 图像尺寸
    """
    os.makedirs(output_dir, exist_ok=True)

    for i in range(num_images):
        # 创建随机图像
        image = np.random.randint(0, 256, (image_size, image_size, 3), dtype=np.uint8)

        # 添加一些图案
        x, y = np.meshgrid(np.linspace(0, 1, image_size), np.linspace(0, 1, image_size))
        pattern = np.sin(2 * np.pi * (4 * x + 4 * y)) * 127 + 128

        image[:, :, 0] = pattern.astype(np.uint8)
        image[:, :, 1] = (pattern * 0.5).astype(np.uint8)
        image[:, :, 2] = (pattern * 0.3).astype(np.uint8)

        # 保存图像
        img = Image.fromarray(image)
        img.save(os.path.join(output_dir, f'image_{i:04d}.png'))

    print(f"Created {num_images} synthetic images in {output_dir}")
