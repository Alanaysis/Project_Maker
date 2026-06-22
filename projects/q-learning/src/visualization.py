"""Visualization utilities for Q-Learning.

Provides functions to visualize training progress, learned policies,
and Q-value landscapes.
"""

from typing import Optional
import numpy as np


# Action symbols for display
ACTION_SYMBOLS = {0: "↑", 1: "→", 2: "↓", 3: "←"}

# Cell type labels
CELL_LABELS = {0: ".", 1: "#", 2: "G", 3: "X"}


def visualize_training(rewards: list[float], steps: list[int], window: int = 50) -> str:
    """Create a text-based visualization of training progress.

    Args:
        rewards: List of episode rewards.
        steps: List of episode steps.
        window: Window size for moving average.

    Returns:
        String with ASCII visualization of training progress.
    """
    if len(rewards) < window:
        window = max(1, len(rewards) // 2)

    # Calculate moving averages
    avg_rewards = _moving_average(rewards, window)
    avg_steps = _moving_average(steps, window)

    lines = []
    lines.append("=" * 60)
    lines.append("TRAINING PROGRESS")
    lines.append("=" * 60)
    lines.append("")

    # Reward plot
    lines.append("Episode Rewards (moving average):")
    lines.append(_ascii_plot(avg_rewards, width=50, height=10))
    lines.append("")

    # Steps plot
    lines.append("Episode Steps (moving average):")
    lines.append(_ascii_plot(avg_steps, width=50, height=10))
    lines.append("")

    # Statistics
    lines.append("-" * 40)
    lines.append("Training Statistics:")
    lines.append(f"  Total Episodes: {len(rewards)}")
    lines.append(f"  Best Reward:    {max(rewards):.1f}")
    lines.append(f"  Worst Reward:   {min(rewards):.1f}")
    lines.append(f"  Final Avg (last {window}): {np.mean(rewards[-window:]):.1f}")
    lines.append(f"  Final Steps (last {window}): {np.mean(steps[-window:]):.1f}")
    lines.append("=" * 60)

    return "\n".join(lines)


def visualize_policy(
    grid: np.ndarray,
    policy: np.ndarray,
    start: tuple[int, int],
    goal: tuple[int, int],
    title: str = "Learned Policy",
) -> str:
    """Create a text-based visualization of the learned policy.

    Args:
        grid: 2D array representing the grid (0=empty, 1=wall, 2=goal, 3=trap).
        policy: 2D array of actions.
        start: Starting position.
        goal: Goal position.
        title: Title for the visualization.

    Returns:
        String with ASCII visualization of the policy.
    """
    rows, cols = grid.shape
    lines = []
    lines.append("=" * 40)
    lines.append(title)
    lines.append("=" * 40)
    lines.append("")

    for r in range(rows):
        row_str = []
        for c in range(cols):
            if r == start[0] and c == start[1]:
                row_str.append(" S ")
            elif r == goal[0] and c == goal[1]:
                row_str.append(" G ")
            elif grid[r, c] == 1:  # Wall
                row_str.append(" # ")
            elif grid[r, c] == 3:  # Trap
                row_str.append(" X ")
            else:
                action = policy[r, c]
                symbol = ACTION_SYMBOLS.get(action, "?")
                row_str.append(f" {symbol} ")
        lines.append("".join(row_str))

    lines.append("")
    lines.append("Legend: S=Start, G=Goal, #=Wall, X=Trap")
    lines.append("Arrows show best action in each state")
    lines.append("=" * 40)

    return "\n".join(lines)


def visualize_q_values(
    grid: np.ndarray,
    value_map: np.ndarray,
    start: tuple[int, int],
    goal: tuple[int, int],
    title: str = "Q-Value Map",
) -> str:
    """Create a text-based visualization of Q-values.

    Args:
        grid: 2D array representing the grid.
        value_map: 2D array of maximum Q-values.
        start: Starting position.
        goal: Goal position.
        title: Title for the visualization.

    Returns:
        String with ASCII visualization of Q-values.
    """
    rows, cols = grid.shape
    lines = []
    lines.append("=" * 50)
    lines.append(title)
    lines.append("=" * 50)
    lines.append("")

    # Find min and max values for scaling
    valid_values = value_map[grid != 1]
    if len(valid_values) > 0:
        vmin = np.min(valid_values)
        vmax = np.max(valid_values)
    else:
        vmin, vmax = -1, 1

    # Create heatmap
    intensity_chars = " .:-=+*#%@"

    for r in range(rows):
        row_str = []
        for c in range(cols):
            if r == start[0] and c == start[1]:
                row_str.append("[S] ")
            elif r == goal[0] and c == goal[1]:
                row_str.append("[G] ")
            elif grid[r, c] == 1:
                row_str.append("[#] ")
            elif grid[r, c] == 3:
                row_str.append("[X] ")
            else:
                val = value_map[r, c]
                if vmax > vmin:
                    normalized = (val - vmin) / (vmax - vmin)
                else:
                    normalized = 0.5
                char_idx = int(normalized * (len(intensity_chars) - 1))
                char_idx = max(0, min(len(intensity_chars) - 1, char_idx))
                char = intensity_chars[char_idx]
                row_str.append(f"[{char}] ")
        lines.append("".join(row_str))

    lines.append("")
    lines.append(f"Q-value range: [{vmin:.1f}, {vmax:.1f}]")
    lines.append("Higher intensity = higher Q-value")
    lines.append("=" * 50)

    return "\n".join(lines)


def visualize_episode_path(
    grid: np.ndarray,
    path: list[tuple[int, int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    title: str = "Episode Path",
) -> str:
    """Visualize the path taken during an episode.

    Args:
        grid: 2D array representing the grid.
        path: List of (row, col) positions visited.
        start: Starting position.
        goal: Goal position.
        title: Title for the visualization.

    Returns:
        String with ASCII visualization of the path.
    """
    rows, cols = grid.shape
    lines = []
    lines.append("=" * 40)
    lines.append(title)
    lines.append("=" * 40)
    lines.append("")

    # Create path markers
    path_set = set(path)

    for r in range(rows):
        row_str = []
        for c in range(cols):
            if r == start[0] and c == start[1]:
                row_str.append(" S ")
            elif r == goal[0] and c == goal[1]:
                row_str.append(" G ")
            elif grid[r, c] == 1:
                row_str.append(" # ")
            elif grid[r, c] == 3:
                row_str.append(" X ")
            elif (r, c) in path_set:
                row_str.append(" * ")
            else:
                row_str.append(" . ")
        lines.append("".join(row_str))

    lines.append("")
    lines.append(f"Path length: {len(path)} steps")
    lines.append("Legend: *=visited path")
    lines.append("=" * 40)

    return "\n".join(lines)


def _moving_average(data: list[float], window: int) -> list[float]:
    """Calculate moving average.

    Args:
        data: Input data.
        window: Window size.

    Returns:
        List of moving averages.
    """
    if len(data) < window:
        return [np.mean(data)]

    result = []
    for i in range(window - 1, len(data)):
        result.append(np.mean(data[i - window + 1 : i + 1]))
    return result


def _ascii_plot(
    data: list[float], width: int = 50, height: int = 10
) -> str:
    """Create an ASCII plot of data.

    Args:
        data: Data to plot.
        width: Width of the plot.
        height: Height of the plot.

    Returns:
        String with ASCII plot.
    """
    if not data:
        return "  No data to plot"

    # Resample data to fit width
    if len(data) > width:
        indices = np.linspace(0, len(data) - 1, width, dtype=int)
        sampled = [data[i] for i in indices]
    else:
        sampled = data
        width = len(sampled)

    # Normalize to height
    vmin = min(sampled)
    vmax = max(sampled)

    if vmax == vmin:
        normalized = [0.5] * len(sampled)
    else:
        normalized = [(v - vmin) / (vmax - vmin) for v in sampled]

    # Create plot grid
    grid = [[" " for _ in range(width)] for _ in range(height)]

    for x, y_val in enumerate(normalized):
        y = int(y_val * (height - 1))
        y = max(0, min(height - 1, y))
        grid[height - 1 - y][x] = "█"

    # Build string
    lines = []
    lines.append(f"  max: {vmax:.1f}")
    for row in grid:
        lines.append("  │" + "".join(row))
    lines.append("  └" + "─" * width)
    lines.append(f"  min: {vmin:.1f}")

    return "\n".join(lines)
