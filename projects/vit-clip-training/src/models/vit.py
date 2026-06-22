"""
Vision Transformer (ViT) Implementation

Paper: "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale"
Authors: Alexey Dosovitskiy et al.

Architecture Overview:
1. Split image into fixed-size patches
2. Linearly embed each patch
3. Add position embeddings
4. Pass through Transformer encoder
5. Use [CLS] token for classification

⭐ Key Insight: ViT treats image patches as "tokens" similar to NLP transformers.
This allows leveraging the powerful self-attention mechanism for vision tasks.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple


class PatchEmbedding(nn.Module):
    """
    Convert image to patch embeddings.

    ⭐ This is the key innovation of ViT:
    - Split image into non-overlapping patches
    - Project each patch to embedding dimension
    - Add learnable [CLS] token and position embeddings

    Input: (B, C, H, W)
    Output: (B, num_patches + 1, embed_dim)  # +1 for [CLS] token
    """

    def __init__(
        self,
        image_size: int = 224,
        patch_size: int = 16,
        in_channels: int = 3,
        embed_dim: int = 768,
    ):
        super().__init__()
        self.image_size = image_size
        self.patch_size = patch_size
        self.num_patches = (image_size // patch_size) ** 2

        # Convolution to extract patches and project to embed_dim
        # This is equivalent to: flatten patches -> linear projection
        self.projection = nn.Conv2d(
            in_channels, embed_dim,
            kernel_size=patch_size,
            stride=patch_size
        )

        # Learnable [CLS] token - used for classification
        self.cls_token = nn.Parameter(torch.randn(1, 1, embed_dim))

        # Learnable position embeddings
        # +1 for [CLS] token
        self.position_embedding = nn.Parameter(
            torch.randn(1, self.num_patches + 1, embed_dim)
        )

        self._init_weights()

    def _init_weights(self):
        """Initialize weights with truncated normal distribution."""
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        nn.init.trunc_normal_(self.position_embedding, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input images, shape (B, C, H, W)

        Returns:
            Patch embeddings with [CLS] token, shape (B, num_patches + 1, embed_dim)
        """
        B = x.shape[0]

        # Extract patches and project: (B, C, H, W) -> (B, embed_dim, H/P, W/P)
        x = self.projection(x)

        # Flatten spatial dimensions: (B, embed_dim, H/P, W/P) -> (B, embed_dim, num_patches)
        x = x.flatten(2)

        # Transpose: (B, embed_dim, num_patches) -> (B, num_patches, embed_dim)
        x = x.transpose(1, 2)

        # Prepend [CLS] token
        cls_tokens = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)

        # Add position embeddings
        x = x + self.position_embedding

        return x


