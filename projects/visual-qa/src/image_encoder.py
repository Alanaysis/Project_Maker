"""
图像编码器模块

使用 CNN 提取图像特征，支持多种预训练骨干网络。
"""

import torch
import torch.nn as nn
import torchvision.models as models
from typing import Optional, Tuple


class ImageEncoder(nn.Module):
    """
    图像编码器

    使用预训练 CNN 提取图像特征，支持 ResNet、VGG 等骨干网络。

    Args:
        backbone: 骨干网络类型 ('resnet18', 'resnet34', 'resnet50', 'vgg16')
        pretrained: 是否使用预训练权重
        feature_dim: 输出特征维度
        freeze_backbone: 是否冻结骨干网络参数
    """

    def __init__(
        self,
        backbone: str = 'resnet18',
        pretrained: bool = False,
        feature_dim: int = 512,
        freeze_backbone: bool = False,
    ):
        super().__init__()

        self.backbone_name = backbone
        self.feature_dim = feature_dim

        # 创建骨干网络
        self.backbone, backbone_out_dim = self._create_backbone(backbone, pretrained)

        # 冻结骨干网络
        if freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False

        # 特征投影层
        self.projection = nn.Sequential(
            nn.Linear(backbone_out_dim, feature_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.1),
        )

    def _create_backbone(self, backbone: str, pretrained: bool) -> Tuple[nn.Module, int]:
        """创建骨干网络并返回模型和输出维度"""

        if backbone == 'resnet18':
            model = models.resnet18(pretrained=pretrained)
            # 移除最后的全连接层
            backbone_out_dim = model.fc.in_features
            model = nn.Sequential(*list(model.children())[:-1])

        elif backbone == 'resnet34':
            model = models.resnet34(pretrained=pretrained)
            backbone_out_dim = model.fc.in_features
            model = nn.Sequential(*list(model.children())[:-1])

        elif backbone == 'resnet50':
            model = models.resnet50(pretrained=pretrained)
            backbone_out_dim = model.fc.in_features
            model = nn.Sequential(*list(model.children())[:-1])

        elif backbone == 'vgg16':
            model = models.vgg16(pretrained=pretrained)
            backbone_out_dim = model.classifier[0].in_features
            # 只使用特征提取部分
            model = model.features

        else:
            raise ValueError(f"不支持的骨干网络: {backbone}")

        return model, backbone_out_dim

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            images: 图像张量 [batch_size, channels, height, width]

        Returns:
            图像特征 [batch_size, feature_dim]
        """
        # 提取特征
        features = self.backbone(images)

        # 展平特征
        if len(features.shape) > 2:
            features = features.view(features.size(0), -1)

        # 投影到指定维度
        features = self.projection(features)

        return features

    def get_output_dim(self) -> int:
        """获取输出特征维度"""
        return self.feature_dim


class SpatialImageEncoder(nn.Module):
    """
    空间图像编码器

    保留空间信息的图像特征提取，输出特征图而非全局特征。

    Args:
        backbone: 骨干网络类型
        pretrained: 是否使用预训练权重
        feature_dim: 输出通道数
    """

    def __init__(
        self,
        backbone: str = 'resnet18',
        pretrained: bool = False,
        feature_dim: int = 256,
    ):
        super().__init__()

        self.feature_dim = feature_dim

        # 创建骨干网络（保留空间维度）
        if backbone == 'resnet18':
            full_model = models.resnet18(pretrained=pretrained)
            # 移除最后两层（avgpool 和 fc）
            self.backbone = nn.Sequential(*list(full_model.children())[:-2])
            backbone_out_dim = 512
        else:
            raise ValueError(f"不支持的骨干网络: {backbone}")

        # 1x1 卷积调整通道数
        self.conv_projection = nn.Conv2d(backbone_out_dim, feature_dim, 1)

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            images: 图像张量 [batch_size, channels, height, width]

        Returns:
            空间特征 [batch_size, feature_dim, h, w]
        """
        features = self.backbone(images)
        features = self.conv_projection(features)
        return features

    def get_output_dim(self) -> int:
        """获取输出通道维度"""
        return self.feature_dim
