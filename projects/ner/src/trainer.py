"""
训练器模块
==========

负责 BiLSTM-CRF 模型的训练:
1. 训练循环
2. 验证评估
3. 早停机制
4. 学习率调度
"""

from typing import Optional, Dict, List
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .model import BiLSTM_CRF
from .evaluator import Evaluator


class Trainer:
    """
    BiLSTM-CRF 训练器

    参数:
        model: BiLSTM-CRF 模型
        tag_vocab: 标签词表，用于将索引转换为标签
        learning_rate: 学习率
        weight_decay: L2 正则化
        device: 计算设备
    """

    def __init__(self, model: BiLSTM_CRF, tag_vocab=None,
                 learning_rate: float = 0.001,
                 weight_decay: float = 1e-5,
                 device: Optional[torch.device] = None):
        self.model = model
        self.device = device or torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.model.to(self.device)

        self.optimizer = torch.optim.Adam(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )

        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='max', patience=3, factor=0.5
        )

        self.evaluator = Evaluator(tag_vocab)

        self.train_losses: List[float] = []
        self.val_f1_scores: List[float] = []

    def train_epoch(self, dataloader: DataLoader) -> float:
        """
        训练一个 epoch

        参数:
            dataloader: 训练数据加载器

        返回:
            avg_loss: 平均损失
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for tokens, tags, mask in dataloader:
            tokens = tokens.to(self.device)
            tags = tags.to(self.device)
            mask = mask.to(self.device)

            # 前向传播
            loss = self.model(tokens, tags, mask)

            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()

            # 梯度裁剪
            nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=5.0)

            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        self.train_losses.append(avg_loss)
        return avg_loss

    def evaluate(self, dataloader: DataLoader) -> Dict:
        """
        评估模型

        参数:
            dataloader: 评估数据加载器

        返回:
            metrics: 评估指标
        """
        self.model.eval()
        all_true_tags = []
        all_pred_tags = []
        all_masks = []

        with torch.no_grad():
            for tokens, tags, mask in dataloader:
                tokens = tokens.to(self.device)
                mask = mask.to(self.device)

                # 解码
                pred_tags = self.model.decode(tokens, mask)

                # 收集结果
                for i in range(len(tokens)):
                    seq_len = int(mask[i].sum().item())
                    true_tag_seq = tags[i][:seq_len].tolist()
                    pred_tag_seq = pred_tags[i][:seq_len]

                    all_true_tags.append(true_tag_seq)
                    all_pred_tags.append(pred_tag_seq)
                    all_masks.append([1] * seq_len)

        # 使用评估器计算指标
        results = self.evaluator.evaluate_from_indices(
            all_true_tags, all_pred_tags, all_masks
        )

        return results

    def train(self, train_loader: DataLoader, val_loader: DataLoader,
              num_epochs: int = 50, early_stopping: int = 5,
              verbose: bool = True) -> Dict:
        """
        完整训练流程

        参数:
            train_loader: 训练数据加载器
            val_loader: 验证数据加载器
            num_epochs: 训练轮数
            early_stopping: 早停轮数
            verbose: 是否打印进度

        返回:
            history: 训练历史
        """
        best_f1 = 0.0
        patience_counter = 0
        best_state = None

        for epoch in range(num_epochs):
            # 训练
            avg_loss = self.train_epoch(train_loader)

            # 验证
            val_results = self.evaluate(val_loader)
            val_f1 = val_results["overall"]["f1"]
            self.val_f1_scores.append(val_f1)

            # 学习率调度
            self.scheduler.step(val_f1)

            if verbose:
                print(f"Epoch {epoch + 1}/{num_epochs} | "
                      f"Loss: {avg_loss:.4f} | "
                      f"Val F1: {val_f1:.4f} | "
                      f"Val P: {val_results['overall']['precision']:.4f} | "
                      f"Val R: {val_results['overall']['recall']:.4f}")

            # 早停检查
            if val_f1 > best_f1:
                best_f1 = val_f1
                patience_counter = 0
                best_state = {
                    k: v.cpu().clone() for k, v in self.model.state_dict().items()
                }
            else:
                patience_counter += 1
                if patience_counter >= early_stopping:
                    if verbose:
                        print(f"Early stopping at epoch {epoch + 1}")
                    break

        # 恢复最佳模型
        if best_state is not None:
            self.model.load_state_dict(best_state)

        return {
            "train_losses": self.train_losses,
            "val_f1_scores": self.val_f1_scores,
            "best_f1": best_f1
        }

    def predict(self, tokens: torch.Tensor,
                mask: torch.Tensor = None) -> List[List[str]]:
        """
        预测

        参数:
            tokens: token IDs (batch, seq_len)
            mask: 掩码 (batch, seq_len)

        返回:
            tag_sequences: 预测的标签序列
        """
        self.model.eval()
        tokens = tokens.to(self.device)
        if mask is not None:
            mask = mask.to(self.device)

        with torch.no_grad():
            pred_indices = self.model.decode(tokens, mask)

        tag_sequences = []
        for pred_seq in pred_indices:
            tag_seq = [self.evaluator.tag_vocab.get_tag(idx) for idx in pred_seq]
            tag_sequences.append(tag_seq)

        return tag_sequences
