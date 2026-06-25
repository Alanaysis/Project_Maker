"""
文本编码器模块

使用 RNN 或 Transformer 编码问题文本。
"""

import torch
import torch.nn as nn
from typing import Optional, Tuple, Dict


class TextEncoder(nn.Module):
    """
    文本编码器

    使用 LSTM/GRU 编码问题文本，支持词嵌入和字符级编码。

    Args:
        vocab_size: 词汇表大小
        embed_dim: 词嵌入维度
        hidden_dim: RNN 隐藏层维度
        feature_dim: 输出特征维度
        num_layers: RNN 层数
        rnn_type: RNN 类型 ('lstm' 或 'gru')
        dropout: Dropout 比率
        bidirectional: 是否使用双向 RNN
    """

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 300,
        hidden_dim: int = 512,
        feature_dim: int = 512,
        num_layers: int = 2,
        rnn_type: str = 'lstm',
        dropout: float = 0.1,
        bidirectional: bool = True,
    ):
        super().__init__()

        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        self.feature_dim = feature_dim

        # 词嵌入层
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)

        # RNN 层
        rnn_class = nn.LSTM if rnn_type == 'lstm' else nn.GRU
        self.rnn = rnn_class(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional,
        )

        # 输出维度
        rnn_output_dim = hidden_dim * 2 if bidirectional else hidden_dim

        # 特征投影层
        self.projection = nn.Sequential(
            nn.Linear(rnn_output_dim, feature_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
        )

        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        前向传播

        Args:
            input_ids: 输入 token IDs [batch_size, seq_len]
            attention_mask: 注意力掩码 [batch_size, seq_len]（可选）

        Returns:
            文本特征 [batch_size, feature_dim]
        """
        # 词嵌入
        embedded = self.embedding(input_ids)
        embedded = self.dropout(embedded)

        # RNN 编码
        output, hidden = self.rnn(embedded)

        # 获取最后一个时间步的输出（考虑双向）
        if self.bidirectional:
            # 拼接前向和后向的最后隐藏状态
            if isinstance(hidden, tuple):  # LSTM
                hidden = hidden[0]  # 只取 hidden state
            # hidden: [num_layers * 2, batch, hidden_dim]
            last_hidden = torch.cat([hidden[-2], hidden[-1]], dim=1)
        else:
            if isinstance(hidden, tuple):  # LSTM
                hidden = hidden[0]
            last_hidden = hidden[-1]

        # 投影到指定维度
        features = self.projection(last_hidden)

        return features

    def get_output_dim(self) -> int:
        """获取输出特征维度"""
        return self.feature_dim


class TransformerTextEncoder(nn.Module):
    """
    Transformer 文本编码器

    使用 Transformer Encoder 编码问题文本。

    Args:
        vocab_size: 词汇表大小
        embed_dim: 词嵌入维度
        num_heads: 注意力头数
        num_layers: Transformer 层数
        feature_dim: 输出特征维度
        max_seq_len: 最大序列长度
        dropout: Dropout 比率
    """

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 300,
        num_heads: int = 8,
        num_layers: int = 4,
        feature_dim: int = 512,
        max_seq_len: int = 50,
        dropout: float = 0.1,
    ):
        super().__init__()

        self.embed_dim = embed_dim
        self.feature_dim = feature_dim

        # 词嵌入
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)

        # 位置编码
        self.position_embedding = nn.Embedding(max_seq_len, embed_dim)

        # Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=embed_dim * 4,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers,
        )

        # 特征投影
        self.projection = nn.Sequential(
            nn.Linear(embed_dim, feature_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
        )

        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        前向传播

        Args:
            input_ids: 输入 token IDs [batch_size, seq_len]
            attention_mask: 注意力掩码 [batch_size, seq_len]（可选）

        Returns:
            文本特征 [batch_size, feature_dim]
        """
        batch_size, seq_len = input_ids.shape

        # 创建位置 IDs
        positions = torch.arange(seq_len, device=input_ids.device).unsqueeze(0).expand(batch_size, -1)

        # 词嵌入 + 位置编码
        embedded = self.embedding(input_ids) + self.position_embedding(positions)
        embedded = self.dropout(embedded)

        # 创建 padding mask
        if attention_mask is not None:
            # 转换为 Transformer 格式的 mask (True 表示忽略)
            src_key_padding_mask = (attention_mask == 0)
        else:
            src_key_padding_mask = None

        # Transformer 编码
        output = self.transformer(
            embedded,
            src_key_padding_mask=src_key_padding_mask,
        )

        # 使用 [CLS] token 或平均池化
        # 这里使用平均池化（排除 padding）
        if attention_mask is not None:
            mask = attention_mask.unsqueeze(-1).float()
            output = (output * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        else:
            output = output.mean(dim=1)

        # 投影
        features = self.projection(output)

        return features

    def get_output_dim(self) -> int:
        """获取输出特征维度"""
        return self.feature_dim
