"""
Tests for utility functions.
"""

import sys
import numpy as np
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from carla_rl.utils.observation import ObservationProcessor
from carla_rl.utils.reward import RewardCalculator, ShapedRewardCalculator


class TestObservationProcessor:
    """Test suite for ObservationProcessor."""

    def test_init(self):
        """Test initialization."""
        processor = ObservationProcessor()
        assert processor.feature_dim > 0
        assert processor.image_size == (84, 84)

    def test_feature_dim(self):
        """Test feature dimension calculation."""
        processor = ObservationProcessor()
        # 6 basic features + 5 waypoints * 2
        expected_dim = 6 + 5 * 2
        assert processor.feature_dim == expected_dim

    def test_process_features(self):
        """Test feature processing."""
        processor = ObservationProcessor()

        vehicle_state = {
            "speed": 30.0,
            "steer": 0.1,
            "throttle": 0.5,
            "brake": 0.0,
            "dist_to_center": 1.0,
            "heading_error": 0.05,
            "waypoints": np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]),
        }

        features = processor.process_features(vehicle_state)

        assert isinstance(features, np.ndarray)
        assert features.dtype == np.float32
        assert features.shape == (processor.feature_dim,)

    def test_process_features_normalization(self):
        """Test feature normalization."""
        processor = ObservationProcessor(normalize_features=True)

        vehicle_state = {
            "speed": 30.0,
            "steer": 0.0,
            "throttle": 0.0,
            "brake": 0.0,
            "dist_to_center": 0.0,
            "heading_error": 0.0,
            "waypoints": np.zeros(10),
        }

        features = processor.process_features(vehicle_state)

        # Normalized features should be close to zero for mean values
        assert abs(features[0]) < 0.1  # speed near mean
        assert abs(features[1]) < 0.1  # steer near mean

    def test_process_image_numpy(self):
        """Test image processing with numpy array."""
        processor = ObservationProcessor(image_size=(84, 84))

        # Create test image
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        processed = processor.process_image(image)

        assert processed.shape == (84, 84, 3)
        assert processed.dtype == np.uint8

    def test_resize_image(self):
        """Test image resizing."""
        processor = ObservationProcessor(image_size=(64, 64))

        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        resized = processor._resize_image(image, (64, 64))

        assert resized.shape == (64, 64, 3)

    def test_normalize_image(self):
        """Test image normalization."""
        processor = ObservationProcessor()

        image = np.random.randint(0, 255, (84, 84, 3), dtype=np.uint8)
        normalized = processor.normalize_image(image)

        assert normalized.dtype == np.float32
        assert normalized.min() >= 0.0
        assert normalized.max() <= 1.0

    def test_grayscale(self):
        """Test grayscale conversion."""
        processor = ObservationProcessor()

        image = np.random.randint(0, 255, (84, 84, 3), dtype=np.uint8)
        gray = processor.grayscale(image)

        assert gray.shape == (84, 84, 1)
        assert gray.dtype == np.uint8

    def test_stack_frames(self):
        """Test frame stacking."""
        processor = ObservationProcessor()

        frames = [
            np.random.randint(0, 255, (84, 84, 1), dtype=np.uint8)
            for _ in range(6)
        ]

        stacked = processor.stack_frames(frames, num_stack=4)

        assert stacked.shape == (84, 84, 4)

    def test_stack_frames_padding(self):
        """Test frame stacking with padding."""
        processor = ObservationProcessor()

        frames = [
            np.random.randint(0, 255, (84, 84, 1), dtype=np.uint8)
            for _ in range(2)
        ]

        stacked = processor.stack_frames(frames, num_stack=4)

        # Should pad with zeros
        assert stacked.shape == (84, 84, 4)


