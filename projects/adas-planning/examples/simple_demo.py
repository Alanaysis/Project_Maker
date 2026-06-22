"""
Simple Demo - Basic ADAS Planning and Control
===============================================

This script demonstrates the basic functionality of the ADAS planning system:
1. Create a grid map with obstacles
2. Plan a path using A*
3. Generate a smooth trajectory
4. Track the trajectory using PID control
5. Visualize the results

Usage:
    python simple_demo.py
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.environment import GridMap, SimulationEnvironment
from src.planner import AStarPlanner
from src.controller import PIDController
from src.trajectory import Trajectory, TrajectoryGenerator
from src.visualization import Visualizer


def main():
    print("=" * 60)
    print("ADAS Planning and Control - Simple Demo")
    print("=" * 60)

    # Step 1: Create grid map
    print("\n[1] Creating grid map...")
    grid_map = GridMap(30, 30)

    # Add some obstacles
    obstacles = [
        # Wall in the middle
        (15, y) for y in range(5, 25)
    ]
    for x, y in obstacles:
        grid_map.add_obstacle(x, y)

    # Add a gap in the wall
    grid_map.remove_obstacle(15, 15)

    print(f"  Map size: {grid_map.width} x {grid_map.height}")
    print(f"  Obstacles: {np.sum(grid_map.grid == 1)}")

    # Step 2: Plan path using A*
    print("\n[2] Planning path using A*...")
    planner = AStarPlanner(allow_diagonal=True)

    start = (2, 15)
    goal = (27, 15)

    path = planner.plan(grid_map, start, goal)

    if path is None:
        print("  ERROR: No path found!")
        return

    print(f"  Path found with {len(path)} points")
    print(f"  Nodes explored: {planner.nodes_explored}")

    # Step 3: Generate smooth trajectory
    print("\n[3] Generating smooth trajectory...")
    generator = TrajectoryGenerator(ds=1.0)

    waypoints = [(float(p[0]), float(p[1])) for p in path]
    trajectory = generator.generate(waypoints, target_velocity=5.0)

    print(f"  Trajectory points: {len(trajectory)}")
    print(f"  Trajectory length: {trajectory.get_length():.2f} m")

    # Step 4: Simulate trajectory tracking
    print("\n[4] Simulating trajectory tracking with PID...")
    environment = SimulationEnvironment(
        grid_map=grid_map,
        start=start,
        goal=goal,
        dt=0.1
    )

    controller = PIDController(
        Kp=1.0,
        Ki=0.01,
        Kd=0.5,
        output_limits=(-np.pi / 4, np.pi / 4)
    )

    # Data recording
    timestamps = []
    positions = []
    speeds = []
    errors = []
    steerings = []

    current_time = 0.0
    max_time = 100.0
    goal_threshold = 2.0

    while current_time < max_time:
        # Get current state
        pos = environment.vehicle_position
        heading = environment.vehicle_heading
        speed = environment.vehicle_speed

        # Find nearest point on trajectory
        nearest_idx = trajectory.get_nearest_index(pos[0], pos[1])
        nearest_point = trajectory.get_point(nearest_idx)

        # Compute cross-track error
        dx = nearest_point.x - pos[0]
        dy = nearest_point.y - pos[1]
        path_heading = nearest_point.heading
        cross_track_error = -dx * np.sin(path_heading) + dy * np.cos(path_heading)

        # Compute heading error
        heading_error = path_heading - heading
        heading_error = np.arctan2(np.sin(heading_error), np.cos(heading_error))

        # Combined error
        error = cross_track_error + 0.3 * heading_error

        # PID control for steering
        steering = controller.compute(error, 0.1)

        # Speed control
        target_speed = trajectory.get_point(
            min(nearest_idx + 5, len(trajectory) - 1)
        ).velocity
        speed_error = target_speed - speed
        acceleration = 0.5 * speed_error

        # Apply limits
        steering = np.clip(steering, -np.pi / 4, np.pi / 4)
        acceleration = np.clip(acceleration, -3.0, 2.0)

        # Execute step
        environment.step(steering, acceleration)

        # Compute tracking error
        tracking_error = np.sqrt(dx ** 2 + dy ** 2)

        # Record data
        timestamps.append(current_time)
        positions.append(pos.copy())
        speeds.append(speed)
        errors.append(tracking_error)
        steerings.append(steering)

        # Check termination
        if environment.is_goal_reached(goal_threshold):
            print(f"  Goal reached at t={current_time:.2f}s!")
            break

        if environment.is_collision():
            print(f"  Collision at t={current_time:.2f}s!")
            break

        current_time += 0.1

    # Compute statistics
    avg_error = np.mean(errors) if errors else 0
    max_error = np.max(errors) if errors else 0
    print(f"\n  Simulation time: {current_time:.2f}s")
    print(f"  Average tracking error: {avg_error:.3f}m")
    print(f"  Maximum tracking error: {max_error:.3f}m")

    # Step 5: Visualize results
    print("\n[5] Visualizing results...")
    visualizer = Visualizer(figsize=(14, 10))

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("ADAS Planning and Control Demo", fontsize=14)

    # Plot 1: Map and path
    ax1 = axes[0, 0]
    visualizer.plot_grid_map(grid_map, ax=ax1, show_grid=False)
    visualizer.plot_path(path, ax=ax1, color='blue', label='A* Path')
    positions_array = np.array(positions)
    ax1.plot(positions_array[:, 0], positions_array[:, 1], 'r-', linewidth=1.5,
            label='Vehicle Path', alpha=0.7)
    ax1.plot(*start, 'go', markersize=10, label='Start')
    ax1.plot(*goal, 'r*', markersize=15, label='Goal')
    ax1.legend()
    ax1.set_title('Path Planning')

    # Plot 2: Velocity profile
    ax2 = axes[0, 1]
    ax2.plot(timestamps, speeds, 'b-', linewidth=2)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Speed (m/s)')
    ax2.set_title('Velocity Profile')
    ax2.grid(True)

    # Plot 3: Tracking error
    ax3 = axes[1, 0]
    ax3.plot(timestamps, errors, 'r-', linewidth=2)
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Tracking Error (m)')
    ax3.set_title('Tracking Error')
    ax3.grid(True)

    # Plot 4: Steering angle
    ax4 = axes[1, 1]
    ax4.plot(timestamps, np.degrees(steerings), 'g-', linewidth=2)
    ax4.set_xlabel('Time (s)')
    ax4.set_ylabel('Steering Angle (deg)')
    ax4.set_title('Steering Command')
    ax4.grid(True)

    plt.tight_layout()
    plt.savefig('demo_result.png', dpi=150, bbox_inches='tight')
    print("  Saved demo_result.png")

    plt.show()

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
