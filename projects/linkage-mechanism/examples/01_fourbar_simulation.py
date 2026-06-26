"""Four-bar linkage simulation.

四连杆机构仿真演示。

This script demonstrates the complete analysis pipeline:
1. Define a crank-rocker mechanism
2. Perform position, velocity, and acceleration analysis
3. Visualize the mechanism and its coupler curve
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt

from src.position_analysis import FourBarParams, check_grashof, GrashofType, classify_linkage_type, LinkageType
from src.visualization import (
    plot_linkage,
    plot_coupler_curve,
    plot_transmission_angle,
    create_full_analysis_figure,
    plot_phase_diagram,
)


def main():
    print("=" * 70)
    print("Four-Bar Linkage Simulation / 四连杆机构仿真")
    print("=" * 70)

    # Define a crank-rocker mechanism
    # 定义曲柄摇杆机构
    print("\n--- Mechanism Parameters / 机构参数 ---")
    params = FourBarParams(
        a1=4.0,   # Ground link / 机架
        a2=1.5,   # Crank (shortest) / 曲柄（最短）
        a3=4.5,   # Coupler / 连杆
        a4=3.5,   # Rocker / 摇杆
        o2=(0.0, 0.0),
        o4=(4.0, 0.0),
    )

    print(f"Ground link a1 = {params.a1}")
    print(f"Crank a2 = {params.a2}")
    print(f"Coupler a3 = {params.a3}")
    print(f"Rocker a4 = {params.a4}")

    # Check Grashof condition
    grashof = check_grashof(params)
    linkage_type = classify_linkage_type(params)
    print(f"\nGrashof condition: {grashof.value}")
    print(f"Linkage type: {linkage_type.value}")

    # Grashof inequality check
    links = [params.a1, params.a2, params.a3, params.a4]
    s = min(links)
    l = max(links)
    print(f"s + l = {s + l:.4f}, p + q = {sum(links) - s - l:.4f}")

    # Analyze mechanism at several positions
    print("\n--- Position Analysis / 位置分析 ---")
    sample_angles = [0, np.pi/6, np.pi/4, np.pi/3, np.pi/2, 2*np.pi/3, np.pi]
    for theta2 in sample_angles:
        try:
            from src.position_analysis import position_analysis
            pos = position_analysis(params, theta2)
            print(f"theta2={np.degrees(theta2):6.1f}° -> "
                  f"theta3={np.degrees(pos.theta3):7.1f}°, "
                  f"theta4={np.degrees(pos.theta4):7.1f}°, "
                  f"mode={pos.assembly_mode}")
        except ValueError as e:
            print(f"theta2={np.degrees(theta2):6.1f}° -> Cannot assemble: {e}")

    # Create visualizations
    print("\n--- Creating Visualizations / 创建可视化 ---")

    fig1, ax1 = plt.subplots(figsize=(8, 6))
    for i, theta2 in enumerate(sample_angles):
        try:
            plot_linkage(params, theta2, show_coupler_point=True,
                         coupler_point_ratio=(0.5, 0.3),
                         coupler_angle_offset=0.0,
                         ax=ax1, title="")
        except ValueError:
            pass
    ax1.set_title("Four-Bar Linkage at Multiple Positions\n四连杆多位置图", fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), 'output_fourbar_linkage.png'),
                dpi=150, bbox_inches='tight')
    print("Saved: output_fourbar_linkage.png")
    plt.close()

    # Coupler curve
    fig2, ax2 = plt.subplots(figsize=(10, 8))
    plot_coupler_curve(params, coupler_point_ratio=(0.5, 0.3),
                       coupler_angle_offset=0.0, num_points=720, ax=ax2)
    ax2.set_title("Coupler Curve of Crank-Rocker Mechanism\n曲柄摇杆机构连杆曲线", fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), 'output_coupler_curve.png'),
                dpi=150, bbox_inches='tight')
    print("Saved: output_coupler_curve.png")
    plt.close()

    # Transmission angle
    fig3, ax3 = plt.subplots(figsize=(10, 4))
    plot_transmission_angle(params, num_points=720, ax=ax3)
    ax3.set_title("Transmission Angle of Crank-Rocker\n曲柄摇杆传动角", fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), 'output_transmission_angle.png'),
                dpi=150, bbox_inches='tight')
    print("Saved: output_transmission_angle.png")
    plt.close()

    # Full analysis figure
    fig4 = create_full_analysis_figure(
        params,
        coupler_point_ratio=(0.5, 0.3),
        omega2=1.0,
        alpha2=0.0,
        sample_angles=[0, np.pi/3, 2*np.pi/3, np.pi],
    )
    fig4.suptitle("Complete Four-Bar Linkage Analysis\n四连杆机构完整分析",
                  fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), 'output_full_analysis.png'),
                dpi=150, bbox_inches='tight')
    print("Saved: output_full_analysis.png")
    plt.close()

    # Phase diagram
    fig5, (ax5a, ax5b) = plt.subplots(1, 2, figsize=(14, 5))
    plot_phase_diagram(params, omega2=1.0, alpha2=0.0, num_points=360, ax1=ax5a)
    ax5a.set_title("Phase Diagram / 相位图", fontsize=13)
    from src.visualization import plot_acceleration_phase
    plot_acceleration_phase(params, omega2=1.0, alpha2=0.0, num_points=360, ax=ax5b)
    ax5b.set_title("Acceleration Phase / 加速度相位", fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), 'output_phase_diagram.png'),
                dpi=150, bbox_inches='tight')
    print("Saved: output_phase_diagram.png")
    plt.close()

    print("\n" + "=" * 70)
    print("Simulation complete! Check the output PNG files.")
    print("仿真完成！请查看输出的 PNG 文件。")
    print("=" * 70)


if __name__ == "__main__":
    main()
