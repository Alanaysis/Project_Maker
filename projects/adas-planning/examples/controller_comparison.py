"""
Controller Comparison Demo
==========================

This script compares different trajectory tracking controllers:
- PID Controller
- Stanley Controller

Usage:
    python controller_comparison.py
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.environment import GridMap, SimulationEnvironment
from src.planner import AStarPlanner
from src.controller import PIDController, StanleyController
from src.trajectory import Trajectory, TrajectoryGenerator
from src.visualization import Visualizer


def run_simulation(grid_map, start, goal, trajectory, controller_type="pid"):
    """Run simulation with specified controller."""
    print(f"\nRunning simulation with {controller_type.upper()} controller...")

    # Create environment
    environment = SimulationEnvironment(
        grid_map=grid_map,
        start=start,
        goal=goal,
        dt=0.1
    )

    # Create controller
    if controller_type == "pid":
        controller = PIDController(
            Kp=1.0, Ki=0.01, Kd=0.5,
            output_limits=(-np.pi / 4, np.pi / 4)
        )
    elif controller_type == "stanley":
        controller = StanleyController(k=1.0)
    else:
        raise ValueError(f"Unknown controller type: {controller_type}")

    # Data recording
    timestamps = []
    positions = []
    headings = []
    speeds = []
    errors = []
    steerings = []

    current_time = 0.0
    max_time = 150.0
    goal_threshold = 2.0

    while current_time < max_time:
        # Get current state
        pos = environment.vehicle_position
        heading = environment.vehicle_heading
        speed = environment.vehicle_speed

        # Find nearest point on trajectory
        nearest_idx = trajectory.get_nearest_index(pos[0], pos[1])
        nearest_point = trajectory.get_point(nearest_idx)

        # Compute tracking error
        dx = nearest_point.x - pos[0]
        dy = nearest_point.y - pos[1]
        tracking_error = np.sqrt(dx ** 2 + dy ** 2)

        # Compute control
        if controller_type == "pid":
            # Compute cross-track error
            path_heading = nearest_point.heading
            cross_track_error = -dx * np.sin(path_heading) + dy * np.cos(path_heading)

            # Compute heading error
            heading_error = path_heading - heading
            heading_error = np.arctan2(np.sin(heading_error), np.cos(heading_error))

            # Combined error
            error = cross_track_error + 0.3 * heading_error

            # PID control
            steering = controller.compute(error, 0.1)

            # Speed control
            target_speed = trajectory.get_point(
                min(nearest_idx + 5, len(trajectory) - 1)
            ).velocity
            speed_error = target_speed - speed
            acceleration = 0.5 * speed_error

        elif controller_type == "stanley":
            # Get path points as numpy arrays
            path_points = trajectory.get_positions()

            # Stanley control
            steering = controller.compute_steering_angle(
                pos, heading, path_points, speed
            )

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

        # Record data
        timestamps.append(current_time)
        positions.append(pos.copy())
        headings.append(heading)
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
    total_time = current_time

    print(f"  Simulation time: {total_time:.2f}s")
    print(f"  Average tracking error: {avg_error:.3f}m")
    print(f"  Maximum tracking error: {max_error:.3f}m")

    return {
        'timestamps': timestamps,
        'positions': positions,
        'headings': headings,
        'speeds': speeds,
        'errors': errors,
        'steerings': steerings,
        'avg_error': avg_error,
        'max_error': max_error,
        'total_time': total_time,
        'success': environment.is_goal_reached(goal_threshold)
    }


def main():
    print("=" * 60)
    print("ADAS Planning - Controller Comparison")
    print("=" * 60)

    # Create grid map
    print("\n[1] Creating grid map...")
    np.random.seed(42)
    grid_map = GridMap(40, 40, obstacle_density=0.2, seed=42)

    start = (2, 20)
    goal = (37, 20)

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

    # Plan path
    print("\n[2] Planning path...")
    planner = AStarPlanner(allow_diagonal=True)
    path = planner.plan(grid_map, start, goal)

    if path is None:
        print("  ERROR: No path found!")
        return

    print(f"  Path found with {len(path)} points")

    # Generate smooth trajectory
    print("\n[3] Generating trajectory...")
    generator = TrajectoryGenerator(ds=1.0)
    waypoints = [(float(p[0]), float(p[1])) for p in path]
    trajectory = generator.generate(waypoints, target_velocity=5.0)
    print(f"  Trajectory points: {len(trajectory)}")

    # Run simulations
    print("\n[4] Running simulations...")
    results = {}
    results['PID'] = run_simulation(grid_map, start, goal, trajectory, "pid")
    results['Stanley'] = run_simulation(grid_map, start, goal, trajectory, "stanley")

    # Print comparison
    print("\n" + "=" * 60)
    print("Comparison Results:")
    print("=" * 60)
    print(f"{'Controller':<15} {'Success':<10} {'Time (s)':<12} {'Avg Error':<12} {'Max Error':<12}")
    print("-" * 60)

    for name, r in results.items():
        print(f"{name:<15} {str(r['success']):<10} {r['total_time']:<12.2f} "
              f"{r['avg_error']:<12.3f} {r['max_error']:<12.3f}")

    # Visualize results
    print("\n[5] Visualizing results...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Controller Comparison: PID vs Stanley", fontsize=14)

    # Plot 1: Paths
    ax1 = axes[0, 0]
    visualizer = Visualizer()
    visualizer.plot_grid_map(grid_map, ax=ax1, show_grid=False, alpha=0.3)

    path_array = np.array(path)
    ax1.plot(path_array[:, 0], path_array[:, 1], 'b-', linewidth=2, label='Planned Path')

    for name, r in results.items():
        positions = np.array(r['positions'])
        ax1.plot(positions[:, 0], positions[:, 1], linewidth=1.5, label=f'{name} Path', alpha=0.7)

    ax1.plot(*start, 'go', markersize=10, label='Start')
    ax1.plot(*goal, 'r*', markersize=15, label='Goal')
    ax1.legend()
    ax1.set_title('Trajectory Comparison')
    ax1.set_aspect('equal')

    # Plot 2: Tracking errors
    ax2 = axes[0, 1]
    for name, r in results.items():
        ax2.plot(r['timestamps'], r['errors'], linewidth=2, label=name)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Tracking Error (m)')
    ax2.set_title('Tracking Error Comparison')
    ax2.legend()
    ax2.grid(True)

    # Plot 3: Steering commands
    ax3 = axes[1, 0]
    for name, r in results.items():
        ax3.plot(r['timestamps'], np.degrees(r['steerings']), linewidth=2, label=name)
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Steering Angle (deg)')
    ax3.set_title('Steering Command Comparison')
    ax3.legend()
    ax3.grid(True)

    # Plot 4: Speed profiles
    ax4 = axes[1, 1]
    for name, r in results.items():
        ax4.plot(r['timestamps'], r['speeds'], linewidth=2, label=name)
    ax4.set_xlabel('Time (s)')
    ax4.set_ylabel('Speed (m/s)')
    ax4.set_title('Speed Profile Comparison')
    ax4.legend()
    ax4.grid(True)

    plt.tight_layout()
    plt.savefig('controller_comparison.png', dpi=150, bbox_inches='tight')
    print("  Saved controller_comparison.png")

    plt.show()

    print("\n" + "=" * 60)
    print("Comparison completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
