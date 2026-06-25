"""
深度估计网络架构 - 编码器-解码器结构

实现单目深度估计模型，使用编码器提取图像特征，
解码器逐步上采样恢复空间分辨率，最终输出深度图。

架构:
    图像输入 → 编码器(下采样) → 瓶颈层 → 解码器(上采样) → 深度图输出
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Optional


class ConvBlock(nn.Module):
    """卷积块: Conv + BatchNorm + ReLU"""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        stride: int = 1,
        padding: int = 1,
    ):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.relu(self.bn(self.conv(x)))


class ResidualBlock(nn.Module):
    """残差块: 两层卷积 + 跳跃连接"""

    def __init__(self, channels: int):
        super().__init__()
        self.conv1 = ConvBlock(channels, channels)
        self.conv2 = nn.Sequential(
            nn.Conv2d(channels, channels, 3, 1, 1),
            nn.BatchNorm2d(channels),
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        out = self.conv1(x)
        out = self.conv2(out)
        out = out + residual
        return self.relu(out)


class DepthEncoder(nn.Module):
    """
    深度估计编码器

    使用多层卷积逐步下采样图像，提取多尺度特征。
    输出各层特征用于解码器的跳跃连接。

    Args:
        in_channels: 输入通道数 (默认 3，RGB 图像)
        base_channels: 基础通道数 (默认 64)
    """

    def __init__(self, in_channels: int = 3, base_channels: int = 64):
        super().__init__()

        # Stem: 7x7 卷积 + 最大池化，快速降低分辨率
        self.stem = nn.Sequential(
            ConvBlock(in_channels, base_channels, kernel_size=7, stride=2, padding=3),
            nn.MaxPool2d(3, stride=2, padding=1),
        )

        # 编码器各层
        self.layer1 = self._make_layer(base_channels, base_channels * 2, num_blocks=2)
        self.layer2 = self._make_layer(base_channels * 2, base_channels * 4, num_blocks=2)
        self.layer3 = self._make_layer(base_channels * 4, base_channels * 8, num_blocks=2)
        self.layer4 = self._make_layer(base_channels * 8, base_channels * 16, num_blocks=2)

    def _make_layer(
        self, in_channels: int, out_channels: int, num_blocks: int
    ) -> nn.Sequential:
        """构建编码器层: 下采样 + 残差块"""
        layers = [
            ConvBlock(in_channels, out_channels, stride=2),  # 下采样
        ]
        for _ in range(num_blocks):
            layers.append(ResidualBlock(out_channels))
        return nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> List[torch.Tensor]:
        """
        前向传播

        Args:
            x: 输入图像 (B, C, H, W)

        Returns:
            各层特征列表 [stem, layer1, layer2, layer3, layer4]
        """
        features = []

        x = self.stem(x)       # 1/4 分辨率
        features.append(x)

        x = self.layer1(x)     # 1/8 分辨率
        features.append(x)

        x = self.layer2(x)     # 1/16 分辨率
        features.append(x)

        x = self.layer3(x)     # 1/32 分辨率
        features.append(x)

        x = self.layer4(x)     # 1/64 分辨率
        features.append(x)

        return features


class DecoderBlock(nn.Module):
    """
    解码器块

    通过反卷积上采样特征图，与编码器的跳跃连接特征融合。

    Args:
        in_channels: 输入通道数
        skip_channels: 跳跃连接通道数
        out_channels: 输出通道数
    """

    def __init__(
        self,
        in_channels: int,
        skip_channels: int,
        out_channels: int,
    ):
        super().__init__()

        # 反卷积上采样
        self.up = nn.ConvTranspose2d(
            in_channels, in_channels // 2, kernel_size=3, stride=2, padding=1, output_padding=1
        )

        # 融合跳跃连接后的卷积
        self.conv = nn.Sequential(
            ConvBlock(in_channels // 2 + skip_channels, out_channels),
            ResidualBlock(out_channels),
        )

    def forward(
        self, x: torch.Tensor, skip: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        前向传播

        Args:
            x: 上一层特征
            skip: 编码器跳跃连接特征

        Returns:
            上采样后的特征
        """
        x = self.up(x)

        # 处理尺寸不匹配
        if skip is not None:
            if x.shape[2:] != skip.shape[2:]:
                x = F.interpolate(x, size=skip.shape[2:], mode="bilinear", align_corners=True)
            x = torch.cat([x, skip], dim=1)

        return self.conv(x)


