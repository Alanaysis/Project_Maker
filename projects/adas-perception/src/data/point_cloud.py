"""
点云处理模块

提供点云的基本操作，包括加载、保存、滤波、降采样等。
"""

import numpy as np
from typing import Tuple, Optional

# 可选导入 open3d
try:
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False
    print("警告: open3d 未安装，部分功能将不可用")


class PointCloud:
    """
    点云数据类，封装点云的基本操作。

    Attributes:
        points: (N, C) 数组，C 通常是 4 (x, y, z, intensity)
    """

    def __init__(self, points: np.ndarray):
        """
        初始化点云。

        Args:
            points: (N, C) 数组，C 通常是 4 (x, y, z, intensity)

        Raises:
            ValueError: 如果点云维度不正确
        """
        if points.ndim != 2:
            raise ValueError(f"点云必须是 2D 数组，当前维度: {points.ndim}")

        self.points = points.astype(np.float32)

    @property
    def num_points(self) -> int:
        """点云数量"""
        return self.points.shape[0]

    @property
    def num_features(self) -> int:
        """特征维度"""
        return self.points.shape[1]

    def filter_by_range(
        self,
        x_range: Tuple[float, float],
        y_range: Tuple[float, float],
        z_range: Tuple[float, float]
    ) -> 'PointCloud':
        """
        按范围过滤点云。

        Args:
            x_range: (min, max) X 轴范围
            y_range: (min, max) Y 轴范围
            z_range: (min, max) Z 轴范围

        Returns:
            过滤后的点云
        """
        mask = (
            (self.points[:, 0] >= x_range[0]) &
            (self.points[:, 0] <= x_range[1]) &
            (self.points[:, 1] >= y_range[0]) &
            (self.points[:, 1] <= y_range[1]) &
            (self.points[:, 2] >= z_range[0]) &
            (self.points[:, 2] <= z_range[1])
        )

        return PointCloud(self.points[mask])

    def downsample(self, voxel_size: float) -> 'PointCloud':
        """
        体素降采样。

        Args:
            voxel_size: 体素大小

        Returns:
            降采样后的点云
        """
        # 计算体素坐标
        voxel_coords = np.floor(self.points[:, :3] / voxel_size).astype(int)

        # 找到唯一的体素
        unique_voxels, indices = np.unique(voxel_coords, axis=0, return_index=True)

        # 取每个体素的中心点
        downsampled_points = self.points[indices]

        return PointCloud(downsampled_points)

    def remove_ground(self, height_threshold: float = -1.5) -> 'PointCloud':
        """
        去除地面点。

        Args:
            height_threshold: 高度阈值，低于此值的点被认为是地面点

        Returns:
            去除地面点后的点云
        """
        mask = self.points[:, 2] > height_threshold
        return PointCloud(self.points[mask])

    def remove_outliers(
        self,
        nb_neighbors: int = 20,
        std_ratio: float = 2.0
    ) -> 'PointCloud':
        """
        去除离群点。

        Args:
            nb_neighbors: 邻域点数
            std_ratio: 标准差倍数

        Returns:
            去除离群点后的点云
        """
        if not HAS_OPEN3D:
            raise ImportError("open3d 未安装，无法使用此功能")

        # 转换为 Open3D 点云
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(self.points[:, :3])

        # 去除离群点
        cl, ind = pcd.remove_statistical_outlier(nb_neighbors, std_ratio)

        # 提取内点
        inlier_points = self.points[ind]

        return PointCloud(inlier_points)

    def to_open3d(self):
        """
        转换为 Open3D 点云。

        Returns:
            Open3D 点云对象
        """
        if not HAS_OPEN3D:
            raise ImportError("open3d 未安装，无法使用此功能")

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(self.points[:, :3])

        # 如果有颜色信息
        if self.points.shape[1] >= 6:
            pcd.colors = o3d.utility.Vector3dVector(self.points[:, 3:6])

        return pcd

    @classmethod
    def from_open3d(cls, pcd) -> 'PointCloud':
        """
        从 Open3D 点云创建。

        Args:
            pcd: Open3D 点云对象

        Returns:
            点云对象
        """
        points = np.asarray(pcd.points)

        # 如果有颜色信息
        if pcd.has_colors():
            colors = np.asarray(pcd.colors)
            points = np.hstack([points, colors])

        return cls(points)

    @classmethod
    def load_from_bin(cls, file_path: str) -> 'PointCloud':
        """
        从二进制文件加载点云 (KITTI 格式)。

        Args:
            file_path: 文件路径

        Returns:
            点云对象
        """
        points = np.fromfile(file_path, dtype=np.float32)
        points = points.reshape(-1, 4)

        return cls(points)

    def save_to_bin(self, file_path: str) -> None:
        """
        保存为二进制文件。

        Args:
            file_path: 文件路径
        """
        self.points.tofile(file_path)

    @classmethod
    def load_from_pcd(cls, file_path: str) -> 'PointCloud':
        """
        从 PCD 文件加载点云。

        Args:
            file_path: 文件路径

        Returns:
            点云对象
        """
        if not HAS_OPEN3D:
            raise ImportError("open3d 未安装，无法使用此功能")

        pcd = o3d.io.read_point_cloud(file_path)
        return cls.from_open3d(pcd)

    def save_to_pcd(self, file_path: str) -> None:
        """
        保存为 PCD 文件。

        Args:
            file_path: 文件路径
        """
        if not HAS_OPEN3D:
            raise ImportError("open3d 未安装，无法使用此功能")

        pcd = self.to_open3d()
        o3d.io.write_point_cloud(file_path, pcd)

    @classmethod
    def load_from_ply(cls, file_path: str) -> 'PointCloud':
        """
        从 PLY 文件加载点云。

        Args:
            file_path: 文件路径

        Returns:
            点云对象
        """
        if not HAS_OPEN3D:
            raise ImportError("open3d 未安装，无法使用此功能")

        pcd = o3d.io.read_point_cloud(file_path)
        return cls.from_open3d(pcd)

    def save_to_ply(self, file_path: str) -> None:
        """
        保存为 PLY 文件。

        Args:
            file_path: 文件路径
        """
        if not HAS_OPEN3D:
            raise ImportError("open3d 未安装，无法使用此功能")

        pcd = self.to_open3d()
        o3d.io.write_point_cloud(file_path, pcd)

    def get_bounding_box(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取点云的边界框。

        Returns:
            (min_point, max_point): 最小点和最大点
        """
        min_point = self.points[:, :3].min(axis=0)
        max_point = self.points[:, :3].max(axis=0)

        return min_point, max_point

    def get_centroid(self) -> np.ndarray:
        """
        获取点云的质心。

        Returns:
            质心坐标
        """
        return self.points[:, :3].mean(axis=0)

    def translate(self, translation: np.ndarray) -> 'PointCloud':
        """
        平移点云。

        Args:
            translation: 平移向量

        Returns:
            平移后的点云
        """
        new_points = self.points.copy()
        new_points[:, :3] += translation

        return PointCloud(new_points)

    def rotate(self, rotation_matrix: np.ndarray) -> 'PointCloud':
        """
        旋转点云。

        Args:
            rotation_matrix: (3, 3) 旋转矩阵

        Returns:
            旋转后的点云
        """
        new_points = self.points.copy()
        new_points[:, :3] = new_points[:, :3] @ rotation_matrix.T

        return PointCloud(new_points)

    def scale(self, scale_factor: float) -> 'PointCloud':
        """
        缩放点云。

        Args:
            scale_factor: 缩放因子

        Returns:
            缩放后的点云
        """
        new_points = self.points.copy()
        new_points[:, :3] *= scale_factor

        return PointCloud(new_points)

    def __len__(self) -> int:
        """点云数量"""
        return self.num_points

    def __repr__(self) -> str:
        """字符串表示"""
        return f"PointCloud(num_points={self.num_points}, num_features={self.num_features})"
