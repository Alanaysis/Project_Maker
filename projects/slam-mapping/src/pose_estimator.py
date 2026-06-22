"""
Pose estimation module for SLAM system.
Handles camera pose estimation from feature matches.
"""

import numpy as np
import cv2
from typing import Tuple, Optional, List
from dataclasses import dataclass

from .config import CameraConfig


@dataclass
class Pose:
    """Represents a camera pose."""
    rotation: np.ndarray      # 3x3 rotation matrix
    translation: np.ndarray   # 3x1 translation vector
    inlier_mask: np.ndarray   # Inlier mask from estimation

    @property
    def transformation_matrix(self) -> np.ndarray:
        """Get 4x4 transformation matrix."""
        T = np.eye(4)
        T[:3, :3] = self.rotation
        T[:3, 3] = self.translation.flatten()
        return T

    @property
    def euler_angles(self) -> np.ndarray:
        """Get Euler angles (roll, pitch, yaw) in degrees."""
        R = self.rotation
        sy = np.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)
        singular = sy < 1e-6

        if not singular:
            x = np.arctan2(R[2, 1], R[2, 2])
            y = np.arctan2(-R[2, 0], sy)
            z = np.arctan2(R[1, 0], R[0, 0])
        else:
            x = np.arctan2(-R[1, 2], R[1, 1])
            y = np.arctan2(-R[2, 0], sy)
            z = 0

        return np.degrees(np.array([x, y, z]))

    def __str__(self) -> str:
        angles = self.euler_angles
        t = self.translation.flatten()
        return (
            f"Pose:\n"
            f"  Translation: [{t[0]:.3f}, {t[1]:.3f}, {t[2]:.3f}]\n"
            f"  Rotation (Euler): [{angles[0]:.1f}, {angles[1]:.1f}, {angles[2]:.1f}] deg"
        )


class PoseEstimator:
    """Camera pose estimation from 2D-2D or 2D-3D correspondences."""

    def __init__(self, camera_config: Optional[CameraConfig] = None):
        """
        Initialize pose estimator.

        Args:
            camera_config: Camera intrinsic parameters
        """
        self.config = camera_config or CameraConfig()
        self.K = self.config.intrinsic_matrix

    def estimate_pose_2d2d(
        self,
        points1: np.ndarray,
        points2: np.ndarray,
        method: int = cv2.RANSAC
    ) -> Optional[Pose]:
        """
        Estimate relative pose from 2D-2D correspondences using Essential matrix.

        Args:
            points1: Points in first image (N, 2)
            points2: Points in second image (N, 2)
            method: RANSAC method

        Returns:
            Estimated pose or None if estimation fails
        """
        if len(points1) < 8:
            return None

        # Find Essential matrix
        E, mask = cv2.findEssentialMat(
            points1, points2,
            self.K,
            method=method,
            prob=0.999,
            threshold=1.0
        )

        if E is None:
            return None

        # Recover pose from Essential matrix
        _, R, t, mask = cv2.recoverPose(E, points1, points2, self.K, mask)

        return Pose(
            rotation=R,
            translation=t,
            inlier_mask=mask.flatten()
        )

    def estimate_pose_pnp(
        self,
        points_3d: np.ndarray,
        points_2d: np.ndarray,
        use_extrinsic_guess: bool = False
    ) -> Optional[Pose]:
        """
        Estimate pose from 3D-2D correspondences using PnP.

        Args:
            points_3d: 3D points in world frame (N, 3)
            points_2d: 2D points in image (N, 2)
            use_extrinsic_guess: Whether to use initial guess

        Returns:
            Estimated pose or None if estimation fails
        """
        if len(points_3d) < 6:
            return None

        # Solve PnP
        success, rvec, tvec, inliers = cv2.solvePnPRansac(
            points_3d.astype(np.float64),
            points_2d.astype(np.float64),
            self.K,
            None,
            useExtrinsicGuess=use_extrinsic_guess,
            iterationsCount=100,
            reprojectionError=5.0,
            confidence=0.99
        )

        if not success or inliers is None:
            return None

        # Convert rotation vector to matrix
        R, _ = cv2.Rodrigues(rvec)

        # Create inlier mask
        mask = np.zeros(len(points_3d), dtype=bool)
        mask[inliers.flatten()] = True

        return Pose(
            rotation=R,
            translation=tvec,
            inlier_mask=mask
        )

    def triangulate_points(
        self,
        points1: np.ndarray,
        points2: np.ndarray,
        pose1: Pose,
        pose2: Pose
    ) -> np.ndarray:
        """
        Triangulate 3D points from two views.

        Args:
            points1: Points in first image (N, 2)
            points2: Points in second image (N, 2)
            pose1: First camera pose
            pose2: Second camera pose

        Returns:
            3D points (N, 3)
        """
        # Projection matrices
        P1 = self.K @ np.hstack([pose1.rotation, pose1.translation])
        P2 = self.K @ np.hstack([pose2.rotation, pose2.translation])

        # Triangulate
        points_4d = cv2.triangulatePoints(P1, P2, points1.T, points2.T)

        # Convert to 3D
        points_3d = (points_4d[:3] / points_4d[3]).T

        return points_3d

    def compute_reprojection_error(
        self,
        points_3d: np.ndarray,
        points_2d: np.ndarray,
        pose: Pose
    ) -> float:
        """
        Compute reprojection error.

        Args:
            points_3d: 3D points (N, 3)
            points_2d: 2D points (N, 2)
            pose: Camera pose

        Returns:
            Mean reprojection error
        """
        # Project 3D points to image
        rvec, _ = cv2.Rodrigues(pose.rotation)
        points_2d_proj, _ = cv2.projectPoints(
            points_3d,
            rvec,
            pose.translation,
            self.K,
            None
        )

        # Compute error
        error = np.linalg.norm(
            points_2d - points_2d_proj.squeeze(),
            axis=1
        )

        return np.mean(error)

    def decompose_essential_matrix(
        self,
        E: np.ndarray,
        points1: np.ndarray,
        points2: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Decompose Essential matrix into R and t.

        Args:
            E: Essential matrix
            points1: Points in first image
            points2: Points in second image

        Returns:
            Tuple of (R, t)
        """
        _, R, t, _ = cv2.recoverPose(E, points1, points2, self.K)
        return R, t
