"""
超分辨率模型训练器

实现 SRCNN 和 ESPCN 模型的训练流程
"""

import os
import time
from typing import Dict, Optional

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from tqdm import tqdm

from .models import get_model
from .dataset import SRDataset


class SRTrainer:
    """
    超分辨率模型训练器

    实现完整的训练流程，包括：
    - 模型初始化
    - 数据加载
    - 训练循环
    - 验证
    - 模型保存

    Args:
        model_name (str): 模型名称，可选 'srcnn', 'espcn', 'edsr'
        scale_factor (int): 缩放因子，默认 2
        device (str): 设备，'cuda' 或 'cpu'
        learning_rate (float): 学习率，默认 1e-4
        checkpoint_dir (str): 模型保存目录
    """

    def __init__(
        self,
        model_name: str = 'srcnn',
        scale_factor: int = 2,
        device: Optional[str] = None,
        learning_rate: float = 1e-4,
        checkpoint_dir: str = 'checkpoints'
    ):
        self.model_name = model_name
        self.scale_factor = scale_factor
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.learning_rate = learning_rate
        self.checkpoint_dir = checkpoint_dir

        # 创建模型
        self.model = get_model(model_name, scale_factor=scale_factor)
        self.model.to(self.device)

        # 损失函数
        self.criterion = nn.MSELoss()

        # 优化器
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=learning_rate,
            betas=(0.9, 0.999)
        )

        # 学习率调度器
        self.scheduler = optim.lr_scheduler.StepLR(
            self.optimizer,
            step_size=20,
            gamma=0.5
        )

        # 创建保存目录
        os.makedirs(checkpoint_dir, exist_ok=True)

        # 训练历史
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'learning_rate': []
        }

    def train(
        self,
        train_dir: str,
        val_dir: Optional[str] = None,
        epochs: int = 100,
        batch_size: int = 16,
        patch_size: int = 96,
        num_workers: int = 4
    ) -> Dict:
        """
        训练模型

        Args:
            train_dir (str): 训练数据目录
            val_dir (str): 验证数据目录（可选）
            epochs (int): 训练轮数
            batch_size (int): 批次大小
            patch_size (int): 训练块大小
            num_workers (int): 数据加载线程数

        Returns:
            Dict: 训练历史
        """
        # 创建数据集
        train_dataset = SRDataset(
            train_dir,
            scale_factor=self.scale_factor,
            patch_size=patch_size,
            is_training=True,
            augment=True
        )

        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=True
        )

        # 验证数据集
        val_loader = None
        if val_dir:
            val_dataset = SRDataset(
                val_dir,
                scale_factor=self.scale_factor,
                patch_size=patch_size,
                is_training=False,
                augment=False
            )

            val_loader = DataLoader(
                val_dataset,
                batch_size=batch_size,
                shuffle=False,
                num_workers=num_workers,
                pin_memory=True
            )

        # 训练循环
        best_val_loss = float('inf')

        for epoch in range(epochs):
            # 训练
            train_loss = self._train_epoch(train_loader, epoch, epochs)
            self.history['train_loss'].append(train_loss)

            # 验证
            val_loss = None
            if val_loader:
                val_loss = self._validate(val_loader)
                self.history['val_loss'].append(val_loss)

            # 更新学习率
            self.scheduler.step()
            self.history['learning_rate'].append(self.optimizer.param_groups[0]['lr'])

            # 保存最佳模型
            if val_loss and val_loss < best_val_loss:
                best_val_loss = val_loss
                self._save_checkpoint(epoch, is_best=True)

            # 定期保存模型
            if (epoch + 1) % 10 == 0:
                self._save_checkpoint(epoch)

            # 打印训练信息
            self._print_epoch_info(epoch, epochs, train_loss, val_loss)

        # 训练结束时保存最终模型
        self._save_checkpoint(epochs - 1)

        return self.history

    def _train_epoch(
        self,
        train_loader: DataLoader,
        epoch: int,
        total_epochs: int
    ) -> float:
        """
        训练一个 epoch

        Args:
            train_loader (DataLoader): 训练数据加载器
            epoch (int): 当前 epoch
            total_epochs (int): 总 epoch 数

        Returns:
            float: 平均训练损失
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        # 进度条
        pbar = tqdm(train_loader, desc=f'Epoch {epoch+1}/{total_epochs}')

        for lr_images, hr_images in pbar:
            # 移动到设备
            lr_images = lr_images.to(self.device)
            hr_images = hr_images.to(self.device)

            # 对于 SRCNN，需要先上采样低分辨率图像
            if self.model_name == 'srcnn':
                lr_images = torch.nn.functional.interpolate(
                    lr_images,
                    size=hr_images.shape[2:],
                    mode='bicubic',
                    align_corners=False
                )

            # 前向传播
            outputs = self.model(lr_images)
            loss = self.criterion(outputs, hr_images)

            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            # 更新统计
            total_loss += loss.item()
            num_batches += 1

            # 更新进度条
            pbar.set_postfix({'loss': f'{loss.item():.4f}'})

        return total_loss / num_batches

    def _validate(self, val_loader: DataLoader) -> float:
        """
        验证模型

        Args:
            val_loader (DataLoader): 验证数据加载器

        Returns:
            float: 平均验证损失
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for lr_images, hr_images in val_loader:
                # 移动到设备
                lr_images = lr_images.to(self.device)
                hr_images = hr_images.to(self.device)

                # 对于 SRCNN，需要先上采样低分辨率图像
                if self.model_name == 'srcnn':
                    lr_images = torch.nn.functional.interpolate(
                        lr_images,
                        size=hr_images.shape[2:],
                        mode='bicubic',
                        align_corners=False
                    )

                # 前向传播
                outputs = self.model(lr_images)
                loss = self.criterion(outputs, hr_images)

                # 更新统计
                total_loss += loss.item()
                num_batches += 1

        return total_loss / num_batches

    def _save_checkpoint(self, epoch: int, is_best: bool = False):
        """
        保存模型检查点

        Args:
            epoch (int): 当前 epoch
            is_best (bool): 是否为最佳模型
        """
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'history': self.history
        }

        # 保存最新模型
        torch.save(checkpoint, os.path.join(self.checkpoint_dir, 'latest.pth'))

        # 保存最佳模型
        if is_best:
            torch.save(checkpoint, os.path.join(self.checkpoint_dir, 'best.pth'))

        # 保存定期模型
        torch.save(checkpoint, os.path.join(self.checkpoint_dir, f'epoch_{epoch+1}.pth'))

    def _print_epoch_info(
        self,
        epoch: int,
        total_epochs: int,
        train_loss: float,
        val_loss: Optional[float]
    ):
        """
        打印训练信息

        Args:
            epoch (int): 当前 epoch
            total_epochs (int): 总 epoch 数
            train_loss (float): 训练损失
            val_loss (float): 验证损失
        """
        lr = self.optimizer.param_groups[0]['lr']

        info = f'Epoch {epoch+1}/{total_epochs} - '
        info += f'Train Loss: {train_loss:.4f} - '
        info += f'LR: {lr:.6f}'

        if val_loss is not None:
            info += f' - Val Loss: {val_loss:.4f}'

        print(info)

    def load_checkpoint(self, checkpoint_path: str):
        """
        加载模型检查点

        Args:
            checkpoint_path (str): 检查点文件路径
        """
        checkpoint = torch.load(checkpoint_path, map_location=self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        self.history = checkpoint['history']

        print(f"Loaded checkpoint from epoch {checkpoint['epoch']+1}")

    def get_model_summary(self) -> str:
        """
        获取模型摘要

        Returns:
            str: 模型摘要信息
        """
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)

        summary = f"Model: {self.model_name}\n"
        summary += f"Scale Factor: {self.scale_factor}x\n"
        summary += f"Total Parameters: {total_params:,}\n"
        summary += f"Trainable Parameters: {trainable_params:,}\n"
        summary += f"Device: {self.device}\n"

        return summary
