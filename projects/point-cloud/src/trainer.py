"""
点云模型训练器

支持 PointNet 分类和分割模型的训练、验证和测试。
"""

import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

from .pointnet import PointNetClassifier, PointNetSegmentor, pointnet_loss


class PointCloudTrainer:
    """
    点云模型训练器

    封装训练循环，支持分类和分割任务。
    """

    def __init__(self, model, task="classification", device="cpu"):
        """
        Args:
            model: PointNet 模型
            task: "classification" 或 "segmentation"
            device: 计算设备
        """
        self.model = model.to(device)
        self.task = task
        self.device = device
        self.history = {
            "train_loss": [],
            "train_acc": [],
            "val_loss": [],
            "val_acc": [],
        }

    @classmethod
    def create_classifier(cls, num_classes=10, use_tnet=True, device="cpu"):
        """创建分类器训练器"""
        model = PointNetClassifier(num_classes=num_classes, use_tnet=use_tnet)
        return cls(model, task="classification", device=device)

    @classmethod
    def create_segmentor(cls, num_classes=10, use_tnet=True, device="cpu"):
        """创建分割器训练器"""
        model = PointNetSegmentor(num_classes=num_classes, use_tnet=use_tnet)
        return cls(model, task="segmentation", device=device)

    def train(self, train_dataset, val_dataset=None, epochs=50, lr=0.001,
              batch_size=32, weight_decay=1e-4):
        """
        训练模型

        Args:
            train_dataset: 训练数据集
            val_dataset: 验证数据集
            epochs: 训练轮数
            lr: 学习率
            batch_size: 批次大小
            weight_decay: 权重衰减

        Returns:
            history: 训练历史
        """
        # 数据加载器
        train_loader = DataLoader(
            train_dataset, batch_size=batch_size, shuffle=True, num_workers=0
        )

        val_loader = None
        if val_dataset is not None:
            val_loader = DataLoader(
                val_dataset, batch_size=batch_size, shuffle=False, num_workers=0
            )

        # 优化器和调度器
        optimizer = optim.Adam(
            self.model.parameters(), lr=lr, weight_decay=weight_decay
        )
        scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=20, gamma=0.5)

        print(f"开始训练 {self.task} 模型...")
        print(f"设备: {self.device}")
        print(f"训练样本: {len(train_dataset)}")
        if val_dataset:
            print(f"验证样本: {len(val_dataset)}")
        print("-" * 60)

        for epoch in range(epochs):
            # 训练
            train_loss, train_acc = self._train_epoch(train_loader, optimizer)
            self.history["train_loss"].append(train_loss)
            self.history["train_acc"].append(train_acc)

            # 验证
            val_loss, val_acc = 0.0, 0.0
            if val_loader is not None:
                val_loss, val_acc = self._evaluate(val_loader)
                self.history["val_loss"].append(val_loss)
                self.history["val_acc"].append(val_acc)

            # 更新学习率
            scheduler.step()

            # 打印进度
            if (epoch + 1) % 5 == 0 or epoch == 0:
                print(f"Epoch [{epoch+1}/{epochs}] "
                      f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f}", end="")
                if val_loader:
                    print(f" | Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}", end="")
                print(f" | LR: {scheduler.get_last_lr()[0]:.6f}")

        print("-" * 60)
        print("训练完成!")

        return self.history

    def _train_epoch(self, dataloader, optimizer):
        """训练一个 epoch"""
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        for points, labels in dataloader:
            points = points.to(self.device)
            labels = labels.to(self.device)

            # 前向传播
            if self.task == "classification":
                logits, trans_input, trans_feat = self.model(points)
                loss = pointnet_loss(logits, labels, trans_feat)
                preds = logits.argmax(dim=1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)
            else:
                logits, trans_input, trans_feat = self.model(points)
                # 分割: logits (B, N, C), labels (B, N)
                logits_flat = logits.reshape(-1, logits.size(-1))
                labels_flat = labels.reshape(-1)
                loss = pointnet_loss(logits_flat, labels_flat, trans_feat)
                preds = logits.argmax(dim=-1)
                correct += (preds == labels).sum().item()
                total += labels.numel()

            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(dataloader)
        accuracy = correct / total

        return avg_loss, accuracy

    @torch.no_grad()
    def _evaluate(self, dataloader):
        """评估模型"""
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0

        for points, labels in dataloader:
            points = points.to(self.device)
            labels = labels.to(self.device)

            if self.task == "classification":
                logits, _, trans_feat = self.model(points)
                loss = pointnet_loss(logits, labels, trans_feat)
                preds = logits.argmax(dim=1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)
            else:
                logits, _, trans_feat = self.model(points)
                logits_flat = logits.reshape(-1, logits.size(-1))
                labels_flat = labels.reshape(-1)
                loss = pointnet_loss(logits_flat, labels_flat, trans_feat)
                preds = logits.argmax(dim=-1)
                correct += (preds == labels).sum().item()
                total += labels.numel()

            total_loss += loss.item()

        avg_loss = total_loss / len(dataloader)
        accuracy = correct / total

        return avg_loss, accuracy

    def predict(self, points):
        """
        预测

        Args:
            points: (B, 3, N) 或 (3, N) 点云

        Returns:
            predictions: 预测结果
        """
        self.model.eval()

        if points.dim() == 2:
            points = points.unsqueeze(0)

        points = points.to(self.device)

        with torch.no_grad():
            logits, _, _ = self.model(points)

        if self.task == "classification":
            predictions = logits.argmax(dim=1)
        else:
            predictions = logits.argmax(dim=-1)

        return predictions.cpu()

    def save_model(self, path):
        """保存模型"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'task': self.task,
            'history': self.history,
        }, path)
        print(f"模型已保存到 {path}")

    def load_model(self, path):
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.history = checkpoint['history']
        print(f"模型已从 {path} 加载")
