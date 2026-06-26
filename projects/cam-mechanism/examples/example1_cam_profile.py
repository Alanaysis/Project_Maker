"""Example 1: Cam Profile Generation for Different Followers.

This example demonstrates cam profile generation for various follower types:
- Translating roller follower (对心滚子从动件)
- Translating flat-foot follower (对心平底从动件)
- Translating pin follower (对心尖顶从动件)
- Offset translating roller follower (偏置滚子从动件)
- Oscillating roller follower (摆动滚子从动件)

Example 1: 凸轮轮廓生成 - 不同从动件类型
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from src.motion_laws import MotionLaw, MotionLawCalculator
from src.cam_profile import CamProfileGenerator, FollowerType, FollowerMotion
from src.visualization import CamVisualizer
import matplotlib.pyplot as plt

# Output directory
output_dir = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(output_dir, exist_ok=True)

print("=" * 60)
print("Example 1: Cam Profile Generation / 凸轮轮廓生成")
print("=" * 60)

# ============================================================
# Configuration / 配置参数
# ============================================================
BASE_RADIUS = 30.0       # 基圆半径 [mm]
ROLLER_RADIUS = 8.0      # 滚子半径 [mm]
LIFT = 20.0              # 升程 [mm]
OMEGA = 10.0             # 角速度 [rad/s]

# Motion phases / 运动阶段
RISE_ANGLE = 120.0       # 升程角 [degrees]
RISE_DWELL = 60.0        # 升程休止角 [degrees]
RETURN_ANGLE = 120.0     # 回程角 [degrees]
RETURN_DWELL = 60.0      # 回程休止角 [degrees]

# ============================================================
# 1. Translating Roller Follower / 对心滚子从动件
# ============================================================
print("\n1. Translating Roller Follower / 对心滚子从动件")
print("-" * 50)

generator = CamProfileGenerator(BASE_RADIUS, ROLLER_RADIUS)

profile1 = generator.generate_profile(
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

fig1 = CamVisualizer.plot_cam_profile(
    profile1,
    show_base_circle=True,
    show_pressure_angle=False,
    title='1. Translating Roller Follower Profile\n对心滚子从动件轮廓',
    save_path=os.path.join(output_dir, 'roller_translating.png')
)

print(f"   Base radius / 基圆半径: {profile1.base_radius} mm")
print(f"   Lift / 升程: {profile1.lift} mm")
print(f"   Total angle / 总转角: {profile1.total_angle} degrees")
print(f"   Profile points: {len(profile1.profile_x)}")

# ============================================================
# 2. Translating Flat-Foot Follower / 对心平底从动件
# ============================================================
print("\n2. Translating Flat-Foot Follower / 对心平底从动件")
print("-" * 50)

profile2 = generator.generate_profile(
    follower_type=FollowerType.FLAT_FOOT,
    follower_motion=FollowerMotion.TRANSLATING,
    motion_law=MotionLaw.CYCLOIDAL,
    lift=LIFT,
    rise_angle=RISE_ANGLE,
    rise_dwell_angle=RISE_DWELL,
    return_angle=RETURN_ANGLE,
    return_dwell_angle=RETURN_DWELL,
    omega=OMEGA
)

fig2 = CamVisualizer.plot_cam_profile(
    profile2,
    show_base_circle=True,
    show_pressure_angle=False,
    title='2. Translating Flat-Foot Follower Profile\n对心平底从动件轮廓',
    save_path=os.path.join(output_dir, 'flat_foot.png')
)

print(f"   Base radius / 基圆半径: {profile2.base_radius} mm")
print(f"   Lift / 升程: {profile2.lift} mm")
print(f"   Profile points: {len(profile2.profile_x)}")

# ============================================================
# 3. Offset Translating Roller Follower / 偏置滚子从动件
# ============================================================
print("\n3. Offset Translating Roller Follower / 偏置滚子从动件")
print("-" * 50)

OFFSET = 10.0  # 偏置距 [mm]

profile3 = generator.generate_profile(
    follower_type=FollowerType.ROLLERS,
    follower_motion=FollowerMotion.OFFSET_TRANSLATING,
    motion_law=MotionLaw.CYCLOIDAL,
    lift=LIFT,
    rise_angle=RISE_ANGLE,
    rise_dwell_angle=RISE_DWELL,
    return_angle=RETURN_ANGLE,
    return_dwell_angle=RETURN_DWELL,
    omega=OMEGA,
    offset=OFFSET
)

fig3 = CamVisualizer.plot_cam_profile(
    profile3,
    show_base_circle=True,
    show_pressure_angle=True,
    title=f'3. Offset Translating Roller Follower (e={OFFSET}mm)\n偏置滚子从动件轮廓',
    save_path=os.path.join(output_dir, 'offset_roller.png')
)

print(f"   Base radius / 基圆半径: {profile3.base_radius} mm")
print(f"   Offset / 偏置距: {profile3.offset} mm")
print(f"   Profile points: {len(profile3.profile_x)}")

# ============================================================
# 4. Oscillating Roller Follower / 摆动滚子从动件
# ============================================================
print("\n4. Oscillating Roller Follower / 摆动滚子从动件")
print("-" * 50)

LINK_LENGTH = 100.0     # 摆杆长度 [mm]
OSCILLATION_ANGLE = 20.0  # 摆杆摆角 [degrees]

profile4 = generator.generate_profile(
    follower_type=FollowerType.ROLLERS,
    follower_motion=FollowerMotion.OSCILLATING,
    motion_law=MotionLaw.CYCLOIDAL,
    lift=LIFT,
    rise_angle=RISE_ANGLE,
    rise_dwell_angle=RISE_DWELL,
    return_angle=RETURN_ANGLE,
    return_dwell_angle=RETURN_DWELL,
    omega=OMEGA,
    link_length=LINK_LENGTH,
    oscillation_angle=OSCILLATION_ANGLE
)

fig4 = CamVisualizer.plot_cam_profile(
    profile4,
    show_base_circle=True,
    show_pressure_angle=True,
    title=f'4. Oscillating Roller Follower (L={LINK_LENGTH}mm, phi={OSCILLATION_ANGLE}deg)\n摆动滚子从动件轮廓',
    save_path=os.path.join(output_dir, 'oscillating.png')
)

print(f"   Base radius / 基圆半径: {profile4.base_radius} mm")
print(f"   Link length / 摆杆长度: {profile4.link_length} mm")
print(f"   Oscillation angle / 摆杆摆角: {OSCILLATION_ANGLE} degrees")
print(f"   Profile points: {len(profile4.profile_x)}")

# ============================================================
# 5. Pin Follower (for comparison) / 尖顶从动件（对比）
# ============================================================
print("\n5. Translating Pin Follower / 对心尖顶从动件")
print("-" * 50)

profile5 = generator.generate_profile(
    follower_type=FollowerType.PIN,
    follower_motion=FollowerMotion.TRANSLATING,
    motion_law=MotionLaw.CYCLOIDAL,
    lift=LIFT,
    rise_angle=RISE_ANGLE,
    rise_dwell_angle=RISE_DWELL,
    return_angle=RETURN_ANGLE,
    return_dwell_angle=RETURN_DWELL,
    omega=OMEGA
)

fig5 = CamVisualizer.plot_cam_profile(
    profile5,
    show_base_circle=True,
    show_pressure_angle=False,
    title='5. Translating Pin Follower Profile\n对心尖顶从动件轮廓',
    save_path=os.path.join(output_dir, 'pin_follower.png')
)

print(f"   Base radius / 基圆半径: {profile5.base_radius} mm")
print(f"   Lift / 升程: {profile5.lift} mm")
print(f"   Profile points: {len(profile5.profile_x)}")

print("\n" + "=" * 60)
print("All profiles generated successfully!")
print("Figures saved to:", output_dir)
print("=" * 60)
