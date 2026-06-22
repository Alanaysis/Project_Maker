"""
CLIP Model Implementation

Paper: "Learning Transferable Visual Models From Natural Language Supervision"
Authors: Alec Radford et al. (OpenAI)

⭐ CLIP Architecture:
1. Image Encoder (ViT or ResNet) -> Image Embedding
2. Text Encoder (Transformer) -> Text Embedding
3. Contrastive Loss to align embeddings

💡 Key Innovation:
- Uses natural language supervision (image-text pairs)
- Learns transferable visual representations
- Zero-shot classification capability

🎯 Training Objective:
- Maximize similarity of matched image-text pairs
- Minimize similarity of unmatched pairs
- Uses symmetric contrastive loss (InfoNCE)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict

from .vit import VisionTransformer, create_vit
from .text_encoder import TextTransformer, create_text_encoder


class CLIPModel(nn.Module):
    """
    CLIP (Contrastive Language-Image Pre-training) model.

    Architecture:
    ┌─────────────────┐    ┌─────────────────┐
    │   Image Encoder  │    │  Text Encoder    │
    │    (ViT)         │    │  (Transformer)   │
    └────────┬────────┘    └────────┬────────┘
             │                      │
             ▼                      ▼
    ┌─────────────────┐    ┌─────────────────┐
    │ Image Embedding  │    │ Text Embedding   │
    │   (B, embed_dim) │    │  (B, embed_dim)  │
    └────────┬────────┘    └────────┬────────┘
             │                      │
             └──────────┬───────────┘
                        │
                        ▼
              ┌─────────────────┐
              │ Contrastive Loss │
              │    (InfoNCE)     │
              └─────────────────┘

    ⭐ Key Design Choices:
    - Temperature parameter τ is learnable (initialized to 1/0.07)
    - Both encoders project to the same embedding dimension
    - Embeddings are L2-normalized before computing similarity

    💡 Zero-shot Classification:
    1. Encode class descriptions as text embeddings
    2. Encode query image as image embedding
    3. Compute cosine similarity with all class embeddings
    4. Predict class with highest similarity

    Example:
        >>> model = CLIPModel()
        >>> images = torch.randn(2, 3, 224, 224)
        >>> texts = torch.randint(0, 49408, (2, 77))
        >>> outputs = model(images, texts)
        >>> logits = outputs["logits_per_image"]  # (2, 2)
    """

    def __init__(
        self,
        # Image encoder config
        image_model: str = "vit_base",
        image_size: int = 224,
        patch_size: int = 16,
        # Text encoder config
        vocab_size: int = 49408,
        max_seq_len: int = 77,
        # Shared config
        embed_dim: int = 512,
        # Projection
        projection_dim: int = 512,
        # Temperature
        init_temperature: float = 0.07,
    ):
        super().__init__()

        # Image encoder
        self.image_encoder = create_vit(
            model_name=image_model,
            image_size=image_size,
            patch_size=patch_size,
            num_classes=embed_dim,  # Output embed_dim instead of num_classes
        )

        # Text encoder
        self.text_encoder = create_text_encoder(
            config_name="text_base",
            vocab_size=vocab_size,
            max_seq_len=max_seq_len,
            embed_dim=embed_dim,
        )

        # Projection layers (optional, for additional transformation)
        self.image_projection = nn.Linear(embed_dim, projection_dim, bias=False)
        self.text_projection = nn.Linear(embed_dim, projection_dim, bias=False)

        # Learnable temperature parameter
        # ⭐ Temperature controls the sharpness of the softmax distribution
        # Lower temperature -> sharper distribution -> more confident predictions
        self.logit_scale = nn.Parameter(
            torch.ones([]) * torch.tensor(1.0 / init_temperature).log()
        )

        self._init_weights()

    def _init_weights(self):
        """Initialize projection weights."""
        for m in [self.image_projection, self.text_projection]:
            nn.init.trunc_normal_(m.weight, std=0.02)

    def encode_image(self, images: torch.Tensor) -> torch.Tensor:
        """
        Encode images to embeddings.

        Args:
            images: Input images, shape (B, C, H, W)

        Returns:
            Image embeddings, shape (B, projection_dim)
        """
        # Get features from ViT
        image_features = self.image_encoder(images, return_features=True)

        # Project to shared space
        image_embeddings = self.image_projection(image_features)

        # L2 normalize
        image_embeddings = F.normalize(image_embeddings, dim=-1)

        return image_embeddings

    def encode_text(self, tokens: torch.Tensor) -> torch.Tensor:
        """
        Encode text to embeddings.

        Args:
            tokens: Token IDs, shape (B, seq_len)

        Returns:
            Text embeddings, shape (B, projection_dim)
        """
        # Get features from text encoder
        text_features = self.text_encoder(tokens)

        # Project to shared space
        text_embeddings = self.text_projection(text_features)

        # L2 normalize
        text_embeddings = F.normalize(text_embeddings, dim=-1)

        return text_embeddings

    def forward(
        self,
        images: torch.Tensor,
        tokens: torch.Tensor,
        return_loss: bool = True,
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass.

        Args:
            images: Input images, shape (B, C, H, W)
            tokens: Text token IDs, shape (B, seq_len)
            return_loss: Whether to compute and return the contrastive loss

        Returns:
            Dictionary containing:
            - logits_per_image: Similarity matrix, shape (B, B)
            - logits_per_text: Similarity matrix, shape (B, B)
            - loss: Contrastive loss (if return_loss=True)
            - image_embeddings: Image embeddings, shape (B, projection_dim)
            - text_embeddings: Text embeddings, shape (B, projection_dim)
        """
        # Encode images and text
        image_embeddings = self.encode_image(images)
        text_embeddings = self.encode_text(tokens)

        # Compute cosine similarity
        # ⭐ Scale by learnable temperature
        logit_scale = self.logit_scale.exp()
        logits_per_image = logit_scale * image_embeddings @ text_embeddings.t()
        logits_per_text = logits_per_image.t()

        outputs = {
            "logits_per_image": logits_per_image,
            "logits_per_text": logits_per_text,
            "image_embeddings": image_embeddings,
            "text_embeddings": text_embeddings,
        }

        if return_loss:
            # Compute contrastive loss
            batch_size = images.shape[0]
            labels = torch.arange(batch_size, device=images.device)
            loss = (
                F.cross_entropy(logits_per_image, labels) +
                F.cross_entropy(logits_per_text, labels)
            ) / 2
            outputs["loss"] = loss

        return outputs


