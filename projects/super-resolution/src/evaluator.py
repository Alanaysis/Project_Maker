"""
超分辨率模型评估器

实现 SRCNN 和 ESPCN 模型的评估功能
"""

import os
from typing import Dict, List, Tuple

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms
from PIL import Image
import numpy as np

from .models import get_model
from .dataset import SRTestDataset


class SREvaluator:
    """
    超分辨率模型评估器

    实现模型评估功能，包括：
    - PSNR（峰值信噪比）
    - SSIM（结构相似性）
    - 视觉对比

    Args:
        model_name (str): 模型名称
        scale_factor (int): 缩放因子
        device (str): 设备
    """

    def __init__(
        self,
        model_name: str = 'srcnn',
        scale_factor: int = 2,
        device: str = None
    ):
        self.model_name = model_name
        self.scale_factor = scale_factor
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')

        # 创建模型
        self.model = get_model(model_name, scale_factor=scale_factor)
        self.model.to(self.device)
        self.model.eval()

    def load_checkpoint(self, checkpoint_path: str):
        """
        加载模型检查点

        Args:
            checkpoint_path (str): 检查点文件路径
        """
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        print(f"Loaded checkpoint from {checkpoint_path}")

    def evaluate(
        self,
        test_dir: str,
        batch_size: int = 1,
        num_workers: int = 4
    ) -> Dict:
        """
        评估模型

        Args:
            test_dir (str): 测试数据目录
            batch_size (int): 批次大小
            num_workers (int): 数据加载线程数

        Returns:
            Dict: 评估结果
        """
        # 创建数据集
        test_dataset = SRTestDataset(
            test_dir,
            scale_factor=self.scale_factor
        )

        test_loader = DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers
        )

        # 评估
        psnr_list = []
        ssim_list = []

        with torch.no_grad():
            for lr_images, hr_images in test_loader:
                lr_images = lr_images.to(self.device)
                hr_images = hr_images.to(self.device)

                # 对于 SRCNN，需要先上采样低分辨率图像
                if self.model_name == 'srcnn':
                    lr_images = torch.nn.functional.interpolate(
                        lr_images,
                        size=hr_images.shape[2:],
                        mode='bicubic',
                        align_corners=False
                    )

                # 前向传播
                sr_images = self.model(lr_images)

                # 计算 PSNR
                psnr = self._calculate_psnr(sr_images, hr_images)
                psnr_list.append(psnr)

                # 计算 SSIM
                ssim = self._calculate_ssim(sr_images, hr_images)
                ssim_list.append(ssim)

        # 计算平均指标
        avg_psnr = np.mean(psnr_list)
        avg_ssim = np.mean(ssim_list)

        results = {
            'psnr': avg_psnr,
            'ssim': avg_ssim,
            'psnr_list': psnr_list,
            'ssim_list': ssim_list,
            'num_images': len(test_dataset)
        }

        return results

    def _calculate_psnr(
        self,
        sr_images: torch.Tensor,
        hr_images: torch.Tensor,
        max_pixel: float = 1.0
    ) -> float:
        """
        计算 PSNR（峰值信噪比）

        PSNR = 10 * log10(MAX^2 / MSE)

        Args:
            sr_images (torch.Tensor): 超分辨率图像
            hr_images (torch.Tensor): 高分辨率图像
            max_pixel (float): 最大像素值

        Returns:
            float: PSNR 值
        """
        mse = torch.mean((sr_images - hr_images) ** 2)

        if mse == 0:
            return float('inf')

        psnr = 10 * torch.log10(max_pixel ** 2 / mse)
        return psnr.item()

    def _calculate_ssim(
        self,
        sr_images: torch.Tensor,
        hr_images: torch.Tensor,
        window_size: int = 11,
        k1: float = 0.01,
        k2: float = 0.03,
        L: float = 1.0
    ) -> float:
        """
        计算 SSIM（结构相似性）

        SSIM = (2*μx*μy + C1)(2*σxy + C2) / ((μx^2 + μy^2 + C1)(σx^2 + σy^2 + C2))

        Args:
            sr_images (torch.Tensor): 超分辨率图像
            hr_images (torch.Tensor): 高分辨率图像
            window_size (int): 窗口大小
            k1 (float): 常数 1
            k2 (float): 常数 2
            L (float): 动态范围

        Returns:
            float: SSIM 值
        """
        c1 = (k1 * L) ** 2
        c2 = (k2 * L) ** 2

        # 创建高斯窗口
        window = self._create_gaussian_window(window_size, sr_images.device)

        # 计算均值
        mu_sr = torch.nn.functional.conv2d(sr_images, window, padding=window_size // 2, groups=sr_images.shape[1])
        mu_hr = torch.nn.functional.conv2d(hr_images, window, padding=window_size // 2, groups=hr_images.shape[1])

        # 计算方差和协方差
        mu_sr_sq = mu_sr ** 2
        mu_hr_sq = mu_hr ** 2
        mu_sr_hr = mu_sr * mu_hr

        sigma_sr_sq = torch.nn.functional.conv2d(sr_images ** 2, window, padding=window_size // 2, groups=sr_images.shape[1]) - mu_sr_sq
        sigma_hr_sq = torch.nn.functional.conv2d(hr_images ** 2, window, padding=window_size // 2, groups=hr_images.shape[1]) - mu_hr_sq
        sigma_sr_hr = torch.nn.functional.conv2d(sr_images * hr_images, window, padding=window_size // 2, groups=sr_images.shape[1]) - mu_sr_hr

        # 计算 SSIM
        numerator = (2 * mu_sr_hr + c1) * (2 * sigma_sr_hr + c2)
        denominator = (mu_sr_sq + mu_hr_sq + c1) * (sigma_sr_sq + sigma_hr_sq + c2)

        ssim_map = numerator / denominator
        ssim = ssim_map.mean()

        return ssim.item()

    def _create_gaussian_window(
        self,
        window_size: int,
        device: torch.device,
        sigma: float = 1.5
    ) -> torch.Tensor:
        """
        创建高斯窗口

        Args:
            window_size (int): 窗口大小
            device (torch.device): 设备
            sigma (float): 标准差

        Returns:
            torch.Tensor: 高斯窗口
        """
        coords = torch.arange(window_size, dtype=torch.float32, device=device) - window_size // 2
        g = torch.exp(-coords ** 2 / (2 * sigma ** 2))
        g = g / g.sum()

        window = g.unsqueeze(1) * g.unsqueeze(0)
        window = window.unsqueeze(0).unsqueeze(0)

        return window

    def upscale_image(
        self,
        lr_image_path: str,
        output_path: str = None
    ) -> Image.Image:
        """
        对单张图像进行超分辨率

        Args:
            lr_image_path (str): 低分辨率图像路径
            output_path (str): 输出路径（可选）

        Returns:
            Image.Image: 超分辨率后的图像
        """
        # 加载图像
        lr_image = Image.open(lr_image_path).convert('RGB')

        # 转换为张量
        to_tensor = transforms.ToTensor()
        lr_tensor = to_tensor(lr_image).unsqueeze(0).to(self.device)

        # 对于 SRCNN，需要先上采样
        if self.model_name == 'srcnn':
            lr_tensor = torch.nn.functional.interpolate(
                lr_tensor,
                scale_factor=self.scale_factor,
                mode='bicubic',
                align_corners=False
            )

        # 前向传播
        with torch.no_grad():
            sr_tensor = self.model(lr_tensor)

        # 转换为图像
        sr_tensor = sr_tensor.squeeze(0).cpu().clamp(0, 1)
        to_pil = transforms.ToPILImage()
        sr_image = to_pil(sr_tensor)

        # 保存图像
        if output_path:
            sr_image.save(output_path)
            print(f"Saved super-resolution image to {output_path}")

        return sr_image

    def compare_images(
        self,
        lr_image_path: str,
        hr_image_path: str,
        output_path: str = None
    ) -> Dict:
        """
        比较低分辨率、超分辨率和高分辨率图像

        Args:
            lr_image_path (str): 低分辨率图像路径
            hr_image_path (str): 高分辨率图像路径
            output_path (str): 输出路径（可选）

        Returns:
            Dict: 比较结果
        """
        # 加载图像
        lr_image = Image.open(lr_image_path).convert('RGB')
        hr_image = Image.open(hr_image_path).convert('RGB')

        # 转换为张量
        to_tensor = transforms.ToTensor()
        lr_tensor = to_tensor(lr_image).unsqueeze(0).to(self.device)
        hr_tensor = to_tensor(hr_image).unsqueeze(0).to(self.device)

        # 对于 SRCNN，需要先上采样
        if self.model_name == 'srcnn':
            lr_tensor = torch.nn.functional.interpolate(
                lr_tensor,
                size=hr_tensor.shape[2:],
                mode='bicubic',
                align_corners=False
            )

        # 前向传播
        with torch.no_grad():
            sr_tensor = self.model(lr_tensor)

        # 计算指标
        psnr = self._calculate_psnr(sr_tensor, hr_tensor)
        ssim = self._calculate_ssim(sr_tensor, hr_tensor)

        # 创建对比图像
        if output_path:
            sr_image = sr_tensor.squeeze(0).cpu().clamp(0, 1)
            to_pil = transforms.ToPILImage()
            sr_pil = to_pil(sr_image)

            # 创建对比图
            comparison = self._create_comparison(lr_image, sr_pil, hr_image)
            comparison.save(output_path)
            print(f"Saved comparison to {output_path}")

        return {
            'psnr': psnr,
            'ssim': ssim
        }

    def _create_comparison(
        self,
        lr_image: Image.Image,
        sr_image: Image.Image,
        hr_image: Image.Image
    ) -> Image.Image:
        """
        创建对比图像

        Args:
            lr_image (Image.Image): 低分辨率图像
            sr_image (Image.Image): 超分辨率图像
            hr_image (Image.Image): 高分辨率图像

        Returns:
            Image.Image: 对比图像
        """
        # 获取尺寸
        w, h = hr_image.size

        # 创建对比图像
        comparison = Image.new('RGB', (w * 3, h))

        # 调整低分辨率图像大小
        lr_resized = lr_image.resize((w, h), Image.BICUBIC)

        # 粘贴图像
        comparison.paste(lr_resized, (0, 0))
        comparison.paste(sr_image, (w, 0))
        comparison.paste(hr_image, (w * 2, 0))

        return comparison
