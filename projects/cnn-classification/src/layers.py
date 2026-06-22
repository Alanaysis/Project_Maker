"""
自定义CNN层实现

用于学习CNN的基本组件：
- Conv2D: 2D卷积层
- MaxPool2D: 最大池化层
- Flatten: 展平层
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional


class Conv2D(nn.Module):
    """
    2D卷积层实现

    卷积操作：在输入特征图上滑动卷积核，计算局部区域的加权和

    参数：
        in_channels: 输入通道数
        out_channels: 输出通道数（卷积核数量）
        kernel_size: 卷积核大小
        stride: 步长
        padding: 填充
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        stride: int = 1,
        padding: int = 0
    ):
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size if isinstance(kernel_size, tuple) else (kernel_size, kernel_size)
        self.stride = stride
        self.padding = padding

        # 初始化卷积核权重
        # 使用Kaiming初始化，适合ReLU激活函数
        self.weight = nn.Parameter(
            torch.randn(out_channels, in_channels, *self.kernel_size)
        )
        self.bias = nn.Parameter(torch.zeros(out_channels))

        # 权重初始化
        nn.init.kaiming_normal_(self.weight, mode='fan_out', nonlinearity='relu')

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        输入形状: (batch_size, in_channels, height, width)
        输出形状: (batch_size, out_channels, height_out, width_out)

        height_out = (height + 2*padding - kernel_size) / stride + 1
        """
        return F.conv2d(x, self.weight, self.bias, self.stride, self.padding)

    def extra_repr(self) -> str:
        return (f'in_channels={self.in_channels}, out_channels={self.out_channels}, '
                f'kernel_size={self.kernel_size}, stride={self.stride}, padding={self.padding}')


class MaxPool2D(nn.Module):
    """
    2D最大池化层

    池化操作：在局部区域取最大值，降低特征图尺寸

    参数：
        kernel_size: 池化窗口大小
        stride: 步长（默认等于kernel_size）
    """

    def __init__(self, kernel_size: int = 2, stride: Optional[int] = None):
        super().__init__()

        self.kernel_size = kernel_size
        self.stride = stride if stride is not None else kernel_size

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        输入形状: (batch_size, channels, height, width)
        输出形状: (batch_size, channels, height_out, width_out)
        """
        return F.max_pool2d(x, self.kernel_size, self.stride)

    def extra_repr(self) -> str:
        return f'kernel_size={self.kernel_size}, stride={self.stride}'


class AvgPool2D(nn.Module):
    """
    2D平均池化层

    参数：
        kernel_size: 池化窗口大小
        stride: 步长
    """

    def __init__(self, kernel_size: int = 2, stride: Optional[int] = None):
        super().__init__()

        self.kernel_size = kernel_size
        self.stride = stride if stride is not None else kernel_size

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.avg_pool2d(x, self.kernel_size, self.stride)

    def extra_repr(self) -> str:
        return f'kernel_size={self.kernel_size}, stride={self.stride}'


class Flatten(nn.Module):
    """
    展平层：将多维特征图展平为一维向量

    输入形状: (batch_size, channels, height, width)
    输出形状: (batch_size, channels * height * width)
    """

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x.view(x.size(0), -1)


class AdaptiveAvgPool2D(nn.Module):
    """
    自适应平均池化层

    将特征图池化到指定大小

    参数：
        output_size: 输出大小 (height, width)
    """

    def __init__(self, output_size: Tuple[int, int] = (1, 1)):
        super().__init__()
        self.output_size = output_size

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.adaptive_avg_pool2d(x, self.output_size)

    def extra_repr(self) -> str:
        return f'output_size={self.output_size}'
