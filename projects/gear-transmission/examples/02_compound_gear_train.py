"""
Example 2: Compound Gear Train
示例2: 复合齿轮系

Demonstrates:
    - Compound gear train design
    - Multi-stage ratio calculation
    - Speed and torque at each stage
    - Performance comparison

演示：
    - 复合齿轮系设计
    - 多级传动比计算
    - 各级速度和扭矩
    - 性能对比
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.spur_gear import SpurGear
from src.gear_ratio import GearRatioCalculator
from src.transmission import TransmissionCalculator
from src.gear_train import CompoundGearTrain
from src.efficiency import EfficiencyAnalyzer


def plot_compound_gear_train():
    """Demonstrate a compound gear train simulation."""
    print("=" * 60)
    print("  Example 2: Compound Gear Train")
    print("  示例2: 复合齿轮系")
    print("=" * 60)
    print()

    # Design a compound gear train for high reduction
    # 设计一个高减速比的复合齿轮系
    print("Designing a compound gear train for high reduction...")
    print("设计高减速比复合齿轮系...")
    print()

    # Create a 3-stage compound gear train
    # 创建3级复合齿轮系
    train = CompoundGearTrain()
    train.add_stage(driver_teeth=15, driven_teeth=45, module=2.0)  # Stage 1: 3:1 reduction
    train.add_stage(driver_teeth=18, driven_teeth=36, module=2.0)  # Stage 2: 2:1 reduction
    train.add_stage(driver_teeth=20, driven_teeth=40, module=2.0)  # Stage 3: 2:1 reduction

    overall_ratio = train.overall_ratio
    print(f"Overall Gear Ratio (总传动比): {overall_ratio:.4f}")
    print(f"  = (45/15) * (36/18) * (40/20)")
    print(f"  = 3 * 2 * 2 = 12")
    print()

    # Stage-by-stage analysis
    print("-" * 40)
    print("Stage-by-Stage Analysis 逐级分析:")
    print("-" * 40)

    stages = train.stage_by_stage_analysis(
        input_speed_rpm=3000,
        input_torque_nm=5,
        mesh_type="spur",
    )

    for stage in stages:
        print(f"  Stage {stage['stage']} ({stage['driver']} -> {stage['driven']}):")
        print(f"    Ratio: {stage['driver_teeth']} -> {stage['driven_teeth']} = {stage['stage_ratio']:.4f}")
        print(f"    Speed: {stage['speed_rpm']} RPM")
        print(f"    Torque: {stage['torque_nm']:.4f} N·m")
        print(f"    Power: {stage['power_w']:.2f} W")
        print(f"    Cumulative Efficiency: {stage['cumulative_efficiency']}%")
        print()

    # Overall transmission result
    result = train.calculate_transmission(
        input_speed_rpm=3000,
        input_torque_nm=5,
        mesh_type="spur",
    )

    summary = result.summary()
    print("-" * 40)
    print("Overall Results 总体结果:")
    print("-" * 40)
    print(f"  Input:  {summary['input_speed_rpm']} RPM, {summary['input_torque_nm']} N·m")
    print(f"  Output: {summary['output_speed_rpm']} RPM, {summary['output_torque_nm']:.4f} N·m")
    print(f"  Ratio:  {summary['overall_ratio']:.4f}")
    print(f"  Efficiency: {summary['efficiency'] * 100:.2f}%")
    print(f"  Power Loss: {summary['power_loss_w']:.2f} W ({summary['power_loss_pct']:.2f}%)")
    print()

    # Plot results
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: Speed vs Stage
    ax1 = axes[0, 0]
    stage_nums = [s['stage'] for s in stages]
    speeds = [s['speed_rpm'] for s in stages]
    ax1.plot([0] + stage_nums, [3000] + speeds, 'bo-', linewidth=2, markersize=8)
    ax1.set_xlabel('Stage (级)', fontsize=11)
    ax1.set_ylabel('Speed (RPM)', fontsize=11)
    ax1.set_title('Speed vs Stage 各级转速', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')

    # Plot 2: Torque vs Stage
    ax2 = axes[0, 1]
    torques = [s['torque_nm'] for s in stages]
    ax2.plot([0] + stage_nums, [5] + torques, 'rs-', linewidth=2, markersize=8)
    ax2.set_xlabel('Stage (级)', fontsize=11)
    ax2.set_ylabel('Torque (N·m)', fontsize=11)
    ax2.set_title('Torque vs Stage 各级扭矩', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')

    # Plot 3: Efficiency vs Stage
    ax3 = axes[1, 0]
    effs = [s['cumulative_efficiency'] for s in stages]
    ax3.plot([0] + stage_nums, [100] + effs, 'g^-^-', linewidth=2, markersize=8)
    ax3.set_xlabel('Stage (级)', fontsize=11)
    ax3.set_ylabel('Efficiency (%)', fontsize=11)
    ax3.set_title('Cumulative Efficiency 累积效率', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(80, 102)

    # Plot 4: Gear arrangement schematic
    ax4 = axes[1, 1]
    ax4.set_xlim(0, 10)
    ax4.set_ylim(0, 10)
    ax4.set_aspect('equal')

    # Draw compound gear schematic
    gear_positions = [
        (1.5, 5, 15, 'steelblue', 'Z1=15'),
        (3.5, 5, 45, 'coral', 'Z2=45'),
        (3.5, 7.5, 18, 'steelblue', 'Z3=18'),
        (6.0, 7.5, 36, 'coral', 'Z4=36'),
        (6.0, 2.5, 20, 'steelblue', 'Z5=20'),
        (8.0, 2.5, 40, 'coral', 'Z6=40'),
    ]

    for x, y, teeth, color, label in gear_positions:
        radius = teeth * 2.0 / 20  # Scaled for visualization
        circle = plt.Circle((x, y), radius, fill=True, facecolor=color,
                            alpha=0.3, edgecolor=color, linewidth=2)
        ax4.add_patch(circle)
        ax4.plot(x, y, 'o', color=color, markersize=6)
        ax4.text(x, y - radius - 0.3, label, ha='center', fontsize=8, fontweight='bold')

    # Draw shafts (shared shafts shown as thick lines)
    ax4.plot([3.5, 3.5], [4.5, 8.0], 'k-', linewidth=4, alpha=0.5)
    ax4.plot([6.0, 6.0], [1.5, 8.0], 'k-', linewidth=4, alpha=0.5)

    # Draw meshing lines
    ax4.plot([3.5, 1.5], [5, 5], 'k--', linewidth=1, alpha=0.5)
    ax4.plot([6.0, 3.5], [7.5, 7.5], 'k--', linewidth=1, alpha=0.5)
    ax4.plot([8.0, 6.0], [2.5, 2.5], 'k--', linewidth=1, alpha=0.5)

    ax4.text(5, 9.5, 'Compound Gear Train Layout 复合齿轮系布局',
             ha='center', fontsize=11, fontweight='bold')
    ax4.text(5, 0.5, 'Shared shafts shown as thick black lines',
             ha='center', fontsize=8, style='italic')
    ax4.axis('off')

    plt.suptitle('Compound Gear Train Analysis 复合齿轮系分析',
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig('/tmp/gear_train_compound.png', dpi=150, bbox_inches='tight')
    print("  Visualization saved to: /tmp/gear_train_compound.png")
    print()

    # Design recommendations
    print("Design Recommendations 设计建议:")
    print("-" * 40)

    # Check for undercutting
    all_gears = train.create_gears()
    for gear in all_gears:
        if gear.undercut_warning:
            print(f"  WARNING: {gear.name} ({gear.num_teeth} teeth) may experience undercutting!")
            print(f"    Minimum teeth to avoid undercutting: {gear.standard_min_teeth}")

    # Efficiency improvement suggestions
    if overall_ratio > 10:
        print(f"  High ratio ({overall_ratio:.1f}:1) achieved in {train.num_stages} stages.")
        print(f"  Consider: helical gears for smoother operation, or planetary for compactness.")

    print()
    print("=" * 60)
    print("  Example 2 Complete! 示例2完成!")
    print("=" * 60)


if __name__ == '__main__':
    plot_compound_gear_train()
