"""
Observation Processing Utilities

Functions for processing and normalizing observations from CARLA
for use with reinforcement learning agents.
"""

import numpy as np
from typing import Dict, Tuple, Optional


class ObservationProcessor:
    """
    Processes raw CARLA observations into RL-ready format.

    Handles:
    - Vehicle state feature extraction and normalization
    - Camera image preprocessing
    - LiDAR point cloud processing (future)
    """

    def __init__(
        self,
        image_size: Tuple[int, int] = (84, 84),
        use_camera: bool = False,
        normalize_features: bool = True,
    ):
        """
        Initialize observation processor.

        Args:
            image_size: Target image dimensions (H, W)
            use_camera: Whether camera observations are used
            normalize_features: Whether to normalize feature vectors
        """
        self.image_size = image_size
        self.use_camera = use_camera
        self.normalize_features = normalize_features

        # Feature normalization parameters
        self.feature_means = {
            "speed": 30.0,  # km/h
            "steer": 0.0,
            "throttle": 0.0,
            "brake": 0.0,
            "dist_to_center": 0.0,
            "heading_error": 0.0,
        }
        self.feature_stds = {
            "speed": 20.0,
            "steer": 0.5,
            "throttle": 0.5,
            "brake": 0.5,
            "dist_to_center": 2.0,
            "heading_error": 0.5,
        }

        # Number of waypoints
        self.num_waypoints = 5

        # Calculate feature dimension
        # Basic features + waypoints (x, y each)
        self.feature_dim = len(self.feature_means) + self.num_waypoints * 2

    def process_features(
        self, vehicle_state: Dict[str, float]
    ) -> np.ndarray:
        """
        Process vehicle state into feature vector.

        Args:
            vehicle_state: Dictionary with vehicle state values

        Returns:
            Normalized feature vector as numpy array
        """
        features = []

        # Basic vehicle state
        for key in ["speed", "steer", "throttle", "brake", "dist_to_center", "heading_error"]:
            value = vehicle_state.get(key, 0.0)
            if self.normalize_features:
                mean = self.feature_means.get(key, 0.0)
                std = self.feature_stds.get(key, 1.0)
                value = (value - mean) / (std + 1e-8)
            features.append(value)

        # Waypoints
        waypoints = vehicle_state.get("waypoints", np.zeros(self.num_waypoints * 2))
        if self.normalize_features:
            waypoints = waypoints / 10.0  # Normalize by typical waypoint distance
        features.extend(waypoints.tolist())

        return np.array(features, dtype=np.float32)

    def process_image(self, carla_image) -> np.ndarray:
        """
        Process CARLA camera image.

        Args:
            carla_image: Raw CARLA image object or numpy array

        Returns:
            Processed image as numpy array (H, W, C) uint8
        """
        if isinstance(carla_image, np.ndarray):
            image = carla_image
        else:
            # CARLA image object
            image = np.frombuffer(carla_image.raw_data, dtype=np.uint8)
            image = image.reshape((carla_image.height, carla_image.width, 4))
            image = image[:, :, :3]  # Remove alpha channel

        # Resize if needed
        if image.shape[:2] != self.image_size:
            image = self._resize_image(image, self.image_size)

        return image

    def _resize_image(
        self, image: np.ndarray, target_size: Tuple[int, int]
    ) -> np.ndarray:
        """
        Resize image to target size using simple interpolation.

        Args:
            image: Input image (H, W, C)
            target_size: Target (H, W)

        Returns:
            Resized image
        """
        h, w = target_size
        src_h, src_w = image.shape[:2]

        # Simple nearest-neighbor interpolation
        row_indices = (np.arange(h) * src_h / h).astype(int)
        col_indices = (np.arange(w) * src_w / w).astype(int)

        return image[np.ix_(row_indices, col_indices)]

    def normalize_image(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize image to [0, 1] range.

        Args:
            image: Input image (uint8)

        Returns:
            Normalized image (float32)
        """
        return image.astype(np.float32) / 255.0

    def grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        Convert image to grayscale.

        Args:
            image: Input image (H, W, 3)

        Returns:
            Grayscale image (H, W, 1)
        """
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Standard grayscale conversion
            gray = np.dot(image[..., :3], [0.2989, 0.5870, 0.1140])
            return gray[:, :, np.newaxis].astype(np.uint8)
        return image

    def stack_frames(
        self, frames: list, num_stack: int = 4
    ) -> np.ndarray:
        """
        Stack multiple frames for temporal information.

        Args:
            frames: List of frames to stack
            num_stack: Number of frames to stack

        Returns:
            Stacked frames as single array
        """
        # Take last num_stack frames
        frames = frames[-num_stack:]

        # Pad with zeros if not enough frames
        while len(frames) < num_stack:
            frames.insert(0, np.zeros_like(frames[0]))

        return np.concatenate(frames, axis=-1)
