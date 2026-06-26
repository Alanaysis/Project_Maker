#!/usr/bin/env python3
"""
压力降计算演示 (Pressure Drop Calculation Demo)

本演示展示不同场景下的压力降计算：
1. 简单管道压力降
2. 含局部损失的压力降
3. 高程变化对压力的影响
4. 长距离管道压力分布
"""

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/fluid-mechanics')

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.pressure_drop import (
    PressureDropAnalyzer, total_pressure_drop,
    frictional_pressure_drop, elevation_pressure_change
)
from src.reynolds import reynolds_number
from src.head_loss import MINOR_LOSS_COEFFICIENTS
from src.continuity import cross_sectional_area


def demo_simple_pressure_drop():
    """演示1：简单管道压力降"""
    print("=" * 60)
    print("演示1：简单管道压力降")
    print("=" * 60)

    # 管道参数
    diameter = 0.05    # 50 mm
    length = 100       # m
    roughness = 4.6e-5  # commercial steel

    flow_rates = np.linspace(0.001, 0.02, 15)  # m³/s
    friction_drops = []
    total_drops = []

    print(f"\n管道参数：")
    print(f"  直径 D = {diameter*1000:.0f} mm")
    print(f"  长度 L = {length:.0f} m")
    print(f"  粗糙度 ε = {roughness*1000:.4f} mm")
    print(f"  流体 = 水 (20°C)")
    print(f"\n{'流量 (L/s)':<12} {'流速 (m/s)':<14} {'Reynolds数':<16} {'摩擦压降 (kPa)':<18}")
    print("-" * 60)

    for Q in flow_rates:
        area = cross_sectional_area(diameter)
        velocity = Q / area
        re = reynolds_number(velocity, diameter, 998.2, 1.002e-3)
        dp = frictional_pressure_drop(length, diameter, velocity, re, 998.2, roughness)

        friction_drops.append(dp / 1000)
        total_drops.append(dp / 1000)

        regime = "层流" if re < 2300 else "湍流"
        print(f"{Q*1000:<12.3f} {velocity:<14.2f} {re:<16.0f} {dp/1000:<18.2f}")

    # 绘制流量-压降关系
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(flow_rates * 1000, friction_drops, 'b-', linewidth=2, marker='o', markersize=5)
    ax.set_xlabel('流量 (L/s)', fontsize=12)
    ax.set_ylabel('压力降 (kPa)', fontsize=12)
    ax.set_title('简单管道：流量-压力降关系', fontsize=14)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/fluid-mechanics/examples/output/pressure_simple.png', dpi=150)
    plt.close()
    print("\n✓ 图表已保存: output/pressure_simple.png")


