"""
GAN 测试套件
============

测试 GAN 的各个组件：
- Generator 生成器
- Discriminator 判别器
- GAN 整体框架
- Trainer 训练器

测试内容：
- 网络结构正确性
- 前向传播形状
- 梯度流动
- 训练循环
"""

import pytest
import torch
import torch.nn as nn
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.generator import Generator
from src.discriminator import Discriminator
from src.gan import GAN


class TestGenerator:
    """生成器测试类"""

    def setup_method(self):
        """测试前准备"""
        self.latent_dim = 100
        self.img_channels = 1
        self.img_size = 28
        self.batch_size = 4

        self.generator = Generator(
            latent_dim=self.latent_dim,
            img_channels=self.img_channels,
            img_size=self.img_size
        )

    def test_generator_initialization(self):
        """测试生成器初始化"""
        assert self.generator.latent_dim == self.latent_dim
        assert self.generator.img_channels == self.img_channels
        assert self.generator.img_size == self.img_size

    def test_generator_forward(self):
        """测试生成器前向传播"""
        z = torch.randn(self.batch_size, self.latent_dim)
        output = self.generator(z)

        # 检查输出形状
        assert output.shape == (self.batch_size, self.img_channels, self.img_size, self.img_size)

        # 检查输出范围 (Tanh 输出范围 [-1, 1])
        assert output.min() >= -1.0
        assert output.max() <= 1.0

    def test_generator_sample_noise(self):
        """测试噪声采样"""
        z = self.generator.sample_noise(self.batch_size)

        # 检查形状
        assert z.shape == (self.batch_size, self.latent_dim)

        # 检查分布 (应该近似标准正态分布)
        assert abs(z.mean()) < 0.5
        assert abs(z.std() - 1.0) < 0.5

    def test_generator_generate(self):
        """测试图像生成"""
        self.generator.eval()
        images = self.generator.generate(batch_size=self.batch_size)

        # 检查形状
        assert images.shape == (self.batch_size, self.img_channels, self.img_size, self.img_size)

    def test_generator_gradient_flow(self):
        """测试梯度流动"""
        z = torch.randn(self.batch_size, self.latent_dim, requires_grad=True)
        output = self.generator(z)

        # 计算损失并反向传播
        loss = output.mean()
        loss.backward()

        # 检查梯度存在
        assert z.grad is not None
        assert z.grad.shape == z.shape

    def test_generator_repr(self):
        """测试字符串表示"""
        repr_str = repr(self.generator)
        assert "Generator" in repr_str
        assert str(self.latent_dim) in repr_str


class TestDiscriminator:
    """判别器测试类"""

    def setup_method(self):
        """测试前准备"""
        self.img_channels = 1
        self.img_size = 28
        self.batch_size = 4

        self.discriminator = Discriminator(
            img_channels=self.img_channels,
            img_size=self.img_size
        )

    def test_discriminator_initialization(self):
        """测试判别器初始化"""
        assert self.discriminator.img_channels == self.img_channels
        assert self.discriminator.img_size == self.img_size

    def test_discriminator_forward(self):
        """测试判别器前向传播"""
        # 创建随机图像
        img = torch.randn(self.batch_size, self.img_channels, self.img_size, self.img_size)
        output = self.discriminator(img)

        # 检查输出形状
        assert output.shape == (self.batch_size, 1)

        # 检查输出范围 (Sigmoid 输出范围 [0, 1])
        assert output.min() >= 0.0
        assert output.max() <= 1.0

    def test_discriminator_predict(self):
        """测试判别器预测"""
        img = torch.randn(self.batch_size, self.img_channels, self.img_size, self.img_size)
        predictions = self.discriminator.predict(img)

        # 检查输出形状
        assert predictions.shape == (self.batch_size, 1)

        # 检查输出类型 (布尔值)
        assert predictions.dtype == torch.bool

    def test_discriminator_get_features(self):
        """测试特征提取"""
        img = torch.randn(self.batch_size, self.img_channels, self.img_size, self.img_size)
        features = self.discriminator.get_features(img)

        # 检查特征形状
        assert features.shape[0] == self.batch_size
        assert len(features.shape) == 2  # (batch_size, feature_dim)

    def test_discriminator_gradient_flow(self):
        """测试梯度流动"""
        img = torch.randn(self.batch_size, self.img_channels, self.img_size, self.img_size, requires_grad=True)
        output = self.discriminator(img)

        # 计算损失并反向传播
        loss = output.mean()
        loss.backward()

        # 检查梯度存在
        assert img.grad is not None
        assert img.grad.shape == img.shape

    def test_discriminator_repr(self):
        """测试字符串表示"""
        repr_str = repr(self.discriminator)
        assert "Discriminator" in repr_str


