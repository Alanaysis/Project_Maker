"""
Algorithm Comparison Demo
=========================

This script compares different path planning algorithms:
- A* with different heuristics
- Dijkstra's algorithm
- RRT

Usage:
    python algorithm_comparison.py
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.environment import GridMap
from src.planner import AStarPlanner, DijkstraPlanner, RRTPlanner
from src.visualization import Visualizer


def run_planner(planner, grid_map, start, goal, name):
    """Run a planner and collect metrics."""
    print(f"\nRunning {name}...")

    start_time = time.time()
    path = planner.plan(grid_map, start, goal)
    elapsed_time = time.time() - start_time

    result = {
        'name': name,
        'path': path,
        'time': elapsed_time,
        'nodes_explored': getattr(planner, 'nodes_explored', 0),
        'path_length': 0,
        'success': path is not None
    }

    if path:
        # Calculate path length
        total_length = 0
        for i in range(len(path) - 1):
            dx = path[i + 1][0] - path[i][0]
            dy = path[i + 1][1] - path[i][1]
            total_length += np.sqrt(dx * dx + dy * dy)
        result['path_length'] = total_length
        print(f"  Path found: {len(path)} points, length={total_length:.2f}")
    else:
        print(f"  No path found")

    print(f"  Time: {elapsed_time:.4f}s")
    print(f"  Nodes explored: {result['nodes_explored']}")

    return result


def main():
    print("=" * 60)
    print("ADAS Planning - Algorithm Comparison")
    print("=" * 60)

    # Create grid map
    print("\n[1] Creating grid map...")
    np.random.seed(42)
    grid_map = GridMap(50, 50, obstacle_density=0.25, seed=42)

    # Ensure start and goal are free
    start = (5, 5)
    goal = (45, 45)

    # Clear area around start and goal
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            sx, sy = start[0] + dx, start[1] + dy
            gx, gy = goal[0] + dx, goal[1] + dy
            if grid_map.in_bounds(sx, sy):
                grid_map.remove_obstacle(sx, sy)
            if grid_map.in_bounds(gx, gy):
                grid_map.remove_obstacle(gx, gy)

    print(f"  Map size: {grid_map.width}x{grid_map.height}")
    print(f"  Obstacles: {np.sum(grid_map.grid == 1)}")
    print(f"  Start: {start}, Goal: {goal}")

    # Run different planners
    print("\n[2] Running planners...")
    results = []

    # A* with Manhattan heuristic
    planner = AStarPlanner(allow_diagonal=False, heuristic_type="manhattan")
    results.append(run_planner(planner, grid_map, start, goal, "A* (Manhattan)"))

    # A* with Euclidean heuristic
    planner = AStarPlanner(allow_diagonal=False, heuristic_type="euclidean")
    results.append(run_planner(planner, grid_map, start, goal, "A* (Euclidean)"))

    # A* with diagonal movement
    planner = AStarPlanner(allow_diagonal=True, heuristic_type="euclidean")
    results.append(run_planner(planner, grid_map, start, goal, "A* (Diagonal)"))

    # Dijkstra
    planner = DijkstraPlanner(allow_diagonal=True)
    results.append(run_planner(planner, grid_map, start, goal, "Dijkstra"))

    # RRT
    planner = RRTPlanner(max_iterations=5000, step_size=3.0)
    results.append(run_planner(planner, grid_map, start, goal, "RRT"))

    # Print comparison table
    print("\n" + "=" * 60)
    print("Comparison Results:")
    print("=" * 60)
    print(f"{'Algorithm':<20} {'Success':<10} {'Path Length':<15} {'Time (s)':<12} {'Nodes':<10}")
    print("-" * 60)

    for r in results:
        print(f"{r['name']:<20} {str(r['success']):<10} {r['path_length']:<15.2f} "
              f"{r['time']:<12.4f} {r['nodes_explored']:<10}")

    # Visualize results
    print("\n[3] Visualizing results...")
    visualizer = Visualizer(figsize=(15, 12))

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle("Path Planning Algorithm Comparison", fontsize=14)

    # Flatten axes for easier indexing
    axes_flat = axes.flatten()

    for idx, result in enumerate(results):
        if idx >= len(axes_flat):
            break

        ax = axes_flat[idx]

        # Plot grid map
        visualizer.plot_grid_map(grid_map, ax=ax, show_grid=False, alpha=0.3)

        # Plot path if found
        if result['path']:
            path_array = np.array(result['path'])
            ax.plot(path_array[:, 0], path_array[:, 1], 'b-', linewidth=2,
                   label=f"Path ({len(result['path'])} pts)")
            ax.plot(path_array[0, 0], path_array[0, 1], 'go', markersize=10)
            ax.plot(path_array[-1, 0], path_array[-1, 1], 'r*', markersize=15)

        ax.set_title(f"{result['name']}\nTime: {result['time']:.4f}s")
        ax.legend(loc='upper right', fontsize=8)
        ax.set_aspect('equal')

    # Plot performance comparison in last subplot
    ax = axes_flat[5]
    algorithms = [r['name'] for r in results]
    times = [r['time'] for r in results]
    path_lengths = [r['path_length'] for r in results]

    x = np.arange(len(algorithms))
    width = 0.35

    ax2 = ax.twinx()
    bars1 = ax.bar(x - width / 2, times, width, label='Time (s)', color='skyblue')
    bars2 = ax2.bar(x + width / 2, path_lengths, width, label='Path Length', color='lightcoral')

    ax.set_xlabel('Algorithm')
    ax.set_ylabel('Time (s)', color='skyblue')
    ax2.set_ylabel('Path Length', color='lightcoral')
    ax.set_title('Performance Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(algorithms, rotation=45, ha='right')
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig('algorithm_comparison.png', dpi=150, bbox_inches='tight')
    print("  Saved algorithm_comparison.png")

    plt.show()

    print("\n" + "=" * 60)
    print("Comparison completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
