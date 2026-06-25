"""
简单 3D 场景 (Simple Scene)
===========================

为了验证 NeRF 实现，我们需要一个简单的3D场景。
这里实现几个基础几何体:

1. 球体 (Sphere): 最简单的3D形状
2. 立方体 (Cube): 轴对齐的立方体
3. 圆环 (Torus): 更复杂的形状

这些场景用于:
- 验证光线-物体相交
- 测试体渲染是否正确
- 作为 NeRF 训练的 ground truth

在实际应用中，场景来自:
- 多视角照片（Structure from Motion）
- 合成数据集（Blender 渲染）
- 深度传感器（RGB-D）
"""

import torch
import numpy as np
from typing import Tuple, Optional


class SimpleScene:
    """
    简单3D场景基类

    提供场景的几何和外观信息，用于生成训练数据。
    """

    def __init__(self):
        pass

    def query(
        self,
        points: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        查询3D点的颜色和密度

        参数:
            points: 3D点坐标 (..., 3)

        返回:
            colors: RGB颜色 (..., 3)
            densities: 体积密度 (..., 1)
        """
        raise NotImplementedError

    def render_rays(
        self,
        rays_o: torch.Tensor,
        rays_d: torch.Tensor,
        near: float,
        far: float,
        num_samples: int,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        渲染光线（用于生成 ground truth）

        参数:
            rays_o: 光线原点 (num_rays, 3)
            rays_d: 光线方向 (num_rays, 3)
            near: 近裁剪面
            far: 远裁剪面
            num_samples: 采样点数

        返回:
            colors: 像素颜色 (num_rays, 3)
            distances: 沿光线的距离 (num_rays, num_samples)
        """
        from .ray_utils import sample_points_along_rays
        from .volume_renderer import VolumeRenderer

        # 采样点
        points, distances = sample_points_along_rays(
            rays_o, rays_d, near, far, num_samples, perturb=False
        )

        # 查询颜色和密度
        colors, densities = self.query(points)

        # 体渲染
        renderer = VolumeRenderer()
        pixel_colors, _, _ = renderer(colors, densities, distances, rays_d)

        return pixel_colors, distances


class SphereScene(SimpleScene):
    """
    球体场景

    一个位于原点的球体，可以指定:
    - 半径
    - 颜色
    - 密度

    参数:
        radius: 球体半径
        color: 球体颜色 (3,)
        density: 体积密度
        center: 球心位置
    """

    def __init__(
        self,
        radius: float = 1.0,
        color: Tuple[float, float, float] = (1.0, 0.0, 0.0),
        density: float = 10.0,
        center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        super().__init__()
        self.radius = radius
        self.color = torch.tensor(color, dtype=torch.float32)
        self.density = density
        self.center = torch.tensor(center, dtype=torch.float32)

    def query(
        self,
        points: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        查询点是否在球体内

        如果点在球体内，返回颜色和密度；
        否则返回黑色和零密度。
        """
        # 计算点到球心的距离
        dist = torch.norm(points - self.center, dim=-1)

        # 判断是否在球体内
        inside = dist < self.radius

        # 颜色
        colors = self.color.expand_as(points).clone()
        colors[~inside] = 0.0

        # 密度
        densities = torch.full(
            (*points.shape[:-1], 1),
            self.density,
            device=points.device,
        )
        densities[~inside] = 0.0

        return colors, densities


class CubeScene(SimpleScene):
    """
    立方体场景

    一个轴对齐的立方体，可以指定:
    - 大小
    - 颜色
    - 位置

    参数:
        size: 立方体半边长
        color: 颜色 (3,)
        density: 体积密度
        center: 中心位置
    """

    def __init__(
        self,
        size: float = 1.0,
        color: Tuple[float, float, float] = (0.0, 1.0, 0.0),
        density: float = 10.0,
        center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        super().__init__()
        self.size = size
        self.color = torch.tensor(color, dtype=torch.float32)
        self.density = density
        self.center = torch.tensor(center, dtype=torch.float32)

    def query(
        self,
        points: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        查询点是否在立方体内
        """
        # 计算点相对于中心的坐标
        rel = points - self.center

        # 判断是否在立方体内
        inside = (
            (rel[..., 0].abs() < self.size)
            & (rel[..., 1].abs() < self.size)
            & (rel[..., 2].abs() < self.size)
        )

        # 颜色
        colors = self.color.expand_as(points).clone()
        colors[~inside] = 0.0

        # 密度
        densities = torch.full(
            (*points.shape[:-1], 1),
            self.density,
            device=points.device,
        )
        densities[~inside] = 0.0

        return colors, densities


class ColorfulSphereScene(SimpleScene):
    """
    彩虹球体场景

    一个颜色随位置变化的球体，用于测试视角无关的颜色学习。

    参数:
        radius: 球体半径
        density: 体积密度
    """

    def __init__(
        self,
        radius: float = 1.0,
        density: float = 10.0,
    ):
        super().__init__()
        self.radius = radius
        self.density = density

    def query(
        self,
        points: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        颜色根据位置变化
        """
        dist = torch.norm(points, dim=-1)
        inside = dist < self.radius

        # 颜色根据归一化坐标变化
        normalized = (points / self.radius + 1.0) / 2.0  # [0, 1]
        colors = normalized.clone()
        colors[~inside] = 0.0

        # 密度
        densities = torch.full(
            (*points.shape[:-1], 1),
            self.density,
            device=points.device,
        )
        densities[~inside] = 0.0

        return colors, densities


class MultiObjectScene(SimpleScene):
    """
    多物体场景

    包含多个简单几何体，用于测试 NeRF 学习复杂场景的能力。

    参数:
        objects: 物体列表
    """

    def __init__(self, objects: list = None):
        super().__init__()
        if objects is None:
            # 默认场景: 一个球和一个立方体
            self.objects = [
                SphereScene(
                    radius=0.8,
                    color=(1.0, 0.0, 0.0),
                    center=(0.0, 0.0, 0.0),
                ),
                CubeScene(
                    size=0.5,
                    color=(0.0, 1.0, 0.0),
                    center=(1.5, 0.0, 0.0),
                ),
            ]
        else:
            self.objects = objects

    def query(
        self,
        points: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        查询多个物体的组合颜色和密度

        使用最大密度优先策略
        """
        all_colors = []
        all_densities = []

        for obj in self.objects:
            colors, densities = obj.query(points)
            all_colors.append(colors)
            all_densities.append(densities)

        # 堆叠所有物体
        all_colors = torch.stack(all_colors, dim=0)      # (num_objects, ..., 3)
        all_densities = torch.stack(all_densities, dim=0) # (num_objects, ..., 1)

        # 选择密度最大的物体
        max_idx = all_densities.argmax(dim=0)  # (..., 1)
        max_idx_expand = max_idx.unsqueeze(-1).expand_as(all_colors)

        colors = torch.gather(all_colors, 0, max_idx_expand).squeeze(0)
        densities = torch.gather(all_densities, 0, max_idx).squeeze(0)

        return colors, densities


def create_synthetic_dataset(
    scene: SimpleScene,
    num_views: int = 100,
    height: int = 100,
    width: int = 100,
    focal_length: float = 50.0,
    near: float = 0.1,
    far: float = 10.0,
    num_samples: int = 64,
    device: str = "cpu",
) -> dict:
    """
    创建合成数据集

    从多个视角渲染场景，生成训练数据。

    参数:
        scene: 3D场景
        num_views: 视角数量
        height: 图像高度
        width: 图像宽度
        focal_length: 焦距
        near: 近裁剪面
        far: 远裁剪面
        num_samples: 每条光线的采样点数
        device: 计算设备

    返回:
        dataset: 包含图像、光线、相机参数的字典
    """
    from .ray_utils import RayGenerator

    generator = RayGenerator(height, width, focal_length, near, far)

    all_images = []
    all_rays_o = []
    all_rays_d = []

    # 生成不同视角
    for i in range(num_views):
        # 均匀分布在球面上
        azimuth = 2 * np.pi * i / num_views
        elevation = np.pi / 4  # 固定仰角

        # 生成相机位姿
        c2w = generator.generate_camera_pose(azimuth, elevation, radius=4.0)

        # 生成光线
        rays_o, rays_d = generator.get_rays(c2w)

        # 渲染
        rays_o_flat = rays_o.reshape(-1, 3)
        rays_d_flat = rays_d.reshape(-1, 3)

        colors, _ = scene.render_rays(rays_o_flat, rays_d_flat, near, far, num_samples)

        # 重塑为图像
        image = colors.reshape(height, width, 3)

        all_images.append(image)
        all_rays_o.append(rays_o)
        all_rays_d.append(rays_d)

    dataset = {
        "images": torch.stack(all_images),
        "rays_o": torch.stack(all_rays_o),
        "rays_d": torch.stack(all_rays_d),
        "height": height,
        "width": width,
        "focal_length": focal_length,
        "near": near,
        "far": far,
    }

    return dataset
