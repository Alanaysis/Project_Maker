#!/usr/bin/env python3
"""
管道网络分析演示 (Pipe Network Analysis Demo)

本演示展示管道网络的计算方法：
1. 串联管道网络
2. 并联管道网络
3. 管道选型计算
4. 流量分配分析
"""

import sys
sys.path.insert(0, '/home/siok/project_copyninja/projects/fluid-mechanics')

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.pipe_flow import PipeSegment, PipeNetwork
from src.reynolds import reynolds_number, classify_flow_regime
from src.head_loss import total_head_loss
from src.continuity import cross_sectional_area


def demo_series_pipe():
    """演示1：串联管道网络"""
    print("=" * 60)
    print("演示1：串联管道网络分析")
    print("=" * 60)

    # 创建串联管道网络
    network = PipeNetwork()

    # 管道1：长管段
    seg1 = PipeSegment(
        diameter=0.1,      # 100 mm
        length=100,        # 100 m
        material='commercial_steel',
        fluid_density=998.2,
        fluid_viscosity=1.002e-3,
    )
    network.add_segment(seg1)

    # 管道2：收缩段
    seg2 = PipeSegment(
        diameter=0.05,     # 50 mm
        length=20,         # 20 m
        material='galvanized_iron',
        fluid_density=998.2,
        fluid_viscosity=1.002e-3,
    )
    network.add_segment(seg2)

    # 管道3：扩张段
    seg3 = PipeSegment(
        diameter=0.08,     # 80 mm
        length=50,         # 50 m
        material='commercial_steel',
        fluid_density=998.2,
        fluid_viscosity=1.002e-3,
    )
    network.add_segment(seg3)

    # 计算不同流量下的损失
    flow_rates = np.linspace(0.001, 0.03, 15)  # m³/s
    total_losses = []

    print(f"\n串联管道网络参数：")
    for i, seg in enumerate(network.segments):
        print(f"  管道{i+1}: D={seg.diameter*1000:.0f} mm, L={seg.length:.0f} m, "
              f"材料={seg.material}")

    print(f"\n{'流量 (L/s)':<12} {'v₁ (m/s)':<12} {'v₂ (m/s)':<12} {'v₃ (m/s)':<12} "
          f"{'总损失 (m)':<14} {'总压降 (kPa)':<14}")
    print("-" * 76)

    for Q in flow_rates:
        results = network.compute_series()
        # 重新计算当前流量
        seg1_vel = seg1.velocity_from_flow(Q)
        seg2_vel = seg2.velocity_from_flow(Q)
        seg3_vel = seg3.velocity_from_flow(Q)

        re1 = seg1.reynolds_number(seg1_vel)
        re2 = seg2.reynolds_number(seg2_vel)
        re3 = seg3.reynolds_number(seg3_vel)

        h1 = seg1.head_loss(seg1_vel)
        h2 = seg2.head_loss(seg2_vel)
        h3 = seg3.head_loss(seg3_vel)
        h_total = h1 + h2 + h3

        total_losses.append(h_total)

        regime1 = classify_flow_regime(re1)["regime_cn"]
        regime2 = classify_flow_regime(re2)["regime_cn"]
        regime3 = classify_flow_regime(re3)["regime_cn"]

        print(f"{Q*1000:<12.3f} {seg1_vel:<12.2f} {seg2_vel:<12.2f} {seg3_vel:<12.2f} "
              f"{h_total:<14.3f} {998.2*9.81*h_total/1000:<14.2f}")

    # 绘制流量-损失关系
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(flow_rates * 1000, total_losses, 'b-', linewidth=2, marker='o', markersize=4)
    ax.set_xlabel('流量 (L/s)', fontsize=12)
    ax.set_ylabel('总水头损失 (m)', fontsize=12)
    ax.set_title('串联管道网络：流量-损失关系', fontsize=14)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/fluid-mechanics/examples/output/pipe_series.png', dpi=150)
    plt.close()
    print("\n✓ 图表已保存: output/pipe_series.png")


def demo_parallel_pipe():
    """演示2：并联管道网络"""
    print("\n" + "=" * 60)
    print("演示2：并联管道网络分析")
    print("=" * 60)

    network = PipeNetwork()

    # 并联支路1
    seg1 = PipeSegment(
        diameter=0.05,
        length=50,
        material='commercial_steel',
        fluid_density=998.2,
        fluid_viscosity=1.002e-3,
    )
    network.add_segment(seg1)

    # 并联支路2
    seg2 = PipeSegment(
        diameter=0.04,
        length=30,
        material='galvanized_iron',
        fluid_density=998.2,
        fluid_viscosity=1.002e-3,
    )
    network.add_segment(seg2)

    # 并联支路3
    seg3 = PipeSegment(
        diameter=0.06,
        length=40,
        material='drawn_tube',
        fluid_density=998.2,
        fluid_viscosity=1.002e-3,
    )
    network.add_segment(seg3)

    total_flow = 0.015  # m³/s
    results = network.compute_parallel()

    print(f"\n并联管道网络参数：")
    for i, seg in enumerate(network.segments):
        print(f"  支路{i+1}: D={seg.diameter*1000:.0f} mm, L={seg.length:.0f} m")

    print(f"\n总流量 Q_total = {total_flow*1000:.3f} L/s")
    print(f"\n{'支路':<8} {'流量 (L/s)':<14} {'速度 (m/s)':<14} {'水头损失 (m)':<16}")
    print("-" * 52)

    for branch in results["branches"]:
        print(f"支路{branch['segment_index']+1:<4} {branch['flow']*1000:<14.4f} "
              f"{branch['velocity']:<14.3f} {branch['head_loss']:<16.4f}")

    print(f"\n关键观察：")
    print(f"  - 流量按阻力分配，阻力小的支路流量大")
    print(f"  - 所有支路的水头损失相等（并联特性）")


