"""Window-based Multi-head Self-Attention (W-MSA).

This module implements the window attention mechanism used in Swin Transformer.
Instead of computing attention over the entire sequence (global attention),
it computes attention within local windows of fixed size.

This reduces computational complexity from O(n²) to O(n), where n is the
number of patches, making it efficient for high-resolution images.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


def window_partition(x: torch.Tensor, window_size: int) -> torch.Tensor:
    """Partition input tensor into non-overlapping windows.

    Args:
        x: Input tensor of shape (B, H, W, C).
        window_size: Size of each window.

    Returns:
        Windows of shape (B * num_windows, window_size, window_size, C).
    """
    B, H, W, C = x.shape

    # Reshape to (B, H//w, w, W//w, w, C)
    x = x.view(B, H // window_size, window_size, W // window_size, window_size, C)

    # Permute to (B, H//w, W//w, w, w, C)
    x = x.permute(0, 1, 3, 2, 4, 5).contiguous()

    # Flatten to (B * num_windows, w, w, C)
    num_windows = (H // window_size) * (W // window_size)
    x = x.view(-1, window_size, window_size, C)

    return x


def window_reverse(windows: torch.Tensor, window_size: int, H: int, W: int) -> torch.Tensor:
    """Reverse window partition to original tensor format.

    Args:
        windows: Window tensor of shape (B * num_windows, window_size, window_size, C).
        window_size: Size of each window.
        H: Height of original feature map.
        W: Width of original feature map.

    Returns:
        Reconstructed tensor of shape (B, H, W, C).
    """
    B = int(windows.shape[0] / (H * W / window_size / window_size))
    num_windows_h = H // window_size
    num_windows_w = W // window_size

    # Reshape to (B, num_windows_h, num_windows_w, window_size, window_size, C)
    x = windows.view(B, num_windows_h, num_windows_w, window_size, window_size, -1)

    # Permute to (B, num_windows_h, window_size, num_windows_w, window_size, C)
    x = x.permute(0, 1, 3, 2, 4, 5).contiguous()

    # Reshape to (B, H, W, C)
    x = x.view(B, H, W, -1)

    return x


class WindowAttention(nn.Module):
    """Window-based Multi-head Self-Attention.

    Computes self-attention within local windows of fixed size, with optional
    relative position bias. This is more efficient than global attention for
    high-resolution feature maps.

    Args:
        dim: Number of input channels.
        window_size: Tuple of (height, width) of the window.
        num_heads: Number of attention heads.
        qkv_bias: If True, add learnable bias to query, key, value.
        attn_drop: Dropout rate for attention weights.
        proj_drop: Dropout rate for output projection.
    """

    def __init__(
        self,
        dim: int,
        window_size: tuple,
        num_heads: int,
        qkv_bias: bool = True,
        attn_drop: float = 0.0,
        proj_drop: float = 0.0,
    ):
        super().__init__()
        self.dim = dim
        self.window_size = window_size  # (Wh, Ww)
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.scale = self.head_dim ** -0.5

        # Relative position bias table
        # Size: (2*Wh-1) * (2*Ww-1), num_heads
        self.relative_position_bias_table = nn.Parameter(
            torch.zeros((2 * window_size[0] - 1) * (2 * window_size[1] - 1), num_heads)
        )

        # Initialize relative position bias
        nn.init.trunc_normal_(self.relative_position_bias_table, std=0.02)

        # Compute relative position indices
        # This is a fixed index mapping for each window
        self._compute_relative_position_index()

        # QKV projection
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)

    def _compute_relative_position_index(self):
        """Compute relative position index for each pair of positions in the window."""
        Wh, Ww = self.window_size

        # Create coordinate grids
        coords_h = torch.arange(Wh)
        coords_w = torch.arange(Ww)
        coords = torch.stack(torch.meshgrid([coords_h, coords_w], indexing="ij"))  # (2, Wh, Ww)
        coords_flatten = torch.flatten(coords, 1)  # (2, Wh*Ww)

        # Compute relative coordinates
        relative_coords = coords_flatten[:, :, None] - coords_flatten[:, None, :]  # (2, N, N)
        relative_coords = relative_coords.permute(1, 2, 0).contiguous()  # (N, N, 2)

        # Shift to start from 0
        relative_coords[:, :, 0] += Wh - 1
        relative_coords[:, :, 1] += Ww - 1

        # Flatten to 1D index
        relative_coords[:, :, 0] *= 2 * Ww - 1
        relative_position_index = relative_coords.sum(-1)  # (N, N)

        self.register_buffer("relative_position_index", relative_position_index)

    def forward(self, x: torch.Tensor, mask: torch.Tensor = None) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input tensor of shape (B * num_windows, window_size * window_size, C).
            mask: Optional attention mask of shape (num_windows, window_size * window_size, window_size * window_size).

        Returns:
            Output tensor of shape (B * num_windows, window_size * window_size, C).
        """
        B_, N, C = x.shape  # N = window_size * window_size

        # QKV projection: (B_, N, C) -> (B_, N, 3 * C) -> 3 * (B_, num_heads, N, head_dim)
        qkv = self.qkv(x).reshape(B_, N, 3, self.num_heads, self.head_dim).permute(2, 0, 3, 1, 4)
        q, k, v = qkv.unbind(0)

        # Compute attention scores with scaling
        q = q * self.scale
        attn = q @ k.transpose(-2, -1)  # (B_, num_heads, N, N)

        # Add relative position bias
        relative_position_bias = self.relative_position_bias_table[
            self.relative_position_index.view(-1)
        ].view(N, N, -1)
        relative_position_bias = relative_position_bias.permute(2, 0, 1).contiguous()  # (num_heads, N, N)
        attn = attn + relative_position_bias.unsqueeze(0)

        # Apply attention mask if provided (for shifted window attention)
        if mask is not None:
            num_windows = mask.shape[0]
            attn = attn.view(B_ // num_windows, num_windows, self.num_heads, N, N)
            attn = attn + mask.unsqueeze(1).unsqueeze(0)  # (B, num_windows, num_heads, N, N)
            attn = attn.view(-1, self.num_heads, N, N)

        # Softmax and dropout
        attn = F.softmax(attn, dim=-1)
        attn = self.attn_drop(attn)

        # Apply attention to values
        x = (attn @ v).transpose(1, 2).reshape(B_, N, C)

        # Output projection
        x = self.proj(x)
        x = self.proj_drop(x)

        return x
