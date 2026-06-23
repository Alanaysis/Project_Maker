"""
Tests for ObservationProcessor.
"""

import numpy as np
import pytest

from carla_rl.utils.observation import ObservationProcessor


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestObservationProcessorInit:
    """Construction and default values."""

    def test_default_init(self):
        proc = ObservationProcessor()
        assert proc.image_size == (84, 84)
        assert proc.use_camera is False
        assert proc.normalize_features is True

    def test_feature_dim(self):
        proc = ObservationProcessor()
        # 6 basic + 5 waypoints * 2
        assert proc.feature_dim == 16

    def test_custom_image_size(self):
        proc = ObservationProcessor(image_size=(64, 64))
        assert proc.image_size == (64, 64)

    def test_no_normalization(self):
        proc = ObservationProcessor(normalize_features=False)
        assert proc.normalize_features is False


# ---------------------------------------------------------------------------
# Feature processing
# ---------------------------------------------------------------------------


class TestFeatureProcessing:
    """process_features tests."""

    def test_output_shape(self, obs_processor, sample_vehicle_state):
        features = obs_processor.process_features(sample_vehicle_state)
        assert features.shape == (obs_processor.feature_dim,)

    def test_output_dtype(self, obs_processor, sample_vehicle_state):
        features = obs_processor.process_features(sample_vehicle_state)
        assert features.dtype == np.float32

    def test_normalized_values_near_zero_for_mean(self):
        """Values at the mean should normalize to ~0."""
        proc = ObservationProcessor(normalize_features=True)
        state = {
            "speed": 30.0,  # mean
            "steer": 0.0,   # mean
            "throttle": 0.0,
            "brake": 0.0,
            "dist_to_center": 0.0,
            "heading_error": 0.0,
            "waypoints": np.zeros(10, dtype=np.float32),
        }
        features = proc.process_features(state)
        # First few features should be near zero
        for i in range(6):
            assert abs(features[i]) < 0.1

    def test_unnormalized_preserves_values(self):
        """Without normalization, raw values should pass through."""
        proc = ObservationProcessor(normalize_features=False)
        state = {
            "speed": 42.0,
            "steer": 0.3,
            "throttle": 0.7,
            "brake": 0.1,
            "dist_to_center": 1.5,
            "heading_error": 0.2,
            "waypoints": np.ones(10, dtype=np.float32),
        }
        features = proc.process_features(state)
        assert features[0] == pytest.approx(42.0)
        assert features[1] == pytest.approx(0.3)

    def test_missing_keys_default_to_zero(self):
        proc = ObservationProcessor()
        state = {}  # empty
        features = proc.process_features(state)
        assert features.shape == (proc.feature_dim,)
        assert np.all(np.isfinite(features))

    def test_waypoint_normalization(self):
        """Waypoints should be divided by 10 when normalizing."""
        proc = ObservationProcessor(normalize_features=True)
        state = {
            "speed": 0.0,
            "steer": 0.0,
            "throttle": 0.0,
            "brake": 0.0,
            "dist_to_center": 0.0,
            "heading_error": 0.0,
            "waypoints": np.full(10, 10.0, dtype=np.float32),
        }
        features = proc.process_features(state)
        # Waypoints start at index 6; 10.0 / 10.0 = 1.0
        assert features[6] == pytest.approx(1.0)

    def test_all_finite(self, obs_processor, sample_vehicle_state):
        features = obs_processor.process_features(sample_vehicle_state)
        assert np.all(np.isfinite(features))


# ---------------------------------------------------------------------------
# Image processing
# ---------------------------------------------------------------------------