def demo_pipe_sizing():
    """演示3：管道选型计算"""
    print("\n" + "=" * 60)
    print("演示3：管道选型计算")
    print("=" * 60)

    from src.continuity import diameter_from_flow

    # 设计条件
    flow_rate = 0.05      # m³/s (50 L/s)
    max_velocity = 3.0    # m/s (推荐流速范围)
    min_velocity = 0.5    # m/s

    # 计算所需管径范围
    max_d = diameter_from_flow(flow_rate, min_velocity)
    min_d = diameter_from_flow(flow_rate, max_velocity)

    print(f"\n设计条件：")
    print(f"  流量 Q = {flow_rate*1000:.1f} L/s")
    print(f"  推荐流速范围: {min_velocity} ~ {max_velocity} m/s")
    print(f"\n计算结果：")
    print(f"  最大允许管径 D_max = {max_d*1000:.1f} mm")
    print(f"  最小允许管径 D_min = {min_d*1000:.1f} mm")

    # 标准管径选择
    standard_diameters = [0.05, 0.06, 0.075, 0.08, 0.1, 0.125, 0.15, 0.2]
    print(f"\n{'标准管径 (mm)':<16} {'流速 (m/s)':<14} {'Reynolds数':<16} {'流动状态':<14}")
    print("-" * 60)

    for d in standard_diameters:
        if d < min_d or d > max_d:
            continue
        v = flow_rate / cross_sectional_area(d)
        re = reynolds_number(v, d, 998.2, 1.002e-3)
        regime = classify_flow_regime(re)["regime_cn"]
        print(f"{d*1000:<16.1f} {v:<14.2f} {re:<16.0f} {regime:<14}")


def demo_friction_comparison():
    """演示4：不同粗糙度的摩擦损失对比"""
    print("\n" + "=" * 60)
    print("演示4：管道粗糙度对摩擦损失的影响")
    print("=" * 60)

    diameter = 0.1       # 100 mm
    length = 100         # m
    flow_rate = 0.02     # m³/s
    velocity = flow_rate / cross_sectional_area(diameter)
    re = reynolds_number(velocity, diameter, 998.2, 1.002e-3)

    materials = [
        ("drawn_tube", "拉制管"),
        ("commercial_steel", "商用钢管"),
        ("galvanized_iron", "镀锌铁管"),
        ("cast_iron", "铸铁管"),
        ("concrete", "混凝土管"),
    ]

    losses = []
    names = []

    print(f"\n条件: D={diameter*1000:.0f}mm, L={length:.0f}m, "
          f"Q={flow_rate*1000:.2f}L/s, Re={re:.0e}")
    print(f"\n{'管道材料':<16} {'粗糙度 (mm)':<14} {'摩擦系数 f':<14} {'水头损失 (m)':<14}")
    print("-" * 58)

    for mat, name in materials:
        seg = PipeSegment(
            diameter=diameter, length=length, material=mat,
            fluid_density=998.2, fluid_viscosity=1.002e-3,
        )
        h = seg.head_loss(velocity)
        f = seg.friction_factor(velocity)
        losses.append(h)
        names.append(name)
        print(f"{name:<16} {seg.roughness*1000:<14.4f} {f:<14.5f} {h:<14.3f}")

    # 绘制对比图
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(range(len(names)), losses, color=['brown', 'gray', 'silver', 'darkgray', 'tan'])
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=15, ha='right')
    ax.set_ylabel('水头损失 (m)', fontsize=12)
    ax.set_title('不同管道材料的水头损失对比', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')

    for bar, loss in zip(bars, losses):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.1,
                f'{loss:.2f}', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/fluid-mechanics/examples/output/pipe_friction.png', dpi=150)
    plt.close()
    print("\n✓ 图表已保存: output/pipe_friction.png")


def main():
    """运行所有管道网络分析演示"""
    print("\n" + "#" * 60)
    print("# 管道网络分析演示 (Pipe Network Analysis)")
    print("#" * 60)

    demo_series_pipe()
    demo_parallel_pipe()
    demo_pipe_sizing()
    demo_friction_comparison()

    print("\n" + "=" * 60)
    print("所有演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
