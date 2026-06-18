"""
Value Head 模块

⭐ 为什么需要 Value Head?
    在 PPO 中，我们需要估计每个状态的价值 V(s)。
    Value Head 是附加在语言模型上的一个线性层，
    将模型的隐藏状态映射到一个标量值（状态价值）。

💡 设计思路:
    - 共享语言模型的主干网络（transformer layers）
    - 在顶部添加一个独立的线性层作为 Value Head
    - Value Head 输出标量值，表示当前状态的价值估计

参考: TRL (Transformer Reinforcement Learning) 的实现
"""

import torch
import torch.nn as nn
from transformers import PreTrainedModel


class ValueHead(nn.Module):
    """
    Value Head: 将隐藏状态映射到状态价值

    输入: 隐藏状态 (batch, seq_len, hidden_dim)
    输出: 状态价值 (batch, seq_len, 1) 或 (batch, 1)

    ⭐ 实现要点:
    1. 使用线性层将 hidden_dim 映射到 1
    2. 可选使用 LayerNorm 稳定训练
    3. 可选使用 Dropout 防止过拟合
    """

    def __init__(
        self,
        hidden_size: int,
        output_size: int = 1,
        dropout: float = 0.0,
        use_layer_norm: bool = False,
    ):
        super().__init__()

        # LayerNorm（可选）
        self.layer_norm = nn.LayerNorm(hidden_size) if use_layer_norm else nn.Identity()

        # Dropout
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()

        # 线性层: hidden_dim -> 1
        self.value_head = nn.Linear(hidden_size, output_size, bias=False)

        # 初始化
        nn.init.zeros_(self.value_head.weight)

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            hidden_states: 隐藏状态, shape (batch, seq_len, hidden_dim)

        Returns:
            状态价值, shape (batch, seq_len)
        """
        # LayerNorm
        hidden_states = self.layer_norm(hidden_states)

        # Dropout
        hidden_states = self.dropout(hidden_states)

        # 线性映射到标量
        values = self.value_head(hidden_states).squeeze(-1)

        return values


def add_value_head(
    model: PreTrainedModel,
    use_layer_norm: bool = False,
    dropout: float = 0.0,
) -> PreTrainedModel:
    """
    为语言模型添加 Value Head

    ⭐ 这是 PPO 训练的关键步骤:
    1. 获取模型的隐藏层维度
    2. 创建 Value Head 模块
    3. 将 Value Head 附加到模型上

    Args:
        model: 预训练语言模型
        use_layer_norm: 是否使用 LayerNorm
        dropout: Dropout 概率

    Returns:
        添加了 Value Head 的模型
    """
    # 获取隐藏层维度
    if hasattr(model.config, "hidden_size"):
        hidden_size = model.config.hidden_size
    elif hasattr(model.config, "n_embd"):
        hidden_size = model.config.n_embd  # GPT-2 使用 n_embd
    else:
        raise ValueError("无法确定模型的隐藏层维度")

    # 创建 Value Head
    value_head = ValueHead(
        hidden_size=hidden_size,
        use_layer_norm=use_layer_norm,
        dropout=dropout,
    )

    # 将 Value Head 附加到模型
    model.value_head = value_head

    return model


def get_value_head_output(
    model: PreTrainedModel,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor = None,
) -> torch.Tensor:
    """
    获取 Value Head 的输出（状态价值估计）

    Args:
        model: 添加了 Value Head 的模型
        input_ids: 输入 token ids
        attention_mask: 注意力掩码

    Returns:
        状态价值, shape (batch, seq_len)
    """
    # 获取模型输出（包含隐藏状态）
    outputs = model(
        input_ids=input_ids,
        attention_mask=attention_mask,
        output_hidden_states=True,
    )

    # 获取最后一层的隐藏状态
    hidden_states = outputs.hidden_states[-1]

    # 通过 Value Head 计算价值
    values = model.value_head(hidden_states)

    return values
