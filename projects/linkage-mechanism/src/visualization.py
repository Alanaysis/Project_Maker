"""Visualization tools for linkage mechanisms.

连杆机构的可视化工具模块。

Provides functions for plotting four-bar linkage configurations,
coupler curves, velocity/acceleration diagrams, and transmission
angle variations.
"""

from typing import Optional, Tuple, List

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from .position_analysis import (
    FourBarParams,
    PositionResult,
    position_analysis,
    check_grashof,
    GrashofType,
    LinkageType,
)
from .velocity_analysis import velocity_analysis
from .acceleration_analysis import acceleration_analysis


def plot_linkage(params: FourBarParams, theta2: float,
                 show_coupler_point: bool = True,
                 coupler_point_ratio: Tuple[float, float] = (0.5, 0.3),
                 coupler_angle_offset: float = 0.0,
                 ax: Optional[plt.Axes] = None,
                 title: str = "Four-Bar Linkage",
                 colors: Optional[dict] = None) -> plt.Axes:
    """Plot a four-bar linkage at a given input angle.

    Args:
        params: Four-bar linkage parameters.
        theta2: Input crank angle in radians.
        show_coupler_point: Whether to show the coupler point.
        coupler_point_ratio: Point location on coupler.
        coupler_angle_offset: Offset angle for the coupler point.
        ax: matplotlib Axes to plot on. Creates new one if None.
        title: Plot title.
        colors: Custom colors for links.

    Returns:
        matplotlib Axes with the plotted linkage.
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))

    if colors is None:
        colors = {
            'ground': '#666666',
            'crank': '#E74C3C',
            'coupler': '#3498DB',
            'rocker': '#2ECC71',
            'coupler_point': '#F39C12',
        }

    a1, a2, a3, a4 = params.a1, params.a2, params.a3, params.a4
    o2, o4 = params.o2, params.o4

    # Compute positions
    pos = position_analysis(params, theta2, coupler_point_ratio, coupler_angle_offset)

    # Joint positions
    O2 = np.array(o2)
    O4 = np.array(o4)
    A = O2 + np.array([a2 * np.cos(theta2), a2 * np.sin(theta2)])
    B = A + np.array([a3 * np.cos(pos.theta3), a3 * np.sin(pos.theta3)])
    C = O4 + np.array([a4 * np.cos(pos.theta4), a4 * np.sin(pos.theta4)])
    P = np.array(pos.coupler_point)

    # Plot links
    linewidth = 3
    # Ground link (O2 to O4)
    ax.plot([O2[0], O4[0]], [O2[1], O4[1]], color=colors['ground'],
            linewidth=linewidth, linestyle='--', label='Ground (机架)')
    # Crank (O2 to A)
    ax.plot([O2[0], A[0]], [O2[1], A[1]], color=colors['crank'],
            linewidth=linewidth, label=f'Crank (曲柄) a2={a2:.2f}')
    # Coupler (A to B)
    ax.plot([A[0], B[0]], [A[1], B[1]], color=colors['coupler'],
            linewidth=linewidth, label=f'Coupler (连杆) a3={a3:.2f}')
    # Rocker (C to O4)
    ax.plot([C[0], O4[0]], [C[1], O4[1]], color=colors['rocker'],
            linewidth=linewidth, label=f'Rocker (摇杆) a4={a4:.2f}')

    # Plot joints
    joint_color = 'black'
    joint_radius = 5
    for pt, label in [(O2, 'O2'), (O4, 'O4'), (A, 'A'), (B, 'B'), (C, 'C')]:
        ax.plot(pt[0], pt[1], 'o', color=joint_color, markersize=joint_radius)
        offset_y = 0.15
        ax.text(pt[0], pt[1] - offset_y, label, fontsize=10, ha='center')

    # Plot coupler point
    if show_coupler_point:
        ax.plot(P[0], P[1], '*', color=colors['coupler_point'],
                markersize=12, label=f'Coupler Point (连杆点)')

    # Add angle arc for input angle
    arc_radius = min(a2 * 0.3, 0.5)
    if arc_radius > 0.01:
        arc_angles = np.linspace(0, theta2, 30) if theta2 > 0 else np.linspace(theta2, 0, 30)
        arc_x = O2[0] + arc_radius * np.cos(arc_angles)
        arc_y = O2[1] + arc_radius * np.sin(arc_angles)
        ax.plot(arc_x, arc_y, 'k-', linewidth=1, alpha=0.5)
        ax.text(O2[0] + arc_radius + 0.1, O2[1] + 0.1,
                f'$\\theta_2$={np.degrees(theta2):.1f}°', fontsize=9)

    # Add dimension labels
    ax.annotate('', xy=(O2[0] + a1/2, O2[1] - 0.3),
                xytext=(O2[0], O2[1]),
                arrowprops=dict(arrowstyle='<->', color='#999', lw=1))
    ax.text(O2[0] + a1/4, O2[1] - 0.5, f'a1={a1:.2f}', fontsize=8, ha='center', color='#999')

    # Set axis properties
    margin = max(a1, a2, a3, a4) * 0.3
    all_x = [O2[0], O4[0], A[0], B[0], C[0]]
    all_y = [O2[1], O4[1], A[1], B[1], C[1]]
    if show_coupler_point:
        all_x.append(P[0])
        all_y.append(P[1])
    ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
    ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X', fontsize=11)
    ax.set_ylabel('Y', fontsize=11)
    ax.set_title(title, fontsize=13)
    ax.legend(loc='upper right', fontsize=9)

    return ax


def plot_coupler_curve(params: FourBarParams,
                       coupler_point_ratio: Tuple[float, float] = (0.5, 0.3),
                       coupler_angle_offset: float = 0.0,
                       num_points: int = 360,
                       ax: Optional[plt.Axes] = None,
                       title: str = "Coupler Curve (连杆曲线)") -> plt.Axes:
    """Plot the coupler curve traced by a point on the coupler link.

    The coupler curve is a characteristic curve of the four-bar linkage
    and is used in mechanism synthesis.

    Args:
        params: Four-bar linkage parameters.
        coupler_point_ratio: Point location on coupler.
        coupler_angle_offset: Offset angle for the coupler point.
        num_points: Number of sample points.
        ax: matplotlib Axes to plot on.
        title: Plot title.

    Returns:
        matplotlib Axes with the plotted coupler curve.
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    # Generate coupler curve
    from .position_analysis import generate_coupler_curve
    curve = generate_coupler_curve(params, num_points, coupler_point_ratio, coupler_angle_offset)

    # Plot coupler curve
    if len(curve) > 0:
        ax.plot(curve[:, 0], curve[:, 1], 'b-', linewidth=1.5,
                label='Coupler Curve (连杆曲线)')

    # Plot the linkage at several positions for reference
    reference_angles = [0, np.pi/4, np.pi/2, 3*np.pi/4, np.pi]
    for theta2_ref in reference_angles:
        try:
            plot_linkage(params, theta2_ref, show_coupler_point=False,
                         coupler_point_ratio=coupler_point_ratio,
                         coupler_angle_offset=coupler_angle_offset, ax=ax)
        except ValueError:
            pass

    # Set axis properties
    if len(curve) > 0:
        margin = max(params.a1, params.a2, params.a3, params.a4) * 0.2
        all_x = [curve[:, 0].min(), curve[:, 0].max()]
        all_y = [curve[:, 1].min(), curve[:, 1].max()]
        ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
        ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X', fontsize=11)
    ax.set_ylabel('Y', fontsize=11)
    ax.set_title(title, fontsize=13)
    ax.legend(loc='upper right', fontsize=9)

    return ax