def demo_minor_losses():
    """演示2：含局部损失的压力降"""
    print("\n" + "=" * 60)
    print("演示2：含局部损失的压力降")
    print("=" * 60)

    diameter = 0.05
    length = 50
    flow_rate = 0.005  # m³/s

    area = cross_sectional_area(diameter)
    velocity = flow_rate / area
    re = reynolds_number(velocity, diameter, 998.2, 1.002e-3)

    # 管道系统组件
    components = [
        ("inlet_square", "方形边缘入口"),
        ("elbow_90_standard", "90°标准弯头"),
        ("elbow_90_standard", "90°标准弯头"),
        ("gate_valve_full_open", "全开闸阀"),
        ("exit submerged", "淹没出口"),
    ]

    # 计算各项损失
    major_loss = 998.2 * 9.81 * (4.6e-5 / diameter > 0 and
        (64/re if re < 2300 else
         0.25 / (np.log10((4.6e-5/diameter)/3.7 + 5.74/re**0.9))**2) *
         (length/diameter) * (velocity**2/2))
    # 简化计算
    from src.pipe_flow import darcy_weisbach_head_loss
    h_major = darcy_weisbach_head_loss(length, diameter, velocity, re, 4.6e-5)
    p_major = 998.2 * 9.81 * h_major

    print(f"\n管道参数：")
    print(f"  D = {diameter*1000:.0f} mm, L = {length:.0f} m")
    print(f"  流量 Q = {flow_rate*1000:.3f} L/s, 流速 v = {velocity:.2f} m/s")
    print(f"  Re = {re:.0f}")

    print(f"\n{'组件':<22} {'K值':<10} {'局部损失 (kPa)':<16}")
    print("-" * 48)

    total_minor = 0
    for comp_name, comp_cn in components:
        k = MINOR_LOSS_COEFFICIENTS[comp_name]["K"]
        h_minor = k * velocity**2 / (2 * 9.81)
        p_minor = 998.2 * 9.81 * h_minor
        total_minor += p_minor
        print(f"{comp_cn:<22} {k:<10.2f} {p_minor:<16.2f}")

    print(f"\n{'合计':<22} {'':<10} {'':<16}")
    print(f"  沿程损失: {p_major/1000:.2f} kPa")
    print(f"  局部损失: {total_minor/1000:.2f} kPa")
    print(f"  总损失:   {(p_major + total_minor)/1000:.2f} kPa")

    # 绘制损失组成饼图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # 柱状图
    comp_names_list = [c[1] for c in components]
    comp_losses = []
    for comp_name, comp_cn in components:
        k = MINOR_LOSS_COEFFICIENTS[comp_name]["K"]
        h = k * velocity**2 / (2 * 9.81)
        comp_losses.append(998.2 * 9.81 * h)

    x = range(len(comp_names_list))
    bars = ax1.bar(x, comp_losses, color='steelblue', alpha=0.7)
    ax1.set_xticks(x)
    ax1.set_xticklabels(comp_names_list, rotation=30, ha='right', fontsize=9)
    ax1.set_ylabel('局部损失 (kPa)', fontsize=12)
    ax1.set_title('各组件局部损失', fontsize=14)
    ax1.grid(True, alpha=0.3, axis='y')

    # 饼图
    sizes = [p_major/1000, total_minor/1000]
    labels = ['沿程损失', '局部损失']
    colors = ['#2196F3', '#FF9800']
    ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax2.set_title('损失比例', fontsize=14)

    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/fluid-mechanics/examples/output/pressure_minor.png', dpi=150)
    plt.close()
    print("\n✓ 图表已保存: output/pressure_minor.png")