class TestRewardCalculator:
    """Test suite for RewardCalculator."""

    def test_init(self):
        """Test initialization."""
        calc = RewardCalculator(target_speed=30.0)
        assert calc.target_speed == 30.0

    def test_compute_basic(self):
        """Test basic reward computation."""
        calc = RewardCalculator(target_speed=30.0)

        reward = calc.compute(
            speed=30.0,
            dist_to_center=0.0,
            heading_error=0.0,
            collision=False,
            lane_invasion=False,
            step_count=1,
        )

        assert isinstance(reward, float)

    def test_speed_reward(self):
        """Test speed reward component."""
        calc = RewardCalculator(target_speed=30.0)

        # At target speed
        reward_target = calc._speed_reward(30.0)

        # Below target speed
        reward_slow = calc._speed_reward(15.0)

        # Above target speed
        reward_fast = calc._speed_reward(45.0)

        # Target speed should give highest reward
        assert reward_target > reward_slow
        assert reward_target > reward_fast

    def test_lane_reward(self):
        """Test lane keeping reward."""
        calc = RewardCalculator()

        # Centered
        reward_center = calc._lane_reward(0.0)

        # Off-center
        reward_off = calc._lane_reward(2.0)

        # Centered should give higher reward
        assert reward_center > reward_off

    def test_heading_reward(self):
        """Test heading reward."""
        calc = RewardCalculator()

        # Correct heading
        reward_correct = calc._heading_reward(0.0)

        # Wrong heading
        reward_wrong = calc._heading_reward(np.pi / 2)

        # Correct heading should give higher reward
        assert reward_correct > reward_wrong

    def test_collision_penalty(self):
        """Test collision penalty."""
        calc = RewardCalculator()

        reward_no_collision = calc.compute(
            speed=30.0,
            dist_to_center=0.0,
            heading_error=0.0,
            collision=False,
            lane_invasion=False,
            step_count=1,
        )

        reward_collision = calc.compute(
            speed=30.0,
            dist_to_center=0.0,
            heading_error=0.0,
            collision=True,
            lane_invasion=False,
            step_count=1,
        )

        # Collision should give much lower reward
        assert reward_collision < reward_no_collision

    def test_custom_weights(self):
        """Test custom reward weights."""
        weights = {
            "progress": 2.0,
            "speed": 1.0,
            "collision": -200.0,
        }

        calc = RewardCalculator(target_speed=30.0, weights=weights)

        assert calc.weights["progress"] == 2.0
        assert calc.weights["speed"] == 1.0
        assert calc.weights["collision"] == -200.0

    def test_reset(self):
        """Test reset function."""
        calc = RewardCalculator()

        # Modify state
        calc.prev_speed = 50.0

        calc.reset()

        assert calc.prev_speed == 0.0


class TestShapedRewardCalculator:
    """Test suite for ShapedRewardCalculator."""

    def test_init(self):
        """Test initialization."""
        calc = ShapedRewardCalculator(target_speed=30.0, gamma=0.99)
        assert calc.gamma == 0.99

    def test_potential(self):
        """Test potential function."""
        calc = ShapedRewardCalculator()

        state_good = {
            "speed": 30.0,
            "dist_to_center": 0.0,
            "heading_error": 0.0,
        }

        state_bad = {
            "speed": 10.0,
            "dist_to_center": 3.0,
            "heading_error": np.pi / 2,
        }

        potential_good = calc.potential(state_good)
        potential_bad = calc.potential(state_bad)

        # Good state should have higher potential
        assert potential_good > potential_bad

    def test_compute_shaped(self):
        """Test shaped reward computation."""
        calc = ShapedRewardCalculator(gamma=0.99)

        # First step
        reward1 = calc.compute(
            speed=30.0,
            dist_to_center=0.0,
            heading_error=0.0,
            collision=False,
            lane_invasion=False,
            step_count=1,
        )

        # Second step (should include shaping)
        reward2 = calc.compute(
            speed=30.0,
            dist_to_center=0.0,
            heading_error=0.0,
            collision=False,
            lane_invasion=False,
            step_count=2,
        )

        assert isinstance(reward1, float)
        assert isinstance(reward2, float)

    def test_reset(self):
        """Test reset function."""
        calc = ShapedRewardCalculator()

        # Modify state
        calc.prev_potential = 5.0

        calc.reset()

        assert calc.prev_potential == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
