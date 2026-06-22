"""
特征融合网络 (Neck) 实现

实现 PANet (Path Aggregation Network) 风格的特征融合网络，
用于融合不同尺度的特征，增强多尺度检测能力。

核心组件:
- C2f: CSP Bottleneck with 2 convolutions
- FPN: Feature Pyramid Network (自顶向下)
- PAN: Path Aggregation Network (自底向上)
- PANet: 完整特征融合网络

参考:
- PANet: https://arxiv.org/abs/1803.01534
- YOLOv8: https://github.com/ultralytics/ultralytics

⭐ 重点理解:
- FPN 如何传递高层语义信息到低层
- PAN 如何传递低层位置信息到高层
- 为什么需要双向特征融合
"""

import torch
import torch.nn as nn
from typing import List

from .backbone import ConvBlock


class C2f(nn.Module):
    """
    CSP Bottleneck with 2 convolutions

    C2f 是 YOLOv8 中使用的特征融合模块，相比传统的 C3 模块，
    它具有更好的梯度流和特征重用。

    结构:
    x → Split → [part1, part2]
                 ↓
              part2 → Bottleneck × N
                 ↓
              [part1, bottleneck_outputs] → Concat → Conv 1x1

    Args:
        in_channels (int): 输入通道数
        out_channels (int): 输出通道数
        num_bottlenecks (int): Bottleneck 数量
        shortcut (bool): 是否使用残差连接

    💡 值得思考:
    - C2f 与 CSPBlock 的区别是什么？
    - 为什么 split 的比例是 1:1？
    - 如何影响梯度流？
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

        # 初始卷积: 将输入通道数减半
        self.conv1 = ConvBlock(in_channels, hidden_channels, kernel_size=1)

        # Bottleneck 序列
        self.bottlenecks = nn.ModuleList([
            Bottleneck(hidden_channels, hidden_channels, shortcut)
            for _ in range(num_bottlenecks)
        ])

        # 最终融合卷积
        # 输入: part1 + bottleneck_outputs (num_bottlenecks + 1) 个 hidden_channels
        self.conv2 = ConvBlock(
            hidden_channels * (num_bottlenecks + 1),
            out_channels,
            kernel_size=1
        )

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

        # Split: 分为两部分
        part1 = x

        # 依次通过 Bottleneck，并保存中间结果
        part2 = x
        outputs = [part1]  # 保存第一部分

        for bottleneck in self.bottlenecks:
            part2 = bottleneck(part2)
            outputs.append(part2)  # 保存每个 Bottleneck 的输出

        # 拼接所有部分
        out = torch.cat(outputs, dim=1)

        # 最终融合
        out = self.conv2(out)

        return out


class Bottleneck(nn.Module):
    """
    瓶颈块: 用于 C2f 中

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

        if self.shortcut:
            out = out + residual

        return out


