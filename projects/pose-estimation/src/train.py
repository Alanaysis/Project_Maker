"""
训练脚本 (Training Script).

提供完整的训练循环，支持:
- 学习率调度
- 模型检查点保存
- 训练历史记录
- 验证评估
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
import time
import os
from typing import Dict, List, Optional, Tuple

from .model import PoseEstimationNet, SimplePoseNet
from .loss import KeypointMSELoss, CombinedPoseLoss
from .heatmap import generate_heatmaps
from .keypoints import extract_keypoints, compute_pck
from .dataset import SyntheticPoseDataset, create_dataloader


class Trainer:
    """
    姿态估计训练器。

    Args:
        model: 姿态估计模型
        train_loader: 训练数据加载器
        val_loader: 验证数据加载器
        config: 训练配置字典
    """

    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        config: Optional[dict] = None,
    ):
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.config = self._default_config()
        if config:
            self.config.update(config)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)

        # 损失函数
        self.criterion = KeypointMSELoss(use_target_weight=True)

        # 优化器
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=self.config["learning_rate"],
            weight_decay=self.config["weight_decay"],
        )

        # 学习率调度
        self.scheduler = optim.lr_scheduler.StepLR(
            self.optimizer,
            step_size=self.config["lr_step_size"],
            gamma=self.config["lr_gamma"],
        )

        # 训练历史
        self.history = {
            "train_loss": [],
            "val_loss": [],
            "val_pck": [],
            "learning_rate": [],
        }

    @staticmethod
    def _default_config() -> dict:
        return {
            "num_epochs": 50,
            "learning_rate": 1e-3,
            "weight_decay": 1e-4,
            "lr_step_size": 20,
            "lr_gamma": 0.1,
            "save_dir": "checkpoints",
            "save_every": 10,
            "print_every": 5,
        }

    def train_one_epoch(self) -> float:
        """训练一个 epoch。"""
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch in self.train_loader:
            images = batch["image"].to(self.device)
            target_heatmaps = batch["heatmaps"].to(self.device)
            target_weights = batch["weights"].to(self.device)

            # 前向传播
            pred_heatmaps = self.model(images)

            # 如果输出尺寸与目标不同，调整尺寸
            if pred_heatmaps.shape[2:] != target_heatmaps.shape[2:]:
                pred_heatmaps = nn.functional.interpolate(
                    pred_heatmaps,
                    size=target_heatmaps.shape[2:],
                    mode="bilinear",
                    align_corners=False,
                )

            # 计算损失
            loss_dict = self.criterion(pred_heatmaps, target_heatmaps, target_weights)
            loss = loss_dict["loss"]

            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        return total_loss / max(num_batches, 1)

    @torch.no_grad()
    def validate(self) -> Tuple[float, float]:
        """验证模型。"""
        if self.val_loader is None:
            return 0.0, 0.0

        self.model.eval()
        total_loss = 0.0
        total_pck = 0.0
        num_batches = 0

        for batch in self.val_loader:
            images = batch["image"].to(self.device)
            target_heatmaps = batch["heatmaps"].to(self.device)
            target_weights = batch["weights"].to(self.device)
            target_keypoints = batch["keypoints"].to(self.device)

            # 前向传播
            pred_heatmaps = self.model(images)

            # 调整尺寸
            if pred_heatmaps.shape[2:] != target_heatmaps.shape[2:]:
                pred_heatmaps = nn.functional.interpolate(
                    pred_heatmaps,
                    size=target_heatmaps.shape[2:],
                    mode="bilinear",
                    align_corners=False,
                )

            # 计算损失
            loss_dict = self.criterion(pred_heatmaps, target_heatmaps, target_weights)
            total_loss += loss_dict["loss"].item()

            # 计算 PCK
            pred_kp, pred_conf = extract_keypoints(pred_heatmaps)
            pck = compute_pck(pred_kp, target_keypoints)
            total_pck += pck

            num_batches += 1

        avg_loss = total_loss / max(num_batches, 1)
        avg_pck = total_pck / max(num_batches, 1)

        return avg_loss, avg_pck

    def train(self) -> dict:
        """
        执行完整训练。

        Returns:
            训练历史字典
        """
        num_epochs = self.config["num_epochs"]
        print_every = self.config["print_every"]
        save_every = self.config["save_every"]
        save_dir = self.config["save_dir"]

        os.makedirs(save_dir, exist_ok=True)

        print(f"开始训练: {num_epochs} epochs, 设备: {self.device}")
        print(f"模型参数量: {sum(p.numel() for p in self.model.parameters()):,}")
        print("-" * 60)

        for epoch in range(1, num_epochs + 1):
            start_time = time.time()

            # 训练
            train_loss = self.train_one_epoch()

            # 验证
            val_loss, val_pck = self.validate()

            # 学习率调度
            current_lr = self.optimizer.param_groups[0]["lr"]
            self.scheduler.step()

            # 记录历史
            self.history["train_loss"].append(train_loss)
            self.history["val_loss"].append(val_loss)
            self.history["val_pck"].append(val_pck)
            self.history["learning_rate"].append(current_lr)

            # 打印进度
            if epoch % print_every == 0 or epoch == 1:
                elapsed = time.time() - start_time
                print(
                    f"Epoch [{epoch}/{num_epochs}] "
                    f"Train Loss: {train_loss:.4f} "
                    f"Val Loss: {val_loss:.4f} "
                    f"Val PCK: {val_pck:.4f} "
                    f"LR: {current_lr:.6f} "
                    f"Time: {elapsed:.1f}s"
                )

            # 保存检查点
            if epoch % save_every == 0:
                checkpoint_path = os.path.join(save_dir, f"model_epoch_{epoch}.pt")
                self.save_checkpoint(checkpoint_path, epoch)

        # 保存最终模型
        final_path = os.path.join(save_dir, "model_final.pt")
        self.save_checkpoint(final_path, num_epochs)
        print(f"\n训练完成! 最终模型已保存至: {final_path}")

        return self.history

    def save_checkpoint(self, path: str, epoch: int):
        """保存模型检查点。"""
        torch.save({
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "history": self.history,
            "config": self.config,
        }, path)

    def load_checkpoint(self, path: str):
        """加载模型检查点。"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        self.history = checkpoint.get("history", self.history)
        return checkpoint.get("epoch", 0)


