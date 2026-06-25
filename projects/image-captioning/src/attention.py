"""
Attention Mechanism - 注意力机制

实现 Bahdanau (Additive) 注意力机制，让解码器在生成每个词时
能够"关注"图像的不同区域。

核心思想：
- 解码器在每个时间步计算一个注意力权重分布
- 权重分布表示图像各区域对当前词生成的重要性
- 加权求和得到上下文向量 (context vector)
- 上下文向量与解码器状态一起用于预测下一个词

数学公式：
    score = V * tanh(W_h * h_decoder + W_v * v_image)
    attention_weights = softmax(score)
    context = sum(attention_weights * v_image)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class Attention(nn.Module):
    """Bahdanau (Additive) 注意力机制。

    计算解码器隐藏状态与图像特征之间的注意力权重，
    生成加权上下文向量。
    """

    def __init__(self, encoder_dim: int, decoder_dim: int, attention_dim: int = 256):
        """初始化注意力模块。

        Args:
            encoder_dim: 编码器输出特征维度 (embed_dim)
            decoder_dim: 解码器隐藏状态维度
            attention_dim: 注意力内部计算维度
        """
        super().__init__()
        self.encoder_dim = encoder_dim
        self.decoder_dim = decoder_dim
        self.attention_dim = attention_dim

        # 将编码器特征映射到注意力空间
        self.encoder_att = nn.Linear(encoder_dim, attention_dim)
        # 将解码器隐藏状态映射到注意力空间
        self.decoder_att = nn.Linear(decoder_dim, attention_dim)
        # 计算注意力分数
        self.full_att = nn.Linear(attention_dim, 1)

        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=-1)

    def forward(
        self, encoder_out: torch.Tensor, decoder_hidden: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """计算注意力权重和上下文向量。

        Args:
            encoder_out: 编码器输出特征 (batch_size, num_pixels, encoder_dim)
            decoder_hidden: 解码器当前隐藏状态 (batch_size, decoder_dim)

        Returns:
            context: 上下文向量 (batch_size, encoder_dim)
            attention_weights: 注意力权重 (batch_size, num_pixels)
        """
        # 将编码器特征映射到注意力空间: (batch, num_pixels, attention_dim)
        att_encoder = self.encoder_att(encoder_out)

        # 将解码器隐藏状态映射到注意力空间: (batch, attention_dim)
        att_decoder = self.decoder_att(decoder_hidden)

        # 计算注意力分数: (batch, num_pixels, 1) -> (batch, num_pixels)
        # 广播：att_decoder 扩展维度与 att_encoder 相加
        attention_scores = self.full_att(
            self.relu(att_encoder + att_decoder.unsqueeze(1))
        ).squeeze(-1)

        # 归一化为概率分布
        attention_weights = self.softmax(attention_scores)  # (batch, num_pixels)

        # 加权求和得到上下文向量: (batch, encoder_dim)
        context = torch.sum(
            encoder_out * attention_weights.unsqueeze(-1), dim=1
        )

        return context, attention_weights


class ScaledDotProductAttention(nn.Module):
    """缩放点积注意力 (Scaled Dot-Product Attention)。

    Transformer 风格的注意力机制，作为 Bahdanau 注意力的替代方案。
    score = Q * K^T / sqrt(d_k)
    """

    def __init__(self, encoder_dim: int, decoder_dim: int, attention_dim: int = 256):
        """初始化缩放点积注意力模块。

        Args:
            encoder_dim: 编码器输出特征维度
            decoder_dim: 解码器隐藏状态维度
            attention_dim: 注意力内部计算维度
        """
        super().__init__()
        self.scale = attention_dim ** 0.5

        self.query = nn.Linear(decoder_dim, attention_dim)
        self.key = nn.Linear(encoder_dim, attention_dim)
        self.value = nn.Linear(encoder_dim, attention_dim)

        self.softmax = nn.Softmax(dim=-1)

    def forward(
        self, encoder_out: torch.Tensor, decoder_hidden: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """计算缩放点积注意力。

        Args:
            encoder_out: 编码器输出特征 (batch_size, num_pixels, encoder_dim)
            decoder_hidden: 解码器当前隐藏状态 (batch_size, decoder_dim)

        Returns:
            context: 上下文向量 (batch_size, attention_dim)
            attention_weights: 注意力权重 (batch_size, num_pixels)
        """
        # Q: (batch, 1, attention_dim)
        Q = self.query(decoder_hidden).unsqueeze(1)
        # K: (batch, num_pixels, attention_dim)
        K = self.key(encoder_out)
        # V: (batch, num_pixels, attention_dim)
        V = self.value(encoder_out)

        # 计算注意力分数: (batch, 1, num_pixels)
        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale
        scores = scores.squeeze(1)  # (batch, num_pixels)

        attention_weights = self.softmax(scores)  # (batch, num_pixels)

        # 加权求和: (batch, attention_dim)
        context = torch.sum(
            V * attention_weights.unsqueeze(-1), dim=1
        )

        return context, attention_weights
