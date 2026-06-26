"""Example 3: Pressure Angle Analysis.

This example demonstrates pressure angle analysis for cam mechanisms:
- Pressure angle calculation for different follower types
- Effect of base circle radius on pressure angle
- Checking pressure angle limits
- Visualizing pressure angle distribution

Example 3: 压力角分析
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from src.motion_laws import MotionLaw
from src.cam_profile import CamProfileGenerator, FollowerType, FollowerMotion
from src.pressure_angle import PressureAngleAnalyzer
from src.visualization import CamVisualizer
import matplotlib.pyplot as plt

# Output directory
output_dir = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(output_dir, exist_ok=True)

print("=" * 60)
print("Example 3: Pressure Angle Analysis / 压力角分析")
print("=" * 60)

# ============================================================
# Configuration / 配置参数
# ============================================================
BASE_RADIUS = 30.0       # 基圆半径 [mm]
ROLLER_RADIUS = 8.0      # 滚子半径 [mm]
LIFT = 20.0              # 升程 [mm]
OMEGA = 10.0             # 角速度 [rad/s]
RISE_ANGLE = 120.0
RISE_DWELL = 60.0
RETURN_ANGLE = 120.0
RETURN_DWELL = 60.0

generator = CamProfileGenerator(BASE_RADIUS, ROLLER_RADIUS)
analyzer = PressureAngleAnalyzer(generator)

# ============================================================
# 1. Pressure angle for different base circle radii / 不同基圆半径的压力角
# ============================================================
print("\n1. Effect of Base Circle Radius on Pressure Angle")
print("   基圆半径对压力角的影响")
print("-" * 60)

base_radii = [20, 25, 30, 35, 40, 50]
max_pressure_angles = []

for rb in base_radii:
    gen = CamProfileGenerator(rb, ROLLER_RADIUS)
    profile = gen.generate_profile(
        follower_type=FollowerType.ROLLERS,
        follower_motion=FollowerMotion.TRANSLATING,
        motion_law=MotionLaw.CYCLOIDAL,
        lift=LIFT,
        rise_angle=RISE_ANGLE,
        rise_dwell_angle=RISE_DWELL,
        return_angle=RETURN_ANGLE,
        return_dwell_angle=RETURN_DWELL,
        omega=OMEGA
    )
    
    angles, pa = analyzer.calculate_pressure_angle(profile)
    max_pa = np.max(np.abs(pa))
    max_pressure_angles.append(max_pa)
    
    status = "OK" if max_pa <= 30 else "EXCEEDS"
    print(f"   rb = {rb:4.0f} mm: max PA = {max_pa:7.2f} deg [{status}]")

# Plot pressure angle vs base radius
fig, ax = plt.subplots(1, 1, figsize=(10, 6))
ax.plot(base_radii, max_pressure_angles, 'bo-', linewidth=2, markersize=8,
        label='Max Pressure Angle / 最大压力角')
ax.axhline(y=30, color='r', linestyle='--', linewidth=2, label='Limit / 限值 (30°)')
ax.axhline(y=20, color='g', linestyle='-.', linewidth=1.5, label='Recommended / 推荐 (20°)')
ax.set_xlabel('Base Circle Radius / 基圆半径 [mm]', fontsize=12)
ax.set_ylabel('Maximum Pressure Angle / 最大压力角 [degrees]', fontsize=12)
ax.set_title('Effect of Base Circle Radius on Pressure Angle\n基圆半径对最大压力角的影响', fontsize=13)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.fill_between(base_radii, 0, 30, alpha=0.1, color='green')
plt.tight_layout()
fig.savefig(os.path.join(output_dir, 'base_radius_effect.png'), dpi=150, bbox_inches='tight')
print(f"\n   Figure saved to: {output_dir}/base_radius_effect.png")

# ============================================================
# 2. Pressure angle distribution for different follower types / 不同从动件类型的压力角分布
# ============================================================
print("\n2. Pressure Angle Distribution by Follower Type")
print("   不同从动件类型的压力角分布")
print("-" * 60)

follower_configs = [
    (FollowerType.ROLLERS, FollowerMotion.TRANSLATING, "对心滚子从动件"),
    (FollowerType.FLAT_FOOT, FollowerMotion.TRANSLATING, "对心平底从动件"),
    (FollowerType.PIN, FollowerMotion.TRANSLATING, "对心尖顶从动件"),
]

for ft, fm, name in follower_configs:
    profile = generator.generate_profile(
        follower_type=ft,
        follower_motion=fm,
        motion_law=MotionLaw.CYCLOIDAL,
        lift=LIFT,
        rise_angle=RISE_ANGLE,
        rise_dwell_angle=RISE_DWELL,
        return_angle=RETURN_ANGLE,
        return_dwell_angle=RETURN_DWELL,
        omega=OMEGA
    )
    
    angles, pa = analyzer.calculate_pressure_angle(profile)
    max_pa = np.max(np.abs(pa))
    mean_pa = np.mean(np.abs(pa))
    
    check = analyzer.check_pressure_angle_limit(pa, 30.0)
    
    print(f"\n   {name}:")
    print(f"     Max PA / 最大压力角: {max_pa:.2f} deg")
    print(f"     Mean PA / 平均压力角: {mean_pa:.2f} deg")
    print(f"     Acceptable / 合格: {check['is_acceptable']}")

# ============================================================
# 3. Pressure angle check for offset follower / 偏置从动件压力角检查
# ============================================================
print("\n3. Offset Translating Roller Follower")
print("   偏置滚子从动件")
print("-" * 60)

offsets = [0, 5, 10, 15, 20]
offset_max_pas = []

for e in offsets:
    profile = generator.generate_profile(
        follower_type=FollowerType.ROLLERS,
        follower_motion=FollowerMotion.OFFSET_TRANSLATING,
        motion_law=MotionLaw.CYCLOIDAL,
        lift=LIFT,
        rise_angle=RISE_ANGLE,
        rise_dwell_angle=RISE_DWELL,
        return_angle=RETURN_ANGLE,
        return_dwell_angle=RETURN_DWELL,
        omega=OMEGA,
        offset=e
    )
    
    angles, pa = analyzer.calculate_pressure_angle(profile)
    max_pa = np.max(np.abs(pa))
    offset_max_pas.append(max_pa)
    
    check = analyzer.check_pressure_angle_limit(pa, 30.0)
    status = "OK" if check['is_acceptable'] else "EXCEEDS"
    print(f"   e = {e:3.0f} mm: max PA = {max_pa:7.2f} deg [{status}]")

# Plot pressure angle vs offset
fig, ax = plt.subplots(1, 1, figsize=(10, 6))
ax.plot(offsets, offset_max_pas, 'ro-', linewidth=2, markersize=8,
        label='Max Pressure Angle / 最大压力角')
ax.axhline(y=30, color='b', linestyle='--', linewidth=2, label='Limit / 限值 (30°)')
ax.set_xlabel('Offset Distance / 偏置距 [mm]', fontsize=12)
ax.set_ylabel('Maximum Pressure Angle / 最大压力角 [degrees]', fontsize=12)
ax.set_title('Effect of Offset on Pressure Angle\n偏置距对最大压力角的影响', fontsize=13)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.fill_between(offsets, 0, 30, alpha=0.1, color='green')
plt.tight_layout()
fig.savefig(os.path.join(output_dir, 'offset_effect.png'), dpi=150, bbox_inches='tight')
print(f"\n   Figure saved to: {output_dir}/offset_effect.png")

# ============================================================
# 4. Pressure angle info / 压力角信息
# ============================================================
print("\n4. Pressure Angle Information / 压力角信息")
print("-" * 60)

info = analyzer.get_pressure_angle_info()
print(f"   Definition / 定义: {info['definition']}")
print(f"   Importance / 重要性: {info['importance']}")
print(f"\n   Typical limits / 典型限值:")
for ft_name, limit in info['typical_limits'].items():
    print(f"     {ft_name}: {limit}")

# ============================================================
# 5. Visualize pressure angle for the main example / 可视化主例的压力角
# ============================================================
print("\n5. Pressure Angle Visualization")
print("   压力角可视化")
print("-" * 60)

profile = generator.generate_profile(
    follower_type=FollowerType.ROLLERS,
    follower_motion=FollowerMotion.TRANSLATING,
    motion_law=MotionLaw.CYCLOIDAL,
    lift=LIFT,
    rise_angle=RISE_ANGLE,
    rise_dwell_angle=RISE_DWELL,
    return_angle=RETURN_ANGLE,
    return_dwell_angle=RETURN_DWELL,
    omega=OMEGA
)

angles, pa = analyzer.calculate_pressure_angle(profile)
max_pa = np.max(np.abs(pa))

print(f"   Max pressure angle / 最大压力角: {max_pa:.2f} degrees")
print(f"   Within limit / 在限值内: {max_pa <= 30}")

CamVisualizer.plot_pressure_angle_analysis(
    angles, pa, max_allowed=30.0,
    title=f'Pressure Angle Distribution (max = {max_pa:.1f}°)\n压力角分布',
    save_path=os.path.join(output_dir, 'pressure_angle_detailed.png')
)

print(f"\n   Figure saved to: {output_dir}/pressure_angle_detailed.png")

print("\n" + "=" * 60)
print("Pressure angle analysis complete!")
print("=" * 60)
