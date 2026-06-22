"""
PointPillars 模型实现

实现 PointPillars 3D 目标检测算法。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Tuple, Optional
import numpy as np


class PillarEncoder(nn.Module):
    """
    PointPillars 编码器。

    将点云转换为伪图像。
    """

    def __init__(
        self,
        voxel_size: List[float],
        point_cloud_range: List[float],
        max_points_per_pillar: int = 32,
        max_pillars: int = 12000
    ):
        """
        初始化 Pillar 编码器。

        Args:
            voxel_size: 体素大小 [x, y, z]
            point_cloud_range: 点云范围 [x_min, y_min, z_min, x_max, y_max, z_max]
            max_points_per_pillar: 每个 Pillar 最大点数
            max_pillars: 最大 Pillar 数量
        """
        super().__init__()

        self.voxel_size = voxel_size
        self.point_cloud_range = point_cloud_range
        self.max_points_per_pillar = max_points_per_pillar
        self.max_pillars = max_pillars

        # 计算网格尺寸
        self.x_size = int((point_cloud_range[3] - point_cloud_range[0]) / voxel_size[0])
        self.y_size = int((point_cloud_range[4] - point_cloud_range[1]) / voxel_size[1])

        # 特征维度: x, y, z, r, xc, yc, zc, xp, yp, zp
        self.in_channels = 9
        self.out_channels = 64

        # 特征提取网络
        self.feature_net = nn.Sequential(
            nn.Linear(self.in_channels, self.out_channels),
            nn.BatchNorm1d(self.out_channels),
            nn.ReLU(),
            nn.Linear(self.out_channels, self.out_channels)
        )

    def forward(self, points: torch.Tensor) -> torch.Tensor:
        """
        前向传播。

        Args:
            points: (B, N, C) 点云数据

        Returns:
            pillars: (B, D, H, W) 伪图像
        """
        batch_size = points.shape[0]

        # 1. 创建 Pillars
        pillars, coords, num_points = self._create_pillars(points)

        # 2. 提取 Pillar 特征
        pillar_features = self._extract_features(pillars, num_points)

        # 3. 散射到图像
        pseudo_image = self._scatter_to_image(pillar_features, coords, batch_size)

        return pseudo_image

    def _create_pillars(self, points: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        将点云组织成 Pillars。

        Args:
            points: (B, N, C) 点云数据

        Returns:
            pillars: (B, max_pillars, max_points, C) Pillar 数据
            coords: (B, max_pillars, 2) Pillar 坐标
            num_points: (B, max_pillars) 每个 Pillar 的点数
        """
        batch_size, num_points, num_features = points.shape

        # 初始化输出
        pillars = torch.zeros(
            batch_size, self.max_pillars, self.max_points_per_pillar, num_features,
            device=points.device
        )
        coords = torch.zeros(
            batch_size, self.max_pillars, 2,
            device=points.device, dtype=torch.long
        )
        num_points_per_pillar = torch.zeros(
            batch_size, self.max_pillars,
            device=points.device, dtype=torch.long
        )

        for b in range(batch_size):
            # 获取当前批次的点云
            batch_points = points[b]

            # 计算每个点所在的 Pillar
            x_coords = ((batch_points[:, 0] - self.point_cloud_range[0]) / self.voxel_size[0]).long()
            y_coords = ((batch_points[:, 1] - self.point_cloud_range[1]) / self.voxel_size[1]).long()

            # 过滤有效点
            valid_mask = (
                (x_coords >= 0) & (x_coords < self.x_size) &
                (y_coords >= 0) & (y_coords < self.y_size)
            )
            valid_points = batch_points[valid_mask]
            valid_x = x_coords[valid_mask]
            valid_y = y_coords[valid_mask]

            # 组织成 Pillars
            pillar_dict = {}
            for i in range(len(valid_points)):
                key = (valid_x[i].item(), valid_y[i].item())
                if key not in pillar_dict:
                    pillar_dict[key] = []
                pillar_dict[key].append(valid_points[i])

                # 限制每个 Pillar 的点数
                if len(pillar_dict[key]) >= self.max_points_per_pillar:
                    break

            # 填充输出
            for pillar_idx, ((x, y), pillar_points) in enumerate(pillar_dict.items()):
                if pillar_idx >= self.max_pillars:
                    break

                # 填充坐标
                coords[b, pillar_idx] = torch.tensor([x, y], dtype=torch.long)

                # 填充点数
                num_points_per_pillar[b, pillar_idx] = min(len(pillar_points), self.max_points_per_pillar)

                # 填充点云
                for point_idx, point in enumerate(pillar_points):
                    if point_idx >= self.max_points_per_pillar:
                        break
                    pillars[b, pillar_idx, point_idx] = point

        return pillars, coords, num_points_per_pillar

    def _extract_features(self, pillars: torch.Tensor, num_points: torch.Tensor) -> torch.Tensor:
        """
        提取 Pillar 特征。

        Args:
            pillars: (B, max_pillars, max_points, C) Pillar 数据
            num_points: (B, max_pillars) 每个 Pillar 的点数

        Returns:
            features: (B, max_pillars, out_channels) Pillar 特征
        """
        batch_size, max_pillars, max_points, num_features = pillars.shape

        # 计算 Pillar 中心
        pillar_centers = pillars[:, :, :, :3].mean(dim=2, keepdim=True)  # (B, P, 1, 3)

        # 计算相对坐标
        relative_coords = pillars[:, :, :, :3] - pillar_centers  # (B, P, N, 3)

        # 计算相对于 Pillar 中心的偏移
        pillar_center_offset = pillars[:, :, :, :3] - pillar_centers  # (B, P, N, 3)

        # 拼接特征
        # 原始特征: x, y, z, r
        # 相对坐标: xc, yc, zc
        # Pillar 中心偏移: xp, yp, zp
        features = torch.cat([
            pillars[:, :, :, :4],  # x, y, z, r
            relative_coords,       # xc, yc, zc
            pillar_center_offset   # xp, yp, zp
        ], dim=-1)  # (B, P, N, 9)

        # 重塑为 (B*P*N, 9)
        features = features.view(-1, self.in_channels)

        # 提取特征
        features = self.feature_net(features)  # (B*P*N, 64)

        # 重塑回 (B, P, N, 64)
        features = features.view(batch_size, max_pillars, max_points, self.out_channels)

        # 最大池化
        # 创建掩码
        mask = torch.arange(max_points, device=pillars.device).unsqueeze(0).unsqueeze(0)
        mask = mask < num_points.unsqueeze(-1)  # (B, P, N)
        mask = mask.unsqueeze(-1)  # (B, P, N, 1)

        # 应用掩码
        features = features * mask.float()

        # 最大池化
        features, _ = features.max(dim=2)  # (B, P, 64)

        return features

    def _scatter_to_image(self, features: torch.Tensor, coords: torch.Tensor, batch_size: int) -> torch.Tensor:
        """
        将 Pillar 特征散射到图像。

        Args:
            features: (B, max_pillars, out_channels) Pillar 特征
            coords: (B, max_pillars, 2) Pillar 坐标
            batch_size: 批次大小

        Returns:
            image: (B, D, H, W) 伪图像
        """
        # 初始化伪图像
        image = torch.zeros(
            batch_size, self.out_channels, self.y_size, self.x_size,
            device=features.device
        )

        # 散射特征
        for b in range(batch_size):
            for p in range(features.shape[1]):
                x, y = coords[b, p]
                if x >= 0 and x < self.x_size and y >= 0 and y < self.y_size:
                    image[b, :, y, x] = features[b, p]

        return image