class CLIPConfig:
    """
    Configuration class for CLIP model.

    ⭐ Different CLIP variants:
    - CLIP-ViT-B/32: ViT-Base, patch size 32
    - CLIP-ViT-B/16: ViT-Base, patch size 16
    - CLIP-ViT-L/14: ViT-Large, patch size 14
    """

    # ViT-B/32 configuration
    VIT_B32 = {
        "image_model": "vit_base",
        "image_size": 224,
        "patch_size": 32,
        "embed_dim": 512,
        "projection_dim": 512,
    }

    # ViT-B/16 configuration
    VIT_B16 = {
        "image_model": "vit_base",
        "image_size": 224,
        "patch_size": 16,
        "embed_dim": 512,
        "projection_dim": 512,
    }

    # ViT-L/14 configuration
    VIT_L14 = {
        "image_model": "vit_large",
        "image_size": 224,
        "patch_size": 14,
        "embed_dim": 768,
        "projection_dim": 768,
    }


def create_clip_model(
    config: str = "vit_b32",
    **kwargs,
) -> CLIPModel:
    """
    Create a CLIP model from predefined configuration.

    Args:
        config: Configuration name ("vit_b32", "vit_b16", "vit_l14")
        **kwargs: Override configuration parameters

    Returns:
        CLIPModel instance
    """
    configs = {
        "vit_b32": CLIPConfig.VIT_B32,
        "vit_b16": CLIPConfig.VIT_B16,
        "vit_l14": CLIPConfig.VIT_L14,
    }

    if config not in configs:
        raise ValueError(f"Unknown config: {config}. Available: {list(configs.keys())}")

    model_config = configs[config].copy()
    model_config.update(kwargs)

    return CLIPModel(**model_config)
