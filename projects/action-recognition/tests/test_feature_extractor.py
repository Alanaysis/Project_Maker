"""Tests for feature extraction pipeline."""

import pytest
import torch

from action_recognition.features.extractor import FeatureExtractor


class TestFeatureExtractor:
    """Test suite for FeatureExtractor."""

    def test_initialization(self):
        extractor = FeatureExtractor(pretrained=False)
        assert extractor.spatial_model is not None
        assert extractor.temporal_model is not None

    def test_extract_spatial(self):
        extractor = FeatureExtractor(pretrained=False)
        frames = torch.randn(2, 4, 3, 224, 224)
        features = extractor.extract_spatial(frames)
        assert features.shape == (2, 4, 512)

    def test_extract_temporal(self):
        extractor = FeatureExtractor(pretrained=False)
        spatial = torch.randn(2, 4, 512)
        temporal = extractor.extract_temporal(spatial)
        assert temporal.shape[0] == 2

    def test_extract_both(self):
        extractor = FeatureExtractor(pretrained=False)
        frames = torch.randn(2, 4, 3, 224, 224)
        result = extractor.extract(frames)
        assert "spatial" in result
        assert "temporal" in result
        assert result["spatial"].shape == (2, 4, 512)
        assert result["temporal"].shape[0] == 2

    def test_extract_with_lengths(self):
        extractor = FeatureExtractor(pretrained=False)
        frames = torch.randn(2, 8, 3, 224, 224)
        lengths = torch.tensor([8, 6])
        result = extractor.extract(frames, lengths)
        assert "spatial" in result
        assert "temporal" in result

    def test_save_load_features(self, tmp_path):
        extractor = FeatureExtractor(pretrained=False)
        frames = torch.randn(2, 4, 3, 224, 224)
        features = extractor.extract(frames)

        save_path = str(tmp_path / "features.pt")
        extractor.save_features(features, save_path)

        loaded = extractor.load_features(save_path)
        assert torch.equal(features["spatial"], loaded["spatial"])
        assert torch.equal(features["temporal"], loaded["temporal"])

    def test_load_nonexistent_file(self):
        extractor = FeatureExtractor(pretrained=False)
        with pytest.raises(FileNotFoundError):
            extractor.load_features("/nonexistent/path/features.pt")
