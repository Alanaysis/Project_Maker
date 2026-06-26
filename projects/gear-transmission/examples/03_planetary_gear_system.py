"""
Example 3: Planetary Gear System
示例3: 行星齿轮系统

Demonstrates:
    - Planetary gear geometry
    - Speed analysis for different configurations
    - All possible operating modes
    - Torque distribution

演示：
    - 行星齿轮几何
    - 不同配置的转速分析
    - 所有可能的运行模式
    - 扭矩分配
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
from src.gear_train import PlanetaryGearTrain
from src.efficiency import EfficiencyAnalyzer


def plot_planary_gear_system(planetary: PlanetaryGearTrain, fixed: str = "ring"):
    """Visualize a planetary gear system."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    # Get pitch radii
    radii = planetary.pitch_radii
    sun_r = radii['sun']
    planet_r = radii['planet']
    ring_r = radii['ring']
    carrier_r = radii['carrier']

    center_x, center_y = 5, 5

    # Draw ring gear (internal)
    ring_circle = plt.Circle((center_x, center_y), ring_r,
                              fill=False, edgecolor='darkred', linewidth=3)
    ax.add_patch(ring_circle)
    # Fill inside ring
    ring_fill = plt.Circle((center_x, center_y), ring_r,
                            fill=True, facecolor='mistyrose', alpha=0.2)
    ax.add_patch(ring_fill)

    # Draw carrier
    carrier_circle = plt.Circle((center_x, center_y), carrier_r,
                                 fill=False, edgecolor='gray', linewidth=1.5,
                                 linestyle='--', alpha=0.5)
    ax.add_patch(carrier_circle)

    # Draw sun gear
    sun_circle = plt.Circle((center_x, center_y), sun_r,
                             fill=True, facecolor='steelblue', alpha=0.4,
                             edgecolor='darkblue', linewidth=2)
    ax.add_patch(sun_circle)
    ax.text(center_x, center_y, f"Sun\nZ={planetary.sun_teeth}",
            ha='center', va='center', fontsize=9, fontweight='bold')

    # Draw planet gears
    for i in range(planetary.num_planets):
        angle = 2 * math.pi * i / planetary.num_planets
        px = center_x + carrier_r * math.cos(angle)
        py = center_y + carrier_r * math.sin(angle)

        planet_circle = plt.Circle((px, py), planet_r,
                                    fill=True, facecolor='coral', alpha=0.4,
                                    edgecolor='darkorange', linewidth=2)
        ax.add_patch(planet_circle)

        # Label
        label_offset = planet_r + 15
        lx = px + label_offset * math.cos(angle)
        ly = py + label_offset * math.sin(angle)
        ax.text(lx, ly, f"P{i+1}\nZ={planetary.planet_teeth}",
                ha='center', va='center', fontsize=8, fontweight='bold')

        # Draw planet center mark
        ax.plot(px, py, 'o', color='darkorange', markersize=5)

    # Draw carrier arms
    for i in range(planetary.num_planets):
        angle = 2 * math.pi * i / planetary.num_planets
        ex = center_x + carrier_r * math.cos(angle)
        ey = center_y + carrier_r * math.sin(angle)
        ax.plot([center_x, ex], [center_y, ey], 'k-', linewidth=2, alpha=0.5)

    # Draw center
    ax.plot(center_x, center_y, 'ko', markersize=8)

    # Add annotations
    ax.text(center_x, center_y - ring_r - 30,
            f"Ring (齿圈) Z={planetary.ring_teeth}",
            ha='center', fontsize=10, fontweight='bold', color='darkred')

    ax.text(center_x, center_y + sun_r + 20,
            f"Sun (太阳轮) Z={planetary.sun_teeth}",
            ha='center', fontsize=10, fontweight='bold', color='darkblue')

    # Fixed component indicator
    if fixed == "ring":
        ax.text(center_x, center_y + ring_r + 15,
                "Ring Fixed (齿圈固定)", ha='center', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

    ax.set_xlim(center_x - ring_r - 40, center_x + ring_r + 40)
    ax.set_ylim(center_y - ring_r - 50, center_y + ring_r + 40)
    ax.set_aspect('equal')
    ax.set_title(
        f'Planetary Gear System 行星齿轮系\n'
        f'Sun={planetary.sun_teeth}, Planets={planetary.planet_teeth}x{planetary.num_planets}, '
        f'Ring={planetary.ring_teeth}',
        fontsize=13, fontweight='bold'
    )
    ax.grid(True, alpha=0.3)
    ax.axis('equal')

    plt.tight_layout()
    plt.savefig('/tmp/planetary_gear.png', dpi=150, bbox_inches='tight')
    print("  Visualization saved to: /tmp/planetary_gear.png")


def analyze_planetary_system():
    """Demonstrate a planetary gear system."""
    print("=" * 60)
    print("  Example 3: Planetary Gear System")
    print("  示例3: 行星齿轮系统")
    print("=" * 60)
    print()

    # Create a planetary gear set
    # Sun = 20 teeth, Planets = 18 teeth, Ring = 56 teeth
    # Check: 56 = 20 + 2*18 = 56 ✓
    planetary = PlanetaryGearTrain(
        sun_teeth=20,
        planet_teeth=18,
        ring_teeth=56,
        num_planets=3,
    )

    print(f"Planetary Gear Set 行星齿轮组:")
    print(f"  Sun (太阳轮):     Zs = {planetary.sun_teeth}")
    print(f"  Planet (行星轮):  Zp = {planetary.planet_teeth}")
    print(f"  Ring (齿圈):      Zr = {planetary.ring_teeth}")
    print(f"  Num Planets (行星数): {planetary.num_planets}")
    print()

    print(f"Pitch Radii (节圆半径):")
    for name, r in planetary.pitch_radii.items():
        print(f"  {name:12s}: {r:.2f} mm")
    print()

    # All operating modes
    print("-" * 40)
    print("All Operating Modes 所有运行模式:")
    print("-" * 40)
    print(f"  {'Fixed':<10} {'Input':<10} {'Output':<10} {'Ratio':>10} {'Type':<12}")
    print(f"  {'-'*8:<10} {'-'*8:<10} {'-'*8:<10} {'-'*8:>10} {'-'*10:<12}")

    modes = planetary.get_modes()
    for mode in modes:
        print(f"  {mode['fixed']:<10} {mode['input']:<10} {mode['output']:<10} "
              f"{mode['ratio']:>10.4f} {mode['type']:<12}")
    print()

    # Detailed analysis for ring-fixed configuration (most common)
    print("-" * 40)
    print("Ring-Fixed Configuration (齿圈固定配置):")
    print("-" * 40)

    # Case 1: Sun input, carrier output (typical reduction)
    speeds = planetary.solve_speed(fixed_component="ring", input_speed=1000, input_component="sun")
    print(f"  Sun Input (太阳轮输入):  1000 RPM")
    print(f"  Carrier Output (行星架输出): {speeds['carrier']:.2f} RPM")
    print(f"  Ratio (传动比): {1000 / speeds['carrier']:.4f}")
    print(f"  Planet Relative Speed (行星相对转速): {speeds['planet_relative']:.2f} RPM")
    print()

    # Case 2: Carrier input, sun output
    speeds = planetary.solve_speed(fixed_component="ring", input_speed=1000, input_component="carrier")
    print(f"  Carrier Input (行星架输入): 1000 RPM")
    print(f"  Sun Output (太阳轮输出): {speeds['sun']:.2f} RPM")
    print(f"  Ratio (传动比): {1000 / speeds['sun']:.4f}")
    print()

    # Case 3: Ring input, carrier output
    speeds = planetary.solve_speed(fixed_component="sun", input_speed=1000, input_component="ring")
    print(f"  Ring Input (齿圈输入): 1000 RPM")
    print(f"  Carrier Output (行星架输出): {speeds['carrier']:.2f} RPM")
    print(f"  Ratio (传动比): {1000 / speeds['carrier']:.4f}")
    print()

    # Plot the planetary gear system
    print("Generating visualization...")
    plot_planary_gear_system(planetary, fixed="ring")
    print()

    # Efficiency comparison
    print("-" * 40)
    print("Efficiency Comparison 效率对比:")
    print("-" * 40)

    analyzer = EfficiencyAnalyzer()

    # Create gear objects for analysis
    m = planetary.planet_module
    sun_gear = SpurGear(module=m, num_teeth=planetary.sun_teeth, name="sun")
    ring_gear = SpurGear(module=m, num_teeth=planetary.ring_teeth, name="ring")
    planet_gears = [
        SpurGear(module=m, num_teeth=planetary.planet_teeth, name=f"planet_{i}")
        for i in range(planetary.num_planets)
    ]

    # Single stage spur comparison
    spur_gear1 = SpurGear(module=2, num_teeth=20, name="spur_driver")
    spur_gear2 = SpurGear(module=2, num_teeth=60, name="spur_driven")

    spur_result = analyzer.analyze_gear_train_efficiency(
        gears=[spur_gear1, spur_gear2],
        input_power_w=1000,
        gear_type="spur",
    )
    print(f"  Single Spur Pair (单级直齿轮): {spur_result.overall_efficiency * 100:.2f}%")

    # Worm gear comparison
    worm_eff = analyzer.calculate_worm_gear_efficiency(
        lead_angle_deg=12,
        lubrication="good_lubrication",
    )
    print(f"  Worm Gear (蜗轮蜗杆, λ=12°): {worm_eff * 100:.2f}%")

    # Planetary effective efficiency (approximate)
    # Each mesh ~98%, 3 planets share load
    planetary_eff = 1 - (1 - 0.98 ** 3)  # Parallel paths reduce impact of one loss
    print(f"  Planetary (approx) (行星近似): {planetary_eff * 100:.2f}%")
    print()

    print("=" * 60)
    print("  Example 3 Complete! 示例3完成!")
    print("=" * 60)


if __name__ == '__main__':
    analyze_planetary_system()