class DepthDecoder(nn.Module):
    """
    深度估计解码器

    逐步上采样特征图，融合编码器的多尺度特征，
    最终输出单通道深度图。

    Args:
        encoder_channels: 编码器各层通道数
        base_channels: 基础通道数
    """

    def __init__(
        self,
        encoder_channels: List[int] = None,
        base_channels: int = 64,
    ):
        super().__init__()

        if encoder_channels is None:
            # 默认编码器通道数: [64, 128, 256, 512, 1024]
            encoder_channels = [
                base_channels,
                base_channels * 2,
                base_channels * 4,
                base_channels * 8,
                base_channels * 16,
            ]

        # 解码器各层 (从最深层开始)
        self.decoder4 = DecoderBlock(
            encoder_channels[4], encoder_channels[3], encoder_channels[3]
        )
        self.decoder3 = DecoderBlock(
            encoder_channels[3], encoder_channels[2], encoder_channels[2]
        )
        self.decoder2 = DecoderBlock(
            encoder_channels[2], encoder_channels[1], encoder_channels[1]
        )
        self.decoder1 = DecoderBlock(
            encoder_channels[1], encoder_channels[0], encoder_channels[0]
        )

        # 最终上采样到原始分辨率 (从 1/4 -> 1/2 -> 1/1)
        self.final_up = nn.Sequential(
            nn.ConvTranspose2d(
                encoder_channels[0], encoder_channels[0] // 2,
                kernel_size=3, stride=2, padding=1, output_padding=1,
            ),
            ConvBlock(encoder_channels[0] // 2, encoder_channels[0] // 4),
            nn.ConvTranspose2d(
                encoder_channels[0] // 4, encoder_channels[0] // 4,
                kernel_size=3, stride=2, padding=1, output_padding=1,
            ),
            ConvBlock(encoder_channels[0] // 4, encoder_channels[0] // 4),
        )

        # 深度预测头
        self.depth_head = nn.Sequential(
            nn.Conv2d(encoder_channels[0] // 4, 32, 3, 1, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 1, 1),
            nn.Sigmoid(),  # 输出 [0, 1] 范围的深度
        )

    def forward(self, features: List[torch.Tensor]) -> torch.Tensor:
        """
        前向传播

        Args:
            features: 编码器各层特征 [stem, layer1, layer2, layer3, layer4]

        Returns:
            预测深度图 (B, 1, H, W)
        """
        # 从最深层开始解码
        x = features[4]                           # 最深层特征
        x = self.decoder4(x, features[3])         # 上采样 + 跳跃连接
        x = self.decoder3(x, features[2])         # 上采样 + 跳跃连接
        x = self.decoder2(x, features[1])         # 上采样 + 跳跃连接
        x = self.decoder1(x, features[0])         # 上采样 + 跳跃连接

        # 最终上采样
        x = self.final_up(x)

        # 预测深度图
        depth = self.depth_head(x)

        return depth


class DepthEstimationNet(nn.Module):
    """
    完整的深度估计网络

    编码器-解码器架构，使用跳跃连接保留多尺度信息。

    Args:
        in_channels: 输入图像通道数 (默认 3)
        base_channels: 基础通道数 (默认 64)

    Example:
        >>> model = DepthEstimationNet(in_channels=3, base_channels=64)
        >>> images = torch.randn(2, 3, 256, 256)
        >>> depth = model(images)
        >>> print(depth.shape)  # (2, 1, 256, 256)
    """

    def __init__(self, in_channels: int = 3, base_channels: int = 64):
        super().__init__()
        self.encoder = DepthEncoder(in_channels, base_channels)
        self.decoder = DepthDecoder(base_channels=base_channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            x: 输入图像 (B, C, H, W)

        Returns:
            预测深度图 (B, 1, H, W)
        """
        features = self.encoder(x)
        depth = self.decoder(features)
        return depth


class SimpleDepthNet(nn.Module):
    """
    简化版深度估计网络

    使用简单的编码器-解码器结构，用于快速测试和验证。

    Args:
        in_channels: 输入通道数
        base_channels: 基础通道数

    Example:
        >>> model = SimpleDepthNet()
        >>> images = torch.randn(2, 3, 128, 128)
        >>> depth = model(images)
        >>> print(depth.shape)  # (2, 1, 128, 128)
    """

    def __init__(self, in_channels: int = 3, base_channels: int = 32):
        super().__init__()

        # 简单编码器
        self.encoder = nn.Sequential(
            ConvBlock(in_channels, base_channels, stride=2),      # 1/2
            ConvBlock(base_channels, base_channels * 2, stride=2),  # 1/4
            ConvBlock(base_channels * 2, base_channels * 4, stride=2),  # 1/8
            ResidualBlock(base_channels * 4),
        )

        # 简单解码器
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(base_channels * 4, base_channels * 2, 4, 2, 1),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(base_channels * 2, base_channels, 4, 2, 1),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(base_channels, base_channels // 2, 4, 2, 1),
            nn.ReLU(inplace=True),
        )

        # 深度预测头
        self.depth_head = nn.Sequential(
            nn.Conv2d(base_channels // 2, 1, 3, 1, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            x: 输入图像 (B, C, H, W)

        Returns:
            预测深度图 (B, 1, H, W)
        """
        features = self.encoder(x)
        decoded = self.decoder(features)

        # 确保输出尺寸与输入匹配
        if decoded.shape[2:] != x.shape[2:]:
            decoded = F.interpolate(decoded, size=x.shape[2:], mode="bilinear", align_corners=True)

        depth = self.depth_head(decoded)
        return depth


class MultiScaleDepthNet(nn.Module):
    """
    多尺度深度估计网络

    在解码器的多个层级输出深度图，用于深度监督训练。

    Args:
        in_channels: 输入通道数
        base_channels: 基础通道数
        num_scales: 输出尺度数 (默认 4)

    Example:
        >>> model = MultiScaleDepthNet()
        >>> images = torch.randn(2, 3, 256, 256)
        >>> depths = model(images)
        >>> for d in depths:
        ...     print(d.shape)
    """

    def __init__(
        self,
        in_channels: int = 3,
        base_channels: int = 64,
        num_scales: int = 4,
    ):
        super().__init__()
        self.num_scales = num_scales
        self.encoder = DepthEncoder(in_channels, base_channels)

        # 编码器各层通道数: [base, base*2, base*4, base*8, base*16]
        # 使用最后 num_scales 层
        self.feature_indices = list(range(5 - num_scales, 5))

        # 各尺度的深度预测头
        self.depth_heads = nn.ModuleList()
        for idx in self.feature_indices:
            channels = base_channels * (2 ** idx)
            self.depth_heads.append(
                nn.Sequential(
                    nn.Conv2d(channels, 1, 1),
                    nn.Sigmoid(),
                )
            )

        # 上采样层
        self.upsamples = nn.ModuleList()
        for i in range(num_scales - 1):
            higher_idx = self.feature_indices[num_scales - 1 - i]
            lower_idx = self.feature_indices[num_scales - 2 - i]
            higher_channels = base_channels * (2 ** higher_idx)
            lower_channels = base_channels * (2 ** lower_idx)
            self.upsamples.append(
                nn.ConvTranspose2d(
                    higher_channels,
                    lower_channels,
                    kernel_size=3,
                    stride=2,
                    padding=1,
                    output_padding=1,
                )
            )

    def forward(self, x: torch.Tensor) -> List[torch.Tensor]:
        """
        前向传播

        Args:
            x: 输入图像 (B, C, H, W)

        Returns:
            各尺度深度图列表
        """
        features = self.encoder(x)
        input_size = x.shape[2:]

        multi_scale_depths = []

        # 从最深层开始
        last_feature_idx = self.feature_indices[-1]
        current = features[last_feature_idx]

        for i in range(self.num_scales):
            # 预测当前尺度深度
            depth = self.depth_heads[self.num_scales - 1 - i](current)
            depth = F.interpolate(depth, size=input_size, mode="bilinear", align_corners=True)
            multi_scale_depths.append(depth)

            # 上采样到下一尺度
            if i < self.num_scales - 1:
                current = self.upsamples[i](current)
                # 融合跳跃连接
                skip_idx = self.feature_indices[self.num_scales - 2 - i]
                skip = features[skip_idx]
                if current.shape[2:] != skip.shape[2:]:
                    current = F.interpolate(current, size=skip.shape[2:], mode="bilinear", align_corners=True)
                current = current + skip

        return multi_scale_depths


def count_parameters(model: nn.Module) -> int:
    """计算模型参数数量"""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def model_summary(model: nn.Module, input_size: Tuple[int, ...] = (1, 3, 256, 256)) -> str:
    """
    打印模型摘要

    Args:
        model: 模型
        input_size: 输入尺寸

    Returns:
        模型摘要字符串
    """
    x = torch.randn(*input_size)
    with torch.no_grad():
        output = model(x)

    if isinstance(output, list):
        output_shapes = [str(o.shape) for o in output]
    else:
        output_shapes = [str(output.shape)]

    total_params = count_parameters(model)

    summary = f"""
模型摘要:
  输入尺寸: {input_size}
  输出尺寸: {output_shapes}
  总参数量: {total_params:,}
  模型大小: {total_params * 4 / 1024 / 1024:.2f} MB (float32)
"""
    return summary
