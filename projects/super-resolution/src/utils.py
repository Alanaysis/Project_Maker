"""
超分辨率工具函数

实现常用的工具函数
"""

import os
import random
from typing import Tuple, List

import torch
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt


def set_seed(seed: int = 42):
    """
    设置随机种子

    Args:
        seed (int): 随机种子
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)


def calculate_psnr(
    sr_image: np.ndarray,
    hr_image: np.ndarray,
    max_pixel: float = 255.0
) -> float:
    """
    计算 PSNR（峰值信噪比）

    Args:
        sr_image (np.ndarray): 超分辨率图像
        hr_image (np.ndarray): 高分辨率图像
        max_pixel (float): 最大像素值

    Returns:
        float: PSNR 值
    """
    mse = np.mean((sr_image - hr_image) ** 2)

    if mse == 0:
        return float('inf')

    psnr = 10 * np.log10(max_pixel ** 2 / mse)
    return psnr


def calculate_ssim(
    sr_image: np.ndarray,
    hr_image: np.ndarray,
    window_size: int = 11,
    k1: float = 0.01,
    k2: float = 0.03,
    L: float = 255.0
) -> float:
    """
    计算 SSIM（结构相似性）

    Args:
        sr_image (np.ndarray): 超分辨率图像
        hr_image (np.ndarray): 高分辨率图像
        window_size (int): 窗口大小
        k1 (float): 常数 1
        k2 (float): 常数 2
        L (float): 动态范围

    Returns:
        float: SSIM 值
    """
    c1 = (k1 * L) ** 2
    c2 = (k2 * L) ** 2

    # 计算均值
    mu_sr = np.mean(sr_image)
    mu_hr = np.mean(hr_image)

    # 计算方差和协方差
    sigma_sr_sq = np.var(sr_image)
    sigma_hr_sq = np.var(hr_image)
    sigma_sr_hr = np.cov(sr_image.flatten(), hr_image.flatten())[0, 1]

    # 计算 SSIM
    numerator = (2 * mu_sr * mu_hr + c1) * (2 * sigma_sr_hr + c2)
    denominator = (mu_sr ** 2 + mu_hr ** 2 + c1) * (sigma_sr_sq + sigma_hr_sq + c2)

    ssim = numerator / denominator
    return ssim


def visualize_results(
    lr_image: Image.Image,
    sr_image: Image.Image,
    hr_image: Image.Image,
    save_path: str = None
):
    """
    可视化超分辨率结果

    Args:
        lr_image (Image.Image): 低分辨率图像
        sr_image (Image.Image): 超分辨率图像
        hr_image (Image.Image): 高分辨率图像
        save_path (str): 保存路径
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # 低分辨率图像
    axes[0].imshow(lr_image)
    axes[0].set_title('Low Resolution')
    axes[0].axis('off')

    # 超分辨率图像
    axes[1].imshow(sr_image)
    axes[1].set_title('Super Resolution')
    axes[1].axis('off')

    # 高分辨率图像
    axes[2].imshow(hr_image)
    axes[2].set_title('High Resolution')
    axes[2].axis('off')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved visualization to {save_path}")

    plt.show()


def plot_training_history(
    history: dict,
    save_path: str = None
):
    """
    绘制训练历史

    Args:
        history (dict): 训练历史
        save_path (str): 保存路径
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # 训练损失
    axes[0].plot(history['train_loss'], label='Train Loss')
    if 'val_loss' in history:
        axes[0].plot(history['val_loss'], label='Val Loss')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training Loss')
    axes[0].legend()
    axes[0].grid(True)

    # 学习率
    axes[1].plot(history['learning_rate'])
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Learning Rate')
    axes[1].set_title('Learning Rate Schedule')
    axes[1].grid(True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved training history to {save_path}")

    plt.show()


def count_parameters(model: torch.nn.Module) -> int:
    """
    计算模型参数数量

    Args:
        model (torch.nn.Module): 模型

    Returns:
        int: 参数数量
    """
    return sum(p.numel() for p in model.parameters())


def get_image_size(image_path: str) -> Tuple[int, int]:
    """
    获取图像尺寸

    Args:
        image_path (str): 图像路径

    Returns:
        Tuple[int, int]: (宽度, 高度)
    """
    with Image.open(image_path) as img:
        return img.size


def create_directory(path: str):
    """
    创建目录

    Args:
        path (str): 目录路径
    """
    os.makedirs(path, exist_ok=True)


def list_images(directory: str, extensions: List[str] = None) -> List[str]:
    """
    列出目录中的图像文件

    Args:
        directory (str): 目录路径
        extensions (List[str]): 文件扩展名列表

    Returns:
        List[str]: 图像文件路径列表
    """
    if extensions is None:
        extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']

    images = []
    for f in os.listdir(directory):
        if any(f.lower().endswith(ext) for ext in extensions):
            images.append(os.path.join(directory, f))

    return sorted(images)