class TestGAN:
    """GAN 整体测试类"""

    def setup_method(self):
        """测试前准备"""
        self.latent_dim = 100
        self.img_channels = 1
        self.img_size = 28
        self.batch_size = 4

        self.gan = GAN(
            latent_dim=self.latent_dim,
            img_channels=self.img_channels,
            img_size=self.img_size
        )

    def test_gan_initialization(self):
        """测试 GAN 初始化"""
        assert self.gan.latent_dim == self.latent_dim
        assert self.gan.img_channels == self.img_channels
        assert self.gan.img_size == self.img_size

        # 检查生成器和判别器
        assert isinstance(self.gan.generator, Generator)
        assert isinstance(self.gan.discriminator, Discriminator)

    def test_gan_forward(self):
        """测试 GAN 前向传播"""
        z = torch.randn(self.batch_size, self.latent_dim)
        output = self.gan(z)

        # 检查输出形状
        assert output.shape == (self.batch_size, self.img_channels, self.img_size, self.img_size)

    def test_gan_train_discriminator(self):
        """测试判别器训练"""
        # 创建真实图像
        real_images = torch.randn(self.batch_size, self.img_channels, self.img_size, self.img_size)

        # 训练判别器
        d_stats = self.gan.train_discriminator(real_images, self.batch_size)

        # 检查返回的统计信息
        assert "d_loss" in d_stats
        assert "d_real_loss" in d_stats
        assert "d_fake_loss" in d_stats
        assert "d_real_acc" in d_stats
        assert "d_fake_acc" in d_stats

        # 检查损失值
        assert d_stats["d_loss"] >= 0.0

    def test_gan_train_generator(self):
        """测试生成器训练"""
        device = "cpu"

        # 训练生成器
        g_stats = self.gan.train_generator(self.batch_size, device)

        # 检查返回的统计信息
        assert "g_loss" in g_stats

        # 检查损失值
        assert g_stats["g_loss"] >= 0.0

    def test_gan_train_step(self):
        """测试一步训练"""
        # 创建真实图像
        real_images = torch.randn(self.batch_size, self.img_channels, self.img_size, self.img_size)

        # 执行一步训练
        stats = self.gan.train_step(real_images)

        # 检查返回的统计信息
        assert "d_loss" in stats
        assert "g_loss" in stats
        assert "d_real_acc" in stats
        assert "d_fake_acc" in stats

    def test_gan_generate_samples(self):
        """测试样本生成"""
        n_samples = 8
        samples = self.gan.generate_samples(n_samples=n_samples)

        # 检查输出形状
        assert samples.shape == (n_samples, self.img_channels, self.img_size, self.img_size)

    def test_gan_training_stats(self):
        """测试训练统计"""
        # 执行几次训练步骤
        for _ in range(3):
            real_images = torch.randn(self.batch_size, self.img_channels, self.img_size, self.img_size)
            self.gan.train_step(real_images)

        # 获取统计信息
        stats = self.gan.get_training_stats()

        # 检查统计信息
        assert len(stats["d_loss"]) == 3
        assert len(stats["g_loss"]) == 3
        assert len(stats["d_real_acc"]) == 3
        assert len(stats["d_fake_acc"]) == 3

    def test_gan_reset_training_stats(self):
        """测试重置训练统计"""
        # 执行训练
        real_images = torch.randn(self.batch_size, self.img_channels, self.img_size, self.img_size)
        self.gan.train_step(real_images)

        # 重置统计
        self.gan.reset_training_stats()

        # 检查统计已清空
        stats = self.gan.get_training_stats()
        assert len(stats["d_loss"]) == 0

    def test_gan_repr(self):
        """测试字符串表示"""
        repr_str = repr(self.gan)
        assert "GAN" in repr_str
        assert str(self.latent_dim) in repr_str


