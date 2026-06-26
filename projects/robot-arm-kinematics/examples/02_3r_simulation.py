"""
Example 2: 3R Arm Simulation / 3R机械臂仿真

This example demonstrates:
1. Forward kinematics for a 3R planar arm
2. Trajectory tracking
3. Workspace analysis for 3R arm
4. Comparison with 2R arm workspace

Learning objectives:
- Understand how adding a joint increases workspace
- See the difference between joint-space and Cartesian-space trajectories
- Visualize workspace expansion with additional DOF
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.forward_kinematics import ForwardKinematics
from src.inverse_kinematics import ik_numerical
from src.jacobian import Jacobian
from src.workspace import plot_2r_workspace, plot_3r_workspace_2d
import matplotlib.pyplot as plt


def compute_3r_position(theta1, theta2, theta3, l1, l2, l3):
    """
    Compute end-effector position for a 3R planar arm.

    x = l1*cos(theta1) + l2*cos(theta1+theta2) + l3*cos(theta1+theta2+theta3)
    y = l1*sin(theta1) + l2*sin(theta1+theta2) + l3*sin(theta1+theta2+theta3)

    Args:
        theta1, theta2, theta3: Joint angles (radians)
        l1, l2, l3: Link lengths (mm)

    Returns:
        (x, y) end-effector position
    """
    x = (l1 * np.cos(theta1) +
         l2 * np.cos(theta1 + theta2) +
         l3 * np.cos(theta1 + theta2 + theta3))
    y = (l1 * np.sin(theta1) +
         l2 * np.sin(theta1 + theta2) +
         l3 * np.sin(theta1 + theta2 + theta3))
    return x, y


def simulate_3r_arm():
    """Simulate a 3R arm following a circular path."""
    print("=" * 60)
    print("Example 2: 3R Arm Simulation / 3R机械臂仿真")
    print("=" * 60)

    l1, l2, l3 = 100, 80, 60

    # Define arm using DH parameters (modified convention)
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': l2,   'alpha': 0,    'd': 0,    'theta': 0},
        {'a': l3,   'alpha': 0,    'd': 0,    'theta': 0},
    ]
    fk = ForwardKinematics(link_params, 'modified')

    # Simulate arm through various configurations
    print("\n--- 3R Arm Configurations / 3R机械臂配置 ---")
    print(f"{'Config':<10} {'theta1':>8} {'theta2':>8} {'theta3':>8} | {'x':>8} {'y':>8} | {'Reach':>8}")
    print("-" * 80)

    configs = [
        (0, 0, 0),
        (np.pi/6, np.pi/6, np.pi/6),
        (np.pi/4, -np.pi/4, np.pi/4),
        (np.pi/3, np.pi/3, -np.pi/3),
        (np.pi/2, 0, -np.pi/2),
        (0, np.pi/2, -np.pi/2),
    ]

    for i, (t1, t2, t3) in enumerate(configs):
        x, y = compute_3r_position(t1, t2, t3, l1, l2, l3)
        reach = np.sqrt(x**2 + y**2)
        print(f"Config {i:<4} {np.degrees(t1):>7.1f}° {np.degrees(t2):>7.1f}° {np.degrees(t3):>7.1f}° | "
              f"{x:>7.1f} {y:>7.1f} | {reach:>7.1f}mm")

    # Circular path tracking
    print("\n--- Circular Path Tracking / 圆形路径追踪 ---")
    radius = 120
    center_x, center_y = 100, 50
    n_points = 100

    # Generate circular path
    theta = np.linspace(0, 2*np.pi, n_points)
    path_x = center_x + radius * np.cos(theta)
    path_y = center_y + radius * np.sin(theta)

    # Track path using joint-space interpolation
    start_angles = [0, 0, 0]
    end_angles = [np.pi/4, -np.pi/6, np.pi/3]

    # Generate smooth trajectory
    from src.mapping import cubic_joint_trajectory, linear_joint_trajectory

    # Joint space trajectory
    q_traj = cubic_joint_trajectory(start_angles, end_angles, 50)

    # Forward kinematics along trajectory
    positions = []
    for q in q_traj:
        pos = fk.get_position(q)
        positions.append(pos)
    positions = np.array(positions)

    print(f"Trajectory points: {len(q_traj)}")
    print(f"Start position: ({positions[0][0]:.1f}, {positions[0][1]:.1f}) mm")
    print(f"End position: ({positions[-1][0]:.1f}, {positions[-1][1]:.1f}) mm")
    print(f"Path length: {np.sum(np.diff(positions, axis=0)):.1f} mm")

    # Visualize
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Arm configurations along path
    sample_indices = [0, 10, 25, 50, 75, 90, 99]
    for idx in sample_indices:
        q = q_traj[idx]
        x1 = l1 * np.cos(q[0])
        y1 = l1 * np.sin(q[0])
        x2 = x1 + l2 * np.cos(q[0] + q[1])
        y2 = y1 + l2 * np.sin(q[0] + q[1])
        x3 = x2 + l3 * np.cos(q[0] + q[1] + q[2])
        y3 = y2 + l3 * np.sin(q[0] + q[1] + q[2])

        alpha = idx / len(q_traj)
        axes[0].plot([0, x1, x2, x3], [0, y1, y2, y3],
                     color='blue', alpha=alpha, linewidth=1.5)

    # Plot end-effector path
    axes[0].plot(positions[:, 0], positions[:, 1], 'r-', linewidth=2, label='End-effector path')
    axes[0].plot([0], [0], 'ko', markersize=10, label='Base')
    axes[0].scatter([path_x[::5]], [path_y[::5]], c='green', s=30, alpha=0.5, label='Target path')
    axes[0].set_aspect('equal')
    axes[0].grid(True, alpha=0.3)
    axes[0].set_xlabel('X (mm)')
    axes[0].set_ylabel('Y (mm)')
    axes[0].set_title('3R Arm Trajectory / 3R机械臂轨迹')
    axes[0].legend()

    # Workspace comparison
    plot_2r_workspace(l1, l2, axes[1], n_samples=500)
    plot_3r_workspace_2d(l1, l2, l3, axes[1], n_samples=300)
    axes[1].set_title('2R vs 3R Workspace / 2R vs 3R工作空间对比')

    fig.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), '..', 'outputs', '3r_simulation.png')
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nSimulation plot saved to outputs/3r_simulation.png")
    plt.close(fig)


def jacobian_analysis():
    """Analyze the Jacobian of the 3R arm."""
    print("\n" + "=" * 60)
    print("Jacobian Analysis / 雅可比矩阵分析")
    print("=" * 60)

    l1, l2, l3 = 100, 80, 60
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': l2,   'alpha': 0,    'd': 0,    'theta': 0},
        {'a': l3,   'alpha': 0,    'd': 0,    'theta': 0},
    ]

    fk = ForwardKinematics(link_params, 'modified')
    jac = Jacobian(link_params, 'modified')

    # Test at different configurations
    configs = [
        (0, 0, 0),
        (np.pi/6, np.pi/6, np.pi/6),
        (np.pi/4, -np.pi/4, 0),
        (np.pi/2, -np.pi/2, 0),
    ]

    for t1, t2, t3 in configs:
        q = np.array([t1, t2, t3])
        J = jac.compute(q)
        pos = fk.get_position(q)
        manip = jac.compute_manipulability(q)
        cond = jac.compute_singularity_index(q)

        print(f"\nConfiguration: [{np.degrees(t1):.1f}°, {np.degrees(t2):.1f}°, {np.degrees(t3):.1f}°]")
        print(f"  Position: ({pos[0]:.1f}, {pos[1]:.1f}) mm")
        print(f"  Manipulability: {manip:.2f}")
        print(f"  Condition number: {cond:.2f}")

        print(f"  Jacobian (linear part):")
        print(f"    {J[:3, :]}")


if __name__ == '__main__':
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
    os.makedirs(output_dir, exist_ok=True)

    simulate_3r_arm()
    jacobian_analysis()

    print("\n" + "=" * 60)
    print("3R simulation completed! / 3R仿真完成!")
    print("=" * 60)
