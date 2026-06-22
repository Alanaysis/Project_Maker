"""Grid World environment for Q-Learning.

A simple grid world where an agent navigates to reach a goal while avoiding obstacles.
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional
import numpy as np


class Action(IntEnum):
    """Possible actions in the grid world."""
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


@dataclass
class State:
    """Represents a position in the grid."""
    row: int
    col: int

    def __hash__(self):
        return hash((self.row, self.col))

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        return self.row == other.row and self.col == other.col

    def to_tuple(self) -> tuple[int, int]:
        return (self.row, self.col)


class GridWorld:
    """A simple grid world environment.

    Grid cells:
        0 = empty (passable)
        1 = wall (impassable)
        2 = goal (terminal state)
        3 = trap (negative reward, terminal)

    Attributes:
        rows: Number of rows in the grid.
        cols: Number of columns in the grid.
        start: Starting position of the agent.
        grid: 2D numpy array representing the world.
    """

    # Default reward values
    REWARD_STEP = -1.0      # Reward for each step (encourages efficiency)
    REWARD_GOAL = 100.0     # Reward for reaching the goal
    REWARD_TRAP = -100.0    # Reward for falling into a trap
    REWARD_WALL = -5.0      # Penalty for hitting a wall

    def __init__(
        self,
        rows: int = 5,
        cols: int = 5,
        start: tuple[int, int] = (0, 0),
        goal: tuple[int, int] = (4, 4),
        walls: Optional[list[tuple[int, int]]] = None,
        traps: Optional[list[tuple[int, int]]] = None,
        seed: Optional[int] = None,
    ):
        """Initialize the grid world.

        Args:
            rows: Number of rows.
            cols: Number of columns.
            start: Starting position (row, col).
            goal: Goal position (row, col).
            walls: List of wall positions.
            traps: List of trap positions.
            seed: Random seed for reproducibility.
        """
        self.rows = rows
        self.cols = cols
        self.start = State(*start)
        self.goal = State(*goal)
        self.rng = np.random.RandomState(seed)

        # Initialize grid
        self.grid = np.zeros((rows, cols), dtype=np.int32)

        # Set walls
        if walls:
            for r, c in walls:
                self.grid[r, c] = 1

        # Set goal
        self.grid[goal[0], goal[1]] = 2

        # Set traps
        if traps:
            for r, c in traps:
                self.grid[r, c] = 3

        # Current agent position
        self.agent_pos = State(self.start.row, self.start.col)

        # Action space
        self.n_actions = len(Action)

        # State space
        self.n_states = rows * cols

    def reset(self) -> tuple[int, int]:
        """Reset the environment to the starting position.

        Returns:
            The starting state as (row, col).
        """
        self.agent_pos = State(self.start.row, self.start.col)
        return self.agent_pos.to_tuple()

    def step(self, action: int) -> tuple[tuple[int, int], float, bool, dict]:
        """Take an action in the environment.

        Args:
            action: The action to take (0=up, 1=right, 2=down, 3=left).

        Returns:
            Tuple of (next_state, reward, done, info).
        """
        # Calculate new position
        dr, dc = self._action_to_delta(action)
        new_row = self.agent_pos.row + dr
        new_col = self.agent_pos.col + dc

        # Check if new position is valid
        if not self._is_valid(new_row, new_col):
            # Hit a wall or boundary - stay in place with penalty
            reward = self.REWARD_WALL
            done = False
            info = {"hit_wall": True}
        else:
            # Move to new position
            self.agent_pos = State(new_row, new_col)
            cell_type = self.grid[new_row, new_col]

            if cell_type == 2:  # Goal
                reward = self.REWARD_GOAL
                done = True
                info = {"reached_goal": True}
            elif cell_type == 3:  # Trap
                reward = self.REWARD_TRAP
                done = True
                info = {"fell_in_trap": True}
            else:  # Empty cell
                reward = self.REWARD_STEP
                done = False
                info = {}

        return self.agent_pos.to_tuple(), reward, done, info

    def _action_to_delta(self, action: int) -> tuple[int, int]:
        """Convert action to row/column delta.

        Args:
            action: The action integer.

        Returns:
            Tuple of (delta_row, delta_col).
        """
        deltas = {
            Action.UP: (-1, 0),
            Action.RIGHT: (0, 1),
            Action.DOWN: (1, 0),
            Action.LEFT: (0, -1),
        }
        return deltas[action]

    def _is_valid(self, row: int, col: int) -> bool:
        """Check if a position is valid (within bounds and not a wall).

        Args:
            row: Row index.
            col: Column index.

        Returns:
            True if the position is valid.
        """
        if row < 0 or row >= self.rows:
            return False
        if col < 0 or col >= self.cols:
            return False
        if self.grid[row, col] == 1:  # Wall
            return False
        return True

    def is_terminal(self, row: int, col: int) -> bool:
        """Check if a state is terminal.

        Args:
            row: Row index.
            col: Column index.

        Returns:
            True if the state is terminal (goal or trap).
        """
        return self.grid[row, col] in (2, 3)

    def render(self) -> str:
        """Render the grid world as a string.

        Returns:
            String representation of the grid.
        """
        symbols = {0: ".", 1: "#", 2: "G", 3: "X"}
        lines = []
        for r in range(self.rows):
            row_str = []
            for c in range(self.cols):
                if r == self.agent_pos.row and c == self.agent_pos.col:
                    row_str.append("A")
                elif r == self.start.row and c == self.start.col:
                    row_str.append("S")
                else:
                    row_str.append(symbols[self.grid[r, c]])
            lines.append(" ".join(row_str))
        return "\n".join(lines)

    def get_all_states(self) -> list[tuple[int, int]]:
        """Get all valid (non-wall) states.

        Returns:
            List of (row, col) tuples for all valid states.
        """
        states = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r, c] != 1:
                    states.append((r, c))
        return states

    def get_state_index(self, row: int, col: int) -> int:
        """Convert (row, col) to a flat state index.

        Args:
            row: Row index.
            col: Column index.

        Returns:
            Flat index.
        """
        return row * self.cols + col

    def index_to_state(self, index: int) -> tuple[int, int]:
        """Convert a flat state index to (row, col).

        Args:
            index: Flat index.

        Returns:
            Tuple of (row, col).
        """
        return (index // self.cols, index % self.cols)
