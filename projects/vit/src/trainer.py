"""
ViT 训练器

提供完整的训练、验证和评估功能。
支持 MNIST / CIFAR-10 等数据集。

训练技巧：
- AdamW 优化器（带权重衰减）
- Cosine Annealing 学习率调度
- 数据增强（随机裁剪、翻转、归一化）
- Label Smoothing
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from typing import Optional, Tuple, Dict, List
import time
import os


def get_mnist_transforms(img_size: int = 28) -> Tuple[transforms.Compose, transforms.Compose]:
    """
    获取 MNIST 数据集的预处理变换

    MNIST 是灰度图像 (1x28x28)，需要调整为 ViT 输入格式。

    参数：
        img_size: 目标图像尺寸
    """
    train_transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.RandomCrop(img_size, padding=2),  # 随机裁剪（数据增强）
        transforms.RandomRotation(10),  # 随机旋转（数据增强）
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,)),  # MNIST 均值和标准差
    ])

    val_transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,)),
    ])

    return train_transform, val_transform


def get_cifar10_transforms(img_size: int = 32) -> Tuple[transforms.Compose, transforms.Compose]:
    """
    获取 CIFAR-10 数据集的预处理变换

    CIFAR-10 是彩色图像 (3x32x32)。
    """
    train_transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.RandomCrop(img_size, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
    ])

    return train_transform, val_transform


class ViTTrainer:
    """
    Vision Transformer 训练器

    提供完整的训练循环，包括：
    - 训练和验证
    - 学习率调度
    - 模型保存和加载
    - 训练历史记录

    参数：
        model: ViT 模型
        train_loader: 训练数据加载器
        val_loader: 验证数据加载器
        lr: 学习率
        weight_decay: 权重衰减
        epochs: 训练轮数
        label_smoothing: 标签平滑系数
        device: 训练设备
    """

    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        lr: float = 3e-4,
        weight_decay: float = 0.01,
        epochs: int = 10,
        label_smoothing: float = 0.1,
        device: Optional[str] = None,
    ):
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.epochs = epochs
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')

        # 将模型移到指定设备
        self.model = self.model.to(self.device)

        # ★ AdamW 优化器：ViT 论文推荐使用 AdamW
        # 相比 Adam，AdamW 的权重衰减实现更正确
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=lr,
            weight_decay=weight_decay,
            betas=(0.9, 0.999),
        )

        # ★ Cosine Annealing 学习率调度
        # 学习率按照余弦函数从初始值逐渐衰减到 0
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=epochs,
        )

        # ★ 损失函数：带 Label Smoothing 的交叉熵
        # Label Smoothing 可以防止模型过度自信，提高泛化能力
        self.criterion = nn.CrossEntropyLoss(label_smoothing=label_smoothing)

        # 训练历史
        self.history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': [],
            'lr': [],
        }

    def train_one_epoch(self) -> Tuple[float, float]:
        """
        训练一个 epoch

        返回：
            avg_loss: 平均损失
            accuracy: 准确率
        """
        self.model.train()

        total_loss = 0.0
        correct = 0
        total = 0

        for batch_idx, (data, target) in enumerate(self.train_loader):
            data, target = data.to(self.device), target.to(self.device)

            # 前向传播
            output, _ = self.model(data)
            loss = self.criterion(output, target)

            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()

            # ★ 梯度裁剪：防止梯度爆炸
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

            self.optimizer.step()

            # 统计
            total_loss += loss.item()
            _, predicted = output.max(1)
            total += target.size(0)
            correct += predicted.eq(target).sum().item()

        avg_loss = total_loss / len(self.train_loader)
        accuracy = correct / total

        return avg_loss, accuracy

    @torch.no_grad()
    def validate(self) -> Tuple[float, float]:
        """
        验证模型

        返回：
            avg_loss: 平均损失
            accuracy: 准确率
        """
        self.model.eval()

        total_loss = 0.0
        correct = 0
        total = 0

        for data, target in self.val_loader:
            data, target = data.to(self.device), target.to(self.device)

            output, _ = self.model(data)
            loss = self.criterion(output, target)

            total_loss += loss.item()
            _, predicted = output.max(1)
            total += target.size(0)
            correct += predicted.eq(target).sum().item()

        avg_loss = total_loss / len(self.val_loader)
        accuracy = correct / total

        return avg_loss, accuracy

    def train(self, save_path: Optional[str] = None) -> Dict[str, List[float]]:
        """
        完整训练流程

        参数：
            save_path: 模型保存路径（None 表示不保存）

        返回：
            history: 训练历史字典
        """
        best_val_acc = 0.0

        print(f"Training on {self.device}")
        print(f"Model parameters: {sum(p.numel() for p in self.model.parameters()):,}")
        print("-" * 60)

        for epoch in range(1, self.epochs + 1):
            start_time = time.time()

            # 训练
            train_loss, train_acc = self.train_one_epoch()

            # 验证
            val_loss, val_acc = self.validate()

            # 更新学习率
            current_lr = self.optimizer.param_groups[0]['lr']
            self.scheduler.step()

            # 记录历史
            self.history['train_loss'].append(train_loss)
            self.history['train_acc'].append(train_acc)
            self.history['val_loss'].append(val_loss)
            self.history['val_acc'].append(val_acc)
            self.history['lr'].append(current_lr)

            elapsed = time.time() - start_time

            # 打印进度
            print(
                f"Epoch {epoch:3d}/{self.epochs} | "
                f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f} | "
                f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f} | "
                f"LR: {current_lr:.6f} | Time: {elapsed:.1f}s"
            )

            # 保存最佳模型
            if save_path and val_acc > best_val_acc:
                best_val_acc = val_acc
                torch.save(self.model.state_dict(), save_path)
                print(f"  -> Saved best model (val_acc={val_acc:.4f})")

        print("-" * 60)
        print(f"Training complete. Best validation accuracy: {best_val_acc:.4f}")

        return self.history

    @staticmethod
    def create_mnist_loaders(
        batch_size: int = 64,
        img_size: int = 28,
        data_dir: str = './data',
        num_workers: int = 0,
    ) -> Tuple[DataLoader, DataLoader]:
        """
        创建 MNIST 数据加载器

        参数：
            batch_size: 批次大小
            img_size: 图像尺寸
            data_dir: 数据目录
            num_workers: 数据加载线程数
        """
        train_transform, val_transform = get_mnist_transforms(img_size)

        train_dataset = datasets.MNIST(
            root=data_dir,
            train=True,
            download=True,
            transform=train_transform,
        )

        val_dataset = datasets.MNIST(
            root=data_dir,
            train=False,
            download=True,
            transform=val_transform,
        )

        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=True,
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=True,
        )

        return train_loader, val_loader

    @staticmethod
    def create_cifar10_loaders(
        batch_size: int = 64,
        img_size: int = 32,
        data_dir: str = './data',
        num_workers: int = 0,
    ) -> Tuple[DataLoader, DataLoader]:
        """
        创建 CIFAR-10 数据加载器

        参数：
            batch_size: 批次大小
            img_size: 图像尺寸
            data_dir: 数据目录
            num_workers: 数据加载线程数
        """
        train_transform, val_transform = get_cifar10_transforms(img_size)

        train_dataset = datasets.CIFAR10(
            root=data_dir,
            train=True,
            download=True,
            transform=train_transform,
        )

        val_dataset = datasets.CIFAR10(
            root=data_dir,
            train=False,
            download=True,
            transform=val_transform,
        )

        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=True,
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=True,
        )

        return train_loader, val_loader
