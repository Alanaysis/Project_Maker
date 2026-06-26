"""
Workspace Visualization Module / 工作空间可视化模块

The workspace (or reach envelope) is the set of all points that the
end-effector can reach. It's a fundamental concept in robot design and
path planning.

Types of workspace:
1. Primary workspace: Points reachable with any orientation
2. Dexterous workspace: Points reachable with any orientation AND velocity
3. Operational workspace: Points reachable with a specific orientation

For a 2R planar arm, the workspace is an annulus (ring):
- Inner radius: |l1 - l2|
- Outer radius: l1 + l2

For a 3R planar arm, the workspace is a filled disk:
- Outer radius: l1 + l2 + l3
- Inner radius: max(0, l1 - l2 - l3)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import patches
from mpl_toolkits.mplot3d import Axes3D
from .forward_kinematics import fk_2r_arm, ForwardKinematics
from .inverse_kinematics import ik_2r_planar_all_solutions


def plot_2r_workspace(l1, l2, ax=None, n_samples=1000, title="2R Arm Workspace"):
    """
    Plot the workspace of a 2R planar arm.

    The workspace is an annulus (ring-shaped region).

    Args:
        l1: Length of first link (mm)
        l2: Length of second link (mm)
        ax: matplotlib axis (creates new one if None)
        n_samples: Number of samples for workspace boundary
        title: Plot title

    Returns:
        matplotlib axis
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))

    # Generate workspace points by sampling all joint configurations
    theta1 = np.linspace(0, 2 * np.pi, n_samples)
    theta2 = np.linspace(-np.pi, np.pi, n_samples)
    THETA1, THETA2 = np.meshgrid(theta1, theta2)

    x = l1 * np.cos(THETA1) + l2 * np.cos(THETA1 + THETA2)
    y = l1 * np.sin(THETA1) + l2 * np.sin(THETA1 + THETA2)

    ax.fill(x.flatten(), y.flatten(), alpha=0.3, label='Workspace')
    ax.plot([0], [0], 'ko', markersize=10, label='Base')
    ax.plot([l1], [0], 'rs', markersize=8, label='Elbow')

    # Draw workspace boundary
    outer_r = l1 + l2
    inner_r = abs(l1 - l2)
    circle_outer = plt.Circle((0, 0), outer_r, fill=False, color='r', linewidth=2, label='Outer boundary')
    circle_inner = plt.Circle((0, 0), inner_r, fill=False, color='b', linewidth=2, label='Inner boundary')
    ax.add_patch(circle_outer)
    ax.add_patch(circle_inner)

    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_title(title)
    ax.legend()

    return ax


def plot_2r_arm(joint_angles, ax=None, title="2R Arm Configuration"):
    """
    Plot a 2R arm in a given configuration.

    Args:
        joint_angles: [theta1, theta2] in radians
        ax: matplotlib axis
        title: Plot title

    Returns:
        matplotlib axis
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))

    l1 = 100
    l2 = 80

    x0, y0 = 0, 0
    x1 = l1 * np.cos(joint_angles[0])
    y1 = l1 * np.sin(joint_angles[0])
    x2 = x1 + l2 * np.cos(joint_angles[0] + joint_angles[1])
    y2 = y1 + l2 * np.sin(joint_angles[0] + joint_angles[1])

    ax.plot([x0, x1], [y0, y1], 'b-', linewidth=4, label='Link 1')
    ax.plot([x1, x2], [y1, y2], 'r-', linewidth=4, label='Link 2')
    ax.plot([x0], [y0], 'ko', markersize=12, label='Base')
    ax.plot([x1], [y1], 'ro', markersize=8, label='Elbow')
    ax.plot([x2], [y2], 'gs', markersize=10, label='End-effector')

    # Draw angle arcs
    arc1 = patches.Arc((x0, y0), 40, 40, angle=0,
                        theta1=np.degrees(0), theta2=np.degrees(joint_angles[0]),
                        color='blue', linewidth=2)
    ax.add_patch(arc1)

    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_title(f"{title}\ntheta1={np.degrees(joint_angles[0]):.1f}°, theta2={np.degrees(joint_angles[1]):.1f}°")
    ax.legend()

    return ax


def plot_2r_fk_ik_comparison(l1, l2, target_x, target_y, ax=None):
    """
    Plot forward and inverse kinematics comparison for 2R arm.

    Shows the arm reaching the target position from both elbow-up
    and elbow-down configurations.

    Args:
        l1: Length of first link (mm)
        l2: Length of second link (mm)
        target_x: Target x position (mm)
        target_y: Target y position (mm)
        ax: matplotlib axis

    Returns:
        matplotlib axis
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 8))

    # Plot workspace
    plot_2r_workspace(l1, l2, ax, n_samples=500)

    # Plot target
    ax.plot([target_x], [target_y], 'k*', markersize=20, label='Target')

    # Plot both IK solutions
    solutions = ik_2r_planar_all_solutions(target_x, target_y, l1, l2)
    colors = ['blue', 'red']
    labels = ['Elbow Up', 'Elbow Down']

    for i, (theta1, theta2) in enumerate(solutions):
        x1 = l1 * np.cos(theta1)
        y1 = l1 * np.sin(theta1)
        x2 = x1 + l2 * np.cos(theta1 + theta2)
        y2 = y1 + l2 * np.sin(theta1 + theta2)

        ax.plot([0, x1], [0, y1], colors[i], linewidth=3, alpha=0.7)
        ax.plot([x1, x2], [y1, y2], colors[i], linewidth=3, alpha=0.7)
        ax.plot([x2], [y2], 'go', markersize=8)

    ax.plot([target_x], [target_y], 'r--', alpha=0.5, linewidth=1)
    ax.plot([0, target_x], [0, target_y], 'k:', alpha=0.3)

    ax.set_aspect('equal')
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_title(f"2R Arm IK Solutions\nTarget: ({target_x:.1f}, {target_y:.1f})")
    ax.legend()

    return ax