class TestImageProcessing:
    """process_image tests."""

    def test_numpy_passthrough(self):
        proc = ObservationProcessor(image_size=(84, 84))
        image = np.random.randint(0, 255, (84, 84, 3), dtype=np.uint8)
        result = proc.process_image(image)
        assert result.shape == (84, 84, 3)
        assert result.dtype == np.uint8

    def test_resize_larger(self):
        proc = ObservationProcessor(image_size=(84, 84))
        image = np.random.randint(0, 255, (160, 160, 3), dtype=np.uint8)
        result = proc.process_image(image)
        assert result.shape == (84, 84, 3)

    def test_resize_smaller(self):
        proc = ObservationProcessor(image_size=(84, 84))
        image = np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8)
        result = proc.process_image(image)
        assert result.shape == (84, 84, 3)

    def test_carla_image_object(self):
        """Simulate CARLA image object (has raw_data, height, width)."""

        class FakeImage:
            def __init__(self, h, w):
                self.height = h
                self.width = w
                self.raw_data = np.random.randint(
                    0, 255, h * w * 4, dtype=np.uint8
                ).tobytes()

        proc = ObservationProcessor(image_size=(84, 84))
        fake = FakeImage(100, 100)
        result = proc.process_image(fake)
        assert result.shape == (84, 84, 3)
        assert result.dtype == np.uint8

    def test_same_size_no_resize(self):
        proc = ObservationProcessor(image_size=(64, 64))
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        result = proc.process_image(image)
        assert result.shape == (64, 64, 3)


# ---------------------------------------------------------------------------
# Image utilities
# ---------------------------------------------------------------------------


class TestImageUtilities:
    """normalize_image, grayscale, stack_frames."""

    def test_normalize_image(self):
        proc = ObservationProcessor()
        image = np.full((84, 84, 3), 255, dtype=np.uint8)
        norm = proc.normalize_image(image)
        assert norm.dtype == np.float32
        assert norm.max() == pytest.approx(1.0)

    def test_normalize_image_zero(self):
        proc = ObservationProcessor()
        image = np.zeros((84, 84, 3), dtype=np.uint8)
        norm = proc.normalize_image(image)
        assert norm.min() == pytest.approx(0.0)

    def test_grayscale_shape(self):
        proc = ObservationProcessor()
        image = np.random.randint(0, 255, (84, 84, 3), dtype=np.uint8)
        gray = proc.grayscale(image)
        assert gray.shape == (84, 84, 1)
        assert gray.dtype == np.uint8

    def test_grayscale_already_gray(self):
        """If already single-channel, should pass through."""
        proc = ObservationProcessor()
        image = np.random.randint(0, 255, (84, 84, 1), dtype=np.uint8)
        result = proc.grayscale(image)
        assert result.shape == (84, 84, 1)

    def test_stack_frames_exact(self):
        proc = ObservationProcessor()
        frames = [np.ones((84, 84, 1), dtype=np.uint8) * i for i in range(4)]
        stacked = proc.stack_frames(frames, num_stack=4)
        assert stacked.shape == (84, 84, 4)

    def test_stack_frames_more_than_needed(self):
        """Should take only the last num_stack frames."""
        proc = ObservationProcessor()
        frames = [np.ones((84, 84, 1), dtype=np.uint8) * i for i in range(8)]
        stacked = proc.stack_frames(frames, num_stack=4)
        assert stacked.shape == (84, 84, 4)

    def test_stack_frames_padding(self):
        """Should zero-pad if fewer frames than num_stack."""
        proc = ObservationProcessor()
        frames = [np.ones((84, 84, 1), dtype=np.uint8) for _ in range(2)]
        stacked = proc.stack_frames(frames, num_stack=4)
        assert stacked.shape == (84, 84, 4)
        # First two channels should be zero (padded)
        assert np.all(stacked[:, :, 0] == 0)
        assert np.all(stacked[:, :, 1] == 0)


# ---------------------------------------------------------------------------
# Resize
# ---------------------------------------------------------------------------


class TestResize:
    """_resize_image internals."""

    def test_resize_square(self):
        proc = ObservationProcessor()
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = proc._resize_image(image, (50, 50))
        assert result.shape == (50, 50, 3)

    def test_resize_rectangular(self):
        proc = ObservationProcessor()
        image = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)
        result = proc._resize_image(image, (50, 100))
        assert result.shape == (50, 100, 3)
