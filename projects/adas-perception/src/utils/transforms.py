"""
数据变换模块

提供点云数据增强和变换功能。
"""

import numpy as np
from typing import Tuple, List, Optional
import random


class PointCloudTransforms:
    """
    点云数据变换类。
    """

    @staticmethod
    def random_flip(
        points: np.ndarray,
        boxes: np.ndarray,
        prob: float = 0.5
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        随机翻转点云。

        Args:
            points: (N, C) 点云数据
            boxes: (M, 7) 3D 边界框 [x, y, z, w, l, h, θ]
            prob: 翻转概率

        Returns:
            翻转后的点云和边界框
        """
        if random.random() < prob:
            # 沿 X 轴翻转
            points = points.copy()
            boxes = boxes.copy()

            points[:, 0] = -points[:, 0]
            boxes[:, 0] = -boxes[:, 0]
            boxes[:, 6] = -boxes[:, 6]  # 角度取反

        if random.random() < prob:
            # 沿 Y 轴翻转
            points = points.copy()
            boxes = boxes.copy()

            points[:, 1] = -points[:, 1]
            boxes[:, 1] = -boxes[:, 1]
            boxes[:, 6] = -boxes[:, 6]  # 角度取反

        return points, boxes

    @staticmethod
    def random_rotation(
        points: np.ndarray,
        boxes: np.ndarray,
        rotation_range: Tuple[float, float] = (-0.78, 0.78)
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        随机旋转点云。

        Args:
            points: (N, C) 点云数据
            boxes: (M, 7) 3D 边界框
            rotation_range: 旋转角度范围 (弧度)

        Returns:
            旋转后的点云和边界框
        """
        angle = random.uniform(*rotation_range)

        # 旋转矩阵
        cos_val = np.cos(angle)
        sin_val = np.sin(angle)
        rot_matrix = np.array([
            [cos_val, -sin_val, 0],
            [sin_val, cos_val, 0],
            [0, 0, 1]
        ])

        # 旋转点云
        points = points.copy()
        points[:, :3] = points[:, :3] @ rot_matrix.T

        # 旋转边界框中心
        boxes = boxes.copy()
        boxes[:, :3] = boxes[:, :3] @ rot_matrix.T

        # 更新角度
        boxes[:, 6] += angle

        return points, boxes

    @staticmethod
    def random_scaling(
        points: np.ndarray,
        boxes: np.ndarray,
        scale_range: Tuple[float, float] = (0.95, 1.05)
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        随机缩放点云。

        Args:
            points: (N, C) 点云数据
            boxes: (M, 7) 3D 边界框
            scale_range: 缩放范围

        Returns:
            缩放后的点云和边界框
        """
        scale = random.uniform(*scale_range)

        # 缩放点云
        points = points.copy()
        points[:, :3] *= scale

        # 缩放边界框
        boxes = boxes.copy()
        boxes[:, :3] *= scale  # 中心
        boxes[:, 3:6] *= scale  # 尺寸

        return points, boxes

    @staticmethod
    def random_translation(
        points: np.ndarray,
        boxes: np.ndarray,
        std: Tuple[float, float, float] = (0.2, 0.2, 0.2)
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        随机平移点云。

        Args:
            points: (N, C) 点云数据
            boxes: (M, 7) 3D 边界框
            std: 平移标准差

        Returns:
            平移后的点云和边界框
        """
        # 生成随机平移
        translation = np.random.normal(0, std, size=3)

        # 平移点云
        points = points.copy()
        points[:, :3] += translation

        # 平移边界框
        boxes = boxes.copy()
        boxes[:, :3] += translation

        return points, boxes

    @staticmethod
    def random_noise(
        points: np.ndarray,
        std: float = 0.01
    ) -> np.ndarray:
        """
        添加随机噪声。

        Args:
            points: (N, C) 点云数据
            std: 噪声标准差

        Returns:
            添加噪声后的点云
        """
        points = points.copy()
        noise = np.random.normal(0, std, size=points[:, :3].shape)
        points[:, :3] += noise

        return points

    @staticmethod
    def random_dropout(
        points: np.ndarray,
        prob: float = 0.1
    ) -> np.ndarray:
        """
        随机丢弃点。

        Args:
            points: (N, C) 点云数据
            prob: 丢弃概率

        Returns:
            丢弃后的点云
        """
        mask = np.random.random(len(points)) > prob
        return points[mask]

    @staticmethod
    def normalize_intensity(
        points: np.ndarray,
        intensity_range: Tuple[float, float] = (0, 1)
    ) -> np.ndarray:
        """
        归一化强度。

        Args:
            points: (N, C) 点云数据
            intensity_range: 强度范围

        Returns:
            归一化后的点云
        """
        points = points.copy()

        if points.shape[1] >= 4:
            intensity = points[:, 3]
            min_val = intensity.min()
            max_val = intensity.max()

            if max_val > min_val:
                intensity = (intensity - min_val) / (max_val - min_val)
                intensity = intensity * (intensity_range[1] - intensity_range[0]) + intensity_range[0]
                points[:, 3] = intensity

        return points

    @staticmethod
    def filter_by_range(
        points: np.ndarray,
        x_range: Tuple[float, float] = (-40, 40),
        y_range: Tuple[float, float] = (-40, 40),
        z_range: Tuple[float, float] = (-3, 1)
    ) -> np.ndarray:
        """
        按范围过滤点云。

        Args:
            points: (N, C) 点云数据
            x_range: X 轴范围
            y_range: Y 轴范围
            z_range: Z 轴范围

        Returns:
            过滤后的点云
        """
        mask = (
            (points[:, 0] >= x_range[0]) &
            (points[:, 0] <= x_range[1]) &
            (points[:, 1] >= y_range[0]) &
            (points[:, 1] <= y_range[1]) &
            (points[:, 2] >= z_range[0]) &
            (points[:, 2] <= z_range[1])
        )

        return points[mask]

    @staticmethod
    def downsample(
        points: np.ndarray,
        voxel_size: float = 0.1
    ) -> np.ndarray:
        """
        体素降采样。

        Args:
            points: (N, C) 点云数据
            voxel_size: 体素大小

        Returns:
            降采样后的点云
        """
        # 计算体素坐标
        voxel_coords = np.floor(points[:, :3] / voxel_size).astype(int)

        # 找到唯一的体素
        unique_voxels, indices = np.unique(voxel_coords, axis=0, return_index=True)

        # 取每个体素的中心点
        downsampled_points = points[indices]

        return downsampled_points


class BoxTransforms:
    """
    边界框变换类。
    """

    @staticmethod
    def boxes_to_corners(boxes: np.ndarray) -> np.ndarray:
        """
        将边界框转换为 8 个角点。

        Args:
            boxes: (M, 7) 3D 边界框 [x, y, z, w, l, h, θ]

        Returns:
            (M, 8, 3) 角点坐标
        """
        num_boxes = len(boxes)
        corners = np.zeros((num_boxes, 8, 3))

        for i in range(num_boxes):
            x, y, z, w, l, h, theta = boxes[i]

            # 计算 8 个顶点
            # 底面 4 个点
            corners[i, 0] = [
                x - w/2 * np.cos(theta) + l/2 * np.sin(theta),
                y - w/2 * np.sin(theta) - l/2 * np.cos(theta),
                z - h/2
            ]
            corners[i, 1] = [
                x + w/2 * np.cos(theta) + l/2 * np.sin(theta),
                y + w/2 * np.sin(theta) - l/2 * np.cos(theta),
                z - h/2
            ]
            corners[i, 2] = [
                x + w/2 * np.cos(theta) - l/2 * np.sin(theta),
                y + w/2 * np.sin(theta) + l/2 * np.cos(theta),
                z - h/2
            ]
            corners[i, 3] = [
                x - w/2 * np.cos(theta) - l/2 * np.sin(theta),
                y - w/2 * np.sin(theta) + l/2 * np.cos(theta),
                z - h/2
            ]

            # 顶面 4 个点
            corners[i, 4] = corners[i, 0].copy()
            corners[i, 4][2] = z + h/2
            corners[i, 5] = corners[i, 1].copy()
            corners[i, 5][2] = z + h/2
            corners[i, 6] = corners[i, 2].copy()
            corners[i, 6][2] = z + h/2
            corners[i, 7] = corners[i, 3].copy()
            corners[i, 7][2] = z + h/2

        return corners

    @staticmethod
    def compute_bev_iou(boxes1: np.ndarray, boxes2: np.ndarray) -> np.ndarray:
        """
        计算 BEV (鸟瞰图) IoU。

        Args:
            boxes1: (M, 7) 3D 边界框
            boxes2: (N, 7) 3D 边界框

        Returns:
            (M, N) IoU 矩阵
        """
        M = len(boxes1)
        N = len(boxes2)
        iou_matrix = np.zeros((M, N))

        for i in range(M):
            for j in range(N):
                iou_matrix[i, j] = BoxTransforms._compute_single_bev_iou(
                    boxes1[i], boxes2[j]
                )

        return iou_matrix

    @staticmethod
    def _compute_single_bev_iou(box1: np.ndarray, box2: np.ndarray) -> float:
        """
        计算单个 BEV IoU。

        Args:
            box1: (7,) 3D 边界框
            box2: (7,) 3D 边界框

        Returns:
            IoU 值
        """
        # 获取边界框参数
        x1, y1, _, w1, l1, _, theta1 = box1
        x2, y2, _, w2, l2, _, theta2 = box2

        # 计算边界框角点
        corners1 = BoxTransforms._get_bev_corners(x1, y1, w1, l1, theta1)
        corners2 = BoxTransforms._get_bev_corners(x2, y2, w2, l2, theta2)

        # 计算交集面积
        intersection_area = BoxTransforms._compute_intersection_area(corners1, corners2)

        # 计算并集面积
        area1 = w1 * l1
        area2 = w2 * l2
        union_area = area1 + area2 - intersection_area

        # 计算 IoU
        iou = intersection_area / union_area if union_area > 0 else 0.0

        return iou

    @staticmethod
    def _get_bev_corners(
        x: float,
        y: float,
        w: float,
        l: float,
        theta: float
    ) -> np.ndarray:
        """
        获取 BEV 角点。

        Args:
            x, y: 中心坐标
            w, l: 宽度和长度
            theta: 旋转角度

        Returns:
            (4, 2) 角点坐标
        """
        corners = np.array([
            [-w/2, -l/2],
            [w/2, -l/2],
            [w/2, l/2],
            [-w/2, l/2]
        ])

        # 旋转
        cos_val = np.cos(theta)
        sin_val = np.sin(theta)
        rotation_matrix = np.array([
            [cos_val, -sin_val],
            [sin_val, cos_val]
        ])
        corners = corners @ rotation_matrix.T

        # 平移
        corners[:, 0] += x
        corners[:, 1] += y

        return corners

    @staticmethod
    def _compute_intersection_area(
        corners1: np.ndarray,
        corners2: np.ndarray
    ) -> float:
        """
        计算两个多边形的交集面积。

        Args:
            corners1: (4, 2) 多边形 1 的角点
            corners2: (4, 2) 多边形 2 的角点

        Returns:
            交集面积
        """
        # 使用 Sutherland-Hodgman 算法计算交集
        # 这里简化实现，使用边界框近似
        x1_min, y1_min = corners1.min(axis=0)
        x1_max, y1_max = corners1.max(axis=0)
        x2_min, y2_min = corners2.min(axis=0)
        x2_max, y2_max = corners2.max(axis=0)

        # 计算交集
        x_min = max(x1_min, x2_min)
        y_min = max(y1_min, y2_min)
        x_max = min(x1_max, x2_max)
        y_max = min(y1_max, y2_max)

        # 计算交集面积
        if x_min < x_max and y_min < y_max:
            intersection_area = (x_max - x_min) * (y_max - y_min)
        else:
            intersection_area = 0.0

        return intersection_area


class Compose:
    """
    组合多个变换。
    """

    def __init__(self, transforms: List):
        """
        初始化。

        Args:
            transforms: 变换列表
        """
        self.transforms = transforms

    def __call__(
        self,
        points: np.ndarray,
        boxes: Optional[np.ndarray] = None,
        labels: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, ...]:
        """
        应用变换。

        Args:
            points: (N, C) 点云数据
            boxes: (M, 7) 3D 边界框
            labels: (M,) 类别标签

        Returns:
            变换后的数据
        """
        for transform in self.transforms:
            if boxes is not None:
                points, boxes = transform(points, boxes)
            else:
                points = transform(points)

        if boxes is not None and labels is not None:
            return points, boxes, labels
        elif boxes is not None:
            return points, boxes
        else:
            return points


def get_train_transforms() -> Compose:
    """
    获取训练数据变换。

    Returns:
        训练数据变换
    """
    return Compose([
        lambda p, b: PointCloudTransforms.random_flip(p, b, prob=0.5),
        lambda p, b: PointCloudTransforms.random_rotation(p, b, rotation_range=(-0.78, 0.78)),
        lambda p, b: PointCloudTransforms.random_scaling(p, b, scale_range=(0.95, 1.05)),
        lambda p, b: PointCloudTransforms.random_translation(p, b, std=(0.2, 0.2, 0.2)),
    ])


def get_val_transforms() -> Compose:
    """
    获取验证数据变换。

    Returns:
        验证数据变换
    """
    return Compose([
        # 验证时只进行范围过滤
        lambda p, b: (PointCloudTransforms.filter_by_range(p), b),
    ])
