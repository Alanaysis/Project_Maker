"""
深度估计工具函数

包含:
- 深度图归一化
- 深度图可视化 (颜色映射)
- 深度估计评估指标
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Optional, Dict


def normalize_depth(
    depth: torch.Tensor,
    min_depth: Optional[float] = None,
    max_depth: Optional[float] = None,
) -> torch.Tensor:
    """
    归一化深度图到 [0, 1]

    Args:
        depth: 深度图 (B, 1, H, W) 或 (1, H, W) 或 (H, W)
        min_depth: 最小深度值，如果为 None 则使用数据最小值
        max_depth: 最大深度值，如果为 None 则使用数据最大值

    Returns:
        归一化后的深度图
    """
    if min_depth is None:
        min_depth = depth.min()
    if max_depth is None:
        max_depth = depth.max()

    depth_norm = (depth - min_depth) / (max_depth - min_depth + 1e-8)
    return torch.clamp(depth_norm, 0, 1)


def colorize_depth(
    depth: torch.Tensor,
    colormap: str = "jet",
    min_depth: Optional[float] = None,
    max_depth: Optional[float] = None,
) -> torch.Tensor:
    """
    将深度图转换为彩色可视化

    使用颜色映射将单通道深度图转换为三通道彩色图像。

    Args:
        depth: 深度图 (H, W) 或 (1, H, W)
        colormap: 颜色映射 ('jet', 'viridis', 'plasma', 'magma', 'inferno')
        min_depth: 最小深度值
        max_depth: 最大深度值

    Returns:
        彩色深度图 (3, H, W)
    """
    if depth.dim() == 3:
        depth = depth.squeeze(0)

    # 归一化
    depth_np = normalize_depth(depth, min_depth, max_depth).cpu().numpy()

    # 颜色映射表
    colormaps = {
        "jet": _jet_colormap,
        "viridis": _viridis_colormap,
        "plasma": _plasma_colormap,
    }

    if colormap in colormaps:
        color_func = colormaps[colormap]
    else:
        color_func = _jet_colormap

    # 应用颜色映射
    colored = color_func(depth_np)

    return torch.from_numpy(colored).float()


def _jet_colormap(depth: np.ndarray) -> np.ndarray:
    """Jet 颜色映射"""
    h, w = depth.shape
    colored = np.zeros((3, h, w), dtype=np.float32)

    # Jet colormap approximation
    for i in range(h):
        for j in range(w):
            val = depth[i, j]
            if val < 0.125:
                r, g, b = 0, 0, 0.5 + 4 * val
            elif val < 0.375:
                r, g, b = 0, 4 * (val - 0.125), 1
            elif val < 0.625:
                r, g, b = 4 * (val - 0.375), 1, 1 - 4 * (val - 0.375)
            elif val < 0.875:
                r, g, b = 1, 1 - 4 * (val - 0.625), 0
            else:
                r, g, b = 1 - 4 * (val - 0.875), 0, 0
            colored[0, i, j] = r
            colored[1, i, j] = g
            colored[2, i, j] = b

    return colored


def _viridis_colormap(depth: np.ndarray) -> np.ndarray:
    """Viridis 颜色映射 (近似)"""
    h, w = depth.shape
    colored = np.zeros((3, h, w), dtype=np.float32)

    for i in range(h):
        for j in range(w):
            val = depth[i, j]
            r = 0.267004 + val * (0.003991 + val * (0.211278 - 0.267004))
            g = 0.004874 + val * (0.475634 + val * (0.473718 - 0.475634))
            b = 0.329415 + val * (0.453231 + val * (0.185360 - 0.453231))
            colored[0, i, j] = np.clip(r, 0, 1)
            colored[1, i, j] = np.clip(g, 0, 1)
            colored[2, i, j] = np.clip(b, 0, 1)

    return colored


def _plasma_colormap(depth: np.ndarray) -> np.ndarray:
    """Plasma 颜色映射 (近似)"""
    h, w = depth.shape
    colored = np.zeros((3, h, w), dtype=np.float32)

    for i in range(h):
        for j in range(w):
            val = depth[i, j]
            r = 0.050383 + val * (0.683226 + val * (0.230344 - 0.683226))
            g = 0.029803 + val * (0.076128 + val * (0.752371 - 0.076128))
            b = 0.527975 + val * (-0.517406 + val * (0.182409 + 0.517406))
            colored[0, i, j] = np.clip(r, 0, 1)
            colored[1, i, j] = np.clip(g, 0, 1)
            colored[2, i, j] = np.clip(b, 0, 1)

    return colored


def visualize_depth(
    image: torch.Tensor,
    pred_depth: torch.Tensor,
    target_depth: Optional[torch.Tensor] = None,
    colormap: str = "jet",
) -> torch.Tensor:
    """
    可视化深度估计结果

    将输入图像、预测深度图和目标深度图组合显示。

    Args:
        image: 输入图像 (3, H, W)
        pred_depth: 预测深度图 (1, H, W)
        target_depth: 目标深度图 (1, H, W)，可选
        colormap: 颜色映射

    Returns:
        可视化结果 (3, H, W*n)，其中 n 是子图数量
    """
    # 预测深度彩色化
    pred_colored = colorize_depth(pred_depth, colormap)

    if target_depth is not None:
        # 目标深度彩色化
        target_colored = colorize_depth(target_depth, colormap)
        # 拼接: 图像 | 预测深度 | 目标深度
        result = torch.cat([image, pred_colored, target_colored], dim=2)
    else:
        # 拼接: 图像 | 预测深度
        result = torch.cat([image, pred_colored], dim=2)

    return result


def compute_depth_metrics(
    pred: torch.Tensor,
    target: torch.Tensor,
    valid_mask: Optional[torch.Tensor] = None,
    min_depth: float = 1e-3,
    max_depth: float = 80.0,
) -> Dict[str, float]:
    """
    计算深度估计评估指标

    包含常用指标:
    - Abs Rel: 绝对相对误差
    - Sq Rel: 平方相对误差
    - RMSE: 均方根误差
    - RMSE Log: 对数均方根误差
    - delta < 1.25: 阈值精度
    - delta < 1.25^2: 阈值精度
    - delta < 1.25^3: 阈值精度

    Args:
        pred: 预测深度图 (B, 1, H, W)
        target: 目标深度图 (B, 1, H, W)
        valid_mask: 有效像素掩码 (B, 1, H, W)
        min_depth: 最小深度值
        max_depth: 最大深度值

    Returns:
        指标字典

    Reference:
        Eigen, D., Puhrsch, C., & Fergus, R. (2014).
        Depth Map Prediction from a Single Image using a Multi-Scale Deep Network.
    """
    # 裁剪深度值
    pred = torch.clamp(pred, min=min_depth, max=max_depth)
    target = torch.clamp(target, min=min_depth, max=max_depth)

    if valid_mask is not None:
        pred = pred[valid_mask > 0]
        target = target[valid_mask > 0]
    else:
        pred = pred.reshape(-1)
        target = target.reshape(-1)

    # 计算各项指标
    thresh = torch.max(pred / target, target / pred)

    # delta < 1.25
    delta1 = (thresh < 1.25).float().mean().item()
    # delta < 1.25^2
    delta2 = (thresh < 1.25 ** 2).float().mean().item()
    # delta < 1.25^3
    delta3 = (thresh < 1.25 ** 3).float().mean().item()

    # 绝对相对误差
    abs_rel = (torch.abs(pred - target) / target).mean().item()

    # 平方相对误差
    sq_rel = (((pred - target) ** 2) / target).mean().item()

    # RMSE
    rmse = torch.sqrt(((pred - target) ** 2).mean()).item()

    # RMSE Log
    rmse_log = torch.sqrt(
        ((torch.log(pred) - torch.log(target)) ** 2).mean()
    ).item()

    # SILog
    log_diff = torch.log(pred) - torch.log(target)
    silog = torch.sqrt(
        (log_diff ** 2).mean() - 0.5 * (log_diff.mean() ** 2)
    ).item()

    # L1 Error
    l1_error = torch.abs(pred - target).mean().item()

    return {
        "abs_rel": abs_rel,
        "sq_rel": sq_rel,
        "rmse": rmse,
        "rmse_log": rmse_log,
        "silog": silog,
        "l1_error": l1_error,
        "delta1": delta1,
        "delta2": delta2,
        "delta3": delta3,
    }


def print_metrics(metrics: Dict[str, float]) -> None:
    """
    打印评估指标

    Args:
        metrics: 指标字典
    """
    print("=" * 50)
    print("深度估计评估指标")
    print("=" * 50)
    print(f"  Abs Rel:    {metrics['abs_rel']:.4f}")
    print(f"  Sq Rel:     {metrics['sq_rel']:.4f}")
    print(f"  RMSE:       {metrics['rmse']:.4f}")
    print(f"  RMSE Log:   {metrics['rmse_log']:.4f}")
    print(f"  SIlog:      {metrics['silog']:.4f}")
    print(f"  L1 Error:   {metrics['l1_error']:.4f}")
    print(f"  delta < 1.25:     {metrics['delta1']:.4f}")
    print(f"  delta < 1.25^2:   {metrics['delta2']:.4f}")
    print(f"  delta < 1.25^3:   {metrics['delta3']:.4f}")
    print("=" * 50)


def depth_to_disparity(depth: torch.Tensor, baseline: float = 0.1, focal: float = 500.0) -> torch.Tensor:
    """
    深度图转视差图

    视差 = baseline * focal / depth

    Args:
        depth: 深度图
        baseline: 基线距离 (米)
        focal: 焦距 (像素)

    Returns:
        视差图
    """
    disparity = baseline * focal / (depth + 1e-8)
    return disparity


def disparity_to_depth(disparity: torch.Tensor, baseline: float = 0.1, focal: float = 500.0) -> torch.Tensor:
    """
    视差图转深度图

    深度 = baseline * focal / disparity

    Args:
        disparity: 视差图
        baseline: 基线距离 (米)
        focal: 焦距 (像素)

    Returns:
        深度图
    """
    depth = baseline * focal / (disparity + 1e-8)
    return depth


def compute_depth_error_histogram(
    pred: torch.Tensor,
    target: torch.Tensor,
    num_bins: int = 20,
    max_error: float = 5.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    计算深度误差直方图

    Args:
        pred: 预测深度图
        target: 目标深度图
        num_bins: 直方图 bin 数量
        max_error: 最大误差值

    Returns:
        (counts, bin_edges) 元组
    """
    errors = torch.abs(pred - target).cpu().numpy().flatten()
    counts, bin_edges = np.histogram(errors, bins=num_bins, range=(0, max_error))
    return counts, bin_edges


def depth_stats(depth: torch.Tensor) -> Dict[str, float]:
    """
    计算深度图统计信息

    Args:
        depth: 深度图

    Returns:
        统计信息字典
    """
    return {
        "min": depth.min().item(),
        "max": depth.max().item(),
        "mean": depth.mean().item(),
        "std": depth.std().item(),
        "median": depth.median().item(),
    }
