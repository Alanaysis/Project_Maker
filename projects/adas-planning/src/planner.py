"""
Path Planning Module
====================

This module implements path planning algorithms:
- AStarPlanner: A* search algorithm
- DijkstraPlanner: Dijkstra's algorithm
- RRTPlanner: Rapidly-exploring Random Tree
"""

from typing import List, Tuple, Dict, Optional, Set
import heapq
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .environment import GridMap


@dataclass(order=True)
class Node:
    """Node for search algorithms."""
    f_score: float
    position: Tuple[int, int] = field(compare=False)
    parent: Optional['Node'] = field(default=None, compare=False)
    g_score: float = field(default=0.0, compare=False)


class PathPlanner(ABC):
    """Abstract base class for path planners."""

    @abstractmethod
    def plan(self, grid_map: GridMap, start: Tuple[int, int],
             goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """Plan a path from start to goal."""
        pass


class AStarPlanner(PathPlanner):
    """
    A* Path Planning Algorithm.

    A* uses a heuristic function to guide the search, combining:
    - g(n): actual cost from start to node n
    - h(n): heuristic estimated cost from n to goal
    - f(n) = g(n) + h(n): total estimated cost

    The algorithm is optimal and complete when using an admissible heuristic.
    """

    def __init__(self, allow_diagonal: bool = True, heuristic_type: str = "euclidean"):
        """
        Initialize A* planner.

        Args:
            allow_diagonal: Whether to allow diagonal movement
            heuristic_type: Type of heuristic ("manhattan", "euclidean", "chebyshev")
        """
        self.allow_diagonal = allow_diagonal
        self.heuristic_type = heuristic_type
        self.nodes_explored = 0

    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """
        Calculate heuristic distance between two points.

        Args:
            a: First point (x, y)
            b: Second point (x, y)

        Returns:
            Heuristic distance
        """
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])

        if self.heuristic_type == "manhattan":
            return dx + dy
        elif self.heuristic_type == "euclidean":
            return np.sqrt(dx * dx + dy * dy)
        elif self.heuristic_type == "chebyshev":
            return max(dx, dy)
        else:
            raise ValueError(f"Unknown heuristic type: {self.heuristic_type}")

    def plan(self, grid_map: GridMap, start: Tuple[int, int],
             goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Plan a path from start to goal using A* algorithm.

        Args:
            grid_map: The grid map
            start: Start position (x, y)
            goal: Goal position (x, y)

        Returns:
            List of (x, y) positions representing the path, or None if no path found
        """
        self.nodes_explored = 0

        # Validate start and goal
        if not grid_map.is_free(*start) or not grid_map.is_free(*goal):
            return None

        # Initialize open list with start node
        start_node = Node(
            f_score=self.heuristic(start, goal),
            position=start,
            g_score=0.0
        )

        open_list = [start_node]
        open_set = {start}  # For O(1) lookup
        closed_set: Set[Tuple[int, int]] = set()
        g_scores: Dict[Tuple[int, int], float] = {start: 0.0}

        while open_list:
            # Get node with lowest f_score
            current_node = heapq.heappop(open_list)
            current_pos = current_node.position

            # Remove from open set
            open_set.discard(current_pos)

            # Skip if already processed
            if current_pos in closed_set:
                continue

            # Goal reached
            if current_pos == goal:
                return self._reconstruct_path(current_node)

            # Add to closed set
            closed_set.add(current_pos)
            self.nodes_explored += 1

            # Explore neighbors
            for neighbor_pos in grid_map.get_neighbors(*current_pos, self.allow_diagonal):
                if neighbor_pos in closed_set:
                    continue

                # Calculate tentative g_score
                dx = neighbor_pos[0] - current_pos[0]
                dy = neighbor_pos[1] - current_pos[1]
                move_cost = np.sqrt(dx * dx + dy * dy)
                tentative_g = current_node.g_score + move_cost

                # Skip if we found a better path already
                if neighbor_pos in g_scores and tentative_g >= g_scores[neighbor_pos]:
                    continue

                # This path is better
                g_scores[neighbor_pos] = tentative_g
                f_score = tentative_g + self.heuristic(neighbor_pos, goal)

                neighbor_node = Node(
                    f_score=f_score,
                    position=neighbor_pos,
                    parent=current_node,
                    g_score=tentative_g
                )

                if neighbor_pos not in open_set:
                    heapq.heappush(open_list, neighbor_node)
                    open_set.add(neighbor_pos)

        # No path found
        return None

    def _reconstruct_path(self, node: Node) -> List[Tuple[int, int]]:
        """Reconstruct path from goal node to start."""
        path = []
        current = node
        while current is not None:
            path.append(current.position)
            current = current.parent
        return path[::-1]


class DijkstraPlanner(PathPlanner):
    """
    Dijkstra's Path Planning Algorithm.

    Dijkstra's algorithm finds the shortest path by exploring nodes
    in order of their distance from the start. It is A* with h(n) = 0.
    """

    def __init__(self, allow_diagonal: bool = True):
        """Initialize Dijkstra planner."""
        self.allow_diagonal = allow_diagonal
        self.nodes_explored = 0

    def plan(self, grid_map: GridMap, start: Tuple[int, int],
             goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Plan a path from start to goal using Dijkstra's algorithm.

        Args:
            grid_map: The grid map
            start: Start position (x, y)
            goal: Goal position (x, y)

        Returns:
            List of (x, y) positions representing the path, or None if no path found
        """
        self.nodes_explored = 0

        if not grid_map.is_free(*start) or not grid_map.is_free(*goal):
            return None

        # Initialize
        start_node = Node(f_score=0.0, position=start, g_score=0.0)
        open_list = [start_node]
        open_set = {start}
        closed_set: Set[Tuple[int, int]] = set()
        g_scores: Dict[Tuple[int, int], float] = {start: 0.0}

        while open_list:
            current_node = heapq.heappop(open_list)
            current_pos = current_node.position

            open_set.discard(current_pos)

            if current_pos in closed_set:
                continue

            if current_pos == goal:
                return self._reconstruct_path(current_node)

            closed_set.add(current_pos)
            self.nodes_explored += 1

            for neighbor_pos in grid_map.get_neighbors(*current_pos, self.allow_diagonal):
                if neighbor_pos in closed_set:
                    continue

                dx = neighbor_pos[0] - current_pos[0]
                dy = neighbor_pos[1] - current_pos[1]
                move_cost = np.sqrt(dx * dx + dy * dy)
                tentative_g = current_node.g_score + move_cost

                if neighbor_pos in g_scores and tentative_g >= g_scores[neighbor_pos]:
                    continue

                g_scores[neighbor_pos] = tentative_g

                neighbor_node = Node(
                    f_score=tentative_g,
                    position=neighbor_pos,
                    parent=current_node,
                    g_score=tentative_g
                )

                if neighbor_pos not in open_set:
                    heapq.heappush(open_list, neighbor_node)
                    open_set.add(neighbor_pos)

        return None

    def _reconstruct_path(self, node: Node) -> List[Tuple[int, int]]:
        """Reconstruct path from goal node to start."""
        path = []
        current = node
        while current is not None:
            path.append(current.position)
            current = current.parent
        return path[::-1]


class RRTPlanner(PathPlanner):
    """
    Rapidly-exploring Random Tree (RRT) Path Planning Algorithm.

    RRT is a sampling-based algorithm that builds a tree by randomly
    exploring the space. It is probabilistically complete.
    """

    def __init__(self, max_iterations: int = 1000, step_size: float = 1.0,
                 goal_sample_rate: float = 0.1):
        """
        Initialize RRT planner.

        Args:
            max_iterations: Maximum number of iterations
            step_size: Maximum step size for tree expansion
            goal_sample_rate: Probability of sampling the goal
        """
        self.max_iterations = max_iterations
        self.step_size = step_size
        self.goal_sample_rate = goal_sample_rate
        self.nodes_explored = 0

    def plan(self, grid_map: GridMap, start: Tuple[int, int],
             goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Plan a path from start to goal using RRT algorithm.

        Args:
            grid_map: The grid map
            start: Start position (x, y)
            goal: Goal position (x, y)

        Returns:
            List of (x, y) positions representing the path, or None if no path found
        """
        self.nodes_explored = 0

        if not grid_map.is_free(*start) or not grid_map.is_free(*goal):
            return None

        # Tree structure: node_id -> (position, parent_id)
        nodes = {0: (start, None)}
        positions = [start]  # For nearest neighbor search

        for i in range(self.max_iterations):
            # Sample random point (with bias toward goal)
            if np.random.random() < self.goal_sample_rate:
                random_point = goal
            else:
                random_point = (
                    np.random.randint(0, grid_map.width),
                    np.random.randint(0, grid_map.height)
                )

            # Find nearest node in tree
            nearest_id = self._find_nearest(positions, random_point)
            nearest_pos = positions[nearest_id]

            # Steer toward random point
            new_pos = self._steer(nearest_pos, random_point)

            # Check if new position is valid
            if grid_map.is_free(*new_pos):
                # Check path from nearest to new is collision-free
                if self._is_path_free(grid_map, nearest_pos, new_pos):
                    # Add to tree
                    new_id = len(positions)
                    nodes[new_id] = (new_pos, nearest_id)
                    positions.append(new_pos)
                    self.nodes_explored += 1

                    # Check if goal reached
                    if self._distance(new_pos, goal) < self.step_size:
                        # Reconstruct path
                        path = []
                        current_id = new_id
                        while current_id is not None:
                            pos, parent_id = nodes[current_id]
                            path.append(pos)
                            current_id = parent_id
                        return path[::-1]

        return None

    def _find_nearest(self, positions: List[Tuple[int, int]],
                      point: Tuple[int, int]) -> int:
        """Find index of nearest position to given point."""
        min_dist = float('inf')
        nearest_idx = 0
        for i, pos in enumerate(positions):
            dist = self._distance(pos, point)
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i
        return nearest_idx

    def _steer(self, from_pos: Tuple[int, int],
               to_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Steer from one position toward another, limited by step size."""
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        dist = np.sqrt(dx * dx + dy * dy)

        if dist <= self.step_size:
            return to_pos

        # Limit step size
        ratio = self.step_size / dist
        new_x = int(from_pos[0] + dx * ratio)
        new_y = int(from_pos[1] + dy * ratio)

        return (new_x, new_y)

    def _distance(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Calculate Euclidean distance between two points."""
        return np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def _is_path_free(self, grid_map: GridMap,
                      start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """Check if path between two points is collision-free using line of sight."""
        x0, y0 = start
        x1, y1 = end

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            if not grid_map.is_free(x0, y0):
                return False

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

        return True


class ThetaStarPlanner(PathPlanner):
    """
    Theta* Path Planning Algorithm.

    Theta* is a variant of A* that allows any-angle paths,
    producing smoother paths than grid-based A*.
    """

    def __init__(self, allow_diagonal: bool = True):
        """Initialize Theta* planner."""
        self.allow_diagonal = allow_diagonal
        self.nodes_explored = 0

    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Euclidean distance heuristic."""
        return np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def plan(self, grid_map: GridMap, start: Tuple[int, int],
             goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Plan a path from start to goal using Theta* algorithm.

        Args:
            grid_map: The grid map
            start: Start position (x, y)
            goal: Goal position (x, y)

        Returns:
            List of (x, y) positions representing the path, or None if no path found
        """
        self.nodes_explored = 0

        if not grid_map.is_free(*start) or not grid_map.is_free(*goal):
            return None

        # Initialize
        start_node = Node(
            f_score=self.heuristic(start, goal),
            position=start,
            g_score=0.0
        )

        open_list = [start_node]
        open_set = {start}
        closed_set: Set[Tuple[int, int]] = set()
        g_scores: Dict[Tuple[int, int], float] = {start: 0.0}
        parents: Dict[Tuple[int, int], Tuple[int, int]] = {start: start}

        while open_list:
            current_node = heapq.heappop(open_list)
            current_pos = current_node.position

            open_set.discard(current_pos)

            if current_pos in closed_set:
                continue

            if current_pos == goal:
                return self._reconstruct_path(current_pos, parents)

            closed_set.add(current_pos)
            self.nodes_explored += 1

            for neighbor_pos in grid_map.get_neighbors(*current_pos, self.allow_diagonal):
                if neighbor_pos in closed_set:
                    continue

                # Try to connect to parent's parent (any-angle path)
                parent_pos = parents[current_pos]
                if parent_pos != current_pos and self._line_of_sight(grid_map, parent_pos, neighbor_pos):
                    # Path 2: Connect through parent
                    dist = self.heuristic(parent_pos, neighbor_pos)
                    tentative_g = g_scores[parent_pos] + dist
                    if tentative_g < g_scores.get(neighbor_pos, float('inf')):
                        g_scores[neighbor_pos] = tentative_g
                        parents[neighbor_pos] = parent_pos
                        f_score = tentative_g + self.heuristic(neighbor_pos, goal)
                        neighbor_node = Node(
                            f_score=f_score,
                            position=neighbor_pos,
                            g_score=tentative_g
                        )
                        if neighbor_pos not in open_set:
                            heapq.heappush(open_list, neighbor_node)
                            open_set.add(neighbor_pos)
                else:
                    # Path 1: Standard A* edge
                    dist = self.heuristic(current_pos, neighbor_pos)
                    tentative_g = current_node.g_score + dist
                    if tentative_g < g_scores.get(neighbor_pos, float('inf')):
                        g_scores[neighbor_pos] = tentative_g
                        parents[neighbor_pos] = current_pos
                        f_score = tentative_g + self.heuristic(neighbor_pos, goal)
                        neighbor_node = Node(
                            f_score=f_score,
                            position=neighbor_pos,
                            g_score=tentative_g
                        )
                        if neighbor_pos not in open_set:
                            heapq.heappush(open_list, neighbor_node)
                            open_set.add(neighbor_pos)

        return None

    def _line_of_sight(self, grid_map: GridMap,
                       start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """Check if there is line of sight between two points."""
        x0, y0 = start
        x1, y1 = end

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            if not grid_map.is_free(x0, y0):
                return False

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

        return True

    def _reconstruct_path(self, goal_pos: Tuple[int, int],
                          parents: Dict[Tuple[int, int], Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Reconstruct path from goal to start."""
        path = []
        current = goal_pos
        while current in parents:
            path.append(current)
            if parents[current] == current:
                break
            current = parents[current]
        return path[::-1]
