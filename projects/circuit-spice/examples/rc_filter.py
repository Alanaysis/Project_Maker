"""
RC 滤波器频率响应示例

演示交流分析和频率响应
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from src.circuit import Circuit
from src.ac_analysis import (
    ACAnalysis, rc_cutoff_frequency, rc_lowpass_response,
    voltage_gain_db, phase_degrees
)


def main():
    print("=" * 60)
    print("RC 低通滤波器分析")
    print("=" * 60)

    # 电路参数
    r = 1000  # 1k Ohm
    c = 1e-6  # 1uF

    # 创建电路
    circuit = Circuit("RC Low Pass Filter")
    circuit.add_voltage_source("V1", 0, 1, 0, ac_mag=1)
    circuit.add_resistor("R1", 1, 2, r)
    circuit.add_capacitor("C1", 2, 0, c)
    circuit.build_node_map()

    print(f"\n电路参数:")
    print(f"  R = {r} Ohm")
    print(f"  C = {c * 1e6} uF")

    # 截止频率
    f_c = rc_cutoff_frequency(r, c)
    print(f"  截止频率 f_c = 1/(2πRC) = {f_c:.2f} Hz")

    # 交流分析
    print("\n" + "=" * 60)
    print("单频率分析")
    print("=" * 60)

    analyzer = ACAnalysis(circuit)

    # 在不同频率分析
    frequencies = [1, 100, f_c, 10000, 100000]
    print("\n频率响应:")
    print(f"{'频率 (Hz)':>12} {'增益 (dB)':>12} {'相位 (度)':>12} {'输出幅度':>12}")
    print("-" * 50)

    for freq in frequencies:
        result = analyzer.solve(freq)
        gain = voltage_gain_db(result.magnitude(2), 1)
        phase = phase_degrees(result.node_voltages[2], 1)
        mag = result.magnitude(2)

        print(f"{freq:>12.1f} {gain:>12.2f} {phase:>12.2f} {mag:>12.4f}")

    # 频率扫描
    print("\n" + "=" * 60)
    print("频率扫描")
    print("=" * 60)

    fr = analyzer.frequency_response(1, 1e6, 100)

    print(f"\n扫描范围: 1 Hz - 1 MHz")
    print(f"频率点数: {len(fr.frequencies)}")

    # 找到 -3dB 点
    db_values = fr.get_db(2)
    idx_3db = np.argmin(np.abs(db_values - (-3)))
    freq_3db = fr.frequencies[idx_3db]

    print(f"\n-3dB 频率 (仿真): {freq_3db:.2f} Hz")
    print(f"-3dB 频率 (理论): {f_c:.2f} Hz")

    # 理论验证
    print("\n" + "=" * 60)
    print("理论验证")
    print("=" * 60)

    # 使用公式计算
    test_freq = f_c
    h_theory = rc_lowpass_response(np.array([test_freq]), r, c)
    gain_theory = voltage_gain_db(abs(h_theory[0]), 1)
    phase_theory = np.degrees(np.angle(h_theory[0]))

    print(f"\n在截止频率 {f_c:.2f} Hz 处:")
    print(f"  理论增益: {gain_theory:.2f} dB")
    print(f"  理论相位: {phase_theory:.2f} 度")

    # 仿真结果
    result = analyzer.solve(f_c)
    gain_sim = voltage_gain_db(result.magnitude(2), 1)
    phase_sim = phase_degrees(result.node_voltages[2], 1)

    print(f"  仿真增益: {gain_sim:.2f} dB")
    print(f"  仿真相位: {phase_sim:.2f} 度")


if __name__ == "__main__":
    main()
