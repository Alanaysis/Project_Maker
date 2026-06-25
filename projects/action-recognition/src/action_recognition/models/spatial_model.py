"""
Spatial feature extraction model using CNN backbone.

Uses a pre-trained CNN (ResNet-18 by default) to extract spatial features
from individual video frames. The final classification layer is removed,
and features are extracted from the penultimate layer.
"""

from typing import Optional

import torch
import torch.nn as nn
import torchvision.models as models


class SpatialModel(nn.Module):
    """Extract spatial features from video frames using CNN backbone.

    Supported backbones:
        - resnet18 (default): 512-dim features
        - resnet34: 512-dim features
        - resnet50: 2048-dim features
        - vgg16: 4096-dim features

    Args:
        backbone: Name of the CNN backbone architecture.
        pretrained: Whether to use ImageNet pre-trained weights.
        feature_dim: Output feature dimension (0 means use backbone default).
        freeze_backbone: Whether to freeze backbone parameters.
    """

    BACKBONE_FEATURE_DIMS = {
        "resnet18": 512,
        "resnet34": 512,
        "resnet50": 2048,
        "vgg16": 4096,
    }

    def __init__(
        self,
        backbone: str = "resnet18",
        pretrained: bool = True,
        feature_dim: int = 0,
        freeze_backbone: bool = False,
    ):
        super().__init__()

        if backbone not in self.BACKBONE_FEATURE_DIMS:
            raise ValueError(
                f"Unsupported backbone '{backbone}'. "
                f"Choose from: {list(self.BACKBONE_FEATURE_DIMS.keys())}"
            )

        self.backbone_name = backbone
        self.pretrained = pretrained
        self._build_backbone(backbone, pretrained, freeze_backbone)

        backbone_dim = self.BACKBONE_FEATURE_DIMS[backbone]

        if feature_dim > 0 and feature_dim != backbone_dim:
            self.projection = nn.Linear(backbone_dim, feature_dim)
            self._feature_dim = feature_dim
        else:
            self.projection = None
            self._feature_dim = backbone_dim

    def _build_backbone(
        self, backbone: str, pretrained: bool, freeze: bool
    ) -> None:
        """Build CNN backbone without the final classification layer."""
        weights = "IMAGENET1K_V1" if pretrained else None

        if backbone.startswith("resnet"):
            model_fn = getattr(models, backbone)
            base_model = model_fn(weights=weights)
            # Remove the final FC layer
            self.feature_extractor = nn.Sequential(*list(base_model.children())[:-1])
        elif backbone == "vgg16":
            base_model = models.vgg16(weights=weights)
            # Remove the final classifier layers
            self.feature_extractor = base_model.features
            self.avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        else:
            raise ValueError(f"Unsupported backbone: {backbone}")

        if freeze:
            for param in self.feature_extractor.parameters():
                param.requires_grad = False

    @property
    def feature_dim(self) -> int:
        """Return the output feature dimension."""
        return self._feature_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Extract spatial features from frames.

        Args:
            x: Input tensor of shape (B, C, H, W) or (B, T, C, H, W).

        Returns:
            Feature tensor of shape (B, feature_dim) or (B, T, feature_dim).
        """
        has_time_dim = x.dim() == 5
        if has_time_dim:
            B, T, C, H, W = x.shape
            x = x.view(B * T, C, H, W)

        features = self.feature_extractor(x)

        if self.backbone_name == "vgg16":
            features = self.avg_pool(features)

        features = features.flatten(1)

        if self.projection is not None:
            features = self.projection(features)

        if has_time_dim:
            features = features.view(B, T, -1)

        return features