class Upsample(nn.Module):
    """
    上采样模块

    使用最近邻插值进行上采样，然后通过卷积调整通道数。

    Args:
        in_channels (int): 输入通道数
        out_channels (int): 输出通道数
        scale_factor (int): 上采样倍数，默认为 2
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        scale_factor: int = 2
    ):
        super().__init__()
        self.upsample = nn.Upsample(
            scale_factor=scale_factor,
            mode='nearest'
        )
        self.conv = ConvBlock(in_channels, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        x = self.upsample(x)
        x = self.conv(x)
        return x


class Downsample(nn.Module):
    """
    下采样模块

    使用步长为 2 的卷积进行下采样。

    Args:
        in_channels (int): 输入通道数
        out_channels (int): 输出通道数
    """

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.conv = ConvBlock(in_channels, out_channels, kernel_size=3, stride=2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        return self.conv(x)


class PANet(nn.Module):
    """
    Path Aggregation Network

    PANet 结合了 FPN (自顶向下) 和 PAN (自底向上)，
    实现双向特征融合。

    结构:
    P5 (20×20) ─────────────────────────────────────┐
        ↓                                            │
    [Upsample + Conv]                                │
        ↓                                            │
    P4 (40×40) ──→ [Concat + C2f] ──→ [Upsample]    │
                                       ↓              │
    P3 (80×80) ──→ [Concat + C2f] ──→ [输出 P3]      │
                                       ↓              │
                              [Downsample + Concat + C2f] ──→ [输出 P4]
                                       ↓
                              [Downsample + Concat + C2f] ──→ [输出 P5]

    Args:
        in_channels_list (List[int]): 输入通道数列表 [P3, P4, P5]
        out_channels_list (List[int]): 输出通道数列表 [P3, P4, P5]
        depth_multiple (float): 深度因子

    ⭐ 重点理解:
    - FPN 部分: 传递高层语义信息到低层 (帮助小目标检测)
    - PAN 部分: 传递低层位置信息到高层 (帮助大目标定位)
    - Concat vs Add: Concat 保留更多信息，Add 更高效
    """

    def __init__(
        self,
        in_channels_list: List[int],
        out_channels_list: List[int],
        depth_multiple: float = 0.33
    ):
        super().__init__()

        # 深度配置
        depth = max(round(3 * depth_multiple), 1)

        # ==================== FPN 部分 (自顶向下) ====================

        # P5 → P4: 上采样 + 融合
        self.up5 = Upsample(in_channels_list[2], out_channels_list[1])
        self.c2f_fpn1 = C2f(
            in_channels_list[1] + out_channels_list[1],
            out_channels_list[1],
            num_bottlenecks=depth
        )

        # P4 → P3: 上采样 + 融合
        self.up4 = Upsample(out_channels_list[1], out_channels_list[0])
        self.c2f_fpn2 = C2f(
            in_channels_list[0] + out_channels_list[0],
            out_channels_list[0],
            num_bottlenecks=depth
        )

        # ==================== PAN 部分 (自底向上) ====================

        # P3 → P4: 下采样 + 融合
        self.down3 = Downsample(out_channels_list[0], out_channels_list[0])
        self.c2f_pan1 = C2f(
            out_channels_list[0] + out_channels_list[1],
            out_channels_list[1],
            num_bottlenecks=depth
        )

        # P4 → P5: 下采样 + 融合
        self.down4 = Downsample(out_channels_list[1], out_channels_list[1])
        self.c2f_pan2 = C2f(
            out_channels_list[1] + out_channels_list[2],
            out_channels_list[2],
            num_bottlenecks=depth
        )

    def forward(self, features: List[torch.Tensor]) -> List[torch.Tensor]:
        """
        前向传播

        Args:
            features: 骨干网络输出的多尺度特征 [P3, P4, P5]

        Returns:
            融合后的多尺度特征 [P3_out, P4_out, P5_out]
        """
        p3, p4, p5 = features

        # ==================== FPN 部分 (自顶向下) ====================

        # P5 → P4
        p5_up = self.up5(p5)  # 上采样
        p4_fpn = self.c2f_fpn1(torch.cat([p4, p5_up], dim=1))  # 融合

        # P4 → P3
        p4_up = self.up4(p4_fpn)  # 上采样
        p3_out = self.c2f_fpn2(torch.cat([p3, p4_up], dim=1))  # 融合

        # ==================== PAN 部分 (自底向上) ====================

        # P3 → P4
        p3_down = self.down3(p3_out)  # 下采样
        p4_out = self.c2f_pan1(torch.cat([p3_down, p4_fpn], dim=1))  # 融合

        # P4 → P5
        p4_down = self.down4(p4_out)  # 下采样
        p5_out = self.c2f_pan2(torch.cat([p4_down, p5], dim=1))  # 融合

        return [p3_out, p4_out, p5_out]


def test_neck():
    """
    测试特征融合网络

    验证:
    1. 模型能正常前向传播
    2. 输出形状正确
    3. 参数量合理
    """
    print("=" * 50)
    print("测试 PANet 特征融合网络")
    print("=" * 50)

    # 创建模拟的骨干网络输出
    batch_size = 2
    p3 = torch.randn(batch_size, 128, 80, 80)  # 小目标特征
    p4 = torch.randn(batch_size, 256, 40, 40)  # 中目标特征
    p5 = torch.randn(batch_size, 512, 20, 20)  # 大目标特征

    features = [p3, p4, p5]

    # 创建 PANet
    neck = PANet(
        in_channels_list=[128, 256, 512],
        out_channels_list=[128, 256, 512],
        depth_multiple=0.33
    )

    # 打印模型参数量
    print(f"\n模型参数量: {sum(p.numel() for p in neck.parameters()):,}")

    # 前向传播
    with torch.no_grad():
        outputs = neck(features)

    # 打印输出形状
    print("\n输入特征图:")
    for i, feat in enumerate(features):
        print(f"  P{i+3}: {feat.shape}")

    print("\n输出特征图:")
    for i, feat in enumerate(outputs):
        print(f"  P{i+3}_out: {feat.shape}")

    # 验证输出形状
    assert outputs[0].shape == (batch_size, 128, 80, 80), "P3 输出形状错误"
    assert outputs[1].shape == (batch_size, 256, 40, 40), "P4 输出形状错误"
    assert outputs[2].shape == (batch_size, 512, 20, 20), "P5 输出形状错误"

    print("\n✓ 特征融合网络测试通过!")
    return True


if __name__ == '__main__':
    test_neck()
