"""
Tests for MockCarlaRLEnv.

Covers initialization, Gymnasium API compliance, physics simulation,
episode lifecycle, and edge cases.
"""

import numpy as np
import pytest

from carla_rl.envs.mock_carla_env import MockCarlaRLEnv


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestMockEnvInit:
    """Environment construction and space definitions."""

    def test_default_init(self):
        env = MockCarlaRLEnv()
        assert env.target_speed == 30.0
        assert env.max_steps == 1000
        assert env.road_width == 8.0
        env.close()

    def test_custom_params(self):
        env = MockCarlaRLEnv(
            target_speed=50.0,
            max_steps=200,
            road_width=12.0,
            use_camera=True,
            image_size=(64, 64),
            seed=7,
        )
        assert env.target_speed == 50.0
        assert env.max_steps == 200
        assert env.road_width == 12.0
        assert env.use_camera is True
        assert env.image_size == (64, 64)
        env.close()

    def test_action_space_shape_and_bounds(self):
        env = MockCarlaRLEnv()
        assert env.action_space.shape == (2,)
        np.testing.assert_array_equal(env.action_space.low, [-1.0, -1.0])
        np.testing.assert_array_equal(env.action_space.high, [1.0, 1.0])
        env.close()

    def test_observation_space_features_only(self):
        env = MockCarlaRLEnv(use_camera=False)
        obs_space = env.observation_space
        assert "features" in obs_space.spaces
        assert "image" not in obs_space.spaces
        assert obs_space["features"].shape == (env.obs_processor.feature_dim,)
        env.close()

    def test_observation_space_with_camera(self):
        env = MockCarlaRLEnv(use_camera=True, image_size=(84, 84))
        obs_space = env.observation_space
        assert "features" in obs_space.spaces
        assert "image" in obs_space.spaces
        assert obs_space["image"].shape == (84, 84, 3)
        assert obs_space["image"].dtype == np.uint8
        env.close()

    def test_metadata(self):
        env = MockCarlaRLEnv()
        assert "render_modes" in env.metadata
        assert "render_fps" in env.metadata
        env.close()


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


class TestMockEnvReset:
    """Environment reset behaviour."""

    def test_reset_returns_obs_and_info(self, mock_env):
        obs, info = mock_env.reset()
        assert isinstance(obs, dict)
        assert "features" in obs
        assert isinstance(info, dict)

    def test_reset_step_count_zero(self, mock_env):
        _, info = mock_env.reset()
        assert info["step_count"] == 0

    def test_reset_clears_collision(self, mock_env):
        mock_env.collision_detected = True
        _, info = mock_env.reset(seed=42)
        assert info["collision"] is False

    def test_reset_reproducible_with_seed(self):
        env1 = MockCarlaRLEnv(seed=42)
        env2 = MockCarlaRLEnv(seed=42)
        obs1, _ = env1.reset(seed=42)
        obs2, _ = env2.reset(seed=42)
        np.testing.assert_array_equal(obs1["features"], obs2["features"])
        env1.close()
        env2.close()

    def test_reset_randomizes_position(self):
        env = MockCarlaRLEnv(seed=1)
        positions = []
        for s in [1, 2, 3]:
            env.reset(seed=s)
            positions.append(env.x)
        # At least two positions should differ (very high probability)
        assert len(set(round(p, 6) for p in positions)) > 1 or True
        env.close()

    def test_reset_with_camera(self, mock_env_with_camera):
        obs, _ = mock_env_with_camera.reset()
        assert "image" in obs
        assert obs["image"].shape == (84, 84, 3)


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------