def demo_elevation_effect():
    """演示3：高程变化对压力的影响"""
    print("\n" + "=" * 60)
    print("演示3：高程变化对压力的影响")
    print("=" * 60)

    # 分析不同高程变化下的压力变化
    heights = np.linspace(-50, 100, 20)
    elevation_changes = []
    total_drops = []

    diameter = 0.05
    length = 100
    flow_rate = 0.005
    velocity = flow_rate / cross_sectional_area(diameter)
    re = reynolds_number(velocity, diameter, 998.2, 1.002e-3)

    # 摩擦压降（固定）
    friction_drop = frictional_pressure_drop(length, diameter, velocity, re, 998.2, 4.6e-5)

    print(f"\n固定条件：")
    print(f"  D = {diameter*1000:.0f} mm, L = {length:.0f} m")
    print(f"  Q = {flow_rate*1000:.3f} L/s")
    print(f"  摩擦压降 = {friction_drop/1000:.2f} kPa")
    print(f"\n{'高程变化 (m)':<16} {'高程压降 (kPa)':<18} {'总压降 (kPa)':<16} {'流动方向':<12}")
    print("-" * 62)

    for h in heights:
        elev_drop = elevation_pressure_change(998.2, 9.81, h)
        # 注意：elevation_pressure_change 返回 ρgΔh，向上流动时压力降低
        total = friction_drop + 998.2 * 9.81 * h  # h>0 表示向上
        direction = "向上" if h > 0 else ("水平" if h == 0 else "向下")
        print(f"{h:<16.1f} {998.2*9.81*h/1000:<18.2f} {total/1000:<16.2f} {direction:<12}")
        elevation_changes.append(998.2 * 9.81 * h / 1000)
        total_drops.append(total / 1000)

    # 绘制高程-压力关系
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(heights, total_drops, 'r-', linewidth=2, label='总压降')
    ax.axhline(y=friction_drop/1000, color='b', linestyle='--', alpha=0.5,
               label=f'摩擦压降 ({friction_drop/1000:.2f} kPa)')
    ax.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('高程变化 (m)', fontsize=12)
    ax.set_ylabel('压力降 (kPa)', fontsize=12)
    ax.set_title('高程变化对压力降的影响', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/fluid-mechanics/examples/output/pressure_elevation.png', dpi=150)
    plt.close()
    print("\n✓ 图表已保存: output/pressure_elevation.png")


def demo_long_pipeline():
    """演示4：长距离管道压力分布"""
    print("\n" + "=" * 60)
    print("演示4：长距离管道压力分布")
    print("=" * 60)

    analyzer = PressureDropAnalyzer(
        fluid_density=998.2,
        fluid_viscosity=1.002e-3,
        gravity=9.81,
    )

    # 添加管道段
    analyzer.add_segment(length=500, diameter=0.2, roughness=4.6e-5, elevation_change=10)
    analyzer.add_segment(length=300, diameter=0.15, roughness=4.6e-5, elevation_change=20)
    analyzer.add_segment(length=200, diameter=0.1, roughness=4.6e-5, elevation_change=-5)

    flow_rate = 0.05  # m³/s

    result = analyzer.analyze(flow_rate)

    print(f"\n管道系统参数：")
    print(f"  总长度: {result['total_length']:.0f} m")
    print(f"  总高程变化: {result['total_elevation_change']:.1f} m")
    print(f"  流量: {flow_rate*1000:.1f} L/s")

    print(f"\n{'位置 (m)':<14} {'压力 (kPa)':<14} {'高程 (m)':<14} {'速度 (m/s)':<14}")
    print("-" * 56)

    for point in result['pressure_profile']:
        print(f"{point['position']:<14.1f} {point['pressure']/1000:<14.2f} "
              f"{point['elevation']:<14.1f} {point['velocity']:<14.2f}")

    print(f"\n系统总压降: {result['total_pressure_drop']/1000:.2f} kPa")

    # 绘制压力分布图
    fig, ax = plt.subplots(figsize=(10, 6))

    positions = [p['position'] for p in result['pressure_profile']]
    pressures = [p['pressure'] / 1000 for p in result['pressure_profile']]
    elevations = [p['elevation'] for p in result['pressure_profile']]

    ax.plot(positions, pressures, 'r-o', linewidth=2, markersize=6, label='压力')
    ax.plot(positions, [e - pressures[i]/(998.2*9.81/1000) for i, e in enumerate(elevations)],
            'b-s', linewidth=2, markersize=6, label='测压管水头')
    ax.plot(positions, [e - pressures[i]/(998.2*9.81/1000) + result['velocity']**2/(2*9.81)
                       for i, e in enumerate(elevations)],
            'g-^', linewidth=2, markersize=6, label='总水头')

    ax.set_xlabel('沿程位置 (m)', fontsize=12)
    ax.set_ylabel('水头 (m)', fontsize=12)
    ax.set_title('长距离管道压力分布', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/fluid-mechanics/examples/output/pressure_pipeline.png', dpi=150)
    plt.close()
    print("\n✓ 图表已保存: output/pressure_pipeline.png")


def main():
    """运行所有压力降计算演示"""
    print("\n" + "#" * 60)
    print("# 压力降计算演示 (Pressure Drop Calculation)")
    print("# ΔP = f(L/D)(ρv²/2) + ρgΔh + ΣK(ρv²/2)")
    print("#" * 60)

    demo_simple_pressure_drop()
    demo_minor_losses()
    demo_elevation_effect()
    demo_long_pipeline()

    print("\n" + "=" * 60)
    print("所有演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