def plot_transmission_angle(params: FourBarParams,
                            num_points: int = 360,
                            ax: Optional[plt.Axes] = None) -> plt.Axes:
    """Plot the transmission angle variation over a full cycle.

    The transmission angle indicates the mechanical advantage of the
    mechanism. Values near 90 degrees are ideal.

    Args:
        params: Four-bar linkage parameters.
        num_points: Number of sample points.
        ax: matplotlib Axes to plot on.

    Returns:
        matplotlib Axes with the transmission angle plot.
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(10, 4))

    from .velocity_analysis import compute_transmission_angle

    theta2_range = np.linspace(0, 2*np.pi, num_points)
    transmission_angles = []

    for theta2 in theta2_range:
        try:
            mu = compute_transmission_angle(params, theta2)
            transmission_angles.append(np.degrees(mu))
        except ValueError:
            transmission_angles.append(np.nan)

    transmission_angles = np.array(transmission_angles)

    ax.plot(np.degrees(theta2_range), transmission_angles, 'b-', linewidth=1.5,
            label='Transmission Angle (传动角)')
    ax.axhline(y=90, color='g', linestyle='--', alpha=0.5, label='Ideal (90°)')
    ax.axhline(y=40, color='r', linestyle='--', alpha=0.3, label='Min recommended (40°)')
    ax.axhline(y=140, color='r', linestyle='--', alpha=0.3, label='Max recommended (140°)')

    # Shade regions outside recommended range
    valid_mask = ~np.isnan(transmission_angles)
    if valid_mask.any():
        ax.fill_between(np.degrees(theta2_range)[valid_mask], transmission_angles[valid_mask],
                        90, alpha=0.15, color='green', label='Good range')

    ax.set_xlabel('Input Angle $\\theta_2$ (degrees)', fontsize=11)
    ax.set_ylabel('Transmission Angle $\\mu$ (degrees)', fontsize=11)
    ax.set_title('Transmission Angle Variation (传动角变化)', fontsize=13)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)

    return ax


def plot_velocity_diagram(params: FourBarParams, theta2: float,
                          omega2: float,
                          ax: Optional[plt.Axes] = None,
                          title: str = "Velocity Diagram (速度图)") -> plt.Axes:
    """Plot the velocity polygon for the four-bar linkage.

    Args:
        params: Four-bar linkage parameters.
        theta2: Input crank angle in radians.
        omega2: Input crank angular velocity (rad/s).
        ax: matplotlib Axes to plot on.
        title: Plot title.

    Returns:
        matplotlib Axes with the velocity diagram.
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))

    from .velocity_analysis import compute_linear_velocity

    velocities = compute_linear_velocity(params, theta2, omega2)

    # Plot velocity vectors from a common origin
    origin = np.array([0, 0])
    scale = 0.5  # Scale factor for visualization

    # Velocity of point A
    VA = np.array(velocities['A'])
    ax.arrow(origin[0], origin[1], VA[0] * scale, VA[1] * scale,
             head_width=0.1, head_length=0.05, fc='red', ec='red', linewidth=2,
             label=f'V_A = {np.linalg.norm(VA):.3f}')

    # Velocity of point B
    VB = np.array(velocities['B'])
    ax.arrow(origin[0], origin[1], VB[0] * scale, VB[1] * scale,
             head_width=0.1, head_length=0.05, fc='blue', ec='blue', linewidth=2,
             label=f'V_B = {np.linalg.norm(VB):.3f}')

    # Velocity of point C
    VC = np.array(velocities['C'])
    ax.arrow(origin[0], origin[1], VC[0] * scale, VC[1] * scale,
             head_width=0.1, head_length=0.05, fc='green', ec='green', linewidth=2,
             label=f'V_C = {np.linalg.norm(VC):.3f}')

    ax.set_xlabel('V_x', fontsize=11)
    ax.set_ylabel('V_y', fontsize=11)
    ax.set_title(title, fontsize=13)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    ax.legend(fontsize=9)

    # Add angular velocity labels
    ax.text(0.02, 0.98,
            f'$\\omega_2$ = {omega2:.2f} rad/s\n'
            f'$\\omega_3$ = {velocities["omega3"]:.2f} rad/s\n'
            f'$\\omega_4$ = {velocities["omega4"]:.2f} rad/s',
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    return ax


def plot_phase_diagram(params: FourBarParams, omega2: float = 1.0,
                       alpha2: float = 0.0,
                       num_points: int = 360,
                       ax1: Optional[plt.Axes] = None,
                       ax2: Optional[plt.Axes] = None) -> Tuple[plt.Axes, plt.Axes]:
    """Plot phase diagram showing theta3, theta4 vs theta2.

    Args:
        params: Four-bar linkage parameters.
        omega2: Input angular velocity (rad/s).
        alpha2: Input angular acceleration (rad/s^2).
        num_points: Number of sample points.
        ax1: First subplot axes (position).
        ax2: Second subplot axes (velocity/acceleration).

    Returns:
        Tuple of (ax1, ax2) matplotlib Axes.
    """
    if ax1 is None:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    theta2_range = np.linspace(0, 2*np.pi, num_points)
    theta3_vals = []
    theta4_vals = []
    omega3_vals = []
    omega4_vals = []
    alpha3_vals = []
    alpha4_vals = []

    for theta2 in theta2_range:
        try:
            pos = position_analysis(params, theta2)
            theta3_vals.append(np.degrees(pos.theta3))
            theta4_vals.append(np.degrees(pos.theta4))

            omega3, omega4 = velocity_analysis(params, theta2, omega2)
            omega3_vals.append(omega3)
            omega4_vals.append(omega4)

            alpha3, alpha4 = acceleration_analysis(params, theta2, omega2, alpha2)
            alpha3_vals.append(alpha3)
            alpha4_vals.append(alpha4)
        except ValueError:
            theta3_vals.append(np.nan)
            theta4_vals.append(np.nan)
            omega3_vals.append(np.nan)
            omega4_vals.append(np.nan)
            alpha3_vals.append(np.nan)
            alpha4_vals.append(np.nan)

    theta3_vals = np.array(theta3_vals)
    theta4_vals = np.array(theta4_vals)
    omega3_vals = np.array(omega3_vals)
    omega4_vals = np.array(omega4_vals)
    alpha3_vals = np.array(alpha3_vals)
    alpha4_vals = np.array(alpha4_vals)

    # Position subplot
    ax1.plot(np.degrees(theta2_range), theta3_vals, 'b-', linewidth=1.5,
             label='$\\theta_3$ (Coupler)')
    ax1.plot(np.degrees(theta2_range), theta4_vals, 'r-', linewidth=1.5,
             label='$\\theta_4$ (Rocker)')
    ax1.set_xlabel('Input Angle $\\theta_2$ (degrees)', fontsize=11)
    ax1.set_ylabel('Angle (degrees)', fontsize=11)
    ax1.set_title('Position Analysis (位置分析)', fontsize=13)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=9)

    # Velocity subplot
    ax2.plot(np.degrees(theta2_range), omega3_vals, 'b-', linewidth=1.5,
             label='$\\omega_3$ (Coupler)')
    ax2.plot(np.degrees(theta2_range), omega4_vals, 'r-', linewidth=1.5,
             label='$\\omega_4$ (Rocker)')
    ax2.set_xlabel('Input Angle $\\theta_2$ (degrees)', fontsize=11)
    ax2.set_ylabel('Angular Velocity (rad/s)', fontsize=11)
    ax2.set_title('Velocity Analysis (速度分析)', fontsize=13)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9)

    return ax1, ax2


