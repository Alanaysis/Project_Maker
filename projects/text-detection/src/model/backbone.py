"""
Backbone Network for Text Detection

Implements VGG-like feature extractor for EAST text detection.
Uses progressive downsampling with 1/32 output stride.
"""

import torch
import torch.nn as nn


class ConvBNReLU(nn.Module):
    """Conv2d + BatchNorm + ReLU block."""

    def __init__(self, in_channels: int, out_channels: int,
                 kernel_size: int = 3, stride: int = 1, padding: int = 1):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.relu(self.bn(self.conv(x)))


class VGGBackbone(nn.Module):
    """
    VGG-like backbone for feature extraction.

    Produces multi-scale feature maps at different stages:
    - Stage 1 (1/2):  64 channels
    - Stage 2 (1/4):  128 channels
    - Stage 3 (1/8):  256 channels
    - Stage 4 (1/16): 512 channels
    - Stage 5 (1/32): 512 channels

    Args:
        in_channels: Number of input channels (3 for RGB)
    """

    def __init__(self, in_channels: int = 3):
        super().__init__()

        # Stage 1: /2
        self.stage1 = nn.Sequential(
            ConvBNReLU(in_channels, 64),
            ConvBNReLU(64, 64),
            nn.MaxPool2d(2, 2),
        )

        # Stage 2: /4
        self.stage2 = nn.Sequential(
            ConvBNReLU(64, 128),
            ConvBNReLU(128, 128),
            nn.MaxPool2d(2, 2),
        )

        # Stage 3: /8
        self.stage3 = nn.Sequential(
            ConvBNReLU(128, 256),
            ConvBNReLU(256, 256),
            ConvBNReLU(256, 256),
            nn.MaxPool2d(2, 2),
        )

        # Stage 4: /16
        self.stage4 = nn.Sequential(
            ConvBNReLU(256, 512),
            ConvBNReLU(512, 512),
            ConvBNReLU(512, 512),
            nn.MaxPool2d(2, 2),
        )

        # Stage 5: /32
        self.stage5 = nn.Sequential(
            ConvBNReLU(512, 512),
            ConvBNReLU(512, 512),
            ConvBNReLU(512, 512),
            nn.MaxPool2d(2, 2),
        )

        self._init_weights()

    def _init_weights(self):
        """Initialize weights with Kaiming initialization."""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x: torch.Tensor):
        """
        Forward pass returning multi-scale features.

        Args:
            x: Input tensor [B, C, H, W]

        Returns:
            Tuple of feature maps at different scales
        """
        f1 = self.stage1(x)    # [B, 64, H/2, W/2]
        f2 = self.stage2(f1)   # [B, 128, H/4, W/4]
        f3 = self.stage3(f2)   # [B, 256, H/8, W/8]
        f4 = self.stage4(f3)   # [B, 512, H/16, W/16]
        f5 = self.stage5(f4)   # [B, 512, H/32, W/32]

        return f1, f2, f3, f4, f5


class LightBackbone(nn.Module):
    """
    Lightweight backbone for fast inference.

    Uses fewer layers and channels for mobile/edge deployment.

    Args:
        in_channels: Number of input channels (3 for RGB)
    """

    def __init__(self, in_channels: int = 3):
        super().__init__()

        self.stage1 = nn.Sequential(
            ConvBNReLU(in_channels, 32),
            nn.MaxPool2d(2, 2),
        )

        self.stage2 = nn.Sequential(
            ConvBNReLU(32, 64),
            nn.MaxPool2d(2, 2),
        )

        self.stage3 = nn.Sequential(
            ConvBNReLU(64, 128),
            ConvBNReLU(128, 128),
            nn.MaxPool2d(2, 2),
        )

        self.stage4 = nn.Sequential(
            ConvBNReLU(128, 256),
            ConvBNReLU(256, 256),
            nn.MaxPool2d(2, 2),
        )

        self.stage5 = nn.Sequential(
            ConvBNReLU(256, 256),
            nn.MaxPool2d(2, 2),
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x: torch.Tensor):
        f1 = self.stage1(x)
        f2 = self.stage2(f1)
        f3 = self.stage3(f2)
        f4 = self.stage4(f3)
        f5 = self.stage5(f4)
        return f1, f2, f3, f4, f5
