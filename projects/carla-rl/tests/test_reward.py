"""
Tests for RewardCalculator and ShapedRewardCalculator.
"""

import numpy as np
import pytest

from carla_rl.utils.reward import RewardCalculator, ShapedRewardCalculator


# ---------------------------------------------------------------------------
# RewardCalculator
# ---------------------------------------------------------------------------


class TestRewardCalculator:
    """Core reward computation tests."""

    def test_default_weights(self):
        calc = RewardCalculator()
        assert calc.weights["progress"] == 1.0
        assert calc.weights["speed"] == 0.5
        assert calc.weights["lane"] == 0.3
        assert calc.weights["heading"] == 0.2
        assert calc.weights["collision"] == -100.0
        assert calc.weights["time"] == -0.01
        assert calc.weights["comfort"] == 0.1

    def test_custom_weights_merge(self):
        calc = RewardCalculator(weights={"collision": -200.0, "speed": 1.0})
        assert calc.weights["collision"] == -200.0
        assert calc.weights["speed"] == 1.0
        # Unchanged defaults
        assert calc.weights["progress"] == 1.0

    def test_compute_returns_float(self, reward_calc):
        r = reward_calc.compute(
            speed=30.0,
            dist_to_center=0.0,
            heading_error=0.0,
            collision=False,
            lane_invasion=False,
            step_count=1,
        )
        assert isinstance(r, float)

    def test_compute_finite(self, reward_calc):
        r = reward_calc.compute(
            speed=0.0,
            dist_to_center=0.0,
            heading_error=0.0,
            collision=False,
            lane_invasion=False,
            step_count=1,
        )
        assert np.isfinite(r)


# ---------------------------------------------------------------------------
# Speed reward
# ---------------------------------------------------------------------------


class TestSpeedReward:
    """Speed tracking reward component."""

    def test_target_speed_best(self):
        calc = RewardCalculator(target_speed=30.0)
        r_target = calc._speed_reward(30.0)
        r_slow = calc._speed_reward(10.0)
        r_fast = calc._speed_reward(50.0)
        assert r_target > r_slow
        assert r_target > r_fast

    def test_target_speed_is_zero_penalty(self):
        calc = RewardCalculator(target_speed=30.0)
        assert calc._speed_reward(30.0) == pytest.approx(0.0)

    def test_overspeed_penalized_more_than_underspeed(self):
        """Overspeed penalty should be 2x underspeed (asymmetric)."""
        calc = RewardCalculator(target_speed=30.0)
        r_slow = calc._speed_reward(15.0)  # -15 error
        r_fast = calc._speed_reward(45.0)  # +15 error
        assert r_fast < r_slow  # more negative

    def test_zero_speed_penalty(self):
        calc = RewardCalculator(target_speed=30.0)
        r = calc._speed_reward(0.0)
        assert r < 0


# ---------------------------------------------------------------------------
# Lane reward
# ---------------------------------------------------------------------------


class TestLaneReward:
    """Lane keeping reward component."""

    def test_centered_best(self):
        calc = RewardCalculator()
        assert calc._lane_reward(0.0) == pytest.approx(0.0)

    def test_off_center_penalty(self):
        calc = RewardCalculator()
        assert calc._lane_reward(2.0) < 0

    def test_monotonic_penalty(self):
        calc = RewardCalculator()
        r1 = calc._lane_reward(1.0)
        r2 = calc._lane_reward(2.0)
        r3 = calc._lane_reward(3.0)
        assert r1 > r2 > r3

    def test_capped_at_max_dist(self):
        """Penalty should saturate at max_dist (4.0 m)."""
        calc = RewardCalculator()
        r_4 = calc._lane_reward(4.0)
        r_10 = calc._lane_reward(10.0)
        assert r_4 == pytest.approx(r_10)


# ---------------------------------------------------------------------------
# Heading reward
# ---------------------------------------------------------------------------


class TestHeadingReward:
    """Heading error reward component."""

    def test_zero_heading_best(self):
        calc = RewardCalculator()
        assert calc._heading_reward(0.0) == pytest.approx(0.0)

    def test_pi_heading_worst(self):
        calc = RewardCalculator()
        assert calc._heading_reward(np.pi) == pytest.approx(-1.0)

    def test_symmetric(self):
        calc = RewardCalculator()
        assert calc._heading_reward(0.5) == pytest.approx(calc._heading_reward(-0.5))


