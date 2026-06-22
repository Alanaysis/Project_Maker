"""
Main SLAM system module.
Implements the complete SLAM pipeline.
"""

import numpy as np
import cv2
from typing import Optional, List, Tuple, Dict
from pathlib import Path

from .config import SLAMConfig, DEFAULT_CONFIG
from .feature_extractor import FeatureExtractor, Frame
from .pose_estimator import PoseEstimator, Pose
from .map_manager import MapManager, Keyframe, MapPoint
from .loop_closure import LoopDetector
from .visualizer import Visualizer


class SLAMSystem:
    """Complete SLAM system implementation."""

    def __init__(self, config: Optional[SLAMConfig] = None):
        """
        Initialize SLAM system.

        Args:
            config: SLAM configuration (uses default if None)
        """
        self.config = config or DEFAULT_CONFIG

        # Initialize components
        self.feature_extractor = FeatureExtractor(self.config.features)
        self.pose_estimator = PoseEstimator(self.config.camera)
        self.map_manager = MapManager(self.config.max_keyframes)
        self.loop_detector = LoopDetector(
            self.feature_extractor,
            min_interval=self.config.loop_closure_interval
        )
        self.visualizer = Visualizer()

        # State tracking
        self.is_initialized = False
        self.current_frame: Optional[Frame] = None
        self.previous_frame: Optional[Frame] = None
        self.current_pose: Optional[Pose] = None
        self.trajectory: List[np.ndarray] = []

        # Frame counter
        self.frame_count = 0

    def initialize(self, first_image: np.ndarray) -> bool:
        """
        Initialize SLAM system with first frame.

        Args:
            first_image: First camera image

        Returns:
            True if initialization successful
        """
        # Extract features from first frame
        first_frame = self.feature_extractor.extract(first_image, timestamp=0)

        if first_frame.num_features < 50:
            print("Error: Not enough features in first frame")
            return False

        # Initialize pose at origin
        initial_pose = Pose(
            rotation=np.eye(3),
            translation=np.zeros(3),
            inlier_mask=np.ones(1)
        )

        # Create first keyframe
        keyframe = self.map_manager.add_keyframe(first_frame, initial_pose)

        # Store first frame descriptors for loop detection
        self.loop_detector.add_keyframe_descriptors(
            keyframe.id, first_frame.descriptors
        )

        # Update state
        self.current_frame = first_frame
        self.current_pose = initial_pose
        self.trajectory.append(np.zeros(3))
        self.is_initialized = True

        print(f"SLAM initialized with {first_frame.num_features} features")
        return True

    def process_frame(self, image: np.ndarray, timestamp: float = 0.0) -> bool:
        """
        Process a new frame through the SLAM pipeline.

        Args:
            image: Camera image (BGR)
            timestamp: Frame timestamp

        Returns:
            True if frame processed successfully
        """
        if not self.is_initialized:
            return self.initialize(image)

        # Extract features
        frame = self.feature_extractor.extract(image, timestamp)
        if frame.num_features < 20:
            print(f"Warning: Only {frame.num_features} features detected")
            return False

        # Track features (visual odometry)
        success, pose = self._track_features(frame)
        if not success:
            print("Warning: Feature tracking failed")
            return False

        # Update current pose
        self.current_pose = pose
        self.previous_frame = self.current_frame
        self.current_frame = frame

        # Update trajectory
        position = -pose.rotation.T @ pose.translation
        self.trajectory.append(position.flatten()[:3])

        # Check if new keyframe is needed
        if self._need_new_keyframe(frame, pose):
            self._create_keyframe(frame, pose)

        # Check for loop closure
        if self.config.loop_closure_enabled:
            self._check_loop_closure()

        self.frame_count += 1
        return True

    def _track_features(self, frame: Frame) -> Tuple[bool, Optional[Pose]]:
        """
        Track features between current and previous frame.

        Args:
            frame: Current frame

        Returns:
            Tuple of (success, pose)
        """
        # Match features with previous frame
        matches, points_prev, points_curr = self.feature_extractor.match_frames(
            self.current_frame, frame
        )

        if len(matches) < self.config.features.min_matches:
            return False, None

        # Estimate pose using 2D-2D correspondences
        pose = self.pose_estimator.estimate_pose_2d2d(points_prev, points_curr)

        if pose is None:
            return False, None

        # Combine with previous pose
        if self.current_pose is not None:
            # Relative pose
            R_rel = pose.rotation
            t_rel = pose.translation

            # Absolute pose
            R_abs = R_rel @ self.current_pose.rotation
            t_abs = R_rel @ self.current_pose.translation + t_rel

            pose = Pose(
                rotation=R_abs,
                translation=t_abs,
                inlier_mask=pose.inlier_mask
            )

        return True, pose

    def _need_new_keyframe(self, frame: Frame, pose: Pose) -> bool:
        """
        Determine if a new keyframe is needed.

        Args:
            frame: Current frame
            pose: Current pose

        Returns:
            True if new keyframe needed
        """
        # Check frame interval
        if self.frame_count % self.config.keyframe_interval != 0:
            return False

        # Check translation
        if self.current_pose is not None:
            translation = np.linalg.norm(
                pose.translation - self.current_pose.translation
            )
            if translation < self.config.min_translation:
                return False

        # Check number of tracked features
        if frame.num_features < 50:
            return True

        return True

    def _create_keyframe(self, frame: Frame, pose: Pose):
        """
        Create a new keyframe and update map.

        Args:
            frame: Current frame
            pose: Current pose
        """
        # Add keyframe to map
        keyframe = self.map_manager.add_keyframe(frame, pose)

        # Store descriptors for loop detection
        self.loop_detector.add_keyframe_descriptors(
            keyframe.id, frame.descriptors
        )

        # Triangulate new map points
        if self.previous_frame is not None:
            self._triangulate_new_points(frame, pose)

        # Update covisibility
        self.map_manager.update_covisibility(keyframe)

        print(f"Created keyframe {keyframe.id} with {frame.num_features} features")

    def _triangulate_new_points(self, frame: Frame, pose: Pose):
        """
        Triangulate new 3D map points.

        Args:
            frame: Current frame
            pose: Current pose
        """
        if self.previous_frame is None or self.current_pose is None:
            return

        # Match features
        matches, points_prev, points_curr = self.feature_extractor.match_frames(
            self.previous_frame, frame
        )

        if len(matches) < 5:
            return

        # Get previous pose
        prev_pose = self.current_pose

        # Triangulate
        points_3d = self.pose_estimator.triangulate_points(
            points_prev, points_curr, prev_pose, pose
        )

        # Filter points by depth
        valid_points = []
        for i, point in enumerate(points_3d):
            # Check if point is in front of camera
            point_cam = pose.rotation @ point + pose.translation.flatten()
            depth = point_cam[2]

            if self.config.min_depth < depth < self.config.max_depth:
                # Get color from image
                x, y = int(points_curr[i][0]), int(points_curr[i][1])
                if 0 <= x < frame.image.shape[1] and 0 <= y < frame.image.shape[0]:
                    color = frame.image[y, x] / 255.0
                    if len(color.shape) == 0:
                        color = np.array([color, color, color])
                else:
                    color = np.zeros(3)

                # Add map point
                match = matches[i]
                self.map_manager.add_map_point(
                    position=point,
                    descriptor=frame.descriptors[match.trainIdx],
                    frame_id=frame.id,
                    keypoint_idx=match.trainIdx,
                    color=color
                )

    def _check_loop_closure(self):
        """Check for loop closure with previous keyframes."""
        if self.map_manager.current_keyframe is None:
            return

        result = self.loop_detector.detect_loop(
            self.map_manager.current_keyframe,
            self.map_manager.keyframes
        )

        if result is not None:
            loop_kf_id, similarity = result
            print(f"Loop closure detected with keyframe {loop_kf_id} "
                  f"(similarity: {similarity:.2f})")

            # Compute loop constraint
            loop_kf = self.map_manager.keyframes[loop_kf_id]
            constraint = self.loop_detector.compute_loop_constraint(
                self.map_manager.current_keyframe,
                loop_kf,
                self.config.camera.intrinsic_matrix
            )

            if constraint is not None:
                R_loop, t_loop = constraint
                print(f"Loop constraint computed successfully")

    def get_map_points(self) -> np.ndarray:
        """Get all map points as array."""
        return self.map_manager.get_point_positions()

    def get_map_colors(self) -> np.ndarray:
        """Get all map point colors as array."""
        return self.map_manager.get_point_colors()

    def get_trajectory(self) -> np.ndarray:
        """Get camera trajectory as array."""
        if not self.trajectory:
            return np.array([])
        # Ensure consistent shape (N, 3)
        trajectory = np.array(self.trajectory)
        if trajectory.ndim == 1:
            trajectory = trajectory.reshape(1, -1)
        return trajectory

    def get_keyframe_poses(self) -> List[np.ndarray]:
        """Get all keyframe poses."""
        return self.map_manager.get_keyframe_poses()

    def get_statistics(self) -> Dict:
        """Get SLAM system statistics."""
        stats = self.map_manager.get_statistics()
        stats['frames_processed'] = self.frame_count
        stats['is_initialized'] = self.is_initialized
        return stats

    def visualize(self, show_cameras: bool = True):
        """
        Visualize the current map.

        Args:
            show_cameras: Whether to show camera frustums
        """
        points = self.get_map_points()
        colors = self.get_map_colors()
        trajectory = self.get_trajectory()
        poses = self.get_keyframe_poses()

        self.visualizer.visualize_map(
            points=points,
            colors=colors,
            trajectory=trajectory,
            camera_poses=poses,
            show_cameras=show_cameras
        )

    def save_map(self, filepath: str):
        """
        Save the map to file.

        Args:
            filepath: Output file path (ply format)
        """
        points = self.get_map_points()
        colors = self.get_map_colors()

        if len(points) > 0:
            self.visualizer.save_point_cloud(points, colors, filepath)
        else:
            print("Warning: No map points to save")

    def reset(self):
        """Reset the SLAM system."""
        self.map_manager.clear()
        self.loop_detector.clear()
        self.is_initialized = False
        self.current_frame = None
        self.previous_frame = None
        self.current_pose = None
        self.trajectory.clear()
        self.frame_count = 0

    def process_video(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        max_frames: Optional[int] = None
    ):
        """
        Process a video file.

        Args:
            video_path: Path to video file
            output_path: Path to save output visualization
            max_frames: Maximum number of frames to process
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return

        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if max_frames and frame_count >= max_frames:
                break

            # Process frame
            success = self.process_frame(frame, timestamp=frame_count / 30.0)

            if not success:
                print(f"Warning: Failed to process frame {frame_count}")

            frame_count += 1

            # Print progress
            if frame_count % 10 == 0:
                stats = self.get_statistics()
                print(f"Processed {frame_count} frames, "
                      f"{stats['num_map_points']} map points")

        cap.release()

        print(f"\nProcessing complete:")
        print(f"  Frames processed: {frame_count}")
        print(f"  Keyframes: {self.map_manager.get_statistics()['num_keyframes']}")
        print(f"  Map points: {self.map_manager.get_statistics()['num_map_points']}")

        if output_path:
            self.save_map(output_path)

    def process_image_sequence(
        self,
        image_dir: str,
        output_path: Optional[str] = None,
        max_frames: Optional[int] = None
    ):
        """
        Process a sequence of images.

        Args:
            image_dir: Directory containing images
            output_path: Path to save output
            max_frames: Maximum number of frames
        """
        image_dir = Path(image_dir)
        image_files = sorted(image_dir.glob('*.png')) + sorted(image_dir.glob('*.jpg'))

        if not image_files:
            print(f"Error: No images found in {image_dir}")
            return

        print(f"Processing {len(image_files)} images...")

        for i, image_file in enumerate(image_files):
            if max_frames and i >= max_frames:
                break

            # Read image
            image = cv2.imread(str(image_file))
            if image is None:
                print(f"Warning: Could not read {image_file}")
                continue

            # Process frame
            success = self.process_frame(image, timestamp=i / 30.0)

            if not success:
                print(f"Warning: Failed to process {image_file}")

            # Print progress
            if (i + 1) % 10 == 0:
                stats = self.get_statistics()
                print(f"Processed {i + 1}/{len(image_files)} images, "
                      f"{stats['num_map_points']} map points")

        print(f"\nProcessing complete:")
        stats = self.get_statistics()
        print(f"  Frames processed: {stats['frames_processed']}")
        print(f"  Keyframes: {stats['num_keyframes']}")
        print(f"  Map points: {stats['num_map_points']}")

        if output_path:
            self.save_map(output_path)