class Backbone2D(nn.Module):
    """
    2D 骨干网络。
    """

    def __init__(self, in_channels: int = 64):
        """
        初始化 2D 骨干网络。

        Args:
            in_channels: 输入通道数
        """
        super().__init__()

        self.block1 = self._make_block(in_channels, 64, num_blocks=2)
        self.block2 = self._make_block(64, 128, num_blocks=2)
        self.block3 = self._make_block(128, 256, num_blocks=2)

    def _make_block(self, in_channels: int, out_channels: int, num_blocks: int) -> nn.Sequential:
        """
        创建卷积块。

        Args:
            in_channels: 输入通道数
            out_channels: 输出通道数
            num_blocks: 卷积层数

        Returns:
            卷积块
        """
        layers = []
        for i in range(num_blocks):
            if i == 0:
                stride = 2  # 第一个卷积下采样
            else:
                stride = 1

            layers.extend([
                nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1),
                nn.BatchNorm2d(out_channels),
                nn.ReLU()
            ])
            in_channels = out_channels

        return nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> List[torch.Tensor]:
        """
        前向传播。

        Args:
            x: (B, C, H, W) 输入特征图

        Returns:
            多尺度特征图列表
        """
        x1 = self.block1(x)   # 1/2 分辨率
        x2 = self.block2(x1)  # 1/4 分辨率
        x3 = self.block3(x2)  # 1/8 分辨率

        return [x1, x2, x3]


class FPN(nn.Module):
    """
    特征金字塔网络。
    """

    def __init__(self, in_channels_list: List[int], out_channels: int):
        """
        初始化 FPN。

        Args:
            in_channels_list: 输入通道数列表
            out_channels: 输出通道数
        """
        super().__init__()

        self.lateral_convs = nn.ModuleList()
        self.output_convs = nn.ModuleList()

        for in_channels in in_channels_list:
            self.lateral_convs.append(
                nn.Conv2d(in_channels, out_channels, kernel_size=1)
            )
            self.output_convs.append(
                nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
            )

    def forward(self, features: List[torch.Tensor]) -> List[torch.Tensor]:
        """
        前向传播。

        Args:
            features: 多尺度特征图列表

        Returns:
            融合后的特征图列表
        """
        # 横向连接
        laterals = [
            conv(feat)
            for conv, feat in zip(self.lateral_convs, features)
        ]

        # 自顶向下路径
        for i in range(len(laterals) - 1, 0, -1):
            laterals[i - 1] += F.interpolate(
                laterals[i],
                size=laterals[i - 1].shape[2:],
                mode='nearest'
            )

        # 输出卷积
        outputs = [
            conv(feat)
            for conv, feat in zip(self.output_convs, laterals)
        ]

        return outputs