def train_simple(
    num_epochs: int = 10,
    batch_size: int = 8,
    num_train_samples: int = 100,
    num_val_samples: int = 20,
    image_size: Tuple[int, int] = (128, 128),
    heatmap_size: Tuple[int, int] = (64, 64),
    num_keypoints: int = 17,
    learning_rate: float = 1e-3,
) -> dict:
    """
    快速训练函数，用于测试和演示。

    Args:
        num_epochs: 训练轮数
        batch_size: 批大小
        num_train_samples: 训练样本数
        num_val_samples: 验证样本数
        image_size: 图像尺寸
        heatmap_size: 热力图尺寸
        num_keypoints: 关键点数量
        learning_rate: 学习率

    Returns:
        训练历史字典
    """
    # 创建数据集
    train_dataset = SyntheticPoseDataset(
        num_samples=num_train_samples,
        image_size=image_size,
        heatmap_size=heatmap_size,
        num_keypoints=num_keypoints,
    )
    val_dataset = SyntheticPoseDataset(
        num_samples=num_val_samples,
        image_size=image_size,
        heatmap_size=heatmap_size,
        num_keypoints=num_keypoints,
    )

    # 创建数据加载器
    train_loader = create_dataloader(train_dataset, batch_size=batch_size)
    val_loader = create_dataloader(val_dataset, batch_size=batch_size, shuffle=False)

    # 创建模型
    model = SimplePoseNet(num_keypoints=num_keypoints, input_size=image_size[0])

    # 创建训练器
    config = {
        "num_epochs": num_epochs,
        "learning_rate": learning_rate,
        "print_every": max(1, num_epochs // 10),
        "save_every": num_epochs + 1,  # 不保存中间检查点
        "save_dir": "checkpoints",
    }

    trainer = Trainer(model, train_loader, val_loader, config)

    # 训练
    history = trainer.train()

    return history