def plot_3r_workspace_2d(l1, l2, l3, ax=None, n_samples=500):
    """
    Plot the workspace of a 3R planar arm.

    The 3R arm can fill the entire disk from 0 to l1+l2+l3.

    Args:
        l1, l2, l3: Link lengths (mm)
        ax: matplotlib axis
        n_samples: Number of samples

    Returns:
        matplotlib axis
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))

    theta1 = np.linspace(0, 2 * np.pi, n_samples)
    theta2 = np.linspace(-np.pi, np.pi, n_samples)
    theta3 = np.linspace(-np.pi, np.pi, n_samples)
    T1, T2, T3 = np.meshgrid(theta1, theta2, theta3)

    x = (l1 * np.cos(T1) + l2 * np.cos(T1 + T2) +
         l3 * np.cos(T1 + T2 + T3))
    y = (l1 * np.sin(T1) + l2 * np.sin(T1 + T2) +
         l3 * np.sin(T1 + T2 + T3))

    ax.fill(x.flatten(), y.flatten(), alpha=0.3, color='green', label='Workspace')
    ax.plot([0], [0], 'ko', markersize=10, label='Base')

    # Boundary
    max_r = l1 + l2 + l3
    circle = plt.Circle((0, 0), max_r, fill=False, color='r', linewidth=2)
    ax.add_patch(circle)

    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_title('3R Arm Workspace')
    ax.legend()

    return ax


def plot_3d_workspace(link_params, joint_ranges, dh_convention='modified',
                      n_samples=200, ax=None):
    """
    Plot the 3D workspace by sampling joint configurations.

    Args:
        link_params: List of dicts with base DH parameters
        joint_ranges: List of (min, max) tuples for each joint angle range
        dh_convention: DH convention
        n_samples: Number of samples per joint
        ax: matplotlib 3D axis

    Returns:
        matplotlib 3D axis
    """
    if ax is None:
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

    fk = ForwardKinematics(link_params, dh_convention)
    n_joints = len(link_params)

    # Generate random joint configurations
    positions = []
    for _ in range(n_samples):
        joint_angles = np.array([
            np.random.uniform(r[0], r[1]) for r in joint_ranges
        ])
        pos = fk.get_position(joint_angles)
        positions.append(pos)

    positions = np.array(positions)
    scatter = ax.scatter(positions[:, 0], positions[:, 1], positions[:, 2],
                         c=positions[:, 2], cmap='viridis', s=5, alpha=0.5)

    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_zlabel('Z (mm)')
    ax.set_title('3D Workspace (sampled)')
    plt.colorbar(scatter, ax=ax, label='Z (mm)')

    return ax


def plot_manipulability_ellipsoid(fk, joint_angles, ax=None):
    """
    Plot the manipulability ellipsoid.

    The ellipsoid shows the instantaneous dexterity of the robot.
    Directions with larger radius = more dexterous.

    Args:
        fk: ForwardKinematics instance
        joint_angles: Current joint angles
        ax: matplotlib axis

    Returns:
        matplotlib axis
    """
    from .jacobian import Jacobian
    jac = Jacobian(fk.link_params, fk.dh_convention)

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))

    J = jac.compute(joint_angles)
    U, S, Vt = np.linalg.svd(J[:3, :])

    # Ellipsoid axes
    axes_lengths = S[:3]

    # Draw ellipsoid
    u = np.linspace(0, 2 * np.pi, 50)
    v = np.linspace(0, np.pi, 50)
    U_v, V_v = np.meshgrid(u, v)

    x_ell = axes_lengths[0] * np.sin(V_v) * np.cos(U_v)
    y_ell = axes_lengths[1] * np.sin(V_v) * np.sin(U_v)
    z_ell = axes_lengths[2] * np.cos(V_v)

    # Transform to world frame
    R = U
    x_world = R[0, 0] * x_ell + R[0, 1] * y_ell + R[0, 2] * z_ell
    y_world = R[1, 0] * x_ell + R[1, 1] * y_ell + R[1, 2] * z_ell
    z_world = R[2, 0] * x_ell + R[2, 1] * y_ell + R[2, 2] * z_ell

    ax.plot_surface(x_world, y_world, z_world, alpha=0.3, color='blue')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title(f"Manipulability Ellipsoid\nw={jac.compute_manipulability(joint_angles):.2f}")

    return ax
