"""
骨干网络模块

提供各种 2D 和 3D 骨干网络实现。
"""

import torch
import torch.nn as nn
from typing import List, Tuple


class ConvBlock(nn.Module):
    """
    卷积块。
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        stride: int = 1,
        padding: int = 1,
        bias: bool = False
    ):
        """
        初始化卷积块。

        Args:
            in_channels: 输入通道数
            out_channels: 输出通道数
            kernel_size: 卷积核大小
            stride: 步长
            padding: 填充
            bias: 是否使用偏置
        """
        super().__init__()

        self.conv = nn.Conv2d(
            in_channels, out_channels,
            kernel_size=kernel_size,
            stride=stride,
            padding=padding,
            bias=bias
        )
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播。

        Args:
            x: (B, C, H, W) 输入特征图

        Returns:
            (B, C', H', W') 输出特征图
        """
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)

        return x


class ResBlock(nn.Module):
    """
    残差块。
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        stride: int = 1
    ):
        """
        初始化残差块。

        Args:
            in_channels: 输入通道数
            out_channels: 输出通道数
            stride: 步长
        """
        super().__init__()

        self.conv1 = nn.Conv2d(
            in_channels, out_channels,
            kernel_size=3, stride=stride, padding=1, bias=False
        )
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(
            out_channels, out_channels,
            kernel_size=3, stride=1, padding=1, bias=False
        )
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

        # 快捷连接
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(
                    in_channels, out_channels,
                    kernel_size=1, stride=stride, bias=False
                ),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播。

        Args:
            x: (B, C, H, W) 输入特征图

        Returns:
            (B, C', H', W') 输出特征图
        """
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        out += self.shortcut(residual)
        out = self.relu(out)

        return out


class ResNet18(nn.Module):
    """
    ResNet-18 骨干网络。
    """

    def __init__(self, in_channels: int = 64):
        """
        初始化 ResNet-18。

        Args:
            in_channels: 输入通道数
        """
        super().__init__()

        self.layer1 = self._make_layer(in_channels, 64, num_blocks=2, stride=1)
        self.layer2 = self._make_layer(64, 128, num_blocks=2, stride=2)
        self.layer3 = self._make_layer(128, 256, num_blocks=2, stride=2)
        self.layer4 = self._make_layer(256, 512, num_blocks=2, stride=2)

    def _make_layer(
        self,
        in_channels: int,
        out_channels: int,
        num_blocks: int,
        stride: int
    ) -> nn.Sequential:
        """
        创建残差层。

        Args:
            in_channels: 输入通道数
            out_channels: 输出通道数
            num_blocks: 残差块数量
            stride: 步长

        Returns:
            残差层
        """
        layers = []
        layers.append(ResBlock(in_channels, out_channels, stride))

        for _ in range(1, num_blocks):
            layers.append(ResBlock(out_channels, out_channels, stride=1))

        return nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> List[torch.Tensor]:
        """
        前向传播。

        Args:
            x: (B, C, H, W) 输入特征图

        Returns:
            多尺度特征图列表
        """
        c1 = self.layer1(x)
        c2 = self.layer2(c1)
        c3 = self.layer3(c2)
        c4 = self.layer4(c3)

        return [c1, c2, c3, c4]


class SEBlock(nn.Module):
    """
    Squeeze-and-Excitation 块。
    """

    def __init__(self, channels: int, reduction: int = 16):
        """
        初始化 SE 块。

        Args:
            channels: 通道数
            reduction: 压缩比
        """
        super().__init__()

        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channels, channels // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channels // reduction, channels, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播。

        Args:
            x: (B, C, H, W) 输入特征图

        Returns:
            (B, C, H, W) 输出特征图
        """
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)

        return x * y.expand_as(x)


class ResNet18WithSE(nn.Module):
    """
    带 SE 模块的 ResNet-18 骨干网络。
    """

    def __init__(self, in_channels: int = 64):
        """
        初始化带 SE 模块的 ResNet-18。

        Args:
            in_channels: 输入通道数
        """
        super().__init__()

        self.layer1 = self._make_layer(in_channels, 64, num_blocks=2, stride=1)
        self.layer2 = self._make_layer(64, 128, num_blocks=2, stride=2)
        self.layer3 = self._make_layer(128, 256, num_blocks=2, stride=2)
        self.layer4 = self._make_layer(256, 512, num_blocks=2, stride=2)

        # SE 模块
        self.se1 = SEBlock(64)
        self.se2 = SEBlock(128)
        self.se3 = SEBlock(256)
        self.se4 = SEBlock(512)

    def _make_layer(
        self,
        in_channels: int,
        out_channels: int,
        num_blocks: int,
        stride: int
    ) -> nn.Sequential:
        """
        创建残差层。

        Args:
            in_channels: 输入通道数
            out_channels: 输出通道数
            num_blocks: 残差块数量
            stride: 步长

        Returns:
            残差层
        """
        layers = []
        layers.append(ResBlock(in_channels, out_channels, stride))

        for _ in range(1, num_blocks):
            layers.append(ResBlock(out_channels, out_channels, stride=1))

        return nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> List[torch.Tensor]:
        """
        前向传播。

        Args:
            x: (B, C, H, W) 输入特征图

        Returns:
            多尺度特征图列表
        """
        c1 = self.se1(self.layer1(x))
        c2 = self.se2(self.layer2(c1))
        c3 = self.se3(self.layer3(c2))
        c4 = self.se4(self.layer4(c3))

        return [c1, c2, c3, c4]


class VGG16(nn.Module):
    """
    VGG-16 骨干网络。
    """

    def __init__(self, in_channels: int = 64):
        """
        初始化 VGG-16。

        Args:
            in_channels: 输入通道数
        """
        super().__init__()

        self.features = nn.Sequential(
            # Block 1
            ConvBlock(in_channels, 64, kernel_size=3, stride=1, padding=1),
            ConvBlock(64, 64, kernel_size=3, stride=1, padding=1),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 2
            ConvBlock(64, 128, kernel_size=3, stride=1, padding=1),
            ConvBlock(128, 128, kernel_size=3, stride=1, padding=1),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 3
            ConvBlock(128, 256, kernel_size=3, stride=1, padding=1),
            ConvBlock(256, 256, kernel_size=3, stride=1, padding=1),
            ConvBlock(256, 256, kernel_size=3, stride=1, padding=1),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 4
            ConvBlock(256, 512, kernel_size=3, stride=1, padding=1),
            ConvBlock(512, 512, kernel_size=3, stride=1, padding=1),
            ConvBlock(512, 512, kernel_size=3, stride=1, padding=1),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 5
            ConvBlock(512, 512, kernel_size=3, stride=1, padding=1),
            ConvBlock(512, 512, kernel_size=3, stride=1, padding=1),
            ConvBlock(512, 512, kernel_size=3, stride=1, padding=1),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播。

        Args:
            x: (B, C, H, W) 输入特征图

        Returns:
            (B, 512, H/32, W/32) 输出特征图
        """
        return self.features(x)


