"""
Environment Module
==================

This module provides grid-based environment representation for path planning.
It includes:
- GridMap: 2D grid representation with obstacles
- SimulationEnvironment: Complete simulation environment with vehicle dynamics
"""

from typing import List, Tuple, Optional, Set
import numpy as np
from dataclasses import dataclass, field
from enum import Enum


class CellType(Enum):
    """Types of cells in the grid map."""
    FREE = 0
    OBSTACLE = 1
    START = 2
    GOAL = 3
    PATH = 4
    VISITED = 5


@dataclass
class GridMap:
    """
    2D Grid Map representation for path planning.

    Attributes:
        width: Width of the grid (number of columns)
        height: Height of the grid (number of rows)
        grid: 2D numpy array representing the map
        resolution: Meters per cell (default 1.0)
    """
    width: int
    height: int
    resolution: float = 1.0
    grid: np.ndarray = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize grid if not provided."""
        if self.grid is None:
            self.grid = np.zeros((self.height, self.width), dtype=np.int8)

    @classmethod
    def from_obstacles(cls, width: int, height: int, obstacles: List[Tuple[int, int]],
                       resolution: float = 1.0) -> 'GridMap':
        """Create a grid map with specified obstacles."""
        grid_map = cls(width, height, resolution)
        for x, y in obstacles:
            grid_map.add_obstacle(x, y)
        return grid_map

    @classmethod
    def from_numpy(cls, grid_array: np.ndarray, resolution: float = 1.0) -> 'GridMap':
        """Create a grid map from a numpy array."""
        height, width = grid_array.shape
        grid_map = cls(width, height, resolution)
        grid_map.grid = grid_array.copy()
        return grid_map

    @classmethod
    def random(cls, width: int, height: int, obstacle_density: float = 0.3,
               seed: Optional[int] = None) -> 'GridMap':
        """Create a random grid map with specified obstacle density."""
        if seed is not None:
            np.random.seed(seed)
        grid_map = cls(width, height)
        # Generate random obstacles
        random_grid = np.random.random((height, width))
        grid_map.grid = (random_grid < obstacle_density).astype(np.int8)
        return grid_map

    @classmethod
    def maze(cls, width: int, height: int, seed: Optional[int] = None) -> 'GridMap':
        """Create a maze-like grid map."""
        if seed is not None:
            np.random.seed(seed)

        # Start with all walls
        grid = np.ones((height, width), dtype=np.int8)

        # Recursive backtracker maze generation
        def carve(x, y):
            grid[y, x] = 0
            directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
            np.random.shuffle(directions)
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and grid[ny, nx] == 1:
                    grid[y + dy // 2, x + dx // 2] = 0
                    carve(nx, ny)

        # Start from odd coordinates
        carve(1, 1)

        return cls.from_numpy(grid)

    def add_obstacle(self, x: int, y: int) -> None:
        """Add an obstacle at position (x, y)."""
        if self.in_bounds(x, y):
            self.grid[y, x] = CellType.OBSTACLE.value

    def remove_obstacle(self, x: int, y: int) -> None:
        """Remove obstacle at position (x, y)."""
        if self.in_bounds(x, y):
            self.grid[y, x] = CellType.FREE.value

    def is_obstacle(self, x: int, y: int) -> bool:
        """Check if position (x, y) is an obstacle."""
        if not self.in_bounds(x, y):
            return True
        return self.grid[y, x] == CellType.OBSTACLE.value

    def is_free(self, x: int, y: int) -> bool:
        """Check if position (x, y) is free."""
        return self.in_bounds(x, y) and not self.is_obstacle(x, y)

    def in_bounds(self, x: int, y: int) -> bool:
        """Check if position (x, y) is within grid bounds."""
        return 0 <= x < self.width and 0 <= y < self.height

    def get_neighbors(self, x: int, y: int, allow_diagonal: bool = True) -> List[Tuple[int, int]]:
        """Get valid neighboring cells."""
        neighbors = []
        # 4-connected neighbors
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        if allow_diagonal:
            directions += [(1, 1), (1, -1), (-1, 1), (-1, -1)]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if self.is_free(nx, ny):
                # For diagonal movement, check that adjacent cells are also free
                if abs(dx) + abs(dy) == 2:  # Diagonal
                    if self.is_free(x + dx, y) and self.is_free(x, y + dy):
                        neighbors.append((nx, ny))
                else:
                    neighbors.append((nx, ny))
        return neighbors

    def add_random_obstacles(self, count: int, seed: Optional[int] = None) -> None:
        """Add random obstacles to the map."""
        if seed is not None:
            np.random.seed(seed)
        added = 0
        while added < count:
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height)
            if self.grid[y, x] == CellType.FREE.value:
                self.grid[y, x] = CellType.OBSTACLE.value
                added += 1

    def clear(self) -> None:
        """Clear all cells to free."""
        self.grid = np.zeros((self.height, self.width), dtype=np.int8)

    def copy(self) -> 'GridMap':
        """Create a copy of this grid map."""
        return GridMap(
            width=self.width,
            height=self.height,
            resolution=self.resolution,
            grid=self.grid.copy()
        )

    def to_numpy(self) -> np.ndarray:
        """Return grid as numpy array."""
        return self.grid.copy()

    def __getitem__(self, key: Tuple[int, int]) -> int:
        """Get cell value at position."""
        x, y = key
        return self.grid[y, x]

    def __setitem__(self, key: Tuple[int, int], value: int) -> None:
        """Set cell value at position."""
        x, y = key
        self.grid[y, x] = value


@dataclass
class SimulationEnvironment:
    """
    Complete simulation environment for autonomous driving.

    Attributes:
        grid_map: The grid map
        start: Start position (x, y)
        goal: Goal position (x, y)
        vehicle_position: Current vehicle position
        vehicle_heading: Current vehicle heading (radians)
        vehicle_speed: Current vehicle speed
        dt: Time step for simulation
    """
    grid_map: GridMap
    start: Tuple[int, int] = (0, 0)
    goal: Tuple[int, int] = (0, 0)
    vehicle_position: np.ndarray = field(default=None)
    vehicle_heading: float = 0.0
    vehicle_speed: float = 0.0
    dt: float = 0.1

    def __post_init__(self):
        """Initialize vehicle position if not set."""
        if self.vehicle_position is None:
            self.vehicle_position = np.array(self.start, dtype=float)

    def reset(self) -> None:
        """Reset the environment to initial state."""
        self.vehicle_position = np.array(self.start, dtype=float)
        self.vehicle_heading = 0.0
        self.vehicle_speed = 0.0

    def step(self, steering: float, acceleration: float) -> Tuple[np.ndarray, float, float]:
        """
        Execute one simulation step.

        Args:
            steering: Steering angle (radians)
            acceleration: Acceleration (m/s^2)

        Returns:
            New position, heading, and speed
        """
        # Simple bicycle model dynamics
        wheelbase = 2.0  # meters

        # Update speed
        self.vehicle_speed += acceleration * self.dt
        self.vehicle_speed = max(0.0, min(self.vehicle_speed, 30.0))  # Limit speed

        # Update heading
        if abs(self.vehicle_speed) > 0.01:
            self.vehicle_heading += (self.vehicle_speed / wheelbase) * np.tan(steering) * self.dt

        # Normalize heading to [-pi, pi]
        self.vehicle_heading = np.arctan2(np.sin(self.vehicle_heading), np.cos(self.vehicle_heading))

        # Update position
        dx = self.vehicle_speed * np.cos(self.vehicle_heading) * self.dt
        dy = self.vehicle_speed * np.sin(self.vehicle_heading) * self.dt
        self.vehicle_position += np.array([dx, dy])

        return self.vehicle_position.copy(), self.vehicle_heading, self.vehicle_speed

    def is_collision(self) -> bool:
        """Check if vehicle is in collision with obstacles."""
        x, y = int(self.vehicle_position[0]), int(self.vehicle_position[1])
        return self.grid_map.is_obstacle(x, y)

    def is_goal_reached(self, threshold: float = 1.0) -> bool:
        """Check if vehicle has reached the goal."""
        distance = np.linalg.norm(self.vehicle_position - np.array(self.goal))
        return distance < threshold

    def get_state(self) -> dict:
        """Get current state of the environment."""
        return {
            "position": self.vehicle_position.copy(),
            "heading": self.vehicle_heading,
            "speed": self.vehicle_speed,
            "at_goal": self.is_goal_reached(),
            "collision": self.is_collision(),
        }
