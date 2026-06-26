"""Example 4: Dynamic Simulation.

This example demonstrates dynamic analysis of cam mechanisms:
- Inertia force calculation
- Dynamic force analysis
- Contact loss check
- Natural frequency analysis
- Dynamic amplification factor

Example 4: 动力学仿真
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from src.motion_laws import MotionLaw
from src.cam_profile import CamProfileGenerator, FollowerType, FollowerMotion
from src.dynamic_analysis import DynamicAnalyzer, SystemParameters
from src.contact_stress import ContactStressAnalyzer
from src.pressure_angle import PressureAngleAnalyzer
from src.visualization import CamVisualizer

# Output directory
output_dir = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(output_dir, exist_ok=True)

print("=" * 60)
print("Example 4: Dynamic Simulation / 动力学仿真")
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

# System parameters / 系统参数
params = SystemParameters(
    follower_mass=0.1,        # 从动件质量 [kg]
    cam_mass=0.5,             # 凸轮质量 [kg]
    spring_stiffness=500.0,   # 弹簧刚度 [N/mm]
    spring_preload=10.0,      # 弹簧预紧力 [N]
    damping_ratio=0.05,       # 阻尼比
    equivalent_mass=0.1,      # 等效质量 [kg]
    equivalent_stiffness=500.0 # 等效刚度 [N/mm]
)

dynamic_analyzer = DynamicAnalyzer(params)
stress_analyzer = ContactStressAnalyzer()

# ============================================================
# 1. Generate cam profile / 生成凸轮轮廓
# ============================================================
print("\n1. Generating Cam Profile / 生成凸轮轮廓")
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

print(f"   Base radius / 基圆半径: {profile.base_radius} mm")
print(f"   Lift / 升程: {profile.lift} mm")
print(f"   Profile points: {len(profile.profile_x)}")

# ============================================================
# 2. Dynamic force analysis / 动力学力分析
# ============================================================
print("\n2. Dynamic Force Analysis / 动力学力分析")
print("-" * 60)

dynamic_result = dynamic_analyzer.analyze_dynamic_forces(profile, params)

print(f"   Max inertia force / 最大惯性力: {np.max(np.abs(dynamic_result.inertia_force)):.2f} N")
print(f"   Max spring force / 最大弹簧力: {np.max(dynamic_result.spring_force):.2f} N")
print(f"   Max total force / 最大总接触力: {np.max(dynamic_result.total_force):.2f} N")
print(f"   Natural frequency / 固有频率: {dynamic_result.natural_frequency:.2f} Hz")
print(f"   Max dynamic factor / 最大动态放大系数: {dynamic_result.max_dynamic_factor:.2f}")

# ============================================================
# 3. Plot dynamic forces / 绘制动态力
# ============================================================
print("\n3. Dynamic Force Plot / 动态力图")
print("-" * 60)

angles = np.linspace(0, profile.total_angle, 360)
CamVisualizer.plot_dynamic_analysis(
    angles,
    dynamic_result.inertia_force,
    dynamic_result.spring_force,
    dynamic_result.total_force,
    title=f'Dynamic Force Analysis (omega = {OMEGA} rad/s)\n动力学力分析',
    save_path=os.path.join(output_dir, 'dynamic_forces.png')
)
print(f"   Figure saved to: {output_dir}/dynamic_forces.png")

# ============================================================
# 4. Contact loss check / 脱离接触检查
# ============================================================
print("\n4. Contact Loss Check / 脱离接触检查")
print("-" * 60)

contact_status, has_loss = dynamic_analyzer.check_contact_loss(profile, params, OMEGA)

if has_loss:
    loss_count = np.sum(contact_status == 0)
    print(f"   WARNING: Contact loss detected! / 警告: 检测到脱离接触!")
    print(f"   Lost contact at {loss_count} points / 脱离接触点数: {loss_count}")
    
    # Find where contact is lost
    loss_angles = angles[contact_status == 0]
    if len(loss_angles) > 0:
        print(f"   Loss occurs between / 脱离发生在: "
              f"{loss_angles[0]:.1f}° - {loss_angles[-1]:.1f}°")
else:
    print(f"   OK: No contact loss detected. / 无脱离接触。")

# ============================================================
# 5. Effect of angular velocity / 角速度影响
# ============================================================
print("\n5. Effect of Angular Velocity / 角速度影响")
print("-" * 60)

omega_values = [5, 10, 20, 30, 50, 100]
print(f"   {'Omega':>8} {'Max Inertia':>12} {'Max Total':>12} {'Nat Freq':>10} {'Dyn Factor':>12} {'Contact':>10}")
print(f"   {'[rad/s]':>8} {'[N]':>12} {'[N]':>12} {'[Hz]':>10} {'':>12} {'Loss?':>10}")
print("   " + "-" * 66)

for omega in omega_values:
    # Recalculate with new omega
    profile_w = generator.generate_profile(
        follower_type=FollowerType.ROLLERS,
        follower_motion=FollowerMotion.TRANSLATING,
        motion_law=MotionLaw.CYCLOIDAL,
        lift=LIFT,
        rise_angle=RISE_ANGLE,
        rise_dwell_angle=RISE_DWELL,
        return_angle=RETURN_ANGLE,
        return_dwell_angle=RETURN_DWELL,
        omega=omega
    )
    
    result = dynamic_analyzer.analyze_dynamic_forces(profile_w, params)
    contact, loss = dynamic_analyzer.check_contact_loss(profile_w, params, omega)
    
    print(f"   {omega:>8} {np.max(np.abs(result.inertia_force)):>12.2f} "
          f"{np.max(result.total_force):>12.2f} {result.natural_frequency:>10.2f} "
          f"{result.max_dynamic_factor:>12.2f} {'YES' if loss else 'No':>10}")

# ============================================================
# 6. Contact stress analysis / 接触应力分析
# ============================================================
print("\n6. Contact Stress Analysis / 接触应力分析")
print("-" * 60)

# Calculate max acceleration for stress estimation
max_accel = 0.0
calc = MotionLaw(LIFT, OMEGA)
for theta in np.linspace(0, RISE_ANGLE, 100):
    from src.motion_laws import MotionLawCalculator
    mcalc = MotionLawCalculator(LIFT, OMEGA)
    result = mcalc.calculate(MotionLaw.CYCLOIDAL, RISE_ANGLE, theta)
    max_accel = max(max_accel, abs(result.acceleration))

# Calculate contact stress
stress_result = stress_analyzer.calculate_contact_stress(
    normal_force=params.follower_mass * max_accel / 1000.0 + params.spring_preload,
    roller_radius=ROLLER_RADIUS,
    cam_radius=BASE_RADIUS,
    follower_width=10.0,
    follower_type=FollowerType.ROLLERS
)

print(f"   Max acceleration / 最大加速度: {max_accel:.2f} mm/s²")
print(f"   Normal force / 法向力: {stress_result.max_hertz_stress:.2f} N (estimated)")
print(f"   Max Hertz stress / 最大赫兹应力: {stress_result.max_hertz_stress:.2f} MPa")
print(f"   Contact half-width / 接触半宽: {stress_result.contact_half_width:.4f} mm")
print(f"   Allowable stress / 许用应力: {stress_result.max_allowed_stress:.0f} MPa")
print(f"   Safe / 安全: {stress_result.is_safe}")

# ============================================================
# 7. Comprehensive report / 综合报告
# ============================================================
print("\n7. Generating Comprehensive Report / 生成综合报告")
print("-" * 60)

# Get pressure angle data
analyzer = PressureAngleAnalyzer(generator)
angles_pa, pa = analyzer.calculate_pressure_angle(profile)

CamVisualizer.create_comprehensive_report(
    profile, angles_pa, pa, dynamic_result, output_dir
)

# ============================================================
# 8. Dynamic info / 动力学信息
# ============================================================
print("\n8. Dynamic Effects Information / 动态效应信息")
print("-" * 60)

info = dynamic_analyzer.get_dynamic_info()
print(f"   {info['dynamic_effects']}")
print(f"   {info['english_effects']}")
print(f"\n   Key factors / 关键因素:")
for factor in info['key_factors']:
    print(f"     - {factor}")
print(f"\n   Design recommendations / 设计建议:")
for rec in info['design_recommendations']:
    print(f"     - {rec}")

print("\n" + "=" * 60)
print("Dynamic simulation complete!")
print("=" * 60)
