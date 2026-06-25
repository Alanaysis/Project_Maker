"""
GAN 生成对抗网络模块
===================

实现完整的 GAN 框架，整合生成器和判别器。

GAN 的核心思想:
    生成器 G 和判别器 D 进行极小极大博弈：
    min_G max_D V(D, G) = E[log D(x)] + E[log(1 - D(G(z)))]

训练过程:
    1. 训练判别器: 最大化 log D(x) + log(1 - D(G(z)))
    2. 训练生成器: 最大化 log D(G(z))

损失函数:
    - 判别器损失: -[log D(x) + log(1 - D(G(z)))]
    - 生成器损失: -log D(G(z))
"""

import torch
import torch.nn as nn
import torch.optim as optim
from typing import Tuple, Dict, Optional

from .generator import Generator
from .discriminator import Discriminator


class GAN(nn.Module):
    """
    生成对抗网络

    整合生成器和判别器，提供训练接口。

    参数:
        latent_dim: 噪声向量维度
        img_channels: 图像通道数
        img_size: 图像尺寸
        lr: 学习率
        beta1: Adam 优化器的 beta1 参数
        beta2: Adam 优化器的 beta2 参数
    """

    def __init__(
        self,
        latent_dim: int = 100,
        img_channels: int = 1,
        img_size: int = 28,
        lr: float = 0.0002,
        beta1: float = 0.5,
        beta2: float = 0.999
    ):
        super(GAN, self).__init__()

        self.latent_dim = latent_dim
        self.img_channels = img_channels
        self.img_size = img_size

        # 创建生成器和判别器
        self.generator = Generator(
            latent_dim=latent_dim,
            img_channels=img_channels,
            img_size=img_size
        )

        self.discriminator = Discriminator(
            img_channels=img_channels,
            img_size=img_size
        )

        # 损失函数
        self.adversarial_loss = nn.BCELoss()

        # 优化器
        self.optimizer_G = optim.Adam(
            self.generator.parameters(),
            lr=lr,
            betas=(beta1, beta2)
        )

        self.optimizer_D = optim.Adam(
            self.discriminator.parameters(),
            lr=lr,
            betas=(beta1, beta2)
        )

        # 训练统计
        self.training_stats = {
            "d_loss": [],
            "g_loss": [],
            "d_real_acc": [],
            "d_fake_acc": []
        }

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """
        前向传播 (仅生成器)

        参数:
            z: 随机噪声向量

        返回:
            生成的图像
        """
        return self.generator(z)

    def train_discriminator(
        self,
        real_images: torch.Tensor,
        batch_size: int
    ) -> Dict[str, float]:
        """
        训练判别器

        参数:
            real_images: 真实图像，形状为 (batch_size, img_channels, img_size, img_size)
            batch_size: 批次大小

        返回:
            训练统计字典
        """
        # 标签
        real_labels = torch.ones(batch_size, 1, device=real_images.device)
        fake_labels = torch.zeros(batch_size, 1, device=real_images.device)

        # 清空梯度
        self.optimizer_D.zero_grad()

        # 真实图像损失
        real_output = self.discriminator(real_images)
        d_real_loss = self.adversarial_loss(real_output, real_labels)

        # 生成假图像
        z = self.generator.sample_noise(batch_size, real_images.device)
        fake_images = self.generator(z)

        # 假图像损失 (detach 防止梯度传到生成器)
        fake_output = self.discriminator(fake_images.detach())
        d_fake_loss = self.adversarial_loss(fake_output, fake_labels)

        # 总损失
        d_loss = (d_real_loss + d_fake_loss) / 2

        # 反向传播和优化
        d_loss.backward()
        self.optimizer_D.step()

        # 计算准确率
        d_real_acc = (real_output > 0.5).float().mean().item()
        d_fake_acc = (fake_output < 0.5).float().mean().item()

        return {
            "d_loss": d_loss.item(),
            "d_real_loss": d_real_loss.item(),
            "d_fake_loss": d_fake_loss.item(),
            "d_real_acc": d_real_acc,
            "d_fake_acc": d_fake_acc
        }

    def train_generator(
        self,
        batch_size: int,
        device: str
    ) -> Dict[str, float]:
        """
        训练生成器

        参数:
            batch_size: 批次大小
            device: 设备类型

        返回:
            训练统计字典
        """
        # 标签 (生成器希望判别器认为假图像是真实的)
        real_labels = torch.ones(batch_size, 1, device=device)

        # 清空梯度
        self.optimizer_G.zero_grad()

        # 生成假图像
        z = self.generator.sample_noise(batch_size, device)
        fake_images = self.generator(z)

        # 生成器损失
        fake_output = self.discriminator(fake_images)
        g_loss = self.adversarial_loss(fake_output, real_labels)

        # 反向传播和优化
        g_loss.backward()
        self.optimizer_G.step()

        return {
            "g_loss": g_loss.item()
        }

    def train_step(
        self,
        real_images: torch.Tensor
    ) -> Dict[str, float]:
        """
        执行一步训练

        参数:
            real_images: 真实图像批次

        返回:
            训练统计字典
        """
        batch_size = real_images.size(0)
        device = real_images.device

        # 训练判别器
        d_stats = self.train_discriminator(real_images, batch_size)

        # 训练生成器
        g_stats = self.train_generator(batch_size, device)

        # 合并统计
        stats = {**d_stats, **g_stats}

        # 记录统计
        self.training_stats["d_loss"].append(stats["d_loss"])
        self.training_stats["g_loss"].append(stats["g_loss"])
        self.training_stats["d_real_acc"].append(stats["d_real_acc"])
        self.training_stats["d_fake_acc"].append(stats["d_fake_acc"])

        return stats

    def generate_samples(
        self,
        n_samples: int = 16,
        device: str = "cpu"
    ) -> torch.Tensor:
        """
        生成样本

        参数:
            n_samples: 样本数量
            device: 设备类型

        返回:
            生成的图像，形状为 (n_samples, img_channels, img_size, img_size)
        """
        self.eval()
        with torch.no_grad():
            z = self.generator.sample_noise(n_samples, device)
            return self.generator(z)

    def get_training_stats(self) -> Dict[str, list]:
        """
        获取训练统计

        返回:
            训练统计字典
        """
        return self.training_stats

    def reset_training_stats(self):
        """重置训练统计"""
        self.training_stats = {
            "d_loss": [],
            "g_loss": [],
            "d_real_acc": [],
            "d_fake_acc": []
        }

    def __repr__(self) -> str:
        """返回 GAN 的字符串表示"""
        return (f"GAN(latent_dim={self.latent_dim}, "
                f"img_channels={self.img_channels}, "
                f"img_size={self.img_size})")
