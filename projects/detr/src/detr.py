"""
DETR 模型
端到端目标检测 Transformer
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List

from .backbone import build_backbone
from .transformer import build_transformer
from .utils import MLP, nested_tensor_from_tensor_list


class DETR(nn.Module):
    """
    DETR: Detection Transformer

    端到端目标检测模型，使用Transformer进行集合预测
    """
    def __init__(self, backbone, transformer, num_classes, num_queries, aux_loss=False):
        """
        Args:
            backbone: CNN骨干网络
            transformer: Transformer编码器-解码器
            num_classes: 类别数量
            num_queries: 查询数量（最大检测数量）
            aux_loss: 是否使用辅助损失（解码器中间层）
        """
        super().__init__()
        self.num_queries = num_queries
        self.transformer = transformer
        hidden_dim = transformer.d_model

        # 分类头：预测类别
        self.class_embed = nn.Linear(hidden_dim, num_classes + 1)

        # 边界框头：预测边界框 [cx, cy, w, h]
        self.bbox_embed = MLP(hidden_dim, hidden_dim, 4, 3)

        # 查询嵌入
        self.query_embed = nn.Embedding(num_queries, hidden_dim)

        # 输入投影：将骨干网络输出映射到Transformer维度
        self.input_proj = nn.Conv2d(backbone.num_channels[0], hidden_dim, kernel_size=1)

        self.backbone = backbone
        self.aux_loss = aux_loss

    def forward(self, samples):
        """
        前向传播

        Args:
            samples: 输入图像
                - NestedTensor: 包含tensor和mask

        Returns:
            输出字典：
                - pred_logits: (batch_size, num_queries, num_classes + 1)
                - pred_boxes: (batch_size, num_queries, 4)
                - aux_outputs: 辅助输出（如果启用）
        """
        if isinstance(samples, (list, torch.Tensor)):
            samples = nested_tensor_from_tensor_list(samples)

        # 特征提取
        features, pos = self.backbone(samples)

        # 获取最后一个特征图
        src, mask = features[-1].decompose()

        # Transformer前向传播
        hs = self.transformer(self.input_proj(src), mask, self.query_embed.weight, pos[-1])[0]

        # 预测
        outputs_class = self.class_embed(hs)
        outputs_coord = self.bbox_embed(hs).sigmoid()

        out = {'pred_logits': outputs_class, 'pred_boxes': outputs_coord}

        # 辅助损失
        if self.aux_loss:
            out['aux_outputs'] = self._set_aux_loss(outputs_class, outputs_coord)

        return out

    @torch.jit.unused
    def _set_aux_loss(self, outputs_class, outputs_coord):
        """
        设置辅助损失
        """
        return [{'pred_logits': a, 'pred_boxes': b}
                for a, b in zip(outputs_class[:-1], outputs_coord[:-1])]


def build_detr(num_classes=91, num_queries=100, aux_loss=False,
               backbone_model='resnet18', train_backbone=True,
               hidden_dim=256, nhead=8, num_encoder_layers=6, num_decoder_layers=6,
               dim_feedforward=2048, dropout=0.1):
    """
    构建DETR模型

    Args:
        num_classes: 类别数量（COCO有80个类别 + 背景）
        num_queries: 查询数量（最大检测数量）
        aux_loss: 是否使用辅助损失
        backbone_model: 骨干网络模型名称
        train_backbone: 是否训练骨干网络
        hidden_dim: Transformer隐藏维度
        nhead: 多头注意力头数
        num_encoder_layers: 编码器层数
        num_decoder_layers: 解码器层数
        dim_feedforward: 前馈网络维度
        dropout: Dropout概率

    Returns:
        DETR模型
    """
    backbone = build_backbone(backbone_model, train_backbone, hidden_dim)
    transformer = build_transformer(hidden_dim, nhead, num_encoder_layers, num_decoder_layers,
                                    dim_feedforward, dropout)
    model = DETR(backbone, transformer, num_classes, num_queries, aux_loss)
    return model
