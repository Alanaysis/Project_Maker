#!/usr/bin/env python3
"""
伯努利方程演示 (Bernoulli Equation Demo)

本演示展示伯努利方程在不同场景下的应用：
1. 水平管道中的压力变化
2. 变径管道中的速度-压力关系
3. 高度变化对压力的影响
4. 能量沿程分布可视化
"""

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/fluid-mechanics')

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.bernoulli import BernoulliSolver
from src.reynolds import FLUID_PROPERTIES
from src.continuity import cross_sectional_area, continuity_solver


def demo_basic_bernoulli():
    """演示1：水平管道中的伯努利方程"""
    print("=" * 60)
    print("演示1：水平管道中的伯努利方程")
    print("=" * 60)

    # 创建求解器（水，20°C）
    solver = BernoulliSolver(density=998.2, gravity=9.81)

    # 场景：水平管道，直径变化
    p1 = 200000  # Pa (200 kPa)
    v1 = 2.0     # m/s
    z1 = z2 = 0  # 水平管道

    # 计算不同出口速度对应的压力
    velocities = np.linspace(0.5, 8.0, 20)
    pressures = []

    print(f"\n入口条件: P₁ = {p1} Pa, v₁ = {v1} m/s")
    print(f"{'出口速度 (m/s)':<18} {'出口压力 (kPa)':<18} {'速度头 (m)':<15} {'压力头 (m)':<15}")
    print("-" * 66)

    for v2 in velocities:
        p2 = solver.solve_for_pressure(p1, v1, z1, v2, z2)
        pressures.append(p2)
        v_head = v2**2 / (2 * 9.81)
        p_head = p2 / (998.2 * 9.81)
        print(f"{v2:<18.2f} {p2/1000:<18.2f} {v_head:<15.3f} {p_head:<15.3f}")

    # 绘制压力-速度关系
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(velocities, np.array(pressures) / 1000, 'b-', linewidth=2, label='出口压力')
    ax.axhline(y=200, color='r', linestyle='--', alpha=0.5, label='入口压力 (200 kPa)')
    ax.set_xlabel('出口速度 (m/s)', fontsize=12)
    ax.set_ylabel('压力 (kPa)', fontsize=12)
    ax.set_title('伯努利方程：水平管道中的压力-速度关系', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/fluid-mechanics/examples/output/bernoulli_basic.png', dpi=150)
    plt.close()
    print("\n✓ 图表已保存: output/bernoulli_basic.png")


def demo_venturi_tube():
    """演示2：文丘里管流量测量"""
    print("\n" + "=" * 60)
    print("演示2：文丘里管流量测量原理")
    print("=" * 60)

    solver = BernoulliSolver(density=998.2, gravity=9.81)

    # 文丘里管参数
    D1 = 0.1   # 入口直径 (m)
    D2 = 0.05  # 喉部直径 (m)

    # 计算喉部面积
    A1 = cross_sectional_area(D1)
    A2 = cross_sectional_area(D2)
    print(f"\n文丘里管参数：")
    print(f"  入口直径 D₁ = {D1*1000} mm, 面积 A₁ = {A1:.6f} m²")
    print(f"  喉部直径 D₂ = {D2*1000} mm, 面积 A₂ = {A2:.6f} m²")
    print(f"  面积比 A₁/A₂ = {A1/A2:.2f}")

    # 连续性方程：v₂ = v₁ × (A₁/A₂)
    # 伯努利方程：P₁ - P₂ = ½ρ(v₂² - v₁²)

    flow_rates = np.linspace(0.001, 0.02, 20)  # m³/s
    pressure_diffs = []

    print(f"\n{'流量 (L/s)':<12} {'v₁ (m/s)':<12} {'v₂ (m/s)':<12} {'ΔP (kPa)':<12}")
    print("-" * 48)

    for Q in flow_rates:
        v1 = Q / A1
        v2 = Q / A2
        dp = 0.5 * 998.2 * (v2**2 - v1**2)
        pressure_diffs.append(dp)
        print(f"{Q*1000:<12.2f} {v1:<12.3f} {v2:<12.3f} {dp/1000:<12.2f}")

    # 绘制流量-压差关系
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(flow_rates * 1000, np.array(pressure_diffs) / 1000, 'g-', linewidth=2)
    ax.set_xlabel('流量 (L/s)', fontsize=12)
    ax.set_ylabel('压差 ΔP (kPa)', fontsize=12)
    ax.set_title('文丘里管：流量-压差关系', fontsize=14)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/fluid-mechanics/examples/output/bernoulli_venturi.png', dpi=150)
    plt.close()
    print("\n✓ 图表已保存: output/bernoulli_venturi.png")

    # 计算示例：给定压差求流量
    dp_measured = 15000  # Pa
    v2 = np.sqrt(2 * dp_measured / 998.2 / (A1**2/A2**2 - 1))
    Q_calculated = v2 * A2
    print(f"\n示例：测量压差 ΔP = {dp_measured/1000} kPa")
    print(f"  计算流量 Q = {Q_calculated*1000:.2f} L/s")


def demo_elevation_effect():
    """演示3：高度变化对压力的影响"""
    print("\n" + "=" * 60)
    print("演示3：高度变化对压力的影响")
    print("=" * 60)

    solver = BernoulliSolver(density=998.2, gravity=9.81)

    p1 = 300000  # Pa (300 kPa)
    v1 = v2 = 1.0  # 等速
    z1 = 0

    heights = np.linspace(0, 50, 30)
    pressures = []

    print(f"\n入口条件: P₁ = {p1/1000} kPa, v₁ = v₂ = {v1} m/s")
    print(f"{'高程 z₂ (m)':<15} {'出口压力 (kPa)':<18} {'压力头 (m)':<15}")
    print("-" * 48)

    for z2 in heights:
        p2 = solver.solve_for_pressure(p1, v1, z1, v2, z2)
        pressures.append(p2)
        p_head = p2 / (998.2 * 9.81)
        print(f"{z2:<15.1f} {p2/1000:<18.2f} {p_head:<15.2f}")

    # 绘制高度-压力关系
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(heights, np.array(pressures) / 1000, 'r-', linewidth=2)
    ax.axhline(y=300, color='b', linestyle='--', alpha=0.5, label='入口压力 (300 kPa)')
    ax.set_xlabel('高程 z₂ (m)', fontsize=12)
    ax.set_ylabel('压力 (kPa)', fontsize=12)
    ax.set_title('伯努利方程：高度变化对压力的影响', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/fluid-mechanics/examples/output/bernoulli_elevation.png', dpi=150)
    plt.close()
    print("\n✓ 图表已保存: output/bernoulli_elevation.png")

    # 计算最大提升高度（压力降至0时的最大高度）
    max_height = p1 / (998.2 * 9.81)
    print(f"\n理论最大提升高度: {max_height:.1f} m")


def demo_energy_profile():
    """演示4：总水头沿程分布"""
    print("\n" + "=" * 60)
    print("演示4：总水头沿程分布")
    print("=" * 60)

    solver = BernoulliSolver(density=998.2, gravity=9.81)

    # 沿流线取多个点
    points = [
        (300000, 1.0, 0.0),    # 点1: 高压、低速、低高程
        (250000, 2.0, 0.0),    # 点2: 压力降低，速度增加
        (200000, 3.0, 0.0),    # 点3: 继续降压加速
        (180000, 4.0, 5.0),    # 点4: 速度最大，高程增加
        (150000, 3.5, 10.0),   # 点5: 速度减小，高程继续增加
        (120000, 2.5, 15.0),   # 点6: 压力最低
    ]

    print(f"\n{'位置':<8} {'压力 (kPa)':<12} {'速度 (m/s)':<12} {'高程 (m)':<10} {'总水头 (m)':<12}")
    print("-" * 54)

    energy_profile = solver.analyze_energy_profile(points)

    total_heads = []
    for i, entry in enumerate(energy_profile["energy_profile"]):
        pos = entry["position"]
        p, v, z = pos[0]/1000, pos[1], pos[2]
        th = entry["total_head"]
        total_heads.append(th)
        print(f"点{i+1:<5} {p:<12.1f} {v:<12.2f} {z:<10.1f} {th:<12.2f}")

    # 绘制能量分布
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

    positions = [entry["position"] for entry in energy_profile["energy_profile"]]
    x = range(len(positions))

    pressure_heads = [e["pressure_head"] for e in energy_profile["energy_profile"]]
    velocity_heads = [e["velocity_head"] for e in energy_profile["energy_profile"]]
    elevations = [e["elevation_head"] for e in energy_profile["energy_profile"]]

    ax1.bar(x, pressure_heads, label='压力头', color='blue', alpha=0.7)
    ax1.bar(x, velocity_heads, bottom=pressure_heads, label='速度头', color='green', alpha=0.7)
    ax1.bar(x, elevations, bottom=[p+v for p, v in zip(pressure_heads, velocity_heads)],
            label='高程头', color='orange', alpha=0.7)
    ax1.set_ylabel('水头 (m)', fontsize=12)
    ax1.set_title('伯努利能量分布（各水头分量）', fontsize=14)
    ax1.legend()
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'点{i+1}' for i in x])
    ax1.grid(True, alpha=0.3)

    ax2.plot(x, total_heads, 'r-o', linewidth=2, markersize=8, label='总水头')
    ax2.set_xlabel('位置', fontsize=12)
    ax2.set_ylabel('总水头 (m)', fontsize=12)
    ax2.set_title('总水头沿程变化', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'点{i+1}' for i in x])

    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/fluid-mechanics/examples/output/bernoulli_energy.png', dpi=150)
    plt.close()
    print("\n✓ 图表已保存: output/bernoulli_energy.png")

    # 理想流体 vs 实际流体
    ideal_total = energy_profile["energy_profile"][0]["total_head"]
    actual_total = energy_profile["energy_profile"][-1]["total_head"]
    loss = ideal_total - actual_total
    print(f"\n理想流体总水头: {ideal_total:.2f} m")
    print(f"实际流体总水头: {actual_total:.2f} m")
    print(f"水头损失: {loss:.2f} m")


def main():
    """运行所有伯努利方程演示"""
    print("\n" + "#" * 60)
    print("# 伯努利方程演示 (Bernoulli Equation Demo)")
    print("# 公式: P/ρg + v²/(2g) + z = constant")
    print("#" * 60)

    demo_basic_bernoulli()
    demo_venturi_tube()
    demo_elevation_effect()
    demo_energy_profile()

    print("\n" + "=" * 60)
    print("所有演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
