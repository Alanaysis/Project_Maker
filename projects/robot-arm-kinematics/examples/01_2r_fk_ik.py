"""
Example 1: 2R Arm Forward and Inverse Kinematics
2R机械臂正向/逆向运动学演示

This example demonstrates:
1. Forward kinematics: joint angles -> end-effector position
2. Inverse kinematics: end-effector position -> joint angles
3. Multiple IK solutions (elbow up vs elbow down)
4. Workspace visualization

Learning objectives:
- Understand how DH parameters define a robot
- See forward kinematics in action
- Explore the relationship between joint space and Cartesian space
- Visualize the workspace and IK solutions
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.forward_kinematics import fk_2r_arm, ForwardKinematics
from src.inverse_kinematics import ik_2r_planar, ik_2r_planar_all_solutions
from src.workspace import plot_2r_workspace, plot_2r_arm, plot_2r_fk_ik_comparison


def example_forward_kinematics():
    """Demonstrate forward kinematics for a 2R arm."""
    print("=" * 60)
    print("Example 1a: Forward Kinematics / 正向运动学")
    print("=" * 60)

    # Define 2R arm parameters
    l1 = 100  # mm
    l2 = 80   # mm

    # Test configurations
    configs = [
        ("Flat", 0, 0),
        ("Bent up", np.pi/4, np.pi/4),
        ("Bent down", np.pi/4, -np.pi/4),
        ("Vertical", np.pi/2, 0),
        ("Folded", np.pi/2, -np.pi/2),
    ]

    print(f"\nLink lengths: l1 = {l1}mm, l2 = {l2}mm")
    print(f"Reachable workspace: [{abs(l1-l2):.1f}, {l1+l2:.1f}] mm")
    print()
    print(f"{'Configuration':<15} {'theta1 (deg)':<14} {'theta2 (deg)':<14} {'x (mm)':<12} {'y (mm)':<12}")
    print("-" * 67)

    for name, theta1, theta2 in configs:
        x, y = fk_2r_arm(theta1, theta2, l1, l2)
        print(f"{name:<15} {np.degrees(theta1):<14.2f} {np.degrees(theta2):<14.2f} {x:<12.2f} {y:<12.2f}")

    # Forward kinematics using DH parameters
    print("\n--- Using DH Parameters (Modified Convention) ---")
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': l2,   'alpha': 0,    'd': 0,    'theta': 0},
    ]
    fk = ForwardKinematics(link_params, 'modified')

    test_angles = [np.pi/4, np.pi/6]
    T = fk.compute(test_angles)
    pos = fk.get_position(test_angles)
    rot = fk.get_orientation(test_angles)

    print(f"\nJoint angles: [{np.degrees(test_angles[0]):.1f}°, {np.degrees(test_angles[1]):.1f}°]")
    print(f"End-effector position: [{pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}] mm")
    print(f"\nTransformation matrix (base to end-effector):")
    print(T)


def example_inverse_kinematics():
    """Demonstrate inverse kinematics for a 2R arm."""
    print("\n" + "=" * 60)
    print("Example 1b: Inverse Kinematics / 逆向运动学")
    print("=" * 60)

    l1 = 100  # mm
    l2 = 80   # mm

    targets = [
        (120, 60),
        (80, 80),
        (50, 50),
        (150, 0),
    ]

    for tx, ty in targets:
        print(f"\nTarget position: ({tx:.1f}, {ty:.1f}) mm")
        print(f"Distance from base: {np.sqrt(tx**2 + ty**2):.2f} mm")

        # Check reachability
        max_reach = l1 + l2
        min_reach = abs(l1 - l2)
        distance = np.sqrt(tx**2 + ty**2)

        if distance > max_reach or distance < min_reach:
            print(f"  WARNING: Target is OUTSIDE workspace! [{min_reach:.1f}, {max_reach:.1f}]")
            continue

        # Get all IK solutions
        solutions = ik_2r_planar_all_solutions(tx, ty, l1, l2)

        for i, (theta1, theta2) in enumerate(solutions):
            config_name = "elbow_up" if theta2 > 0 else "elbow_down"
            print(f"  Solution {i+1} ({config_name}):")
            print(f"    theta1 = {np.degrees(theta1):.2f}°")
            print(f"    theta2 = {np.degrees(theta2):.2f}°")

            # Verify by forward kinematics
            vx, vy = fk_2r_arm(theta1, theta2, l1, l2)
            error = np.sqrt((vx - tx)**2 + (vy - ty)**2)
            print(f"    Verification: ({vx:.2f}, {vy:.2f}), error = {error:.6f} mm")


def example_workspace_visualization():
    """Generate workspace visualization plots."""
    print("\n" + "=" * 60)
    print("Example 1c: Workspace Visualization / 工作空间可视化")
    print("=" * 60)

    l1 = 100
    l2 = 80

    # Plot workspace
    from src.workspace import plot_2r_workspace, plot_2r_fk_ik_comparison
    import matplotlib.pyplot as plt

    # Workspace plot
    fig1, ax1 = plt.subplots(1, 1, figsize=(8, 8))
    plot_2r_workspace(l1, l2, ax1, n_samples=1000, title="2R Arm Workspace / 2R机械臂工作空间")
    fig1.savefig(os.path.join(os.path.dirname(__file__), '..', 'outputs', 'workspace_2r.png'), dpi=150, bbox_inches='tight')
    print(f"Workspace plot saved to outputs/workspace_2r.png")
    plt.close(fig1)

    # FK/IK comparison
    fig2, ax2 = plt.subplots(1, 1, figsize=(10, 8))
    target_x, target_y = 120, 60
    plot_2r_fk_ik_comparison(l1, l2, target_x, target_y, ax2,
                             title=f"FK/IK Comparison / 正向逆向对比\nTarget: ({target_x}, {target_y})")
    fig2.savefig(os.path.join(os.path.dirname(__file__), '..', 'outputs', 'fk_ik_comparison.png'), dpi=150, bbox_inches='tight')
    print(f"FK/IK comparison saved to outputs/fk_ik_comparison.png")
    plt.close(fig2)

    # Individual configurations
    fig3, axes = plt.subplots(1, 3, figsize=(18, 6))
    configs = [
        (0, 0),
        (np.pi/4, np.pi/4),
        (np.pi/2, -np.pi/2),
    ]
    titles = ["Flat", "Bent Up", "Folded"]
    for ax, (t1, t2), title in zip(axes, configs, titles):
        plot_2r_arm([t1, t2], ax, title)
    fig3.savefig(os.path.join(os.path.dirname(__file__), '..', 'outputs', 'arm_configs.png'), dpi=150, bbox_inches='tight')
    print(f"Arm configurations saved to outputs/arm_configs.png")
    plt.close(fig3)


if __name__ == '__main__':
    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
    os.makedirs(output_dir, exist_ok=True)

    example_forward_kinematics()
    example_inverse_kinematics()
    example_workspace_visualization()

    print("\n" + "=" * 60)
    print("All examples completed! / 所有示例完成!")
    print("=" * 60)
