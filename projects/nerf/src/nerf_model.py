"""
NeRF 模型 (MLP)
===============

NeRF 使用多层感知机(MLP)来表示连续的3D场景。

输入: 位置坐标 (x,y,z) 和观察方向 (θ,φ)
输出: 颜色 (r,g,b) 和体积密度 (σ)

架构设计:
1. 位置编码后的坐标 → 8层全连接网络 → 密度 σ
2. 将中间特征与方向编码拼接 → 1层全连接网络 → 颜色 (r,g,b)

关键设计:
- 密度只依赖于位置，不依赖于观察方向
- 颜色依赖于位置和观察方向（实现视角相关效果）
- 使用 ReLU 激活函数
- 密度使用 Softplus 确保非负

参考论文:
- NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis (ECCV 2020)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple

from .positional_encoding import PositionalEncoding


class NeRFModel(nn.Module):
    """
    NeRF 核心模型

    参数:
        pos_encoding_dim: 位置编码后的维度（默认 63 = 3 + 10*2*3）
        dir_encoding_dim: 方向编码后的维度（默认 27 = 2 + 6*2*2）
        hidden_dim: 隐藏层维度（默认 256）
        num_layers: 主干网络层数（默认 8）
        skip_layer: 跳跃连接的位置（默认第4层后）
        use_viewdirs: 是否使用观察方向
    """

    def __init__(
        self,
        pos_encoding_dim: int = 63,
        dir_encoding_dim: int = 27,
        hidden_dim: int = 256,
        num_layers: int = 8,
        skip_layer: int = 4,
        use_viewdirs: bool = True,
    ):
        super().__init__()

        self.pos_encoding_dim = pos_encoding_dim
        self.dir_encoding_dim = dir_encoding_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.skip_layer = skip_layer
        self.use_viewdirs = use_viewdirs

        # ===== 主干网络 (处理位置) =====
        # 输入: 位置编码后的坐标
        # 输出: 密度 σ 和中间特征
        backbone_layers = []
        for i in range(num_layers):
            if i == 0:
                in_dim = pos_encoding_dim
            elif i == skip_layer:
                # 跳跃连接: 拼接原始输入
                in_dim = hidden_dim + pos_encoding_dim
            else:
                in_dim = hidden_dim
            backbone_layers.append(nn.Linear(in_dim, hidden_dim))

        self.backbone = nn.ModuleList(backbone_layers)

        # ===== 密度预测头 =====
        # 从中间特征预测密度
        self.density_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Softplus(),  # 确保密度非负
        )

        # ===== 颜色预测头 =====
        if use_viewdirs:
            # 颜色预测: 中间特征 + 方向编码 → RGB
            self.feature_layer = nn.Linear(hidden_dim, hidden_dim)
            self.color_head = nn.Sequential(
                nn.Linear(hidden_dim + dir_encoding_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, 3),
                nn.Sigmoid(),  # RGB 范围 [0, 1]
            )
        else:
            # 不使用方向: 直接从特征预测颜色
            self.color_head = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, 3),
                nn.Sigmoid(),
            )

    def forward(
        self,
        positions: torch.Tensor,
        directions: torch.Tensor = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        前向传播

        参数:
            positions: 位置坐标，已编码 (batch, pos_encoding_dim)
            directions: 观察方向，已编码 (batch, dir_encoding_dim)
                        如果 use_viewdirs=False，可以为 None

        返回:
            density: 体积密度 (batch, 1)
            color: RGB 颜色 (batch, 3)
        """
        # ===== 主干网络 =====
        h = positions
        for i, layer in enumerate(self.backbone):
            if i == self.skip_layer:
                # 跳跃连接
                h = torch.cat([h, positions], dim=-1)
            h = layer(h)
            h = F.relu(h)

        # ===== 密度预测 =====
        density = self.density_head(h)

        # ===== 颜色预测 =====
        if self.use_viewdirs and directions is not None:
            feature = self.feature_layer(h)
            color_input = torch.cat([feature, directions], dim=-1)
            color = self.color_head(color_input)
        else:
            color = self.color_head(h)

        return density, color


class TinyNeRF(nn.Module):
    """
    轻量级 NeRF 模型，用于快速实验

    简化版本:
    - 更少的层数 (4层)
    - 更小的隐藏维度 (128)
    - 无跳跃连接
    - 无方向依赖

    适用于:
    - 简单几何体
    - 快速原型验证
    - 学习理解
    """

    def __init__(
        self,
        pos_encoding_dim: int = 63,
        hidden_dim: int = 128,
        num_layers: int = 4,
    ):
        super().__init__()

        self.pos_encoding_dim = pos_encoding_dim
        self.hidden_dim = hidden_dim

        # 主干网络
        layers = [nn.Linear(pos_encoding_dim, hidden_dim), nn.ReLU()]
        for _ in range(num_layers - 1):
            layers.extend([nn.Linear(hidden_dim, hidden_dim), nn.ReLU()])
        self.backbone = nn.Sequential(*layers)

        # 输出头
        self.density_head = nn.Sequential(
            nn.Linear(hidden_dim, 1),
            nn.Softplus(),
        )

        self.color_head = nn.Sequential(
            nn.Linear(hidden_dim, 3),
            nn.Sigmoid(),
        )

    def forward(
        self,
        positions: torch.Tensor,
        directions: torch.Tensor = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        前向传播

        参数:
            positions: 位置编码后的坐标 (batch, pos_encoding_dim)
            directions: 未使用，保持接口一致

        返回:
            density: 体积密度 (batch, 1)
            color: RGB 颜色 (batch, 3)
        """
        features = self.backbone(positions)
        density = self.density_head(features)
        color = self.color_head(features)
        return density, color
