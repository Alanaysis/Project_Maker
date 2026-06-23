"""
Encoder module for U-Net.

The encoder (contracting path) progressively downsamples the input image
while extracting increasingly abstract features at each level.

Architecture:
    Input -> DoubleConv -> [Down -> DoubleConv] x (n_levels - 1)

At each level, spatial resolution is halved and channels are doubled.
Skip connections are saved at each level for the decoder to use.
"""

from typing import List, Tuple

import torch
import torch.nn as nn

from .blocks import DoubleConv, Down


class Encoder(nn.Module):
    """U-Net encoder (contracting path).

    Progressively downsamples the input while extracting features.
    Returns intermediate feature maps for skip connections.

    Args:
        in_channels: Number of input channels (e.g., 3 for RGB).
        base_channels: Number of channels at the first level (default: 64).
        n_levels: Number of encoding levels (default: 4).
        use_batch_norm: Whether to use batch normalization (default: True).

    Example:
        >>> encoder = Encoder(in_channels=3, base_channels=64, n_levels=4)
        >>> x = torch.randn(1, 3, 256, 256)
        >>> skips, bottleneck = encoder(x)
        >>> # skips[0]: (1, 64, 256, 256) - first level features
        >>> # skips[1]: (1, 128, 128, 128) - second level features
        >>> # skips[2]: (1, 256, 64, 64) - third level features
        >>> # skips[3]: (1, 512, 32, 32) - fourth level features
        >>> # bottleneck: (1, 1024, 16, 16) - deepest features
    """

    def __init__(
        self,
        in_channels: int = 3,
        base_channels: int = 64,
        n_levels: int = 4,
        use_batch_norm: bool = True,
    ):
        super().__init__()
        self._in_channels = in_channels
        self._base_channels = base_channels
        self.n_levels = n_levels

        # First level: initial double convolution (no downsampling)
        self.inc = DoubleConv(in_channels, base_channels, use_batch_norm=use_batch_norm)

        # Subsequent levels: downsample then convolve
        self.down_blocks = nn.ModuleList()
        channels = base_channels
        for _ in range(n_levels):
            self.down_blocks.append(Down(channels, channels * 2, use_batch_norm=use_batch_norm))
            channels *= 2

    def forward(self, x: torch.Tensor) -> Tuple[List[torch.Tensor], torch.Tensor]:
        """Forward pass through the encoder.

        Args:
            x: Input tensor of shape (B, in_channels, H, W).

        Returns:
            A tuple of:
            - skips: List of feature maps at each level for skip connections.
            - bottleneck: The deepest feature map.
        """
        # First level (no downsampling)
        skips = [self.inc(x)]

        # Subsequent levels
        for down in self.down_blocks:
            skips.append(down(skips[-1]))

        # The last element is the bottleneck
        bottleneck = skips.pop()
        return skips, bottleneck

    @property
    def out_channels(self) -> int:
        """Number of output channels at the bottleneck."""
        return self._base_channels * (2 ** self.n_levels)

    @property
    def skip_channels(self) -> List[int]:
        """Number of channels at each skip connection level."""
        return [self._base_channels * (2 ** i) for i in range(self.n_levels)]

    def __repr__(self) -> str:
        return (
            f"Encoder(in_channels={self._in_channels}, "
            f"base_channels={self._base_channels}, "
            f"n_levels={self.n_levels})"
        )
