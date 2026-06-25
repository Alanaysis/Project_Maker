"""视频特征提取器模块

使用预训练 CNN 提取视频帧的空间特征，并通过池化操作聚合为视频级特征。
"""

from typing import Optional

import torch
import torch.nn as nn
import torchvision.models as models


class VideoFeatureExtractor(nn.Module):
    """视频特征提取器

    使用预训练 CNN（如 ResNet）提取每帧的空间特征，
    然后通过时序池化聚合为视频级特征向量。

    Args:
        backbone: 骨干网络名称 ('resnet18', 'resnet34', 'resnet50')
        pretrained: 是否使用预训练权重
        feature_dim: 输出特征维度
        pooling: 时序池化方式 ('mean', 'max', 'attention')
    """

    def __init__(
        self,
        backbone: str = "resnet18",
        pretrained: bool = True,
        feature_dim: int = 512,
        pooling: str = "mean",
    ):
        super().__init__()
        self.backbone_name = backbone
        self.feature_dim = feature_dim
        self.pooling_type = pooling

        # 构建骨干网络
        self.backbone, backbone_out_dim = self._build_backbone(backbone, pretrained)

        # 特征投影层
        self.projection = nn.Sequential(
            nn.Linear(backbone_out_dim, feature_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
        )

        # 时序池化
        if pooling == "attention":
            self.attention = nn.Sequential(
                nn.Linear(feature_dim, feature_dim // 4),
                nn.Tanh(),
                nn.Linear(feature_dim // 4, 1),
            )

    def _build_backbone(self, name: str, pretrained: bool) -> tuple:
        """构建骨干网络，移除最后的分类层"""
        if name == "resnet18":
            weights = models.ResNet18_Weights.DEFAULT if pretrained else None
            net = models.resnet18(weights=weights)
            out_dim = net.fc.in_features
            net.fc = nn.Identity()
        elif name == "resnet34":
            weights = models.ResNet34_Weights.DEFAULT if pretrained else None
            net = models.resnet34(weights=weights)
            out_dim = net.fc.in_features
            net.fc = nn.Identity()
        elif name == "resnet50":
            weights = models.ResNet50_Weights.DEFAULT if pretrained else None
            net = models.resnet50(weights=weights)
            out_dim = net.fc.in_features
            net.fc = nn.Identity()
        else:
            raise ValueError(f"不支持的骨干网络: {name}")

        return net, out_dim

    def extract_frame_features(self, frames: torch.Tensor) -> torch.Tensor:
        """提取单帧或帧序列的空间特征

        Args:
            frames: 帧张量，形状为 (T, C, H, W) 或 (B, T, C, H, W)

        Returns:
            帧特征，形状为 (T, feature_dim) 或 (B, T, feature_dim)
        """
        squeeze = False
        if frames.dim() == 4:
            # (T, C, H, W) -> (1, T, C, H, W)
            frames = frames.unsqueeze(0)
            squeeze = True

        B, T, C, H, W = frames.shape

        # 合并 batch 和 time 维度
        x = frames.view(B * T, C, H, W)
        # 提取特征
        features = self.backbone(x)
        # 投影
        features = self.projection(features)
        # 恢复维度
        features = features.view(B, T, -1)

        if squeeze:
            features = features.squeeze(0)

        return features

    def temporal_pool(self, features: torch.Tensor) -> torch.Tensor:
        """时序池化

        Args:
            features: 帧特征，形状为 (B, T, D) 或 (T, D)

        Returns:
            视频级特征，形状为 (B, D) 或 (D,)
        """
        squeeze = False
        if features.dim() == 2:
            features = features.unsqueeze(0)
            squeeze = True

        if self.pooling_type == "mean":
            pooled = features.mean(dim=1)
        elif self.pooling_type == "max":
            pooled = features.max(dim=1)[0]
        elif self.pooling_type == "attention":
            # 注意力加权池化
            attn_scores = self.attention(features)  # (B, T, 1)
            attn_weights = torch.softmax(attn_scores, dim=1)
            pooled = (features * attn_weights).sum(dim=1)
        else:
            raise ValueError(f"未知池化方式: {self.pooling_type}")

        if squeeze:
            pooled = pooled.squeeze(0)

        return pooled

    def forward(self, frames: torch.Tensor) -> torch.Tensor:
        """前向传播：提取帧特征并池化

        Args:
            frames: 视频帧张量，形状为 (B, T, C, H, W) 或 (T, C, H, W)

        Returns:
            视频特征向量，形状为 (B, feature_dim) 或 (feature_dim,)
        """
        frame_features = self.extract_frame_features(frames)
        video_feature = self.temporal_pool(frame_features)
        return video_feature

    def __repr__(self) -> str:
        return (
            f"VideoFeatureExtractor(backbone='{self.backbone_name}', "
            f"feature_dim={self.feature_dim}, pooling='{self.pooling_type}')"
        )
