"""
Tests for map management module.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.map_manager import MapManager, MapPoint, Keyframe
from src.feature_extractor import Frame
from src.pose_estimator import Pose


@pytest.fixture
def map_manager():
    """Create map manager instance."""
    return MapManager(max_keyframes=100)


@pytest.fixture
def sample_pose():
    """Create sample pose."""
    return Pose(
        rotation=np.eye(3),
        translation=np.zeros(3),
        inlier_mask=np.ones(1)
    )


@pytest.fixture
def sample_frame():
    """Create sample frame."""
    return Frame(
        id=0,
        image=np.zeros((480, 640), dtype=np.uint8),
        keypoints=[cv2.KeyPoint(float(i * 10), float(i * 10), 10) for i in range(10)],
        descriptors=np.random.randint(0, 256, (10, 32), dtype=np.uint8),
        timestamp=0.0
    )


class TestMapPoint:
    """Test cases for MapPoint."""

    def test_creation(self):
        """Test map point creation."""
        point = MapPoint(
            id=0,
            position=np.array([1, 2, 3]),
            descriptor=np.random.randint(0, 256, 32, dtype=np.uint8)
        )

        assert point.id == 0
        assert np.array_equal(point.position, [1, 2, 3])
        assert point.num_observations == 0

    def test_add_observation(self):
        """Test adding observation."""
        point = MapPoint(
            id=0,
            position=np.array([1, 2, 3]),
            descriptor=np.random.randint(0, 256, 32, dtype=np.uint8)
        )

        point.add_observation(0, 5)
        point.add_observation(1, 10)

        assert point.num_observations == 2
        assert point.observations[0] == 5
        assert point.observations[1] == 10

    def test_remove_observation(self):
        """Test removing observation."""
        point = MapPoint(
            id=0,
            position=np.array([1, 2, 3]),
            descriptor=np.random.randint(0, 256, 32, dtype=np.uint8)
        )

        point.add_observation(0, 5)
        point.add_observation(1, 10)
        point.remove_observation(0)

        assert point.num_observations == 1
        assert 0 not in point.observations


class TestKeyframe:
    """Test cases for Keyframe."""

    def test_creation(self, sample_frame, sample_pose):
        """Test keyframe creation."""
        kf = Keyframe(
            id=0,
            frame=sample_frame,
            pose=sample_pose,
            timestamp=0.0
        )

        assert kf.id == 0
        assert kf.frame == sample_frame
        assert kf.pose == sample_pose

    def test_position(self, sample_frame, sample_pose):
        """Test keyframe position property."""
        kf = Keyframe(
            id=0,
            frame=sample_frame,
            pose=sample_pose,
            timestamp=0.0
        )

        position = kf.position
        assert position.shape == (3,)
        assert np.allclose(position, 0)

    def test_covisibility(self, sample_frame, sample_pose):
        """Test covisibility management."""
        kf = Keyframe(
            id=0,
            frame=sample_frame,
            pose=sample_pose,
            timestamp=0.0
        )

        kf.add_covisibility(1, 10)
        kf.add_covisibility(2, 20)
        kf.add_covisibility(3, 5)

        best = kf.get_best_covisible_keyframes(2)
        assert len(best) == 2
        assert best[0][0] == 2  # Highest covisibility
        assert best[1][0] == 1


class TestMapManager:
    """Test cases for MapManager."""

    def test_initialization(self, map_manager):
        """Test map manager initialization."""
        assert len(map_manager.keyframes) == 0
        assert len(map_manager.map_points) == 0
        assert map_manager.keyframe_counter == 0
        assert map_manager.map_point_counter == 0

    def test_add_keyframe(self, map_manager, sample_frame, sample_pose):
        """Test adding keyframe."""
        kf = map_manager.add_keyframe(sample_frame, sample_pose)

        assert kf.id == 0
        assert len(map_manager.keyframes) == 1
        assert map_manager.current_keyframe == kf

    def test_add_map_point(self, map_manager):
        """Test adding map point."""
        point = map_manager.add_map_point(
            position=np.array([1, 2, 3]),
            descriptor=np.random.randint(0, 256, 32, dtype=np.uint8),
            frame_id=0,
            keypoint_idx=5
        )

        assert point.id == 0
        assert len(map_manager.map_points) == 1
        assert point.num_observations == 1

    def test_get_map_points_in_frame(self, map_manager):
        """Test getting map points in frame."""
        # Add some points
        for i in range(5):
            map_manager.add_map_point(
                position=np.array([i, 0, 0]),
                descriptor=np.random.randint(0, 256, 32, dtype=np.uint8),
                frame_id=0,
                keypoint_idx=i
            )

        for i in range(3):
            map_manager.add_map_point(
                position=np.array([i, 1, 0]),
                descriptor=np.random.randint(0, 256, 32, dtype=np.uint8),
                frame_id=1,
                keypoint_idx=i
            )

        points_in_frame0 = map_manager.get_map_points_in_frame(0)
        points_in_frame1 = map_manager.get_map_points_in_frame(1)

        assert len(points_in_frame0) == 5
        assert len(points_in_frame1) == 3

    def test_get_point_positions(self, map_manager):
        """Test getting point positions."""
        for i in range(3):
            map_manager.add_map_point(
                position=np.array([i, 0, 0]),
                descriptor=np.random.randint(0, 256, 32, dtype=np.uint8),
                frame_id=0,
                keypoint_idx=i
            )

        positions = map_manager.get_point_positions()
        assert positions.shape == (3, 3)

    def test_get_keyframe_poses(self, map_manager, sample_frame, sample_pose):
        """Test getting keyframe poses."""
        for i in range(3):
            frame = Frame(
                id=i,
                image=np.zeros((480, 640), dtype=np.uint8),
                keypoints=[],
                descriptors=np.array([]),
                timestamp=float(i)
            )
            map_manager.add_keyframe(frame, sample_pose)

        poses = map_manager.get_keyframe_poses()
        assert len(poses) == 3
        assert all(p.shape == (4, 4) for p in poses)

    def test_covisibility_update(self, map_manager, sample_frame, sample_pose):
        """Test covisibility graph update."""
        # Add two keyframes
        kf1 = map_manager.add_keyframe(sample_frame, sample_pose)

        frame2 = Frame(
            id=1,
            image=np.zeros((480, 640), dtype=np.uint8),
            keypoints=[],
            descriptors=np.array([]),
            timestamp=1.0
        )
        kf2 = map_manager.add_keyframe(frame2, sample_pose)

        # Add shared map points
        for i in range(15):
            map_manager.add_map_point(
                position=np.array([i, 0, 0]),
                descriptor=np.random.randint(0, 256, 32, dtype=np.uint8),
                frame_id=kf1.id,
                keypoint_idx=i
            )
            # Add observation from second keyframe
            map_manager.map_points[i].add_observation(kf2.id, i)

        # Update covisibility
        map_manager.update_covisibility(kf2)

        # Check covisibility was updated
        assert kf2.id in kf1.covisibility or kf1.id in kf2.covisibility

    def test_statistics(self, map_manager, sample_frame, sample_pose):
        """Test statistics computation."""
        # Add some data
        map_manager.add_keyframe(sample_frame, sample_pose)
        map_manager.add_map_point(
            position=np.array([1, 2, 3]),
            descriptor=np.random.randint(0, 256, 32, dtype=np.uint8),
            frame_id=0,
            keypoint_idx=0
        )

        stats = map_manager.get_statistics()

        assert stats['num_keyframes'] == 1
        assert stats['num_map_points'] == 1
        assert stats['total_observations'] == 1

    def test_clear(self, map_manager, sample_frame, sample_pose):
        """Test clearing map."""
        map_manager.add_keyframe(sample_frame, sample_pose)
        map_manager.add_map_point(
            position=np.array([1, 2, 3]),
            descriptor=np.random.randint(0, 256, 32, dtype=np.uint8),
            frame_id=0,
            keypoint_idx=0
        )

        map_manager.clear()

        assert len(map_manager.keyframes) == 0
        assert len(map_manager.map_points) == 0
        assert map_manager.keyframe_counter == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
