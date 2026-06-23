"""
Building blocks for the U-Net architecture.

Implements the fundamental building blocks:
- DoubleConv: Two consecutive 3x3 conv layers with BatchNorm and ReLU
- Down: MaxPool followed by DoubleConv (encoder block)
- Up: Upsample followed by concatenation and DoubleConv (decoder block)
"""

from typing import Optional

import torch
import torch.nn as nn


class DoubleConv(nn.Module):
    """Double convolution block: (Conv2d -> BN -> ReLU) x 2.

    This is the fundamental building block of U-Net. Each block applies
    two 3x3 convolutions, each followed by batch normalization and ReLU activation.
    The padding=1 keeps spatial dimensions unchanged.

    Args:
        in_channels: Number of input channels.
        out_channels: Number of output channels.
        mid_channels: Optional intermediate channels (defaults to out_channels).
        use_batch_norm: Whether to use batch normalization (default: True).
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        mid_channels: Optional[int] = None,
        use_batch_norm: bool = True,
    ):
        super().__init__()
        if mid_channels is None:
            mid_channels = out_channels

        layers = [
            nn.Conv2d(in_channels, mid_channels, kernel_size=3, padding=1, bias=not use_batch_norm),
        ]
        if use_batch_norm:
            layers.append(nn.BatchNorm2d(mid_channels))
        layers.append(nn.ReLU(inplace=True))

        layers.append(nn.Conv2d(mid_channels, out_channels, kernel_size=3, padding=1, bias=not use_batch_norm))
        if use_batch_norm:
            layers.append(nn.BatchNorm2d(out_channels))
        layers.append(nn.ReLU(inplace=True))

        self.double_conv = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through double convolution.

        Args:
            x: Input tensor of shape (B, C_in, H, W).

        Returns:
            Output tensor of shape (B, C_out, H, W).
        """
        return self.double_conv(x)


class Down(nn.Module):
    """Downscaling block: MaxPool2d -> DoubleConv.

    Used in the encoder path to reduce spatial dimensions by 2x
    while increasing the number of feature channels.

    Args:
        in_channels: Number of input channels.
        out_channels: Number of output channels.
        use_batch_norm: Whether to use batch normalization (default: True).
    """

    def __init__(self, in_channels: int, out_channels: int, use_batch_norm: bool = True):
        super().__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_channels, out_channels, use_batch_norm=use_batch_norm),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass: downsample then convolve.

        Args:
            x: Input tensor of shape (B, C_in, H, W).

        Returns:
            Output tensor of shape (B, C_out, H//2, W//2).
        """
        return self.maxpool_conv(x)


class Up(nn.Module):
    """Upscaling block: Upsample/ConvTranspose2d -> Concat skip -> DoubleConv.

    Used in the decoder path to increase spatial dimensions by 2x.
    Concatenates the upsampled features with the corresponding encoder
    features (skip connection) before applying double convolution.

    Args:
        in_channels: Number of input channels from the lower level (before concatenation).
        out_channels: Number of output channels.
        skip_channels: Number of channels from the skip connection.
        use_bilinear: Use bilinear interpolation if True, ConvTranspose2d if False.
        use_batch_norm: Whether to use batch normalization (default: True).
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        skip_channels: int = 0,
        use_bilinear: bool = True,
        use_batch_norm: bool = True,
    ):
        super().__init__()
        self.use_bilinear = use_bilinear

        if use_bilinear:
            self.up = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True)
            up_channels = in_channels
        else:
            self.up = nn.ConvTranspose2d(
                in_channels, in_channels // 2, kernel_size=2, stride=2
            )
            up_channels = in_channels // 2

        # After concatenation: up_channels + skip_channels
        concat_channels = up_channels + skip_channels
        self.conv = DoubleConv(
            concat_channels,
            out_channels,
            mid_channels=out_channels,
            use_batch_norm=use_batch_norm,
        )

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        """Forward pass: upsample, concatenate with skip, then convolve.

        Args:
            x: Input tensor from the lower level, shape (B, C_in, H, W).
            skip: Skip connection tensor from the encoder, shape (B, C_skip, 2H, 2W).

        Returns:
            Output tensor of shape (B, C_out, 2H, 2W).
        """
        x = self.up(x)

        # Handle size mismatch due to odd dimensions
        diff_h = skip.size(2) - x.size(2)
        diff_w = skip.size(3) - x.size(3)
        if diff_h != 0 or diff_w != 0:
            x = nn.functional.pad(x, [diff_w // 2, diff_w - diff_w // 2,
                                       diff_h // 2, diff_h - diff_h // 2])

        # Concatenate along the channel dimension
        x = torch.cat([skip, x], dim=1)
        return self.conv(x)
