"""
Trainer - 训练器

封装模型训练逻辑，支持：
- 标准交叉熵损失训练
- 训练过程日志记录
- 模型检查点保存
- 验证集评估
"""

import os
import time
from typing import Optional

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .model import ImageCaptioningModel
from .dataset import collate_fn


class Trainer:
    """图像描述模型训练器。"""

    def __init__(
        self,
        model: ImageCaptioningModel,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        learning_rate: float = 1e-4,
        weight_decay: float = 1e-5,
        device: Optional[str] = None,
        checkpoint_dir: str = "checkpoints",
    ):
        """初始化训练器。

        Args:
            model: 图像描述模型
            train_loader: 训练数据加载器
            val_loader: 验证数据加载器
            learning_rate: 学习率
            weight_decay: 权重衰减
            device: 计算设备
            checkpoint_dir: 检查点保存目录
        """
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.checkpoint_dir = checkpoint_dir

        # 设备选择
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.model.to(self.device)

        # 优化器
        self.optimizer = torch.optim.Adam(
            model.parameters(), lr=learning_rate, weight_decay=weight_decay
        )

        # 学习率调度器
        self.scheduler = torch.optim.lr_scheduler.StepLR(
            self.optimizer, step_size=5, gamma=0.8
        )

        # 损失函数（忽略填充位置的损失）
        self.criterion = nn.CrossEntropyLoss(ignore_index=0)  # 0 = <pad>

        # 训练历史
        self.history = {
            "train_loss": [],
            "val_loss": [],
            "learning_rate": [],
        }

        os.makedirs(checkpoint_dir, exist_ok=True)

    def train_epoch(self) -> float:
        """训练一个 epoch。

        Returns:
            平均训练损失
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch_idx, (images, captions, lengths) in enumerate(self.train_loader):
            images = images.to(self.device)
            captions = captions.to(self.device)
            lengths = lengths.to(self.device)

            # 前向传播
            predictions, _ = self.model(images, captions, lengths)

            # 计算损失
            # predictions: (batch, seq_len, vocab_size)
            # targets: (batch, seq_len)，需要对齐
            targets = captions[:, 1:]  # 去掉 <start>
            # 截断到相同长度
            min_len = min(predictions.size(1), targets.size(1))
            predictions = predictions[:, :min_len, :].contiguous().view(-1, predictions.size(2))
            targets = targets[:, :min_len].contiguous().view(-1)

            loss = self.criterion(predictions, targets)

            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()

            # 梯度裁剪
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=5.0)

            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / max(num_batches, 1)
        return avg_loss

    @torch.no_grad()
    def validate(self) -> float:
        """在验证集上评估模型。

        Returns:
            平均验证损失
        """
        if self.val_loader is None:
            return 0.0

        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        for images, captions, lengths in self.val_loader:
            images = images.to(self.device)
            captions = captions.to(self.device)
            lengths = lengths.to(self.device)

            predictions, _ = self.model(images, captions, lengths)

            targets = captions[:, 1:]
            min_len = min(predictions.size(1), targets.size(1))
            predictions = predictions[:, :min_len, :].contiguous().view(-1, predictions.size(2))
            targets = targets[:, :min_len].contiguous().view(-1)

            loss = self.criterion(predictions, targets)
            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / max(num_batches, 1)
        return avg_loss

    def train(
        self,
        num_epochs: int = 10,
        print_every: int = 1,
        save_every: int = 5,
    ) -> dict:
        """完整训练流程。

        Args:
            num_epochs: 训练轮数
            print_every: 每隔多少个 epoch 打印日志
            save_every: 每隔多少个 epoch 保存检查点

        Returns:
            训练历史字典
        """
        print(f"开始训练，共 {num_epochs} 个 epoch")
        print(f"设备: {self.device}")
        print(f"训练样本数: {len(self.train_loader.dataset)}")
        if self.val_loader:
            print(f"验证样本数: {len(self.val_loader.dataset)}")
        print("-" * 60)

        best_val_loss = float("inf")

        for epoch in range(1, num_epochs + 1):
            start_time = time.time()

            # 训练
            train_loss = self.train_epoch()

            # 验证
            val_loss = self.validate()

            # 学习率调度
            self.scheduler.step()
            current_lr = self.optimizer.param_groups[0]["lr"]

            # 记录历史
            self.history["train_loss"].append(train_loss)
            self.history["val_loss"].append(val_loss)
            self.history["learning_rate"].append(current_lr)

            elapsed = time.time() - start_time

            if epoch % print_every == 0:
                msg = (
                    f"Epoch [{epoch}/{num_epochs}] "
                    f"Train Loss: {train_loss:.4f}"
                )
                if self.val_loader:
                    msg += f" | Val Loss: {val_loss:.4f}"
                msg += f" | LR: {current_lr:.6f} | Time: {elapsed:.1f}s"
                print(msg)

            # 保存最佳模型
            if self.val_loader and val_loss < best_val_loss:
                best_val_loss = val_loss
                self.save_checkpoint(f"best_model.pt")

            # 定期保存检查点
            if save_every > 0 and epoch % save_every == 0:
                self.save_checkpoint(f"checkpoint_epoch_{epoch}.pt")

        print("-" * 60)
        print("训练完成！")
        return self.history

    def save_checkpoint(self, filename: str) -> None:
        """保存模型检查点。

        Args:
            filename: 检查点文件名
        """
        filepath = os.path.join(self.checkpoint_dir, filename)
        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "history": self.history,
        }
        torch.save(checkpoint, filepath)

    def load_checkpoint(self, filename: str) -> None:
        """加载模型检查点。

        Args:
            filename: 检查点文件名
        """
        filepath = os.path.join(self.checkpoint_dir, filename)
        checkpoint = torch.load(filepath, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        if "scheduler_state_dict" in checkpoint:
            self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        if "history" in checkpoint:
            self.history = checkpoint["history"]
