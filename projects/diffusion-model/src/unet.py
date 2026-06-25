"""
U-Net Architecture for Noise Prediction in Diffusion Models.

Implements a simplified U-Net with time embeddings for DDPM.
Based on: https://arxiv.org/abs/2006.11239
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import List, Optional, Tuple


class SinusoidalPositionEmbeddings(nn.Module):
    """
    Sinusoidal position embeddings for timestep encoding.
    Similar to Transformer positional encodings.
    """

    def __init__(self, dim: int):
        """
        Initialize sinusoidal embeddings.

        Args:
            dim: Dimension of the embeddings
        """
        super().__init__()
        self.dim = dim

    def forward(self, time: torch.Tensor) -> torch.Tensor:
        """
        Create sinusoidal embeddings for timesteps.

        Args:
            time: Timestep tensor [B]

        Returns:
            Time embeddings [B, dim]
        """
        device = time.device
        half_dim = self.dim // 2
        embeddings = math.log(10000) / (half_dim - 1)
        embeddings = torch.exp(torch.arange(half_dim, device=device) * -embeddings)
        embeddings = time[:, None] * embeddings[None, :]
        embeddings = torch.cat((embeddings.sin(), embeddings.cos()), dim=-1)

        return embeddings


class ResidualBlock(nn.Module):
    """
    Residual block with time embedding.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        time_emb_dim: int,
        dropout: float = 0.1
    ):
        """
        Initialize residual block.

        Args:
            in_channels: Number of input channels
            out_channels: Number of output channels
            time_emb_dim: Dimension of time embeddings
            dropout: Dropout rate
        """
        super().__init__()

        self.norm1 = nn.GroupNorm(8, in_channels)
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)

        self.time_mlp = nn.Sequential(
            nn.SiLU(),
            nn.Linear(time_emb_dim, out_channels)
        )

        self.norm2 = nn.GroupNorm(8, out_channels)
        self.dropout = nn.Dropout(dropout)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)

        if in_channels != out_channels:
            self.shortcut = nn.Conv2d(in_channels, out_channels, kernel_size=1)
        else:
            self.shortcut = nn.Identity()

    def forward(self, x: torch.Tensor, time_emb: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor [B, C, H, W]
            time_emb: Time embedding [B, time_emb_dim]

        Returns:
            Output tensor [B, out_channels, H, W]
        """
        h = self.norm1(x)
        h = F.silu(h)
        h = self.conv1(h)

        # Add time embedding
        time_emb = self.time_mlp(time_emb)
        h = h + time_emb[:, :, None, None]

        h = self.norm2(h)
        h = F.silu(h)
        h = self.dropout(h)
        h = self.conv2(h)

        return h + self.shortcut(x)


class AttentionBlock(nn.Module):
    """
    Self-attention block for capturing long-range dependencies.
    """

    def __init__(
        self,
        channels: int,
        num_heads: int = 4
    ):
        """
        Initialize attention block.

        Args:
            channels: Number of channels
            num_heads: Number of attention heads
        """
        super().__init__()

        self.norm = nn.GroupNorm(8, channels)
        self.attention = nn.MultiheadAttention(
            embed_dim=channels,
            num_heads=num_heads,
            batch_first=True
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor [B, C, H, W]

        Returns:
            Output tensor [B, C, H, W]
        """
        B, C, H, W = x.shape
        h = self.norm(x)

        # Reshape for attention: [B, C, H, W] -> [B, H*W, C]
        h = h.view(B, C, H * W).transpose(1, 2)

        # Self-attention
        h, _ = self.attention(h, h, h)

        # Reshape back: [B, H*W, C] -> [B, C, H, W]
        h = h.transpose(1, 2).view(B, C, H, W)

        return h + x


class Downsample(nn.Module):
    """Downsample block using strided convolution."""

    def __init__(self, channels: int):
        super().__init__()
        self.conv = nn.Conv2d(channels, channels, kernel_size=3, stride=2, padding=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(x)


class Upsample(nn.Module):
    """Upsample block using transposed convolution."""

    def __init__(self, channels: int):
        super().__init__()
        self.conv = nn.ConvTranspose2d(channels, channels, kernel_size=4, stride=2, padding=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(x)


class UNet(nn.Module):
    """
    U-Net architecture for noise prediction in diffusion models.

    This version uses a clean encoder-decoder structure with skip connections.
    For larger images, you would need more layers and channels.

    Architecture for hidden_channels=[64, 128, 256]:
        Encoder: init_conv -> [level0:64@HxW] -> down -> [level1:128@H/2xH/2] -> down -> [level2:256@H/4xW/4]
        Middle: [256@H/4xW/4]
        Decoder: up -> cat(skip_level1) -> [level1:128@H/2xH/2] -> up -> cat(skip_level0) -> [level0:64@HxW]
        Final: [out_channels@HxW]
    """

    def __init__(
        self,
        in_channels: int = 1,
        out_channels: int = 1,
        hidden_channels: List[int] = [64, 128, 256],
        time_emb_dim: int = 256,
        num_res_blocks: int = 2,
        attention: bool = True,
        dropout: float = 0.1
    ):
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.hidden_channels = hidden_channels
        self.num_levels = len(hidden_channels)

        # Time embedding network
        self.time_mlp = nn.Sequential(
            SinusoidalPositionEmbeddings(time_emb_dim),
            nn.Linear(time_emb_dim, time_emb_dim * 4),
            nn.SiLU(),
            nn.Linear(time_emb_dim * 4, time_emb_dim)
        )

        # Initial convolution
        self.init_conv = nn.Conv2d(in_channels, hidden_channels[0], kernel_size=3, padding=1)

        # Encoder (downsampling) blocks
        # Each level has residual blocks that process features
        self.down_blocks = nn.ModuleList()
        self.down_samples = nn.ModuleList()

        current_channels = hidden_channels[0]
        for i, out_ch in enumerate(hidden_channels):
            blocks = nn.ModuleList()
            for _ in range(num_res_blocks):
                blocks.append(ResidualBlock(current_channels, out_ch, time_emb_dim, dropout))
                current_channels = out_ch
                if attention and i >= 1:
                    blocks.append(AttentionBlock(current_channels))
            self.down_blocks.append(blocks)

            if i < self.num_levels - 1:
                self.down_samples.append(Downsample(current_channels))

        # Middle block
        self.middle_block = nn.Sequential(
            ResidualBlock(current_channels, current_channels, time_emb_dim, dropout),
            AttentionBlock(current_channels) if attention else nn.Identity(),
            ResidualBlock(current_channels, current_channels, time_emb_dim, dropout)
        )

        # Decoder (upsampling) blocks
        # Reversed channels: [256, 128, 64] for hidden_channels=[64, 128, 256]
        reversed_channels = list(reversed(hidden_channels))
        # Number of decoder levels = num_levels - 1 (deepest level is the bottleneck)
        num_decoder_levels = self.num_levels - 1

        self.up_samples = nn.ModuleList()
        self.up_blocks = nn.ModuleList()

        current_channels = hidden_channels[-1]  # Start from deepest level channels
        for i in range(num_decoder_levels):
            # Upsample to match encoder spatial dimensions
            up = Upsample(current_channels)
            self.up_samples.append(up)

            # After upsampling, concatenate with skip connection
            skip_ch = reversed_channels[i + 1]  # Matching encoder level
            cat_channels = current_channels + skip_ch

            blocks = nn.ModuleList()
            for j in range(num_res_blocks):
                in_ch = cat_channels if j == 0 else reversed_channels[i + 1]
                blocks.append(ResidualBlock(in_ch, reversed_channels[i + 1], time_emb_dim, dropout))
                current_channels = reversed_channels[i + 1]
                if attention and i <= 0:
                    blocks.append(AttentionBlock(current_channels))
            self.up_blocks.append(blocks)

        # Final convolution
        self.final_conv = nn.Sequential(
            nn.GroupNorm(8, current_channels),
            nn.SiLU(),
            nn.Conv2d(current_channels, out_channels, kernel_size=3, padding=1)
        )

    def forward(self, x: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input noisy image [B, C, H, W]
            t: Timestep indices [B]

        Returns:
            Predicted noise [B, C, H, W]
        """
        t_emb = self.time_mlp(t)

        # Initial convolution
        h = self.init_conv(x)

        # Encoder path: store skip connections at each level
        # We store features BEFORE downsampling at each level except the deepest
        skips = []
        for i, blocks in enumerate(self.down_blocks):
            for block in blocks:
                if isinstance(block, ResidualBlock):
                    h = block(h, t_emb)
                else:
                    h = block(h)

            if i < self.num_levels - 1:
                skips.append(h)  # Store features before downsampling
                h = self.down_samples[i](h)

        # Middle block (processes deepest level features)
        for block in self.middle_block:
            if isinstance(block, ResidualBlock):
                h = block(h, t_emb)
            else:
                h = block(h)

        # Decoder path: upsample and concatenate with skip connections
        # skips are stored in order [level0, level1, ...], we pop from end
        for i, blocks in enumerate(self.up_blocks):
            # Upsample to match encoder spatial dimensions
            h = self.up_samples[i](h)

            # Concatenate with skip connection from encoder (matching spatial dims)
            skip = skips.pop()
            h = torch.cat([h, skip], dim=1)

            # Process with residual blocks
            for block in blocks:
                if isinstance(block, ResidualBlock):
                    h = block(h, t_emb)
                else:
                    h = block(h)

        # Final convolution
        return self.final_conv(h)


class SimpleUNet(nn.Module):
    """
    Simplified U-Net for educational purposes.
    Easier to understand but less powerful than the full implementation.

    This version uses a simpler architecture that properly handles
    skip connections with matching spatial dimensions.
    """

    def __init__(
        self,
        in_channels: int = 1,
        out_channels: int = 1,
        time_emb_dim: int = 128
    ):
        """
        Initialize simplified U-Net.

        Args:
            in_channels: Number of input channels
            out_channels: Number of output channels
            time_emb_dim: Dimension of time embeddings
        """
        super().__init__()

        # Time embedding
        self.time_mlp = nn.Sequential(
            SinusoidalPositionEmbeddings(time_emb_dim),
            nn.Linear(time_emb_dim, time_emb_dim),
            nn.SiLU(),
            nn.Linear(time_emb_dim, time_emb_dim)
        )

        # Encoder (downsampling path)
        self.enc1 = self._block(in_channels, 64)
        self.enc2 = self._block(64, 128)

        # Bottleneck
        self.bottleneck = nn.Sequential(
            nn.Conv2d(128, 256, 3, padding=1),
            nn.GroupNorm(8, 256),
            nn.SiLU(),
            nn.Conv2d(256, 256, 3, padding=1),
            nn.GroupNorm(8, 256),
            nn.SiLU()
        )

        # Time embedding projection
        self.time_proj = nn.Linear(time_emb_dim, 256)

        # Decoder (upsampling path)
        self.dec2 = self._block(128 + 128, 128)
        self.dec1 = self._block(64 + 64, 64)

        # Final output layer
        self.final_conv = nn.Conv2d(64, out_channels, 3, padding=1)

        # Downsampling
        self.down = nn.MaxPool2d(2)

        # Upsampling
        self.up2 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.up1 = nn.ConvTranspose2d(128, 64, 2, stride=2)

    def _block(self, in_ch: int, out_ch: int) -> nn.Sequential:
        """Create a convolutional block."""
        # Use dynamic num_groups to handle cases where out_ch < 8
        num_groups = min(8, out_ch) if out_ch >= 1 else 1
        return nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.GroupNorm(num_groups, out_ch),
            nn.SiLU(),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.GroupNorm(num_groups, out_ch),
            nn.SiLU()
        )

    def forward(self, x: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input noisy image [B, C, H, W]
            t: Timestep indices [B]

        Returns:
            Predicted noise [B, C, H, W]
        """
        # Time embedding
        t_emb = self.time_mlp(t)

        # Encoder
        e1 = self.enc1(x)  # [B, 64, H, W]
        e2 = self.enc2(self.down(e1))  # [B, 128, H/2, W/2]

        # Bottleneck with time embedding
        b = self.bottleneck(self.down(e2))  # [B, 256, H/4, W/4]
        t_proj = self.time_proj(t_emb)[:, :, None, None]
        b = b + t_proj

        # Decoder with skip connections
        d2 = self.up2(b)  # [B, 128, H/2, W/2]
        d2 = torch.cat([d2, e2], dim=1)  # [B, 256, H/2, W/2]
        d2 = self.dec2(d2)  # [B, 128, H/2, W/2]

        d1 = self.up1(d2)  # [B, 64, H, W]
        d1 = torch.cat([d1, e1], dim=1)  # [B, 128, H, W]
        d1 = self.dec1(d1)  # [B, 64, H, W]

        return self.final_conv(d1)
