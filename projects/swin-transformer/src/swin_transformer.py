"""Swin Transformer Model.

This module implements the complete Swin Transformer architecture for image classification.
The architecture consists of:
1. Patch Embedding: Convert image patches to embeddings
2. Multiple Stages: Each stage has shifted window transformer blocks
3. Patch Merging: Downsample between stages (except the last)
4. Classification Head: Global average pooling + linear layer

The hierarchical design creates feature maps at multiple scales, making it
suitable for various vision tasks.
"""

import torch
import torch.nn as nn

from .patch_embedding import PatchEmbedding, PatchMerging
from .shifted_window import ShiftedWindowTransformerBlock


class SwinTransformerStage(nn.Module):
    """A stage of the Swin Transformer.

    Each stage consists of multiple shifted window transformer blocks.
    The first block uses shifted window attention, and the second uses
    regular window attention (alternating pattern).

    Args:
        dim: Number of input channels.
        input_resolution: Tuple of (height, width) of input feature map.
        depth: Number of transformer blocks in this stage.
        num_heads: Number of attention heads.
        window_size: Size of the attention window.
        mlp_ratio: Ratio of MLP hidden dim to embedding dim.
        qkv_bias: If True, add learnable bias to query, key, value.
        drop: Dropout rate.
        attn_drop: Dropout rate for attention weights.
        downsample: Downsample layer at the end of the stage.
    """

    def __init__(
        self,
        dim: int,
        input_resolution: tuple,
        depth: int,
        num_heads: int,
        window_size: int = 7,
        mlp_ratio: float = 4.0,
        qkv_bias: bool = True,
        drop: float = 0.0,
        attn_drop: float = 0.0,
        downsample=None,
    ):
        super().__init__()
        self.dim = dim
        self.input_resolution = input_resolution
        self.depth = depth

        # Build transformer blocks
        self.blocks = nn.ModuleList([
            ShiftedWindowTransformerBlock(
                dim=dim,
                input_resolution=input_resolution,
                num_heads=num_heads,
                window_size=window_size,
                shift_size=0 if i % 2 == 0 else window_size // 2,
                mlp_ratio=mlp_ratio,
                qkv_bias=qkv_bias,
                drop=drop,
                attn_drop=attn_drop,
            )
            for i in range(depth)
        ])

        # Optional downsample layer
        self.downsample = downsample

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input tensor of shape (B, H*W, C).

        Returns:
            Output tensor, optionally downsampled.
        """
        for block in self.blocks:
            x = block(x)

        if self.downsample is not None:
            x = self.downsample(x)

        return x


class SwinTransformer(nn.Module):
    """Swin Transformer for image classification.

    A hierarchical Vision Transformer that uses shifted window attention
    for efficient computation. It produces hierarchical feature maps
    similar to CNNs while maintaining the advantages of transformers.

    Args:
        img_size: Input image size.
        patch_size: Patch size for initial embedding.
        in_channels: Number of input channels.
        num_classes: Number of classification classes.
        embed_dim: Initial embedding dimension.
        depths: Number of blocks in each stage.
        num_heads: Number of attention heads in each stage.
        window_size: Size of the attention window.
        mlp_ratio: Ratio of MLP hidden dim to embedding dim.
        qkv_bias: If True, add learnable bias to query, key, value.
        drop_rate: Dropout rate.
        attn_drop_rate: Dropout rate for attention weights.
    """

    def __init__(
        self,
        img_size: int = 224,
        patch_size: int = 4,
        in_channels: int = 3,
        num_classes: int = 1000,
        embed_dim: int = 96,
        depths: tuple = (2, 2, 6, 2),
        num_heads: tuple = (3, 6, 12, 24),
        window_size: int = 7,
        mlp_ratio: float = 4.0,
        qkv_bias: bool = True,
        drop_rate: float = 0.0,
        attn_drop_rate: float = 0.0,
    ):
        super().__init__()
        self.num_classes = num_classes
        self.num_layers = len(depths)
        self.embed_dim = embed_dim
        self.num_features = int(embed_dim * 2 ** (self.num_layers - 1))
        self.mlp_ratio = mlp_ratio

        # Patch embedding
        self.patch_embed = PatchEmbedding(
            img_size=img_size,
            patch_size=patch_size,
            in_channels=in_channels,
            embed_dim=embed_dim,
        )

        # Calculate initial feature map resolution
        patches_resolution = self.patch_embed.num_patches_h
        self.patches_resolution = patches_resolution

        # Absolute position embedding (optional)
        self.pos_drop = nn.Dropout(p=drop_rate)

        # Build stages
        self.layers = nn.ModuleList()
        for i_layer in range(self.num_layers):
            # Calculate dimension and resolution for this stage
            stage_dim = int(embed_dim * 2 ** i_layer)
            stage_resolution = (patches_resolution // (2 ** i_layer), patches_resolution // (2 ** i_layer))

            # Downsample layer (except for the last stage)
            if i_layer < self.num_layers - 1:
                downsample = PatchMerging(
                    input_resolution=stage_resolution,
                    dim=stage_dim,
                )
            else:
                downsample = None

            # Create stage
            stage = SwinTransformerStage(
                dim=stage_dim,
                input_resolution=stage_resolution,
                depth=depths[i_layer],
                num_heads=num_heads[i_layer],
                window_size=window_size,
                mlp_ratio=mlp_ratio,
                qkv_bias=qkv_bias,
                drop=drop_rate,
                attn_drop=attn_drop_rate,
                downsample=downsample,
            )
            self.layers.append(stage)

        # Final normalization
        self.norm = nn.LayerNorm(self.num_features)

        # Classification head
        self.avgpool = nn.AdaptiveAvgPool1d(1)
        self.head = nn.Linear(self.num_features, num_classes) if num_classes > 0 else nn.Identity()

        # Initialize weights
        self.apply(self._init_weights)

    def _init_weights(self, m: nn.Module):
        """Initialize weights using trunc_normal_."""
        if isinstance(m, nn.Linear):
            nn.init.trunc_normal_(m.weight, std=0.02)
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LayerNorm):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)

    def forward_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract features without classification head.

        Args:
            x: Input image tensor of shape (B, C, H, W).

        Returns:
            Feature tensor of shape (B, num_features).
        """
        # Patch embedding
        x = self.patch_embed(x)  # (B, num_patches, embed_dim)

        # Position dropout
        x = self.pos_drop(x)

        # Process through stages
        for layer in self.layers:
            x = layer(x)

        # Final normalization
        x = self.norm(x)  # (B, H'*W', C')

        # Global average pooling
        x = self.avgpool(x.transpose(1, 2))  # (B, C', 1)
        x = x.flatten(1)  # (B, C')

        return x

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input image tensor of shape (B, C, H, W).

        Returns:
            Classification logits of shape (B, num_classes).
        """
        x = self.forward_features(x)
        x = self.head(x)
        return x


def swin_tiny_patch4_window7_224(num_classes: int = 1000) -> SwinTransformer:
    """Create Swin-Tiny model configuration.

    This is the smallest Swin Transformer variant, suitable for
    learning and experimentation.

    Args:
        num_classes: Number of classification classes.

    Returns:
        SwinTransformer model instance.
    """
    return SwinTransformer(
        img_size=224,
        patch_size=4,
        in_channels=3,
        num_classes=num_classes,
        embed_dim=96,
        depths=(2, 2, 6, 2),
        num_heads=(3, 6, 12, 24),
        window_size=7,
        mlp_ratio=4.0,
        qkv_bias=True,
        drop_rate=0.0,
        attn_drop_rate=0.0,
    )


def swin_small_patch4_window7_224(num_classes: int = 1000) -> SwinTransformer:
    """Create Swin-Small model configuration.

    Args:
        num_classes: Number of classification classes.

    Returns:
        SwinTransformer model instance.
    """
    return SwinTransformer(
        img_size=224,
        patch_size=4,
        in_channels=3,
        num_classes=num_classes,
        embed_dim=96,
        depths=(2, 2, 18, 2),
        num_heads=(3, 6, 12, 24),
        window_size=7,
        mlp_ratio=4.0,
        qkv_bias=True,
        drop_rate=0.0,
        attn_drop_rate=0.0,
    )


def swin_base_patch4_window7_224(num_classes: int = 1000) -> SwinTransformer:
    """Create Swin-Base model configuration.

    Args:
        num_classes: Number of classification classes.

    Returns:
        SwinTransformer model instance.
    """
    return SwinTransformer(
        img_size=224,
        patch_size=4,
        in_channels=3,
        num_classes=num_classes,
        embed_dim=128,
        depths=(2, 2, 18, 2),
        num_heads=(4, 8, 16, 32),
        window_size=7,
        mlp_ratio=4.0,
        qkv_bias=True,
        drop_rate=0.0,
        attn_drop_rate=0.0,
    )
