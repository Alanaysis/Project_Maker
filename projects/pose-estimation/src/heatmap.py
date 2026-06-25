"""
热力图生成与处理 (Heatmap Generation and Processing).

热力图回归是姿态估计的核心技术之一：
1. 为每个关键点生成高斯热力图 (Ground Truth)
2. 网络预测热力图
3. 从预测热力图中提取关键点坐标

数学原理:
- 高斯热力图: H(x,y) = exp(-((x-x_k)^2 + (y-y_k)^2) / (2*sigma^2))
- 关键点提取: argmax 或 soft-argmax
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Optional


def generate_heatmaps(
    keypoints: torch.Tensor,
    keypoint_weights: torch.Tensor,
    heatmap_size: Tuple[int, int],
    sigma: float = 2.0,
) -> torch.Tensor:
    """
    从关键点坐标生成高斯热力图。

    Args:
        keypoints: 关键点坐标 (batch, num_keypoints, 2)，值域 [0, 1] 归一化坐标
        keypoint_weights: 关键点可见性权重 (batch, num_keypoints)，0 或 1
        heatmap_size: 热力图尺寸 (H, W)
        sigma: 高斯核标准差

    Returns:
        heatmaps: 高斯热力图 (batch, num_keypoints, H, W)
    """
    batch_size, num_keypoints, _ = keypoints.shape
    h, w = heatmap_size
    device = keypoints.device

    # 创建坐标网格
    y_coords = torch.arange(h, device=device, dtype=torch.float32)
    x_coords = torch.arange(w, device=device, dtype=torch.float32)
    y_grid, x_grid = torch.meshgrid(y_coords, x_coords, indexing="ij")
    # y_grid, x_grid: (H, W)

    # 将归一化关键点坐标转换为热力图像素坐标
    # keypoint (x, y) 范围 [0, 1] -> 像素坐标范围 [0, W-1] 和 [0, H-1]
    kx = keypoints[:, :, 0] * (w - 1)  # (batch, K)
    ky = keypoints[:, :, 1] * (h - 1)  # (batch, K)

    # 计算高斯热力图
    # 扩展维度进行广播
    # kx: (batch, K, 1, 1), x_grid: (1, 1, H, W)
    kx = kx[:, :, None, None]
    ky = ky[:, :, None, None]

    # H(x,y) = exp(-((x-x_k)^2 + (y-y_k)^2) / (2*sigma^2))
    heatmaps = torch.exp(
        -((x_grid[None, None] - kx) ** 2 + (y_grid[None, None] - ky) ** 2)
        / (2 * sigma ** 2)
    )  # (batch, K, H, W)

    # 应用可见性权重，不可见的关键点热力图为全零
    weights = keypoint_weights[:, :, None, None]  # (batch, K, 1, 1)
    heatmaps = heatmaps * weights

    return heatmaps


def heatmaps_to_keypoints(heatmaps: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    从热力图中提取关键点坐标 (使用 argmax)。

    Args:
        heatmaps: 热力图 (batch, num_keypoints, H, W)

    Returns:
        keypoints: 关键点坐标 (batch, num_keypoints, 2)，归一化坐标 [0, 1]
        confidence: 关键点置信度 (batch, num_keypoints)
    """
    batch_size, num_keypoints, h, w = heatmaps.shape

    # 展平空间维度
    heatmaps_flat = heatmaps.view(batch_size, num_keypoints, -1)  # (B, K, H*W)

    # 找到最大值和位置
    confidence, max_idx = torch.max(heatmaps_flat, dim=2)  # (B, K)

    # 转换为 2D 坐标 (使用整数除法)
    y_coords = (max_idx // w).float()  # 行坐标
    x_coords = (max_idx % w).float()   # 列坐标

    # 归一化到 [0, 1]
    x_norm = x_coords / (w - 1)
    y_norm = y_coords / (h - 1)

    keypoints = torch.stack([x_norm, y_norm], dim=2)  # (B, K, 2)

    return keypoints, confidence


def soft_argmax(heatmaps: torch.Tensor, beta: float = 100.0) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    使用 Soft-Argmax 从热力图中提取关键点坐标。

    Soft-Argmax 是可微的关键点提取方法，比 argmax 更平滑。
    公式: x = sum(x * softmax(beta * H)) / sum(softmax(beta * H))

    Args:
        heatmaps: 热力图 (batch, num_keypoints, H, W)
        beta: 温度参数，越大越接近 argmax

    Returns:
        keypoints: 关键点坐标 (batch, num_keypoints, 2)，归一化坐标 [0, 1]
        confidence: 关键点置信度 (batch, num_keypoints)
    """
    batch_size, num_keypoints, h, w = heatmaps.shape
    device = heatmaps.device

    # 创建坐标网格
    y_coords = torch.arange(h, device=device, dtype=torch.float32)
    x_coords = torch.arange(w, device=device, dtype=torch.float32)
    y_grid, x_grid = torch.meshgrid(y_coords, x_coords, indexing="ij")
    # (H, W)

    # 应用 softmax
    heatmaps_flat = heatmaps.view(batch_size, num_keypoints, -1)  # (B, K, H*W)
    attention = F.softmax(beta * heatmaps_flat, dim=2)  # (B, K, H*W)

    # 计算期望坐标
    x_flat = x_grid.reshape(-1)  # (H*W,)
    y_flat = y_grid.reshape(-1)  # (H*W,)

    # x_coords = sum(x * attention)
    x_expect = (attention * x_flat[None, None, :]).sum(dim=2)  # (B, K)
    y_expect = (attention * y_flat[None, None, :]).sum(dim=2)  # (B, K)

    # 归一化到 [0, 1]
    x_norm = x_expect / (w - 1)
    y_norm = y_expect / (h - 1)

    keypoints = torch.stack([x_norm, y_norm], dim=2)  # (B, K, 2)

    # 置信度为热力图最大值
    confidence = heatmaps_flat.max(dim=2)[0]  # (B, K)

    return keypoints, confidence


def decode_heatmap_batch(
    heatmaps: torch.Tensor,
    method: str = "argmax",
    beta: float = 100.0,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    批量解码热力图为关键点坐标。

    Args:
        heatmaps: 热力图 (batch, num_keypoints, H, W)
        method: 解码方法，"argmax" 或 "soft_argmax"
        beta: soft_argmax 的温度参数

    Returns:
        keypoints: (batch, num_keypoints, 2) 归一化坐标
        confidence: (batch, num_keypoints) 置信度
    """
    if method == "argmax":
        return heatmaps_to_keypoints(heatmaps)
    elif method == "soft_argmax":
        return soft_argmax(heatmaps, beta)
    else:
        raise ValueError(f"Unknown method: {method}. Use 'argmax' or 'soft_argmax'.")


def resize_heatmaps(
    heatmaps: torch.Tensor,
    target_size: Tuple[int, int],
) -> torch.Tensor:
    """
    调整热力图尺寸。

    Args:
        heatmaps: 热力图 (batch, num_keypoints, H, W)
        target_size: 目标尺寸 (H', W')

    Returns:
        调整后的热力图 (batch, num_keypoints, H', W')
    """
    return F.interpolate(heatmaps, size=target_size, mode="bilinear", align_corners=False)