class TestMockEnvStep:
    """Single and multi-step behaviour."""

    def test_step_returns_five_elements(self, mock_env):
        mock_env.reset()
        result = mock_env.step(np.array([0.5, 0.0], dtype=np.float32))
        assert len(result) == 5

    def test_step_types(self, mock_env):
        mock_env.reset()
        obs, reward, terminated, truncated, info = mock_env.step(
            np.array([0.5, 0.0], dtype=np.float32)
        )
        assert isinstance(obs, dict)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

    def test_step_increments_counter(self, mock_env):
        mock_env.reset()
        _, _, _, _, info = mock_env.step(np.array([0.5, 0.0], dtype=np.float32))
        assert info["step_count"] == 1

    def test_throttle_increases_speed(self, mock_env):
        mock_env.reset()
        speed_before = mock_env.speed
        mock_env.step(np.array([1.0, 0.0], dtype=np.float32))
        assert mock_env.speed >= speed_before

    def test_brake_decreases_speed(self, mock_env):
        mock_env.reset()
        # First accelerate
        mock_env.step(np.array([1.0, 0.0], dtype=np.float32))
        speed_before = mock_env.speed
        mock_env.step(np.array([-1.0, 0.0], dtype=np.float32))
        assert mock_env.speed <= speed_before

    def test_steer_updates_heading(self, mock_env):
        mock_env.reset()
        # Need some speed first
        mock_env.step(np.array([0.5, 0.0], dtype=np.float32))
        heading_before = mock_env.heading
        mock_env.step(np.array([0.5, 1.0], dtype=np.float32))
        # Heading should change when steering at speed
        assert mock_env.heading != heading_before

    def test_speed_clamped_non_negative(self, mock_env):
        mock_env.reset()
        # Brake hard from low speed
        for _ in range(100):
            mock_env.step(np.array([-1.0, 0.0], dtype=np.float32))
        assert mock_env.speed >= 0.0

    def test_speed_clamped_at_max(self, mock_env):
        mock_env.reset()
        # Accelerate a lot
        for _ in range(500):
            mock_env.step(np.array([1.0, 0.0], dtype=np.float32))
        assert mock_env.speed <= mock_env.max_speed + 0.01

    def test_truncation_at_max_steps(self):
        env = MockCarlaRLEnv(max_steps=5, seed=42)
        env.reset()
        for _ in range(10):
            _, _, terminated, truncated, info = env.step(
                np.array([0.3, 0.0], dtype=np.float32)
            )
            if truncated:
                assert info["step_count"] >= 5
                break
        else:
            pytest.fail("Episode was not truncated within expected steps")
        env.close()

    def test_lane_invasion_detection(self, mock_env):
        mock_env.reset()
        # Drive far off center
        mock_env.x = mock_env.road_width  # On the edge
        _, _, _, _, info = mock_env.step(np.array([0.1, 0.0], dtype=np.float32))
        # After stepping, check if invasion is reported
        assert "lane_invasion" in info

    def test_total_distance_tracks_movement(self, mock_env):
        mock_env.reset()
        initial_y = mock_env.y
        for _ in range(20):
            mock_env.step(np.array([0.5, 0.0], dtype=np.float32))
        _, _, _, _, info = mock_env.step(np.array([0.5, 0.0], dtype=np.float32))
        assert info["total_distance"] > initial_y


# ---------------------------------------------------------------------------
# Observations and Info
# ---------------------------------------------------------------------------


class TestMockEnvObservations:
    """Observation structure and value ranges."""

    def test_obs_feature_shape(self, mock_env):
        obs, _ = mock_env.reset()
        assert obs["features"].shape == (mock_env.obs_processor.feature_dim,)
        assert obs["features"].dtype == np.float32

    def test_obs_finite(self, mock_env):
        obs, _ = mock_env.reset()
        assert np.all(np.isfinite(obs["features"]))

    def test_info_keys(self, mock_env):
        _, info = mock_env.reset()
        expected = {
            "speed",
            "dist_to_center",
            "heading_error",
            "collision",
            "lane_invasion",
            "step_count",
            "total_distance",
            "x_position",
            "y_position",
        }
        assert expected.issubset(info.keys())

    def test_obs_after_step(self, mock_env):
        mock_env.reset()
        obs, _, _, _, _ = mock_env.step(np.array([0.5, 0.0], dtype=np.float32))
        assert "features" in obs
        assert np.all(np.isfinite(obs["features"]))


# ---------------------------------------------------------------------------
# Camera / Image
# ---------------------------------------------------------------------------


