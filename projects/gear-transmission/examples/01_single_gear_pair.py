"""
Example 1: Single Gear Pair Simulation
示例1: 单级齿轮副仿真

Demonstrates:
    - Creating spur gears
    - Calculating gear ratio
    - Transmission analysis
    - Visualizing gear geometry

演示：
    - 创建直齿轮
    - 计算齿轮比
    - 传动分析
    - 可视化齿轮几何
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from src.spur_gear import SpurGear
from src.gear_ratio import GearRatioCalculator, GearPair
from src.transmission import TransmissionCalculator
from src.contact_ratio import ContactRatioCalculator


def create_gear_circle(ax, center_x, center_y, outer_radius, root_radius, num_teeth, color, name):
    """Draw a simplified gear representation."""
    # Draw root circle
    root_circle = plt.Circle((center_x, center_y), root_radius,
                              fill=False, edgecolor='gray', linewidth=1, linestyle='--')
    ax.add_patch(root_circle)

    # Draw pitch circle
    pitch_radius = (outer_radius + root_radius) / 2
    pitch_circle = plt.Circle((center_x, center_y), pitch_radius,
                              fill=False, edgecolor='blue', linewidth=1.5, linestyle='-')
    ax.add_patch(pitch_circle)

    # Draw outer circle
    outer_circle = plt.Circle((center_x, center_y), outer_radius,
                              fill=True, facecolor=color, alpha=0.3,
                              edgecolor=color, linewidth=2)
    ax.add_patch(outer_circle)

    # Draw teeth (simplified as rectangles)
    tooth_height = (outer_radius - root_radius)
    tooth_width = math.pi * outer_radius / num_teeth * 0.8

    for i in range(num_teeth):
        angle = 2 * math.pi * i / num_teeth
        # Tooth center position
        tx = center_x + outer_radius * math.cos(angle)
        ty = center_y + outer_radius * math.sin(angle)

        # Small tooth representation
        tooth_angle = angle
        dx = tooth_width / 2 * math.cos(tooth_angle + math.pi / 2)
        dy = tooth_width / 2 * math.sin(tooth_angle + math.pi / 2)

        tooth = patches.FancyBboxPatch(
            (tx - dx - tooth_height * 0.3 * math.cos(angle),
             ty - dy - tooth_height * 0.3 * math.sin(angle)),
            tooth_height * 0.6,
            tooth_width,
            angle=math.degrees(angle),
            fill=True, facecolor=color, alpha=0.5,
            edgecolor=color, linewidth=1
        )
        ax.add_patch(tooth)

    # Center mark
    ax.plot(center_x, center_y, 'ko', markersize=5)
    ax.plot([center_x - 3, center_x + 3], [center_y, center_y], 'k-', linewidth=1)
    ax.plot([center_x, center_x], [center_y - 3, center_y + 3], 'k-', linewidth=1)

    # Label
    ax.text(center_x, center_y - outer_radius - 15, name,
            ha='center', va='top', fontsize=10, fontweight='bold')


def plot_single_gear_pair():
    """Demonstrate a single gear pair simulation."""
    print("=" * 60)
    print("  Example 1: Single Gear Pair Simulation")
    print("  示例1: 单级齿轮副仿真")
    print("=" * 60)
    print()

    # Create gear pair
    # 创建齿轮副
    module = 2.0
    driver = SpurGear(
        module=module,
        num_teeth=20,
        pressure_angle_deg=20,
        face_width=15,
        name="主动轮 (Driver)",
    )
    driven = SpurGear(
        module=module,
        num_teeth=40,
        pressure_angle_deg=20,
        face_width=15,
        name="从动轮 (Driven)",
    )

    print(f"Gear 1 (齿轮1): {driver}")
    print(f"  模数 (Module):        {driver.module} mm")
    print(f"  齿数 (Teeth):         {driver.num_teeth}")
    print(f"  压力角 (Pressure):    {driver.pressure_angle_deg}°")
    print(f"  分度圆直径 (Pitch D): {driver.pitch_diameter:.2f} mm")
    print(f"  齿顶圆直径 (OD):      {driver.outside_diameter:.2f} mm")
    print(f"  齿根圆直径 (Root D):  {driver.root_diameter:.2f} mm")
    print()

    print(f"Gear 2 (齿轮2): {driven}")
    print(f"  模数 (Module):        {driven.module} mm")
    print(f"  齿数 (Teeth):         {driven.num_teeth}")
    print(f"  分度圆直径 (Pitch D): {driven.pitch_diameter:.2f} mm")
    print(f"  齿顶圆直径 (OD):      {driven.outside_diameter:.2f} mm")
    print()

    # Gear ratio calculation
    print("-" * 40)
    print("Gear Ratio Analysis 齿轮比分析:")
    print("-" * 40)

    ratio_calc = GearRatioCalculator()
    gear_pair = GearPair(
        driver=driver.name,
        driven=driven.name,
        driver_teeth=driver.num_teeth,
        driven_teeth=driven.num_teeth,
        driver_module=module,
        driven_module=module,
    )

    ratio = gear_pair.gear_ratio
    speed_ratio = gear_pair.speed_ratio
    torque_ratio = gear_pair.torque_ratio

    print(f"  传动比 (Gear Ratio) i = z2/z1 = {driven.num_teeth}/{driver.num_teeth} = {ratio:.4f}")
    print(f"  转速比 (Speed Ratio)  = 1/i = {speed_ratio:.4f}")
    print(f"  扭矩比 (Torque Ratio) = i = {torque_ratio:.4f}")
    print(f"  中心距 (Center Dist)  = {gear_pair.center_distance:.2f} mm")
    print()

    # Transmission analysis
    print("-" * 40)
    print("Transmission Analysis 传动分析:")
    print("-" * 40)

    calc = TransmissionCalculator("spur")
    result = calc.calculate_gear_pair(
        driver=driver,
        driven=driven,
        input_speed_rpm=1500,
        input_torque_nm=10,
        mesh_type="spur",
    )

    summary = result.summary()
    print(f"  Input Speed (输入转速):   {summary['input_speed_rpm']} RPM")
    print(f"  Output Speed (输出转速):  {summary['output_speed_rpm']} RPM")
    print(f"  Speed Reduction (减速比):  {summary['speed_reduction']}")
    print(f"  Input Torque (输入扭矩):   {summary['input_torque_nm']} N·m")
    print(f"  Output Torque (输出扭矩):  {summary['output_torque_nm']} N·m")
    print(f"  Torque Amplification (扭矩放大): {summary['torque_amplification']}")
    print(f"  Input Power (输入功率):    {summary['input_power_w']} W")
    print(f"  Output Power (输出功率):   {summary['output_power_w']} W")
    print(f"  Power Loss (功率损失):     {summary['power_loss_w']} W ({summary['power_loss_pct']}%)")
    print(f"  Efficiency (效率):         {summary['efficiency']}%")
    print()

    # Contact ratio
    print("-" * 40)
    print("Contact Ratio Analysis 重合度分析:")
    print("-" * 40)

    cr_result = ContactRatioCalculator.calculate(driver, driven)
    cr_summary = cr_result.summary()
    print(f"  Contact Ratio (重合度): {cr_summary['contact_ratio']}")
    print(f"  Path of Contact (啮合路径): {cr_summary['path_of_contact_mm']} mm")
    print(f"  Is Adequate (是否满足): {cr_summary['is_adequate']}")
    print(f"  {cr_summary['recommendation']}")
    print()

    # Plot gear visualization
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    # Calculate positions
    center_dist = gear_pair.center_distance
    r1 = driver.outside_diameter / 2
    r2 = driven.outside_diameter / 2

    # Position gears
    x1 = center_dist / 2
    y1 = 0
    x2 = -center_dist / 2
    y2 = 0

    # Draw gears
    create_gear_circle(ax, x1, y1, r1, driver.root_diameter / 2,
                       driver.num_teeth, 'steelblue', driver.name)
    create_gear_circle(ax, x2, y2, r2, driven.root_diameter / 2,
                       driven.num_teeth, 'coral', driven.name)

    # Draw center line
    ax.plot([x1, x2], [y1, y2], 'k--', linewidth=1, alpha=0.3, label='Center Line 中心线')

    # Draw pitch circles
    pitch_r1 = driver.pitch_diameter / 2
    pitch_r2 = driven.pitch_diameter / 2
    pc1 = plt.Circle((x1, y1), pitch_r1, fill=False, edgecolor='blue',
                     linewidth=2, linestyle='-', alpha=0.7)
    pc2 = plt.Circle((x2, y2), pitch_r2, fill=False, edgecolor='red',
                     linewidth=2, linestyle='-', alpha=0.7)
    ax.add_patch(pc1)
    ax.add_patch(pc2)

    # Add rotation arrows
    ax.annotate('', xy=(x1 + r1 + 30, y1), xytext=(x1 + r1 + 10, y1 + 20),
                arrowprops=dict(arrowstyle='->', color='green', lw=2))
    ax.text(x1 + r1 + 20, y1 + 30, 'ω1', color='green', fontsize=12, fontweight='bold')

    ax.annotate('', xy=(x2 - r2 - 30, y2), xytext=(x2 - r2 - 10, y2 + 20),
                arrowprops=dict(arrowstyle='->', color='orange', lw=2))
    ax.text(x2 - r2 - 50, y2 + 30, 'ω2', color='orange', fontsize=12, fontweight='bold')

    ax.set_xlim(-r2 - 80, r1 + 80)
    ax.set_ylim(-max(r1, r2) - 60, max(r1, r2) + 60)
    ax.set_aspect('equal')
    ax.set_xlabel('X (mm)', fontsize=11)
    ax.set_ylabel('Y (mm)', fontsize=11)
    ax.set_title('Single Gear Pair 单级齿轮副', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/tmp/gear_pair_single.png', dpi=150, bbox_inches='tight')
    print("  Visualization saved to: /tmp/gear_pair_single.png")
    print()

    # Ratio analysis
    ratio_analysis = ratio_calc.analyze_ratio(ratio)
    print("Ratio Analysis 传动比分析:")
    print(f"  Type (类型): {ratio_analysis['type']}")
    print(f"  Behavior (特性): {ratio_analysis['behavior']}")
    print()

    print("=" * 60)
    print("  Example 1 Complete! 示例1完成!")
    print("=" * 60)

    return result, cr_result


if __name__ == '__main__':
    plot_single_gear_pair()
