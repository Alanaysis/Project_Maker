"""
Example 4: Efficiency Comparison
示例4: 效率对比

Demonstrates:
    - Efficiency analysis across different gear types
    - Impact of stage count on overall efficiency
    - Worm gear efficiency vs lead angle
    - Thermal considerations

演示：
    - 不同齿轮类型的效率分析
    - 级数对总效率的影响
    - 蜗轮蜗杆效率与导程角的关系
    - 热力学考虑
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.spur_gear import SpurGear
from src.efficiency import EfficiencyAnalyzer
from src.gear_ratio import GearRatioCalculator


def plot_efficiency_comparison():
    """Demonstrate efficiency comparison across configurations."""
    print("=" * 60)
    print("  Example 4: Efficiency Comparison")
    print("  示例4: 效率对比")
    print("=" * 60)
    print()

    analyzer = EfficiencyAnalyzer()

    # 1. Mesh efficiency by gear type
    print("-" * 40)
    print("1. Mesh Efficiency by Gear Type 各类型齿轮啮合效率:")
    print("-" * 40)

    gear_types = ["spur", "helical", "double_helical", "bevel", "hypoid",
                  "worm_single", "worm_double", "rack_pinion"]
    base_efficiencies = []

    for gt in gear_types:
        eff = analyzer.analyze_mesh_efficiency(gear_type=gt, pitch_line_velocity=5.0)
        base_efficiencies.append(eff)
        print(f"  {gt:20s}: {eff * 100:.2f}%")
    print()

    # 2. Impact of stage count on overall efficiency
    print("-" * 40)
    print("2. Efficiency vs Number of Stages 级数对效率的影响:")
    print("-" * 40)

    stages = list(range(1, 8))
    spur_efficiencies = []
    helical_efficiencies = []

    for n in stages:
        spur_eff = 0.98 ** n
        helical_eff = 0.985 ** n
        spur_efficiencies.append(spur_eff)
        helical_efficiencies.append(helical_eff)
        print(f"  Stages={n:1d}: Spur={spur_eff*100:.2f}%, Helical={helical_eff*100:.2f}%")
    print()

    # 3. Worm gear efficiency vs lead angle
    print("-" * 40)
    print("3. Worm Gear Efficiency vs Lead Angle 蜗轮蜗杆效率与导程角:")
    print("-" * 40)

    lead_angles = [5, 8, 10, 12, 15, 20, 25, 30]
    worm_effs_good = []
    worm_effs_poor = []

    for la in lead_angles:
        eff_good = analyzer.calculate_worm_gear_efficiency(
            lead_angle_deg=la, lubrication="good_lubrication"
        )
        eff_poor = analyzer.calculate_worm_gear_efficiency(
            lead_angle_deg=la, lubrication="poor_lubrication"
        )
        worm_effs_good.append(eff_good)
        worm_effs_poor.append(eff_poor)
        print(f"  Lambda={la:2d}°: Good={eff_good*100:.2f}%, Poor={eff_poor*100:.2f}%")
    print()

    # 4. Full efficiency analysis of a compound train
    print("-" * 40)
    print("4. Full Efficiency Analysis 完整效率分析:")
    print("-" * 40)

    # Create a 3-stage compound train
    gears = [
        SpurGear(module=2, num_teeth=15, name="G1"),
        SpurGear(module=2, num_teeth=45, name="G2"),
        SpurGear(module=2, num_teeth=18, name="G3"),
        SpurGear(module=2, num_teeth=36, name="G4"),
        SpurGear(module=2, num_teeth=20, name="G5"),
        SpurGear(module=2, num_teeth=40, name="G6"),
    ]

    eff_result = analyzer.analyze_gear_train_efficiency(
        gears=gears,
        input_power_w=5000,
        gear_type="spur",
        num_bearings=10,
        num_seals=4,
        pitch_line_velocity=8.0,
    )

    print(EfficiencyAnalyzer.print_efficiency_report(eff_result))
    print()

    # 5. Contact ratio comparison
    print("-" * 40)
    print("5. Contact Ratio Comparison 重合度对比:")
    print("-" * 40)

    # Compare different tooth count combinations
    combos = [
        (17, 17), (20, 40), (15, 45), (20, 60), (25, 50), (30, 60),
    ]
    for z1, z2 in combos:
        g1 = SpurGear(module=2, num_teeth=z1, name=f"z1_{z1}")
        g2 = SpurGear(module=2, num_teeth=z2, name=f"z2_{z2}")
        cr = analyzer.analyze_mesh_efficiency("spur")  # placeholder
        # Use ContactRatioCalculator directly
        from src.contact_ratio import ContactRatioCalculator
        cr_result = ContactRatioCalculator.calculate(g1, g2)
        quality = ContactRatioCalculator.analyze_contact_ratio(cr_result.contact_ratio)
        print(f"  Z1={z1:2d}, Z2={z2:2d}: CR={cr_result.contact_ratio:.4f}, "
              f"Quality={quality['quality']}, {quality['description']}")
    print()

    # Plot all results
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: Mesh efficiency by gear type
    ax1 = axes[0, 0]
    colors1 = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
               '#8c564b', '#e377c2', '#7f7f7f']
    bars1 = ax1.bar(gear_types, [e * 100 for e in base_efficiencies], color=colors1, alpha=0.8)
    ax1.set_xlabel('Gear Type (齿轮类型)', fontsize=10)
    ax1.set_ylabel('Mesh Efficiency (%) (啮合效率)', fontsize=10)
    ax1.set_title('Mesh Efficiency by Type 各类型齿轮啮合效率', fontsize=11, fontweight='bold')
    ax1.set_ylim(40, 101)
    ax1.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars1, base_efficiencies):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                 f'{val*100:.1f}%', ha='center', va='bottom', fontsize=7)
    plt.xticks(rotation=45, ha='right', fontsize=7)

    # Plot 2: Stages vs efficiency
    ax2 = axes[0, 1]
    ax2.plot(stages, [e * 100 for e in spur_efficiencies], 'bo-', linewidth=2,
             markersize=6, label='Spur (直齿轮)')
    ax2.plot(stages, [e * 100 for e in helical_efficiencies], 'rs-', linewidth=2,
             markersize=6, label='Helical (斜齿轮)')
    ax2.axhline(y=90, color='green', linestyle='--', alpha=0.5, label='90% threshold')
    ax2.set_xlabel('Number of Stages (级数)', fontsize=10)
    ax2.set_ylabel('Overall Efficiency (%) (总效率)', fontsize=10)
    ax2.set_title('Efficiency vs Stage Count 级数与效率', fontsize=11, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(70, 101)

    # Plot 3: Worm gear efficiency vs lead angle
    ax3 = axes[1, 0]
    ax3.plot(lead_angles, [e * 100 for e in worm_effs_good], 'go-', linewidth=2,
             markersize=6, label='Good Lubrication (良好润滑)')
    ax3.plot(lead_angles, [e * 100 for e in worm_effs_poor], 'rx-', linewidth=2,
             markersize=6, label='Poor Lubrication (较差润滑)')
    ax3.set_xlabel('Lead Angle (导程角) (degrees)', fontsize=10)
    ax3.set_ylabel('Efficiency (%) (效率)', fontsize=10)
    ax3.set_title('Worm Gear: Efficiency vs Lead Angle 蜗轮蜗杆效率与导程角',
                  fontsize=11, fontweight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 101)

    # Plot 4: Power loss breakdown
    ax4 = axes[1, 1]
    loss_labels = ['Mesh\n啮合', 'Bearing\n轴承', 'Seal\n密封', 'Windage\n风阻']
    loss_values = [
        sum(l['power_loss_w'] for l in eff_result.mesh_losses),
        eff_result.bearing_loss_w,
        eff_result.seal_loss_w,
        eff_result.windage_loss_w,
    ]
    colors4 = ['#d62728', '#ff7f0e', '#1f77b4', '#2ca02c']
    bars4 = ax4.bar(loss_labels, loss_values, color=colors4, alpha=0.8, edgecolor='black')
    ax4.set_ylabel('Power Loss (W) (功率损失)', fontsize=10)
    ax4.set_title('Power Loss Breakdown 功率损失分解', fontsize=11, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars4, loss_values):
        ax4.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10,
                 f'{val:.1f}W', ha='center', va='bottom', fontsize=8)

    plt.suptitle('Efficiency Comparison 效率对比分析',
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig('/tmp/efficiency_comparison.png', dpi=150, bbox_inches='tight')
    print("  Visualization saved to: /tmp/efficiency_comparison.png")
    print()

    # Key takeaways
    print("Key Takeaways 关键结论:")
    print("-" * 40)
    print("  1. More stages = lower overall efficiency (级数越多，总效率越低)")
    print("     Each stage multiplies efficiency: eta_total = eta^N")
    print("     每级效率相乘: 总效率 = 单级效率^级数")
    print()
    print("  2. Worm gears have self-locking capability but low efficiency")
    print("     蜗轮蜗杆可自锁但效率较低")
    print("     Use for high reduction in compact space only")
    print("     仅适用于紧凑空间的高减速比")
    print()
    print("  3. Helical gears are more efficient than spur gears")
    print("     斜齿轮比直齿轮效率更高")
    print("     But require axial thrust bearings")
    print("     但需要轴向推力轴承")
    print()
    print("  4. Planetary gears distribute load across multiple paths")
    print("     行星齿轮通过多路径分配载荷")
    print("     Higher torque density, compact design")
    print("     扭矩密度高，结构紧凑")
    print()

    print("=" * 60)
    print("  Example 4 Complete! 示例4完成!")
    print("=" * 60)


if __name__ == '__main__':
    plot_efficiency_comparison()
