"""
Decoder module for U-Net.

The decoder (expanding path) progressively upsamples the bottleneck features
back to the original resolution, using skip connections from the encoder
to preserve spatial information.

Architecture:
    [Up + Skip Concat -> DoubleConv] x n_levels
"""

from typing import List

import torch
import torch.nn as nn

from .blocks import Up


class Decoder(nn.Module):
    """U-Net decoder (expanding path).

    Progressively upsamples features while incorporating skip connections
    from the encoder. Each level doubles the spatial resolution and halves
    the number of channels.

    Args:
        out_channels: Number of output channels (e.g., number of segmentation classes).
        skip_channels: List of channel counts from each encoder skip connection.
        base_channels: Number of channels at the first encoder level (default: 64).
        n_levels: Number of decoding levels (default: 4).
        use_bilinear: Use bilinear upsampling if True, ConvTranspose2d if False (default: True).
        use_batch_norm: Whether to use batch normalization (default: True).

    Example:
        >>> decoder = Decoder(
        ...     out_channels=1,
        ...     skip_channels=[64, 128, 256, 512],
        ...     base_channels=64,
        ...     n_levels=4,
        ... )
        >>> bottleneck = torch.randn(1, 1024, 16, 16)
        >>> skips = [
        ...     torch.randn(1, 64, 256, 256),
        ...     torch.randn(1, 128, 128, 128),
        ...     torch.randn(1, 256, 64, 64),
        ...     torch.randn(1, 512, 32, 32),
        ... ]
        >>> output = decoder(bottleneck, skips)
        >>> # output: (1, 1, 256, 256)
    """

    def __init__(
        self,
        out_channels: int = 1,
        skip_channels: List[int] = None,
        base_channels: int = 64,
        n_levels: int = 4,
        use_bilinear: bool = True,
        use_batch_norm: bool = True,
    ):
        super().__init__()
        self.n_levels = n_levels

        if skip_channels is None:
            skip_channels = [base_channels * (2 ** i) for i in range(n_levels)]

        # Build upsampling blocks
        # bottleneck_channels = base_channels * 2^n_levels
        bottleneck_channels = base_channels * (2 ** n_levels)
        self.up_blocks = nn.ModuleList()

        channels = bottleneck_channels
        for i in range(n_levels):
            self.up_blocks.append(
                Up(
                    in_channels=channels,
                    out_channels=skip_channels[i],
                    skip_channels=skip_channels[self.n_levels - 1 - i],
                    use_bilinear=use_bilinear,
                    use_batch_norm=use_batch_norm,
                )
            )
            channels = skip_channels[i]

        # Final 1x1 convolution to map to output channels
        self.outc = nn.Conv2d(channels, out_channels, kernel_size=1)

    def forward(self, bottleneck: torch.Tensor, skips: List[torch.Tensor]) -> torch.Tensor:
        """Forward pass through the decoder.

        Args:
            bottleneck: Deepest feature map from encoder, shape (B, C_bottleneck, H, W).
            skips: List of skip connection feature maps from encoder, ordered from
                   shallowest to deepest (i.e., highest spatial resolution first).

        Returns:
            Segmentation map of shape (B, out_channels, H_orig, W_orig).
        """
        x = bottleneck

        # Process from deepest to shallowest (reverse order of skips)
        for i, up in enumerate(self.up_blocks):
            skip_idx = self.n_levels - 1 - i
            x = up(x, skips[skip_idx])

        return self.outc(x)
