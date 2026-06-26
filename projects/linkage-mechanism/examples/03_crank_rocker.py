"""Crank-rocker mechanism analysis.

曲柄摇杆机构分析。

Demonstrates a crank-rocker mechanism where:
- The crank (input) rotates fully
- The rocker (output) oscillates within a limited range
- The transmission angle varies throughout the cycle

This is one of the most common four-bar linkage configurations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt

from src.position_analysis import (
    FourBarParams,
    check_grashof,
    classify_linkage_type,
    GrashofType,
    LinkageType,
)
from src.velocity_analysis import velocity_analysis, compute_transmission_angle
from src.acceleration_analysis import acceleration_analysis
from src.visualization import (
    plot_linkage,
    plot_transmission_angle,
    plot_phase_diagram,
    plot_acceleration_phase,
)


def main():
    print("=" * 70)
    print("Crank-Rocker Mechanism Analysis / 曲柄摇杆机构分析")
    print("=" * 70)

    # Define a crank-rocker mechanism
    # Grashof condition: s + l < p + q
    # Shortest link is adjacent to ground => crank-rocker
    params = FourBarParams(
        a1=4.0,   # Ground link
        a2=1.5,   # Crank (shortest link)
        a3=4.5,   # Coupler
        a4=3.5,   # Rocker
        o2=(0.0, 0.0),
        o4=(4.0, 0.0),
    )

    print("\n--- Mechanism Parameters / 机构参数 ---")
    print(f"a1 (ground) = {params.a1}")
    print(f"a2 (crank)  = {params.a2}")
    print(f"a3 (coupler) = {params.a3}")
    print(f"a4 (rocker)  = {params.a4}")

    grashof = check_grashof(params)
    linkage_type = classify_linkage_type(params)
    print(f"\nGrashof condition: {grashof.value}")
    print(f"Linkage type: {linkage_type.value}")

    links = [params.a1, params.a2, params.a3, params.a4]
    s, l = min(links), max(links)
    print(f"Verification: s+l={s+l:.2f} {'<' if s+l < sum(links)-s-l else '>='} "
          f"p+q={sum(links)-s-l:.2f}")

    # Crank can rotate fully (Grashof condition met with shortest = crank)
    print("\n--- Crank Rotation Range / 曲柄旋转范围 ---")
    print("Crank can rotate through full 360 degrees (Grashof condition met)")

    # Analyze rocker oscillation limits
    print("\n--- Rocker Oscillation Limits / 摇杆摆动范围 ---")
    from src.position_analysis import compute_rocker_limits
    theta4_min, theta4_max = compute_rocker_limits(params)
    print(f"Rocker angle range: [{np.degrees(theta4_min):.2f}°, {np.degrees(theta4_max):.2f}°]")
    print(f"Rocker oscillation amplitude: {np.degrees(theta4_max - theta4_min):.2f}°")

    # Detailed analysis at key positions
    print("\n--- Detailed Analysis at Key Positions / 关键位置详细分析 ---")
    print(f"{'θ2(°)':>8} {'θ3(°)':>8} {'θ4(°)':>8} {'μ(°)':>8} "
          f"{'ω3(rad/s)':>10} {'ω4(rad/s)':>10} "
          f"{'α3(rad/s²)':>10} {'α4(rad/s²)':>10}")
    print("-" * 86)

    omega2 = 1.0  # rad/s
    alpha2 = 0.0  # rad/s^2
    key_angles = [0, np.pi/6, np.pi/4, np.pi/3, np.pi/2,
                  2*np.pi/3, 3*np.pi/4, 5*np.pi/6, np.pi,
                  7*np.pi/6, 5*np.pi/4, 4*np.pi/3, 3*np.pi/2,
                  5*np.pi/3, 7*np.pi/4, 11*np.pi/6, 2*np.pi]

    for theta2 in key_angles:
        try:
            from src.position_analysis import position_analysis
            pos = position_analysis(params, theta2)
            omega3, omega4 = velocity_analysis(params, theta2, omega2)
            alpha3, alpha4 = acceleration_analysis(params, theta2, omega2, alpha2)
            mu = compute_transmission_angle(params, theta2)

            print(f"{np.degrees(theta2):8.1f} {np.degrees(pos.theta3):8.1f} "
                  f"{np.degrees(pos.theta4):8.1f} {np.degrees(mu):8.1f} "
                  f"{omega3:10.3f} {omega4:10.3f} "
                  f"{alpha3:10.3f} {alpha4:10.3f}")
        except ValueError as e:
            print(f"{np.degrees(theta2):8.1f} {'N/A':>8} {'N/A':>8} "
                  f"{'N/A':>8} {'N/A':>10} {'N/A':>10} "
                  f"{'N/A':>10} {'N/A':>10}")

    # Find maximum and minimum transmission angles
    print("\n--- Transmission Angle Statistics / 传动角统计 ---")
    theta2_range = np.linspace(0, 2*np.pi, 720)
    mu_values = []
    for theta2 in theta2_range:
        try:
            mu = compute_transmission_angle(params, theta2)
            mu_values.append(np.degrees(mu))
        except ValueError:
            pass

    if mu_values:
        mu_arr = np.array(mu_values)
        print(f"Min transmission angle: {mu_arr.min():.2f}°")
        print(f"Max transmission angle: {mu_arr.max():.2f}°")
        print(f"Mean transmission angle: {mu_arr.mean():.2f}°")

        # Check if transmission angle is acceptable
        if mu_arr.min() >= 40 and mu_arr.max() <= 140:
            print("Transmission angle is within acceptable range [40°, 140°]")
        else:
            print("WARNING: Transmission angle may be outside acceptable range!")

    # Create visualizations
    print("\n--- Creating Visualizations / 创建可视化 ---")

    # Transmission angle plot
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    plot_transmission_angle(params, num_points=720, ax=ax1)
    ax1.set_title("Crank-Rocker: Transmission Angle\n曲柄摇杆传动角", fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), 'output_crank_rocker_transmission.png'),
                dpi=150, bbox_inches='tight')
    print("Saved: output_crank_rocker_transmission.png")
    plt.close()

    # Phase diagram
    fig2, (ax2a, ax2b) = plt.subplots(1, 2, figsize=(14, 5))
    plot_phase_diagram(params, omega2=1.0, alpha2=0.0, num_points=360, ax1=ax2a)
    ax2a.set_title("Crank-Rocker Phase Diagram\n曲柄摇杆相位图", fontsize=13)
    plot_acceleration_phase(params, omega2=1.0, alpha2=0.0, num_points=360, ax=ax2b)
    ax2b.set_title("Crank-Rocker Acceleration\n曲柄摇杆加速度", fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), 'output_crank_rocker_phase.png'),
                dpi=150, bbox_inches='tight')
    print("Saved: output_crank_rocker_phase.png")
    plt.close()

    # Linkage at min/max transmission angles
    print("\n--- Linkage at Critical Positions / 临界位置连杆图 ---")
    mu_max_idx = np.argmax(mu_values)
    mu_min_idx = np.argmin(mu_values)
    theta2_at_mu_max = theta2_range[mu_max_idx]
    theta2_at_mu_min = theta2_range[mu_min_idx]

    fig3, axes = plt.subplots(1, 2, figsize=(14, 6))
    plot_linkage(params, theta2_at_mu_max, show_coupler_point=True,
                 coupler_point_ratio=(0.5, 0.3), ax=axes[0],
                 title=f"Max Transmission Angle (最大传动角)\n"
                       f"$\\theta_2$={np.degrees(theta2_at_mu_max):.1f}°, "
                       f"$\\mu$={mu_arr[mu_max_idx]:.1f}°")
    plot_linkage(params, theta2_at_mu_min, show_coupler_point=True,
                 coupler_point_ratio=(0.5, 0.3), ax=axes[1],
                 title=f"Min Transmission Angle (最小传动角)\n"
                       f"$\\theta_2$={np.degrees(theta2_at_mu_min):.1f}°, "
                       f"$\\mu$={mu_arr[mu_min_idx]:.1f}°")
    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), 'output_crank_rocker_critical.png'),
                dpi=150, bbox_inches='tight')
    print("Saved: output_crank_rocker_critical.png")
    plt.close()

    print("\n" + "=" * 70)
    print("Crank-rocker analysis complete!")
    print("曲柄摇杆机构分析完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
