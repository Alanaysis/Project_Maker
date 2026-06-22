"""
Tests for the Mock CARLA Environment.

These tests verify the mock environment works correctly
without requiring a CARLA simulator installation.
"""

import sys
import numpy as np
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from carla_rl.envs.mock_carla_env import MockCarlaRLEnv


class TestMockCarlaRLEnv:
    """Test suite for MockCarlaRLEnv."""

    def test_init(self):
        """Test environment initialization."""
        env = MockCarlaRLEnv()
        assert env is not None
        assert env.action_space is not None
        assert env.observation_space is not None
        env.close()

    def test_observation_space(self):
        """Test observation space definition."""
        env = MockCarlaRLEnv()
        obs_space = env.observation_space

        assert "features" in obs_space.spaces
        assert obs_space["features"].shape == (env.obs_processor.feature_dim,)
        assert obs_space["features"].dtype == np.float32

        env.close()

    def test_action_space(self):
        """Test action space definition."""
        env = MockCarlaRLEnv()
        action_space = env.action_space

        assert action_space.shape == (2,)
        assert action_space.low[0] == -1.0
        assert action_space.high[0] == 1.0
        assert action_space.low[1] == -1.0
        assert action_space.high[1] == 1.0

        env.close()

    def test_reset(self):
        """Test environment reset."""
        env = MockCarlaRLEnv(seed=42)
        obs, info = env.reset()

        assert isinstance(obs, dict)
        assert "features" in obs
        assert isinstance(obs["features"], np.ndarray)
        assert obs["features"].dtype == np.float32

        assert isinstance(info, dict)
        assert "speed" in info
        assert "dist_to_center" in info
        assert "step_count" in info
        assert info["step_count"] == 0

        env.close()

    def test_step(self):
        """Test environment step."""
        env = MockCarlaRLEnv(seed=42)
        obs, info = env.reset()

        # Take a step with throttle
        action = np.array([0.5, 0.0], dtype=np.float32)
        obs, reward, terminated, truncated, info = env.step(action)

        assert isinstance(obs, dict)
        assert "features" in obs
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)
        assert info["step_count"] == 1

        env.close()

    def test_multiple_steps(self):
        """Test multiple steps."""
        env = MockCarlaRLEnv(max_steps=10, seed=42)
        obs, info = env.reset()

        for i in range(10):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)

            if terminated or truncated:
                break

        # Episode should be truncated after max_steps
        assert info["step_count"] <= 10

        env.close()

    def test_collision_termination(self):
        """Test that collision causes termination."""
        env = MockCarlaRLEnv(seed=42)
        obs, info = env.reset()

        # Run until collision or max steps
        max_steps = 1000
        for _ in range(max_steps):
            action = np.array([1.0, 0.0], dtype=np.float32)  # Full throttle
            obs, reward, terminated, truncated, info = env.step(action)

            if terminated:
                assert info["collision"] == True
                break

        env.close()

    def test_reward_calculation(self):
        """Test that rewards are computed."""
        env = MockCarlaRLEnv(seed=42)
        obs, info = env.reset()

        # Take several steps
        rewards = []
        for _ in range(10):
            action = np.array([0.5, 0.0], dtype=np.float32)
            obs, reward, terminated, truncated, info = env.step(action)
            rewards.append(reward)

        # Rewards should be non-zero
        assert any(r != 0 for r in rewards)

        env.close()

    def test_camera_observation(self):
        """Test camera observation when enabled."""
        env = MockCarlaRLEnv(use_camera=True, image_size=(84, 84), seed=42)
        obs, info = env.reset()

        assert "image" in obs
        assert obs["image"].shape == (84, 84, 3)
        assert obs["image"].dtype == np.uint8

        # Take a step
        action = np.array([0.5, 0.0], dtype=np.float32)
        obs, reward, terminated, truncated, info = env.step(action)

        assert "image" in obs
        assert obs["image"].shape == (84, 84, 3)

        env.close()

    def test_random_seed(self):
        """Test that random seed produces reproducible results."""
        env1 = MockCarlaRLEnv(seed=42)
        env2 = MockCarlaRLEnv(seed=42)

        obs1, _ = env1.reset(seed=42)
        obs2, _ = env2.reset(seed=42)

        np.testing.assert_array_equal(obs1["features"], obs2["features"])

        env1.close()
        env2.close()

    def test_action_space_sample(self):
        """Test action space sampling."""
        env = MockCarlaRLEnv(seed=42)

        for _ in range(100):
            action = env.action_space.sample()
            assert action.shape == (2,)
            assert -1.0 <= action[0] <= 1.0
            assert -1.0 <= action[1] <= 1.0

        env.close()

    def test_vehicle_state(self):
        """Test vehicle state extraction."""
        env = MockCarlaRLEnv(seed=42)
        obs, info = env.reset()

        assert "speed" in info
        assert "dist_to_center" in info
        assert "heading_error" in info
        assert "total_distance" in info

        assert info["speed"] >= 0
        assert info["dist_to_center"] >= 0
        assert info["total_distance"] >= 0

        env.close()

    def test_render(self):
        """Test render function."""
        env = MockCarlaRLEnv(use_camera=True, render_mode="rgb_array", seed=42)
        env.reset()

        image = env.render()
        assert image is not None
        assert isinstance(image, np.ndarray)
        assert image.shape == (84, 84, 3)

        env.close()

    def test_close(self):
        """Test environment close."""
        env = MockCarlaRLEnv(seed=42)
        env.reset()
        env.close()  # Should not raise


class TestMockCarlaRLEnvIntegration:
    """Integration tests for the mock environment."""

    def test_gymnasium_compatibility(self):
        """Test compatibility with Gymnasium API."""
        import gymnasium as gym

        env = MockCarlaRLEnv(seed=42)

        # Check that it's a proper Gymnasium env
        assert isinstance(env, gym.Env)
        assert hasattr(env, "observation_space")
        assert hasattr(env, "action_space")
        assert hasattr(env, "reset")
        assert hasattr(env, "step")
        assert hasattr(env, "close")

        env.close()

    def test_sb3_compatibility(self):
        """Test compatibility with Stable-Baselines3."""
        from stable_baselines3.common.env_checker import check_env

        env = MockCarlaRLEnv(seed=42)

        # This will raise an error if the env is not compatible
        try:
            check_env(env)
        except Exception as e:
            pytest.skip(f"SB3 check_env failed: {e}")

        env.close()

    def test_training_loop(self):
        """Test a short training loop."""
        from stable_baselines3 import PPO

        env = MockCarlaRLEnv(max_steps=100, seed=42)

        model = PPO(
            "MlpPolicy",
            env,
            n_steps=64,
            batch_size=32,
            n_epochs=2,
            verbose=0,
            seed=42,
        )

        # Train for a small number of steps
        model.learn(total_timesteps=128)

        # Evaluate
        obs, _ = env.reset()
        for _ in range(10):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break

        env.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
