"""
U-Net architecture for semantic segmentation.

Implements the full U-Net model with:
- Encoder (contracting path) with skip connections
- Bottleneck layer
- Decoder (expanding path) with skip connections
- Final 1x1 convolution for pixel-wise classification

Reference: Ronneberger et al., "U-Net: Convolutional Networks for Biomedical
Image Segmentation", MICCAI 2015.
"""

import torch
import torch.nn as nn

from .encoder import Encoder
from .decoder import Decoder


class UNet(nn.Module):
    """U-Net: Convolutional Networks for Biomedical Image Segmentation.

    A fully convolutional network with an encoder-decoder architecture and
    skip connections. The encoder progressively downsamples the input while
    extracting features, and the decoder upsamples the features back to the
    original resolution for pixel-wise classification.

    Architecture:
        Input (B, C_in, H, W)
            |
        [Encoder]
            |-- skip_0 (B, 64, H, W)
            |-- skip_1 (B, 128, H/2, W/2)
            |-- skip_2 (B, 256, H/4, W/4)
            |-- skip_3 (B, 512, H/8, W/8)
            |
        Bottleneck (B, 1024, H/16, W/16)
            |
        [Decoder]
            |-- up_0 + skip_3 -> (B, 512, H/8, W/8)
            |-- up_1 + skip_2 -> (B, 256, H/4, W/4)
            |-- up_2 + skip_1 -> (B, 128, H/2, W/2)
            |-- up_3 + skip_0 -> (B, 64, H, W)
            |
        1x1 Conv -> Output (B, C_out, H, W)

    Args:
        in_channels: Number of input channels (default: 3 for RGB).
        out_channels: Number of output channels / classes (default: 1 for binary).
        base_channels: Number of channels at the first encoder level (default: 64).
        n_levels: Number of encoder/decoder levels (default: 4).
        use_bilinear: Use bilinear upsampling if True, ConvTranspose2d if False.
        use_batch_norm: Whether to use batch normalization (default: True).

    Example:
        >>> model = UNet(in_channels=3, out_channels=1, base_channels=64, n_levels=4)
        >>> x = torch.randn(1, 3, 256, 256)
        >>> output = model(x)
        >>> # output: (1, 1, 256, 256) - same spatial size as input
    """

    def __init__(
        self,
        in_channels: int = 3,
        out_channels: int = 1,
        base_channels: int = 64,
        n_levels: int = 4,
        use_bilinear: bool = True,
        use_batch_norm: bool = True,
    ):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.base_channels = base_channels
        self.n_levels = n_levels

        self.encoder = Encoder(
            in_channels=in_channels,
            base_channels=base_channels,
            n_levels=n_levels,
            use_batch_norm=use_batch_norm,
        )

        self.decoder = Decoder(
            out_channels=out_channels,
            skip_channels=[base_channels * (2 ** i) for i in range(n_levels)],
            base_channels=base_channels,
            n_levels=n_levels,
            use_bilinear=use_bilinear,
            use_batch_norm=use_batch_norm,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the full U-Net.

        Args:
            x: Input tensor of shape (B, in_channels, H, W).

        Returns:
            Segmentation map of shape (B, out_channels, H, W).
        """
        skips, bottleneck = self.encoder(x)
        output = self.decoder(bottleneck, skips)
        return output

    def predict(self, x: torch.Tensor, threshold: float = 0.5) -> torch.Tensor:
        """Predict segmentation mask with sigmoid activation and thresholding.

        Args:
            x: Input tensor of shape (B, in_channels, H, W).
            threshold: Threshold for binary segmentation (default: 0.5).

        Returns:
            Binary mask of shape (B, out_channels, H, W) with values 0 or 1.
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probs = torch.sigmoid(logits)
            masks = (probs > threshold).float()
        return masks

    def count_parameters(self) -> int:
        """Count the total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def __repr__(self) -> str:
        return (
            f"UNet(in_channels={self.in_channels}, out_channels={self.out_channels}, "
            f"base_channels={self.base_channels}, n_levels={self.n_levels}, "
            f"parameters={self.count_parameters():,})"
        )
