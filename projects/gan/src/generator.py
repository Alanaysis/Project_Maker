"""
Generator 生成器模块
===================

实现 GAN 的生成器网络，将随机噪声映射到图像空间。

生成器的核心任务:
    学习从低维噪声空间到高维图像空间的映射，
    生成尽可能逼真的图像以欺骗判别器。

网络结构:
    噪声向量 -> 全连接层 -> 反卷积层 -> 生成图像

数学表示:
    G: z -> x_fake
    其中 z ~ N(0,1) 是随机噪声，x_fake 是生成的图像
"""

import torch
import torch.nn as nn
from typing import Tuple


class Generator(nn.Module):
    """
    GAN 生成器

    将随机噪声向量映射到图像空间。

    参数:
        latent_dim: 噪声向量维度
        img_channels: 输出图像通道数 (1=灰度, 3=RGB)
        img_size: 输出图像尺寸
        hidden_dims: 隐藏层维度列表
    """

    def __init__(
        self,
        latent_dim: int = 100,
        img_channels: int = 1,
        img_size: int = 28,
        hidden_dims: list = None
    ):
        super(Generator, self).__init__()

        self.latent_dim = latent_dim
        self.img_channels = img_channels
        self.img_size = img_size

        if hidden_dims is None:
            hidden_dims = [256, 512]

        self.hidden_dims = hidden_dims

        # 计算初始空间大小
        self.init_size = img_size // 4
        self.fc = nn.Linear(latent_dim, hidden_dims[0] * self.init_size * self.init_size)

        # 构建反卷积层
        layers = []
        in_channels = hidden_dims[0]

        for i, out_channels in enumerate(hidden_dims[1:], 1):
            layers.extend([
                nn.ConvTranspose2d(in_channels, out_channels, 4, 2, 1),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True)
            ])
            in_channels = out_channels

        # 最后一层，输出图像
        layers.extend([
            nn.ConvTranspose2d(in_channels, img_channels, 4, 2, 1),
            nn.Tanh()  # 输出范围 [-1, 1]
        ])

        self.network = nn.Sequential(*layers)

        # 权重初始化
        self._initialize_weights()

    def _initialize_weights(self):
        """初始化网络权重"""
        for m in self.modules():
            if isinstance(m, (nn.ConvTranspose2d, nn.Conv2d)):
                nn.init.normal_(m.weight, 0.0, 0.02)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.normal_(m.weight, 1.0, 0.02)
                nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0.0, 0.02)
                nn.init.zeros_(m.bias)

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        参数:
            z: 随机噪声向量，形状为 (batch_size, latent_dim)

        返回:
            生成的图像，形状为 (batch_size, img_channels, img_size, img_size)
        """
        # 全连接层
        out = self.fc(z)
        out = out.view(-1, self.hidden_dims[0], self.init_size, self.init_size)

        # 反卷积层
        img = self.network(out)

        return img

    def sample_noise(self, batch_size: int, device: str = "cpu") -> torch.Tensor:
        """
        生成随机噪声

        参数:
            batch_size: 批次大小
            device: 设备类型 ("cpu" 或 "cuda")

        返回:
            随机噪声向量，形状为 (batch_size, latent_dim)
        """
        return torch.randn(batch_size, self.latent_dim, device=device)

    def generate(self, batch_size: int = 1, device: str = "cpu") -> torch.Tensor:
        """
        生成图像

        参数:
            batch_size: 批次大小
            device: 设备类型

        返回:
            生成的图像，形状为 (batch_size, img_channels, img_size, img_size)
        """
        self.eval()
        with torch.no_grad():
            z = self.sample_noise(batch_size, device)
            return self.forward(z)

    def __repr__(self) -> str:
        """返回生成器的字符串表示"""
        return (f"Generator(latent_dim={self.latent_dim}, "
                f"img_channels={self.img_channels}, "
                f"img_size={self.img_size})")
