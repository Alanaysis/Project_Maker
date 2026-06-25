"""
Action classifier combining spatial and temporal models.

End-to-end model that processes video clips through spatial feature
extraction, temporal modeling, and final action classification.
"""

from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from action_recognition.models.spatial_model import SpatialModel
from action_recognition.models.temporal_model import TemporalModel


class ActionClassifier(nn.Module):
    """End-to-end action recognition model.

    Pipeline: Video frames -> Spatial features -> Temporal modeling -> Classification

    Args:
        num_classes: Number of action categories.
        backbone: CNN backbone for spatial feature extraction.
        pretrained: Whether to use pre-trained backbone weights.
        temporal_arch: Temporal architecture ('lstm', 'gru', 'transformer').
        hidden_dim: Hidden dimension for temporal model.
        num_layers: Number of temporal layers.
        dropout: Dropout probability.
        freeze_backbone: Whether to freeze the backbone during training.
    """

    def __init__(
        self,
        num_classes: int,
        backbone: str = "resnet18",
        pretrained: bool = True,
        temporal_arch: str = "lstm",
        hidden_dim: int = 256,
        num_layers: int = 2,
        dropout: float = 0.3,
        freeze_backbone: bool = False,
    ):
        super().__init__()

        self.num_classes = num_classes
        self.spatial_model = SpatialModel(
            backbone=backbone,
            pretrained=pretrained,
            freeze_backbone=freeze_backbone,
        )

        self.temporal_model = TemporalModel(
            input_dim=self.spatial_model.feature_dim,
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            arch=temporal_arch,
            dropout=dropout,
        )

        self.classifier = nn.Sequential(
            nn.Linear(self.temporal_model.output_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(
        self,
        video_clips: torch.Tensor,
        lengths: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Classify actions in video clips.

        Args:
            video_clips: Video tensor of shape (B, T, C, H, W).
            lengths: Actual frame counts per clip (optional).

        Returns:
            Logits of shape (B, num_classes).
        """
        B, T, C, H, W = video_clips.shape

        # Extract spatial features for each frame
        spatial_features = self.spatial_model(video_clips)  # (B, T, feat_dim)

        # Model temporal relationships
        temporal_features = self.temporal_model(spatial_features, lengths)  # (B, hidden)

        # Classify
        logits = self.classifier(temporal_features)  # (B, num_classes)

        return logits

    def predict(
        self,
        video_clips: torch.Tensor,
        lengths: Optional[torch.Tensor] = None,
        top_k: int = 5,
    ) -> List[Dict[str, float]]:
        """Predict action classes with confidence scores.

        Args:
            video_clips: Video tensor of shape (B, T, C, H, W).
            lengths: Actual frame counts per clip (optional).
            top_k: Number of top predictions to return.

        Returns:
            List of dicts mapping class indices to probabilities.
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(video_clips, lengths)
            probs = F.softmax(logits, dim=-1)

        results = []
        for i in range(probs.size(0)):
            top_probs, top_indices = probs[i].topk(top_k)
            pred = {
                idx.item(): prob.item()
                for idx, prob in zip(top_indices, top_probs)
            }
            results.append(pred)

        return results

    def get_spatial_features(
        self, video_clips: torch.Tensor
    ) -> torch.Tensor:
        """Extract spatial features only (for feature visualization).

        Args:
            video_clips: Video tensor of shape (B, T, C, H, W).

        Returns:
            Spatial features of shape (B, T, feature_dim).
        """
        return self.spatial_model(video_clips)

    def get_temporal_features(
        self,
        video_clips: torch.Tensor,
        lengths: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Extract temporal features (before classification).

        Args:
            video_clips: Video tensor of shape (B, T, C, H, W).
            lengths: Actual frame counts per clip (optional).

        Returns:
            Temporal features of shape (B, temporal_output_dim).
        """
        spatial_features = self.spatial_model(video_clips)
        return self.temporal_model(spatial_features, lengths)
