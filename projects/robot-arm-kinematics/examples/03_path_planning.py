"""
Example 3: Path Planning Demo / 路径规划演示

This example demonstrates:
1. Cartesian linear interpolation with IK
2. Waypoint following
3. Trajectory smoothing (cubic/quintic blending)
4. Path length optimization

Learning objectives:
- Understand path planning in Cartesian vs joint space
- See the difference between linear and smooth trajectories
- Learn about IK feasibility along paths
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.forward_kinematics import ForwardKinematics
from src.inverse_kinematics import ik_numerical
from src.jacobian import Jacobian
from src.mapping import (
    linear_joint_trajectory,
    cubic_joint_trajectory,
    quintic_joint_trajectory,
    cartesian_linear_path,
    generate_waypoint_path,
    compute_path_length,
)
import matplotlib.pyplot as plt


def demo_cartesian_linear_path():
    """Demonstrate Cartesian linear path planning."""
    print("=" * 60)
    print("Example 3a: Cartesian Linear Path / 笛卡尔直线路径")
    print("=" * 60)

    # Define a 3R arm
    l1, l2, l3 = 100, 80, 60
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': l2,   'alpha': 0,    'd': 0,    'theta': 0},
        {'a': l3,   'alpha': 0,    'd': 0,    'theta': 0},
    ]

    fk = ForwardKinematics(link_params, 'modified')
    jac = Jacobian(link_params, 'modified')

    # Start and end configurations
    q_start = np.array([0, np.pi/4, -np.pi/4])
    q_end = np.array([np.pi/4, 0, np.pi/4])

    n_points = 50

    # Cartesian linear path (requires IK at each point)
    print("\n--- Cartesian Linear Path Planning ---")
    q_cartesian, poses = cartesian_linear_path(fk, q_start, q_end, n_points)

    if len(q_cartesian) > 0:
        print(f"Cartesian path: {len(q_cartesian)} waypoints")
        print(f"Start pose: ({poses[0][:3, 3][0]:.1f}, {poses[0][:3, 3][1]:.1f}) mm")
        print(f"End pose: ({poses[-1][:3, 3][0]:.1f}, {poses[-1][:3, 3][1]:.1f}) mm")
        path_length = compute_path_length(poses)
        print(f"Path length: {path_length:.1f} mm")

        # Check Jacobian condition along path
        print("\n  Waypoint | Position (x,y) | Condition # | Manipulability")
        print("  " + "-" * 65)
        for i in range(0, len(q_cartesian), max(1, len(q_cartesian)//10)):
            q = q_cartesian[i]
            pos = fk.get_position(q)
            cond = jac.compute_singularity_index(q)
            manip = jac.compute_manipulability(q)
            print(f"  {i:>8} | ({pos[0]:>7.1f}, {pos[1]:>7.1f})    | {cond:>13.2f} | {manip:>14.2f}")

    # Joint space linear path (no IK needed)
    print("\n--- Joint Space Linear Path ---")
    q_joint = linear_joint_trajectory(q_start, q_end, n_points)
    positions = [fk.get_position(q) for q in q_joint]

    print(f"Joint path: {len(q_joint)} waypoints")
    print(f"Start position: ({positions[0][0]:.1f}, {positions[0][1]:.1f}) mm")
    print(f"End position: ({positions[-1][0]:.1f}, {positions[-1][1]:.1f}) mm")


def demo_trajectory_smoothing():
    """Demonstrate trajectory smoothing with cubic and quintic polynomials."""
    print("\n" + "=" * 60)
    print("Example 3b: Trajectory Smoothing / 轨迹平滑")
    print("=" * 60)

    q_start = np.array([0, 0, 0])
    q_end = np.array([np.pi/3, -np.pi/4, np.pi/6])
    n_points = 100

    # Generate different trajectories
    q_linear = linear_joint_trajectory(q_start, q_end, n_points)
    q_cubic = cubic_joint_trajectory(q_start, q_end, n_points)
    q_quintic = quintic_joint_trajectory(q_start, q_end, n_points)

    # Compute velocities and accelerations
    dt = 1.0 / (n_points - 1)

    v_linear = np.diff(q_linear, axis=0) / dt
    v_cubic = np.diff(q_cubic, axis=0) / dt
    v_quintic = np.diff(q_quintic, axis=0) / dt

    a_linear = np.diff(v_linear, axis=0)
    a_cubic = np.diff(v_cubic, axis=0)
    a_quintic = np.diff(v_quintic, axis=0)

    print("\n  Trajectory | Max Velocity | Max Acceleration | Smoothness")
    print("  " + "-" * 60)
    print(f"  Linear     | {np.max(np.linalg.norm(v_linear, axis=1)):.4f}     | {np.max(np.linalg.norm(a_linear, axis=1)):.4f}       | Poor")
    print(f"  Cubic      | {np.max(np.linalg.norm(v_cubic, axis=1)):.4f}     | {np.max(np.linalg.norm(a_cubic, axis=1)):.4f}       | Good")
    print(f"  Quintic    | {np.max(np.linalg.norm(v_quintic, axis=1)):.4f}     | {np.max(np.linalg.norm(a_quintic, axis=1)):.4f}       | Best")

    # Visualize
    t = np.linspace(0, 1, n_points)
    t_acc = np.linspace(0, 1, n_points - 1)

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    # Position
    for i in range(3):
        axes[0].plot(t, q_linear[:, i], '--', alpha=0.5, label=f'Joint {i+1} (Linear)')
        axes[0].plot(t, q_cubic[:, i], '-', label=f'Joint {i+1} (Cubic)')
    axes[0].set_ylabel('Joint Angle (rad)')
    axes[0].set_title('Position Profiles / 位置曲线')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Velocity
    for i in range(3):
        axes[1].plot(t_acc, v_cubic[:, i], '-', label=f'Joint {i+1}')
    axes[1].set_ylabel('Velocity (rad/s)')
    axes[1].set_title('Velocity Profiles / 速度曲线')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Acceleration
    for i in range(3):
        axes[2].plot(t_acc, a_cubic[:, i], '-', label=f'Joint {i+1}')
    axes[2].set_ylabel('Acceleration (rad/s²)')
    axes[2].set_xlabel('Time (normalized)')
    axes[2].set_title('Acceleration Profiles / 加速度曲线')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    fig.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'trajectory_smoothing.png')
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nTrajectory plot saved to outputs/trajectory_smoothing.png")
    plt.close(fig)


def demo_waypoint_path():
    """Demonstrate waypoint-based path planning."""
    print("\n" + "=" * 60)
    print("Example 3c: Waypoint Path Planning / 路径点规划")
    print("=" * 60)

    l1, l2, l3 = 100, 80, 60
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': l2,   'alpha': 0,    'd': 0,    'theta': 0},
        {'a': l3,   'alpha': 0,    'd': 0,    'theta': 0},
    ]

    fk = ForwardKinematics(link_params, 'modified')

    # Define waypoints in Cartesian space
    waypoints = [
        np.array([[1, 0, 0, 100],
                  [0, 1, 0, 50],
                  [0, 0, 1, 0],
                  [0, 0, 0, 1]]),
        np.array([[1, 0, 0, 150],
                  [0, 1, 0, 80],
                  [0, 0, 1, 0],
                  [0, 0, 0, 1]]),
        np.array([[1, 0, 0, 120],
                  [0, 1, 0, 120],
                  [0, 0, 1, 0],
                  [0, 0, 0, 1]]),
    ]

    # Convert waypoints to joint angles (initial guess)
    joint_waypoints = []
    for wp in waypoints:
        q = ik_numerical(link_params, wp, 'modified', initial_guess=np.zeros(3))
        if q is not None:
            joint_waypoints.append(q)

    if len(joint_waypoints) >= 2:
        # Generate path through waypoints
        trajectory = generate_waypoint_path(fk, joint_waypoints, n_points_per_segment=30)

        if len(trajectory) > 0:
            print(f"Waypoint path: {len(trajectory)} total waypoints")
            print(f"Through {len(joint_waypoints)} waypoints")

            # Compute Cartesian path
            cartesian_path = [fk.compute(q) for q in trajectory]
            total_length = compute_path_length(cartesian_path)
            print(f"Total path length: {total_length:.1f} mm")

            # Visualize
            positions = [fk.get_position(q) for q in trajectory]
            positions = np.array(positions)

            fig, ax = plt.subplots(figsize=(10, 8))

            # Plot arm at sample points
            sample_indices = [0, len(trajectory)//4, len(trajectory)//2, 3*len(trajectory)//4, len(trajectory)-1]
            for idx in sample_indices:
                q = trajectory[idx]
                x1 = l1 * np.cos(q[0])
                y1 = l1 * np.sin(q[0])
                x2 = x1 + l2 * np.cos(q[0] + q[1])
                y2 = y1 + l2 * np.sin(q[0] + q[1])
                x3 = x2 + l3 * np.cos(q[0] + q[1] + q[2])
                y3 = y2 + l3 * np.sin(q[0] + q[1] + q[2])
                ax.plot([0, x1, x2, x3], [0, y1, y2, y3], 'b-', alpha=0.4, linewidth=2)
                ax.plot([x3], [y3], 'go', markersize=6)

            # Plot full path
            ax.plot(positions[:, 0], positions[:, 1], 'r-', linewidth=2, label='Path')
            ax.plot([wp[0, 3] for wp in waypoints], [wp[1, 3] for wp in waypoints],
                    'ks--', markersize=10, label='Waypoints')

            for i, wp in enumerate(waypoints):
                ax.text(wp[0, 3], wp[1, 3], f'  W{i+1}', fontsize=12)

            ax.plot([0], [0], 'ko', markersize=12, label='Base')
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('X (mm)')
            ax.set_ylabel('Y (mm)')
            ax.set_title('Waypoint Path Planning / 路径点规划')
            ax.legend()

            output_path = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'waypoint_path.png')
            fig.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Waypoint path saved to outputs/waypoint_path.png")
            plt.close(fig)


if __name__ == '__main__':
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
    os.makedirs(output_dir, exist_ok=True)

    demo_cartesian_linear_path()
    demo_trajectory_smoothing()
    demo_waypoint_path()

    print("\n" + "=" * 60)
    print("Path planning demo completed! / 路径规划演示完成!")
    print("=" * 60)
