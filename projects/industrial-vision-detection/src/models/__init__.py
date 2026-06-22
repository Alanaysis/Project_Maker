"""
模型模块 - 定义神经网络模型

包含:
- backbone: 骨干网络 (CSPDarknet)
- neck: 特征融合网络 (PANet)
- head: 检测头 (Decoupled Head)
- yolo: 完整 YOLO 模型
- losses: 损失函数
"""

from .backbone import CSPDarknet, ConvBlock, CSPBlock, SPPF
from .neck import PANet, C2f
from .head import DetectHead
from .yolo import YOLOModel, YOLOv8Tiny
from .losses import BCELoss, FocalLoss, CIoULoss, YOLOLoss

__all__ = [
    # Backbone
    'CSPDarknet',
    'ConvBlock',
    'CSPBlock',
    'SPPF',

    # Neck
    'PANet',
    'C2f',

    # Head
    'DetectHead',

    # YOLO
    'YOLOModel',
    'YOLOv8Tiny',

    # Losses
    'BCELoss',
    'FocalLoss',
    'CIoULoss',
    'YOLOLoss',
]
