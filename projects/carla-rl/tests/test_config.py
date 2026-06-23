"""
Tests for YAML configuration loading and structure.
"""

import sys
from pathlib import Path

import pytest
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

CONFIGS_DIR = Path(__file__).parent.parent / "configs"


# ---------------------------------------------------------------------------
# Config file existence
# ---------------------------------------------------------------------------


class TestConfigFiles:
    """Verify config files exist and are valid YAML."""

    def test_default_yaml_exists(self):
        assert (CONFIGS_DIR / "default.yaml").is_file()

    def test_mock_yaml_exists(self):
        assert (CONFIGS_DIR / "mock.yaml").is_file()

    def test_default_yaml_parseable(self):
        with open(CONFIGS_DIR / "default.yaml") as f:
            config = yaml.safe_load(f)
        assert isinstance(config, dict)

    def test_mock_yaml_parseable(self):
        with open(CONFIGS_DIR / "mock.yaml") as f:
            config = yaml.safe_load(f)
        assert isinstance(config, dict)


# ---------------------------------------------------------------------------
# Default config structure
# ---------------------------------------------------------------------------


class TestDefaultConfig:
    """Validate default.yaml has all required keys."""

    @pytest.fixture
    def config(self):
        with open(CONFIGS_DIR / "default.yaml") as f:
            return yaml.safe_load(f)

    def test_env_section(self, config):
        assert "env" in config
        env = config["env"]
        assert "host" in env
        assert "port" in env
        assert "town" in env
        assert "target_speed" in env
        assert "max_steps" in env
        assert "use_camera" in env
        assert "image_size" in env

    def test_reward_section(self, config):
        assert "reward" in config
        reward = config["reward"]
        for key in ("progress", "speed", "lane", "heading", "collision", "time", "comfort"):
            assert key in reward, f"Missing reward weight: {key}"

    def test_ppo_section(self, config):
        assert "ppo" in config
        ppo = config["ppo"]
        assert "policy" in ppo
        assert "learning_rate" in ppo
        assert "n_steps" in ppo
        assert "batch_size" in ppo
        assert "gamma" in ppo

    def test_training_section(self, config):
        assert "training" in config
        training = config["training"]
        assert "total_timesteps" in training
        assert "eval_freq" in training
        assert "save_freq" in training

    def test_logging_section(self, config):
        assert "logging" in config

    def test_target_speed_positive(self, config):
        assert config["env"]["target_speed"] > 0

    def test_max_steps_positive(self, config):
        assert config["env"]["max_steps"] > 0

    def test_gamma_range(self, config):
        gamma = config["ppo"]["gamma"]
        assert 0.0 <= gamma <= 1.0

    def test_learning_rate_positive(self, config):
        assert config["ppo"]["learning_rate"] > 0


# ---------------------------------------------------------------------------
# Mock config structure
# ---------------------------------------------------------------------------


class TestMockConfig:
    """Validate mock.yaml has all required keys."""

    @pytest.fixture
    def config(self):
        with open(CONFIGS_DIR / "mock.yaml") as f:
            return yaml.safe_load(f)

    def test_env_section(self, config):
        assert "env" in config
        env = config["env"]
        assert "target_speed" in env
        assert "max_steps" in env
        assert "road_width" in env

    def test_reward_section(self, config):
        assert "reward" in config

    def test_ppo_section(self, config):
        assert "ppo" in config

    def test_training_section(self, config):
        assert "training" in config

    def test_mock_timesteps_smaller(self):
        """Mock config should use fewer timesteps for faster testing."""
        with open(CONFIGS_DIR / "default.yaml") as f:
            default = yaml.safe_load(f)
        with open(CONFIGS_DIR / "mock.yaml") as f:
            mock = yaml.safe_load(f)
        assert mock["training"]["total_timesteps"] <= default["training"]["total_timesteps"]


# ---------------------------------------------------------------------------
# Config consistency
# ---------------------------------------------------------------------------


class TestConfigConsistency:
    """Cross-config consistency checks."""

    def test_reward_keys_match(self):
        """Both configs should define the same reward weight keys."""
        with open(CONFIGS_DIR / "default.yaml") as f:
            default = yaml.safe_load(f)
        with open(CONFIGS_DIR / "mock.yaml") as f:
            mock = yaml.safe_load(f)
        assert set(default["reward"].keys()) == set(mock["reward"].keys())

    def test_image_size_is_two_element_list(self):
        for name in ("default.yaml", "mock.yaml"):
            with open(CONFIGS_DIR / name) as f:
                config = yaml.safe_load(f)
            size = config["env"]["image_size"]
            assert len(size) == 2
            assert all(isinstance(v, int) for v in size)
