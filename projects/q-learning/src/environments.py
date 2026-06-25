"""Additional environments for Q-Learning.

Includes FrozenLake, Maze, and simple game environments.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np


class FrozenLake:
    """FrozenLake environment.

    A grid world where the agent must reach the goal without falling into holes.
    - S: Start (safe)
    - F: Frozen (safe, can move)
    - H: Hole (fall in, episode ends)
    - G: Goal (reach to win)

    The ice is slippery: movement is stochastic (80% intended, 10% left, 10% right).
    """

    REWARD_STEP = 0.0
    REWARD_GOAL = 1.0
    REWARD_HOLE = 0.0

    # Predefined maps
    MAPS = {
        "4x4": [
            "SFFF",
            "FHFH",
            "FFFH",
            "HFFG",
        ],
        "8x8": [
            "SFFFFFFF",
            "FFFFFFFF",
            "FFFHFFFF",
            "FFFFFHFF",
            "FFFHFFFF",
            "FHHFFFHF",
            "FHFFHFHF",
            "FFFHFFFG",
        ],
    }

    def __init__(
        self,
        map_name: str = "4x4",
        is_slippery: bool = True,
        seed: Optional[int] = None,
    ):
        """Initialize FrozenLake environment.

        Args:
            map_name: Name of predefined map ("4x4" or "8x8").
            is_slippery: Whether movement is stochastic.
            seed: Random seed.
        """
        if map_name not in self.MAPS:
            raise ValueError(f"Unknown map: {map_name}. Choose from {list(self.MAPS.keys())}")

        self.map = self.MAPS[map_name]
        self.rows = len(self.map)
        self.cols = len(self.map[0])
        self.is_slippery = is_slippery
        self.rng = np.random.RandomState(seed)

        # Parse map
        self.grid = np.zeros((self.rows, self.cols), dtype=np.int32)
        self.start = None
        self.goal = None

        for r, row in enumerate(self.map):
            for c, cell in enumerate(row):
                if cell == 'S':
                    self.start = (r, c)
                    self.grid[r, c] = 0  # Safe
                elif cell == 'F':
                    self.grid[r, c] = 0  # Frozen (safe)
                elif cell == 'H':
                    self.grid[r, c] = 3  # Hole
                elif cell == 'G':
                    self.goal = (r, c)
                    self.grid[r, c] = 2  # Goal

        if self.start is None:
            self.start = (0, 0)
        if self.goal is None:
            self.goal = (self.rows - 1, self.cols - 1)

        self.agent_pos = self.start
        self.n_actions = 4  # Up, Right, Down, Left
        self.n_states = self.rows * self.cols

    def reset(self) -> tuple[int, int]:
        """Reset environment."""
        self.agent_pos = self.start
        return self.agent_pos

    def step(self, action: int) -> tuple[tuple[int, int], float, bool, dict]:
        """Take an action.

        Args:
            action: 0=up, 1=right, 2=down, 3=left.

        Returns:
            Tuple of (next_state, reward, done, info).
        """
        if self.is_slippery:
            # Stochastic movement: 80% intended, 10% left, 10% right
            prob = self.rng.random()
            if prob < 0.1:
                action = (action - 1) % 4  # Turn left
            elif prob < 0.2:
                action = (action + 1) % 4  # Turn right
            # else: intended action (80%)

        # Calculate new position
        deltas = {0: (-1, 0), 1: (0, 1), 2: (1, 0), 3: (0, -1)}
        dr, dc = deltas[action]
        new_r = self.agent_pos[0] + dr
        new_c = self.agent_pos[1] + dc

        # Check bounds
        if 0 <= new_r < self.rows and 0 <= new_c < self.cols:
            self.agent_pos = (new_r, new_c)

        # Check cell type
        cell = self.grid[self.agent_pos[0], self.agent_pos[1]]

        if cell == 2:  # Goal
            return self.agent_pos, self.REWARD_GOAL, True, {"reached_goal": True}
        elif cell == 3:  # Hole
            return self.agent_pos, self.REWARD_HOLE, True, {"fell_in_hole": True}
        else:  # Safe
            return self.agent_pos, self.REWARD_STEP, False, {}

    def get_state_index(self, row: int, col: int) -> int:
        """Convert (row, col) to flat index."""
        return row * self.cols + col

    def index_to_state(self, index: int) -> tuple[int, int]:
        """Convert flat index to (row, col)."""
        return (index // self.cols, index % self.cols)

    def is_terminal(self, row: int, col: int) -> bool:
        """Check if state is terminal."""
        return self.grid[row, col] in (2, 3)

    def render(self) -> str:
        """Render environment."""
        symbols = {0: "F", 1: "#", 2: "G", 3: "H"}
        lines = []
        for r in range(self.rows):
            row_str = []
            for c in range(self.cols):
                if (r, c) == self.agent_pos:
                    row_str.append("A")
                elif (r, c) == self.start:
                    row_str.append("S")
                else:
                    row_str.append(symbols[self.grid[r, c]])
            lines.append(" ".join(row_str))
        return "\n".join(lines)


class Maze:
    """Maze environment for Q-Learning.

    A maze where the agent must find the path from start to goal.
    """

    REWARD_STEP = -1.0
    REWARD_GOAL = 100.0
    REWARD_WALL = -5.0

    def __init__(
        self,
        maze: Optional[list[list[int]]] = None,
        start: tuple[int, int] = (0, 0),
        goal: tuple[int, int] = None,
        seed: Optional[int] = None,
    ):
        """Initialize Maze environment.

        Args:
            maze: 2D list where 0=path, 1=wall. If None, generates random maze.
            start: Starting position.
            goal: Goal position.
            seed: Random seed.
        """
        self.rng = np.random.RandomState(seed)

        if maze is None:
            self.grid = self._generate_maze(11, 11)
        else:
            self.grid = np.array(maze, dtype=np.int32)

        self.rows, self.cols = self.grid.shape
        self.start = start
        self.goal = goal if goal else (self.rows - 2, self.cols - 2)

        # Ensure start and goal are valid
        self.grid[self.start[0], self.start[1]] = 0
        self.grid[self.goal[0], self.goal[1]] = 0

        self.agent_pos = self.start
        self.n_actions = 4
        self.n_states = self.rows * self.cols

    def _generate_maze(self, rows: int, cols: int) -> np.ndarray:
        """Generate a random maze using DFS.

        Args:
            rows: Number of rows (must be odd).
            cols: Number of columns (must be odd).

        Returns:
            2D numpy array representing the maze.
        """
        # Ensure odd dimensions
        rows = rows if rows % 2 == 1 else rows + 1
        cols = cols if cols % 2 == 1 else cols + 1

        # Initialize with walls
        maze = np.ones((rows, cols), dtype=np.int32)

        # Carve paths using DFS
        def carve(r, c):
            maze[r, c] = 0
            directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
            self.rng.shuffle(directions)

            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 1 <= nr < rows - 1 and 1 <= nc < cols - 1 and maze[nr, nc] == 1:
                    maze[r + dr // 2, c + dc // 2] = 0
                    carve(nr, nc)

        carve(1, 1)

        # Set start and goal
        maze[1, 1] = 0
        maze[rows - 2, cols - 2] = 0

        return maze

    def reset(self) -> tuple[int, int]:
        """Reset environment."""
        self.agent_pos = self.start
        return self.agent_pos

    def step(self, action: int) -> tuple[tuple[int, int], float, bool, dict]:
        """Take an action."""
        deltas = {0: (-1, 0), 1: (0, 1), 2: (1, 0), 3: (0, -1)}
        dr, dc = deltas[action]
        new_r = self.agent_pos[0] + dr
        new_c = self.agent_pos[1] + dc

        # Check if new position is valid
        if 0 <= new_r < self.rows and 0 <= new_c < self.cols and self.grid[new_r, new_c] == 0:
            self.agent_pos = (new_r, new_c)

            if self.agent_pos == self.goal:
                return self.agent_pos, self.REWARD_GOAL, True, {"reached_goal": True}
            else:
                return self.agent_pos, self.REWARD_STEP, False, {}
        else:
            # Hit wall - stay in place
            return self.agent_pos, self.REWARD_WALL, False, {"hit_wall": True}

    def get_state_index(self, row: int, col: int) -> int:
        """Convert (row, col) to flat index."""
        return row * self.cols + col

    def index_to_state(self, index: int) -> tuple[int, int]:
        """Convert flat index to (row, col)."""
        return (index // self.cols, index % self.cols)

    def render(self) -> str:
        """Render maze."""
        symbols = {0: ".", 1: "#"}
        lines = []
        for r in range(self.rows):
            row_str = []
            for c in range(self.cols):
                if (r, c) == self.agent_pos:
                    row_str.append("A")
                elif (r, c) == self.start:
                    row_str.append("S")
                elif (r, c) == self.goal:
                    row_str.append("G")
                else:
                    row_str.append(symbols[self.grid[r, c]])
            lines.append(" ".join(row_str))
        return "\n".join(lines)


class SimpleGame:
    """Simple game environment.

    A number guessing game where the agent learns to guess a target number.
    States: last guess result (too_high, too_low, correct)
    Actions: guess ranges
    """

    REWARD_CORRECT = 100.0
    REWARD_CLOSE = 10.0
    REWARD_WRONG = -1.0

    def __init__(
        self,
        max_number: int = 100,
        max_attempts: int = 10,
        seed: Optional[int] = None,
    ):
        """Initialize SimpleGame.

        Args:
            max_number: Maximum number to guess.
            max_attempts: Maximum attempts per game.
            seed: Random seed.
        """
        self.max_number = max_number
        self.max_attempts = max_attempts
        self.rng = np.random.RandomState(seed)

        # State: (low, high, attempt)
        # Discretized into buckets
        self.n_buckets = 10
        self.n_states = self.n_buckets * self.n_buckets * max_attempts
        self.n_actions = self.n_buckets  # Guess in different ranges

        self.target = None
        self.low = 0
        self.high = max_number
        self.attempt = 0

    def reset(self) -> tuple[int, int, int]:
        """Reset game with new target."""
        self.target = self.rng.randint(1, self.max_number + 1)
        self.low = 0
        self.high = self.max_number
        self.attempt = 0
        return self._get_state()

    def _get_state(self) -> tuple[int, int, int]:
        """Get discretized state."""
        # Bucket the low and high ranges
        low_bucket = min(self.n_buckets - 1, int(self.low / self.max_number * self.n_buckets))
        high_bucket = min(self.n_buckets - 1, int(self.high / self.max_number * self.n_buckets))
        return (low_bucket, high_bucket, self.attempt)

    def _state_to_index(self, state: tuple[int, int, int]) -> int:
        """Convert state to flat index."""
        return state[0] * (self.n_buckets * self.max_attempts) + state[1] * self.max_attempts + state[2]

    def get_state_index(self, *args) -> int:
        """Get state index (compatible with other environments)."""
        if len(args) == 3:
            return self._state_to_index(args)
        elif len(args) == 1 and isinstance(args[0], tuple):
            return self._state_to_index(args[0])
        else:
            raise ValueError("Invalid arguments for get_state_index")

    def step(self, action: int) -> tuple[tuple[int, int, int], float, bool, dict]:
        """Take an action (make a guess).

        Args:
            action: Action index (0 to n_buckets-1).

        Returns:
            Tuple of (next_state, reward, done, info).
        """
        # Convert action to guess range
        bucket_size = (self.high - self.low) / self.n_actions
        guess = int(self.low + (action + 0.5) * bucket_size)
        guess = max(self.low + 1, min(self.high - 1, guess))

        self.attempt += 1

        if guess == self.target:
            # Correct guess
            reward = self.REWARD_CORRECT + (self.max_attempts - self.attempt) * 10
            return self._get_state(), reward, True, {"correct": True, "guess": guess}
        elif abs(guess - self.target) <= 5:
            # Close guess
            reward = self.REWARD_CLOSE
        else:
            reward = self.REWARD_WRONG

        # Update range
        if guess < self.target:
            self.low = guess
            info = {"too_low": True, "guess": guess}
        else:
            self.high = guess
            info = {"too_high": True, "guess": guess}

        # Check if out of attempts
        if self.attempt >= self.max_attempts:
            return self._get_state(), reward, True, {"out_of_attempts": True, "guess": guess}

        return self._get_state(), reward, False, info

    def render(self) -> str:
        """Render game state."""
        return f"Range: [{self.low}, {self.high}] | Attempt: {self.attempt}/{self.max_attempts}"