class MobileNetV2(nn.Module):
    """
    MobileNetV2 骨干网络。
    """

    def __init__(self, in_channels: int = 64):
        """
        初始化 MobileNetV2。

        Args:
            in_channels: 输入通道数
        """
        super().__init__()

        # 初始卷积层
        self.conv1 = ConvBlock(in_channels, 32, kernel_size=3, stride=2, padding=1)

        # 倒残差块
        self.blocks = nn.Sequential(
            self._inverted_residual(32, 16, stride=1, expand_ratio=1),
            self._inverted_residual(16, 24, stride=2, expand_ratio=6),
            self._inverted_residual(24, 24, stride=1, expand_ratio=6),
            self._inverted_residual(24, 32, stride=2, expand_ratio=6),
            self._inverted_residual(32, 32, stride=1, expand_ratio=6),
            self._inverted_residual(32, 32, stride=1, expand_ratio=6),
            self._inverted_residual(32, 64, stride=2, expand_ratio=6),
            self._inverted_residual(64, 64, stride=1, expand_ratio=6),
            self._inverted_residual(64, 64, stride=1, expand_ratio=6),
            self._inverted_residual(64, 64, stride=1, expand_ratio=6),
            self._inverted_residual(64, 96, stride=1, expand_ratio=6),
            self._inverted_residual(96, 96, stride=1, expand_ratio=6),
            self._inverted_residual(96, 96, stride=1, expand_ratio=6),
            self._inverted_residual(96, 160, stride=2, expand_ratio=6),
            self._inverted_residual(160, 160, stride=1, expand_ratio=6),
            self._inverted_residual(160, 160, stride=1, expand_ratio=6),
            self._inverted_residual(160, 320, stride=1, expand_ratio=6),
        )

        # 最终卷积层
        self.conv2 = ConvBlock(320, 1280, kernel_size=1, stride=1, padding=0)

    def _inverted_residual(
        self,
        in_channels: int,
        out_channels: int,
        stride: int,
        expand_ratio: int
    ) -> nn.Sequential:
        """
        创建倒残差块。

        Args:
            in_channels: 输入通道数
            out_channels: 输出通道数
            stride: 步长
            expand_ratio: 扩展比

        Returns:
            倒残差块
        """
        hidden_dim = in_channels * expand_ratio

        layers = []

        # 扩展层
        if expand_ratio != 1:
            layers.extend([
                nn.Conv2d(in_channels, hidden_dim, kernel_size=1, bias=False),
                nn.BatchNorm2d(hidden_dim),
                nn.ReLU6(inplace=True)
            ])

        # 深度可分离卷积
        layers.extend([
            nn.Conv2d(
                hidden_dim, hidden_dim,
                kernel_size=3, stride=stride, padding=1,
                groups=hidden_dim, bias=False
            ),
            nn.BatchNorm2d(hidden_dim),
            nn.ReLU6(inplace=True)
        ])

        # 投影层
        layers.extend([
            nn.Conv2d(hidden_dim, out_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(out_channels)
        ])

        return nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播。

        Args:
            x: (B, C, H, W) 输入特征图

        Returns:
            (B, 1280, H/32, W/32) 输出特征图
        """
        x = self.conv1(x)
        x = self.blocks(x)
        x = self.conv2(x)

        return x


def build_backbone(backbone_name: str, in_channels: int = 64) -> nn.Module:
    """
    构建骨干网络。

    Args:
        backbone_name: 骨干网络名称
        in_channels: 输入通道数

    Returns:
        骨干网络模型

    Raises:
        ValueError: 如果骨干网络名称不支持
    """
    backbone_dict = {
        'resnet18': ResNet18,
        'resnet18_se': ResNet18WithSE,
        'vgg16': VGG16,
        'mobilenet_v2': MobileNetV2,
    }

    if backbone_name not in backbone_dict:
        raise ValueError(f"不支持的骨干网络: {backbone_name}")

    backbone = backbone_dict[backbone_name](in_channels)

    return backbone
