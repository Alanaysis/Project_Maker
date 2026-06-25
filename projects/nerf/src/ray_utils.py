"""
光线工具 (Ray Utilities)
========================

NeRF 使用相机光线将3D场景投影到2D图像。

核心概念:
1. 相机模型: 使用针孔相机模型
2. 光线生成: 从相机位置穿过每个像素
3. 采样策略: 在光线上采样3D点

相机坐标系:
- 相机位于原点，看向 -z 方向
- x 轴向右，y 轴向上
- 图像平面在 z = -f 处

光线表示:
r(t) = o + t * d
- o: 光线原点（相机位置）
- d: 光线方向（归一化）
- t: 参数，表示沿光线的距离

采样策略:
1. 均匀采样: 在 [near, far] 区间均匀采样
2. 分层采样: 将区间分成 N 份，在每份中随机采样
3. 重要性采样: 根据密度分布调整采样点（高级）
"""

import torch
import numpy as np
from typing import Tuple, Optional


class RayGenerator:
    """
    相机光线生成器

    从相机参数生成穿过每个像素的光线。

    参数:
        height: 图像高度
        width: 图像宽度
        focal_length: 焦距（像素单位）
        near: 近裁剪面距离
        far: 远裁剪面距离
    """

    def __init__(
        self,
        height: int,
        width: int,
        focal_length: float,
        near: float = 2.0,
        far: float = 6.0,
    ):
        self.height = height
        self.width = width
        self.focal_length = focal_length
        self.near = near
        self.far = far

        # 生成像素坐标网格
        # (i, j) 表示像素中心坐标
        i, j = torch.meshgrid(
            torch.arange(width, dtype=torch.float32),
            torch.arange(height, dtype=torch.float32),
            indexing="ij",
        )

        # 转换为归一化设备坐标 (NDC)
        # 相机看向 -z 方向
        # x = (i - width/2) / focal_length
        # y = -(j - height/2) / focal_length
        # z = -1
        directions = torch.stack([
            (i - width * 0.5) / focal_length,
            -(j - height * 0.5) / focal_length,
            -torch.ones_like(i),
        ], dim=-1)

        # 存储原始方向（用于后续变换）
        self.directions = directions
        self.pixel_coords = (i, j)

    def get_rays(
        self,
        camera_to_world: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        生成世界坐标系下的光线

        参数:
            camera_to_world: 相机到世界坐标的变换矩阵 (4, 4)
                             [R | t]
                             [0 | 1]

        返回:
            rays_o: 光线原点 (height, width, 3)
            rays_d: 光线方向 (height, width, 3)
        """
        # 获取旋转矩阵和平移向量
        R = camera_to_world[:3, :3]  # (3, 3)
        t = camera_to_world[:3, 3]   # (3,)

        # 将方向转换到世界坐标系
        # directions: (height, width, 3)
        # 确保 directions 在同一设备上
        directions = self.directions.to(camera_to_world.device)
        rays_d = torch.matmul(
            directions.reshape(-1, 3),
            R.T,
        ).reshape(directions.shape)

        # 归一化方向
        rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)

        # 光线原点就是相机位置
        rays_o = t.expand_as(rays_d)

        return rays_o, rays_d

    def get_rays_simple(
        self,
        camera_pos: torch.Tensor = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        简化版本：假设相机在原点，看向 -z 方向

        参数:
            camera_pos: 相机位置，默认原点

        返回:
            rays_o: 光线原点 (height, width, 3)
            rays_d: 光线方向 (height, width, 3)
        """
        if camera_pos is None:
            camera_pos = torch.zeros(3)

        rays_o = camera_pos.expand_as(self.directions).clone()
        rays_d = self.directions.clone()

        # 归一化
        rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)

        return rays_o, rays_d

    def generate_camera_pose(
        self,
        azimuth: float,
        elevation: float,
        radius: float = 4.0,
        target: torch.Tensor = None,
    ) -> torch.Tensor:
        """
        生成相机位姿矩阵

        参数:
            azimuth: 方位角（弧度）
            elevation: 仰角（弧度）
            radius: 相机到目标的距离
            target: 目标点位置，默认原点

        返回:
            c2w: 相机到世界坐标的变换矩阵 (4, 4)
        """
        if target is None:
            target = torch.zeros(3, dtype=torch.float32)

        # 计算相机位置
        # 球坐标转笛卡尔坐标
        camera_pos = torch.tensor([
            radius * np.cos(elevation) * np.sin(azimuth),
            radius * np.sin(elevation),
            radius * np.cos(elevation) * np.cos(azimuth),
        ], dtype=torch.float32)

        # 计算相机朝向
        # 相机看向目标点
        forward = target - camera_pos
        forward = forward / torch.norm(forward)

        # 上方向
        up = torch.tensor([0.0, 1.0, 0.0], dtype=torch.float32)

        # 右方向
        right = torch.linalg.cross(forward, up)
        right = right / torch.norm(right)

        # 重新计算上方向（确保正交）
        up = torch.linalg.cross(right, forward)

        # 构建变换矩阵
        c2w = torch.eye(4)
        c2w[:3, 0] = right
        c2w[:3, 1] = up
        c2w[:3, 2] = -forward  # 相机看向 -z
        c2w[:3, 3] = camera_pos

        return c2w


