"""Patch Embedding for Swin Transformer.

This module converts images into patch embeddings, which is the first step
in the Swin Transformer pipeline: Image → Patch Embedding → Window Attention.
"""

import torch
import torch.nn as nn


class PatchEmbedding(nn.Module):
    """Convert image patches to embeddings.

    Splits the input image into non-overlapping patches and projects each patch
    into a higher-dimensional embedding space using a convolutional layer.

    Args:
        img_size: Input image size (assumed square).
        patch_size: Size of each patch (assumed square).
        in_channels: Number of input channels (e.g., 3 for RGB).
        embed_dim: Dimension of the patch embeddings.
    """

    def __init__(
        self,
        img_size: int = 224,
        patch_size: int = 4,
        in_channels: int = 3,
        embed_dim: int = 96,
    ):
        super().__init__()
        self.img_size = img_size
        self.patch_size = patch_size
        self.in_channels = in_channels
        self.embed_dim = embed_dim

        # Calculate number of patches
        self.num_patches_h = img_size // patch_size
        self.num_patches_w = img_size // patch_size
        self.num_patches = self.num_patches_h * self.num_patches_w

        # Use Conv2d to create patch embeddings
        # stride = patch_size ensures non-overlapping patches
        self.projection = nn.Conv2d(
            in_channels=in_channels,
            out_channels=embed_dim,
            kernel_size=patch_size,
            stride=patch_size,
        )

        self.norm = nn.LayerNorm(embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input tensor of shape (B, C, H, W).

        Returns:
            Patch embeddings of shape (B, num_patches, embed_dim).
        """
        B, C, H, W = x.shape

        # Project patches: (B, C, H, W) -> (B, embed_dim, H//p, W//p)
        x = self.projection(x)

        # Flatten spatial dimensions: (B, embed_dim, H', W') -> (B, embed_dim, H'*W')
        x = x.flatten(2)

        # Transpose to (B, num_patches, embed_dim)
        x = x.transpose(1, 2)

        # Apply layer normalization
        x = self.norm(x)

        return x


class PatchMerging(nn.Module):
    """Patch Merging Layer for downsampling.

    Reduces spatial resolution by 2x while doubling the feature dimension.
    This is used between stages in the Swin Transformer to create
    hierarchical feature maps.

    Args:
        input_resolution: Tuple of (height, width) of input feature map.
        dim: Number of input channels.
    """

    def __init__(self, input_resolution: tuple, dim: int):
        super().__init__()
        self.input_resolution = input_resolution
        self.dim = dim

        # Linear layer to reduce dimension after merging
        self.reduction = nn.Linear(4 * dim, 2 * dim, bias=False)
        self.norm = nn.LayerNorm(4 * dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input tensor of shape (B, H*W, C).

        Returns:
            Merged patches of shape (B, H/2*W/2, 2*C).
        """
        H, W = self.input_resolution
        B, L, C = x.shape

        assert L == H * W, f"Input feature size ({L}) doesn't match resolution ({H}x{W})."

        # Reshape to 2D spatial dimensions
        x = x.view(B, H, W, C)

        # Extract 2x2 patches (non-overlapping)
        # Stack 4 neighboring patches
        x0 = x[:, 0::2, 0::2, :]  # Top-left
        x1 = x[:, 1::2, 0::2, :]  # Bottom-left
        x2 = x[:, 0::2, 1::2, :]  # Top-right
        x3 = x[:, 1::2, 1::2, :]  # Bottom-right

        # Concatenate along feature dimension
        x = torch.cat([x0, x1, x2, x3], dim=-1)  # (B, H/2, W/2, 4*C)

        # Reshape back to sequence
        x = x.view(B, -1, 4 * C)

        # Normalize and project
        x = self.norm(x)
        x = self.reduction(x)

        return x
