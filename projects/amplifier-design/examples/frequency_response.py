"""
频率响应分析演示

展示增益带宽积、相位补偿和稳定性分析。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.frequency import GainBandwidthProduct, PhaseCompensation, StabilityAnalyzer


def main():
    print("=" * 70)
    print("频率响应分析演示")
    print("=" * 70)

    # ========================================
    # 1. 增益带宽积
    # ========================================
    print("\n[1] 增益带宽积 (GBW = 1MHz)")
    print("-" * 50)

    gbw = GainBandwidthProduct(gbw=1e6)

    print(f"  {'增益':<10} {'增益(dB)':<12} {'带宽(Hz)':<15} {'GBW验证':<15}")
    print("  " + "-" * 50)
    for gain in [1, 10, 100, 1000]:
        bw = gbw.bandwidth_at_gain(gain)
        gain_db = 20 * np.log10(gain)
        gbw_check = gain * bw
        print(f"  {gain:<10.0f} {gain_db:<12.1f} {bw:<15.0f} {gbw_check:<15.0f}")

    # 频率响应曲线数据
    print(f"\n  频率响应 (Av=100, f_p={1e6/100:.0f} Hz):")
    f = np.array([10, 100, 1000, 10000, 100000, 1000000])
    gain_db = gbw.gain_db_at_frequency(100, f)
    phase = gbw.phase_at_frequency(100, f)

    print(f"  {'频率(Hz)':<12} {'增益(dB)':<12} {'相位(度)':<12}")
    print("  " + "-" * 36)
    for fi, gd, ph in zip(f, gain_db, phase):
        print(f"  {fi:<12.0f} {gd:<12.2f} {ph:<12.1f}")

    # ========================================
    # 2. 相位补偿
    # ========================================
    print("\n[2] 相位补偿技术")
    print("-" * 50)

    # 2.1 主极点补偿
    print("\n  2.1 主极点补偿:")
    result = PhaseCompensation.dominant_pole_compensation(
        gbw_original=1e6, f_p1=1e3, f_p2=5e5, f_new_pole=100
    )
    print(f"    原始 GBW: {result['original_gbw']:.0f} Hz")
    print(f"    补偿后 GBW: {result['compensated_gbw']:.0f} Hz")
    print(f"    新主极点: {result['new_pole']:.0f} Hz")
    print(f"    相位裕度: {result['phase_margin']:.1f}°")
    print(f"    稳定性: {'稳定' if result['stable'] else '不稳定'}")

    # 2.2 超前补偿
    print("\n  2.2 超前补偿:")
    result = PhaseCompensation.lead_compensation(
        f_crossover=100e3, phase_deficit=30
    )
    print(f"    中心频率: {result['center_frequency']:.0f} Hz")
    print(f"    零点频率: {result['zero_frequency']:.0f} Hz")
    print(f"    极点频率: {result['pole_frequency']:.0f} Hz")
    print(f"    相位提升: {result['phase_boost_deg']:.0f}°")
    print(f"    alpha: {result['alpha']:.2f}")

    # 2.3 滞后补偿
    print("\n  2.3 滞后补偿:")
    result = PhaseCompensation.lag_compensation(
        desired_bw=10e3, original_gbw=1e6, feedback_gain=10
    )
    print(f"    期望带宽: {result['desired_bandwidth']:.0f} Hz")
    print(f"    滞后零点: {result['lag_zero_frequency']:.0f} Hz")
    print(f"    增益衰减: {result['gain_reduction_dB']:.1f} dB")

    # 2.4 密勒补偿
    print("\n  2.4 密勒补偿:")
    result = PhaseCompensation.miller_compensation(
        C_m=10e-12, g_m=1e-3, R_out=100e3
    )
    print(f"    密勒电容: {result['miller_capacitance']*1e12:.0f} pF")
    print(f"    等效电容: {result['effective_capacitance']*1e12:.0f} pF")
    print(f"    主极点: {result['dominant_pole']:.0f} Hz")
    print(f"    第二极点: {result['second_pole']:.0f} Hz")
    print(f"    极点分离比: {result['pole_splitting_ratio']:.0f}x")

    # ========================================
    # 3. 稳定性分析
    # ========================================
    print("\n[3] 环路稳定性分析")
    print("-" * 50)

    # 单极点系统
    print("\n  3.1 单极点系统 (稳定):")
    tf1 = StabilityAnalyzer.loop_gain_tf(gbw=1e6, gain=100)
    result1 = StabilityAnalyzer.phase_margin(tf1)
    print(f"    增益交越频率: {result1['gain_crossover_freq']:.0f} Hz")
    print(f"    相位裕度: {result1['phase_margin']:.1f}°")
    print(f"    增益裕度: {result1['gain_margin']:.1f} dB")
    print(f"    稳定: {result1['stable']}")

    # 多极点系统
    print("\n  3.2 多极点系统 (可能不稳定):")
    tf2 = StabilityAnalyzer.loop_gain_tf(
        gbw=1e6, gain=1000, poles=[100e3, 200e3]
    )
    result2 = StabilityAnalyzer.phase_margin(tf2)
    print(f"    增益交越频率: {result2['gain_crossover_freq']:.0f} Hz")
    print(f"    相位裕度: {result2['phase_margin']:.1f}°")
    print(f"    增益裕度: {result2['gain_margin']:.1f} dB")
    print(f"    稳定: {result2['stable']}")

    # 阶跃响应参数
    print("\n  3.3 相位裕度 vs 阶跃响应:")
    print(f"    {'相位裕度':<12} {'阻尼比':<10} {'超调量%':<12} {'状态':<10}")
    print("    " + "-" * 44)
    for pm in [30, 40, 45, 50, 60, 70, 80]:
        sr = StabilityAnalyzer.step_response_params(pm)
        status = "良好阻尼" if sr['well_damped'] else "欠阻尼"
        print(f"    {pm:<12.0f} {sr['damping_ratio']:<10.3f} {sr['overshoot_percent']:<12.1f} {status:<10}")

    # ========================================
    # 总结
    # ========================================
    print("\n" + "=" * 70)
    print("关键设计准则")
    print("=" * 70)
    print("  1. GBW = 增益 x 带宽 = 常数 (增益-带宽折衷)")
    print("  2. 相位裕度 > 45° 保证稳定 (推荐 > 60°)")
    print("  3. 增益裕度 > 10dB (推荐 > 20dB)")
    print("  4. 主极点补偿: 牺牲带宽换取稳定性")
    print("  5. 超前补偿: 在交越频率附近增加相位")
    print("  6. 密勒补偿: 利用极点分离原理")


if __name__ == '__main__':
    main()
