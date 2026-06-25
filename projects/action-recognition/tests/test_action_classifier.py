"""Tests for end-to-end action classifier."""

import pytest
import torch

from action_recognition.models.action_classifier import ActionClassifier


class TestActionClassifier:
    """Test suite for ActionClassifier."""

    def test_initialization(self):
        model = ActionClassifier(num_classes=10, pretrained=False)
        assert model.num_classes == 10

    def test_forward(self):
        model = ActionClassifier(num_classes=5, pretrained=False)
        x = torch.randn(2, 4, 3, 224, 224)
        out = model(x)
        assert out.shape == (2, 5)

    def test_forward_with_lengths(self):
        model = ActionClassifier(num_classes=5, pretrained=False)
        x = torch.randn(2, 8, 3, 224, 224)
        lengths = torch.tensor([8, 6])
        out = model(x, lengths)
        assert out.shape == (2, 5)

    def test_predict(self):
        model = ActionClassifier(num_classes=10, pretrained=False)
        model.eval()
        x = torch.randn(3, 4, 3, 224, 224)
        results = model.predict(x, top_k=3)
        assert len(results) == 3
        for pred in results:
            assert len(pred) == 3
            # All probabilities should be positive and sum to <= 1.0
            total = sum(pred.values())
            assert total <= 1.0 + 1e-6
            assert all(v > 0 for v in pred.values())

    def test_different_backbones(self):
        for backbone in ["resnet18", "resnet34"]:
            model = ActionClassifier(
                num_classes=5, backbone=backbone, pretrained=False
            )
            x = torch.randn(1, 4, 3, 224, 224)
            out = model(x)
            assert out.shape == (1, 5)

    def test_different_temporal_archs(self):
        for arch in ["lstm", "gru", "transformer"]:
            model = ActionClassifier(
                num_classes=5, temporal_arch=arch, pretrained=False
            )
            x = torch.randn(2, 4, 3, 224, 224)
            out = model(x)
            assert out.shape == (2, 5)

    def test_get_spatial_features(self):
        model = ActionClassifier(num_classes=5, pretrained=False)
        x = torch.randn(2, 4, 3, 224, 224)
        features = model.get_spatial_features(x)
        assert features.dim() == 3  # (B, T, feat_dim)
        assert features.shape[0] == 2
        assert features.shape[1] == 4

    def test_get_temporal_features(self):
        model = ActionClassifier(num_classes=5, pretrained=False)
        x = torch.randn(2, 4, 3, 224, 224)
        features = model.get_temporal_features(x)
        assert features.dim() == 2  # (B, feat_dim)
        assert features.shape[0] == 2

    def test_freeze_backbone(self):
        model = ActionClassifier(
            num_classes=5, pretrained=False, freeze_backbone=True
        )
        for param in model.spatial_model.feature_extractor.parameters():
            assert not param.requires_grad
