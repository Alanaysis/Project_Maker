"""
CARLA Gymnasium Environment

A Gymnasium-compatible environment wrapping the CARLA simulator
for autonomous driving reinforcement learning.
"""

import time
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Optional, Dict, Any, Tuple, List

from carla_rl.utils.observation import ObservationProcessor
from carla_rl.utils.reward import RewardCalculator


class CarlaRLEnv(gym.Env):
    """
    Gymnasium environment for CARLA simulator.

    This environment wraps the CARLA simulator to provide a standard
    reinforcement learning interface for autonomous driving tasks.

    Action Space:
        - Continuous: [throttle/brake, steer]
          throttle/brake: [-1.0, 1.0] (positive = throttle, negative = brake)
          steer: [-1.0, 1.0]

    Observation Space:
        - Dict with:
            - 'features': vehicle state vector [speed, steer, dist_to_center, heading_error, ...]
            - 'image': optional camera image (84x84x3)
    """

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    def __init__(
        self,
        host: str = "localhost",
        port: int = 2000,
        town: str = "Town01",
        vehicle_model: str = "model3",
        target_speed: float = 30.0,
        max_steps: int = 1000,
        use_camera: bool = False,
        image_size: Tuple[int, int] = (84, 84),
        reward_weights: Optional[Dict[str, float]] = None,
        render_mode: Optional[str] = None,
        seed: Optional[int] = None,
    ):
        """
        Initialize the CARLA RL environment.

        Args:
            host: CARLA server hostname
            port: CARLA server port
            town: CARLA town/map to use
            vehicle_model: Vehicle blueprint to spawn
            target_speed: Target speed in km/h
            max_steps: Maximum steps per episode
            use_camera: Whether to include camera observations
            image_size: Camera image dimensions (H, W)
            reward_weights: Weights for reward components
            render_mode: Rendering mode ('human' or 'rgb_array')
            seed: Random seed
        """
        super().__init__()

        self.host = host
        self.port = port
        self.town = town
        self.vehicle_model = vehicle_model
        self.target_speed = target_speed
        self.max_steps = max_steps
        self.use_camera = use_camera
        self.image_size = image_size
        self.render_mode = render_mode

        # Set seed
        self.np_random = np.random.default_rng(seed)

        # CARLA objects (initialized in _connect)
        self.client = None
        self.world = None
        self.vehicle = None
        self.camera = None
        self.collision_sensor = None
        self.lane_invasion_sensor = None

        # Episode state
        self.step_count = 0
        self.collision_detected = False
        self.lane_invasion_detected = False
        self.prev_location = None
        self.total_distance = 0.0

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

        # Latest sensor data buffers
        self._latest_image = None
        self._latest_collision = None
        self._latest_lane_invasion = None

    def _connect(self):
        """Connect to CARLA server and setup world."""
        try:
            import carla
        except ImportError:
            raise ImportError(
                "CARLA Python API not found. Please install CARLA or use MockCarlaRLEnv for testing."
            )

        self.carla = carla
        self.client = carla.Client(self.host, self.port)
        self.client.set_timeout(30.0)

        # Load world
        self.world = self.client.load_world(self.town)

        # Setup synchronous mode
        settings = self.world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 0.05  # 20 FPS
        self.world.apply_settings(settings)

        # Get blueprint library
        self.blueprint_library = self.world.get_blueprint_library()
        self.map = self.world.get_map()

    def _spawn_vehicle(self):
        """Spawn the ego vehicle at a random spawn point."""
        vehicle_bp = self.blueprint_library.filter(self.vehicle_model)[0]
        spawn_points = self.map.get_spawn_points()
        spawn_point = self.np_random.choice(spawn_points)

        self.vehicle = self.world.spawn_actor(vehicle_bp, spawn_point)
        if self.vehicle is None:
            raise RuntimeError("Failed to spawn vehicle")

        # Wait for vehicle to be ready
        self.world.tick()

    def _setup_sensors(self):
        """Attach sensors to the vehicle."""
        # Collision sensor
        collision_bp = self.blueprint_library.find("sensor.other.collision")
        self.collision_sensor = self.world.spawn_actor(
            collision_bp,
            self.carla.Transform(),
            attach_to=self.vehicle,
        )
        self.collision_sensor.listen(lambda event: self._on_collision(event))

        # Lane invasion sensor
        lane_bp = self.blueprint_library.find("sensor.other.lane_invasion")
        self.lane_invasion_sensor = self.world.spawn_actor(
            lane_bp,
            self.carla.Transform(),
            attach_to=self.vehicle,
        )
        self.lane_invasion_sensor.listen(lambda event: self._on_lane_invasion(event))

        # Camera sensor (optional)
        if self.use_camera:
            camera_bp = self.blueprint_library.find("sensor.camera.rgb")
            camera_bp.set_attribute("image_size_x", str(self.image_size[1]))
            camera_bp.set_attribute("image_size_y", str(self.image_size[0]))
            camera_bp.set_attribute("sensor_tick", "0.05")

            camera_transform = self.carla.Transform(
                self.carla.Location(x=1.5, z=2.4)
            )
            self.camera = self.world.spawn_actor(
                camera_bp, camera_transform, attach_to=self.vehicle
            )
            self.camera.listen(lambda image: self._on_camera(image))

        # Tick to register sensors
        self.world.tick()

    def _on_collision(self, event):
        """Collision sensor callback."""
        self._latest_collision = event
        self.collision_detected = True

    def _on_lane_invasion(self, event):
        """Lane invasion sensor callback."""
        self._latest_lane_invasion = event
        self.lane_invasion_detected = True

    def _on_camera(self, image):
        """Camera sensor callback."""
        self._latest_image = image

    def _get_vehicle_state(self) -> Dict[str, float]:
        """Get current vehicle state from CARLA."""
        transform = self.vehicle.get_transform()
        velocity = self.vehicle.get_velocity()
        control = self.vehicle.get_control()

        # Calculate speed in km/h
        speed = 3.6 * np.sqrt(
            velocity.x**2 + velocity.y**2 + velocity.z**2
        )

        # Get waypoint information
        waypoint = self.map.get_waypoint(transform.location)

        # Calculate distance to lane center
        lane_center = waypoint.transform.location
        dist_to_center = np.sqrt(
            (transform.location.x - lane_center.x) ** 2
            + (transform.location.y - lane_center.y) ** 2
        )

        # Calculate heading error
        vehicle_yaw = np.radians(transform.rotation.yaw)
        lane_yaw = np.radians(waypoint.transform.rotation.yaw)
        heading_error = np.arctan2(
            np.sin(vehicle_yaw - lane_yaw),
            np.cos(vehicle_yaw - lane_yaw),
        )

        # Get next waypoints for navigation
        next_waypoints = []
        current_wp = waypoint
        for _ in range(5):
            next_wps = current_wp.next(2.0)
            if next_wps:
                current_wp = next_wps[0]
                # Transform to vehicle-relative coordinates
                rel_x = current_wp.transform.location.x - transform.location.x
                rel_y = current_wp.transform.location.y - transform.location.y
                # Rotate to vehicle frame
                cos_yaw = np.cos(-vehicle_yaw)
                sin_yaw = np.sin(-vehicle_yaw)
                local_x = rel_x * cos_yaw - rel_y * sin_yaw
                local_y = rel_x * sin_yaw + rel_y * cos_yaw
                next_waypoints.extend([local_x, local_y])
            else:
                next_waypoints.extend([0.0, 0.0])

        return {
            "speed": speed,
            "steer": control.steer,
            "throttle": control.throttle,
            "brake": control.brake,
            "dist_to_center": dist_to_center,
            "heading_error": heading_error,
            "waypoints": np.array(next_waypoints, dtype=np.float32),
        }

    def _compute_reward(self, vehicle_state: Dict[str, float]) -> float:
        """Compute reward based on current state."""
        return self.reward_calculator.compute(
            speed=vehicle_state["speed"],
            dist_to_center=vehicle_state["dist_to_center"],
            heading_error=vehicle_state["heading_error"],
            collision=self.collision_detected,
            lane_invasion=self.lane_invasion_detected,
            step_count=self.step_count,
        )

    def _is_done(self) -> Tuple[bool, bool]:
        """Check if episode is terminated or truncated."""
        terminated = False
        truncated = False

        # Terminated conditions
        if self.collision_detected:
            terminated = True

        # Truncated conditions
        if self.step_count >= self.max_steps:
            truncated = True

        return terminated, truncated

    def _get_obs(self) -> Dict[str, np.ndarray]:
        """Get current observation."""
        vehicle_state = self._get_vehicle_state()

        obs = {
            "features": self.obs_processor.process_features(vehicle_state),
        }

        if self.use_camera and self._latest_image is not None:
            obs["image"] = self.obs_processor.process_image(self._latest_image)

        return obs

    def _get_info(self) -> Dict[str, Any]:
        """Get additional information."""
        vehicle_state = self._get_vehicle_state()
        return {
            "speed": vehicle_state["speed"],
            "dist_to_center": vehicle_state["dist_to_center"],
            "heading_error": vehicle_state["heading_error"],
            "collision": self.collision_detected,
            "lane_invasion": self.lane_invasion_detected,
            "step_count": self.step_count,
            "total_distance": self.total_distance,
        }

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """
        Reset the environment.

        Returns:
            observation: Initial observation
            info: Additional information
        """
        super().reset(seed=seed)

        if seed is not None:
            self.np_random = np.random.default_rng(seed)

        # Clean up existing actors
        self._cleanup()

        # Connect to CARLA if not already connected
        if self.client is None:
            self._connect()

        # Spawn vehicle and sensors
        self._spawn_vehicle()
        self._setup_sensors()

        # Reset episode state
        self.step_count = 0
        self.collision_detected = False
        self.lane_invasion_detected = False
        self.prev_location = self.vehicle.get_transform().location
        self.total_distance = 0.0

        # Apply initial control
        self.vehicle.apply_control(
            self.carla.VehicleControl(throttle=0.0, steer=0.0)
        )
        self.world.tick()

        obs = self._get_obs()
        info = self._get_info()

        return obs, info

    def step(
        self, action: np.ndarray
    ) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.

        Args:
            action: [throttle/brake, steer]

        Returns:
            observation: Next observation
            reward: Reward for this step
            terminated: Whether episode ended naturally
            truncated: Whether episode was truncated
            info: Additional information
        """
        # Parse action
        throttle_brake = float(action[0])
        steer = float(action[1])

        # Apply control
        if throttle_brake >= 0:
            control = self.carla.VehicleControl(
                throttle=throttle_brake, steer=steer
            )
        else:
            control = self.carla.VehicleControl(
                brake=-throttle_brake, steer=steer
            )

        self.vehicle.apply_control(control)

        # Tick simulation
        self.world.tick()
        self.step_count += 1

        # Update distance
        current_location = self.vehicle.get_transform().location
        if self.prev_location is not None:
            dx = current_location.x - self.prev_location.x
            dy = current_location.y - self.prev_location.y
            self.total_distance += np.sqrt(dx**2 + dy**2)
        self.prev_location = current_location

        # Get state
        vehicle_state = self._get_vehicle_state()

        # Compute reward
        reward = self._compute_reward(vehicle_state)

        # Check termination
        terminated, truncated = self._is_done()

        # Get observation and info
        obs = self._get_obs()
        info = self._get_info()

        return obs, reward, terminated, truncated, info

    def render(self):
        """Render the environment."""
        if self.render_mode == "rgb_array" and self._latest_image is not None:
            # Convert CARLA image to numpy array
            image = np.frombuffer(self._latest_image.raw_data, dtype=np.uint8)
            image = image.reshape(
                (self._latest_image.height, self._latest_image.width, 4)
            )
            return image[:, :, :3]  # Remove alpha channel
        return None

    def close(self):
        """Clean up resources."""
        self._cleanup()

    def _cleanup(self):
        """Destroy all spawned actors."""
        if self.camera is not None:
            self.camera.destroy()
            self.camera = None

        if self.collision_sensor is not None:
            self.collision_sensor.destroy()
            self.collision_sensor = None

        if self.lane_invasion_sensor is not None:
            self.lane_invasion_sensor.destroy()
            self.lane_invasion_sensor = None

        if self.vehicle is not None:
            self.vehicle.destroy()
            self.vehicle = None
