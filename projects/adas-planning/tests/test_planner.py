"""
Tests for Path Planning Module.
"""

import unittest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.planner import AStarPlanner, DijkstraPlanner, RRTPlanner
from src.environment import GridMap


class TestAStarPlanner(unittest.TestCase):
    """Tests for A* path planning algorithm."""

    def test_simple_path(self):
        """Test path planning on a simple grid."""
        grid_map = GridMap(10, 10)
        planner = AStarPlanner(allow_diagonal=False)

        path = planner.plan(grid_map, (0, 0), (9, 9))

        self.assertIsNotNone(path)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (9, 9))
        self.assertGreater(len(path), 0)

    def test_path_around_obstacle(self):
        """Test that path avoids obstacles."""
        grid_map = GridMap(10, 10)

        # Create wall in the middle
        for y in range(10):
            if y != 5:  # Leave a gap
                grid_map.add_obstacle(5, y)

        planner = AStarPlanner(allow_diagonal=False)
        path = planner.plan(grid_map, (0, 0), (9, 9))

        self.assertIsNotNone(path)
        # Check that path doesn't go through obstacles
        for x, y in path:
            self.assertFalse(grid_map.is_obstacle(x, y))

    def test_no_path(self):
        """Test when no path exists."""
        grid_map = GridMap(10, 10)

        # Create complete wall
        for y in range(10):
            grid_map.add_obstacle(5, y)

        planner = AStarPlanner(allow_diagonal=False)
        path = planner.plan(grid_map, (0, 0), (9, 9))

        self.assertIsNone(path)

    def test_start_is_goal(self):
        """Test when start is the goal."""
        grid_map = GridMap(10, 10)
        planner = AStarPlanner()

        path = planner.plan(grid_map, (5, 5), (5, 5))

        self.assertIsNotNone(path)
        self.assertEqual(len(path), 1)
        self.assertEqual(path[0], (5, 5))

    def test_diagonal_movement(self):
        """Test diagonal movement allowed."""
        grid_map = GridMap(10, 10)
        planner = AStarPlanner(allow_diagonal=True)

        path = planner.plan(grid_map, (0, 0), (9, 9))

        self.assertIsNotNone(path)
        # Diagonal path should be shorter
        self.assertLess(len(path), 19)  # Manhattan distance would be 18

    def test_different_heuristics(self):
        """Test different heuristic functions."""
        grid_map = GridMap(10, 10)

        for heuristic in ["manhattan", "euclidean", "chebyshev"]:
            planner = AStarPlanner(heuristic_type=heuristic)
            path = planner.plan(grid_map, (0, 0), (9, 9))
            self.assertIsNotNone(path, f"Failed with {heuristic} heuristic")

    def test_invalid_start(self):
        """Test with invalid start position."""
        grid_map = GridMap(10, 10)
        grid_map.add_obstacle(0, 0)

        planner = AStarPlanner()
        path = planner.plan(grid_map, (0, 0), (9, 9))

        self.assertIsNone(path)

    def test_nodes_explored(self):
        """Test that nodes_explored counter works."""
        grid_map = GridMap(10, 10)
        planner = AStarPlanner()

        planner.plan(grid_map, (0, 0), (9, 9))

        self.assertGreater(planner.nodes_explored, 0)


class TestDijkstraPlanner(unittest.TestCase):
    """Tests for Dijkstra path planning algorithm."""

    def test_simple_path(self):
        """Test Dijkstra on simple grid."""
        grid_map = GridMap(10, 10)
        planner = DijkstraPlanner(allow_diagonal=False)

        path = planner.plan(grid_map, (0, 0), (9, 9))

        self.assertIsNotNone(path)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (9, 9))

    def test_optimal_path(self):
        """Test that Dijkstra finds optimal path."""
        grid_map = GridMap(10, 10)
        planner = DijkstraPlanner(allow_diagonal=False)

        path = planner.plan(grid_map, (0, 0), (9, 9))

        # Manhattan distance for optimal path without obstacles
        expected_length = 18  # 9 + 9
        path_length = len(path) - 1  # Number of edges

        self.assertEqual(path_length, expected_length)


class TestRRTPlanner(unittest.TestCase):
    """Tests for RRT path planning algorithm."""

    def test_simple_path(self):
        """Test RRT on simple grid."""
        grid_map = GridMap(20, 20)
        planner = RRTPlanner(max_iterations=2000, step_size=2.0)

        path = planner.plan(grid_map, (2, 2), (18, 18))

        self.assertIsNotNone(path)
        self.assertEqual(path[0], (2, 2))
        # RRT is approximate, so check it gets close to goal
        end_x, end_y = path[-1]
        self.assertLess(abs(end_x - 18) + abs(end_y - 18), 5)  # Within 5 of goal

    def test_with_obstacles(self):
        """Test RRT with obstacles."""
        grid_map = GridMap(20, 20)

        # Add some obstacles
        for i in range(10, 15):
            grid_map.add_obstacle(i, 10)

        planner = RRTPlanner(max_iterations=2000, step_size=2.0)

        path = planner.plan(grid_map, (2, 2), (18, 18))

        # RRT is probabilistic, so we just check it found a valid path
        if path is not None:
            for x, y in path:
                self.assertFalse(grid_map.is_obstacle(x, y))


if __name__ == "__main__":
    unittest.main()
