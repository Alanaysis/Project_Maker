"""
Tests for feature extraction module.
"""

import pytest
import numpy as np
import cv2
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.feature_extractor import FeatureExtractor, Frame
from src.config import FeatureConfig


@pytest.fixture
def feature_extractor():
    """Create feature extractor instance."""
    return FeatureExtractor()


@pytest.fixture
def sample_image():
    """Create sample test image."""
    image = np.zeros((480, 640), dtype=np.uint8)
    # Add some geometric shapes
    cv2.rectangle(image, (100, 100), (200, 200), 255, -1)
    cv2.circle(image, (400, 300), 50, 255, -1)
    cv2.line(image, (0, 0), (640, 480), 255, 2)
    return image


@pytest.fixture
def sample_color_image():
    """Create sample color test image."""
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(image, (100, 100), (200, 200), (0, 255, 0), -1)
    cv2.circle(image, (400, 300), 50, (0, 0, 255), -1)
    return image


class TestFeatureExtractor:
    """Test cases for FeatureExtractor."""

    def test_initialization(self, feature_extractor):
        """Test feature extractor initialization."""
        assert feature_extractor.orb is not None
        assert feature_extractor.matcher is not None
        assert feature_extractor.frame_counter == 0

    def test_extract_features(self, feature_extractor, sample_image):
        """Test feature extraction from image."""
        frame = feature_extractor.extract(sample_image)

        assert isinstance(frame, Frame)
        assert frame.id == 0
        assert frame.num_features > 0
        assert frame.descriptors is not None
        assert len(frame.keypoints) == frame.num_features

    def test_extract_features_color_image(self, feature_extractor, sample_color_image):
        """Test feature extraction from color image."""
        frame = feature_extractor.extract(sample_color_image)

        assert frame.num_features > 0
        assert len(frame.image.shape) == 2  # Should be converted to grayscale

    def test_frame_counter(self, feature_extractor, sample_image):
        """Test frame counter increments."""
        frame1 = feature_extractor.extract(sample_image)
        frame2 = feature_extractor.extract(sample_image)

        assert frame1.id == 0
        assert frame2.id == 1

    def test_match_features(self, feature_extractor, sample_image):
        """Test feature matching."""
        # Extract features from same image
        frame1 = feature_extractor.extract(sample_image)
        frame2 = feature_extractor.extract(sample_image)

        # Match features
        matches = feature_extractor.match_features(
            frame1.descriptors,
            frame2.descriptors
        )

        # Should find matches (same image)
        assert len(matches) > 0

    def test_match_frames(self, feature_extractor, sample_image):
        """Test frame matching."""
        frame1 = feature_extractor.extract(sample_image)
        frame2 = feature_extractor.extract(sample_image)

        matches, points1, points2 = feature_extractor.match_frames(frame1, frame2)

        assert len(matches) > 0
        assert points1.shape[1] == 2
        assert points2.shape[1] == 2
        assert len(matches) == len(points1) == len(points2)

    def test_empty_descriptors(self, feature_extractor):
        """Test matching with empty descriptors."""
        empty_desc = np.array([])
        matches = feature_extractor.match_features(empty_desc, empty_desc)

        assert len(matches) == 0

    def test_get_keypoint_positions(self, feature_extractor, sample_image):
        """Test getting keypoint positions."""
        frame = feature_extractor.extract(sample_image)
        positions = frame.get_keypoint_positions()

        assert positions.shape == (frame.num_features, 2)
        assert positions.dtype == np.float32

    def test_custom_config(self):
        """Test feature extractor with custom config."""
        config = FeatureConfig(n_features=500)
        extractor = FeatureExtractor(config)

        assert extractor.config.n_features == 500


class TestFrame:
    """Test cases for Frame dataclass."""

    def test_frame_properties(self, feature_extractor, sample_image):
        """Test frame properties."""
        frame = feature_extractor.extract(sample_image)

        assert frame.num_features == len(frame.keypoints)
        assert frame.image is not None
        assert frame.timestamp == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