class TestGANIntegration:
    """GAN 集成测试类"""

    def test_training_loop(self):
        """测试完整训练循环"""
        # 创建小型 GAN
        gan = GAN(
            latent_dim=50,
            img_channels=1,
            img_size=28,
            lr=0.0002
        )

        # 创建模拟数据
        batch_size = 8
        n_batches = 3

        # 模拟训练循环
        for epoch in range(2):
            for batch in range(n_batches):
                # 创建随机图像
                real_images = torch.randn(batch_size, 1, 28, 28)

                # 执行一步训练
                stats = gan.train_step(real_images)

                # 检查损失
                assert stats["d_loss"] >= 0.0
                assert stats["g_loss"] >= 0.0

        # 检查训练统计
        total_steps = 2 * n_batches
        assert len(gan.get_training_stats()["d_loss"]) == total_steps

    def test_gradient_accumulation(self):
        """测试梯度累积"""
        gan = GAN(latent_dim=50, img_channels=1, img_size=28)

        # 执行多次训练步骤
        for _ in range(5):
            real_images = torch.randn(4, 1, 28, 28)
            gan.train_step(real_images)

        # 检查梯度已更新
        for param in gan.generator.parameters():
            assert param.grad is not None or not param.requires_grad

    def test_model_save_load(self):
        """测试模型保存和加载"""
        import tempfile

        gan = GAN(latent_dim=50, img_channels=1, img_size=28)

        # 训练一步
        real_images = torch.randn(4, 1, 28, 28)
        gan.train_step(real_images)

        # 保存模型
        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
            checkpoint = {
                "generator": gan.generator.state_dict(),
                "discriminator": gan.discriminator.state_dict()
            }
            torch.save(checkpoint, f.name)

            # 加载模型
            loaded_checkpoint = torch.load(f.name)
            new_gan = GAN(latent_dim=50, img_channels=1, img_size=28)
            new_gan.generator.load_state_dict(loaded_checkpoint["generator"])
            new_gan.discriminator.load_state_dict(loaded_checkpoint["discriminator"])

            # 检查参数是否一致
            for p1, p2 in zip(gan.generator.parameters(), new_gan.generator.parameters()):
                assert torch.allclose(p1, p2)

            # 清理
            os.unlink(f.name)

    def test_device_transfer(self):
        """测试设备转移"""
        gan = GAN(latent_dim=50, img_channels=1, img_size=28)

        # 转移到 CPU
        gan = gan.to("cpu")

        # 训练一步
        real_images = torch.randn(4, 1, 28, 28)
        stats = gan.train_step(real_images)

        assert stats["d_loss"] >= 0.0

    def test_different_image_sizes(self):
        """测试不同图像尺寸"""
        for img_size in [28, 32, 64]:
            gan = GAN(
                latent_dim=50,
                img_channels=1,
                img_size=img_size
            )

            # 创建对应尺寸的图像
            real_images = torch.randn(4, 1, img_size, img_size)

            # 训练一步
            stats = gan.train_step(real_images)
            assert stats["d_loss"] >= 0.0

    def test_different_channels(self):
        """测试不同通道数"""
        for channels in [1, 3]:
            gan = GAN(
                latent_dim=50,
                img_channels=channels,
                img_size=32
            )

            # 创建对应通道数的图像
            real_images = torch.randn(4, channels, 32, 32)

            # 训练一步
            stats = gan.train_step(real_images)
            assert stats["d_loss"] >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
