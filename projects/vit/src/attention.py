"""
Multi-Head Self-Attention 模块

实现 Transformer 的核心组件：多头自注意力机制。

核心思想：
    自注意力让每个 token 能够"关注"序列中所有其他 token，从而捕获全局依赖关系。
    多头机制让模型在不同的子空间中并行计算注意力，捕获不同类型的特征。

论文公式：
    Attention(Q, K, V) = softmax(Q K^T / sqrt(d_k)) V
    MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W^O
    其中 head_i = Attention(X W_i^Q, X W_i^K, X W_i^V)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional, Tuple


class MultiHeadSelfAttention(nn.Module):
    """
    多头自注意力机制

    将输入序列的每个位置与所有其他位置计算注意力权重，
    然后对值向量进行加权求和，得到新的表示。

    参数：
        embed_dim: 输入嵌入维度
        num_heads: 注意力头数
        dropout: 注意力权重的 dropout 概率
        bias: 是否使用偏置
    """

    def __init__(
        self,
        embed_dim: int = 768,
        num_heads: int = 12,
        dropout: float = 0.0,
        bias: bool = True,
    ):
        super().__init__()

        assert embed_dim % num_heads == 0, \
            f"embed_dim ({embed_dim}) 必须能被 num_heads ({num_heads}) 整除"

        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads  # 每个头的维度
        self.scale = self.head_dim ** -0.5  # 缩放因子 1/sqrt(d_k)

        # ★ 核心：Q, K, V 投影矩阵
        # 使用一个大矩阵一次性计算 Q, K, V，效率更高
        # 等价于三个独立的线性层
        self.qkv = nn.Linear(embed_dim, embed_dim * 3, bias=bias)

        # 输出投影矩阵
        self.proj = nn.Linear(embed_dim, embed_dim, bias=bias)

        # 注意力 dropout
        self.attn_dropout = nn.Dropout(dropout)

        # 输出 dropout
        self.proj_dropout = nn.Dropout(dropout)

        # 初始化
        self._init_weights()

    def _init_weights(self):
        """初始化权重"""
        nn.init.xavier_uniform_(self.qkv.weight)
        nn.init.xavier_uniform_(self.proj.weight)
        if self.qkv.bias is not None:
            nn.init.zeros_(self.qkv.bias)
        if self.proj.bias is not None:
            nn.init.zeros_(self.proj.bias)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        前向传播

        流程：
            1. 输入通过 QKV 投影得到 Q, K, V
            2. 将 Q, K, V 拆分为多个头
            3. 计算注意力分数：scores = Q @ K^T / sqrt(d_k)
            4. 应用 softmax 得到注意力权重
            5. 对 V 进行加权求和
            6. 拼接多头输出，通过输出投影

        参数：
            x: 输入张量，形状 (B, N, D)
            mask: 可选的注意力 mask

        返回：
            output: 注意力输出，形状 (B, N, D)
            attn_weights: 注意力权重，形状 (B, H, N, N)
        """
        B, N, D = x.shape

        # Step 1: QKV 投影
        # (B, N, D) -> (B, N, 3*D)
        qkv = self.qkv(x)

        # Step 2: 拆分为 Q, K, V 并分头
        # (B, N, 3*D) -> (B, N, 3, H, d_k) -> (3, B, H, N, d_k)
        qkv = qkv.reshape(B, N, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)

        # 拆分 Q, K, V
        # 每个形状: (B, H, N, d_k)
        q, k, v = qkv.unbind(0)

        # Step 3: 计算注意力分数
        # Q @ K^T: (B, H, N, d_k) @ (B, H, d_k, N) -> (B, H, N, N)
        # 除以 sqrt(d_k) 进行缩放，防止点积过大导致 softmax 梯度消失
        attn = (q @ k.transpose(-2, -1)) * self.scale

        # 应用 mask（如果提供）
        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))

        # Step 4: Softmax 归一化
        attn = F.softmax(attn, dim=-1)

        # 保存注意力权重用于可视化
        attn_weights = attn.detach()

        # 注意力 dropout
        attn = self.attn_dropout(attn)

        # Step 5: 对 V 进行加权求和
        # (B, H, N, N) @ (B, H, N, d_k) -> (B, H, N, d_k)
        out = attn @ v

        # Step 6: 拼接多头
        # (B, H, N, d_k) -> (B, N, H, d_k) -> (B, N, D)
        out = out.transpose(1, 2).reshape(B, N, D)

        # 输出投影
        out = self.proj(out)
        out = self.proj_dropout(out)

        return out, attn_weights


class Attention(nn.Module):
    """
    简化版单头注意力（用于学习理解）

    与 MultiHeadSelfAttention 功能相同，但代码更简洁易读。
    适合初学者理解注意力机制的核心原理。

    参数：
        dim: 输入维度
        dropout: dropout 概率
    """

    def __init__(self, dim: int, dropout: float = 0.0):
        super().__init__()
        self.dim = dim
        self.scale = dim ** -0.5

        self.qkv = nn.Linear(dim, dim * 3)
        self.proj = nn.Linear(dim, dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        简化版注意力前向传播

        参数：
            x: 输入 (B, N, D)

        返回：
            输出 (B, N, D)
        """
        B, N, D = x.shape

        # 计算 Q, K, V
        qkv = self.qkv(x).reshape(B, N, 3, D).permute(2, 0, 1, 3)
        q, k, v = qkv[0], qkv[1], qkv[2]

        # 注意力分数
        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = F.softmax(attn, dim=-1)
        attn = self.dropout(attn)

        # 加权求和
        out = (attn @ v)
        out = self.proj(out)

        return out
