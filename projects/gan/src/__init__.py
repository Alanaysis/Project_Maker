"""
GAN 生成对抗网络模块
===================

实现完整的生成对抗网络 (GAN)，包含：
- Generator: 生成器，从随机噪声生成图像
- Discriminator: 判别器，区分真实图像和生成图像
- GAN: 对抗训练框架

核心思想:
    生成器和判别器进行博弈训练。
    生成器试图生成逼真的图像欺骗判别器，
    判别器试图区分真实图像和生成图像。
    最终达到纳什均衡，生成器能够生成逼真的图像。
"""

from .generator import Generator
from .discriminator import Discriminator
from .gan import GAN
from .trainer import GANTrainer

__all__ = ["Generator", "Discriminator", "GAN", "GANTrainer"]

__version__ = "1.0.0"
