"""
Temporal modeling module for action recognition.

Captures temporal dynamics across video frames using LSTM, GRU, or
Transformer-based architectures. Operates on sequences of spatial features.
"""

from typing import Optional, Tuple

import torch
import torch.nn as nn


class TemporalModel(nn.Module):
    """Model temporal relationships across video frames.

    Supports three architectures:
        - LSTM: Long Short-Term Memory network
        - GRU: Gated Recurrent Unit
        - Transformer: Self-attention based temporal modeling

    Args:
        input_dim: Dimension of input features per frame.
        hidden_dim: Hidden state dimension.
        num_layers: Number of recurrent/transformer layers.
        arch: Architecture type ('lstm', 'gru', 'transformer').
        num_heads: Number of attention heads (transformer only).
        dropout: Dropout probability.
        bidirectional: Whether to use bidirectional recurrence.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 256,
        num_layers: int = 2,
        arch: str = "lstm",
        num_heads: int = 4,
        dropout: float = 0.3,
        bidirectional: bool = False,
    ):
        super().__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.arch = arch
        self.bidirectional = bidirectional
        self.num_layers = num_layers

        output_dim = hidden_dim * 2 if bidirectional else hidden_dim

        if arch == "lstm":
            self.temporal_net = nn.LSTM(
                input_size=input_dim,
                hidden_size=hidden_dim,
                num_layers=num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0.0,
                bidirectional=bidirectional,
            )
        elif arch == "gru":
            self.temporal_net = nn.GRU(
                input_size=input_dim,
                hidden_size=hidden_dim,
                num_layers=num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0.0,
                bidirectional=bidirectional,
            )
        elif arch == "transformer":
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=input_dim,
                nhead=num_heads,
                dim_feedforward=hidden_dim * 4,
                dropout=dropout,
                batch_first=True,
            )
            self.temporal_net = nn.TransformerEncoder(
                encoder_layer, num_layers=num_layers
            )
            output_dim = input_dim
        else:
            raise ValueError(
                f"Unsupported architecture '{arch}'. "
                f"Choose from: lstm, gru, transformer"
            )

        self.output_dim = output_dim
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        lengths: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Process temporal sequence of features.

        Args:
            x: Input features of shape (B, T, input_dim).
            lengths: Actual sequence lengths for packing (optional).

        Returns:
            Temporal features of shape (B, output_dim).
            For LSTM/GRU: last hidden state.
            For Transformer: mean-pooled output.
        """
        if self.arch in ("lstm", "gru"):
            if lengths is not None:
                packed = nn.utils.rnn.pack_padded_sequence(
                    x, lengths.cpu(), batch_first=True, enforce_sorted=False
                )
                output, hidden = self.temporal_net(packed)
                output, _ = nn.utils.rnn.pad_packed_sequence(
                    output, batch_first=True
                )
            else:
                output, hidden = self.temporal_net(x)

            if self.arch == "lstm":
                hidden = hidden[0]  # (num_layers * num_directions, B, H)

            # Take the last layer's hidden state
            if self.bidirectional:
                # Concatenate forward and backward last layer states
                fwd = hidden[-2]
                bwd = hidden[-1]
                temporal_feature = torch.cat([fwd, bwd], dim=1)
            else:
                temporal_feature = hidden[-1]

        else:  # transformer
            output = self.temporal_net(x)
            # Mean pooling over time dimension
            if lengths is not None:
                mask = torch.arange(x.size(1), device=x.device).unsqueeze(0) < lengths.unsqueeze(1)
                mask = mask.unsqueeze(-1).float()
                temporal_feature = (output * mask).sum(1) / lengths.unsqueeze(1).float()
            else:
                temporal_feature = output.mean(dim=1)

        return self.dropout(temporal_feature)
