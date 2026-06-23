"""
Shared fixtures for CARLA RL tests.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add src to path so imports work from project root
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from carla_rl.envs.mock_carla_env import MockCarlaRLEnv
from carla_rl.utils.observation import ObservationProcessor
from carla_rl.utils.reward import RewardCalculator, ShapedRewardCalculator


@pytest.fixture
def mock_env():
    """Create a mock environment for testing."""
    env = MockCarlaRLEnv(max_steps=100, seed=42)
    yield env
    env.close()


@pytest.fixture
def mock_env_with_camera():
    """Create a mock environment with camera enabled."""
    env = MockCarlaRLEnv(max_steps=100, use_camera=True, image_size=(84, 84), seed=42)
    yield env
    env.close()


@pytest.fixture
def obs_processor():
    """Create an observation processor."""
    return ObservationProcessor()


@pytest.fixture
def reward_calc():
    """Create a reward calculator with default settings."""
    return RewardCalculator(target_speed=30.0)


@pytest.fixture
def shaped_reward_calc():
    """Create a shaped reward calculator."""
    return ShapedRewardCalculator(target_speed=30.0, gamma=0.99)


@pytest.fixture
def sample_vehicle_state():
    """Sample vehicle state dictionary for testing."""
    return {
        "speed": 25.0,
        "steer": 0.1,
        "throttle": 0.4,
        "brake": 0.0,
        "dist_to_center": 0.5,
        "heading_error": 0.05,
        "waypoints": np.array(
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            dtype=np.float32,
        ),
    }
