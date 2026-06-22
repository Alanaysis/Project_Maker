"""
模型训练器

封装训练循环、验证、测试等功能
支持多种优化器和学习率调度策略
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from typing import Optional, Dict, List, Tuple
import time
from tqdm import tqdm
import json
from pathlib import Path


class Trainer:
    """
    模型训练器

    功能：
    - 训练循环
    - 验证评估
    - 学习率调度
    - 模型保存/加载
    - 训练历史记录
    """

    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        test_loader: Optional[DataLoader] = None,
        device: Optional[str] = None
    ):
        """
        初始化训练器

        参数：
            model: 要训练的模型
            train_loader: 训练数据加载器
            val_loader: 验证数据加载器
            test_loader: 测试数据加载器
            device: 计算设备 ('cuda' 或 'cpu')
        """
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.test_loader = test_loader

        # 自动选择设备
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)

        self.model.to(self.device)

        # 训练历史
        self.history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': [],
            'lr': []
        }

        self.best_val_acc = 0.0
        self.best_model_state = None

    def compile(
        self,
        optimizer: str = 'adam',
        lr: float = 0.001,
        weight_decay: float = 0.0,
        scheduler: Optional[str] = None,
        **kwargs
    ):
        """
        配置优化器和损失函数

        参数：
            optimizer: 优化器类型 ('adam', 'sgd', 'adamw')
            lr: 学习率
            weight_decay: 权重衰减
            scheduler: 学习率调度器 ('step', 'cosine', 'plateau')
        """
        # 损失函数
        self.criterion = nn.CrossEntropyLoss()

        # 优化器
        if optimizer == 'adam':
            self.optimizer = optim.Adam(
                self.model.parameters(),
                lr=lr,
                weight_decay=weight_decay
            )
        elif optimizer == 'sgd':
            self.optimizer = optim.SGD(
                self.model.parameters(),
                lr=lr,
                momentum=kwargs.get('momentum', 0.9),
                weight_decay=weight_decay
            )
        elif optimizer == 'adamw':
            self.optimizer = optim.AdamW(
                self.model.parameters(),
                lr=lr,
                weight_decay=weight_decay
            )
        else:
            raise ValueError(f"Unknown optimizer: {optimizer}")

        # 学习率调度器
        if scheduler == 'step':
            self.scheduler = optim.lr_scheduler.StepLR(
                self.optimizer,
                step_size=kwargs.get('step_size', 10),
                gamma=kwargs.get('gamma', 0.1)
            )
        elif scheduler == 'cosine':
            self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer,
                T_max=kwargs.get('T_max', 50)
            )
        elif scheduler == 'plateau':
            self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
                self.optimizer,
                mode='max',
                patience=kwargs.get('patience', 5),
                factor=kwargs.get('factor', 0.1)
            )
        else:
            self.scheduler = None

    def train_epoch(self) -> Tuple[float, float]:
        """
        训练一个epoch

        返回：
            (平均损失, 准确率)
        """
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        pbar = tqdm(self.train_loader, desc='Training')
        for batch_idx, (data, target) in enumerate(pbar):
            data, target = data.to(self.device), target.to(self.device)

            # 前向传播
            self.optimizer.zero_grad()
            output = self.model(data)
            loss = self.criterion(output, target)

            # 反向传播
            loss.backward()
            self.optimizer.step()

            # 统计
            total_loss += loss.item() * data.size(0)
            _, predicted = output.max(1)
            total += target.size(0)
            correct += predicted.eq(target).sum().item()

            # 更新进度条
            pbar.set_postfix({
                'loss': loss.item(),
                'acc': 100. * correct / total
            })

        avg_loss = total_loss / total
        accuracy = 100. * correct / total

        return avg_loss, accuracy

    @torch.no_grad()
    def evaluate(self, data_loader: DataLoader) -> Tuple[float, float]:
        """
        评估模型

        参数：
            data_loader: 数据加载器

        返回：
            (平均损失, 准确率)
        """
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0

        for data, target in data_loader:
            data, target = data.to(self.device), target.to(self.device)
            output = self.model(data)
            loss = self.criterion(output, target)

            total_loss += loss.item() * data.size(0)
            _, predicted = output.max(1)
            total += target.size(0)
            correct += predicted.eq(target).sum().item()

        avg_loss = total_loss / total
        accuracy = 100. * correct / total

        return avg_loss, accuracy

    def fit(
        self,
        epochs: int = 20,
        save_dir: Optional[str] = None,
        early_stopping: Optional[int] = None,
        verbose: bool = True
    ) -> Dict[str, List[float]]:
        """
        训练模型

        参数：
            epochs: 训练轮数
            save_dir: 模型保存目录
            early_stopping: 早停轮数（None表示不使用早停）
            verbose: 是否显示详细信息

        返回：
            训练历史
        """
        print(f"Training on {self.device}")
        print(f"Model parameters: {sum(p.numel() for p in self.model.parameters()):,}")
        print("-" * 60)

        patience_counter = 0
        start_time = time.time()

        for epoch in range(1, epochs + 1):
            epoch_start = time.time()

            # 训练
            train_loss, train_acc = self.train_epoch()

            # 验证
            val_loss, val_acc = self.evaluate(self.val_loader)

            # 记录历史
            self.history['train_loss'].append(train_loss)
            self.history['train_acc'].append(train_acc)
            self.history['val_loss'].append(val_loss)
            self.history['val_acc'].append(val_acc)
            self.history['lr'].append(self.optimizer.param_groups[0]['lr'])

            # 更新学习率
            if self.scheduler is not None:
                if isinstance(self.scheduler, optim.lr_scheduler.ReduceLROnPlateau):
                    self.scheduler.step(val_acc)
                else:
                    self.scheduler.step()

            # 保存最佳模型
            if val_acc > self.best_val_acc:
                self.best_val_acc = val_acc
                self.best_model_state = self.model.state_dict().copy()
                patience_counter = 0

                if save_dir:
                    self.save_model(save_dir)
            else:
                patience_counter += 1

            epoch_time = time.time() - epoch_start

            if verbose:
                print(f"Epoch {epoch:3d}/{epochs} | "
                      f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
                      f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}% | "
                      f"LR: {self.optimizer.param_groups[0]['lr']:.6f} | "
                      f"Time: {epoch_time:.1f}s")

            # 早停
            if early_stopping and patience_counter >= early_stopping:
                print(f"\nEarly stopping at epoch {epoch}")
                break

        total_time = time.time() - start_time
        print("-" * 60)
        print(f"Training completed in {total_time:.1f}s")
        print(f"Best validation accuracy: {self.best_val_acc:.2f}%")

        # 加载最佳模型
        if self.best_model_state:
            self.model.load_state_dict(self.best_model_state)

        return self.history

    def test(self) -> Tuple[float, float]:
        """
        在测试集上评估模型

        返回：
            (测试损失, 测试准确率)
        """
        if self.test_loader is None:
            raise ValueError("Test loader not provided")

        test_loss, test_acc = self.evaluate(self.test_loader)
        print(f"\nTest Loss: {test_loss:.4f} | Test Acc: {test_acc:.2f}%")
        return test_loss, test_acc

    def save_model(self, save_dir: str):
        """
        保存模型

        参数：
            save_dir: 保存目录
        """
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        # 保存模型权重
        torch.save(self.model.state_dict(), save_path / 'model.pth')

        # 保存训练历史
        with open(save_path / 'history.json', 'w') as f:
            json.dump(self.history, f)

        # 保存模型配置
        config = {
            'model_class': self.model.__class__.__name__,
            'best_val_acc': self.best_val_acc
        }
        with open(save_path / 'config.json', 'w') as f:
            json.dump(config, f, indent=2)

    def load_model(self, load_dir: str):
        """
        加载模型

        参数：
            load_dir: 加载目录
        """
        load_path = Path(load_dir)
        self.model.load_state_dict(torch.load(load_path / 'model.pth'))

        # 加载历史
        history_path = load_path / 'history.json'
        if history_path.exists():
            with open(history_path, 'r') as f:
                self.history = json.load(f)

    def predict(self, data: torch.Tensor) -> torch.Tensor:
        """
        预测

        参数：
            data: 输入数据

        返回：
            预测结果
        """
        self.model.eval()
        with torch.no_grad():
            data = data.to(self.device)
            output = self.model(data)
            _, predicted = output.max(1)
        return predicted

    def get_confusion_matrix(self, data_loader: DataLoader) -> torch.Tensor:
        """
        获取混淆矩阵

        参数：
            data_loader: 数据加载器

        返回：
            混淆矩阵
        """
        self.model.eval()
        num_classes = 10  # MNIST有10个类别
        confusion = torch.zeros(num_classes, num_classes)

        with torch.no_grad():
            for data, target in data_loader:
                data, target = data.to(self.device), target.to(self.device)
                output = self.model(data)
                _, predicted = output.max(1)

                for t, p in zip(target, predicted):
                    confusion[t][p] += 1

        return confusion
