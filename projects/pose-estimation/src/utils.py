"""
可视化与工具函数 (Visualization and Utility Functions).

提供姿态估计结果的可视化和常用工具。
"""

import torch
import numpy as np
from typing import Tuple, List, Optional, Union

from .keypoints import KEYPOINT_NAMES, SKELETON_CONNECTIONS, LIMB_COLORS


def draw_skeleton(
    image: np.ndarray,
    keypoints: np.ndarray,
    confidence: Optional[np.ndarray] = None,
    connections: Optional[List[Tuple[int, int]]] = None,
    keypoint_color: Tuple[int, int, int] = (0, 255, 0),
    line_color: Tuple[int, int, int] = (255, 200, 0),
    radius: int = 3,
    thickness: int = 2,
    confidence_threshold: float = 0.1,
) -> np.ndarray:
    """
    在图像上绘制骨骼。

    Args:
        image: 输入图像 (H, W, 3) uint8, BGR 格式
        keypoints: 关键点坐标 (K, 2)，像素坐标 (x, y)
        confidence: 关键点置信度 (K,)
        connections: 骨骼连接关系列表，默认使用 COCO 连接
        keypoint_color: 关键点颜色 (B, G, R)
        line_color: 连线颜色 (B, G, R)
        radius: 关键点半径
        thickness: 连线粗细
        confidence_threshold: 置信度阈值

    Returns:
        绘制了骨骼的图像 (H, W, 3)
    """
    if connections is None:
        connections = SKELETON_CONNECTIONS

    img = image.copy()
    h, w = img.shape[:2]
    num_kp = keypoints.shape[0]

    # 绘制连线
    for idx, (i, j) in enumerate(connections):
        if i >= num_kp or j >= num_kp:
            continue

        # 检查置信度
        if confidence is not None:
            if confidence[i] < confidence_threshold or confidence[j] < confidence_threshold:
                continue

        x1, y1 = int(keypoints[i, 0]), int(keypoints[i, 1])
        x2, y2 = int(keypoints[j, 0]), int(keypoints[j, 1])

        # 使用肢体颜色
        color = LIMB_COLORS[idx % len(LIMB_COLORS)] if idx < len(LIMB_COLORS) else line_color

        try:
            import cv2
            cv2.line(img, (x1, y1), (x2, y2), color, thickness)
        except ImportError:
            _draw_line_numpy(img, x1, y1, x2, y2, color)

    # 绘制关键点
    for k in range(num_kp):
        if confidence is not None and confidence[k] < confidence_threshold:
            continue

        x, y = int(keypoints[k, 0]), int(keypoints[k, 1])
        if 0 <= x < w and 0 <= y < h:
            try:
                import cv2
                cv2.circle(img, (x, y), radius, keypoint_color, -1)
            except ImportError:
                _draw_circle_numpy(img, x, y, radius, keypoint_color)

    return img


def _draw_line_numpy(
    img: np.ndarray, x1: int, y1: int, x2: int, y2: int, color: tuple
):
    """纯 numpy 画线。"""
    h, w = img.shape[:2]
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    steps = max(dx, dy)
    if steps == 0:
        return
    for t in range(steps + 1):
        x = int(x1 + (x2 - x1) * t / steps)
        y = int(y1 + (y2 - y1) * t / steps)
        if 0 <= x < w and 0 <= y < h:
            img[y, x] = color


def _draw_circle_numpy(img: np.ndarray, cx: int, cy: int, radius: int, color: tuple):
    """纯 numpy 画圆。"""
    h, w = img.shape[:2]
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < h and 0 <= nx < w:
                    img[ny, nx] = color