# ---------------------------------------------------------------------------
# Collision penalty
# ---------------------------------------------------------------------------


class TestCollisionPenalty:
    """Collision penalty tests."""

    def test_collision_large_penalty(self):
        calc = RewardCalculator()
        r_no = calc.compute(
            speed=30.0,
            dist_to_center=0.0,
            heading_error=0.0,
            collision=False,
            lane_invasion=False,
            step_count=1,
        )
        r_yes = calc.compute(
            speed=30.0,
            dist_to_center=0.0,
            heading_error=0.0,
            collision=True,
            lane_invasion=False,
            step_count=1,
        )
        assert r_yes < r_no
        # The difference should be at least the collision weight
        assert (r_no - r_yes) >= abs(calc.weights["collision"]) * 0.9

    def test_lane_invasion_penalty(self):
        calc = RewardCalculator()
        r_no = calc.compute(
            speed=30.0,
            dist_to_center=0.0,
            heading_error=0.0,
            collision=False,
            lane_invasion=False,
            step_count=1,
        )
        r_yes = calc.compute(
            speed=30.0,
            dist_to_center=0.0,
            heading_error=0.0,
            collision=False,
            lane_invasion=True,
            step_count=1,
        )
        assert r_yes < r_no


# ---------------------------------------------------------------------------
# Comfort reward
# ---------------------------------------------------------------------------


class TestComfortReward:
    """Comfort / smoothness penalty."""

    def test_no_jerk_at_constant_speed(self):
        calc = RewardCalculator()
        calc.prev_speed = 30.0
        r = calc._comfort_reward(30.0)
        assert r == pytest.approx(0.0)

    def test_jerk_penalty(self):
        calc = RewardCalculator()
        calc.prev_speed = 10.0
        r = calc._comfort_reward(30.0)
        assert r < 0


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


class TestRewardCalculatorReset:
    """Reset behaviour."""

    def test_reset_clears_state(self):
        calc = RewardCalculator()
        calc.prev_speed = 99.0
        calc.prev_steering = 0.5
        calc.reset()
        assert calc.prev_speed == 0.0
        assert calc.prev_steering == 0.0


# ---------------------------------------------------------------------------
# ShapedRewardCalculator
# ---------------------------------------------------------------------------


class TestShapedRewardCalculator:
    """Potential-based reward shaping tests."""

    def test_init_gamma(self):
        calc = ShapedRewardCalculator(gamma=0.95)
        assert calc.gamma == 0.95

    def test_potential_good_state_higher(self):
        calc = ShapedRewardCalculator()
        good = {"speed": 30.0, "dist_to_center": 0.0, "heading_error": 0.0}
        bad = {"speed": 5.0, "dist_to_center": 3.0, "heading_error": np.pi}
        assert calc.potential(good) > calc.potential(bad)

    def test_potential_range(self):
        """Potential should be negative (all terms are penalties)."""
        calc = ShapedRewardCalculator()
        state = {"speed": 30.0, "dist_to_center": 0.0, "heading_error": 0.0}
        assert calc.potential(state) <= 0.0

    def test_shaped_reward_includes_shaping(self):
        """Shaped reward should differ from base reward after first step."""
        calc = ShapedRewardCalculator(gamma=0.99)
        # First step (sets prev_potential)
        r1 = calc.compute(
            speed=30.0,
            dist_to_center=0.0,
            heading_error=0.0,
            collision=False,
            lane_invasion=False,
            step_count=1,
        )
        # Second step with different state
        r2 = calc.compute(
            speed=20.0,
            dist_to_center=1.0,
            heading_error=0.5,
            collision=False,
            lane_invasion=False,
            step_count=2,
        )
        assert isinstance(r1, float)
        assert isinstance(r2, float)

    def test_reset_clears_potential(self):
        calc = ShapedRewardCalculator()
        calc.prev_potential = 5.0
        calc.reset()
        assert calc.prev_potential == 0.0

    def test_inherits_from_reward_calculator(self):
        calc = ShapedRewardCalculator()
        assert isinstance(calc, RewardCalculator)