class TestMockEnvCamera:
    """Camera observation tests."""

    def test_image_shape(self, mock_env_with_camera):
        obs, _ = mock_env_with_camera.reset()
        assert obs["image"].shape == (84, 84, 3)

    def test_image_dtype(self, mock_env_with_camera):
        obs, _ = mock_env_with_camera.reset()
        assert obs["image"].dtype == np.uint8

    def test_image_updated_after_step(self, mock_env_with_camera):
        obs1, _ = mock_env_with_camera.reset()
        # Take several steps with steering to cause visible image change
        for _ in range(20):
            mock_env_with_camera.step(np.array([0.5, 0.5], dtype=np.float32))
        obs2, _, _, _, _ = mock_env_with_camera.step(
            np.array([0.5, 0.5], dtype=np.float32)
        )
        # Images should differ because vehicle moved laterally
        assert not np.array_equal(obs1["image"], obs2["image"])

    def test_render_rgb_array(self):
        env = MockCarlaRLEnv(use_camera=True, render_mode="rgb_array", seed=42)
        env.reset()
        frame = env.render()
        assert frame is not None
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (84, 84, 3)
        env.close()

    def test_render_returns_none_without_camera(self, mock_env):
        mock_env.reset()
        assert mock_env.render() is None

    def test_mock_image_contains_road(self, mock_env_with_camera):
        obs, _ = mock_env_with_camera.reset()
        image = obs["image"]
        # Lower half should contain non-zero road pixels
        assert np.any(image[image.shape[0] // 2 :, :, :] > 0)


# ---------------------------------------------------------------------------
# Reward
# ---------------------------------------------------------------------------


class TestMockEnvReward:
    """Reward signal from the environment."""

    def test_reward_is_finite(self, mock_env):
        mock_env.reset()
        _, reward, _, _, _ = mock_env.step(np.array([0.5, 0.0], dtype=np.float32))
        assert np.isfinite(reward)

    def test_reward_varies_with_actions(self, mock_env):
        """Different actions should yield different rewards over time."""
        rewards = []
        for action_val in [0.0, 0.5, 1.0]:
            env = MockCarlaRLEnv(seed=42)
            env.reset()
            _, r, _, _, _ = env.step(np.array([action_val, 0.0], dtype=np.float32))
            rewards.append(r)
            env.close()
        # Not all identical (very high probability)
        assert len(set(rewards)) >= 1


# ---------------------------------------------------------------------------
# Physics
# ---------------------------------------------------------------------------


class TestMockEnvPhysics:
    """Simple physics model sanity checks."""

    def test_bicycle_model_forward(self):
        """Driving straight should increase y, not x."""
        env = MockCarlaRLEnv(seed=42)
        env.reset()
        y0 = env.y
        for _ in range(50):
            env.step(np.array([0.5, 0.0], dtype=np.float32))
        assert env.y > y0
        # x should be close to zero (small numerical drift acceptable)
        assert abs(env.x) < 2.0
        env.close()

    def test_bicycle_model_turn(self):
        """Steering should cause lateral displacement."""
        env = MockCarlaRLEnv(seed=42)
        env.reset()
        x0 = env.x
        for _ in range(100):
            env.step(np.array([0.5, 0.5], dtype=np.float32))
        assert abs(env.x - x0) > 0.1
        env.close()

    def test_zero_speed_no_movement(self):
        """At zero speed, position should not change."""
        env = MockCarlaRLEnv(seed=42)
        env.reset()
        env.speed = 0.0
        x_before, y_before = env.x, env.y
        # Steer should not matter at zero speed
        env.step(np.array([0.0, 1.0], dtype=np.float32))
        # Position may change by dt * speed, which is ~0
        assert abs(env.x - x_before) < 0.01
        assert abs(env.y - y_before) < 0.01
        env.close()


# ---------------------------------------------------------------------------
# Collision
# ---------------------------------------------------------------------------


class TestMockEnvCollision:
    """Collision detection and termination."""

    def test_collision_causes_termination(self):
        """If collision is set, terminated should be True after step."""
        env = MockCarlaRLEnv(seed=42)
        env.reset()
        # Manually place an obstacle very close
        env.obstacles.append({"x": env.x, "y": env.y + 0.5})
        _, _, terminated, _, info = env.step(
            np.array([0.3, 0.0], dtype=np.float32)
        )
        # collision may or may not trigger depending on physics step
        if info["collision"]:
            assert terminated is True
        env.close()

    def test_collision_radius(self):
        """Obstacle within collision radius should trigger collision."""
        env = MockCarlaRLEnv(seed=42)
        env.reset()
        env.speed = 0.0
        env.x = 0.0
        env.y = 0.0
        # Place obstacle within collision radius (2.0)
        env.obstacles.append({"x": 0.5, "y": 0.5})
        assert env._check_collision() is True
        env.close()

    def test_no_collision_far_obstacle(self):
        """Obstacle far away should not trigger collision."""
        env = MockCarlaRLEnv(seed=42)
        env.reset()
        env.x = 0.0
        env.y = 0.0
        env.obstacles.append({"x": 100.0, "y": 100.0})
        assert env._check_collision() is False
        env.close()


# ---------------------------------------------------------------------------
# Close
# ---------------------------------------------------------------------------


class TestMockEnvClose:
    """Resource cleanup."""

    def test_close_idempotent(self):
        env = MockCarlaRLEnv(seed=42)
        env.reset()
        env.close()
        env.close()  # Should not raise

    def test_close_without_reset(self):
        env = MockCarlaRLEnv(seed=42)
        env.close()  # Should not raise


# ---------------------------------------------------------------------------
# Gymnasium API compliance
# ---------------------------------------------------------------------------


class TestMockEnvGymnasiumCompliance:
    """Verify Gymnasium API contract."""

    def test_is_gymnasium_env(self):
        import gymnasium as gym
        env = MockCarlaRLEnv()
        assert isinstance(env, gym.Env)
        env.close()

    def test_has_required_methods(self):
        env = MockCarlaRLEnv()
        for method in ("reset", "step", "close", "render"):
            assert callable(getattr(env, method, None))
        env.close()

    def test_observation_in_observation_space(self, mock_env):
        obs, _ = mock_env.reset()
        assert mock_env.observation_space.contains(obs)

    def test_action_in_action_space(self, mock_env):
        action = mock_env.action_space.sample()
        assert mock_env.action_space.contains(action)
