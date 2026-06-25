"""
位置编码 (Positional Encoding)
=============================

NeRF 的核心创新之一是使用位置编码将低维坐标映射到高维空间。
这使得 MLP 能够学习高频细节（如纹理、边缘）。

数学公式:
γ(p) = (sin(2^0 π p), cos(2^0 π p), ..., sin(2^(L-1) π p), cos(2^(L-1) π p))

其中:
- p: 输入坐标（可以是位置 x,y,z 或方向 θ,φ）
- L: 编码的频率层数
- 每层频率翻倍，从 2^0 到 2^(L-1)

为什么需要位置编码?
- MLP 倾向于学习低频函数（平滑函数）
- 3D 场景包含高频细节（纹理、边缘、细节）
- 位置编码将高频信息显式编码到输入中
- 让 MLP 能够拟合高频函数
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Optional


class PositionalEncoding(nn.Module):
    """
    位置编码层

    将输入坐标编码为高维特征，使用正弦和余弦函数。

    参数:
        input_dim: 输入维度（3 表示 xyz，2 表示方向）
        num_freqs: 频率层数 L
        include_input: 是否在编码中包含原始输入
        log_sampling: 是否使用对数间隔频率（默认是）
    """

    def __init__(
        self,
        input_dim: int = 3,
        num_freqs: int = 10,
        include_input: bool = True,
        log_sampling: bool = True,
    ):
        super().__init__()

        self.input_dim = input_dim
        self.num_freqs = num_freqs
        self.include_input = include_input
        self.log_sampling = log_sampling

        # 计算频率 bands
        if log_sampling:
            # 对数间隔: 2^0, 2^1, ..., 2^(L-1)
            freq_bands = 2.0 ** torch.linspace(0.0, num_freqs - 1, num_freqs)
        else:
            # 线性间隔
            freq_bands = torch.linspace(1.0, 2.0 ** (num_freqs - 1), num_freqs)

        self.register_buffer("freq_bands", freq_bands)

        # 计算输出维度
        # 每个频率层产生 2 * input_dim 个特征 (sin 和 cos)
        # 如果 include_input，再加 input_dim
        self.output_dim = num_freqs * 2 * input_dim
        if include_input:
            self.output_dim += input_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        对输入进行位置编码

        参数:
            x: 输入张量，形状 (..., input_dim)

        返回:
            编码后的张量，形状 (..., output_dim)
        """
        # x: (..., input_dim)
        encoded_parts = []

        # 包含原始输入
        if self.include_input:
            encoded_parts.append(x)

        # 对每个频率进行编码
        for freq in self.freq_bands:
            # sin(2^k * π * x)
            encoded_parts.append(torch.sin(freq * np.pi * x))
            # cos(2^k * π * x)
            encoded_parts.append(torch.cos(freq * np.pi * x))

        # 拼接所有编码
        return torch.cat(encoded_parts, dim=-1)


class IntegratedPositionalEncoding(nn.Module):
    """
    积分位置编码 (用于 Mip-NeRF)

    与标准位置编码不同，它对一个区间进行积分，
    而不是只对单个点编码。这有助于减少锯齿伪影。

    参数:
        input_dim: 输入维度
        num_freqs: 频率层数
        include_input: 是否包含原始输入
    """

    def __init__(
        self,
        input_dim: int = 3,
        num_freqs: int = 10,
        include_input: bool = True,
    ):
        super().__init__()

        self.input_dim = input_dim
        self.num_freqs = num_freqs
        self.include_input = include_input

        freq_bands = 2.0 ** torch.linspace(0.0, num_freqs - 1, num_freqs)
        self.register_buffer("freq_bands", freq_bands)

        self.output_dim = num_freqs * 2 * input_dim
        if include_input:
            self.output_dim += input_dim

    def forward(
        self,
        x: torch.Tensor,
        variance: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        积分位置编码

        参数:
            x: 中心点坐标 (..., input_dim)
            variance: 每个点的方差 (..., input_dim)
                      如果为 None，退化为标准位置编码

        返回:
            编码后的张量 (..., output_dim)
        """
        encoded_parts = []

        if self.include_input:
            encoded_parts.append(x)

        for freq in self.freq_bands:
            if variance is None:
                # 标准编码
                encoded_parts.append(torch.sin(freq * np.pi * x))
                encoded_parts.append(torch.cos(freq * np.pi * x))
            else:
                # 积分编码：考虑区间的影响
                # 使用高斯积分公式
                # E[sin(wx)] ≈ sin(wx) * exp(-0.5 * w^2 * var)
                scale = torch.exp(-0.5 * (freq * np.pi) ** 2 * variance)
                encoded_parts.append(torch.sin(freq * np.pi * x) * scale)
                encoded_parts.append(torch.cos(freq * np.pi * x) * scale)

        return torch.cat(encoded_parts, dim=-1)
