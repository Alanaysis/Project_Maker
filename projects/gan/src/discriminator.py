"""
Discriminator 判别器模块
=======================

实现 GAN 的判别器网络，区分真实图像和生成图像。

判别器的核心任务:
    学习区分真实图像和生成图像，
    为真实图像输出高概率，为生成图像输出低概率。

网络结构:
    图像 -> 卷积层 -> 全连接层 -> 真/假概率

数学表示:
    D: x -> [0, 1]
    其中 x 是图像，输出是图像为真实的概率
"""

import torch
import torch.nn as nn
from typing import List


class Discriminator(nn.Module):
    """
    GAN 判别器

    区分真实图像和生成图像。

    参数:
        img_channels: 输入图像通道数 (1=灰度, 3=RGB)
        img_size: 输入图像尺寸
        hidden_dims: 隐藏层维度列表
    """

    def __init__(
        self,
        img_channels: int = 1,
        img_size: int = 28,
        hidden_dims: List[int] = None
    ):
        super(Discriminator, self).__init__()

        self.img_channels = img_channels
        self.img_size = img_size

        if hidden_dims is None:
            hidden_dims = [128, 256, 512]

        # 构建卷积层
        layers = []
        in_channels = img_channels

        for out_channels in hidden_dims:
            layers.extend([
                nn.Conv2d(in_channels, out_channels, 4, 2, 1),
                nn.LeakyReLU(0.2, inplace=True),
                nn.Dropout2d(0.25)
            ])
            in_channels = out_channels

        self.network = nn.Sequential(*layers)

        # 计算卷积后的特征图大小
        self.feature_size = img_size // (2 ** len(hidden_dims))

        # 分类层
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dims[-1] * self.feature_size * self.feature_size, 1),
            nn.Sigmoid()
        )

        # 权重初始化
        self._initialize_weights()

    def _initialize_weights(self):
        """初始化网络权重"""
        for m in self.modules():
            if isinstance(m, (nn.Conv2d, nn.ConvTranspose2d)):
                nn.init.normal_(m.weight, 0.0, 0.02)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.normal_(m.weight, 1.0, 0.02)
                nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0.0, 0.02)
                nn.init.zeros_(m.bias)

    def forward(self, img: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        参数:
            img: 输入图像，形状为 (batch_size, img_channels, img_size, img_size)

        返回:
            图像为真实的概率，形状为 (batch_size, 1)
        """
        # 卷积特征提取
        features = self.network(img)

        # 展平
        features = features.view(features.size(0), -1)

        # 分类
        validity = self.classifier(features)

        return validity

    def predict(self, img: torch.Tensor) -> torch.Tensor:
        """
        预测图像是否为真实图像

        参数:
            img: 输入图像，形状为 (batch_size, img_channels, img_size, img_size)

        返回:
            预测结果 (True=真实, False=生成)
        """
        self.eval()
        with torch.no_grad():
            validity = self.forward(img)
            return validity > 0.5

    def get_features(self, img: torch.Tensor) -> torch.Tensor:
        """
        提取图像特征

        参数:
            img: 输入图像

        返回:
            特征向量
        """
        self.eval()
        with torch.no_grad():
            features = self.network(img)
            return features.view(features.size(0), -1)

    def __repr__(self) -> str:
        """返回判别器的字符串表示"""
        return (f"Discriminator(img_channels={self.img_channels}, "
                f"img_size={self.img_size})")
