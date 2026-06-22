"""
Reward Calculation Utilities

Functions for computing rewards for autonomous driving tasks.
Implements multiple reward components that can be weighted.
"""

import numpy as np
from typing import Dict, Optional


class RewardCalculator:
    """
    Computes rewards for autonomous driving RL tasks.

    Reward components:
    - Progress: reward for moving forward
    - Speed tracking: penalty for deviating from target speed
    - Lane keeping: penalty for being off-center
    - Heading: penalty for wrong heading direction
    - Collision: large penalty for collisions
    - Time: small penalty per step to encourage efficiency
    """

    def __init__(
        self,
        target_speed: float = 30.0,
        weights: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize reward calculator.

        Args:
            target_speed: Target speed in km/h
            weights: Custom weights for reward components
        """
        self.target_speed = target_speed

        # Default weights
        self.weights = {
            "progress": 1.0,
            "speed": 0.5,
            "lane": 0.3,
            "heading": 0.2,
            "collision": -100.0,
            "time": -0.01,
            "comfort": 0.1,
        }

        # Update with custom weights
        if weights:
            self.weights.update(weights)

        # Previous state for computing deltas
        self.prev_speed = 0.0
        self.prev_steering = 0.0

    def compute(
        self,
        speed: float,
        dist_to_center: float,
        heading_error: float,
        collision: bool,
        lane_invasion: bool,
        step_count: int,
        progress: float = 0.0,
    ) -> float:
        """
        Compute total reward.

        Args:
            speed: Current speed in km/h
            dist_to_center: Distance to lane center in meters
            heading_error: Heading error in radians
            collision: Whether collision occurred
            lane_invasion: Whether lane invasion occurred
            step_count: Current step count
            progress: Forward progress in meters

        Returns:
            Total reward
        """
        reward = 0.0

        # Progress reward
        reward += self.weights["progress"] * self._progress_reward(progress)

        # Speed tracking reward
        reward += self.weights["speed"] * self._speed_reward(speed)

        # Lane keeping reward
        reward += self.weights["lane"] * self._lane_reward(dist_to_center)

        # Heading reward
        reward += self.weights["heading"] * self._heading_reward(heading_error)

        # Collision penalty (large negative)
        if collision:
            reward += self.weights["collision"]

        # Lane invasion penalty
        if lane_invasion:
            reward += -5.0

        # Time penalty (encourages efficiency)
        reward += self.weights["time"]

        # Comfort penalty (smooth driving)
        reward += self.weights["comfort"] * self._comfort_reward(speed)

        # Update previous state
        self.prev_speed = speed

        return float(reward)

    def _progress_reward(self, progress: float) -> float:
        """
        Reward for forward progress.

        Args:
            progress: Forward distance traveled in meters

        Returns:
            Progress reward
        """
        return progress

    def _speed_reward(self, speed: float) -> float:
        """
        Reward for maintaining target speed.

        Uses negative squared deviation from target speed.
        Penalizes both too slow and too fast.

        Args:
            speed: Current speed in km/h

        Returns:
            Speed reward
        """
        speed_error = speed - self.target_speed
        # Quadratic penalty with asymmetric weighting
        # Penalize overspeed more than underspeed
        if speed_error > 0:
            return -(speed_error / self.target_speed) ** 2 * 2.0
        else:
            return -(speed_error / self.target_speed) ** 2

    def _lane_reward(self, dist_to_center: float) -> float:
        """
        Reward for staying centered in lane.

        Args:
            dist_to_center: Distance to lane center in meters

        Returns:
            Lane keeping reward
        """
        # Quadratic penalty for being off-center
        max_dist = 4.0  # half lane width
        normalized_dist = min(dist_to_center / max_dist, 1.0)
        return -normalized_dist ** 2

    def _heading_reward(self, heading_error: float) -> float:
        """
        Reward for correct heading direction.

        Args:
            heading_error: Heading error in radians

        Returns:
            Heading reward
        """
        # Penalize heading error
        return -abs(heading_error) / np.pi

    def _comfort_reward(self, speed: float) -> float:
        """
        Penalty for uncomfortable driving (jerk, lateral acceleration).

        Args:
            speed: Current speed in km/h

        Returns:
            Comfort penalty (negative)
        """
        # Simple jerk approximation
        jerk = abs(speed - self.prev_speed) / 0.05  # assuming 0.05s time step
        return -jerk / 100.0  # normalize

    def reset(self):
        """Reset internal state."""
        self.prev_speed = 0.0
        self.prev_steering = 0.0


class ShapedRewardCalculator(RewardCalculator):
    """
    Enhanced reward calculator with potential-based shaping.

    Uses potential-based reward shaping to maintain optimal policy
    while providing denser reward signals.
    """

    def __init__(
        self,
        target_speed: float = 30.0,
        weights: Optional[Dict[str, float]] = None,
        gamma: float = 0.99,
    ):
        """
        Initialize shaped reward calculator.

        Args:
            target_speed: Target speed in km/h
            weights: Custom weights
            gamma: Discount factor for potential shaping
        """
        super().__init__(target_speed, weights)
        self.gamma = gamma
        self.prev_potential = 0.0

    def potential(self, state: Dict) -> float:
        """
        Compute potential function for state.

        Args:
            state: Dictionary with state information

        Returns:
            Potential value
        """
        speed = state.get("speed", 0.0)
        dist_to_center = state.get("dist_to_center", 0.0)
        heading_error = state.get("heading_error", 0.0)

        # Potential based on how "good" the state is
        speed_potential = -abs(speed - self.target_speed) / self.target_speed
        lane_potential = -dist_to_center / 4.0
        heading_potential = -abs(heading_error) / np.pi

        return speed_potential + lane_potential + heading_potential

    def compute(
        self,
        speed: float,
        dist_to_center: float,
        heading_error: float,
        collision: bool,
        lane_invasion: bool,
        step_count: int,
        progress: float = 0.0,
    ) -> float:
        """
        Compute shaped reward.

        Adds potential-based shaping to base reward.
        """
        # Base reward
        base_reward = super().compute(
            speed, dist_to_center, heading_error,
            collision, lane_invasion, step_count, progress
        )

        # Potential-based shaping
        current_potential = self.potential({
            "speed": speed,
            "dist_to_center": dist_to_center,
            "heading_error": heading_error,
        })

        shaping = self.gamma * current_potential - self.prev_potential
        self.prev_potential = current_potential

        return base_reward + shaping

    def reset(self):
        """Reset internal state."""
        super().reset()
        self.prev_potential = 0.0
