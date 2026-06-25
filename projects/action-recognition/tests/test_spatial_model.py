"""Tests for spatial feature extraction model."""

import pytest
import torch

from action_recognition.models.spatial_model import SpatialModel


class TestSpatialModel:
    """Test suite for SpatialModel."""

    def test_default_initialization(self):
        model = SpatialModel(pretrained=False)
        assert model.backbone_name == "resnet18"
        assert model.feature_dim == 512

    def test_resnet50_initialization(self):
        model = SpatialModel(backbone="resnet50", pretrained=False)
        assert model.feature_dim == 2048

    def test_custom_feature_dim(self):
        model = SpatialModel(feature_dim=256, pretrained=False)
        assert model.feature_dim == 256
        assert model.projection is not None

    def test_invalid_backbone(self):
        with pytest.raises(ValueError, match="Unsupported backbone"):
            SpatialModel(backbone="invalid_backbone")

    def test_forward_single_frame(self):
        model = SpatialModel(pretrained=False)
        x = torch.randn(2, 3, 224, 224)
        out = model(x)
        assert out.shape == (2, 512)

    def test_forward_video_clip(self):
        model = SpatialModel(pretrained=False)
        x = torch.randn(2, 4, 3, 224, 224)
        out = model(x)
        assert out.shape == (2, 4, 512)

    def test_forward_with_projection(self):
        model = SpatialModel(feature_dim=256, pretrained=False)
        x = torch.randn(2, 3, 224, 224)
        out = model(x)
        assert out.shape == (2, 256)

    def test_freeze_backbone(self):
        model = SpatialModel(pretrained=False, freeze_backbone=True)
        for param in model.feature_extractor.parameters():
            assert not param.requires_grad

    def test_not_freeze_backbone(self):
        model = SpatialModel(pretrained=False, freeze_backbone=False)
        has_trainable = any(
            p.requires_grad for p in model.feature_extractor.parameters()
        )
        assert has_trainable
