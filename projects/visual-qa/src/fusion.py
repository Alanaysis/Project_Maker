"""
多模态融合模块

实现图像和文本特征的融合策略，包括拼接、注意力融合等。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class ConcatFusion(nn.Module):
    """
    拼接融合

    将图像和文本特征简单拼接后通过全连接层。

    Args:
        image_dim: 图像特征维度
        text_dim: 文本特征维度
        output_dim: 输出维度
        dropout: Dropout 比率
    """

    def __init__(
        self,
        image_dim: int,
        text_dim: int,
        output_dim: int = 1024,
        dropout: float = 0.1,
    ):
        super().__init__()

        self.fc = nn.Sequential(
            nn.Linear(image_dim + text_dim, output_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(output_dim, output_dim),
            nn.ReLU(inplace=True),
        )

    def forward(
        self,
        image_features: torch.Tensor,
        text_features: torch.Tensor,
    ) -> torch.Tensor:
        """
        前向传播

        Args:
            image_features: 图像特征 [batch_size, image_dim]
            text_features: 文本特征 [batch_size, text_dim]

        Returns:
            融合特征 [batch_size, output_dim]
        """
        # 拼接特征
        combined = torch.cat([image_features, text_features], dim=1)
        # 通过全连接层
        fused = self.fc(combined)
        return fused


class BilinearFusion(nn.Module):
    """
    双线性融合

    使用双线性池化融合图像和文本特征。

    Args:
        image_dim: 图像特征维度
        text_dim: 文本特征维度
        output_dim: 输出维度
        dropout: Dropout 比率
    """

    def __init__(
        self,
        image_dim: int,
        text_dim: int,
        output_dim: int = 1024,
        dropout: float = 0.1,
    ):
        super().__init__()

        self.bilinear = nn.Bilinear(image_dim, text_dim, output_dim)
        self.fc = nn.Sequential(
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
        )

    def forward(
        self,
        image_features: torch.Tensor,
        text_features: torch.Tensor,
    ) -> torch.Tensor:
        """
        前向传播

        Args:
            image_features: 图像特征 [batch_size, image_dim]
            text_features: 文本特征 [batch_size, text_dim]

        Returns:
            融合特征 [batch_size, output_dim]
        """
        fused = self.bilinear(image_features, text_features)
        fused = self.fc(fused)
        return fused


class AttentionFusion(nn.Module):
    """
    注意力融合

    使用注意力机制融合图像和文本特征。

    Args:
        image_dim: 图像特征维度
        text_dim: 文本特征维度
        output_dim: 输出维度
        num_heads: 注意力头数
        dropout: Dropout 比率
    """

    def __init__(
        self,
        image_dim: int,
        text_dim: int,
        output_dim: int = 1024,
        num_heads: int = 8,
        dropout: float = 0.1,
    ):
        super().__init__()

        # 将维度对齐
        self.image_proj = nn.Linear(image_dim, output_dim)
        self.text_proj = nn.Linear(text_dim, output_dim)

        # 交叉注意力
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=output_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
        )

        # 前馈网络
        self.ffn = nn.Sequential(
            nn.Linear(output_dim, output_dim * 4),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(output_dim * 4, output_dim),
        )

        # 层归一化
        self.norm1 = nn.LayerNorm(output_dim)
        self.norm2 = nn.LayerNorm(output_dim)

        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        image_features: torch.Tensor,
        text_features: torch.Tensor,
    ) -> torch.Tensor:
        """
        前向传播

        Args:
            image_features: 图像特征 [batch_size, image_dim]
            text_features: 文本特征 [batch_size, text_dim]

        Returns:
            融合特征 [batch_size, output_dim]
        """
        # 投影到相同维度
        image_proj = self.image_proj(image_features).unsqueeze(1)  # [batch, 1, dim]
        text_proj = self.text_proj(text_features).unsqueeze(1)  # [batch, 1, dim]

        # 拼接作为 key/value
        kv = torch.cat([image_proj, text_proj], dim=1)  # [batch, 2, dim]

        # 交叉注意力：用图像特征查询文本信息
        attended, _ = self.cross_attention(
            query=image_proj,
            key=kv,
            value=kv,
        )

        # 残差连接 + 层归一化
        attended = self.norm1(attended + image_proj)

        # 前馈网络
        ffn_out = self.ffn(attended)
        fused = self.norm2(ffn_out + attended)

        # 压缩序列维度
        fused = fused.squeeze(1)

        return fused


class CoAttentionFusion(nn.Module):
    """
    协同注意力融合

    图像和文本之间的双向注意力融合。

    Args:
        image_dim: 图像特征维度
        text_dim: 文本特征维度
        output_dim: 输出维度
        dropout: Dropout 比率
    """

    def __init__(
        self,
        image_dim: int,
        text_dim: int,
        output_dim: int = 1024,
        dropout: float = 0.1,
    ):
        super().__init__()

        # 投影层
        self.image_proj = nn.Linear(image_dim, output_dim)
        self.text_proj = nn.Linear(text_dim, output_dim)

        # 图像到文本注意力
        self.i2t_attention = nn.Sequential(
            nn.Linear(output_dim * 2, output_dim),
            nn.Tanh(),
            nn.Linear(output_dim, 1),
        )

        # 文本到图像注意力
        self.t2i_attention = nn.Sequential(
            nn.Linear(output_dim * 2, output_dim),
            nn.Tanh(),
            nn.Linear(output_dim, 1),
        )

        # 融合层
        self.fusion = nn.Sequential(
            nn.Linear(output_dim * 2, output_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
        )

        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        image_features: torch.Tensor,
        text_features: torch.Tensor,
    ) -> torch.Tensor:
        """
        前向传播

        Args:
            image_features: 图像特征 [batch_size, image_dim]
            text_features: 文本特征 [batch_size, text_dim]

        Returns:
            融合特征 [batch_size, output_dim]
        """
        # 投影
        image_proj = self.image_proj(image_features)  # [batch, dim]
        text_proj = self.text_proj(text_features)  # [batch, dim]

        # 扩展维度用于注意力计算
        image_exp = image_proj.unsqueeze(1)  # [batch, 1, dim]
        text_exp = text_proj.unsqueeze(1)  # [batch, 1, dim]

        # 图像到文本注意力
        image_text_concat = torch.cat([
            image_exp.expand(-1, 1, -1),
            text_exp.expand(-1, 1, -1),
        ], dim=-1)
        i2t_weights = torch.softmax(self.i2t_attention(image_text_concat), dim=1)
        text_attended = (text_exp * i2t_weights).squeeze(1)

        # 文本到图像注意力
        t2i_weights = torch.softmax(self.t2i_attention(image_text_concat), dim=1)
        image_attended = (image_exp * t2i_weights).squeeze(1)

        # 融合
        fused = self.fusion(torch.cat([image_attended, text_attended], dim=1))

        return fused


class FusionModule(nn.Module):
    """
    融合模块包装器

    统一接口，支持多种融合策略。

    Args:
        fusion_type: 融合类型 ('concat', 'bilinear', 'attention', 'co_attention')
        image_dim: 图像特征维度
        text_dim: 文本特征维度
        output_dim: 输出维度
        **kwargs: 其他参数
    """

    def __init__(
        self,
        fusion_type: str = 'concat',
        image_dim: int = 512,
        text_dim: int = 512,
        output_dim: int = 1024,
        **kwargs,
    ):
        super().__init__()

        self.fusion_type = fusion_type

        if fusion_type == 'concat':
            self.fusion = ConcatFusion(image_dim, text_dim, output_dim, **kwargs)
        elif fusion_type == 'bilinear':
            self.fusion = BilinearFusion(image_dim, text_dim, output_dim, **kwargs)
        elif fusion_type == 'attention':
            self.fusion = AttentionFusion(image_dim, text_dim, output_dim, **kwargs)
        elif fusion_type == 'co_attention':
            self.fusion = CoAttentionFusion(image_dim, text_dim, output_dim, **kwargs)
        else:
            raise ValueError(f"不支持的融合类型: {fusion_type}")

    def forward(
        self,
        image_features: torch.Tensor,
        text_features: torch.Tensor,
    ) -> torch.Tensor:
        """
        前向传播

        Args:
            image_features: 图像特征 [batch_size, image_dim]
            text_features: 文本特征 [batch_size, text_dim]

        Returns:
            融合特征 [batch_size, output_dim]
        """
        return self.fusion(image_features, text_features)

    def get_output_dim(self) -> int:
        """获取输出维度"""
        return self.fusion.fc[-2].out_features if hasattr(self.fusion, 'fc') else 1024
