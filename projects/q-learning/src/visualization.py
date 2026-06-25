"""Visualization utilities for Q-Learning.

Provides functions to visualize training progress, learned policies,
Q-value landscapes, and algorithm comparisons.
"""

from typing import Optional
import numpy as np


# Action symbols for display
ACTION_SYMBOLS = {0: "↑", 1: "→", 2: "↓", 3: "←"}

# Cell type labels
CELL_LABELS = {0: ".", 1: "#", 2: "G", 3: "X"}


def visualize_q_table_heatmap(
    q_table: np.ndarray,
    rows: int,
    cols: int,
    title: str = "Q-Table Heatmap",
) -> str:
    """Create a text-based heatmap of Q-values.

    Args:
        q_table: Q-value table (n_states x n_actions).
        rows: Number of rows in grid.
        cols: Number of columns in grid.
        title: Title for visualization.

    Returns:
        String with ASCII heatmap.
    """
    # Get max Q-value for each state
    max_q = np.max(q_table, axis=1)
    min_q = np.min(q_table, axis=1)
    avg_q = np.mean(q_table, axis=1)

    lines = []
    lines.append("=" * 50)
    lines.append(title)
    lines.append("=" * 50)
    lines.append("")

    # Heatmap for max Q-values
    lines.append("Max Q-Value Heatmap:")
    intensity_chars = " .:-=+*#%@"

    for r in range(rows):
        row_str = []
        for c in range(cols):
            state_idx = r * cols + c
            val = max_q[state_idx]

            # Normalize to 0-1
            all_max = np.max(max_q)
            all_min = np.min(max_q)
            if all_max > all_min:
                normalized = (val - all_min) / (all_max - all_min)
            else:
                normalized = 0.5

            char_idx = int(normalized * (len(intensity_chars) - 1))
            char_idx = max(0, min(len(intensity_chars) - 1, char_idx))
            row_str.append(f"[{intensity_chars[char_idx]}]")
        lines.append(" ".join(row_str))

    lines.append("")
    lines.append(f"Q-value range: [{np.min(q_table):.2f}, {np.max(q_table):.2f}]")
    lines.append("=" * 50)

    return "\n".join(lines)


def visualize_learning_curves(
    curves: dict[str, list[float]],
    window: int = 50,
    title: str = "Learning Curves Comparison",
) -> str:
    """Compare learning curves of different algorithms.

    Args:
        curves: Dict mapping algorithm names to reward lists.
        window: Window size for moving average.
        title: Title for visualization.

    Returns:
        String with ASCII comparison plot.
    """
    lines = []
    lines.append("=" * 60)
    lines.append(title)
    lines.append("=" * 60)
    lines.append("")

    # Statistics for each algorithm
    lines.append("Algorithm Comparison:")
    lines.append("-" * 60)
    lines.append(f"{'Algorithm':<20} {'Final Avg':<15} {'Best':<15} {'Converged':<10}")
    lines.append("-" * 60)

    for name, rewards in curves.items():
        if len(rewards) >= window:
            final_avg = np.mean(rewards[-window:])
            best = max(rewards)
            # Simple convergence check
            if len(rewards) >= 2 * window:
                recent = np.mean(rewards[-window:])
                older = np.mean(rewards[-2 * window:-window])
                converged = abs(recent - older) < 0.05
            else:
                converged = False
            lines.append(f"{name:<20} {final_avg:<15.1f} {best:<15.1f} {'Yes' if converged else 'No':<10}")
        else:
            lines.append(f"{name:<20} {'N/A':<15} {'N/A':<15} {'N/A':<10}")

    lines.append("-" * 60)

    # ASCII plot comparison
    lines.append("")
    lines.append("Learning Curves (moving average):")
    lines.append("")

    # Find global min/max for scaling
    all_values = []
    for rewards in curves.values():
        if len(rewards) >= window:
            all_values.extend(_moving_average(rewards, window))

    if not all_values:
        lines.append("  No data to plot")
        return "\n".join(lines)

    vmin, vmax = min(all_values), max(all_values)

    # Simple ASCII plot for each algorithm
    symbols = ["*", "+", "x", "o", "#"]
    for i, (name, rewards) in enumerate(curves.items()):
        if len(rewards) >= window:
            avg = _moving_average(rewards, window)
            # Show last 50 values
            display = avg[-50:] if len(avg) > 50 else avg
            symbol = symbols[i % len(symbols)]
            line = f"  {symbol} {name}: "
            for val in display:
                if vmax > vmin:
                    intensity = int((val - vmin) / (vmax - vmin) * 5)
                else:
                    intensity = 3
                line += "▁▂▃▄▅"[min(4, max(0, intensity))]
            lines.append(line)

    lines.append("")
    lines.append("Legend: " + ", ".join(f"{symbols[i % len(symbols)]}={name}" for i, name in enumerate(curves.keys())))
    lines.append("=" * 60)

    return "\n".join(lines)


def visualize_strategy_comparison(
    results: dict[str, dict],
    title: str = "Strategy Comparison",
) -> str:
    """Compare different exploration strategies.

    Args:
        results: Dict mapping strategy names to result dicts.
        title: Title for visualization.

    Returns:
        String with comparison table.
    """
    lines = []
    lines.append("=" * 70)
    lines.append(title)
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"{'Strategy':<20} {'Success Rate':<15} {'Avg Reward':<15} {'Avg Steps':<15}")
    lines.append("-" * 70)

    for name, metrics in results.items():
        success = metrics.get("success_rate", 0)
        reward = metrics.get("mean_reward", 0)
        steps = metrics.get("mean_steps", 0)
        lines.append(f"{name:<20} {success:<15.1%} {reward:<15.1f} {steps:<15.1f}")

    lines.append("-" * 70)
    lines.append("=" * 70)

    return "\n".join(lines)


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
