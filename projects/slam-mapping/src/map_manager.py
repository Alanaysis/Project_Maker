"""
Map management module for SLAM system.
Handles 3D map points and keyframe management.
"""

import numpy as np
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from .feature_extractor import Frame
from .pose_estimator import Pose


@dataclass
class MapPoint:
    """Represents a 3D point in the map."""
    id: int
    position: np.ndarray        # 3D position (3,)
    descriptor: np.ndarray      # ORB descriptor
    observations: Dict[int, int] = field(default_factory=dict)  # frame_id -> keypoint_idx
    normal: np.ndarray = field(default_factory=lambda: np.zeros(3))
    color: np.ndarray = field(default_factory=lambda: np.zeros(3))

    @property
    def num_observations(self) -> int:
        return len(self.observations)

    def add_observation(self, frame_id: int, keypoint_idx: int):
        """Add an observation of this point."""
        self.observations[frame_id] = keypoint_idx

    def remove_observation(self, frame_id: int):
        """Remove an observation of this point."""
        if frame_id in self.observations:
            del self.observations[frame_id]


@dataclass
class Keyframe:
    """Represents a keyframe in the map."""
    id: int
    frame: Frame
    pose: Pose
    timestamp: float = 0.0

    # Connected keyframes
    covisibility: Dict[int, int] = field(default_factory=dict)  # kf_id -> num_shared_points

    @property
    def position(self) -> np.ndarray:
        """Get camera position in world frame."""
        return -self.pose.rotation.T @ self.pose.translation

    def add_covisibility(self, kf_id: int, num_shared: int):
        """Add covisibility with another keyframe."""
        self.covisibility[kf_id] = num_shared

    def get_best_covisible_keyframes(self, n: int = 10) -> List[Tuple[int, int]]:
        """Get top N covisible keyframes."""
        sorted_kf = sorted(
            self.covisibility.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_kf[:n]


class MapManager:
    """Manages the 3D map of points and keyframes."""

    def __init__(self, max_keyframes: int = 1000):
        """
        Initialize map manager.

        Args:
            max_keyframes: Maximum number of keyframes to keep
        """
        self.max_keyframes = max_keyframes

        # Storage
        self.keyframes: Dict[int, Keyframe] = {}
        self.map_points: Dict[int, MapPoint] = {}

        # Counters
        self.keyframe_counter = 0
        self.map_point_counter = 0

        # Current state
        self.current_keyframe: Optional[Keyframe] = None

    def add_keyframe(self, frame: Frame, pose: Pose) -> Keyframe:
        """
        Add a new keyframe to the map.

        Args:
            frame: Frame data
            pose: Camera pose

        Returns:
            Created keyframe
        """
        keyframe = Keyframe(
            id=self.keyframe_counter,
            frame=frame,
            pose=pose,
            timestamp=frame.timestamp
        )

        self.keyframes[keyframe.id] = keyframe
        self.current_keyframe = keyframe
        self.keyframe_counter += 1

        # Remove old keyframes if necessary
        if len(self.keyframes) > self.max_keyframes:
            self._remove_old_keyframe()

        return keyframe

    def add_map_point(
        self,
        position: np.ndarray,
        descriptor: np.ndarray,
        frame_id: int,
        keypoint_idx: int,
        color: Optional[np.ndarray] = None
    ) -> MapPoint:
        """
        Add a new map point.

        Args:
            position: 3D position
            descriptor: ORB descriptor
            frame_id: Frame where point was observed
            keypoint_idx: Keypoint index in frame
            color: Optional RGB color

        Returns:
            Created map point
        """
        point = MapPoint(
            id=self.map_point_counter,
            position=position,
            descriptor=descriptor,
            color=color if color is not None else np.zeros(3)
        )

        point.add_observation(frame_id, keypoint_idx)
        self.map_points[point.id] = point
        self.map_point_counter += 1

        return point

    def get_map_points_in_frame(self, keyframe_id: int) -> List[MapPoint]:
        """Get all map points visible in a keyframe."""
        points = []
        for point in self.map_points.values():
            if keyframe_id in point.observations:
                points.append(point)
        return points

    def get_point_positions(self) -> np.ndarray:
        """Get all map point positions as array."""
        if not self.map_points:
            return np.array([])
        return np.array([p.position for p in self.map_points.values()])

    def get_point_colors(self) -> np.ndarray:
        """Get all map point colors as array."""
        if not self.map_points:
            return np.array([])
        return np.array([p.color for p in self.map_points.values()])

    def get_keyframe_poses(self) -> List[np.ndarray]:
        """Get all keyframe poses as list of 4x4 matrices."""
        return [kf.pose.transformation_matrix for kf in self.keyframes.values()]

    def get_keyframe_positions(self) -> np.ndarray:
        """Get all keyframe positions as array."""
        if not self.keyframes:
            return np.array([])
        return np.array([kf.position.flatten() for kf in self.keyframes.values()])

    def update_covisibility(self, keyframe: Keyframe):
        """
        Update covisibility graph for a keyframe.

        Args:
            keyframe: Keyframe to update covisibility for
        """
        # Get map points visible in this keyframe
        points = self.get_map_points_in_frame(keyframe.id)

        # Count shared points with other keyframes
        shared_counts: Dict[int, int] = defaultdict(int)
        for point in points:
            for kf_id in point.observations:
                if kf_id != keyframe.id:
                    shared_counts[kf_id] += 1

        # Update covisibility
        for kf_id, count in shared_counts.items():
            if count >= 10:  # Minimum shared points threshold
                keyframe.add_covisibility(kf_id, count)
                if kf_id in self.keyframes:
                    self.keyframes[kf_id].add_covisibility(keyframe.id, count)

    def _remove_old_keyframe(self):
        """Remove the oldest keyframe to stay within limits."""
        if len(self.keyframes) <= self.max_keyframes:
            return

        # Find keyframe with least covisibility
        min_covisibility = float('inf')
        kf_to_remove = None

        for kf in self.keyframes.values():
            if kf == self.current_keyframe:
                continue
            total_covisibility = sum(kf.covisibility.values())
            if total_covisibility < min_covisibility:
                min_covisibility = total_covisibility
                kf_to_remove = kf

        if kf_to_remove is not None:
            self._remove_keyframe(kf_to_remove.id)

    def _remove_keyframe(self, keyframe_id: int):
        """Remove a keyframe and its associated data."""
        if keyframe_id not in self.keyframes:
            return

        kf = self.keyframes[keyframe_id]

        # Remove observations from map points
        for point in self.map_points.values():
            point.remove_observation(keyframe_id)

        # Remove covisibility links
        for other_kf_id in kf.covisibility:
            if other_kf_id in self.keyframes:
                other_kf = self.keyframes[other_kf_id]
                if keyframe_id in other_kf.covisibility:
                    del other_kf.covisibility[keyframe_id]

        # Remove keyframe
        del self.keyframes[keyframe_id]

        # Clean up orphaned map points
        self._cleanup_orphaned_points()

    def _cleanup_orphaned_points(self):
        """Remove map points with no observations."""
        orphaned = [
            pid for pid, point in self.map_points.items()
            if point.num_observations == 0
        ]
        for pid in orphaned:
            del self.map_points[pid]

    def get_statistics(self) -> Dict:
        """Get map statistics."""
        return {
            'num_keyframes': len(self.keyframes),
            'num_map_points': len(self.map_points),
            'total_observations': sum(
                p.num_observations for p in self.map_points.values()
            ),
            'avg_observations_per_point': (
                sum(p.num_observations for p in self.map_points.values()) /
                len(self.map_points) if self.map_points else 0
            )
        }

    def clear(self):
        """Clear all map data."""
        self.keyframes.clear()
        self.map_points.clear()
        self.keyframe_counter = 0
        self.map_point_counter = 0
        self.current_keyframe = None
