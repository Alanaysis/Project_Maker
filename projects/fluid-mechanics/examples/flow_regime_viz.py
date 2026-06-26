#!/usr/bin/env python3
"""
流动状态可视化演示 (Flow Regime Visualization Demo)

本演示展示不同 Reynolds 数下的流动状态：
1. Reynolds 数范围概览
2. 不同流体的临界速度
3. 速度剖面变化
4. 流动状态相图
"""

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/fluid-mechanics')

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.reynolds import (
    reynolds_number, reynolds_number_kinematic, classify_flow_regime,
    critical_velocity, FLUID_PROPERTIES, FlowRegimeAnalyzer
)
from src.pipe_flow import PipeSegment


def demo_reynolds_range():
    """演示1：Reynolds 数范围"""
    print("=" * 60)
    print("演示1：Reynolds 数范围概览")
    print("=" * 60)

    # 常见流动的 Reynolds 数范围
    examples = [
        ("微血管流动", 0.001, 0.008, 998.2, 1.002e-3),
        ("管道层流", 0.1, 1.0, 998.2, 1.002e-3),
        ("管道湍流", 0.1, 5.0, 998.2, 1.002e-3),
        ("飞机飞行 (Mach 0.8)", 10.0, 50000, 1.204, 1.825e-5),
        ("河流流动", 1.0, 10.0, 1000, 1.0e-6),
        ("血液流动 (主动脉)", 0.025, 0.5, 1060, 3.5e-3),
    ]

    print(f"\n{'流动类型':<25} {'特征速度 (m/s)':<18} {'特征长度 (m)':<18} {'Reynolds数':<15} {'状态':<10}")
    print("-" * 86)

    for name, v, L, rho, mu in examples:
        re = reynolds_number(v, L, rho, mu)
        regime = classify_flow_regime(re)["regime_cn"]
        re_str = f"{re:.2e}" if re >= 1000 else f"{re:.2f}"
        print(f"{name:<25} {v:<18.4f} {L:<18.6f} {re_str:<15} {regime:<10}")


def demo_flow_regime_plot():
    """演示2：流动状态可视化"""
    print("\n" + "=" * 60)
    print("演示2：流动状态相图")
    print("=" * 60)

    # 为水 (20°C) 创建分析器
    analyzer = FlowRegimeAnalyzer("water_20c")

    diameters = np.logspace(-3, 1, 30)  # 1mm to 100mm
    velocities = np.logspace(-3, 3, 30)  # 0.001 to 1000 m/s

    regimes = np.zeros((len(velocities), len(diameters)))

    for i, v in enumerate(velocities):
        for j, d in enumerate(diameters):
            re = analyzer.reynolds_number(v, d)
            regime = classify_flow_regime(re)
            if regime["regime"] == "laminar":
                regimes[i, j] = 1
            elif regime["regime"] == "transitional":
                regimes[i, j] = 2
            else:
                regimes[i, j] = 3

    # 绘制流动状态图
    fig, ax = plt.subplots(figsize=(10, 7))
    contour = ax.contourf(
        np.log10(diameters), np.log10(velocities), regimes,
        levels=[0.5, 1.5, 2.5, 3.5],
        colors=['#4CAF50', '#FFEB3B', '#F44336'],
        alpha=0.7
    )
    ax.contour(
        np.log10(diameters), np.log10(velocities), regimes,
        levels=[1.5, 2.5],
        colors='black', linewidths=1.5
    )

    # 添加标注
    ax.annotate('层流区', xy=(-1, 0), fontsize=14, color='white', fontweight='bold')
    ax.annotate('过渡区', xy=(1, 1), fontsize=14, color='black', fontweight='bold')
    ax.annotate('湍流区', xy=(2, 2.5), fontsize=14, color='white', fontweight='bold')

    ax.set_xlabel('log₁₀(Diameter [m])', fontsize=12)
    ax.set_ylabel('log₁₀(Velocity [m/s])', fontsize=12)
    ax.set_title('水的流动状态图 (20°C)\nRe = 2300 和 Re = 4000 为分界线', fontsize=14)

    cbar = plt.colorbar(contour, ax=ax)
    cbar.set_label('流动状态', fontsize=12)
    cbar.set_ticks([1, 2, 3])
    cbar.set_ticklabels(['层流', '过渡流', '湍流'])

    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/fluid-mechanics/examples/output/flow_regime.png', dpi=150)
    plt.close()
    print("\n✓ 图表已保存: output/flow_regime.png")


