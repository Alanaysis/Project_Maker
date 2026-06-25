"""
实际应用演示

展示信号调理、传感器放大和音频放大应用。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.applications import SignalConditioner, SensorAmplifier, AudioAmplifier


def main():
    print("=" * 70)
    print("放大器实际应用演示")
    print("=" * 70)

    # ========================================
    # 1. 信号调理
    # ========================================
    print("\n[1] 信号调理 (Signal Conditioning)")
    print("-" * 50)

    # 模拟 ADC 输入信号 (0-3.3V)
    conditioner = SignalConditioner(gain=3.3, offset=1.65, v_ref=0.0, v_supply=3.3)

    # 传感器原始信号 (-0.5V ~ +0.5V)
    sensor_signal = np.array([-0.5, -0.25, 0.0, 0.25, 0.5])
    conditioned = conditioner.process(sensor_signal)

    print("  传感器信号 -> ADC 信号 (0-3.3V):")
    print(f"  {'输入(V)':<12} {'输出(V)':<12}")
    print("  " + "-" * 24)
    for vin, vout in zip(sensor_signal, conditioned):
        print(f"  {vin:<12.3f} {vout:<12.3f}")

    # 电平移位
    print("\n  电平移位 (双极性 -> 单极性):")
    bipolar = np.array([-2.5, -1.25, 0, 1.25, 2.5])
    unipolar = conditioner.level_shift(bipolar, 2.5)
    for vin, vout in zip(bipolar, unipolar):
        print(f"    {vin:+.2f}V -> {vout:.2f}V")

    # AC 耦合放大
    print("\n  AC 耦合放大 (去除直流):")
    t = np.linspace(0, 0.1, 10000)
    dc_offset = 2.5
    ac_signal = 0.01 * np.sin(2 * np.pi * 1000 * t)
    noisy_signal = dc_offset + ac_signal

    sc_ac = SignalConditioner(gain=100, offset=1.65, v_supply=3.3)
    clean_output = sc_ac.ac_coupled_amplify(noisy_signal, f_cutoff=50.0, fs=100000)
    print(f"    输入直流偏移: {dc_offset} V")
    print(f"    输入AC幅度: {0.01*1000:.0f} mV")
    print(f"    输出直流偏移: ~{np.mean(clean_output[-1000:]):.3f} V")
    print(f"    输出AC幅度: ~{np.std(clean_output[-1000:])*2.83:.3f} V (峰峰值)")

    # ========================================
    # 2. 传感器放大
    # ========================================
    print("\n[2] 传感器放大 (Sensor Amplification)")
    print("-" * 50)

    sa = SensorAmplifier()

    # 热电偶
    print("  2.1 热电偶放大器 (K型, ~40uV/°C):")
    tc = sa.thermocouple_amp(R_g=100, R1=49.4e3)
    print(f"    增益: {tc['gain']:.1f} ({tc['gain_dB']:.1f} dB)")
    print(f"    灵敏度: {tc['sensitivity']*1e3:.2f} mV/°C")
    print(f"    带宽: {tc['bandwidth']:.0f} Hz")
    # 计算温度分辨率
    temp_resolution = 1e-3 / tc['sensitivity']  # 1mV 对应的温度
    print(f"    温度分辨率 (1mV ADC): {temp_resolution:.1f}°C")

    # 应变片
    print("\n  2.2 应变片放大器 (350 Ohm, GF=2.0):")
    sg = sa.strain_gauge_amp(R_gauge=350, R_g=1000, V_excitation=5.0)
    print(f"    增益: {sg['gain']:.1f}")
    print(f"    电桥输出 (满量程): {sg['bridge_output']*1e3:.3f} mV")
    print(f"    放大后输出: {sg['amplified_output']*1e3:.1f} mV")
    print(f"    灵敏度: {sg['sensitivity']:.3f} V/strain")

    # 光电二极管
    print("\n  2.3 光电二极管跨阻放大器:")
    pd = sa.photodiode_amp(R_f=1e6, C_f=1e-12, responsivity=0.5)
    print(f"    跨阻增益: {pd['transimpedance']/1e6:.0f} MOhm")
    print(f"    灵敏度: {pd['sensitivity']:.0f} V/W")
    print(f"    带宽: {pd['bandwidth']/1e3:.0f} kHz")

    # 压电传感器
    print("\n  2.4 压电传感器放大器:")
    pz = sa.piezo_amp(R_f=10e6, C_in=1e-9)
    print(f"    增益: {pz['gain']:.0f}")
    print(f"    输入阻抗: {pz['input_impedance']/1e12:.0f} T Ohm")
    print(f"    低频截止: {pz['low_cutoff']:.1f} Hz")

    # ========================================
    # 3. 音频放大
    # ========================================
    print("\n[3] 音频放大 (Audio Amplification)")
    print("-" * 50)

    audio = AudioAmplifier(v_supply=15.0)

    # 前置放大
    print("  3.1 前置放大器 (麦克风):")
    preamp = audio.preamp(R_in=1e3, R_f=100e3)
    print(f"    增益: {preamp['gain']:.0f} ({preamp['gain_dB']:.1f} dB)")
    print(f"    带宽: {preamp['bandwidth']/1e3:.0f} kHz")
    print(f"    输入阻抗: {preamp['input_impedance']/1e6:.0f} MOhm")
    print(f"    最大输出: {preamp['max_output']:.1f} V")

    # 音调控制
    print("\n  3.2 Baxandall 音调控制:")
    tc = audio.tone_control(bass_gain=2.0, treble_gain=0.5)
    print(f"    低音增益: +{tc['bass_gain_dB']:.1f} dB")
    print(f"    高音增益: {tc['treble_gain_dB']:.1f} dB")

    # 频率响应
    f_test = np.array([20, 100, 1000, 5000, 20000])
    response = audio.baxandall_response(f_test, bass_gain=2.0, treble_gain=0.5)
    print(f"    频率响应:")
    print(f"    {'频率(Hz)':<12} {'增益(dB)':<12}")
    print("    " + "-" * 24)
    for fi, gd in zip(f_test, response):
        print(f"    {fi:<12.0f} {gd:<12.2f}")

    # 功率驱动
    print("\n  3.3 功率放大器驱动级:")
    driver = audio.power_amp_driver(gain=10, f_low=20, f_high=20000)
    print(f"    增益: {driver['gain']:.0f} ({driver['gain_dB']:.1f} dB)")
    print(f"    带宽: {driver['bandwidth']:.0f} Hz")
    print(f"    最大输出: {driver['max_output_voltage']:.1f} V")
    print(f"    最大功率 (8 Ohm): {driver['max_output_power_8ohm']:.1f} W")

    # 分频器
    print("\n  3.4 分频器设计:")
    xover = audio.crossover_network(f_crossover=3000, order=2)
    print(f"    分频频率: {xover['crossover_frequency']} Hz")
    print(f"    斜率: {xover['slope']}")
    print(f"    低通: {xover['low_pass_type']}")
    print(f"    高通: {xover['high_pass_type']}")

    # ========================================
    # 设计流程总结
    # ========================================
    print("\n" + "=" * 70)
    print("放大器设计流程")
    print("=" * 70)
    print("  1. 确定信号特征 (幅度、频率、阻抗)")
    print("  2. 选择放大器拓扑 (CE/CC/CB 或 运放)")
    print("  3. 设计偏置电路 (确保工作在放大区)")
    print("  4. 计算增益和带宽需求")
    print("  5. 选择补偿策略 (确保稳定性)")
    print("  6. 设计电源和接地 (降低噪声)")
    print("  7. 仿真验证 -> 实际测试")


if __name__ == '__main__':
    main()
