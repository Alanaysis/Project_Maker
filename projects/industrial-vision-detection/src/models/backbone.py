"""
骨干网络 (Backbone) 实现

实现 CSPDarknet 风格的骨干网络，用于提取图像的多尺度特征。

核心组件:
- ConvBlock: 基础卷积块 (Conv + BN + Activation)
- CSPBlock: Cross Stage Partial 块
- SPPF: Spatial Pyramid Pooling - Fast
- CSPDarknet: 完整骨干网络

参考:
- YOLOv8: https://github.com/ultralytics/ultralytics
- CSPNet: https://arxiv.org/abs/1911.11929
"""

import torch
import torch.nn as nn
from typing import List, Tuple


class ConvBlock(nn.Module):
    """
    基础卷积块: Conv + BatchNorm + Activation

    这是构建所有复杂模块的基础组件。

    Args:
        in_channels (int): 输入通道数
        out_channels (int): 输出通道数
        kernel_size (int): 卷积核大小，默认为 1
        stride (int): 步长，默认为 1
        activation (str): 激活函数类型，默认为 'SiLU'

    ⭐ 重点理解:
    - BatchNorm 的作用: 稳定训练，加速收敛
    - SiLU 激活函数: f(x) = x * sigmoid(x)，比 ReLU 更平滑
    - bias=False: 使用 BN 时不需要 bias
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 1,
        stride: int = 1,
        activation: str = 'SiLU'
    ):
        super().__init__()

        # 计算 padding 保持空间尺寸不变
        padding = kernel_size // 2

        # 卷积层
        self.conv = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size,
            stride,
            padding,
            bias=False  # 使用 BN 时不需要 bias
        )

        # 批归一化层
        self.bn = nn.BatchNorm2d(out_channels)

        # 激活函数
        if activation == 'SiLU':
            self.act = nn.SiLU(inplace=True)
        elif activation == 'ReLU':
            self.act = nn.ReLU(inplace=True)
        elif activation == 'LeakyReLU':
            self.act = nn.LeakyReLU(0.1, inplace=True)
        else:
            self.act = nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            x: 输入张量 [B, C_in, H, W]

        Returns:
            输出张量 [B, C_out, H', W']
        """
        return self.act(self.bn(self.conv(x)))


