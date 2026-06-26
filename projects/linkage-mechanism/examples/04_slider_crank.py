"""Slider-crank mechanism analysis.

滑块曲柄机构分析。

Demonstrates a slider-crank mechanism where:
- The crank (input) rotates fully
- The slider (output) reciprocates (linear motion)
- The connecting rod (coupler) links crank to slider

Common in internal combustion engines and compressors.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt

from src.position_analysis import FourBarParams, check_grashof


def slider_crank_position(theta2: float, a2: float, a3: float,
                          offset: float = 0.0) -> float:
    """Compute slider position for a given crank angle.

    For an inline slider-crank (offset = 0):
        x = a2*cos(theta2) + sqrt(a3^2 - a2^2*sin^2(theta2))

    For an offset slider-crank:
        x = a2*cos(theta2) + sqrt(a3^2 - (a2*sin(theta2) - offset)^2)

    Args:
        theta2: Crank angle in radians.
        a2: Crank length.
        a3: Connecting rod length.
        offset: Offset distance between crank axis and slider path.

    Returns:
        Slider position (distance from crank axis along slider path).
    """
    term = a2 * np.sin(theta2) - offset
    if abs(term) > a3:
        return np.nan  # Mechanism cannot be assembled
    return a2 * np.cos(theta2) + np.sqrt(a3**2 - term**2)


def slider_crank_velocity(theta2: float, omega2: float, a2: float,
                          a3: float, offset: float = 0.0) -> float:
    """Compute slider velocity.

    For inline slider-crank:
        v = -a2*omega2*(sin(theta2) + (a2*sin(2*theta2))/(2*sqrt(a3^2 - a2^2*sin^2(theta2))))

    Args:
        theta2: Crank angle in radians.
        omega2: Crank angular velocity (rad/s).
        a2: Crank length.
        a3: Connecting rod length.
        offset: Offset distance.

    Returns:
        Slider velocity.
    """
    sin_t2 = np.sin(theta2)
    sin_2t2 = np.sin(2 * theta2)
    denom = a3**2 - (a2 * sin_t2 - offset)**2

    if denom <= 0:
        return np.nan

    sqrt_term = np.sqrt(denom)
    v = -a2 * omega2 * (sin_t2 + (a2 * sin_2t2) / (2 * sqrt_term))
    return v


def slider_crank_acceleration(theta2: float, omega2: float, alpha2: float,
                              a2: float, a3: float, offset: float = 0.0) -> float:
    """Compute slider acceleration.

    For inline slider-crank:
        a = -a2*alpha2*sin(theta2) - a2*omega2^2*cos(theta2)
            - (a2^2*omega2^2*sin(2*theta2))/(4*a3*sqrt(1 - (a2/a3)^2*sin^2(theta2)))
            + (a2^2*omega2^2*sin(2*theta2)*(a2/a3)^2*cos(2*theta2))/(4*(1-(a2/a3)^2*sin^2(theta2))^(3/2))

    Args:
        theta2: Crank angle in radians.
        omega2: Crank angular velocity (rad/s).
        alpha2: Crank angular acceleration (rad/s^2).
        a2: Crank length.
        a3: Connecting rod length.
        offset: Offset distance.

    Returns:
        Slider acceleration.
    """
    sin_t2 = np.sin(theta2)
    sin_2t2 = np.sin(2 * theta2)
    cos_t2 = np.cos(theta2)
    denom = a3**2 - (a2 * sin_t2 - offset)**2

    if denom <= 0:
        return np.nan

    sqrt_term = np.sqrt(denom)
    term1 = -a2 * alpha2 * sin_t2
    term2 = -a2 * omega2**2 * cos_t2
    term3 = -(a2**2 * omega2**2 * sin_2t2) / (4 * sqrt_term)
    term4 = (a2**2 * omega2**2 * sin_2t2 * (a2*sin_t2 - offset)*cos_t2) / (2 * denom**(3/2))

    return term1 + term2 + term3 + term4


def main():
    print("=" * 70)
    print("Slider-Crank Mechanism Analysis / 滑块曲柄机构分析")
    print("=" * 70)

    # Mechanism parameters
    a2 = 1.0   # Crank length / 曲柄长度
    a3 = 3.0   # Connecting rod length / 连杆长度
    offset = 0.0  # Offset / 偏置

    print("\n--- Mechanism Parameters / 机构参数 ---")
    print(f"Crank a2 = {a2}")
    print(f"Connecting rod a3 = {a3}")
    print(f"Offset = {offset}")
    print(f"Ratio a2/a3 = {a2/a3:.3f}")

    # Stroke calculation
    if offset == 0:
        stroke = 2 * a2
        print(f"Stroke (行程) = 2*a2 = {stroke}")
    else:
        stroke = slider_crank_position(0, a2, a3, offset) - \
                 slider_crank_position(np.pi, a2, a3, offset)
        print(f"Stroke (行程) = {stroke:.4f}")

    # Analysis at key positions
    print("\n--- Position Analysis / 位置分析 ---")
    print(f"{'θ2(°)':>8} {'x_slider':>10} {'v_slider':>10} {'a_slider':>10}")
    print("-" * 48)

    omega2 = 10.0  # rad/s (typical for engine analysis)
    alpha2 = 0.0   # rad/s^2

    key_angles = [0, np.pi/12, np.pi/6, np.pi/4, np.pi/3, np.pi/2,
                  2*np.pi/3, 3*np.pi/4, 5*np.pi/6, np.pi,
                  7*np.pi/6, 5*np.pi/4, 4*np.pi/3, 3*np.pi/2,
                  5*np.pi/3, 7*np.pi/4, 11*np.pi/6, 2*np.pi]

    for theta2 in key_angles:
        x = slider_crank_position(theta2, a2, a3, offset)
        v = slider_crank_velocity(theta2, omega2, a2, a3, offset)
        a = slider_crank_acceleration(theta2, omega2, alpha2, a2, a3, offset)
        print(f"{np.degrees(theta2):8.1f} {x:10.4f} {v:10.4f} {a:10.4f}")

    # Stroke positions
    print("\n--- Dead Center Positions / 死点位置 ---")
    x_TDC = slider_crank_position(0, a2, a3, offset)
    x_BDC = slider_crank_position(np.pi, a2, a3, offset)
    print(f"TDC (上止点) x = {x_TDC:.4f}")
    print(f"BDC (下止点) x = {x_BDC:.4f}")
    print(f"Stroke = {abs(x_BDC - x_TDC):.4f}")

    # Maximum velocity position
    print("\n--- Maximum Velocity / 最大速度 ---")
    theta2_range = np.linspace(0, 2*np.pi, 720)
    x_vals = []
    v_vals = []
    a_vals = []
    for theta2 in theta2_range:
        x = slider_crank_position(theta2, a2, a3, offset)
        v = slider_crank_velocity(theta2, omega2, a2, a3, offset)
        a = slider_crank_acceleration(theta2, omega2, alpha2, a2, a3, offset)
        if not np.isnan(x):
            x_vals.append(x)
            v_vals.append(v)
            a_vals.append(a)

    if v_vals:
        v_arr = np.array(v_vals)
        max_vel_idx = np.argmax(np.abs(v_arr))
        print(f"Max velocity: {v_arr[max_vel_idx]:.4f} at θ2 = {np.degrees(theta2_range[max_vel_idx]):.1f}°")
        print(f"Min velocity: {v_arr[np.argmin(v_arr)]:.4f} at θ2 = {np.degrees(theta2_range[np.argmin(v_arr)]):.1f}°")

    # Create visualizations
    print("\n--- Creating Visualizations / 创建可视化 ---")

    fig, axes = plt.subplots(3, 1, figsize=(12, 12))

    # Slider position vs crank angle
    axes[0].plot(np.degrees(theta2_range), x_vals, 'b-', linewidth=2)
    axes[0].axhline(y=x_TDC, color='r', linestyle='--', alpha=0.5, label=f'TDC = {x_TDC:.3f}')
    axes[0].axhline(y=x_BDC, color='g', linestyle='--', alpha=0.5, label=f'BDC = {x_BDC:.3f}')
    axes[0].set_xlabel('Crank Angle θ2 (degrees)', fontsize=11)
    axes[0].set_ylabel('Slider Position x', fontsize=11)
    axes[0].set_title('Slider Position vs Crank Angle\n滑块位置 vs 曲柄角度', fontsize=13)
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    # Slider velocity vs crank angle
    axes[1].plot(np.degrees(theta2_range), v_vals, 'r-', linewidth=2)
    axes[1].axhline(y=0, color='k', linestyle='-', alpha=0.3)
    axes[1].set_xlabel('Crank Angle θ2 (degrees)', fontsize=11)
    axes[1].set_ylabel('Slider Velocity v', fontsize=11)
    axes[1].set_title('Slider Velocity vs Crank Angle\n滑块速度 vs 曲柄角度', fontsize=13)
    axes[1].grid(True, alpha=0.3)

    # Slider acceleration vs crank angle
    axes[2].plot(np.degrees(theta2_range), a_vals, 'g-', linewidth=2)
    axes[2].axhline(y=0, color='k', linestyle='-', alpha=0.3)
    axes[2].set_xlabel('Crank Angle θ2 (degrees)', fontsize=11)
    axes[2].set_ylabel('Slider Acceleration a', fontsize=11)
    axes[2].set_title('Slider Acceleration vs Crank Angle\n滑块加速度 vs 曲柄角度', fontsize=13)
    axes[2].grid(True, alpha=0.3)

    plt.suptitle('Slider-Crank Mechanism Analysis\n滑块曲柄机构分析',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), 'output_slider_crank.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()

    # Mechanism configuration at key positions
    fig2, axes = plt.subplots(1, 3, figsize=(15, 5))

    positions = [
        (0, "TDC (上止点)"),
        (np.pi/2, "θ2=90°"),
        (np.pi, "BDC (下止点)"),
    ]

    for idx, (theta2, label) in enumerate(positions):
        ax = axes[idx]
        x = slider_crank_position(theta2, a2, a3, offset)
        if np.isnan(x):
            continue

        # Draw mechanism
        crank_end_x = a2 * np.cos(theta2)
        crank_end_y = a2 * np.sin(theta2)
        slider_x = x

        # Crank
        ax.plot([0, crank_end_x], [0, crank_end_y], 'r-', linewidth=3, label='Crank')
        # Connecting rod
        ax.plot([crank_end_x, slider_x], [crank_end_y, offset], 'b-', linewidth=3, label='Connecting Rod')
        # Ground
        ax.plot([-0.5, slider_x + 0.5], [-0.5, -0.5], 'k--', linewidth=2, label='Ground')
        # Slider
        ax.plot(slider_x, offset, 'go', markersize=12, label='Slider')
        # Crank pivot
        ax.plot(0, 0, 'ko', markersize=8)

        ax.set_xlim(-1.5, slider_x + 1.0)
        ax.set_ylim(-1.5, 1.5)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_title(label, fontsize=12)
        ax.legend(fontsize=9)

    plt.suptitle('Slider-Crank at Key Positions\n滑块曲柄机构关键位置',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    output_path2 = os.path.join(os.path.dirname(__file__), 'output_slider_crank_positions.png')
    plt.savefig(output_path2, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path2}")
    plt.close()

    print("\n" + "=" * 70)
    print("Slider-crank analysis complete!")
    print("滑块曲柄机构分析完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
