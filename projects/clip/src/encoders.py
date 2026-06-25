"""Image and Text encoders for CLIP model."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class ImageEncoder(nn.Module):
    """
    Image encoder using a simplified ResNet-like architecture.
    Encodes images into a fixed-size embedding vector.
    """

    def __init__(
        self,
        embed_dim: int = 512,
        hidden_dim: int = 256,
        num_layers: int = 4,
        in_channels: int = 3,
    ):
        super().__init__()
        self.embed_dim = embed_dim

        # Convolutional layers for feature extraction
        self.conv_layers = nn.Sequential(
            # Initial conv block
            nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1),

            # Residual blocks
            self._make_residual_block(64, 128, stride=2),
            self._make_residual_block(128, 256, stride=2),
            self._make_residual_block(256, 512, stride=2),

            # Global average pooling
            nn.AdaptiveAvgPool2d((1, 1)),
        )

        # Projection head
        self.projection = nn.Sequential(
            nn.Linear(512, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, embed_dim),
        )

    def _make_residual_block(
        self, in_channels: int, out_channels: int, stride: int = 1
    ) -> nn.Sequential:
        """Create a residual block."""
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, stride=stride, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input images [batch_size, channels, height, width]

        Returns:
            Image embeddings [batch_size, embed_dim]
        """
        features = self.conv_layers(x)
        features = features.flatten(start_dim=1)
        embeddings = self.projection(features)
        return F.normalize(embeddings, dim=-1)


class TextEncoder(nn.Module):
    """
    Text encoder using a simplified Transformer architecture.
    Encodes text tokens into a fixed-size embedding vector.
    """

    def __init__(
        self,
        vocab_size: int = 10000,
        embed_dim: int = 512,
        hidden_dim: int = 256,
        num_heads: int = 8,
        num_layers: int = 6,
        max_seq_length: int = 77,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.embed_dim = embed_dim
        self.max_seq_length = max_seq_length

        # Token and position embeddings
        self.token_embedding = nn.Embedding(vocab_size, embed_dim)
        self.position_embedding = nn.Embedding(max_seq_length, embed_dim)

        # Transformer encoder layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer, num_layers=num_layers
        )

        # Layer normalization
        self.ln_final = nn.LayerNorm(embed_dim)

        # Projection head
        self.projection = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, embed_dim),
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            input_ids: Token IDs [batch_size, seq_length]
            attention_mask: Attention mask [batch_size, seq_length]

        Returns:
            Text embeddings [batch_size, embed_dim]
        """
        batch_size, seq_length = input_ids.shape

        # Create position IDs
        position_ids = torch.arange(seq_length, device=input_ids.device)
        position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)

        # Embeddings
        token_embeds = self.token_embedding(input_ids)
        position_embeds = self.position_embedding(position_ids)
        hidden_states = token_embeds + position_embeds

        # Create padding mask for transformer (True = ignore/pad)
        padding_mask = None
        if attention_mask is not None:
            # Transformer expects src_key_padding_mask where True = masked/ignored
            padding_mask = (attention_mask == 0)

        # Transformer encoding
        hidden_states = self.transformer(
            hidden_states, src_key_padding_mask=padding_mask
        )
        hidden_states = self.ln_final(hidden_states)

        # Use EOS token embedding (last token) as sentence representation
        # Find the last non-padding token for each sequence
        if attention_mask is not None:
            eos_indices = attention_mask.sum(dim=1).long() - 1
            eos_indices = eos_indices.clamp(min=0)
            hidden_states = hidden_states[
                torch.arange(batch_size, device=hidden_states.device),
                eos_indices,
            ]
        else:
            hidden_states = hidden_states[:, -1, :]

        # Project to embedding space
        embeddings = self.projection(hidden_states)
        return F.normalize(embeddings, dim=-1)