class MultiHeadAttention(nn.Module):
    """
    Multi-Head Self-Attention mechanism.

    ⭐ Core of Transformer architecture:
    - Allows each token to attend to all other tokens
    - Captures long-range dependencies
    - Multiple heads capture different types of relationships

    💡 Why self-attention for vision?
    - Convolution has local receptive field
    - Self-attention has global receptive field from the start
    - Can learn to focus on relevant image regions
    """

    def __init__(
        self,
        embed_dim: int = 768,
        num_heads: int = 12,
        dropout: float = 0.0,
    ):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5

        assert embed_dim % num_heads == 0, "embed_dim must be divisible by num_heads"

        self.qkv = nn.Linear(embed_dim, 3 * embed_dim)
        self.proj = nn.Linear(embed_dim, embed_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            x: Input tensor, shape (B, N, D)
            mask: Optional attention mask

        Returns:
            Output tensor, shape (B, N, D)
        """
        B, N, D = x.shape

        # Compute Q, K, V
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)
        q, k, v = qkv.unbind(0)

        # Compute attention scores
        attn = (q @ k.transpose(-2, -1)) * self.scale

        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))

        attn = F.softmax(attn, dim=-1)
        attn = self.dropout(attn)

        # Apply attention to values
        x = (attn @ v).transpose(1, 2).reshape(B, N, D)
        x = self.proj(x)

        return x


class TransformerBlock(nn.Module):
    """
    Single Transformer encoder block.

    Structure:
    1. Layer Norm -> Multi-Head Attention -> Residual Connection
    2. Layer Norm -> MLP -> Residual Connection

    💡 Pre-norm vs Post-norm:
    - Original Transformer uses post-norm (LN after residual)
    - ViT uses pre-norm (LN before attention/MLP)
    - Pre-norm is more stable for training
    """

    def __init__(
        self,
        embed_dim: int = 768,
        num_heads: int = 12,
        mlp_ratio: float = 4.0,
        dropout: float = 0.0,
    ):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn = MultiHeadAttention(embed_dim, num_heads, dropout)
        self.norm2 = nn.LayerNorm(embed_dim)

        mlp_hidden = int(embed_dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim, mlp_hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_hidden, embed_dim),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor, shape (B, N, D)

        Returns:
            Output tensor, shape (B, N, D)
        """
        # Self-attention with residual connection
        x = x + self.attn(self.norm1(x))

        # MLP with residual connection
        x = x + self.mlp(self.norm2(x))

        return x


class VisionTransformer(nn.Module):
    """
    Vision Transformer (ViT) model.

    Architecture:
    1. Patch Embedding: Split image into patches, add [CLS] token and position embeddings
    2. Transformer Encoder: Stack of Transformer blocks
    3. Classification Head: Use [CLS] token representation

    ⭐ Key Design Choices:
    - Patch size: 16x16 or 32x32 (trade-off between compute and performance)
    - [CLS] token: Aggregates global image information
    - Position embeddings: Learnable, captures spatial relationships

    💡 Variants:
    - ViT-B/16: Base model, patch size 16
    - ViT-L/14: Large model, patch size 14
    - ViT-H/14: Huge model, patch size 14

    Example:
        >>> model = VisionTransformer(image_size=224, patch_size=16, embed_dim=768)
        >>> x = torch.randn(2, 3, 224, 224)
        >>> output = model(x)  # (2, 768)
    """

    def __init__(
        self,
        image_size: int = 224,
        patch_size: int = 16,
        in_channels: int = 3,
        num_classes: int = 1000,
        embed_dim: int = 768,
        depth: int = 12,
        num_heads: int = 12,
        mlp_ratio: float = 4.0,
        dropout: float = 0.0,
        global_pool: str = "cls",  # "cls" or "mean"
    ):
        super().__init__()
        self.global_pool = global_pool

        # Patch embedding
        self.patch_embed = PatchEmbedding(
            image_size=image_size,
            patch_size=patch_size,
            in_channels=in_channels,
            embed_dim=embed_dim,
        )

        # Transformer encoder blocks
        self.blocks = nn.ModuleList([
            TransformerBlock(
                embed_dim=embed_dim,
                num_heads=num_heads,
                mlp_ratio=mlp_ratio,
                dropout=dropout,
            )
            for _ in range(depth)
        ])

        # Final layer norm
        self.norm = nn.LayerNorm(embed_dim)

        # Classification head
        self.head = nn.Linear(embed_dim, num_classes)

        self._init_weights()

    def _init_weights(self):
        """Initialize weights."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.trunc_normal_(m.weight, std=0.02)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.LayerNorm):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def forward_features(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extract features from the model.

        Args:
            x: Input images, shape (B, C, H, W)

        Returns:
            Features, shape (B, embed_dim)
        """
        # Patch embedding
        x = self.patch_embed(x)  # (B, num_patches + 1, embed_dim)

        # Transformer blocks
        for block in self.blocks:
            x = block(x)

        # Final normalization
        x = self.norm(x)

        # Global pooling
        if self.global_pool == "cls":
            x = x[:, 0]  # Use [CLS] token
        elif self.global_pool == "mean":
            x = x.mean(dim=1)  # Average all tokens

        return x

    def forward(
        self,
        x: torch.Tensor,
        return_features: bool = False,
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input images, shape (B, C, H, W)
            return_features: If True, return features before classification head

        Returns:
            If return_features=False: Classification logits, shape (B, num_classes)
            If return_features=True: Features, shape (B, embed_dim)
        """
        features = self.forward_features(x)

        if return_features:
            return features

        return self.head(features)


def vit_small(
    image_size: int = 224,
    patch_size: int = 16,
    num_classes: int = 1000,
    **kwargs,
) -> VisionTransformer:
    """ViT-Small configuration."""
    return VisionTransformer(
        image_size=image_size,
        patch_size=patch_size,
        num_classes=num_classes,
        embed_dim=384,
        depth=12,
        num_heads=6,
        **kwargs,
    )


def vit_base(
    image_size: int = 224,
    patch_size: int = 16,
    num_classes: int = 1000,
    **kwargs,
) -> VisionTransformer:
    """ViT-Base configuration."""
    return VisionTransformer(
        image_size=image_size,
        patch_size=patch_size,
        num_classes=num_classes,
        embed_dim=768,
        depth=12,
        num_heads=12,
        **kwargs,
    )


def vit_large(
    image_size: int = 224,
    patch_size: int = 16,
    num_classes: int = 1000,
    **kwargs,
) -> VisionTransformer:
    """ViT-Large configuration."""
    return VisionTransformer(
        image_size=image_size,
        patch_size=patch_size,
        num_classes=num_classes,
        embed_dim=1024,
        depth=24,
        num_heads=16,
        **kwargs,
    )


# Model configurations registry
VIT_CONFIGS = {
    "vit_small": vit_small,
    "vit_base": vit_base,
    "vit_large": vit_large,
}


def create_vit(
    model_name: str = "vit_base",
    **kwargs,
) -> VisionTransformer:
    """
    Create a ViT model by name.

    Args:
        model_name: Name of the model configuration
        **kwargs: Additional arguments to pass to the model

    Returns:
        VisionTransformer model
    """
    if model_name not in VIT_CONFIGS:
        raise ValueError(f"Unknown model: {model_name}. Available: {list(VIT_CONFIGS.keys())}")

    return VIT_CONFIGS[model_name](**kwargs)
