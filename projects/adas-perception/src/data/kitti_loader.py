"""
KITTI 数据集加载器

提供 KITTI 数据集的加载和处理功能。
"""

import os
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from .point_cloud import PointCloud


class KITTILoader:
    """
    KITTI 数据集加载器。

    Attributes:
        root_dir: KITTI 数据集根目录
        split: 数据集划分 ('training' 或 'testing')
    """

    # KITTI 类别映射
    CLASS_MAP = {
        'Car': 0,
        'Pedestrian': 1,
        'Cyclist': 2,
        'Van': 3,
        'Truck': 4,
        'Tram': 5,
        'Misc': 6,
        'DontCare': 7
    }

    # 类别颜色映射
    CLASS_COLORS = {
        'Car': (0, 1, 0),        # 绿色
        'Pedestrian': (1, 0, 0), # 红色
        'Cyclist': (0, 0, 1),    # 蓝色
        'Van': (1, 1, 0),        # 黄色
        'Truck': (1, 0, 1),      # 紫色
        'Tram': (0, 1, 1),       # 青色
        'Misc': (0.5, 0.5, 0.5), # 灰色
        'DontCare': (0, 0, 0)    # 黑色
    }

    def __init__(self, root_dir: str, split: str = 'training'):
        """
        初始化 KITTI 数据加载器。

        Args:
            root_dir: KITTI 数据集根目录
            split: 数据集划分 ('training' 或 'testing')

        Raises:
            FileNotFoundError: 如果数据集目录不存在
        """
        self.root_dir = Path(root_dir)
        self.split = split

        # 验证目录存在
        if not self.root_dir.exists():
            raise FileNotFoundError(f"数据集目录不存在: {self.root_dir}")

        # 设置子目录
        self.split_dir = self.root_dir / split
        self.velodyne_dir = self.split_dir / 'velodyne'
        self.label_dir = self.split_dir / 'label_2'
        self.calib_dir = self.split_dir / 'calib'
        self.image_dir = self.split_dir / 'image_2'

        # 获取样本 ID 列表
        self.sample_ids = self._get_sample_ids()

    def _get_sample_ids(self) -> List[str]:
        """
        获取样本 ID 列表。

        Returns:
            样本 ID 列表
        """
        if not self.velodyne_dir.exists():
            return []

        # 获取所有点云文件
        velodyne_files = sorted(self.velodyne_dir.glob('*.bin'))

        # 提取样本 ID
        sample_ids = [f.stem for f in velodyne_files]

        return sample_ids

    def __len__(self) -> int:
        """数据集大小"""
        return len(self.sample_ids)

    def __getitem__(self, idx: int) -> Dict:
        """
        获取样本。

        Args:
            idx: 样本索引

        Returns:
            样本字典，包含点云、标注等信息
        """
        sample_id = self.sample_ids[idx]

        # 加载点云
        points = self.load_point_cloud(sample_id)

        # 加载标注 (如果是训练集)
        labels = None
        if self.split == 'training':
            labels = self.load_labels(sample_id)

        # 加载标定参数
        calibration = self.load_calibration(sample_id)

        return {
            'sample_id': sample_id,
            'points': points,
            'labels': labels,
            'calibration': calibration
        }

    def load_point_cloud(self, sample_id: str) -> np.ndarray:
        """
        加载点云数据。

        Args:
            sample_id: 样本 ID

        Returns:
            (N, 4) 点云数据 [x, y, z, intensity]

        Raises:
            FileNotFoundError: 如果点云文件不存在
        """
        velodyne_file = self.velodyne_dir / f'{sample_id}.bin'

        if not velodyne_file.exists():
            raise FileNotFoundError(f"点云文件不存在: {velodyne_file}")

        # 加载二进制文件
        points = np.fromfile(str(velodyne_file), dtype=np.float32)
        points = points.reshape(-1, 4)

        return points

    def load_labels(self, sample_id: str) -> List[Dict]:
        """
        加载标注数据。

        Args:
            sample_id: 样本 ID

        Returns:
            标注列表，每个标注是一个字典
        """
        label_file = self.label_dir / f'{sample_id}.txt'

        if not label_file.exists():
            return []

        labels = []

        with open(label_file, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if not line:
                    continue

                # 解析标注行
                parts = line.split()

                # 提取信息
                obj_class = parts[0]
                truncated = float(parts[1])
                occluded = int(parts[2])
                alpha = float(parts[3])

                # 2D 边界框
                bbox_2d = np.array([
                    float(parts[4]),  # x1
                    float(parts[5]),  # y1
                    float(parts[6]),  # x2
                    float(parts[7])   # y2
                ])

                # 3D 尺寸
                dimensions = np.array([
                    float(parts[8]),   # h
                    float(parts[9]),   # w
                    float(parts[10])   # l
                ])

                # 3D 位置
                location = np.array([
                    float(parts[11]),  # x
                    float(parts[12]),  # y
                    float(parts[13])   # z
                ])

                # 旋转角度
                rotation_y = float(parts[14])

                labels.append({
                    'class': obj_class,
                    'class_id': self.CLASS_MAP.get(obj_class, -1),
                    'truncated': truncated,
                    'occluded': occluded,
                    'alpha': alpha,
                    'bbox_2d': bbox_2d,
                    'dimensions': dimensions,
                    'location': location,
                    'rotation_y': rotation_y
                })

        return labels

    def load_calibration(self, sample_id: str) -> Dict:
        """
        加载标定参数。

        Args:
            sample_id: 样本 ID

        Returns:
            标定参数字典
        """
        calib_file = self.calib_dir / f'{sample_id}.txt'

        if not calib_file.exists():
            return {}

        calibration = {}

        with open(calib_file, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if not line:
                    continue

                # 解析标定行
                key, value = line.split(':', 1)
                values = np.array([float(x) for x in value.split()])

                # 重塑为矩阵
                if key.startswith('P'):
                    calibration[key] = values.reshape(3, 4)
                elif key.startswith('R'):
                    calibration[key] = values.reshape(3, 3)
                elif key == 'Tr_velo_to_cam':
                    calibration[key] = values.reshape(3, 4)
                elif key == 'Tr_imu_to_velo':
                    calibration[key] = values.reshape(3, 4)

        return calibration

    def get_point_cloud(self, idx: int) -> PointCloud:
        """
        获取点云对象。

        Args:
            idx: 样本索引

        Returns:
            点云对象
        """
        sample_id = self.sample_ids[idx]
        points = self.load_point_cloud(sample_id)

        return PointCloud(points)

    def get_boxes_3d(self, idx: int) -> np.ndarray:
        """
        获取 3D 边界框。

        Args:
            idx: 样本索引

        Returns:
            (M, 7) 3D 边界框 [x, y, z, w, l, h, θ]
        """
        sample_id = self.sample_ids[idx]
        labels = self.load_labels(sample_id)

        boxes = []
        for label in labels:
            # 跳过 DontCare 类别
            if label['class'] == 'DontCare':
                continue

            # 提取 3D 边界框参数
            x, y, z = label['location']
            h, w, l = label['dimensions']
            theta = label['rotation_y']

            boxes.append([x, y, z, w, l, h, theta])

        return np.array(boxes) if boxes else np.zeros((0, 7))

    def get_class_labels(self, idx: int) -> np.ndarray:
        """
        获取类别标签。

        Args:
            idx: 样本索引

        Returns:
            (M,) 类别标签
        """
        sample_id = self.sample_ids[idx]
        labels = self.load_labels(sample_id)

        class_ids = []
        for label in labels:
            # 跳过 DontCare 类别
            if label['class'] == 'DontCare':
                continue

            class_ids.append(label['class_id'])

        return np.array(class_ids) if class_ids else np.array([])

    def get_difficulty(self, idx: int) -> np.ndarray:
        """
        获取难度等级。

        Args:
            idx: 样本索引

        Returns:
            (M,) 难度等级 (0: Easy, 1: Moderate, 2: Hard)
        """
        sample_id = self.sample_ids[idx]
        labels = self.load_labels(sample_id)

        difficulties = []
        for label in labels:
            # 跳过 DontCare 类别
            if label['class'] == 'DontCare':
                continue

            # 根据截断和遮挡程度判断难度
            truncated = label['truncated']
            occluded = label['occluded']

            if truncated <= 0.15 and occluded == 0:
                difficulty = 0  # Easy
            elif truncated <= 0.30 and occluded <= 1:
                difficulty = 1  # Moderate
            else:
                difficulty = 2  # Hard

            difficulties.append(difficulty)

        return np.array(difficulties) if difficulties else np.array([])

    def get_sample_info(self, idx: int) -> Dict:
        """
        获取样本信息。

        Args:
            idx: 样本索引

        Returns:
            样本信息字典
        """
        sample_id = self.sample_ids[idx]

        return {
            'sample_id': sample_id,
            'velodyne_file': str(self.velodyne_dir / f'{sample_id}.bin'),
            'label_file': str(self.label_dir / f'{sample_id}.txt'),
            'calib_file': str(self.calib_dir / f'{sample_id}.txt'),
            'image_file': str(self.image_dir / f'{sample_id}.png')
        }

    def visualize_sample(self, idx: int) -> None:
        """
        可视化样本。

        Args:
            idx: 样本索引
        """
        import open3d as o3d

        # 获取点云
        points = self.load_point_cloud(self.sample_ids[idx])

        # 创建 Open3D 点云
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points[:, :3])

        # 可视化
        o3d.visualization.draw_geometries([pcd])


class KITTIDataset:
    """
    KITTI 数据集类，用于 PyTorch 训练。

    Attributes:
        root_dir: KITTI 数据集根目录
        split: 数据集划分
        transform: 数据变换
    """

    def __init__(
        self,
        root_dir: str,
        split: str = 'training',
        transform=None
    ):
        """
        初始化 KITTI 数据集。

        Args:
            root_dir: KITTI 数据集根目录
            split: 数据集划分
            transform: 数据变换
        """
        self.loader = KITTILoader(root_dir, split)
        self.transform = transform

    def __len__(self) -> int:
        """数据集大小"""
        return len(self.loader)

    def __getitem__(self, idx: int) -> Dict:
        """
        获取样本。

        Args:
            idx: 样本索引

        Returns:
            样本字典
        """
        # 获取数据
        points = self.loader.load_point_cloud(self.loader.sample_ids[idx])
        boxes = self.loader.get_boxes_3d(idx)
        class_labels = self.loader.get_class_labels(idx)

        # 应用变换
        if self.transform:
            points, boxes, class_labels = self.transform(points, boxes, class_labels)

        return {
            'points': points,
            'boxes': boxes,
            'class_labels': class_labels,
            'sample_id': self.loader.sample_ids[idx]
        }
