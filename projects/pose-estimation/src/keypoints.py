"""
关键点检测与处理 (Keypoint Detection and Processing).

定义人体骨骼关键点和连接关系，实现关键点提取和解码。

COCO 17 关键点定义:
0: 鼻子 (nose)
1: 左眼 (left_eye)
2: 右眼 (right_eye)
3: 左耳 (left_ear)
4: 右耳 (right_ear)
5: 左肩 (left_shoulder)
6: 右肩 (right_shoulder)
7: 左肘 (left_elbow)
8: 右肘 (right_elbow)
9: 左腕 (left_wrist)
10: 右腕 (right_wrist)
11: 左髋 (left_hip)
12: 右髋 (right_hip)
13: 左膝 (left_knee)
14: 右膝 (right_knee)
15: 左踝 (left_ankle)
16: 右踝 (right_ankle)
"""

import torch
import numpy as np
from typing import Tuple, List, Optional


# COCO 17 关键点名称
KEYPOINT_NAMES = [
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
]

# 骨骼连接关系 (每对关键点索引)
SKELETON_CONNECTIONS = [
    # 头部
    (0, 1),   # 鼻子 - 左眼
    (0, 2),   # 鼻子 - 右眼
    (1, 3),   # 左眼 - 左耳
    (2, 4),   # 右眼 - 右耳
    # 躯干
    (5, 6),   # 左肩 - 右肩
    (5, 11),  # 左肩 - 左髋
    (6, 12),  # 右肩 - 右髋
    (11, 12), # 左髋 - 右髋
    # 左臂
    (5, 7),   # 左肩 - 左肘
    (7, 9),   # 左肘 - 左腕
    # 右臂
    (6, 8),   # 右肩 - 右肘
    (8, 10),  # 右肘 - 右腕
    # 左腿
    (11, 13), # 左髋 - 左膝
    (13, 15), # 左膝 - 左踝
    # 右腿
    (12, 14), # 右髋 - 右膝
    (14, 16), # 右膝 - 右踝
]

# 各肢体的颜色 (用于可视化)
LIMB_COLORS = [
    (255, 0, 0),     # 头部 - 红色
    (255, 0, 0),
    (255, 0, 0),
    (255, 0, 0),
    (0, 255, 0),     # 躯干 - 绿色
    (0, 255, 0),
    (0, 255, 0),
    (0, 255, 0),
    (0, 0, 255),     # 左臂 - 蓝色
    (0, 0, 255),
    (255, 255, 0),   # 右臂 - 黄色
    (255, 255, 0),
    (128, 0, 255),   # 左腿 - 紫色
    (128, 0, 255),
    (255, 128, 0),   # 右腿 - 橙色
    (255, 128, 0),
]


