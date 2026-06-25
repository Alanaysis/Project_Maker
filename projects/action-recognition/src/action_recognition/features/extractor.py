"""
Feature extraction pipeline for action recognition.

Combines spatial and temporal feature extraction into a unified interface.
Supports both raw feature extraction and cached feature loading.
"""

import os
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import numpy as np

from action_recognition.models.spatial_model import SpatialModel
from action_recognition.models.temporal_model import TemporalModel


class FeatureExtractor:
    """Extract spatio-temporal features from video clips.

    Provides a high-level interface for feature extraction with support for:
        - Batch processing
        - Feature caching to disk
        - Multiple backbone architectures

    Args:
        backbone: CNN backbone for spatial features.
        pretrained: Whether to use pre-trained weights.
        temporal_arch: Temporal architecture type.
        hidden_dim: Temporal model hidden dimension.
        device: Device to run extraction on.
    """

    def __init__(
        self,
        backbone: str = "resnet18",
        pretrained: bool = True,
        temporal_arch: str = "lstm",
        hidden_dim: int = 256,
        device: Optional[str] = None,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self.spatial_model = SpatialModel(
            backbone=backbone, pretrained=pretrained
        ).to(self.device)
        self.spatial_model.eval()

        self.temporal_model = TemporalModel(
            input_dim=self.spatial_model.feature_dim,
            hidden_dim=hidden_dim,
            arch=temporal_arch,
        ).to(self.device)
        self.temporal_model.eval()

    @torch.no_grad()
    def extract_spatial(
        self, frames: torch.Tensor
    ) -> torch.Tensor:
        """Extract spatial features from video frames.

        Args:
            frames: Tensor of shape (B, T, C, H, W).

        Returns:
            Spatial features of shape (B, T, feature_dim).
        """
        frames = frames.to(self.device)
        return self.spatial_model(frames).cpu()

    @torch.no_grad()
    def extract_temporal(
        self,
        spatial_features: torch.Tensor,
        lengths: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Extract temporal features from spatial feature sequences.

        Args:
            spatial_features: Tensor of shape (B, T, feature_dim).
            lengths: Actual sequence lengths (optional).

        Returns:
            Temporal features of shape (B, temporal_output_dim).
        """
        spatial_features = spatial_features.to(self.device)
        if lengths is not None:
            lengths = lengths.to(self.device)
        return self.temporal_model(spatial_features, lengths).cpu()

    @torch.no_grad()
    def extract(
        self,
        frames: torch.Tensor,
        lengths: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """Extract both spatial and temporal features.

        Args:
            frames: Video tensor of shape (B, T, C, H, W).
            lengths: Actual sequence lengths (optional).

        Returns:
            Dict with 'spatial' and 'temporal' feature tensors.
        """
        spatial = self.extract_spatial(frames)
        temporal = self.extract_temporal(spatial, lengths)
        return {"spatial": spatial, "temporal": temporal}

    def save_features(
        self,
        features: Dict[str, torch.Tensor],
        path: str,
    ) -> None:
        """Save extracted features to disk.

        Args:
            features: Dict of feature tensors.
            path: File path to save features.
        """
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        torch.save(features, path)

    def load_features(self, path: str) -> Dict[str, torch.Tensor]:
        """Load cached features from disk.

        Args:
            path: File path to load features from.

        Returns:
            Dict of feature tensors.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Feature file not found: {path}")
        return torch.load(path, map_location="cpu")
