"""
NeRF 神经辐射场实现
==================

实现神经辐射场(Neural Radiance Fields)用于3D场景重建。

核心组件:
- Positional Encoding: 位置编码，将低维坐标映射到高维空间
- NeRF Model: 多层感知机，预测颜色和密度
- Volume Renderer: 体渲染，将3D信息合成2D图像
- Ray Utilities: 相机光线生成和采样

核心流程:
相机光线 → 采样点 → 位置编码 → MLP → 颜色/密度 → 体渲染 → 图像
"""

from .positional_encoding import PositionalEncoding
from .nerf_model import NeRFModel
from .volume_renderer import VolumeRenderer
from .ray_utils import RayGenerator, sample_points_along_rays
from .scene import SimpleScene, SphereScene, CubeScene, ColorfulSphereScene, MultiObjectScene
from .trainer import NeRFTrainer

__all__ = [
    "PositionalEncoding",
    "NeRFModel",
    "VolumeRenderer",
    "RayGenerator",
    "sample_points_along_rays",
    "SimpleScene",
    "SphereScene",
    "CubeScene",
    "ColorfulSphereScene",
    "MultiObjectScene",
    "NeRFTrainer",
]
