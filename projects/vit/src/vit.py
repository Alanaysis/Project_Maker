"""
Vision Transformer (ViT) 完整模型

实现论文 "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale"
(Dosovitskiy et al., 2020) 中提出的 Vision Transformer 架构。

核心流程：
    图像 -> Patch Embedding -> Transformer Encoder -> [CLS] token -> 分类头 -> 输出

架构图：
    ┌─────────┐
    │  Image   │  (B, C, H, W)
    └────┬────┘
         │
    ┌────▼────────────────────┐
    │  Patch Embedding        │  (B, N+1, D)
    │  + CLS Token            │
    │  + Position Embedding   │
    └────┬────────────────────┘
         │
    ┌────▼────────────────────┐
    │  Transformer Encoder    │  (B, N+1, D)
    │  x L layers             │
    └────┬────────────────────┘
         │
    ┌────▼────┐
    │ CLS Head│  取 [CLS] token 的输出
    └────┬────┘
         │
    ┌────▼────┐
    │  MLP    │  Linear -> Tanh -> Linear
    │  Head   │
    └────┬────┘
         │
    ┌────▼────┐
    │  Output │  (B, num_classes)
    └─────────┘
"""

import torch
import torch.nn as nn
from typing import Optional, Tuple

from .patch_embedding import PatchEmbedding
from .transformer import TransformerEncoder


class MLPHead(nn.Module):
    """
    分类头（MLP Head）

    用于将 [CLS] token 的表示映射到类别空间。

    架构（原论文）：Linear -> Tanh -> Linear
    这里也提供了简单的单层线性头作为备选。

    参数：
        in_features: 输入维度
        hidden_features: 隐藏层维度（None 表示使用单层线性头）
        out_features: 输出类别数
        dropout: dropout 概率
    """

    def __init__(
        self,
        in_features: int,
        hidden_features: Optional[int] = None,
        out_features: int = 1000,
        dropout: float = 0.0,
    ):
        super().__init__()

        if hidden_features is not None:
            # 原论文使用的 MLP 头
            self.head = nn.Sequential(
                nn.Linear(in_features, hidden_features),
                nn.Tanh(),
                nn.Dropout(dropout),
                nn.Linear(hidden_features, out_features),
            )
        else:
            # 简单的线性头
            self.head = nn.Linear(in_features, out_features)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(x)


