"""
深度估计训练脚本

提供训练和验证功能:
- 训练循环
- 验证循环
- 学习率调度
- 指标记录
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from typing import Dict, List, Optional, Tuple
import time

from .model import DepthEstimationNet, SimpleDepthNet, count_parameters
from .loss import CombinedDepthLoss, SILogLoss
from .dataset import SyntheticDepthDataset, create_dataloader
from .utils import compute_depth_metrics, print_metrics


class DepthTrainer:
    """
    深度估计训练器

    封装训练和验证逻辑，支持多种配置。

    Args:
        model: 深度估计模型
        criterion: 损失函数
        optimizer: 优化器
        scheduler: 学习率调度器
        device: 训练设备
        gradient_clip: 梯度裁剪值

    Example:
        >>> model = SimpleDepthNet()
        >>> criterion = CombinedDepthLoss()
        >>> optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
        >>> trainer = DepthTrainer(model, criterion, optimizer)
        >>> history = trainer.train(train_loader, val_loader, num_epochs=10)
    """

    def __init__(
        self,
        model: nn.Module,
        criterion: nn.Module,
        optimizer: optim.Optimizer,
        scheduler: Optional[optim.lr_scheduler._LRScheduler] = None,
        device: Optional[str] = None,
        gradient_clip: float = 1.0,
    ):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = torch.device(device)
        self.model = model.to(self.device)
        self.criterion = criterion.to(self.device)
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.gradient_clip = gradient_clip

    def train_epoch(self, dataloader: DataLoader) -> Dict[str, float]:
        """
        训练一个 epoch

        Args:
            dataloader: 训练数据加载器

        Returns:
            平均损失字典
        """
        self.model.train()
        total_losses = {}
        num_batches = 0

        for images, depths, masks in dataloader:
            images = images.to(self.device)
            depths = depths.to(self.device)
            masks = masks.to(self.device)

            # 前向传播
            pred_depths = self.model(images)

            # 计算损失
            if isinstance(pred_depths, list):
                # 多尺度输出
                loss_dict = self.criterion(pred_depths[0], depths, masks)
                # 添加其他尺度的损失
                for i, pred in enumerate(pred_depths[1:], 1):
                    scale_loss = self.criterion(pred, depths, masks)
                    if isinstance(scale_loss, dict):
                        loss_dict["total"] = loss_dict["total"] + 0.5 ** i * scale_loss["total"]
                    else:
                        loss_dict["total"] = loss_dict["total"] + 0.5 ** i * scale_loss
            else:
                loss_dict = self.criterion(pred_depths, depths, masks)

            # 处理损失字典
            if isinstance(loss_dict, dict):
                loss = loss_dict["total"]
            else:
                loss = loss_dict
                loss_dict = {"total": loss}

            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()

            # 梯度裁剪
            if self.gradient_clip > 0:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), self.gradient_clip
                )

            self.optimizer.step()

            # 记录损失
            for key, value in loss_dict.items():
                if key not in total_losses:
                    total_losses[key] = 0
                total_losses[key] += value.item()
            num_batches += 1

        # 计算平均损失
        avg_losses = {key: value / num_batches for key, value in total_losses.items()}
        return avg_losses

    @torch.no_grad()
    def validate(self, dataloader: DataLoader) -> Dict[str, float]:
        """
        验证

        Args:
            dataloader: 验证数据加载器

        Returns:
            评估指标字典
        """
        self.model.eval()
        all_metrics = []

        for images, depths, masks in dataloader:
            images = images.to(self.device)
            depths = depths.to(self.device)
            masks = masks.to(self.device)

            # 前向传播
            pred_depths = self.model(images)

            if isinstance(pred_depths, list):
                pred_depths = pred_depths[0]

            # 计算指标
            metrics = compute_depth_metrics(pred_depths, depths, masks)
            all_metrics.append(metrics)

        # 计算平均指标
        avg_metrics = {}
        for key in all_metrics[0].keys():
            avg_metrics[key] = sum(m[key] for m in all_metrics) / len(all_metrics)

        return avg_metrics

    def train(
        self,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        num_epochs: int = 50,
        print_every: int = 5,
    ) -> Dict[str, List[float]]:
        """
        完整训练流程

        Args:
            train_loader: 训练数据加载器
            val_loader: 验证数据加载器
            num_epochs: 训练轮数
            print_every: 打印间隔

        Returns:
            训练历史字典
        """
        history = {
            "train_loss": [],
            "val_abs_rel": [],
            "val_rmse": [],
            "val_delta1": [],
        }

        print(f"开始训练 (共 {num_epochs} 轮)")
        print(f"模型参数量: {count_parameters(self.model):,}")
        print("=" * 60)

        for epoch in range(num_epochs):
            start_time = time.time()

            # 训练
            train_losses = self.train_epoch(train_loader)
            train_loss = train_losses.get("total", 0)
            history["train_loss"].append(train_loss)

            # 验证
            val_metrics = {}
            if val_loader is not None:
                val_metrics = self.validate(val_loader)
                history["val_abs_rel"].append(val_metrics.get("abs_rel", 0))
                history["val_rmse"].append(val_metrics.get("rmse", 0))
                history["val_delta1"].append(val_metrics.get("delta1", 0))

            # 学习率调度
            if self.scheduler is not None:
                self.scheduler.step()

            # 打印进度
            if (epoch + 1) % print_every == 0:
                elapsed = time.time() - start_time
                lr = self.optimizer.param_groups[0]["lr"]

                print(f"Epoch [{epoch+1}/{num_epochs}] "
                      f"Loss: {train_loss:.4f} "
                      f"LR: {lr:.2e} "
                      f"Time: {elapsed:.1f}s")

                if val_metrics:
                    print(f"  Val Abs Rel: {val_metrics.get('abs_rel', 0):.4f} "
                          f"RMSE: {val_metrics.get('rmse', 0):.4f} "
                          f"delta1: {val_metrics.get('delta1', 0):.4f}")

        print("=" * 60)
        print("训练完成!")

        return history


def train_simple(
    num_epochs: int = 20,
    batch_size: int = 8,
    num_train_samples: int = 200,
    num_val_samples: int = 50,
    image_size: Tuple[int, int] = (128, 128),
    learning_rate: float = 1e-3,
    device: Optional[str] = None,
) -> Dict[str, List[float]]:
    """
    快速训练函数 (用于测试)

    Args:
        num_epochs: 训练轮数
        batch_size: 批量大小
        num_train_samples: 训练样本数
        num_val_samples: 验证样本数
        image_size: 图像尺寸
        learning_rate: 学习率
        device: 训练设备

    Returns:
        训练历史
    """
    # 创建数据集
    train_dataset = SyntheticDepthDataset(
        num_samples=num_train_samples,
        image_size=image_size,
    )
    val_dataset = SyntheticDepthDataset(
        num_samples=num_val_samples,
        image_size=image_size,
    )

    train_loader = create_dataloader(train_dataset, batch_size=batch_size)
    val_loader = create_dataloader(val_dataset, batch_size=batch_size, shuffle=False)

    # 创建模型
    model = SimpleDepthNet()

    # 损失函数
    criterion = CombinedDepthLoss()

    # 优化器
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # 学习率调度
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)

    # 训练
    trainer = DepthTrainer(
        model=model,
        criterion=criterion,
        optimizer=optimizer,
        scheduler=scheduler,
        device=device,
    )

    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=num_epochs,
        print_every=max(1, num_epochs // 5),
    )

    return history


def train_full(
    num_epochs: int = 50,
    batch_size: int = 16,
    num_train_samples: int = 1000,
    num_val_samples: int = 200,
    image_size: Tuple[int, int] = (256, 256),
    base_channels: int = 64,
    learning_rate: float = 1e-4,
    weight_decay: float = 1e-5,
    device: Optional[str] = None,
) -> Tuple[DepthEstimationNet, Dict[str, List[float]]]:
    """
    完整训练函数

    Args:
        num_epochs: 训练轮数
        batch_size: 批量大小
        num_train_samples: 训练样本数
        num_val_samples: 验证样本数
        image_size: 图像尺寸
        base_channels: 基础通道数
        learning_rate: 学习率
        weight_decay: 权重衰减
        device: 训练设备

    Returns:
        (模型, 训练历史) 元组
    """
    # 创建数据集
    train_dataset = SyntheticDepthDataset(
        num_samples=num_train_samples,
        image_size=image_size,
    )
    val_dataset = SyntheticDepthDataset(
        num_samples=num_val_samples,
        image_size=image_size,
    )

    train_loader = create_dataloader(train_dataset, batch_size=batch_size)
    val_loader = create_dataloader(val_dataset, batch_size=batch_size, shuffle=False)

    # 创建模型
    model = DepthEstimationNet(base_channels=base_channels)

    # 损失函数
    criterion = CombinedDepthLoss()

    # 优化器
    optimizer = optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay,
    )

    # 学习率调度
    scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(
        optimizer, T_0=10, T_mult=2
    )

    # 训练
    trainer = DepthTrainer(
        model=model,
        criterion=criterion,
        optimizer=optimizer,
        scheduler=scheduler,
        device=device,
    )

    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=num_epochs,
        print_every=max(1, num_epochs // 10),
    )

    return model, history
