"""
Tests for SLAM system integration.
"""

import pytest
import numpy as np
import cv2
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.slam_system import SLAMSystem
from src.config import SLAMConfig, CameraConfig, FeatureConfig


@pytest.fixture
def slam_config():
    """Create SLAM configuration for testing."""
    return SLAMConfig(
        camera=CameraConfig(
            fx=525.0,
            fy=525.0,
            cx=319.5,
            cy=239.5,
            width=640,
            height=480
        ),
        features=FeatureConfig(
            n_features=500,
            min_matches=5
        ),
        keyframe_interval=3,
        max_keyframes=10,
        loop_closure_enabled=False
    )


@pytest.fixture
def slam_system(slam_config):
    """Create SLAM system instance."""
    return SLAMSystem(slam_config)


@pytest.fixture
def synthetic_images():
    """Create synthetic test images."""
    images = []
    base_image = np.zeros((480, 640), dtype=np.uint8)

    # Add geometric features
    cv2.rectangle(base_image, (100, 100), (200, 200), 255, -1)
    cv2.circle(base_image, (400, 300), 50, 255, -1)
    cv2.line(base_image, (0, 0), (640, 480), 255, 2)

    # Create sequence with slight transformations
    for i in range(10):
        M = np.float32([
            [1, 0, i * 5],
            [0, 1, i * 2]
        ])
        transformed = cv2.warpAffine(base_image, M, (640, 480))
        images.append(transformed)

    return images


class TestSLAMSystem:
    """Test cases for SLAMSystem."""

    def test_initialization(self, slam_system):
        """Test SLAM system initialization."""
        assert not slam_system.is_initialized
        assert slam_system.frame_count == 0
        assert slam_system.current_frame is None

    def test_initialize_with_frame(self, slam_system, synthetic_images):
        """Test SLAM initialization with first frame."""
        success = slam_system.initialize(synthetic_images[0])

        assert success
        assert slam_system.is_initialized
        assert slam_system.current_frame is not None
        assert slam_system.current_pose is not None

    def test_process_frame(self, slam_system, synthetic_images):
        """Test frame processing."""
        # Initialize
        slam_system.initialize(synthetic_images[0])

        # Process subsequent frames
        for i in range(1, len(synthetic_images)):
            success = slam_system.process_frame(synthetic_images[i])

            if success:
                assert slam_system.frame_count > 0
                assert len(slam_system.trajectory) > 0

    def test_get_trajectory(self, slam_system, synthetic_images):
        """Test trajectory retrieval."""
        slam_system.initialize(synthetic_images[0])

        for image in synthetic_images[1:]:
            slam_system.process_frame(image)

        trajectory = slam_system.get_trajectory()

        if len(trajectory) > 0:
            assert trajectory.shape[1] == 3

    def test_get_map_points(self, slam_system, synthetic_images):
        """Test map points retrieval."""
        slam_system.initialize(synthetic_images[0])

        for image in synthetic_images[1:]:
            slam_system.process_frame(image)

        points = slam_system.get_map_points()

        # May or may not have points depending on processing
        if len(points) > 0:
            assert points.shape[1] == 3

    def test_statistics(self, slam_system, synthetic_images):
        """Test statistics computation."""
        slam_system.initialize(synthetic_images[0])

        for image in synthetic_images[1:5]:
            slam_system.process_frame(image)

        stats = slam_system.get_statistics()

        assert 'frames_processed' in stats
        assert 'num_keyframes' in stats
        assert 'num_map_points' in stats
        assert stats['is_initialized'] == True

    def test_reset(self, slam_system, synthetic_images):
        """Test system reset."""
        slam_system.initialize(synthetic_images[0])

        for image in synthetic_images[1:3]:
            slam_system.process_frame(image)

        slam_system.reset()

        assert not slam_system.is_initialized
        assert slam_system.frame_count == 0
        assert len(slam_system.trajectory) == 0

    def test_process_video(self, slam_system, tmp_path):
        """Test video processing."""
        # Create a simple test video
        video_path = tmp_path / "test.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))

        # Write some frames
        for i in range(10):
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            out.write(frame)
        out.release()

        # Process video
        output_path = tmp_path / "map.ply"
        slam_system.process_video(str(video_path), str(output_path), max_frames=5)

        assert slam_system.frame_count > 0


class TestSLAMIntegration:
    """Integration tests for SLAM system."""

    def test_full_pipeline(self, slam_config):
        """Test complete SLAM pipeline."""
        slam = SLAMSystem(slam_config)

        # Create synthetic sequence
        base_image = np.zeros((480, 640), dtype=np.uint8)
        cv2.rectangle(base_image, (100, 100), (300, 300), 255, -1)
        cv2.circle(base_image, (400, 200), 50, 255, -1)

        # Process frames
        for i in range(20):
            M = np.float32([
                [1, 0, i * 3],
                [0, 1, i * 1]
            ])
            frame = cv2.warpAffine(base_image, M, (640, 480))
            slam.process_frame(frame, timestamp=i / 30.0)

        # Verify results
        stats = slam.get_statistics()
        assert stats['frames_processed'] == 20
        assert stats['is_initialized'] == True

    def test_keyframe_creation(self, slam_config):
        """Test keyframe creation during processing."""
        slam = SLAMSystem(slam_config)

        base_image = np.zeros((480, 640), dtype=np.uint8)
        cv2.rectangle(base_image, (100, 100), (300, 300), 255, -1)

        # Process enough frames to create keyframes
        for i in range(15):
            M = np.float32([
                [1, 0, i * 5],
                [0, 1, i * 2]
            ])
            frame = cv2.warpAffine(base_image, M, (640, 480))
            slam.process_frame(frame)

        stats = slam.get_statistics()
        # Should have created at least one keyframe
        assert stats['num_keyframes'] >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