def sample_points_along_rays(
    rays_o: torch.Tensor,
    rays_d: torch.Tensor,
    near: float,
    far: float,
    num_samples: int,
    perturb: bool = True,
    lindisp: bool = False,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    沿光线采样3D点

    参数:
        rays_o: 光线原点 (num_rays, 3)
        rays_d: 光线方向 (num_rays, 3)
        near: 近裁剪面距离
        far: 远裁剪面距离
        num_samples: 每条光线的采样点数
        perturb: 是否添加随机扰动（训练时使用）
        lindisp: 是否在视差空间采样（近处采样更密集）

    返回:
        points: 采样点坐标 (num_rays, num_samples, 3)
        distances: 沿光线的距离 (num_rays, num_samples)
    """
    num_rays = rays_o.shape[0]
    device = rays_o.device

    # 生成采样距离
    t = torch.linspace(near, far, num_samples, device=device)
    t = t.expand(num_rays, num_samples)  # (num_rays, num_samples)

    if lindisp:
        # 在视差空间采样: 近处更密集
        # t' = 1 / (1/t_near + (1/t_far - 1/t_near) * u)
        t = 1.0 / (
            1.0 / near
            + (1.0 / far - 1.0 / near)
            * torch.linspace(0.0, 1.0, num_samples, device=device)
        )
        t = t.expand(num_rays, num_samples)

    # 添加随机扰动（分层采样）
    if perturb:
        # 计算相邻采样点的间距
        midpoints = 0.5 * (t[:, :-1] + t[:, 1:])
        upper = torch.cat([midpoints, t[:, -1:]], dim=-1)
        lower = torch.cat([t[:, :1], midpoints], dim=-1)
        # 在每个区间内随机采样
        random_offsets = torch.rand_like(t)
        t = lower + (upper - lower) * random_offsets

    # 计算3D点坐标: r(t) = o + t * d
    # rays_o: (num_rays, 3) -> (num_rays, 1, 3)
    # rays_d: (num_rays, 3) -> (num_rays, 1, 3)
    # t: (num_rays, num_samples) -> (num_rays, num_samples, 1)
    points = (
        rays_o.unsqueeze(1) + t.unsqueeze(-1) * rays_d.unsqueeze(1)
    )  # (num_rays, num_samples, 3)

    return points, t


def sample_pdf(
    bins: torch.Tensor,
    weights: torch.Tensor,
    num_samples: int,
    perturb: bool = True,
) -> torch.Tensor:
    """
    根据权重分布进行重要性采样

    这是 NeRF 的第二阶段采样策略:
    1. 先均匀采样粗略点
    2. 根据粗略网络的权重，在高权重区域密集采样

    参数:
        bins: 采样区间边界 (num_rays, num_bins)
        weights: 权重分布 (num_rays, num_bins)
        num_samples: 采样点数
        perturb: 是否添加随机扰动

    返回:
        samples: 采样点距离 (num_rays, num_samples)
    """
    device = bins.device
    num_rays = bins.shape[0]

    # 归一化权重
    weights = weights + 1e-5  # 避免 0 权重
    pdf = weights / weights.sum(dim=-1, keepdim=True)
    cdf = torch.cumsum(pdf, dim=-1)
    cdf = torch.cat([torch.zeros_like(cdf[:, :1]), cdf], dim=-1)

    # 生成均匀分布的采样点
    if perturb:
        u = torch.rand(num_rays, num_samples, device=device)
    else:
        u = torch.linspace(0.0, 1.0, num_samples, device=device)
        u = u.expand(num_rays, num_samples)

    # 反变换采样
    # 找到 u 对应的区间
    indices = torch.searchsorted(cdf, u, right=True)
    below = (indices - 1).clamp(min=0)
    above = indices.clamp(max=cdf.shape[-1] - 1)

    # 线性插值
    cdf_below = torch.gather(cdf, 1, below)
    cdf_above = torch.gather(cdf, 1, above)
    bins_below = torch.gather(bins, 1, below)
    bins_above = torch.gather(bins, 1, above)

    # 插值权重
    denom = cdf_above - cdf_below
    denom = torch.where(denom < 1e-5, torch.ones_like(denom), denom)
    t = (u - cdf_below) / denom
    samples = bins_below + t * (bins_above - bins_below)

    return samples
