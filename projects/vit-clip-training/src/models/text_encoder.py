"""
Text Encoder for CLIP

Implements a Transformer-based text encoder that converts text to embeddings
in the same space as image embeddings for contrastive learning.

⭐ Key Design:
- Uses causal masking (autoregressive) like GPT
- [EOS] token (last token) is used as text representation
- Projects to the same embedding dimension as image encoder

💡 Why causal masking?
- CLIP uses a causal text encoder (like GPT)
- Each token can only attend to previous tokens
- The final token [EOS] captures the full sequence meaning
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class TextTransformer(nn.Module):
    """
    Text Transformer Encoder for CLIP.

    Architecture:
    1. Token embedding + Position embedding
    2. Transformer blocks with causal masking
    3. Take [EOS] token representation
    4. Project to shared embedding space

    ⭐ Key difference from BERT:
    - CLIP uses causal (left-to-right) masking
    - BERT uses bidirectional attention
    - Causal masking allows autoregressive generation

    Example:
        >>> encoder = TextTransformer(vocab_size=49408, embed_dim=512)
        >>> tokens = torch.randint(0, 49408, (2, 77))  # (batch, seq_len)
        >>> features = encoder(tokens)  # (2, 512)
    """

    def __init__(
        self,
        vocab_size: int = 49408,  # CLIP vocabulary size
        max_seq_len: int = 77,    # CLIP max sequence length
        embed_dim: int = 512,
        depth: int = 12,
        num_heads: int = 8,
        mlp_ratio: float = 4.0,
        dropout: float = 0.0,
    ):
        super().__init__()
        self.max_seq_len = max_seq_len
        self.embed_dim = embed_dim

        # Token embedding
        self.token_embedding = nn.Embedding(vocab_size, embed_dim)

        # Position embedding (learnable)
        self.position_embedding = nn.Parameter(
            torch.randn(1, max_seq_len, embed_dim) * 0.02
        )

        # Transformer blocks
        self.blocks = nn.ModuleList([
            TextTransformerBlock(
                embed_dim=embed_dim,
                num_heads=num_heads,
                mlp_ratio=mlp_ratio,
                dropout=dropout,
            )
            for _ in range(depth)
        ])

        # Final layer norm
        self.norm = nn.LayerNorm(embed_dim)

        # Attention mask (causal)
        self.register_buffer(
            "causal_mask",
            self._create_causal_mask(max_seq_len),
        )

        self._init_weights()

    def _create_causal_mask(self, seq_len: int) -> torch.Tensor:
        """
        Create causal attention mask.

        ⭐ Causal mask ensures each token can only attend to previous tokens:
        [[1, 0, 0],
         [1, 1, 0],
         [1, 1, 1]]
        """
        mask = torch.tril(torch.ones(seq_len, seq_len))
        return mask.unsqueeze(0).unsqueeze(0)  # (1, 1, seq_len, seq_len)

    def _init_weights(self):
        """Initialize weights."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.trunc_normal_(m.weight, std=0.02)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Embedding):
                nn.init.trunc_normal_(m.weight, std=0.02)
            elif isinstance(m, nn.LayerNorm):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(
        self,
        tokens: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            tokens: Token IDs, shape (B, seq_len)
            attention_mask: Optional mask for padding tokens

        Returns:
            Text features, shape (B, embed_dim)
        """
        B, seq_len = tokens.shape

        # Token + position embedding
        x = self.token_embedding(tokens)  # (B, seq_len, embed_dim)
        x = x + self.position_embedding[:, :seq_len, :]

        # Create combined mask
        mask = self.causal_mask[:, :, :seq_len, :seq_len]
        if attention_mask is not None:
            # Expand attention mask for broadcasting
            # attention_mask: (B, seq_len) -> (B, 1, 1, seq_len)
            attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)
            mask = mask * attention_mask

        # Transformer blocks
        for block in self.blocks:
            x = block(x, mask)

        # Final normalization
        x = self.norm(x)

        # Take the features from the [EOS] token (last non-padding token)
        # For CLIP, this is typically the last token
        x = x[:, -1, :]

        return x


class TextTransformerBlock(nn.Module):
    """
    Single Transformer block for text encoder.

    Structure:
    1. Layer Norm -> Multi-Head Attention (with causal mask) -> Residual
    2. Layer Norm -> MLP -> Residual
    """

    def __init__(
        self,
        embed_dim: int = 512,
        num_heads: int = 8,
        mlp_ratio: float = 4.0,
        dropout: float = 0.0,
    ):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn = MultiHeadAttention(embed_dim, num_heads, dropout)
        self.norm2 = nn.LayerNorm(embed_dim)

        mlp_hidden = int(embed_dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim, mlp_hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_hidden, embed_dim),
            nn.Dropout(dropout),
        )

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        # Self-attention with causal mask
        x = x + self.attn(self.norm1(x), mask)

        # MLP
        x = x + self.mlp(self.norm2(x))

        return x


class MultiHeadAttention(nn.Module):
    """Multi-Head Attention with optional mask support."""

    def __init__(
        self,
        embed_dim: int = 512,
        num_heads: int = 8,
        dropout: float = 0.0,
    ):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5

        self.qkv = nn.Linear(embed_dim, 3 * embed_dim)
        self.proj = nn.Linear(embed_dim, embed_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        B, N, D = x.shape

        # Compute Q, K, V
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)
        q, k, v = qkv.unbind(0)

        # Attention scores
        attn = (q @ k.transpose(-2, -1)) * self.scale

        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))

        attn = F.softmax(attn, dim=-1)
        attn = self.dropout(attn)

        # Apply attention
        x = (attn @ v).transpose(1, 2).reshape(B, N, D)
        x = self.proj(x)

        return x


# Pre-defined configurations
TEXT_CONFIGS = {
    "text_small": {
        "embed_dim": 512,
        "depth": 12,
        "num_heads": 8,
    },
    "text_base": {
        "embed_dim": 512,
        "depth": 12,
        "num_heads": 8,
    },
    "text_large": {
        "embed_dim": 768,
        "depth": 12,
        "num_heads": 12,
    },
}


def create_text_encoder(
    config_name: str = "text_base",
    **kwargs,
) -> TextTransformer:
    """Create a text encoder by configuration name."""
    if config_name not in TEXT_CONFIGS:
        raise ValueError(f"Unknown config: {config_name}")

    config = TEXT_CONFIGS[config_name].copy()
    config.update(kwargs)

    return TextTransformer(**config)
