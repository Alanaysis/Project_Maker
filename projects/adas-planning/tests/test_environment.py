"""
Tests for Environment Module.
"""

import unittest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.environment import GridMap, SimulationEnvironment, CellType


class TestGridMap(unittest.TestCase):
    """Tests for GridMap."""

    def test_initialization(self):
        """Test grid map initialization."""
        grid_map = GridMap(10, 10)

        self.assertEqual(grid_map.width, 10)
        self.assertEqual(grid_map.height, 10)
        self.assertEqual(grid_map.grid.shape, (10, 10))

    def test_add_obstacle(self):
        """Test adding obstacles."""
        grid_map = GridMap(10, 10)

        grid_map.add_obstacle(5, 5)

        self.assertTrue(grid_map.is_obstacle(5, 5))
        self.assertFalse(grid_map.is_free(5, 5))

    def test_remove_obstacle(self):
        """Test removing obstacles."""
        grid_map = GridMap(10, 10)

        grid_map.add_obstacle(5, 5)
        grid_map.remove_obstacle(5, 5)

        self.assertFalse(grid_map.is_obstacle(5, 5))
        self.assertTrue(grid_map.is_free(5, 5))

    def test_bounds_checking(self):
        """Test bounds checking."""
        grid_map = GridMap(10, 10)

        self.assertTrue(grid_map.in_bounds(0, 0))
        self.assertTrue(grid_map.in_bounds(9, 9))
        self.assertFalse(grid_map.in_bounds(-1, 0))
        self.assertFalse(grid_map.in_bounds(0, -1))
        self.assertFalse(grid_map.in_bounds(10, 0))
        self.assertFalse(grid_map.in_bounds(0, 10))

    def test_get_neighbors(self):
        """Test neighbor retrieval."""
        grid_map = GridMap(10, 10)

        # Center position should have 8 neighbors (with diagonal)
        neighbors = grid_map.get_neighbors(5, 5, allow_diagonal=True)
        self.assertEqual(len(neighbors), 8)

        # Corner position should have 3 neighbors (with diagonal)
        neighbors = grid_map.get_neighbors(0, 0, allow_diagonal=True)
        self.assertEqual(len(neighbors), 3)

    def test_get_neighbors_no_diagonal(self):
        """Test neighbor retrieval without diagonal."""
        grid_map = GridMap(10, 10)

        neighbors = grid_map.get_neighbors(5, 5, allow_diagonal=False)
        self.assertEqual(len(neighbors), 4)

    def test_get_neighbors_with_obstacles(self):
        """Test neighbor retrieval with obstacles."""
        grid_map = GridMap(10, 10)

        # Add obstacles around center
        grid_map.add_obstacle(4, 5)
        grid_map.add_obstacle(6, 5)

        neighbors = grid_map.get_neighbors(5, 5, allow_diagonal=False)
        self.assertEqual(len(neighbors), 2)  # Only up and down

    def test_from_obstacles(self):
        """Test creating grid from obstacle list."""
        obstacles = [(2, 2), (3, 3), (4, 4)]
        grid_map = GridMap.from_obstacles(10, 10, obstacles)

        for x, y in obstacles:
            self.assertTrue(grid_map.is_obstacle(x, y))

    def test_random_generation(self):
        """Test random grid generation."""
        grid_map = GridMap.random(20, 20, obstacle_density=0.3, seed=42)

        # Should have approximately 30% obstacles
        obstacle_count = np.sum(grid_map.grid == CellType.OBSTACLE.value)
        total_cells = 20 * 20
        density = obstacle_count / total_cells

        self.assertGreater(density, 0.2)
        self.assertLess(density, 0.4)

    def test_copy(self):
        """Test grid map copy."""
        grid_map = GridMap(10, 10)
        grid_map.add_obstacle(5, 5)

        copy = grid_map.copy()

        # Modify original
        grid_map.add_obstacle(6, 6)

        # Copy should not be affected
        self.assertTrue(copy.is_obstacle(5, 5))
        self.assertFalse(copy.is_obstacle(6, 6))

    def test_to_numpy(self):
        """Test numpy conversion."""
        grid_map = GridMap(10, 10)
        grid_map.add_obstacle(5, 5)

        array = grid_map.to_numpy()

        self.assertEqual(array.shape, (10, 10))
        self.assertEqual(array[5, 5], CellType.OBSTACLE.value)


class TestSimulationEnvironment(unittest.TestCase):
    """Tests for SimulationEnvironment."""

    def test_initialization(self):
        """Test environment initialization."""
        grid_map = GridMap(10, 10)
        env = SimulationEnvironment(
            grid_map=grid_map,
            start=(0, 0),
            goal=(9, 9)
        )

        self.assertTrue(np.array_equal(env.vehicle_position, np.array([0.0, 0.0])))
        self.assertEqual(env.vehicle_heading, 0.0)
        self.assertEqual(env.vehicle_speed, 0.0)

    def test_reset(self):
        """Test environment reset."""
        grid_map = GridMap(10, 10)
        env = SimulationEnvironment(
            grid_map=grid_map,
            start=(0, 0),
            goal=(9, 9)
        )

        # Move vehicle
        env.step(0.5, 1.0)

        # Reset
        env.reset()

        self.assertTrue(np.array_equal(env.vehicle_position, np.array([0.0, 0.0])))
        self.assertEqual(env.vehicle_heading, 0.0)
        self.assertEqual(env.vehicle_speed, 0.0)

    def test_step(self):
        """Test simulation step."""
        grid_map = GridMap(10, 10)
        env = SimulationEnvironment(
            grid_map=grid_map,
            start=(0, 0),
            goal=(9, 9),
            dt=0.1
        )

        # Step with acceleration
        pos, heading, speed = env.step(0.0, 1.0)

        # Speed should increase
        self.assertGreater(speed, 0.0)
        # Position should change
        self.assertTrue(pos[0] > 0.0 or pos[1] > 0.0)

    def test_steering(self):
        """Test steering effect."""
        grid_map = GridMap(20, 20)
        env = SimulationEnvironment(
            grid_map=grid_map,
            start=(5, 5),
            goal=(15, 15),
            dt=0.1
        )

        # Set initial speed
        env.vehicle_speed = 5.0

        # Step with steering
        pos1, heading1, _ = env.step(0.0, 0.0)  # No steering
        env.reset()
        env.vehicle_speed = 5.0
        pos2, heading2, _ = env.step(0.5, 0.0)  # With steering

        # Heading should be different
        self.assertNotEqual(heading1, heading2)

    def test_goal_reached(self):
        """Test goal reached detection."""
        grid_map = GridMap(10, 10)
        env = SimulationEnvironment(
            grid_map=grid_map,
            start=(5, 5),
            goal=(5, 5)  # Start at goal
        )

        self.assertTrue(env.is_goal_reached())

    def test_collision_detection(self):
        """Test collision detection."""
        grid_map = GridMap(10, 10)
        grid_map.add_obstacle(5, 5)

        env = SimulationEnvironment(
            grid_map=grid_map,
            start=(5, 5),  # Start on obstacle
            goal=(9, 9)
        )

        self.assertTrue(env.is_collision())

    def test_get_state(self):
        """Test state retrieval."""
        grid_map = GridMap(10, 10)
        env = SimulationEnvironment(
            grid_map=grid_map,
            start=(0, 0),
            goal=(9, 9)
        )

        state = env.get_state()

        self.assertIn("position", state)
        self.assertIn("heading", state)
        self.assertIn("speed", state)
        self.assertIn("at_goal", state)
        self.assertIn("collision", state)


if __name__ == "__main__":
    unittest.main()
