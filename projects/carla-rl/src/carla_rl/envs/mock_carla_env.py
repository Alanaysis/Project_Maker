"""
Mock CARLA Environment for testing without CARLA simulator.

This environment simulates the CARLA interface using simple physics,
allowing development and testing without a running CARLA server.
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Optional, Dict, Any, Tuple

from carla_rl.utils.observation import ObservationProcessor
from carla_rl.utils.reward import RewardCalculator


class MockCarlaRLEnv(gym.Env):
    """
    Mock CARLA environment for testing and development.

    Simulates a simple 2D driving scenario with:
    - A road with lane markings
    - Vehicle physics (speed, steering)
    - Random obstacles
    - Lane keeping metrics
    """

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    def __init__(
        self,
        target_speed: float = 30.0,
        max_steps: int = 1000,
        road_width: float = 8.0,
        use_camera: bool = False,
        image_size: Tuple[int, int] = (84, 84),
        reward_weights: Optional[Dict[str, float]] = None,
        render_mode: Optional[str] = None,
        seed: Optional[int] = None,
    ):
        """
        Initialize the mock CARLA environment.

        Args:
            target_speed: Target speed in km/h
            max_steps: Maximum steps per episode
            road_width: Width of the road in meters
            use_camera: Whether to generate mock camera images
            image_size: Mock image dimensions (H, W)
            reward_weights: Weights for reward components
            render_mode: Rendering mode
            seed: Random seed
        """
        super().__init__()

        self.target_speed = target_speed
        self.max_steps = max_steps
        self.road_width = road_width
        self.use_camera = use_camera
        self.image_size = image_size
        self.render_mode = render_mode

        # Set seed
        self.np_random = np.random.default_rng(seed)

        # Initialize processors
        self.obs_processor = ObservationProcessor(
            image_size=image_size, use_camera=use_camera
        )
        self.reward_calculator = RewardCalculator(
            target_speed=target_speed,
            weights=reward_weights,
        )

        # Define action space: [throttle/brake, steer]
        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0], dtype=np.float32),
            high=np.array([1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )

        # Define observation space
        obs_spaces = {
            "features": spaces.Box(
                low=-np.inf,
                high=np.inf,
                shape=(self.obs_processor.feature_dim,),
                dtype=np.float32,
            ),
        }
        if use_camera:
            obs_spaces["image"] = spaces.Box(
                low=0,
                high=255,
                shape=(image_size[0], image_size[1], 3),
                dtype=np.uint8,
            )

        self.observation_space = spaces.Dict(obs_spaces)

        # Vehicle state
        self.x = 0.0  # lateral position
        self.y = 0.0  # longitudinal position
        self.speed = 0.0  # m/s
        self.heading = 0.0  # radians
        self.steer = 0.0

        # Episode state
        self.step_count = 0
        self.collision_detected = False
        self.prev_y = 0.0

        # Road features
        self.road_curvature = 0.0
        self.obstacles = []

        # Physics parameters
        self.dt = 0.05  # time step (same as CARLA)
        self.wheelbase = 2.5  # vehicle wheelbase in meters
        self.max_speed = 50.0 / 3.6  # max speed in m/s (50 km/h)
        self.acceleration = 5.0  # m/s^2
        self.deceleration = 8.0  # m/s^2

    def _update_road(self):
        """Update road curvature and obstacles."""
        # Simple sinusoidal road
        self.road_curvature = 0.001 * np.sin(0.01 * self.y)

        # Random obstacles
        if self.np_random.random() < 0.01:
            self.obstacles.append({
                "x": self.np_random.uniform(-self.road_width/2, self.road_width/2),
                "y": self.y + 50.0,
            })

        # Remove passed obstacles
        self.obstacles = [obs for obs in self.obstacles if obs["y"] > self.y - 10.0]

    def _check_collision(self) -> bool:
        """Check if vehicle collides with obstacles."""
        for obs in self.obstacles:
            dx = self.x - obs["x"]
            dy = self.y - obs["y"]
            dist = np.sqrt(dx**2 + dy**2)
            if dist < 2.0:  # collision radius
                return True
        return False

    def _get_vehicle_state(self) -> Dict[str, float]:
        """Get current vehicle state."""
        # Distance to lane center (center of road)
        dist_to_center = abs(self.x)

        # Heading error (relative to road direction)
        heading_error = self.heading - self.road_curvature

        # Speed in km/h
        speed_kmh = self.speed * 3.6

        # Generate waypoints
        waypoints = []
        for i in range(5):
            wp_y = self.y + (i + 1) * 5.0
            wp_x = 0.0  # road center
            # Transform to vehicle frame
            rel_y = wp_y - self.y
            rel_x = wp_x - self.x
            cos_h = np.cos(-self.heading)
            sin_h = np.sin(-self.heading)
            local_x = rel_x * cos_h - rel_y * sin_h
            local_y = rel_x * sin_h + rel_y * cos_h
            waypoints.extend([local_x, local_y])

        return {
            "speed": speed_kmh,
            "steer": self.steer,
            "throttle": max(0, self.speed / self.max_speed),
            "brake": max(0, -self.speed / self.max_speed),
            "dist_to_center": dist_to_center,
            "heading_error": heading_error,
            "waypoints": np.array(waypoints, dtype=np.float32),
        }

    def _get_obs(self) -> Dict[str, np.ndarray]:
        """Get current observation."""
        vehicle_state = self._get_vehicle_state()

        obs = {
            "features": self.obs_processor.process_features(vehicle_state),
        }

        if self.use_camera:
            # Generate mock camera image
            obs["image"] = self._generate_mock_image()

        return obs

    def _generate_mock_image(self) -> np.ndarray:
        """Generate a mock camera image for testing."""
        h, w = self.image_size
        image = np.zeros((h, w, 3), dtype=np.uint8)

        # Simple road representation
        road_center = w // 2 + int(self.x * 10)
        road_width_px = int(self.road_width * 10)

        # Road surface
        road_left = max(0, road_center - road_width_px // 2)
        road_right = min(w, road_center + road_width_px // 2)
        image[h//2:, road_left:road_right] = [100, 100, 100]  # gray road

        # Lane markings
        image[h//2:, road_center-1:road_center+1] = [255, 255, 255]  # white line

        # Obstacles
        for obs in self.obstacles:
            obs_x = int(w//2 + (obs["x"] - self.x) * 10)
            obs_y = int(h//2 - (obs["y"] - self.y) * 2)
            if 0 <= obs_x < w and 0 <= obs_y < h:
                image[max(0,obs_y-5):obs_y+5, max(0,obs_x-5):obs_x+5] = [255, 0, 0]

        return image

    def _get_info(self) -> Dict[str, Any]:
        """Get additional information."""
        vehicle_state = self._get_vehicle_state()
        return {
            "speed": vehicle_state["speed"],
            "dist_to_center": vehicle_state["dist_to_center"],
            "heading_error": vehicle_state["heading_error"],
            "collision": self.collision_detected,
            "lane_invasion": abs(self.x) > self.road_width / 2,
            "step_count": self.step_count,
            "total_distance": self.y,
            "x_position": self.x,
            "y_position": self.y,
        }

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """Reset the environment."""
        super().reset(seed=seed)

        if seed is not None:
            self.np_random = np.random.default_rng(seed)

        # Reset vehicle state
        self.x = self.np_random.uniform(-1.0, 1.0)
        self.y = 0.0
        self.speed = self.np_random.uniform(5.0, 15.0)  # initial speed m/s
        self.heading = 0.0
        self.steer = 0.0

        # Reset episode state
        self.step_count = 0
        self.collision_detected = False
        self.prev_y = 0.0

        # Reset road
        self.obstacles = []
        self._update_road()

        obs = self._get_obs()
        info = self._get_info()

        return obs, info

    def step(
        self, action: np.ndarray
    ) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        """Execute one step."""
        # Parse action
        throttle_brake = float(action[0])
        steer = float(action[1])

        # Update steering
        self.steer = np.clip(steer, -1.0, 1.0)

        # Update speed
        if throttle_brake >= 0:
            self.speed += throttle_brake * self.acceleration * self.dt
        else:
            self.speed += throttle_brake * self.deceleration * self.dt

        self.speed = np.clip(self.speed, 0.0, self.max_speed)

        # Update heading based on steering (bicycle model)
        if self.speed > 0.1:
            turning_radius = self.wheelbase / np.tan(self.steer + 1e-6)
            angular_velocity = self.speed / turning_radius
            self.heading += angular_velocity * self.dt

        # Update position
        self.prev_y = self.y
        self.x += self.speed * np.sin(self.heading) * self.dt
        self.y += self.speed * np.cos(self.heading) * self.dt

        # Update road and obstacles
        self._update_road()

        # Check collision
        self.collision_detected = self._check_collision()

        # Increment step counter
        self.step_count += 1

        # Get state and compute reward
        vehicle_state = self._get_vehicle_state()
        reward = self.reward_calculator.compute(
            speed=vehicle_state["speed"],
            dist_to_center=vehicle_state["dist_to_center"],
            heading_error=vehicle_state["heading_error"],
            collision=self.collision_detected,
            lane_invasion=abs(self.x) > self.road_width / 2,
            step_count=self.step_count,
        )

        # Check termination
        terminated = self.collision_detected
        truncated = self.step_count >= self.max_steps

        obs = self._get_obs()
        info = self._get_info()

        return obs, reward, terminated, truncated, info

    def render(self):
        """Render the environment."""
        if self.render_mode == "rgb_array" and self.use_camera:
            return self._generate_mock_image()
        return None

    def close(self):
        """Clean up resources."""
        pass
