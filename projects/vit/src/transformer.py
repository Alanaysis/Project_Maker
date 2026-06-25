"""
Transformer Encoder 模块

实现 Transformer 编码器，由多个 Transformer Block 堆叠而成。

每个 Transformer Block 包含：
1. Multi-Head Self-Attention (MHSA)
2. Feed-Forward Network (FFN)
3. Layer Normalization (Pre-LN 架构)
4. Residual Connection（残差连接）

论文公式（Pre-LN）：
    z'_l = MHSA(LN(z_{l-1})) + z_{l-1}
    z_l = FFN(LN(z'_l)) + z'_l
"""

import torch
import torch.nn as nn
from typing import Optional, Tuple

from .attention import MultiHeadSelfAttention


class FeedForward(nn.Module):
    """
    Feed-Forward Network (FFN)

    两层全连接网络，中间使用 GELU 激活函数。

    架构：Linear -> GELU -> Dropout -> Linear -> Dropout

    通常隐藏层维度是嵌入维度的 4 倍（如 768 -> 3072）

    参数：
        in_features: 输入维度
        hidden_features: 隐藏层维度（默认为输入维度的 4 倍）
        dropout: dropout 概率
    """

    def __init__(
        self,
        in_features: int,
        hidden_features: Optional[int] = None,
        dropout: float = 0.0,
    ):
        super().__init__()

        hidden_features = hidden_features or in_features * 4

        self.fc1 = nn.Linear(in_features, hidden_features)
        self.act = nn.GELU()
        self.drop1 = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden_features, in_features)
        self.drop2 = nn.Dropout(dropout)

        self._init_weights()

    def _init_weights(self):
        """初始化权重"""
        nn.init.xavier_uniform_(self.fc1.weight)
        nn.init.xavier_uniform_(self.fc2.weight)
        nn.init.zeros_(self.fc1.bias)
        nn.init.zeros_(self.fc2.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        参数：
            x: 输入 (B, N, D)

        返回：
            输出 (B, N, D)
        """
        x = self.fc1(x)
        x = self.act(x)
        x = self.drop1(x)
        x = self.fc2(x)
        x = self.drop2(x)
        return x


class TransformerBlock(nn.Module):
    """
    Transformer 编码器块

    单个 Transformer 编码器层，包含：
    1. Layer Norm + Multi-Head Self-Attention + Residual Connection
    2. Layer Norm + Feed-Forward Network + Residual Connection

    采用 Pre-LN 架构（Layer Normalization 放在注意力/FFN 之前），
    这比 Post-LN 架构训练更稳定。

    参数：
        embed_dim: 嵌入维度
        num_heads: 注意力头数
        mlp_ratio: FFN 隐藏层维度与嵌入维度的比率
        dropout: dropout 概率
        attention_dropout: 注意力 dropout 概率
    """

    def __init__(
        self,
        embed_dim: int = 768,
        num_heads: int = 12,
        mlp_ratio: float = 4.0,
        dropout: float = 0.0,
        attention_dropout: float = 0.0,
    ):
        super().__init__()

        # 第一个子层：Layer Norm + Multi-Head Self-Attention
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn = MultiHeadSelfAttention(
            embed_dim=embed_dim,
            num_heads=num_heads,
            dropout=attention_dropout,
        )

        # 第二个子层：Layer Norm + Feed-Forward Network
        self.norm2 = nn.LayerNorm(embed_dim)
        self.ffn = FeedForward(
            in_features=embed_dim,
            hidden_features=int(embed_dim * mlp_ratio),
            dropout=dropout,
        )

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        前向传播

        Pre-LN 流程：
            1. z' = MHSA(LN(x)) + x    （自注意力 + 残差）
            2. z  = FFN(LN(z')) + z'    （前馈网络 + 残差）

        参数：
            x: 输入 (B, N, D)
            mask: 可选的注意力 mask

        返回：
            output: 输出 (B, N, D)
            attn_weights: 注意力权重 (B, H, N, N)
        """
        # 子层 1: Self-Attention
        residual = x
        x_norm = self.norm1(x)
        attn_out, attn_weights = self.attn(x_norm, mask=mask)
        x = residual + attn_out  # 残差连接

        # 子层 2: Feed-Forward
        residual = x
        x_norm = self.norm2(x)
        ffn_out = self.ffn(x_norm)
        x = residual + ffn_out  # 残差连接

        return x, attn_weights


class TransformerEncoder(nn.Module):
    """
    Transformer 编码器

    由多个 Transformer Block 堆叠而成，形成深层的特征提取网络。

    参数：
        embed_dim: 嵌入维度
        depth: Transformer Block 的层数
        num_heads: 注意力头数
        mlp_ratio: FFN 隐藏层维度比率
        dropout: dropout 概率
        attention_dropout: 注意力 dropout 概率
    """

    def __init__(
        self,
        embed_dim: int = 768,
        depth: int = 12,
        num_heads: int = 12,
        mlp_ratio: float = 4.0,
        dropout: float = 0.0,
        attention_dropout: float = 0.0,
    ):
        super().__init__()

        self.embed_dim = embed_dim
        self.depth = depth

        # 堆叠 Transformer Block
        self.blocks = nn.ModuleList([
            TransformerBlock(
                embed_dim=embed_dim,
                num_heads=num_heads,
                mlp_ratio=mlp_ratio,
                dropout=dropout,
                attention_dropout=attention_dropout,
            )
            for _ in range(depth)
        ])

        # 最终 Layer Normalization
        self.norm = nn.LayerNorm(embed_dim)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, list]:
        """
        前向传播

        流程：
            1. 依次通过每个 Transformer Block
            2. 最终 Layer Normalization

        参数：
            x: 输入 (B, N, D)
            mask: 可选的注意力 mask

        返回：
            output: 编码器输出 (B, N, D)
            all_attn_weights: 每层的注意力权重列表
        """
        all_attn_weights = []

        for block in self.blocks:
            x, attn_weights = block(x, mask=mask)
            all_attn_weights.append(attn_weights)

        x = self.norm(x)

        return x, all_attn_weights