class DetectionHead(nn.Module):
    """
    检测头。
    """

    def __init__(
        self,
        in_channels: int,
        num_classes: int,
        num_anchors_per_location: int
    ):
        """
        初始化检测头。

        Args:
            in_channels: 输入通道数
            num_classes: 类别数
            num_anchors_per_location: 每个位置的 Anchor 数量
        """
        super().__init__()

        self.num_classes = num_classes
        self.num_anchors = num_anchors_per_location

        # 分类分支
        self.cls_head = nn.Conv2d(
            in_channels,
            num_anchors_per_location * num_classes,
            kernel_size=1
        )

        # 回归分支 (x, y, z, w, l, h, θ)
        self.reg_head = nn.Conv2d(
            in_channels,
            num_anchors_per_location * 7,
            kernel_size=1
        )

        # 方向分类分支
        self.dir_head = nn.Conv2d(
            in_channels,
            num_anchors_per_location * 2,
            kernel_size=1
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        前向传播。

        Args:
            x: (B, C, H, W) 特征图

        Returns:
            cls_score: 分类分数
            bbox_pred: 边界框预测
            dir_pred: 方向预测
        """
        cls_score = self.cls_head(x)
        bbox_pred = self.reg_head(x)
        dir_pred = self.dir_head(x)

        return cls_score, bbox_pred, dir_pred


class PointPillars(nn.Module):
    """
    PointPillars 3D 目标检测模型。
    """

    def __init__(
        self,
        voxel_size: List[float] = [0.16, 0.16, 4],
        point_cloud_range: List[float] = [-40, -40, -3, 40, 40, 1],
        max_points_per_pillar: int = 32,
        max_pillars: int = 12000,
        num_classes: int = 3,
        num_anchors_per_location: int = 2
    ):
        """
        初始化 PointPillars。

        Args:
            voxel_size: 体素大小
            point_cloud_range: 点云范围
            max_points_per_pillar: 每个 Pillar 最大点数
            max_pillars: 最大 Pillar 数量
            num_classes: 类别数
            num_anchors_per_location: 每个位置的 Anchor 数量
        """
        super().__init__()

        self.voxel_size = voxel_size
        self.point_cloud_range = point_cloud_range
        self.num_classes = num_classes

        # Pillar 编码器
        self.pillar_encoder = PillarEncoder(
            voxel_size=voxel_size,
            point_cloud_range=point_cloud_range,
            max_points_per_pillar=max_points_per_pillar,
            max_pillars=max_pillars
        )

        # 2D 骨干网络
        self.backbone = Backbone2D(in_channels=64)

        # FPN
        self.fpn = FPN(
            in_channels_list=[64, 128, 256],
            out_channels=64
        )

        # 检测头
        self.detection_head = DetectionHead(
            in_channels=64,
            num_classes=num_classes,
            num_anchors_per_location=num_anchors_per_location
        )

        # 初始化权重
        self._init_weights()

    def _init_weights(self):
        """初始化权重"""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, points: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        前向传播。

        Args:
            points: (B, N, C) 点云数据

        Returns:
            包含预测结果的字典
        """
        # 1. Pillar 编码
        pillar_features = self.pillar_encoder(points)  # (B, 64, H, W)

        # 2. 2D 骨干网络
        backbone_features = self.backbone(pillar_features)  # [C1, C2, C3]

        # 3. FPN
        fpn_features = self.fpn(backbone_features)  # [F1, F2, F3]

        # 4. 使用最高分辨率的特征图进行检测
        detection_feature = fpn_features[0]  # (B, 64, H, W)

        # 5. 检测头
        cls_score, bbox_pred, dir_pred = self.detection_head(detection_feature)

        return {
            'cls_score': cls_score,
            'bbox_pred': bbox_pred,
            'dir_pred': dir_pred
        }


def build_pointpillars(config: Dict) -> PointPillars:
    """
    构建 PointPillars 模型。

    Args:
        config: 配置字典

    Returns:
        PointPillars 模型
    """
    model = PointPillars(
        voxel_size=config.get('voxel_size', [0.16, 0.16, 4]),
        point_cloud_range=config.get('point_cloud_range', [-40, -40, -3, 40, 40, 1]),
        max_points_per_pillar=config.get('max_points_per_pillar', 32),
        max_pillars=config.get('max_pillars', 12000),
        num_classes=config.get('num_classes', 3),
        num_anchors_per_location=config.get('num_anchors_per_location', 2)
    )

    return model
