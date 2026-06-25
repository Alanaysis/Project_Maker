"""Shifted Window Transformer Block.

This module implements the shifted window mechanism from Swin Transformer.
The key innovation is alternating between:
1. Regular window attention (W-MSA): Attention within non-overlapping windows
2. Shifted window attention (SW-MSA): Windows shifted by half the window size

The shifted window enables cross-window information flow while maintaining
linear computational complexity.
"""

import torch
import torch.nn as nn

from .window_attention import WindowAttention, window_partition, window_reverse


class MLP(nn.Module):
    """Multi-layer Perceptron (MLP) block.

    Args:
        in_features: Number of input features.
        hidden_features: Number of hidden features.
        out_features: Number of output features.
        drop: Dropout rate.
    """

    def __init__(
        self,
        in_features: int,
        hidden_features: int = None,
        out_features: int = None,
        drop: float = 0.0,
    ):
        super().__init__()
        hidden_features = hidden_features or in_features
        out_features = out_features or in_features

        self.fc1 = nn.Linear(in_features, hidden_features)
        self.act = nn.GELU()
        self.drop1 = nn.Dropout(drop)
        self.fc2 = nn.Linear(hidden_features, out_features)
        self.drop2 = nn.Dropout(drop)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.fc1(x)
        x = self.act(x)
        x = self.drop1(x)
        x = self.fc2(x)
        x = self.drop2(x)
        return x


class ShiftedWindowTransformerBlock(nn.Module):
    """Swin Transformer Block with either regular or shifted window attention.

    This block applies:
    1. Window-based self-attention (regular or shifted)
    2. MLP with residual connections

    Args:
        dim: Number of input channels.
        input_resolution: Tuple of (height, width) of input feature map.
        num_heads: Number of attention heads.
        window_size: Size of the attention window.
        shift_size: Size of the window shift (0 for regular, window_size//2 for shifted).
        mlp_ratio: Ratio of MLP hidden dim to embedding dim.
        qkv_bias: If True, add learnable bias to query, key, value.
        drop: Dropout rate.
        attn_drop: Dropout rate for attention weights.
    """

    def __init__(
        self,
        dim: int,
        input_resolution: tuple,
        num_heads: int,
        window_size: int = 7,
        shift_size: int = 0,
        mlp_ratio: float = 4.0,
        qkv_bias: bool = True,
        drop: float = 0.0,
        attn_drop: float = 0.0,
    ):
        super().__init__()
        self.dim = dim
        self.input_resolution = input_resolution
        self.num_heads = num_heads
        self.window_size = window_size
        self.shift_size = shift_size
        self.mlp_ratio = mlp_ratio

        # Ensure window_size divides the input resolution
        H, W = input_resolution
        assert 0 <= self.shift_size < self.window_size, (
            f"Shift size ({shift_size}) must be in [0, window_size ({window_size}))"
        )

        # Layer normalization
        self.norm1 = nn.LayerNorm(dim)

        # Window attention
        self.attn = WindowAttention(
            dim=dim,
            window_size=(window_size, window_size),
            num_heads=num_heads,
            qkv_bias=qkv_bias,
            attn_drop=attn_drop,
            proj_drop=drop,
        )

        # Second layer normalization
        self.norm2 = nn.LayerNorm(dim)

        # MLP
        mlp_hidden_dim = int(dim * mlp_ratio)
        self.mlp = MLP(
            in_features=dim,
            hidden_features=mlp_hidden_dim,
            drop=drop,
        )

        # Compute attention mask for shifted window
        if self.shift_size > 0:
            self._compute_attention_mask()

    def _compute_attention_mask(self):
        """Compute attention mask for shifted window partitioning.

        The mask ensures that tokens from different cyclic-shifted regions
        don't attend to each other.
        """
        H, W = self.input_resolution
        window_size = self.window_size
        shift_size = self.shift_size

        # Create a region map
        img_mask = torch.zeros((1, H, W, 1))
        h_slices = (
            slice(0, -window_size),
            slice(-window_size, -shift_size),
            slice(-shift_size, None),
        )
        w_slices = (
            slice(0, -window_size),
            slice(-window_size, -shift_size),
            slice(-shift_size, None),
        )

        # Assign region IDs
        cnt = 0
        for h in h_slices:
            for w in w_slices:
                img_mask[:, h, w, :] = cnt
                cnt += 1

        # Partition into windows
        mask_windows = window_partition(img_mask, window_size)  # (num_windows, w, w, 1)
        mask_windows = mask_windows.view(-1, window_size * window_size)

        # Compute attention mask
        # Two tokens can attend if they are in the same region
        attn_mask = mask_windows.unsqueeze(1) - mask_windows.unsqueeze(2)  # (num_windows, N, N)
        attn_mask = attn_mask.masked_fill(attn_mask != 0, float(-100.0))
        attn_mask = attn_mask.masked_fill(attn_mask == 0, float(0.0))

        self.register_buffer("attn_mask", attn_mask)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input tensor of shape (B, H*W, C).

        Returns:
            Output tensor of shape (B, H*W, C).
        """
        H, W = self.input_resolution
        B, L, C = x.shape

        assert L == H * W, f"Input feature size ({L}) doesn't match resolution ({H}x{W})."

        # Shortcut for residual connection
        shortcut = x

        # First normalization
        x = self.norm1(x)

        # Reshape to 2D spatial format
        x = x.view(B, H, W, C)

        # Cyclic shift for shifted window attention
        if self.shift_size > 0:
            shifted_x = torch.roll(x, shifts=(-self.shift_size, -self.shift_size), dims=(1, 2))
        else:
            shifted_x = x

        # Partition into windows
        x_windows = window_partition(shifted_x, self.window_size)  # (num_windows*B, w, w, C)
        x_windows = x_windows.view(-1, self.window_size * self.window_size, C)  # (num_windows*B, N, C)

        # Apply window attention
        attn_windows = self.attn(x_windows, mask=self.attn_mask if self.shift_size > 0 else None)

        # Reshape back to spatial format
        attn_windows = attn_windows.view(-1, self.window_size, self.window_size, C)

        # Reverse window partition
        shifted_x = window_reverse(attn_windows, self.window_size, H, W)  # (B, H, W, C)

        # Reverse cyclic shift
        if self.shift_size > 0:
            x = torch.roll(shifted_x, shifts=(self.shift_size, self.shift_size), dims=(1, 2))
        else:
            x = shifted_x

        # Reshape back to sequence format
        x = x.view(B, H * W, C)

        # First residual connection
        x = shortcut + x

        # MLP with residual connection
        x = x + self.mlp(self.norm2(x))

        return x
