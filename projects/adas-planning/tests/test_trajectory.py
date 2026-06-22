"""
Tests for Trajectory Module.
"""

import unittest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.trajectory import Trajectory, TrajectoryPoint, TrajectoryGenerator


class TestTrajectoryPoint(unittest.TestCase):
    """Tests for TrajectoryPoint."""

    def test_initialization(self):
        """Test TrajectoryPoint initialization."""
        point = TrajectoryPoint(x=1.0, y=2.0, heading=0.5)

        self.assertEqual(point.x, 1.0)
        self.assertEqual(point.y, 2.0)
        self.assertEqual(point.heading, 0.5)

    def test_to_numpy(self):
        """Test conversion to numpy."""
        point = TrajectoryPoint(x=1.0, y=2.0, heading=0.5)

        arr = point.to_numpy()

        self.assertEqual(arr.shape, (3,))
        self.assertEqual(arr[0], 1.0)
        self.assertEqual(arr[1], 2.0)
        self.assertEqual(arr[2], 0.5)

    def test_from_numpy(self):
        """Test creation from numpy."""
        arr = np.array([1.0, 2.0, 0.5])

        point = TrajectoryPoint.from_numpy(arr)

        self.assertEqual(point.x, 1.0)
        self.assertEqual(point.y, 2.0)
        self.assertEqual(point.heading, 0.5)


class TestTrajectory(unittest.TestCase):
    """Tests for Trajectory."""

    def test_initialization(self):
        """Test Trajectory initialization."""
        trajectory = Trajectory()

        self.assertEqual(len(trajectory), 0)

    def test_add_point(self):
        """Test adding points."""
        trajectory = Trajectory()

        trajectory.add_point(TrajectoryPoint(x=0.0, y=0.0))
        trajectory.add_point(TrajectoryPoint(x=1.0, y=1.0))

        self.assertEqual(len(trajectory), 2)

    def test_from_waypoints(self):
        """Test creation from waypoints."""
        waypoints = [(0, 0), (1, 0), (2, 0)]

        trajectory = Trajectory.from_waypoints(waypoints)

        self.assertEqual(len(trajectory), 3)
        self.assertEqual(trajectory[0].x, 0.0)
        self.assertEqual(trajectory[1].x, 1.0)

    def test_from_numpy(self):
        """Test creation from numpy array."""
        array = np.array([[0, 0], [1, 1], [2, 2]])

        trajectory = Trajectory.from_numpy(array)

        self.assertEqual(len(trajectory), 3)

    def test_get_positions(self):
        """Test getting positions."""
        trajectory = Trajectory.from_waypoints([(0, 0), (1, 1), (2, 2)])

        positions = trajectory.get_positions()

        self.assertEqual(positions.shape, (3, 2))

    def test_get_headings(self):
        """Test getting headings."""
        trajectory = Trajectory.from_waypoints([(0, 0), (1, 0), (2, 0)])

        headings = trajectory.get_headings()

        self.assertEqual(len(headings), 3)

    def test_get_length(self):
        """Test trajectory length calculation."""
        trajectory = Trajectory.from_waypoints([(0, 0), (3, 0), (3, 4)])

        length = trajectory.get_length()

        self.assertAlmostEqual(length, 7.0, places=5)  # 3 + 4

    def test_get_nearest_index(self):
        """Test finding nearest point."""
        trajectory = Trajectory.from_waypoints([(0, 0), (1, 0), (2, 0)])

        idx = trajectory.get_nearest_index(0.5, 0.1)

        self.assertIn(idx, [0, 1])

    def test_get_lookahead_point(self):
        """Test lookahead point retrieval."""
        trajectory = Trajectory.from_waypoints([(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)])

        point = trajectory.get_lookahead_point(0.0, 0.0, 2.0)

        self.assertIsNotNone(point)

    def test_to_numpy(self):
        """Test numpy conversion."""
        trajectory = Trajectory.from_waypoints([(0, 0), (1, 1)])

        array = trajectory.to_numpy()

        self.assertEqual(array.shape, (2, 2))


class TestTrajectoryGenerator(unittest.TestCase):
    """Tests for TrajectoryGenerator."""

    def test_initialization(self):
        """Test generator initialization."""
        generator = TrajectoryGenerator(ds=0.1)

        self.assertEqual(generator.ds, 0.1)

    def test_generate_simple(self):
        """Test simple trajectory generation."""
        generator = TrajectoryGenerator(ds=1.0)
        waypoints = [(0, 0), (5, 0), (10, 0)]

        trajectory = generator.generate(waypoints, target_velocity=5.0)

        self.assertGreater(len(trajectory), 0)

    def test_generate_smooth(self):
        """Test that generated trajectory is smooth."""
        generator = TrajectoryGenerator(ds=0.5)
        waypoints = [(0, 0), (5, 5), (10, 0)]

        trajectory = generator.generate(waypoints, target_velocity=5.0)

        # Check that headings change gradually
        headings = trajectory.get_headings()
        heading_diffs = np.abs(np.diff(headings))
        self.assertLess(np.max(heading_diffs), np.pi / 2)  # No sharp turns

    def test_generate_with_velocity_profile(self):
        """Test trajectory generation with velocity profile."""
        generator = TrajectoryGenerator(ds=1.0)
        waypoints = [(0, 0), (10, 0), (10, 10)]

        trajectory = generator.generate_with_velocity_profile(
            waypoints,
            max_velocity=10.0,
            max_acceleration=2.0
        )

        # Check velocities are positive
        velocities = trajectory.get_velocities()
        self.assertTrue(np.all(velocities >= 0))

    def test_curvature_computation(self):
        """Test curvature computation."""
        generator = TrajectoryGenerator(ds=0.5)
        waypoints = [(0, 0), (5, 5), (10, 0)]

        trajectory = generator.generate(waypoints, target_velocity=5.0)

        curvatures = trajectory.get_curvatures()

        # Curvatures should be non-negative
        self.assertTrue(np.all(curvatures >= 0))

    def test_minimum_waypoints(self):
        """Test with minimum number of waypoints."""
        generator = TrajectoryGenerator()
        waypoints = [(0, 0), (1, 0)]

        trajectory = generator.generate(waypoints)

        self.assertGreater(len(trajectory), 0)


if __name__ == "__main__":
    unittest.main()
