"""
答案预测器模块

基于融合特征预测答案，支持分类和生成两种模式。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict


class AnswerPredictor(nn.Module):
    """
    答案预测器

    基于融合特征预测答案，支持多类分类。

    Args:
        input_dim: 输入特征维度
        num_answers: 答案数量（分类数）
        hidden_dim: 隐藏层维度
        dropout: Dropout 比率
    """

    def __init__(
        self,
        input_dim: int = 1024,
        num_answers: int = 1000,
        hidden_dim: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()

        self.num_answers = num_answers

        # 多层感知机
        self.classifier = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_answers),
        )

        # 初始化权重
        self._init_weights()

    def _init_weights(self):
        """初始化权重"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(
        self,
        fused_features: torch.Tensor,
        targets: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        前向传播

        Args:
            fused_features: 融合特征 [batch_size, input_dim]
            targets: 目标答案 [batch_size]（可选，用于计算损失）

        Returns:
            包含 logits 和可选 loss 的字典
        """
        # 预测 logits
        logits = self.classifier(fused_features)

        outputs = {'logits': logits}

        # 计算损失
        if targets is not None:
            loss = F.cross_entropy(logits, targets)
            outputs['loss'] = loss

            # 计算准确率
            predictions = logits.argmax(dim=1)
            accuracy = (predictions == targets).float().mean()
            outputs['accuracy'] = accuracy

        return outputs

    def predict(self, fused_features: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        预测答案

        Args:
            fused_features: 融合特征 [batch_size, input_dim]

        Returns:
            (预测类别, 置信度)
        """
        logits = self.classifier(fused_features)
        probabilities = F.softmax(logits, dim=1)
        confidence, predictions = probabilities.max(dim=1)
        return predictions, confidence

    def predict_top_k(
        self,
        fused_features: torch.Tensor,
        k: int = 5,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        预测 top-k 答案

        Args:
            fused_features: 融合特征 [batch_size, input_dim]
            k: top-k 数量

        Returns:
            (top-k 预测类别, top-k 置信度)
        """
        logits = self.classifier(fused_features)
        probabilities = F.softmax(logits, dim=1)
        confidence, predictions = probabilities.topk(k, dim=1)
        return predictions, confidence


class MultiHeadAnswerPredictor(nn.Module):
    """
    多头答案预测器

    支持多种类型答案的预测（如是否、数字、颜色等）。

    Args:
        input_dim: 输入特征维度
        answer_groups: 答案分组字典 {'group_name': num_answers}
        hidden_dim: 隐藏层维度
        dropout: Dropout 比率
    """

    def __init__(
        self,
        input_dim: int = 1024,
        answer_groups: Optional[Dict[str, int]] = None,
        hidden_dim: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()

        if answer_groups is None:
            answer_groups = {
                'yes_no': 2,
                'number': 10,
                'color': 20,
                'other': 500,
            }

        self.answer_groups = answer_groups

        # 共享特征提取
        self.shared = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
        )

        # 每个分组的预测头
        self.heads = nn.ModuleDict()
        for group_name, num_answers in answer_groups.items():
            self.heads[group_name] = nn.Linear(hidden_dim, num_answers)

        # 分组分类器
        self.group_classifier = nn.Linear(hidden_dim, len(answer_groups))

    def forward(
        self,
        fused_features: torch.Tensor,
        group_labels: Optional[torch.Tensor] = None,
        answer_labels: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        前向传播

        Args:
            fused_features: 融合特征 [batch_size, input_dim]
            group_labels: 分组标签 [batch_size]（可选）
            answer_labels: 答案标签 [batch_size]（可选）

        Returns:
            包含预测结果和损失的字典
        """
        # 共享特征
        shared_features = self.shared(fused_features)

        # 分组预测
        group_logits = self.group_classifier(shared_features)

        outputs = {
            'group_logits': group_logits,
            'head_logits': {},
        }

        # 各头预测
        for group_name, head in self.heads.items():
            outputs['head_logits'][group_name] = head(shared_features)

        return outputs
