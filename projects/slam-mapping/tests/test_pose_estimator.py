"""
Tests for pose estimation module.
"""

import pytest
import numpy as np
import cv2
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pose_estimator import PoseEstimator, Pose
from src.config import CameraConfig


@pytest.fixture
def camera_config():
    """Create camera configuration."""
    return CameraConfig(
        fx=525.0,
        fy=525.0,
        cx=319.5,
        cy=239.5
    )


@pytest.fixture
def pose_estimator(camera_config):
    """Create pose estimator instance."""
    return PoseEstimator(camera_config)


@pytest.fixture
def sample_points():
    """Create sample 2D points."""
    points1 = np.array([
        [100, 100],
        [200, 150],
        [300, 200],
        [400, 250],
        [150, 300],
        [250, 350],
        [350, 400],
        [450, 100]
    ], dtype=np.float32)

    # Slightly shifted points (simulating camera motion)
    points2 = points1 + np.random.randn(8, 2) * 2

    return points1, points2


class TestPose:
    """Test cases for Pose dataclass."""

    def test_pose_creation(self):
        """Test pose creation."""
        R = np.eye(3)
        t = np.zeros(3)
        mask = np.ones(10)

        pose = Pose(rotation=R, translation=t, inlier_mask=mask)

        assert np.array_equal(pose.rotation, R)
        assert np.array_equal(pose.translation, t)
        assert np.array_equal(pose.inlier_mask, mask)

    def test_transformation_matrix(self):
        """Test transformation matrix property."""
        R = np.eye(3)
        t = np.array([1, 2, 3])
        pose = Pose(rotation=R, translation=t, inlier_mask=np.ones(1))

        T = pose.transformation_matrix

        assert T.shape == (4, 4)
        assert np.array_equal(T[:3, :3], R)
        assert np.array_equal(T[:3, 3], t)
        assert T[3, 3] == 1.0

    def test_euler_angles(self):
        """Test Euler angles computation."""
        # Identity rotation should give zero angles
        pose = Pose(
            rotation=np.eye(3),
            translation=np.zeros(3),
            inlier_mask=np.ones(1)
        )

        angles = pose.euler_angles
        assert np.allclose(angles, 0, atol=1e-10)

    def test_str_representation(self):
        """Test string representation."""
        pose = Pose(
            rotation=np.eye(3),
            translation=np.array([1, 2, 3]),
            inlier_mask=np.ones(1)
        )

        str_repr = str(pose)
        assert 'Pose' in str_repr
        assert '1.000' in str_repr


class TestPoseEstimator:
    """Test cases for PoseEstimator."""

    def test_initialization(self, pose_estimator, camera_config):
        """Test pose estimator initialization."""
        assert pose_estimator.K.shape == (3, 3)
        assert pose_estimator.K[0, 0] == camera_config.fx
        assert pose_estimator.K[1, 1] == camera_config.fy

    def test_estimate_pose_2d2d(self, pose_estimator, sample_points):
        """Test 2D-2D pose estimation."""
        points1, points2 = sample_points

        pose = pose_estimator.estimate_pose_2d2d(points1, points2)

        if pose is not None:
            assert isinstance(pose, Pose)
            assert pose.rotation.shape == (3, 3)
            assert pose.translation.shape[0] == 3

            # Check rotation matrix properties
            assert np.allclose(
                np.linalg.det(pose.rotation), 1.0, atol=1e-6
            )
            assert np.allclose(
                pose.rotation @ pose.rotation.T, np.eye(3), atol=1e-6
            )

    def test_estimate_pose_2d2d_insufficient_points(self, pose_estimator):
        """Test pose estimation with insufficient points."""
        points1 = np.array([[100, 100], [200, 200]], dtype=np.float32)
        points2 = np.array([[105, 105], [205, 205]], dtype=np.float32)

        pose = pose_estimator.estimate_pose_2d2d(points1, points2)
        assert pose is None

    def test_triangulate_points(self, pose_estimator):
        """Test point triangulation."""
        # Create two views
        pose1 = Pose(
            rotation=np.eye(3),
            translation=np.zeros(3),
            inlier_mask=np.ones(1)
        )
        pose2 = Pose(
            rotation=np.eye(3),
            translation=np.array([[0.1], [0], [0]]),
            inlier_mask=np.ones(1)
        )

        # Simple points
        points1 = np.array([[320, 240]], dtype=np.float32)
        points2 = np.array([[310, 240]], dtype=np.float32)

        points_3d = pose_estimator.triangulate_points(
            points1, points2, pose1, pose2
        )

        assert points_3d.shape == (1, 3)

    def test_compute_reprojection_error(self, pose_estimator):
        """Test reprojection error computation."""
        # Create a simple pose
        pose = Pose(
            rotation=np.eye(3),
            translation=np.zeros(3),
            inlier_mask=np.ones(1)
        )

        # Create 3D points
        points_3d = np.array([
            [0, 0, 1],
            [1, 0, 1],
            [0, 1, 1]
        ], dtype=np.float64)

        # Project to 2D
        K = pose_estimator.K
        points_2d = (K @ points_3d.T).T
        points_2d = points_2d[:, :2] / points_2d[:, 2:3]

        # Compute error (should be near zero)
        error = pose_estimator.compute_reprojection_error(
            points_3d, points_2d, pose
        )

        assert error < 1.0  # Should be very small


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