def extract_keypoints(
    heatmaps: torch.Tensor,
    threshold: float = 0.1,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    从热力图中提取关键点坐标。

    使用 argmax 找到热力图峰值，然后转换为归一化坐标。

    Args:
        heatmaps: 热力图 (batch, num_keypoints, H, W)
        threshold: 置信度阈值，低于此值的关键点被标记为不可见

    Returns:
        keypoints: (batch, num_keypoints, 2) 归一化坐标 (x, y) in [0, 1]
        confidence: (batch, num_keypoints) 置信度分数
    """
    batch_size, num_keypoints, h, w = heatmaps.shape

    # 展平空间维度
    heatmaps_flat = heatmaps.view(batch_size, num_keypoints, -1)  # (B, K, H*W)

    # 找到最大值和位置
    confidence, max_idx = torch.max(heatmaps_flat, dim=2)  # (B, K)

    # 转换为 2D 坐标 (在热力图空间中，使用整数除法)
    y_coords = (max_idx // w).float()  # 行索引
    x_coords = (max_idx % w).float()   # 列索引

    # 归一化到 [0, 1]
    x_norm = x_coords / (w - 1)
    y_norm = y_coords / (h - 1)

    # 裁剪到 [0, 1] 范围
    x_norm = x_norm.clamp(0.0, 1.0)
    y_norm = y_norm.clamp(0.0, 1.0)

    keypoints = torch.stack([x_norm, y_norm], dim=2)  # (B, K, 2)

    # 应用阈值: 低置信度的关键点坐标设为 0
    mask = confidence < threshold
    keypoints[mask] = 0.0

    return keypoints, confidence


def extract_keypoints_with_subpixel(
    heatmaps: torch.Tensor,
    threshold: float = 0.1,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    从热力图中提取关键点坐标，使用亚像素精度。

    在 argmax 的 3x3 邻域内进行二次插值，提高精度。

    Args:
        heatmaps: 热力图 (batch, num_keypoints, H, W)
        threshold: 置信度阈值

    Returns:
        keypoints: (batch, num_keypoints, 2) 归一化坐标
        confidence: (batch, num_keypoints) 置信度
    """
    batch_size, num_keypoints, h, w = heatmaps.shape
    device = heatmaps.device

    # 找到 argmax 位置
    heatmaps_flat = heatmaps.view(batch_size, num_keypoints, -1)
    confidence, max_idx = torch.max(heatmaps_flat, dim=2)  # (B, K)

    # 转换为 2D 坐标
    y_int = max_idx // w  # 行索引
    x_int = max_idx % w   # 列索引

    # 亚像素偏移 (使用中心差分)
    x_offset = torch.zeros_like(x_int, dtype=torch.float32)
    y_offset = torch.zeros_like(y_int, dtype=torch.float32)

    for b in range(batch_size):
        for k in range(num_keypoints):
            xi, yi = x_int[b, k].item(), y_int[b, k].item()

            # 处理边界
            if 0 < xi < w - 1:
                left = heatmaps[b, k, yi, xi - 1].item()
                right = heatmaps[b, k, yi, xi + 1].item()
                center = heatmaps[b, k, yi, xi].item()
                if left + right - 2 * center != 0:
                    x_offset[b, k] = 0.5 * (left - right) / (left + right - 2 * center)

            if 0 < yi < h - 1:
                up = heatmaps[b, k, yi - 1, xi].item()
                down = heatmaps[b, k, yi + 1, xi].item()
                center = heatmaps[b, k, yi, xi].item()
                if up + down - 2 * center != 0:
                    y_offset[b, k] = 0.5 * (up - down) / (up + down - 2 * center)

    # 计算亚像素坐标
    x_sub = (x_int.float() + x_offset).clamp(0, w - 1)
    y_sub = (y_int.float() + y_offset).clamp(0, h - 1)

    # 归一化到 [0, 1]
    x_norm = (x_sub / (w - 1)).clamp(0.0, 1.0)
    y_norm = (y_sub / (h - 1)).clamp(0.0, 1.0)

    keypoints = torch.stack([x_norm, y_norm], dim=2)

    # 应用阈值
    mask = confidence < threshold
    keypoints[mask] = 0.0

    return keypoints, confidence


def decode_predictions(
    heatmaps: torch.Tensor,
    image_size: Tuple[int, int],
    threshold: float = 0.1,
    method: str = "argmax",
) -> dict:
    """
    解码模型预测为关键点结果。

    Args:
        heatmaps: 模型输出的热力图 (batch, K, H, W)
        image_size: 原始图像尺寸 (H, W)
        threshold: 置信度阈值
        method: 解码方法 "argmax" 或 "subpixel"

    Returns:
        包含关键点坐标和置信度的字典
    """
    if method == "argmax":
        keypoints_norm, confidence = extract_keypoints(heatmaps, threshold)
    elif method == "subpixel":
        keypoints_norm, confidence = extract_keypoints_with_subpixel(heatmaps, threshold)
    else:
        raise ValueError(f"Unknown method: {method}")

    # 转换为图像坐标
    img_h, img_w = image_size
    keypoints_img = keypoints_norm.clone()
    keypoints_img[:, :, 0] *= img_w
    keypoints_img[:, :, 1] *= img_h

    return {
        "keypoints_norm": keypoints_norm,     # 归一化坐标 (B, K, 2)
        "keypoints_img": keypoints_img,        # 图像坐标 (B, K, 2)
        "confidence": confidence,              # 置信度 (B, K)
        "num_keypoints": heatmaps.shape[1],
    }


def compute_pck(
    pred_keypoints: torch.Tensor,
    target_keypoints: torch.Tensor,
    threshold: float = 0.2,
    reference_length: Optional[torch.Tensor] = None,
) -> float:
    """
    计算 PCK (Percentage of Correct Keypoints)。

    PCK 是姿态估计的标准评估指标：
    - 预测关键点与 GT 的距离 < 阈值 * 参考长度 → 正确

    Args:
        pred_keypoints: 预测关键点 (batch, K, 2)，归一化坐标
        target_keypoints: GT 关键点 (batch, K, 2)，归一化坐标
        threshold: 阈值比例
        reference_length: 参考长度 (batch,)，如躯干长度。默认使用图像对角线

    Returns:
        PCK 分数 (0-1)
    """
    # 计算欧氏距离
    dist = torch.norm(pred_keypoints - target_keypoints, dim=2)  # (B, K)

    # 确定参考长度
    if reference_length is None:
        # 使用图像对角线 = sqrt(2) ≈ 1.414 (归一化坐标下)
        ref_len = np.sqrt(2)
    else:
        ref_len = reference_length[:, None]  # (B, 1)

    # 计算正确率
    correct = (dist < threshold * ref_len).float()

    return correct.mean().item()


def compute_pck_per_keypoint(
    pred_keypoints: torch.Tensor,
    target_keypoints: torch.Tensor,
    threshold: float = 0.2,
) -> List[float]:
    """
    计算每个关键点的 PCK。

    Args:
        pred_keypoints: (B, K, 2)
        target_keypoints: (B, K, 2)
        threshold: 阈值

    Returns:
        每个关键点的 PCK 分数列表
    """
    dist = torch.norm(pred_keypoints - target_keypoints, dim=2)  # (B, K)
    ref_len = np.sqrt(2)
    correct = (dist < threshold * ref_len).float()

    pck_per_kp = correct.mean(dim=0).tolist()  # (K,)
    return pck_per_kp
