"""
BiLSTM-CRF 模型
===============

结合双向 LSTM 和 CRF 的序列标注模型:

架构:
  Input -> Embedding -> BiLSTM -> Linear -> CRF -> Output

原理:
1. Embedding: 将离散的词/字符映射为连续向量
2. BiLSTM: 捕获上下文信息 (前向 + 后向)
3. Linear: 将隐状态映射为发射分数
4. CRF: 建模标签之间的转移关系，解码最优序列

为什么需要 CRF?
- 纯 LSTM 输出独立地为每个位置预测标签，不考虑标签间的依赖
- 例如: I-PER 不应该跟在 B-LOC 后面
- CRF 通过转移矩阵学习标签之间的合法转移
"""

import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

from .crf import CRF


class BiLSTM_CRF(nn.Module):
    """
    BiLSTM-CRF 序列标注模型

    参数:
        vocab_size: 词表大小
        num_tags: 标签数量
        embedding_dim: 词嵌入维度
        hidden_dim: LSTM 隐藏层维度
        num_layers: LSTM 层数
        dropout: Dropout 概率
        pad_idx: 填充索引
    """

    def __init__(self, vocab_size: int, num_tags: int,
                 embedding_dim: int = 128, hidden_dim: int = 256,
                 num_layers: int = 1, dropout: float = 0.5,
                 pad_idx: int = 0):
        super().__init__()
        self.vocab_size = vocab_size
        self.num_tags = num_tags
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.pad_idx = pad_idx

        # 词嵌入层
        self.embedding = nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=embedding_dim,
            padding_idx=pad_idx
        )

        # 双向 LSTM
        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0
        )

        # Dropout
        self.dropout = nn.Dropout(dropout)

        # 线性层: 将 BiLSTM 输出映射到标签空间
        # BiLSTM 输出维度 = hidden_dim * 2 (双向)
        self.hidden2tag = nn.Linear(hidden_dim * 2, num_tags)

        # CRF 层
        self.crf = CRF(num_tags, batch_first=True)

        self._init_weights()

    def _init_weights(self):
        """初始化权重"""
        nn.init.xavier_uniform_(self.embedding.weight)
        # 填充向量设为 0
        with torch.no_grad():
            self.embedding.weight[self.pad_idx].fill_(0)

        nn.init.xavier_uniform_(self.hidden2tag.weight)
        nn.init.zeros_(self.hidden2tag.bias)

    def forward(self, tokens: torch.Tensor, tags: torch.Tensor,
                mask: torch.Tensor = None) -> torch.Tensor:
        """
        前向传播 - 计算损失

        参数:
            tokens: 输入 token IDs (batch, seq_len)
            tags: 真实标签 (batch, seq_len)
            mask: 掩码 (batch, seq_len)

        返回:
            loss: CRF 负对数似然损失
        """
        emissions = self._get_emissions(tokens, mask)
        loss = self.crf(emissions, tags, mask)
        return loss

    def decode(self, tokens: torch.Tensor,
               mask: torch.Tensor = None) -> list:
        """
        解码 - 找到最优标签序列

        参数:
            tokens: 输入 token IDs (batch, seq_len)
            mask: 掩码 (batch, seq_len)

        返回:
            best_tags: 最优标签序列列表
        """
        emissions = self._get_emissions(tokens, mask)
        return self.crf.decode(emissions, mask)

    def _get_emissions(self, tokens: torch.Tensor,
                       mask: torch.Tensor = None) -> torch.Tensor:
        """
        计算发射分数

        流程: tokens -> embedding -> BiLSTM -> linear -> emissions
        """
        # 词嵌入
        embeds = self.dropout(self.embedding(tokens))  # (batch, seq_len, emb_dim)

        # 处理变长序列
        if mask is not None:
            seq_lengths = mask.sum(dim=1).long()
            packed = pack_padded_sequence(
                embeds, seq_lengths.cpu(), batch_first=True, enforce_sorted=False
            )
            lstm_out, _ = self.lstm(packed)
            lstm_out, _ = pad_packed_sequence(lstm_out, batch_first=True)
        else:
            lstm_out, _ = self.lstm(embeds)

        lstm_out = self.dropout(lstm_out)

        # 线性映射到标签空间
        emissions = self.hidden2tag(lstm_out)  # (batch, seq_len, num_tags)

        return emissions
