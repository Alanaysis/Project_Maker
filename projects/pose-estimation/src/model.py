"""
姿态估计网络架构 (Pose Estimation Network Architecture).

实现基于热力图回归的人体姿态估计模型。

Architecture Overview:
- 输入: RGB 图像 (batch, 3, H, W)
- 骨干网络: 轻量级 CNN 提取特征
- 预测头: 反卷积 + 卷积生成热力图
- 输出: K 个热力图 (batch, K, H', W')

每个热力图对应一个关键点，热力图峰值位置即为关键点坐标。

支持的关键点格式:
- COCO 17 关键点: 鼻子、眼睛、耳朵、肩膀、肘部、手腕、髋部、膝盖、脚踝
"""

import torch
import torch.nn as nn
from typing import Tuple, Optional


class ConvBlock(nn.Module):
    """卷积 + 批归一化 + ReLU 模块."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        stride: int = 1,
        padding: int = 1,
    ):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.relu(self.bn(self.conv(x)))


class ResidualBlock(nn.Module):
    """残差块 (Residual Block)."""

    def __init__(self, channels: int):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(channels, channels, 3, 1, 1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels, channels, 3, 1, 1, bias=False),
            nn.BatchNorm2d(channels),
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.relu(x + self.block(x))


class LightweightBackbone(nn.Module):
    """
    轻量级骨干网络，用于特征提取。

    类似于简化版 ResNet，包含多层卷积和残差块。
    输出特征图尺寸为输入的 1/4。

    Args:
        in_channels: 输入通道数 (默认 3，RGB 图像)
    """

    def __init__(self, in_channels: int = 3):
        super().__init__()

        # 初始卷积层: 3 -> 64
        self.stem = nn.Sequential(
            ConvBlock(in_channels, 64, kernel_size=7, stride=2, padding=3),
            nn.MaxPool2d(2, stride=2),  # 1/4 下采样
        )

        # 特征提取层
        self.layer1 = nn.Sequential(
            ConvBlock(64, 128),
            ResidualBlock(128),
        )
        self.layer2 = nn.Sequential(
            ConvBlock(128, 256),
            ResidualBlock(256),
        )
        self.layer3 = nn.Sequential(
            ConvBlock(256, 256),
            ResidualBlock(256),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播。

        Args:
            x: 输入张量 (batch, in_channels, H, W)

        Returns:
            特征张量 (batch, 256, H/4, W/4)
        """
        x = self.stem(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        return x


class HeatmapHead(nn.Module):
    """
    热力图预测头。

    使用反卷积上采样 + 卷积生成关键点热力图。

    Args:
        in_channels: 输入通道数 (骨干网络输出通道)
        num_keypoints: 关键点数量
        deconv_channels: 反卷积通道数列表
    """

    def __init__(
        self,
        in_channels: int = 256,
        num_keypoints: int = 17,
        deconv_channels: list = None,
    ):
        super().__init__()

        if deconv_channels is None:
            deconv_channels = [256, 256, 256]

        layers = []
        ch = in_channels
        for out_ch in deconv_channels:
            layers.extend([
                nn.ConvTranspose2d(ch, out_ch, kernel_size=4, stride=2, padding=1, bias=False),
                nn.BatchNorm2d(out_ch),
                nn.ReLU(inplace=True),
            ])
            ch = out_ch

        self.deconv = nn.Sequential(*layers)

        # 最终卷积层，输出 K 个热力图
        self.final = nn.Conv2d(ch, num_keypoints, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播。

        Args:
            x: 特征张量 (batch, in_channels, H', W')

        Returns:
            热力图张量 (batch, num_keypoints, H, W)
        """
        x = self.deconv(x)
        x = self.final(x)
        return x


class PoseEstimationNet(nn.Module):
    """
    人体姿态估计网络。

    组合骨干网络和热力图预测头，实现端到端的姿态估计。

    Architecture:
        Input (B, 3, 256, 256)
            → LightweightBackbone → (B, 256, 64, 64)
            → HeatmapHead → (B, K, 256, 256)

    Args:
        num_keypoints: 关键点数量 (默认 17，COCO 格式)
        in_channels: 输入通道数 (默认 3)
        input_size: 输入图像尺寸 (默认 256)
        heatmap_size: 热力图尺寸 (默认 64)
    """

    def __init__(
        self,
        num_keypoints: int = 17,
        in_channels: int = 3,
        input_size: int = 256,
        heatmap_size: int = 64,
    ):
        super().__init__()
        self.num_keypoints = num_keypoints
        self.input_size = input_size
        self.heatmap_size = heatmap_size

        self.backbone = LightweightBackbone(in_channels)

        # 骨干网络输出 1/4，热力图需要从 1/4 上采样到 heatmap_size
        # 如果 heatmap_size = input_size / 4，不需要额外上采样
        # 如果 heatmap_size = input_size，需要 4x 上采样
        scale_factor = input_size // (input_size // 4)  # 骨干网络输出相对于输入的缩放
        deconv_layers = []
        ch = 256
        current_size = input_size // 4

        # 计算需要多少次 2x 上采样才能达到 heatmap_size
        while current_size < heatmap_size:
            out_ch = max(ch // 2, 64)
            deconv_layers.append(out_ch)
            current_size *= 2
            ch = out_ch

        if not deconv_layers:
            # heatmap_size <= input_size/4，直接用卷积
            self.head = nn.Sequential(
                nn.Conv2d(256, 256, 3, 1, 1, bias=False),
                nn.BatchNorm2d(256),
                nn.ReLU(inplace=True),
                nn.Conv2d(256, num_keypoints, 1),
            )
        else:
            self.head = HeatmapHead(256, num_keypoints, deconv_layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播。

        Args:
            x: 输入图像张量 (batch, 3, H, W)

        Returns:
            热力图张量 (batch, num_keypoints, heatmap_H, heatmap_W)
        """
        features = self.backbone(x)
        heatmaps = self.head(features)
        return heatmaps

    def predict_keypoints(
        self, x: torch.Tensor, threshold: float = 0.1
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        预测关键点坐标。

        Args:
            x: 输入图像张量 (batch, 3, H, W)
            threshold: 置信度阈值

        Returns:
            keypoints: (batch, num_keypoints, 2) 关键点坐标 (x, y)
            confidence: (batch, num_keypoints) 置信度
        """
        from .keypoints import extract_keypoints

        heatmaps = self.forward(x)
        keypoints, confidence = extract_keypoints(heatmaps, threshold)
        return keypoints, confidence


class SimplePoseNet(nn.Module):
    """
    简化版姿态估计网络，用于测试和快速原型。

    使用更少的层和更小的参数量。

    Args:
        num_keypoints: 关键点数量
        input_size: 输入图像尺寸
    """

    def __init__(self, num_keypoints: int = 17, input_size: int = 128):
        super().__init__()
        self.num_keypoints = num_keypoints
        self.input_size = input_size

        self.features = nn.Sequential(
            ConvBlock(3, 32, stride=2),   # 1/2
            ConvBlock(32, 64, stride=2),  # 1/4
            ConvBlock(64, 128, stride=2), # 1/8
            ResidualBlock(128),
            ConvBlock(128, 128),
            ResidualBlock(128),
        )

        # 直接上采样到目标尺寸
        self.head = nn.Sequential(
            nn.ConvTranspose2d(128, 64, 4, 2, 1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(64, 32, 4, 2, 1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, num_keypoints, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.features(x)
        heatmaps = self.head(features)
        return heatmaps
