"""
CNN Encoder - 图像特征提取器

使用预训练的 ResNet 作为图像编码器，提取图像的高层特征。
通过移除最后的全连接层，将 ResNet 转换为特征提取器。

核心思路：
- 输入图像 (3, H, W)
- 通过 ResNet 提取特征图 (embed_dim, h, w)
- 将特征图展平为序列 (h*w, embed_dim)，每个位置对应图像的一个区域
"""

import torch
import torch.nn as nn
import torchvision.models as models


class CNNEncoder(nn.Module):
    """CNN 编码器，基于预训练 ResNet 提取图像特征。

    将 ResNet 的最后全连接层和平均池化层移除，
    输出卷积特征图，可展平为序列供注意力机制使用。
    """

    def __init__(self, embed_dim: int = 256, backbone: str = "resnet50", pretrained: bool = True):
        """初始化 CNN 编码器。

        Args:
            embed_dim: 输出特征维度
            backbone: 骨干网络类型，支持 resnet18/resnet34/resnet50
            pretrained: 是否使用预训练权重
        """
        super().__init__()
        self.embed_dim = embed_dim

        # 加载预训练 ResNet
        if backbone == "resnet18":
            resnet = models.resnet18(
                weights=models.ResNet18_Weights.DEFAULT if pretrained else None
            )
            self.feature_dim = 512
        elif backbone == "resnet34":
            resnet = models.resnet34(
                weights=models.ResNet34_Weights.DEFAULT if pretrained else None
            )
            self.feature_dim = 512
        elif backbone == "resnet50":
            resnet = models.resnet50(
                weights=models.ResNet50_Weights.DEFAULT if pretrained else None
            )
            self.feature_dim = 2048
        else:
            raise ValueError(f"不支持的骨干网络: {backbone}")

        # 移除最后的全连接层和平均池化层，保留卷积特征
        # 原始 ResNet: conv layers -> avgpool -> fc
        # 我们只需要: conv layers -> 特征图
        self.backbone = nn.Sequential(*list(resnet.children())[:-2])

        # 线性投影层：将特征图维度映射到 embed_dim
        self.projection = nn.Linear(self.feature_dim, embed_dim)
        self.bn = nn.BatchNorm1d(embed_dim)

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        """提取图像特征。

        Args:
            images: 输入图像张量 (batch_size, 3, H, W)

        Returns:
            特征序列 (batch_size, num_pixels, embed_dim)
            其中 num_pixels = h * w（特征图的空间维度乘积）
        """
        # 提取卷积特征图: (batch_size, feature_dim, h, w)
        features = self.backbone(images)

        # 获取特征图的空间维度
        batch_size, feature_dim, h, w = features.shape

        # 将特征图从 (batch, C, H, W) 转换为 (batch, H*W, C)
        # 每个空间位置成为一个时间步
        features = features.permute(0, 2, 3, 1)  # (batch, h, w, feature_dim)
        features = features.reshape(batch_size, h * w, feature_dim)  # (batch, h*w, feature_dim)

        # 线性投影到 embed_dim
        features = self.projection(features)  # (batch, h*w, embed_dim)

        # 对每个位置的特征应用 BatchNorm
        # 需要 reshape 为 (batch * h*w, embed_dim) 再 reshape 回来
        batch_size, num_pixels, embed_dim = features.shape
        features = self.bn(features.reshape(-1, embed_dim))
        features = features.reshape(batch_size, num_pixels, embed_dim)

        return features

    @property
    def num_pixels(self) -> int:
        """获取特征图的空间像素数量（需要先做一次前向传播来确定）。
        对于标准 ResNet + 224x224 输入，通常是 7*7=49。
        """
        # 典型值：224x224 输入 -> 7x7 特征图 -> 49 个像素
        return 49  # 7x7 for ResNet with 224x224 input
