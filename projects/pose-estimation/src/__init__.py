# Human Pose Estimation
"""
人体姿态估计 (Human Pose Estimation)
====================================

实现人体姿态估计，检测骨骼关键点。

核心流程:
图像输入 → 骨干网络 → 特征提取 → 热力图回归 → 关键点坐标

Modules:
- model: 姿态估计网络架构 (骨干网络 + 热力图预测头)
- heatmap: 热力图生成与处理
- loss: 热力图回归损失函数
- keypoints: 关键点检测与提取
- dataset: 数据集处理
- utils: 可视化与工具函数
- train: 训练脚本
"""

from .model import PoseEstimationNet, LightweightBackbone
from .heatmap import generate_heatmaps, heatmaps_to_keypoints, soft_argmax
from .loss import KeypointMSELoss, KeypointOHKMLoss
from .keypoints import (
    KEYPOINT_NAMES,
    SKELETON_CONNECTIONS,
    extract_keypoints,
    decode_predictions,
)
from .utils import draw_skeleton, visualize_pose

__version__ = "0.1.0"
__all__ = [
    "PoseEstimationNet",
    "LightweightBackbone",
    "generate_heatmaps",
    "heatmaps_to_keypoints",
    "soft_argmax",
    "KeypointMSELoss",
    "KeypointOHKMLoss",
    "KEYPOINT_NAMES",
    "SKELETON_CONNECTIONS",
    "extract_keypoints",
    "decode_predictions",
    "draw_skeleton",
    "visualize_pose",
]
