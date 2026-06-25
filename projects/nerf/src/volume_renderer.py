"""
体渲染 (Volume Rendering)
==========================

体渲染是将3D体积数据转换为2D图像的技术。
在 NeRF 中，它将沿光线采样的颜色和密度合成为最终像素颜色。

物理原理:
光线穿过参与介质（如烟雾、云、体积）时，会发生:
1. 吸收 (Absorption): 光被介质吸收
2. 发射 (Emission): 介质自身发光
3. 散射 (Scattering): 光改变方向

数学公式:
NeRF 使用离散体渲染方程:

C(r) = Σ T_i * α_i * c_i

其中:
- C(r): 光线 r 的最终颜色
- T_i = exp(-Σ_{j<i} σ_j * δ_j): 累积透射率
- α_i = 1 - exp(-σ_i * δ_i): alpha 不透明度
- σ_i: 第 i 个采样点的体积密度
- δ_i: 相邻采样点之间的距离
- c_i: 第 i 个采样点的颜色

直觉理解:
- 如果 σ 很大，光线被阻挡，α 接近 1
- 如果 σ 很小，光线穿过，α 接近 0
- T_i 表示光线到达第 i 个点的概率
- 前面的点如果密度大，后面的点贡献小
"""

import torch
import torch.nn as nn
from typing import Tuple, Optional


class VolumeRenderer(nn.Module):
    """
    体渲染器

    将沿光线采样的颜色和密度合成为最终像素颜色。

    参数:
        background_color: 背景颜色，默认白色 (1,1,1)
                          对于透明区域使用背景颜色填充
        white_background: 是否使用白色背景（合成数据常用）
    """

    def __init__(
        self,
        background_color: Optional[torch.Tensor] = None,
        white_background: bool = True,
    ):
        super().__init__()

        if background_color is not None:
            self.register_buffer("background_color", background_color)
        elif white_background:
            self.register_buffer(
                "background_color", torch.tensor([1.0, 1.0, 1.0])
            )
        else:
            self.register_buffer(
                "background_color", torch.tensor([0.0, 0.0, 0.0])
            )

    def forward(
        self,
        colors: torch.Tensor,
        densities: torch.Tensor,
        distances: torch.Tensor,
        rays_d: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, dict]:
        """
        体渲染前向传播

        参数:
            colors: 采样点颜色 (num_rays, num_samples, 3)
            densities: 采样点密度 (num_rays, num_samples, 1)
            distances: 相邻采样点距离 (num_rays, num_samples)
            rays_d: 光线方向 (num_rays, 3)，用于计算距离

        返回:
            pixel_colors: 最终像素颜色 (num_rays, 3)
            depth_map: 深度图 (num_rays, 1)
            extras: 额外信息（alpha, transmittance 等）
        """
        # 计算相邻采样点之间的距离
        # distances: (num_rays, num_samples)
        # 相邻点距离
        deltas = distances[:, 1:] - distances[:, :-1]
        # 最后一个点使用一个大值
        last_delta = torch.full_like(deltas[:, :1], 1e10)
        deltas = torch.cat([deltas, last_delta], dim=-1)

        # 如果光线方向不是单位向量，需要缩放距离
        if rays_d is not None:
            deltas = deltas * torch.norm(rays_d, dim=-1, keepdim=True)

        # 计算 alpha 不透明度
        # α_i = 1 - exp(-σ_i * δ_i)
        densities = densities.squeeze(-1)  # (num_rays, num_samples)
        alpha = 1.0 - torch.exp(-densities * deltas)

        # 计算累积透射率
        # T_i = exp(-Σ_{j<i} σ_j * δ_j)
        # 等价于 Π_{j<i} (1 - α_j)
        transmittance = torch.cumprod(
            torch.cat([
                torch.ones_like(alpha[:, :1]),  # T_0 = 1
                1.0 - alpha[:, :-1],
            ], dim=-1),
            dim=-1,
        )

        # 计算每个采样点的权重
        # w_i = T_i * α_i
        weights = transmittance * alpha

        # 合成最终颜色
        # C = Σ w_i * c_i
        pixel_colors = (weights.unsqueeze(-1) * colors).sum(dim=1)

        # 计算深度图
        # depth = Σ w_i * t_i
        depth_map = (weights * distances).sum(dim=1, keepdim=True)

        # 添加背景颜色
        # 如果总权重 < 1，说明光线穿过了场景，使用背景颜色填充
        acc_map = weights.sum(dim=-1, keepdim=True)
        pixel_colors = pixel_colors + (1.0 - acc_map) * self.background_color

        # 收集额外信息
        extras = {
            "weights": weights,
            "alpha": alpha,
            "transmittance": transmittance,
            "accumulation": acc_map,
        }

        return pixel_colors, depth_map, extras


class VolumeRendererWithEntropy(nn.Module):
    """
    带熵正则化的体渲染器

    除了基本的体渲染，还计算权重的熵，
    用于正则化训练，鼓励密度集中在表面附近。

    参数:
        background_color: 背景颜色
        entropy_weight: 熵损失权重
    """

    def __init__(
        self,
        background_color: Optional[torch.Tensor] = None,
        white_background: bool = True,
        entropy_weight: float = 1e-3,
    ):
        super().__init__()

        self.base_renderer = VolumeRenderer(background_color, white_background)
        self.entropy_weight = entropy_weight

    def forward(
        self,
        colors: torch.Tensor,
        densities: torch.Tensor,
        distances: torch.Tensor,
        rays_d: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, dict]:
        """
        带熵正则化的体渲染

        返回额外的 entropy_loss
        """
        pixel_colors, depth_map, extras = self.base_renderer(
            colors, densities, distances, rays_d
        )

        # 计算熵损失
        # H = -Σ w_i * log(w_i + ε)
        weights = extras["weights"]
        eps = 1e-10
        entropy = -torch.sum(weights * torch.log(weights + eps), dim=-1)
        extras["entropy_loss"] = entropy.mean() * self.entropy_weight

        return pixel_colors, depth_map, extras