class Bottleneck(nn.Module):
    """
    瓶颈块: 用于 CSPBlock 中

    结构:
    x → Conv 1x1 → Conv 3x3 → + x (残差连接)

    Args:
        in_channels (int): 输入通道数
        out_channels (int): 输出通道数
        shortcut (bool): 是否使用残差连接
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        shortcut: bool = True
    ):
        super().__init__()
        hidden_channels = out_channels

        self.conv1 = ConvBlock(in_channels, hidden_channels, kernel_size=1)
        self.conv2 = ConvBlock(hidden_channels, out_channels, kernel_size=3)
        self.shortcut = shortcut and in_channels == out_channels

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        residual = x
        out = self.conv1(x)
        out = self.conv2(out)

        # 残差连接
        if self.shortcut:
            out = out + residual

        return out


class CSPBlock(nn.Module):
    """
    Cross Stage Partial Block

    CSP 结构将输入分为两部分:
    1. 一部分直接通过 (shortcut)
    2. 一部分经过多个 Bottleneck

    最后将两部分拼接并融合。

    这种设计:
    - 减少了计算量
    - 增强了梯度流
    - 提升了特征重用

    Args:
        in_channels (int): 输入通道数
        out_channels (int): 输出通道数
        num_bottlenecks (int): Bottleneck 数量
        shortcut (bool): 是否使用残差连接

    ⭐ 重点理解:
    - CSP 结构如何减少计算量: 只对一部分特征进行处理
    - 为什么能增强梯度流: 保留了直接的梯度路径
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        num_bottlenecks: int = 1,
        shortcut: bool = True
    ):
        super().__init__()

        # 将输入通道分为两部分
        hidden_channels = out_channels // 2

        # 第一部分: 直接通过
        self.conv1 = ConvBlock(in_channels, hidden_channels, kernel_size=1)

        # 第二部分: 经过多个 Bottleneck
        self.conv2 = ConvBlock(in_channels, hidden_channels, kernel_size=1)

        # Bottleneck 序列
        self.bottlenecks = nn.Sequential(*[
            Bottleneck(hidden_channels, hidden_channels, shortcut)
            for _ in range(num_bottlenecks)
        ])

        # 最终融合卷积
        self.conv3 = ConvBlock(hidden_channels * 2, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            x: 输入张量 [B, C_in, H, W]

        Returns:
            输出张量 [B, C_out, H, W]
        """
        # 第一部分: 直接通过
        part1 = self.conv1(x)

        # 第二部分: 经过 Bottleneck
        part2 = self.conv2(x)
        part2 = self.bottlenecks(part2)

        # 拼接两部分
        out = torch.cat([part1, part2], dim=1)

        # 融合
        out = self.conv3(out)

        return out


class SPPF(nn.Module):
    """
    Spatial Pyramid Pooling - Fast

    SPPF 通过多个不同大小的 MaxPool 来增强感受野，
    能够处理不同尺度的目标。

    结构:
    x → Conv 1x1 → MaxPool 5x5 → MaxPool 5x5 → MaxPool 5x5
                 ↓               ↓               ↓
              (concat all) → Conv 1x1 → output

    Args:
        in_channels (int): 输入通道数
        out_channels (int): 输出通道数
        kernel_size (int): MaxPool 核大小，默认为 5

    💡 值得思考:
    - 为什么 SPP 能增强感受野？
    - SPPF 与 SPP 的区别是什么？
    - 对检测大目标有什么帮助？
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 5
    ):
        super().__init__()
        hidden_channels = in_channels // 2

        # 初始卷积
        self.conv1 = ConvBlock(in_channels, hidden_channels, kernel_size=1)

        # 多个 MaxPool
        self.pool1 = nn.MaxPool2d(kernel_size, stride=1, padding=kernel_size // 2)
        self.pool2 = nn.MaxPool2d(kernel_size, stride=1, padding=kernel_size // 2)
        self.pool3 = nn.MaxPool2d(kernel_size, stride=1, padding=kernel_size // 2)

        # 最终卷积
        self.conv2 = ConvBlock(hidden_channels * 4, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            x: 输入张量 [B, C_in, H, W]

        Returns:
            输出张量 [B, C_out, H, W]
        """
        # 初始卷积
        x = self.conv1(x)

        # 多个 MaxPool 并拼接
        pool1 = self.pool1(x)
        pool2 = self.pool2(pool1)
        pool3 = self.pool3(pool2)

        # 拼接所有特征
        out = torch.cat([x, pool1, pool2, pool3], dim=1)

        # 最终卷积
        out = self.conv2(out)

        return out


class CSPDarknet(nn.Module):
    """
    CSPDarknet 骨干网络

    这是 YOLO 系列使用的骨干网络，用于提取多尺度特征。

    结构:
    输入图像 [B, 3, H, W]
        ↓
    Stem (Conv 3x3, stride=2)
        ↓
    Stage 1 (CSP Block × 1) → [B, 64, H/4, W/4]
        ↓
    Stage 2 (CSP Block × 2) → [B, 128, H/8, W/8]    ← P3 输出
        ↓
    Stage 3 (CSP Block × 2) → [B, 256, H/16, W/16]   ← P4 输出
        ↓
    Stage 4 (CSP Block × 1) → [B, 512, H/32, W/32]   ← P5 输出
        ↓
    SPPF → [B, 512, H/32, W/32]

    Args:
        depth_multiple (float): 深度因子，控制模块重复次数
        width_multiple (float): 宽度因子，控制通道数

    ⭐ 重点理解:
    - 多尺度特征图的含义: P3检测小目标，P5检测大目标
    - 下采样的作用: 扩大感受野，减少计算量
    - CSP 结构的优势: 减少计算量，增强梯度流
    """

    def __init__(
        self,
        depth_multiple: float = 0.33,
        width_multiple: float = 0.25
    ):
        super().__init__()

        # 基础通道数
        base_channels = int(64 * width_multiple)

        # 深度 (每个 stage 的 CSP Block 数量)
        depth1 = max(round(1 * depth_multiple), 1)
        depth2 = max(round(2 * depth_multiple), 1)

        # Stem: 初始下采样
        # 输入: [B, 3, 640, 640] → 输出: [B, 32, 320, 320]
        self.stem = ConvBlock(3, base_channels, kernel_size=3, stride=2)

        # Stage 1: 第一个 CSP 阶段
        # 输入: [B, 32, 320, 320] → 输出: [B, 64, 160, 160]
        self.stage1 = nn.Sequential(
            ConvBlock(base_channels, base_channels * 2, kernel_size=3, stride=2),
            CSPBlock(base_channels * 2, base_channels * 2, num_bottlenecks=depth1)
        )

        # Stage 2: 第二个 CSP 阶段 (输出 P3)
        # 输入: [B, 64, 160, 160] → 输出: [B, 128, 80, 80]
        self.stage2 = nn.Sequential(
            ConvBlock(base_channels * 2, base_channels * 4, kernel_size=3, stride=2),
            CSPBlock(base_channels * 4, base_channels * 4, num_bottlenecks=depth2)
        )

        # Stage 3: 第三个 CSP 阶段 (输出 P4)
        # 输入: [B, 128, 80, 80] → 输出: [B, 256, 40, 40]
        self.stage3 = nn.Sequential(
            ConvBlock(base_channels * 4, base_channels * 8, kernel_size=3, stride=2),
            CSPBlock(base_channels * 8, base_channels * 8, num_bottlenecks=depth2)
        )

        # Stage 4: 第四个 CSP 阶段 (输出 P5)
        # 输入: [B, 256, 40, 40] → 输出: [B, 512, 20, 20]
        self.stage4 = nn.Sequential(
            ConvBlock(base_channels * 8, base_channels * 16, kernel_size=3, stride=2),
            CSPBlock(base_channels * 16, base_channels * 16, num_bottlenecks=depth1)
        )

        # SPPF: 空间金字塔池化
        # 输入: [B, 512, 20, 20] → 输出: [B, 512, 20, 20]
        self.sppf = SPPF(base_channels * 16, base_channels * 16)

    def forward(self, x: torch.Tensor) -> List[torch.Tensor]:
        """
        前向传播，提取多尺度特征

        Args:
            x: 输入图像 [B, 3, H, W]

        Returns:
            多尺度特征列表:
            - P3: [B, 128, H/8, W/8]   (小目标)
            - P4: [B, 256, H/16, W/16]  (中目标)
            - P5: [B, 512, H/32, W/32]  (大目标)
        """
        # Stem
        x = self.stem(x)

        # Stage 1
        x = self.stage1(x)

        # Stage 2 → P3
        p3 = self.stage2(x)

        # Stage 3 → P4
        p4 = self.stage3(p3)

        # Stage 4 → P5
        p5 = self.stage4(p4)

        # SPPF
        p5 = self.sppf(p5)

        return [p3, p4, p5]


def test_backbone():
    """
    测试骨干网络

    验证:
    1. 模型能正常前向传播
    2. 输出形状正确
    3. 参数量合理
    """
    print("=" * 50)
    print("测试 CSPDarknet 骨干网络")
    print("=" * 50)

    # 创建模型
    model = CSPDarknet(depth_multiple=0.33, width_multiple=0.25)

    # 打印模型结构
    print(f"\n模型参数量: {sum(p.numel() for p in model.parameters()):,}")

    # 创建测试输入
    batch_size = 2
    input_tensor = torch.randn(batch_size, 3, 640, 640)
    print(f"输入形状: {input_tensor.shape}")

    # 前向传播
    with torch.no_grad():
        outputs = model(input_tensor)

    # 打印输出形状
    print("\n输出特征图:")
    for i, feat in enumerate(outputs):
        print(f"  P{i+3}: {feat.shape}")

    # 验证输出形状
    assert outputs[0].shape == (batch_size, 64, 80, 80), "P3 形状错误"
    assert outputs[1].shape == (batch_size, 128, 40, 40), "P4 形状错误"
    assert outputs[2].shape == (batch_size, 256, 20, 20), "P5 形状错误"

    print("\n✓ 骨干网络测试通过!")
    return True


if __name__ == '__main__':
    test_backbone()