def demo_velocity_profile():
    """演示3：速度剖面变化"""
    print("\n" + "=" * 60)
    print("演示3：速度剖面变化")
    print("=" * 60)

    diameter = 0.1  # 100 mm
    r = np.linspace(0, diameter/2, 100)  # 径向位置

    # 层流速度剖面（抛物线）
    v_laminar = 2 * 1.0 * (1 - (r / (diameter/2))**2)

    # 湍流速度剖面（1/7次方律）
    re_turbulent = reynolds_number(5.0, diameter, 998.2, 1.002e-3)
    regime = classify_flow_regime(re_turbulent)
    v_turbulent = 5.0 * (1 - r / (diameter/2))**(1/7)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # 层流剖面
    ax1.plot(v_laminar, r * 1000, 'b-', linewidth=2, label='v = v_max(1 - (r/R)²)')
    ax1.axvline(x=1.0, color='b', linestyle='--', alpha=0.3)
    ax1.set_xlabel('流速 (m/s)', fontsize=12)
    ax1.set_ylabel('径向位置 (mm)', fontsize=12)
    ax1.set_title('层流速度剖面 (Re < 2300)', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.invert_yaxis()

    # 湍流剖面
    ax2.plot(v_turbulent, r * 1000, 'r-', linewidth=2, label='v = v_max(1 - r/R)^(1/7)')
    ax2.axvline(x=5.0, color='r', linestyle='--', alpha=0.3)
    ax2.set_xlabel('流速 (m/s)', fontsize=12)
    ax2.set_ylabel('径向位置 (mm)', fontsize=12)
    ax2.set_title('湍流速度剖面 (Re > 4000)', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.invert_yaxis()

    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/fluid-mechanics/examples/output/velocity_profile.png', dpi=150)
    plt.close()
    print("\n✓ 图表已保存: output/velocity_profile.png")

    print(f"\n速度剖面特点：")
    print(f"  层流: 抛物线分布，中心速度 = 2 × 平均速度")
    print(f"  湍流: 均匀分布，中心速度 ≈ 1.2 × 平均速度")


def demo_critical_velocity():
    """演示4：临界速度对比"""
    print("\n" + "=" * 60)
    print("演示4：不同流体的临界速度")
    print("=" * 60)

    diameter = 0.05  # 50 mm

    print(f"\n管道直径 D = {diameter*1000:.0f} mm")
    print(f"\n{'流体':<18} {'密度 (kg/m³)':<16} {'粘度 (Pa·s)':<16} {'临界速度 (m/s)':<18}")
    print("-" * 68)

    for fluid_key, props in FLUID_PROPERTIES.items():
        v_crit = critical_velocity(diameter, props["density"], props["viscosity"])
        print(f"{props['name_cn']:<18} {props['density']:<16.1f} "
              f"{props['viscosity']:<16.4e} {v_crit:<18.4f}")

    # 绘制临界速度对比图
    fluids_data = []
    for fluid_key, props in FLUID_PROPERTIES.items():
        v_crit = critical_velocity(diameter, props["density"], props["viscosity"])
        fluids_data.append((props["name_cn"], v_crit))

    fig, ax = plt.subplots(figsize=(10, 6))
    names = [f[0] for f in fluids_data]
    v_crits = [f[1] for f in fluids_data]
    colors = ['#2196F3', '#FF9800', '#4CAF50', '#9C27B0', '#F44336']
    bars = ax.bar(range(len(names)), v_crits, color=colors, alpha=0.7)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=15, ha='right')
    ax.set_ylabel('临界速度 (m/s)', fontsize=12)
    ax.set_title(f'不同流体在 D={diameter*1000:.0f}mm 管道中的临界速度', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')

    for bar, v in zip(bars, v_crits):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                f'{v:.3f}', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/fluid-mechanics/examples/output/critical_velocity.png', dpi=150)
    plt.close()
    print("\n✓ 图表已保存: output/critical_velocity.png")


def main():
    """运行所有流动状态可视化演示"""
    print("\n" + "#" * 60)
    print("# 流动状态可视化 (Flow Regime Visualization)")
    print("# Re = ρvD/μ")
    print("#" * 60)

    demo_reynolds_range()
    demo_flow_regime_plot()
    demo_velocity_profile()
    demo_critical_velocity()

    print("\n" + "=" * 60)
    print("所有演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
