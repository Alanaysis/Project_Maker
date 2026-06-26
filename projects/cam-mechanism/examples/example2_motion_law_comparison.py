"""Example 2: Motion Law Comparison.

This example compares different motion laws for cam followers:
- Uniform motion (等速运动)
- Parabolic motion (等加速/等减速运动)
- Cycloidal motion (摆线运动)
- Polynomial 3rd order (三次多项式)
- Polynomial 5th order (五次多项式)
- Harmonic motion (简谐运动)
- Modified sine (改良正弦)
- Modified trapezoidal (改良梯形)

Example 2: 运动规律对比
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from src.motion_laws import MotionLaw, MotionLawCalculator, MotionLawCalculator
from src.visualization import CamVisualizer

# Output directory
output_dir = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(output_dir, exist_ok=True)

print("=" * 60)
print("Example 2: Motion Law Comparison / 运动规律对比")
print("=" * 60)

# ============================================================
# Configuration / 配置参数
# ============================================================
LIFT = 20.0        # 升程 [mm]
TOTAL_ANGLE = 180.0  # 推程运动角 [degrees]
OMEGA = 10.0       # 角速度 [rad/s]

# ============================================================
# Define motion laws to compare / 定义要对比的运动规律
# ============================================================
motion_laws = [
    (MotionLaw.UNIFORM, "等速运动 / Uniform"),
    (MotionLaw.PARABOLIC, "等加速等减速 / Parabolic"),
    (MotionLaw.CYCLOIDAL, "摆线运动 / Cycloidal"),
    (MotionLaw.POLYNOMIAL_3, "三次多项式 / 3rd Poly"),
    (MotionLaw.POLYNOMIAL_5, "五次多项式 / 5th Poly"),
    (MotionLaw.SINUSOIDAL, "简谐运动 / Harmonic"),
    (MotionLaw.MODIFIED_SINE, "改良正弦 / Mod. Sine"),
    (MotionLaw.MODIFIED_TRAP, "改良梯形 / Mod. Trap"),
]

# ============================================================
# Plot motion diagrams / 绘制运动图
# ============================================================
print("\nGenerating motion diagrams...")
fig = CamVisualizer.plot_motion_diagram(
    laws=motion_laws,
    lift=LIFT,
    angle=TOTAL_ANGLE,
    omega=OMEGA,
    title=f'Motion Law Comparison (h={LIFT}mm, phi={TOTAL_ANGLE}deg)\n运动规律对比',
    save_path=os.path.join(output_dir, 'motion_comparison.png')
)

# ============================================================
# Detailed analysis / 详细分析
# ============================================================
print("\n" + "=" * 60)
print("Motion Law Properties / 运动规律特性")
print("=" * 60)

calc = MotionLawCalculator(LIFT, OMEGA)

for law, label in motion_laws:
    info = calc.get_motion_law_info(law)
    
    # Calculate max values during rise phase
    max_s, max_v, max_a, max_j = 0, 0, 0, 0
    n_points = 360
    for theta in np.linspace(0, TOTAL_ANGLE, n_points):
        result = calc.calculate(law, TOTAL_ANGLE, theta)
        max_s = max(max_s, abs(result.displacement))
        max_v = max(max_v, abs(result.velocity))
        max_a = max(max_a, abs(result.acceleration))
        max_j = max(max_j, abs(result.jerk))
    
    print(f"\n{info['name']}")
    print(f"  Smoothness / 平滑度: {info['smoothness']}")
    print(f"  Speed range / 速度范围: {info['speed_range']}")
    print(f"  Peak accel factor / 峰值加速度系数: {info['peak_acc_factor']}")
    print(f"  Max velocity / 最大速度: {max_v:.2f} mm/s")
    print(f"  Max acceleration / 最大加速度: {max_a:.2f} mm/s²")
    print(f"  Max jerk / 最大跃度: {max_j:.2f} mm/s³")
    print(f"  Description / 说明: {info['description']}")

# ============================================================
# Summary table / 总结表
# ============================================================
print("\n" + "=" * 60)
print("Summary / 总结")
print("=" * 60)
print(f"{'Motion Law':<25} {'Max V':>10} {'Max A':>12} {'Max J':>12} {'Smoothness':>12}")
print("-" * 70)

for law, label in motion_laws:
    info = calc.get_motion_law_info(law)
    
    max_s, max_v, max_a, max_j = 0, 0, 0, 0
    n_points = 360
    for theta in np.linspace(0, TOTAL_ANGLE, n_points):
        result = calc.calculate(law, TOTAL_ANGLE, theta)
        max_v = max(max_v, abs(result.velocity))
        max_a = max(max_a, abs(result.acceleration))
        max_j = max(max_j, abs(result.jerk))
    
    smooth = info['smoothness'].split(' - ')[0]
    print(f"{label:<25} {max_v:>10.1f} {max_a:>12.1f} {max_j:>12.1f} {smooth:>12}")

print("\n" + "=" * 60)
print("Recommendation / 推荐:")
print("  - Low speed (低速): Any motion law is acceptable")
print("  - Medium speed (中速): Cycloidal, Harmonic")
print("  - High speed (高速): Modified sine, Modified trapezoidal, 5th order polynomial")
print("=" * 60)

print(f"\nFigure saved to: {output_dir}/motion_comparison.png")