def visualize_pose(
    image: Union[np.ndarray, torch.Tensor],
    keypoints: Union[np.ndarray, torch.Tensor],
    confidence: Optional[Union[np.ndarray, torch.Tensor]] = None,
    image_size: Optional[Tuple[int, int]] = None,
) -> np.ndarray:
    """
    可视化姿态估计结果。

    自动处理张量到 numpy 的转换和坐标归一化。

    Args:
        image: 输入图像，可以是 numpy 数组或 PyTorch 张量
        keypoints: 关键点坐标，可以是归一化坐标或像素坐标
        confidence: 关置信度
        image_size: 图像尺寸 (H, W)，如果 keypoint 是归一化坐标则需要

    Returns:
        带有骨骼标注的图像
    """
    # 转换图像
    if isinstance(image, torch.Tensor):
        img = image.detach().cpu().numpy()
        if img.ndim == 3 and img.shape[0] in [1, 3]:
            img = img.transpose(1, 2, 0)  # CHW -> HWC
        if img.max() <= 1.0:
            img = (img * 255).astype(np.uint8)
        else:
            img = img.astype(np.uint8)
    else:
        img = image.copy()

    # 转换关键点
    if isinstance(keypoints, torch.Tensor):
        kp = keypoints.detach().cpu().numpy()
    else:
        kp = keypoints.copy()

    # 如果是归一化坐标，转换为像素坐标
    if kp.max() <= 1.0 and image_size is not None:
        h, w = image_size
        kp[:, 0] *= w
        kp[:, 1] *= h

    # 转换置信度
    conf = None
    if confidence is not None:
        if isinstance(confidence, torch.Tensor):
            conf = confidence.detach().cpu().numpy()
        else:
            conf = confidence

    return draw_skeleton(img, kp, conf)


def normalize_keypoints(
    keypoints: torch.Tensor,
    image_size: Tuple[int, int],
) -> torch.Tensor:
    """
    将像素坐标归一化到 [0, 1]。

    Args:
        keypoints: (K, 2) 像素坐标
        image_size: (H, W)

    Returns:
        归一化后的关键点
    """
    h, w = image_size
    kp = keypoints.clone()
    kp[..., 0] /= w
    kp[..., 1] /= h
    return kp


def denormalize_keypoints(
    keypoints: torch.Tensor,
    image_size: Tuple[int, int],
) -> torch.Tensor:
    """
    将归一化坐标转换为像素坐标。

    Args:
        keypoints: (K, 2) 归一化坐标 [0, 1]
        image_size: (H, W)

    Returns:
        像素坐标
    """
    h, w = image_size
    kp = keypoints.clone()
    kp[..., 0] *= w
    kp[..., 1] *= h
    return kp


def compute_oks(
    pred_keypoints: torch.Tensor,
    gt_keypoints: torch.Tensor,
    gt_areas: torch.Tensor,
    gt_visibility: torch.Tensor,
    sigmas: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    """
    计算 OKS (Object Keypoint Similarity)。

    OKS 是 COCO 数据集使用的姿态估计评估指标。
    OKS = sum(exp(-d^2 / (2 * s^2 * kappa^2)) * v) / sum(v)

    Args:
        pred_keypoints: 预测关键点 (B, K, 2)
        gt_keypoints: GT 关键点 (B, K, 2)
        gt_areas: GT 目标面积 (B,)
        gt_visibility: GT 可见性 (B, K)
        sigmas: 每个关键点的标准差 (K,)，默认使用 COCO 标准值

    Returns:
        OKS 分数 (B,)
    """
    if sigmas is None:
        # COCO 默认 sigmas
        sigmas = torch.tensor([
            0.026, 0.025, 0.025, 0.035, 0.035,  # 头部
            0.079, 0.079, 0.072, 0.072,          # 肩膀-肘部
            0.062, 0.062,                         # 手腕
            0.107, 0.107,                         # 髋部
            0.087, 0.087,                         # 膝盖
            0.089, 0.089,                         # 脚踝
        ], device=pred_keypoints.device)

    # 计算距离
    dx = pred_keypoints[:, :, 0] - gt_keypoints[:, :, 0]
    dy = pred_keypoints[:, :, 1] - gt_keypoints[:, :, 1]
    dist_sq = dx ** 2 + dy ** 2  # (B, K)

    # 计算面积的平方根
    s_sq = gt_areas  # (B,)

    # kappa^2 * s^2
    kappa_sq = (2 * sigmas) ** 2  # (K,)
    denom = 2 * kappa_sq[None, :] * s_sq[:, None]  # (B, K)

    # OKS per keypoint
    oks_per_kp = torch.exp(-dist_sq / denom)  # (B, K)

    # 应用可见性
    oks_per_kp = oks_per_kp * gt_visibility  # (B, K)

    # 平均
    oks = oks_per_kp.sum(dim=1) / gt_visibility.sum(dim=1).clamp(min=1.0)  # (B,)

    return oks


def get_keypoint_names() -> List[str]:
    """获取关键点名称列表。"""
    return KEYPOINT_NAMES.copy()


def get_skeleton_connections() -> List[Tuple[int, int]]:
    """获取骨骼连接关系列表。"""
    return SKELETON_CONNECTIONS.copy()