def plot_acceleration_phase(params: FourBarParams, omega2: float = 1.0,
                            alpha2: float = 0.0,
                            num_points: int = 360,
                            ax: Optional[plt.Axes] = None) -> plt.Axes:
    """Plot acceleration phase diagram.

    Args:
        params: Four-bar linkage parameters.
        omega2: Input angular velocity (rad/s).
        alpha2: Input angular acceleration (rad/s^2).
        num_points: Number of sample points.
        ax: matplotlib Axes to plot on.

    Returns:
        matplotlib Axes with the acceleration phase diagram.
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    theta2_range = np.linspace(0, 2*np.pi, num_points)
    alpha3_vals = []
    alpha4_vals = []

    for theta2 in theta2_range:
        try:
            alpha3, alpha4 = acceleration_analysis(params, theta2, omega2, alpha2)
            alpha3_vals.append(alpha3)
            alpha4_vals.append(alpha4)
        except ValueError:
            alpha3_vals.append(np.nan)
            alpha4_vals.append(np.nan)

    alpha3_vals = np.array(alpha3_vals)
    alpha4_vals = np.array(alpha4_vals)

    ax.plot(np.degrees(theta2_range), alpha3_vals, 'b-', linewidth=1.5,
            label='$\\alpha_3$ (Coupler)')
    ax.plot(np.degrees(theta2_range), alpha4_vals, 'r-', linewidth=1.5,
            label='$\\alpha_4$ (Rocker)')

    ax.set_xlabel('Input Angle $\\theta_2$ (degrees)', fontsize=11)
    ax.set_ylabel('Angular Acceleration (rad/s$^2$)', fontsize=11)
    ax.set_title('Acceleration Analysis (加速度分析)', fontsize=13)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)

    return ax


def create_full_analysis_figure(params: FourBarParams,
                                coupler_point_ratio: Tuple[float, float] = (0.5, 0.3),
                                coupler_angle_offset: float = 0.0,
                                omega2: float = 1.0,
                                alpha2: float = 0.0,
                                sample_angles: Optional[list] = None) -> plt.Figure:
    """Create a comprehensive analysis figure.

    Creates a multi-panel figure showing:
    1. Linkage at sample positions
    2. Coupler curve
    3. Transmission angle
    4. Phase diagrams

    Args:
        params: Four-bar linkage parameters.
        coupler_point_ratio: Point location on coupler.
        coupler_angle_offset: Offset angle for the coupler point.
        omega2: Input angular velocity (rad/s).
        alpha2: Input angular acceleration (rad/s^2).
        sample_angles: Sample crank angles for linkage plots.

    Returns:
        matplotlib Figure object.
    """
    if sample_angles is None:
        sample_angles = [0, np.pi/3, 2*np.pi/3, np.pi]

    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)

    # Subplot 1: Linkage at sample positions
    ax1 = fig.add_subplot(gs[0, 0])
    for i, theta2 in enumerate(sample_angles):
        try:
            plot_linkage(params, theta2, show_coupler_point=True,
                         coupler_point_ratio=coupler_point_ratio,
                         coupler_angle_offset=coupler_angle_offset,
                         ax=ax1, title="",
                         colors={'ground': '#666666', 'crank': '#E74C3C',
                                 'coupler': '#3498DB', 'rocker': '#2ECC71',
                                 'coupler_point': '#F39C12'})
        except ValueError:
            pass

    # Subplot 2: Coupler curve
    ax2 = fig.add_subplot(gs[0, 1:])
    plot_coupler_curve(params, coupler_point_ratio, coupler_angle_offset,
                       num_points=720, ax=ax2,
                       title="Coupler Curve (连杆曲线)")

    # Subplot 3: Transmission angle
    ax3 = fig.add_subplot(gs[1, :])
    plot_transmission_angle(params, num_points=720, ax=ax3)

    # Subplot 4: Phase diagram (position + velocity)
    ax4 = fig.add_subplot(gs[2, :2])
    ax4.set_title('Phase Diagram / 相位图', fontsize=13)
    # Manually plot phase data into ax4 (left side) and ax5 (right side)
    theta2_range = np.linspace(0, 2*np.pi, 360)
    theta3_vals, theta4_vals = [], []
    omega3_vals, omega4_vals = [], []
    for theta2 in theta2_range:
        try:
            pos = position_analysis(params, theta2)
            theta3_vals.append(np.degrees(pos.theta3))
            theta4_vals.append(np.degrees(pos.theta4))
            omega3, omega4 = velocity_analysis(params, theta2, omega2)
            omega3_vals.append(omega3)
            omega4_vals.append(omega4)
        except ValueError:
            theta3_vals.append(np.nan)
            theta4_vals.append(np.nan)
            omega3_vals.append(np.nan)
            omega4_vals.append(np.nan)
    theta3_vals, theta4_vals = np.array(theta3_vals), np.array(theta4_vals)
    omega3_vals, omega4_vals = np.array(omega3_vals), np.array(omega4_vals)
    ax4.plot(np.degrees(theta2_range), theta3_vals, 'b-', linewidth=1.5, label='$\\theta_3$ (Coupler)')
    ax4.plot(np.degrees(theta2_range), theta4_vals, 'r-', linewidth=1.5, label='$\\theta_4$ (Rocker)')
    ax4.set_xlabel('Input Angle $\\theta_2$ (degrees)', fontsize=11)
    ax4.set_ylabel('Angle (degrees)', fontsize=11)
    ax4.grid(True, alpha=0.3)
    ax4.legend(fontsize=9)

    # Subplot 5: Acceleration
    ax5 = fig.add_subplot(gs[2, 2])
    plot_acceleration_phase(params, omega2, alpha2, num_points=360, ax=ax5)

    return fig
