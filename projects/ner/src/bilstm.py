"""
独立 BiLSTM 序列标注模型
========================

不带 CRF 层的 BiLSTM 模型，独立预测每个位置的标签。

与 BiLSTM-CRF 的区别:
- BiLSTM: 独立预测每个位置，不考虑标签间依赖
- BiLSTM-CRF: 加入 CRF 层，建模标签间依赖关系

BiLSTM 通常比 BiLSTM-CRF 效果差一些，因为:
- 可能产生非法标签序列 (如 I-PER 跟在 B-LOC 后面)
- 无法利用标签间的转移规律

但 BiLSTM 也有优势:
- 训练更快 (不需要前向算法)
- 实现更简单
- 预测更快 (不需要维特比解码)
"""

import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
from typing import List, Optional


class BiLSTM(nn.Module):
    """
    独立 BiLSTM 序列标注模型

    架构: Input -> Embedding -> BiLSTM -> Linear -> Output

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
        self.hidden2tag = nn.Linear(hidden_dim * 2, num_tags)

        self._init_weights()

    def _init_weights(self):
        """初始化权重"""
        nn.init.xavier_uniform_(self.embedding.weight)
        with torch.no_grad():
            self.embedding.weight[self.pad_idx].fill_(0)

        nn.init.xavier_uniform_(self.hidden2tag.weight)
        nn.init.zeros_(self.hidden2tag.bias)

    def forward(self, tokens: torch.Tensor, mask: torch.Tensor = None) -> torch.Tensor:
        """
        前向传播 - 计算发射分数

        参数:
            tokens: 输入 token IDs (batch, seq_len)
            mask: 掩码 (batch, seq_len)

        返回:
            emissions: 发射分数 (batch, seq_len, num_tags)
        """
        # 词嵌入
        embeds = self.dropout(self.embedding(tokens))

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
        emissions = self.hidden2tag(lstm_out)

        return emissions

    def decode(self, tokens: torch.Tensor,
               mask: torch.Tensor = None) -> List[List[int]]:
        """
        解码 - 独立预测每个位置的标签

        参数:
            tokens: 输入 token IDs (batch, seq_len)
            mask: 掩码 (batch, seq_len)

        返回:
            best_tags: 最优标签索引序列列表
        """
        emissions = self.forward(tokens, mask)
        # 独立取 argmax
        best_tags = emissions.argmax(dim=-1)  # (batch, seq_len)

        # 应用掩码
        if mask is not None:
            seq_lengths = mask.sum(dim=1).long()
            result = []
            for i in range(len(tokens)):
                seq_len = seq_lengths[i].item()
                result.append(best_tags[i][:seq_len].tolist())
            return result
        else:
            return best_tags.tolist()


class BiLSTMWithSoftmax(nn.Module):
    """
    带 Softmax 的 BiLSTM 模型

    使用 CrossEntropyLoss 训练，输出概率分布。

    与 BiLSTM 的区别:
    - BiLSTM: 输出原始分数，配合 CRF 使用
    - BiLSTMWithSoftmax: 输出概率，使用 CrossEntropyLoss
    """

    def __init__(self, vocab_size: int, num_tags: int,
                 embedding_dim: int = 128, hidden_dim: int = 256,
                 num_layers: int = 1, dropout: float = 0.5,
                 pad_idx: int = 0):
        super().__init__()
        self.vocab_size = vocab_size
        self.num_tags = num_tags
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

        self.dropout = nn.Dropout(dropout)

        # 线性层
        self.hidden2tag = nn.Linear(hidden_dim * 2, num_tags)

        # 损失函数 (忽略填充位置)
        self.criterion = nn.CrossEntropyLoss(ignore_index=pad_idx)

        self._init_weights()

    def _init_weights(self):
        """初始化权重"""
        nn.init.xavier_uniform_(self.embedding.weight)
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
            loss: 交叉熵损失
        """
        # 词嵌入
        embeds = self.dropout(self.embedding(tokens))

        # BiLSTM
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

        # 线性映射
        emissions = self.hidden2tag(lstm_out)  # (batch, seq_len, num_tags)

        # 计算损失
        # CrossEntropyLoss 需要 (batch, num_classes, ...) 格式
        loss = self.criterion(
            emissions.view(-1, self.num_tags),
            tags.view(-1)
        )

        return loss

    def decode(self, tokens: torch.Tensor,
               mask: torch.Tensor = None) -> List[List[int]]:
        """
        解码

        参数:
            tokens: 输入 token IDs (batch, seq_len)
            mask: 掩码 (batch, seq_len)

        返回:
            best_tags: 标签索引序列列表
        """
        self.eval()
        with torch.no_grad():
            embeds = self.embedding(tokens)

            if mask is not None:
                seq_lengths = mask.sum(dim=1).long()
                packed = pack_padded_sequence(
                    embeds, seq_lengths.cpu(), batch_first=True, enforce_sorted=False
                )
                lstm_out, _ = self.lstm(packed)
                lstm_out, _ = pad_packed_sequence(lstm_out, batch_first=True)
            else:
                lstm_out, _ = self.lstm(embeds)

            emissions = self.hidden2tag(lstm_out)
            best_tags = emissions.argmax(dim=-1)

        if mask is not None:
            seq_lengths = mask.sum(dim=1).long()
            result = []
            for i in range(len(tokens)):
                seq_len = seq_lengths[i].item()
                result.append(best_tags[i][:seq_len].tolist())
            return result
        else:
            return best_tags.tolist()
