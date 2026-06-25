"""
Point Cloud Processing - 点云处理

实现 3D 点云处理，支持分类和分割
"""

__version__ = "1.0.0"

from .pointnet import PointNetClassifier, PointNetSegmentor
from .dataset import PointCloudDataset, generate_random_pointcloud, generate_segmentation_data
from .trainer import PointCloudTrainer
from .visualization import PointCloudVisualizer
from .utils import normalize_pointcloud, farthest_point_sample

__all__ = [
    "PointNetClassifier",
    "PointNetSegmentor",
    "PointCloudDataset",
    "generate_random_pointcloud",
    "generate_segmentation_data",
    "PointCloudTrainer",
    "PointCloudVisualizer",
    "normalize_pointcloud",
    "farthest_point_sample",
]
