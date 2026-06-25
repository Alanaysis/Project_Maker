"""
Context Encoder: U-Net Generator and PatchGAN Discriminator for Image Inpainting.

This module implements the core neural network architectures used in image inpainting:

1. **UNetGenerator**: An encoder-decoder architecture with skip connections.
2. **PatchDiscriminator**: A PatchGAN discriminator for local patch classification.

Key Concepts:
- The generator takes [corrupted_image, mask] (4 channels for RGB) and outputs 3ch
- Skip connections preserve fine spatial details from encoder to decoder
- PatchGAN focuses on local texture quality rather than global structure
"""

import torch
import torch.nn as nn
from typing import Optional


class UNetGenerator(nn.Module):
    """U-Net based generator for image inpainting.

    Architecture (for 128x128 input, ngf=64, num_downsamples=6):

    Encoder (downsample):
        128x128 (4ch) -> 64x64 (64) -> 32x32 (128) -> 16x16 (256)
        -> 8x8 (512) -> 4x4 (512) -> 2x2 (512)

    Bottleneck:
        2x2 (512) -> 1x1 (512)

    Decoder (upsample, with skip connections from encoder):
        1x1 (512) -> 2x2 (512)
        2x2 (512+512) -> 4x4 (512)
        4x4 (512+512) -> 8x8 (512)
        8x8 (512+512) -> 16x16 (256)
        16x16 (256+256) -> 32x32 (128)
        32x32 (128+128) -> 64x64 (64)

    Output layer:
        64x64 (64+64) -> 128x128 (3) with Tanh

    Args:
        in_channels: Number of input channels (default 4: RGB + mask).
        out_channels: Number of output channels (default 3: RGB).
        ngf: Number of generator filters in the first encoder layer.
        num_downsamples: Number of downsampling blocks. If None, defaults to 6.
        use_batchnorm: Whether to use batch normalization.
    """

    def __init__(
        self,
        in_channels: int = 4,
        out_channels: int = 3,
        ngf: int = 64,
        num_downsamples: Optional[int] = None,
        use_batchnorm: bool = True,
    ):
        super().__init__()
        if num_downsamples is None:
            num_downsamples = 6
        self.num_downsamples = num_downsamples

        def enc_ch(level):
            """Channels at encoder level."""
            return min(ngf * (2 ** level), ngf * 8)

        # ---- Encoder ----
        self.encoders = nn.ModuleList()
        for i in range(num_downsamples):
            in_ch = in_channels if i == 0 else enc_ch(i - 1)
            out_ch = enc_ch(i)
            use_bn = use_batchnorm and i > 0
            layers = [nn.Conv2d(in_ch, out_ch, 4, 2, 1, bias=False)]
            if use_bn:
                layers.append(nn.BatchNorm2d(out_ch))
            layers.append(nn.LeakyReLU(0.2, inplace=True))
            self.encoders.append(nn.Sequential(*layers))

        # ---- Bottleneck ----
        max_ch = enc_ch(num_downsamples - 1)
        self.bottleneck = nn.Sequential(
            nn.Conv2d(max_ch, max_ch, 4, 2, 1, bias=False),
            nn.ReLU(inplace=True),
        )

        # ---- Decoder ----
        # decoder[0]: no skip, bottleneck -> upsample
        # decoder[i>0]: cat(x, encoder[num_downsamples - i]) -> upsample
        self.decoders = nn.ModuleList()
        for i in range(num_downsamples):
            if i == 0:
                # No skip connection
                in_ch = max_ch
                out_ch = max_ch
            else:
                skip_idx = num_downsamples - i  # encoder index for skip
                skip_ch = enc_ch(skip_idx)
                # x channels = output of previous decoder
                if i == 1:
                    x_ch = max_ch  # decoder[0] outputs max_ch
                else:
                    prev_skip_idx = num_downsamples - (i - 1)
                    x_ch = enc_ch(prev_skip_idx)
                in_ch = x_ch + skip_ch
                out_ch = skip_ch

            layers = [nn.ConvTranspose2d(in_ch, out_ch, 4, 2, 1, bias=False)]
            if use_batchnorm:
                layers.append(nn.BatchNorm2d(out_ch))
            if i < 3:
                layers.append(nn.Dropout(0.5))
            layers.append(nn.ReLU(inplace=True))
            self.decoders.append(nn.Sequential(*layers))

        # ---- Output layer ----
        # Concat decoder[-1] output with encoder[0] output
        last_dec_out = enc_ch(1)  # decoder[-1] output channels
        first_enc_out = enc_ch(0)  # encoder[0] output channels
        self.output_layer = nn.Sequential(
            nn.ConvTranspose2d(last_dec_out + first_enc_out, out_channels, 4, 2, 1, bias=False),
            nn.Tanh(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the U-Net.

        Args:
            x: Input tensor of shape (B, 4, H, W) where channels are [R, G, B, Mask].

        Returns:
            Inpainted image tensor of shape (B, 3, H, W) with values in [-1, 1].
        """
        # Encoder path (save outputs for skip connections)
        encoder_outputs = []
        for encoder in self.encoders:
            x = encoder(x)
            encoder_outputs.append(x)

        # Bottleneck
        x = self.bottleneck(encoder_outputs[-1])

        # Decoder path with skip connections
        for i, decoder in enumerate(self.decoders):
            if i == 0:
                x = decoder(x)
            else:
                # Skip from encoder[num_downsamples - i]
                skip_idx = self.num_downsamples - i
                skip = encoder_outputs[skip_idx]
                x = decoder(torch.cat([x, skip], dim=1))

        # Output: concat with first encoder output
        output = self.output_layer(torch.cat([x, encoder_outputs[0]], dim=1))
        return output


class PatchDiscriminator(nn.Module):
    """PatchGAN discriminator for image inpainting.

    Classifies whether local image patches are real or fake.

    Architecture:
        Input (6ch: image pair) -> Conv layers -> patch-level predictions

    Args:
        in_channels: Number of input channels (default 6: image pair).
        ndf: Number of discriminator filters in the first layer.
        num_layers: Number of conv layers in the discriminator.
    """

    def __init__(
        self,
        in_channels: int = 6,
        ndf: int = 64,
        num_layers: int = 3,
    ):
        super().__init__()

        layers = [
            nn.Conv2d(in_channels, ndf, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
        ]

        nf_mult = 1
        for n in range(1, num_layers):
            nf_mult_prev = nf_mult
            nf_mult = min(2 ** n, 8)
            layers.extend([
                nn.Conv2d(ndf * nf_mult_prev, ndf * nf_mult, 4, 2, 1, bias=False),
                nn.BatchNorm2d(ndf * nf_mult),
                nn.LeakyReLU(0.2, inplace=True),
            ])

        # Final layer: stride=1 to maintain spatial resolution
        nf_mult_prev = nf_mult
        nf_mult = min(2 ** num_layers, 8)
        layers.extend([
            nn.Conv2d(ndf * nf_mult_prev, ndf * nf_mult, 4, 1, 1, bias=False),
            nn.BatchNorm2d(ndf * nf_mult),
            nn.LeakyReLU(0.2, inplace=True),
        ])

        # Output: single channel prediction map
        layers.append(nn.Conv2d(ndf * nf_mult, 1, 4, 1, 1, bias=False))

        self.model = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the PatchGAN discriminator.

        Args:
            x: Input tensor of shape (B, 6, H, W).

        Returns:
            Prediction map of shape (B, 1, H', W').
        """
        return self.model(x)


def weights_init(m: nn.Module) -> None:
    """Initialize network weights for GAN training stability.

    Convolutional layers: normal distribution with mean=0, std=0.02
    BatchNorm layers: weight ~ N(1, 0.02), bias = 0

    Args:
        m: A PyTorch module to initialize.
    """
    classname = m.__class__.__name__
    if classname.find("Conv") != -1:
        nn.init.normal_(m.weight.data, 0.0, 0.02)
    elif classname.find("BatchNorm") != -1:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0)