class VisionTransformer(nn.Module):
    """
    Vision Transformer (ViT)

    完整的 Vision Transformer 模型，用于图像分类任务。

    参数：
        img_size: 输入图像尺寸
        patch_size: patch 大小
        in_channels: 输入通道数
        num_classes: 分类类别数
        embed_dim: 嵌入维度
        depth: Transformer 层数
        num_heads: 注意力头数
        mlp_ratio: FFN 隐藏层维度比率
        dropout: dropout 概率
        attention_dropout: 注意力 dropout 概率
        representation_size: MLP Head 隐藏层维度（None 表示使用线性头）

    预定义配置：
        - ViT-Ti (Tiny):   embed_dim=192, depth=4,  heads=3
        - ViT-S  (Small):  embed_dim=384, depth=8,  heads=6
        - ViT-B  (Base):   embed_dim=768, depth=12, heads=12
        - ViT-L  (Large):  embed_dim=1024, depth=24, heads=16
        - ViT-H  (Huge):   embed_dim=1280, depth=32, heads=16
    """

    def __init__(
        self,
        img_size: int = 224,
        patch_size: int = 16,
        in_channels: int = 3,
        num_classes: int = 1000,
        embed_dim: int = 768,
        depth: int = 12,
        num_heads: int = 12,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1,
        attention_dropout: float = 0.0,
        representation_size: Optional[int] = None,
    ):
        super().__init__()

        self.num_classes = num_classes
        self.embed_dim = embed_dim

        # 1. Patch Embedding 层
        # 将图像分割为 patches，添加 CLS token 和位置编码
        self.patch_embedding = PatchEmbedding(
            img_size=img_size,
            patch_size=patch_size,
            in_channels=in_channels,
            embed_dim=embed_dim,
        )

        # 2. Embedding Dropout
        self.embed_dropout = nn.Dropout(dropout)

        # 3. Transformer Encoder
        # 多层 Transformer Block 堆叠
        self.transformer = TransformerEncoder(
            embed_dim=embed_dim,
            depth=depth,
            num_heads=num_heads,
            mlp_ratio=mlp_ratio,
            dropout=dropout,
            attention_dropout=attention_dropout,
        )

        # 4. 分类头
        # 取 [CLS] token 的输出，通过 MLP 映射到类别空间
        self.classifier = MLPHead(
            in_features=embed_dim,
            hidden_features=representation_size,
            out_features=num_classes,
        )

        # 初始化所有权重
        self.apply(self._init_weights)

    def _init_weights(self, m: nn.Module):
        """
        权重初始化策略

        - Linear 层：Xavier 均匀分布
        - LayerNorm：权重为 1，偏置为 0
        """
        if isinstance(m, nn.Linear):
            nn.init.xavier_uniform_(m.weight)
            if m.bias is not None:
                nn.init.zeros_(m.bias)
        elif isinstance(m, nn.LayerNorm):
            nn.init.ones_(m.weight)
            nn.init.zeros_(m.bias)

    def forward(
        self,
        x: torch.Tensor,
        return_attention: bool = False,
    ) -> Tuple[torch.Tensor, Optional[list]]:
        """
        前向传播

        流程：
            1. Patch Embedding：图像 -> patch 序列
            2. Embedding Dropout
            3. Transformer Encoder：多层自注意力 + FFN
            4. 取 [CLS] token 的输出
            5. 分类头：映射到类别空间

        参数：
            x: 输入图像 (B, C, H, W)
            return_attention: 是否返回注意力权重（用于可视化）

        返回：
            logits: 分类 logits (B, num_classes)
            all_attn_weights: 注意力权重列表（如果 return_attention=True）
        """
        # Step 1: Patch Embedding
        # (B, C, H, W) -> (B, N+1, D)
        x = self.patch_embedding(x)

        # Step 2: Embedding Dropout
        x = self.embed_dropout(x)

        # Step 3: Transformer Encoder
        # (B, N+1, D) -> (B, N+1, D)
        x, all_attn_weights = self.transformer(x)

        # Step 4: 取 [CLS] token 的输出
        # [CLS] token 在序列的第一个位置（index 0）
        # (B, N+1, D) -> (B, D)
        cls_output = x[:, 0]

        # Step 5: 分类头
        # (B, D) -> (B, num_classes)
        logits = self.classifier(cls_output)

        if return_attention:
            return logits, all_attn_weights
        return logits, None

    def get_attention_maps(
        self,
        x: torch.Tensor,
    ) -> list:
        """
        获取注意力图（用于可视化）

        参数：
            x: 输入图像 (B, C, H, W)

        返回：
            all_attn_weights: 每层的注意力权重 (B, H, N+1, N+1)
        """
        _, all_attn_weights = self.forward(x, return_attention=True)
        return all_attn_weights

    @staticmethod
    def vit_tiny(
        img_size: int = 224,
        patch_size: int = 16,
        num_classes: int = 10,
        **kwargs
    ) -> 'VisionTransformer':
        """ViT-Tiny 配置：适合小数据集和快速实验"""
        return VisionTransformer(
            img_size=img_size,
            patch_size=patch_size,
            num_classes=num_classes,
            embed_dim=192,
            depth=4,
            num_heads=3,
            **kwargs,
        )

    @staticmethod
    def vit_small(
        img_size: int = 224,
        patch_size: int = 16,
        num_classes: int = 10,
        **kwargs
    ) -> 'VisionTransformer':
        """ViT-Small 配置"""
        return VisionTransformer(
            img_size=img_size,
            patch_size=patch_size,
            num_classes=num_classes,
            embed_dim=384,
            depth=8,
            num_heads=6,
            **kwargs,
        )

    @staticmethod
    def vit_base(
        img_size: int = 224,
        patch_size: int = 16,
        num_classes: int = 1000,
        **kwargs
    ) -> 'VisionTransformer':
        """ViT-Base 配置：原论文标准配置"""
        return VisionTransformer(
            img_size=img_size,
            patch_size=patch_size,
            num_classes=num_classes,
            embed_dim=768,
            depth=12,
            num_heads=12,
            **kwargs,
        )
