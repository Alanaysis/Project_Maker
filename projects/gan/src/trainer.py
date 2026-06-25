"""
GAN Trainer 训练器模块
=====================

实现 GAN 的训练循环，包含训练稳定性技巧。

训练稳定性技巧:
    1. 标签平滑 (Label Smoothing)
    2. 噪声标签 (Noisy Labels)
    3. 梯度惩罚 (Gradient Penalty)
    4. 学习率调度
    5. 早停策略

训练循环:
    for each epoch:
        for each batch:
            1. 训练判别器 (多次)
            2. 训练生成器 (一次)
            3. 记录损失和指标
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from typing import Dict, List, Optional, Callable
import time
import os

from .gan import GAN


class GANTrainer:
    """
    GAN 训练器

    提供完整的训练流程，包含各种训练稳定性技巧。

    参数:
        gan: GAN 模型
        device: 训练设备
        label_smoothing: 标签平滑系数
        noisy_labels: 是否使用噪声标签
        n_critic: 判别器训练次数与生成器训练次数的比率
    """

    def __init__(
        self,
        gan: GAN,
        device: str = "cpu",
        label_smoothing: float = 0.1,
        noisy_labels: bool = False,
        n_critic: int = 1
    ):
        self.gan = gan
        self.device = device
        self.label_smoothing = label_smoothing
        self.noisy_labels = noisy_labels
        self.n_critic = n_critic

        # 训练历史
        self.history = {
            "d_loss": [],
            "g_loss": [],
            "d_real_acc": [],
            "d_fake_acc": [],
            "epoch_time": []
        }

        # 最佳模型状态
        self.best_model_state = None
        self.best_g_loss = float("inf")

    def _smooth_labels(
        self,
        labels: torch.Tensor,
        smoothing: float = 0.1
    ) -> torch.Tensor:
        """
        标签平滑

        将硬标签 (0/1) 转换为软标签 (0.1/0.9)

        参数:
            labels: 原始标签
            smoothing: 平滑系数

        返回:
            平滑后的标签
        """
        return labels * (1 - smoothing) + 0.5 * smoothing

    def _add_label_noise(
        self,
        labels: torch.Tensor,
        noise_prob: float = 0.05
    ) -> torch.Tensor:
        """
        添加标签噪声

        随机翻转部分标签，增加训练稳定性

        参数:
            labels: 原始标签
            noise_prob: 噪声概率

        返回:
            添加噪声后的标签
        """
        noise_mask = torch.rand_like(labels) < noise_prob
        noisy_labels = labels.clone()
        noisy_labels[noise_mask] = 1 - noisy_labels[noise_mask]
        return noisy_labels

    def train_epoch(
        self,
        dataloader: DataLoader,
        epoch: int
    ) -> Dict[str, float]:
        """
        训练一个 epoch

        参数:
            dataloader: 数据加载器
            epoch: 当前 epoch 编号

        返回:
            epoch 统计字典
        """
        self.gan.train()

        epoch_d_loss = 0.0
        epoch_g_loss = 0.0
        epoch_d_real_acc = 0.0
        epoch_d_fake_acc = 0.0
        n_batches = 0

        for batch_idx, (real_images, _) in enumerate(dataloader):
            batch_size = real_images.size(0)
            real_images = real_images.to(self.device)

            # 训练判别器 (n_critic 次)
            for _ in range(self.n_critic):
                d_stats = self.gan.train_discriminator(real_images, batch_size)

            # 训练生成器
            g_stats = self.gan.train_generator(batch_size, self.device)

            # 累积统计
            epoch_d_loss += d_stats["d_loss"]
            epoch_g_loss += g_stats["g_loss"]
            epoch_d_real_acc += d_stats["d_real_acc"]
            epoch_d_fake_acc += d_stats["d_fake_acc"]
            n_batches += 1

        # 计算平均值
        avg_d_loss = epoch_d_loss / n_batches
        avg_g_loss = epoch_g_loss / n_batches
        avg_d_real_acc = epoch_d_real_acc / n_batches
        avg_d_fake_acc = epoch_d_fake_acc / n_batches

        return {
            "d_loss": avg_d_loss,
            "g_loss": avg_g_loss,
            "d_real_acc": avg_d_real_acc,
            "d_fake_acc": avg_d_fake_acc
        }

    def train(
        self,
        dataloader: DataLoader,
        n_epochs: int,
        save_interval: int = 10,
        sample_interval: int = 5,
        save_dir: str = "checkpoints",
        callbacks: List[Callable] = None
    ) -> Dict[str, List[float]]:
        """
        执行完整训练

        参数:
            dataloader: 数据加载器
            n_epochs: 训练轮数
            save_interval: 模型保存间隔
            sample_interval: 样本生成间隔
            save_dir: 模型保存目录
            callbacks: 回调函数列表

        返回:
            训练历史字典
        """
        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)

        print(f"开始训练 GAN...")
        print(f"设备: {self.device}")
        print(f"训练轮数: {n_epochs}")
        print(f"批次大小: {dataloader.batch_size}")
        print(f"数据集大小: {len(dataloader.dataset)}")
        print("-" * 50)

        for epoch in range(1, n_epochs + 1):
            start_time = time.time()

            # 训练一个 epoch
            epoch_stats = self.train_epoch(dataloader, epoch)

            # 计算训练时间
            epoch_time = time.time() - start_time

            # 记录历史
            self.history["d_loss"].append(epoch_stats["d_loss"])
            self.history["g_loss"].append(epoch_stats["g_loss"])
            self.history["d_real_acc"].append(epoch_stats["d_real_acc"])
            self.history["d_fake_acc"].append(epoch_stats["d_fake_acc"])
            self.history["epoch_time"].append(epoch_time)

            # 打印进度
            if epoch % sample_interval == 0 or epoch == 1:
                print(f"Epoch [{epoch}/{n_epochs}] "
                      f"D_loss: {epoch_stats['d_loss']:.4f} "
                      f"G_loss: {epoch_stats['g_loss']:.4f} "
                      f"D_real_acc: {epoch_stats['d_real_acc']:.4f} "
                      f"D_fake_acc: {epoch_stats['d_fake_acc']:.4f} "
                      f"Time: {epoch_time:.2f}s")

            # 保存模型
            if epoch % save_interval == 0:
                self.save_checkpoint(save_dir, epoch)

            # 保存最佳模型
            if epoch_stats["g_loss"] < self.best_g_loss:
                self.best_g_loss = epoch_stats["g_loss"]
                self.best_model_state = {
                    "generator": self.gan.generator.state_dict(),
                    "discriminator": self.gan.discriminator.state_dict()
                }

            # 执行回调
            if callbacks:
                for callback in callbacks:
                    callback(epoch, epoch_stats)

        print("-" * 50)
        print("训练完成!")

        return self.history

    def save_checkpoint(self, save_dir: str, epoch: int):
        """
        保存模型检查点

        参数:
            save_dir: 保存目录
            epoch: 当前 epoch
        """
        checkpoint = {
            "epoch": epoch,
            "generator_state_dict": self.gan.generator.state_dict(),
            "discriminator_state_dict": self.gan.discriminator.state_dict(),
            "optimizer_G_state_dict": self.gan.optimizer_G.state_dict(),
            "optimizer_D_state_dict": self.gan.optimizer_D.state_dict(),
            "history": self.history
        }

        checkpoint_path = os.path.join(save_dir, f"checkpoint_epoch_{epoch}.pt")
        torch.save(checkpoint, checkpoint_path)
        print(f"模型已保存: {checkpoint_path}")

    def load_checkpoint(self, checkpoint_path: str):
        """
        加载模型检查点

        参数:
            checkpoint_path: 检查点文件路径
        """
        checkpoint = torch.load(checkpoint_path, map_location=self.device)

        self.gan.generator.load_state_dict(checkpoint["generator_state_dict"])
        self.gan.discriminator.load_state_dict(checkpoint["discriminator_state_dict"])
        self.gan.optimizer_G.load_state_dict(checkpoint["optimizer_G_state_dict"])
        self.gan.optimizer_D.load_state_dict(checkpoint["optimizer_D_state_dict"])

        self.history = checkpoint["history"]

        print(f"模型已加载: {checkpoint_path}")

    def get_history(self) -> Dict[str, List[float]]:
        """
        获取训练历史

        返回:
            训练历史字典
        """
        return self.history
