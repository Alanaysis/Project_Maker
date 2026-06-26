"""
Example 4: Workspace Visualization / 工作空间可视化

This example demonstrates:
1. 2R arm workspace (annulus)
2. 3R arm workspace (filled disk)
3. 3D workspace for spatial manipulators
4. Manipulability ellipsoid visualization
5. Singularity analysis

Learning objectives:
- Understand how link lengths affect workspace
- Visualize the difference between 2R and 3R workspaces
- See the manipulability ellipsoid in action
- Identify singular configurations
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.forward_kinematics import ForwardKinematics
from src.jacobian import Jacobian
from src.workspace import (
    plot_2r_workspace,
    plot_3r_workspace_2d,
    plot_3d_workspace,
    plot_manipulability_ellipsoid,
)
import matplotlib.pyplot as plt


def demo_2r_workspace_analysis():
    """Detailed workspace analysis for 2R arm."""
    print("=" * 60)
    print("Example 4a: 2R Workspace Analysis / 2R工作空间分析")
    print("=" * 60)

    l1, l2 = 100, 80

    # Workspace properties
    inner_r = abs(l1 - l2)
    outer_r = l1 + l2
    area = np.pi * (outer_r**2 - inner_r**2)

    print(f"\nLink lengths: l1 = {l1}mm, l2 = {l2}mm")
    print(f"Workspace type: Annulus (环形区域)")
    print(f"Inner radius: {inner_r}mm")
    print(f"Outer radius: {outer_r}mm")
    print(f"Workspace area: {area:.1f} mm²")

    # Density analysis: how many configurations reach each point
    print("\n--- Workspace Density / 工作空间密度 ---")
    print("(Higher density = more configurations reach that point)")

    grid_size = 50
    x_grid = np.linspace(-outer_r, outer_r, grid_size)
    y_grid = np.linspace(-outer_r, outer_r, grid_size)
    X, Y = np.meshgrid(x_grid, y_grid)

    density = np.zeros_like(X)
    n_samples = 10000

    for _ in range(n_samples):
        t1 = np.random.uniform(0, 2*np.pi)
        t2 = np.random.uniform(-np.pi, np.pi)
        x = l1 * np.cos(t1) + l2 * np.cos(t1 + t2)
        y = l1 * np.sin(t1) + l2 * np.sin(t1 + t2)

        # Find nearest grid cell
        ix = np.clip(np.argmin(np.abs(x_grid - x)), 0, grid_size - 1)
        iy = np.clip(np.argmin(np.abs(y_grid - y)), 0, grid_size - 1)
        density[iy, ix] += 1

    # Visualize
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Density heatmap
    im = axes[0].pcolormesh(X, Y, density, cmap='viridis', shading='auto')
    axes[0].set_aspect('equal')
    axes[0].set_xlabel('X (mm)')
    axes[0].set_ylabel('Y (mm)')
    axes[0].set_title('2R Workspace Density / 2R工作空间密度')
    plt.colorbar(im, ax=axes[0], label='Samples')

    # Workspace boundary
    plot_2r_workspace(l1, l2, axes[1], n_samples=500, title="2R Arm Workspace / 2R机械臂工作空间")

    fig.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), '..', 'outputs', '2r_workspace_analysis.png')
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nWorkspace analysis saved to outputs/2r_workspace_analysis.png")
    plt.close(fig)


def demo_3r_workspace_comparison():
    """Compare 2R and 3R arm workspaces."""
    print("\n" + "=" * 60)
    print("Example 4b: 3R Workspace Comparison / 3R工作空间对比")
    print("=" * 60)

    l1, l2, l3 = 100, 80, 60

    # 3R workspace properties
    max_reach = l1 + l2 + l3
    min_reach = max(0, l1 - l2 - l3)
    area = np.pi * (max_reach**2 - min_reach**2)

    print(f"\nLink lengths: l1 = {l1}mm, l2 = {l2}mm, l3 = {l3}mm")
    print(f"Workspace type: Disk (圆形区域)")
    print(f"Maximum reach: {max_reach}mm")
    print(f"Minimum reach: {min_reach}mm")
    print(f"Workspace area: {area:.1f} mm²")

    # Comparison
    print(f"\n--- Workspace Comparison / 工作空间对比 ---")
    print(f"{'Arm':<10} {'Type':<15} {'Area (mm²)':<15} {'Max Reach':<12}")
    print("-" * 52)
    print(f"{'2R':<10} {'Annulus':<15} {np.pi*((l1+l2)**2 - (l1-l2)**2):<15.1f} {l1+l2:<12}")
    print(f"{'3R':<10} {'Disk':<15} {np.pi*max_reach**2:<15.1f} {max_reach:<12}")
    print(f"{'Area gain':<10} {'':<15} {np.pi*max_reach**2 - np.pi*((l1+l2)**2 - (l1-l2)**2):<15.1f} {'':<12}")


def demo_3d_workspace():
    """Generate 3D workspace for a spatial manipulator."""
    print("\n" + "=" * 60)
    print("Example 4c: 3D Workspace / 3D工作空间")
    print("=" * 60)

    # SCARA-like arm (2 revolute + 1 prismatic)
    link_params = [
        {'a': 0,    'alpha': -np.pi/2, 'd': 0,     'theta': 0},
        {'a': 100,  'alpha': 0,        'd': 0,     'theta': 0},
        {'a': 80,   'alpha': 0,        'd': 0,     'theta': 0},
        {'a': 0,    'alpha': 0,        'd': 0,     'theta': 0},  # prismatic joint (d varies)
    ]

    # For prismatic joint, use theta as the variable (simplified)
    joint_ranges = [
        (0, 2*np.pi),      # Joint 1: full rotation
        (-np.pi, np.pi),   # Joint 2: full rotation
        (-np.pi, np.pi),   # Joint 3: prismatic (using theta as proxy)
        (0, 2*np.pi),      # Joint 4: full rotation
    ]

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Sample workspace
    from src.workspace import plot_3d_workspace
    ax = plot_3d_workspace(link_params, joint_ranges, 'modified', n_samples=500, ax=ax)

    output_path = os.path.join(os.path.dirname(__file__), '..', 'outputs', '3d_workspace.png')
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"3D workspace saved to outputs/3d_workspace.png")
    plt.close(fig)


def demo_manipulability():
    """Demonstrate manipulability ellipsoid at different configurations."""
    print("\n" + "=" * 60)
    print("Example 4d: Manipulability Analysis / 可操作性分析")
    print("=" * 60)

    l1, l2 = 100, 80
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': l2,   'alpha': 0,    'd': 0,    'theta': 0},
    ]

    fk = ForwardKinematics(link_params, 'modified')
    jac = Jacobian(link_params, 'modified')

    configs = [
        ("Flat", np.array([0, 0])),
        ("Bent", np.array([np.pi/4, np.pi/3])),
        ("Folded", np.array([np.pi/4, -np.pi/4])),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    for (name, q), ax in zip(configs, axes):
        manip = jac.compute_manipulability(q)
        cond = jac.compute_singularity_index(q)
        pos = fk.get_position(q)

        print(f"\n{name}:")
        print(f"  Joint angles: [{np.degrees(q[0]):.1f}°, {np.degrees(q[1]):.1f}°]")
        print(f"  Position: ({pos[0]:.1f}, {pos[1]:.1f}) mm")
        print(f"  Manipulability: {manip:.2f}")
        print(f"  Condition number: {cond:.2f}")

        # Plot arm and ellipsoid
        x1 = l1 * np.cos(q[0])
        y1 = l1 * np.sin(q[0])
        x2 = x1 + l2 * np.cos(q[0] + q[1])
        y2 = y1 + l2 * np.sin(q[0] + q[1])

        ax.plot([0, x1, x2], [0, y1, y2], 'b-', linewidth=4)
        ax.plot([0], [0], 'ko', markersize=10)
        ax.plot([x2], [y2], 'ro', markersize=8)

        # Plot ellipsoid at end-effector
        from src.workspace import plot_manipulability_ellipsoid
        plot_manipulability_ellipsoid(fk, q, ax)

        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_title(f"{name}\nw={manip:.1f}, κ={cond:.1f}")
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')

    fig.suptitle("Manipulability Ellipsoid at Different Configurations / 不同配置的可操作性椭球")
    output_path = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'manipulability.png')
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nManipulability plot saved to outputs/manipulability.png")
    plt.close(fig)


def demo_singularity_analysis():
    """Analyze singular configurations."""
    print("\n" + "=" * 60)
    print("Example 4e: Singularity Analysis / 奇异分析")
    print("=" * 60)

    l1, l2 = 100, 80
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': l2,   'alpha': 0,    'd': 0,    'theta': 0},
    ]

    fk = ForwardKinematics(link_params, 'modified')
    jac = Jacobian(link_params, 'modified')

    print("\n--- Singularity Analysis for 2R Arm ---")
    print("Singular when: theta2 = 0 (fully extended) or theta2 = pi (fully folded)")
    print()
    print(f"{'theta1':>10} {'theta2':>10} {'Condition #':>14} {'Manipulability':>16} {'Status':<15}")
    print("-" * 70)

    test_angles = [
        (0, 0.01),      # Near singular (extended)
        (np.pi/4, np.pi/6),   # Non-singular
        (np.pi/2, np.pi/2),   # Non-singular
        (np.pi/4, -np.pi/4),  # Non-singular
        (np.pi/2, np.pi - 0.01),  # Near singular (folded)
        (np.pi/4, np.pi),     # Singular (folded)
    ]

    for t1, t2 in test_angles:
        q = np.array([t1, t2])
        cond = jac.compute_singularity_index(q)
        manip = jac.compute_manipulability(q)
        pos = fk.get_position(q)

        if cond > 1000:
            status = "SINGULAR"
        elif cond > 100:
            status = "NEAR SINGULAR"
        else:
            status = "OK"

        print(f"{np.degrees(t1):>10.1f}° {np.degrees(t2):>10.1f}° {cond:>14.2f} {manip:>16.2f} {status:<15}")


if __name__ == '__main__':
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
    os.makedirs(output_dir, exist_ok=True)

    demo_2r_workspace_analysis()
    demo_3r_workspace_comparison()
    demo_3d_workspace()
    demo_manipulability()
    demo_singularity_analysis()

    print("\n" + "=" * 60)
    print("Workspace visualization completed! / 工作空间可视化完成!")
    print("=" * 60)
