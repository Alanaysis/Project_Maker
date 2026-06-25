"""
训练器模块

提供 VQA 模型的训练和评估功能。
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from typing import Dict, List, Optional, Tuple
import time
import json
from pathlib import Path

from .vqa_model import VQAModel


class VQATrainer:
    """
    VQA 训练器

    提供模型训练、验证和评估功能。

    Args:
        model: VQA 模型
        learning_rate: 学习率
        weight_decay: 权重衰减
        device: 计算设备
    """

    def __init__(
        self,
        model: VQAModel,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        device: Optional[str] = None,
    ):
        self.model = model

        # 设备选择
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)

        self.model.to(self.device)

        # 优化器
        self.optimizer = optim.Adam(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,
        )

        # 学习率调度器
        self.scheduler = optim.lr_scheduler.StepLR(
            self.optimizer,
            step_size=10,
            gamma=0.5,
        )

        # 训练历史
        self.history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': [],
        }

    def train_epoch(self, dataloader: DataLoader) -> Dict[str, float]:
        """
        训练一个 epoch

        Args:
            dataloader: 训练数据加载器

        Returns:
            训练指标字典
        """
        self.model.train()
        total_loss = 0
        total_correct = 0
        total_samples = 0

        for batch in dataloader:
            # 移动数据到设备
            question_ids = batch['question_ids'].to(self.device)
            image_features = batch['image_features'].to(self.device)
            targets = batch.get('answer_idx')

            if targets is not None:
                targets = targets.to(self.device)

            # 前向传播
            outputs = self.model(
                question_ids=question_ids,
                image_features=image_features,
                targets=targets,
            )

            # 计算损失
            loss = outputs.get('loss')
            if loss is None:
                continue

            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()

            # 梯度裁剪
            nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

            self.optimizer.step()

            # 统计
            total_loss += loss.item() * question_ids.size(0)
            if 'accuracy' in outputs:
                total_correct += outputs['accuracy'].item() * question_ids.size(0)
            total_samples += question_ids.size(0)

        # 更新学习率
        self.scheduler.step()

        # 计算平均指标
        avg_loss = total_loss / total_samples if total_samples > 0 else 0
        avg_acc = total_correct / total_samples if total_samples > 0 else 0

        return {'loss': avg_loss, 'accuracy': avg_acc}

    @torch.no_grad()
    def evaluate(self, dataloader: DataLoader) -> Dict[str, float]:
        """
        评估模型

        Args:
            dataloader: 验证数据加载器

        Returns:
            评估指标字典
        """
        self.model.eval()
        total_loss = 0
        total_correct = 0
        total_samples = 0

        for batch in dataloader:
            question_ids = batch['question_ids'].to(self.device)
            image_features = batch['image_features'].to(self.device)
            targets = batch.get('answer_idx')

            if targets is not None:
                targets = targets.to(self.device)

            # 前向传播
            outputs = self.model(
                question_ids=question_ids,
                image_features=image_features,
                targets=targets,
            )

            loss = outputs.get('loss')
            if loss is not None:
                total_loss += loss.item() * question_ids.size(0)
            if 'accuracy' in outputs:
                total_correct += outputs['accuracy'].item() * question_ids.size(0)
            total_samples += question_ids.size(0)

        avg_loss = total_loss / total_samples if total_samples > 0 else 0
        avg_acc = total_correct / total_samples if total_samples > 0 else 0

        return {'loss': avg_loss, 'accuracy': avg_acc}

    def train(
        self,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        num_epochs: int = 20,
        save_dir: Optional[str] = None,
    ) -> Dict[str, List[float]]:
        """
        完整训练流程

        Args:
            train_loader: 训练数据加载器
            val_loader: 验证数据加载器（可选）
            num_epochs: 训练轮数
            save_dir: 模型保存目录（可选）

        Returns:
            训练历史
        """
        best_val_acc = 0

        for epoch in range(num_epochs):
            start_time = time.time()

            # 训练
            train_metrics = self.train_epoch(train_loader)
            self.history['train_loss'].append(train_metrics['loss'])
            self.history['train_acc'].append(train_metrics['accuracy'])

            # 验证
            val_metrics = {'loss': 0, 'accuracy': 0}
            if val_loader is not None:
                val_metrics = self.evaluate(val_loader)
                self.history['val_loss'].append(val_metrics['loss'])
                self.history['val_acc'].append(val_metrics['accuracy'])

            elapsed = time.time() - start_time

            # 打印进度
            print(f"Epoch {epoch + 1}/{num_epochs} ({elapsed:.1f}s)")
            print(f"  Train - Loss: {train_metrics['loss']:.4f}, Acc: {train_metrics['accuracy']:.2%}")
            if val_loader is not None:
                print(f"  Val   - Loss: {val_metrics['loss']:.4f}, Acc: {val_metrics['accuracy']:.2%}")

            # 保存最佳模型
            if save_dir and val_metrics['accuracy'] > best_val_acc:
                best_val_acc = val_metrics['accuracy']
                self.save_model(save_dir)
                print(f"  -> 保存最佳模型 (Val Acc: {best_val_acc:.2%})")

        return self.history

    def save_model(self, save_dir: str):
        """
        保存模型

        Args:
            save_dir: 保存目录
        """
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        # 保存模型权重
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'history': self.history,
        }, save_path / 'model.pt')

        # 保存配置
        config = self.model.get_model_info()
        with open(save_path / 'config.json', 'w') as f:
            json.dump(config, f, indent=2)

    def load_model(self, save_dir: str):
        """
        加载模型

        Args:
            save_dir: 模型目录
        """
        save_path = Path(save_dir)
        checkpoint = torch.load(save_path / 'model.pt', map_location=self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        self.history = checkpoint['history']


class VQAEvaluator:
    """
    VQA 评估器

    提供详细的模型评估功能。

    Args:
        model: VQA 模型
        device: 计算设备
    """

    def __init__(
        self,
        model: VQAModel,
        device: Optional[str] = None,
    ):
        self.model = model

        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)

        self.model.to(self.device)

    @torch.no_grad()
    def predict_batch(
        self,
        batch: Dict[str, torch.Tensor],
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        批量预测

        Args:
            batch: 数据批次

        Returns:
            (预测类别, 置信度)
        """
        self.model.eval()
        question_ids = batch['question_ids'].to(self.device)
        image_features = batch['image_features'].to(self.device)

        outputs = self.model(
            question_ids=question_ids,
            image_features=image_features,
        )

        predictions, confidence = self.model.predictor.predict(outputs['fused_features'])
        return predictions, confidence

    @torch.no_grad()
    def compute_accuracy(
        self,
        dataloader: DataLoader,
    ) -> Dict[str, float]:
        """
        计算准确率

        Args:
            dataloader: 数据加载器

        Returns:
            准确率指标
        """
        self.model.eval()
        correct = 0
        total = 0

        for batch in dataloader:
            question_ids = batch['question_ids'].to(self.device)
            image_features = batch['image_features'].to(self.device)
            targets = batch.get('answer_idx')

            if targets is None:
                continue

            targets = targets.to(self.device)

            outputs = self.model(
                question_ids=question_ids,
                image_features=image_features,
            )

            predictions = outputs['logits'].argmax(dim=1)
            correct += (predictions == targets).sum().item()
            total += targets.size(0)

        accuracy = correct / total if total > 0 else 0

        return {
            'accuracy': accuracy,
            'correct': correct,
            'total': total,
        }
