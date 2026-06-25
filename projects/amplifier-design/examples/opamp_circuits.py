"""
运算放大器电路演示

展示反相、同相、差分和仪表放大器的特性。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.opamp import (
    OpAmpParams, InvertingAmp, NonInvertingAmp,
    DifferentialAmp, InstrumentationAmp
)


def main():
    print("=" * 70)
    print("运算放大器电路演示")
    print("=" * 70)

    # 通用运放参数 (类似 TL072 / LM358)
    opamp = OpAmpParams(
        A_OL=1e5,      # 开环增益
        GBW=1e6,        # 增益带宽积 1MHz
        SR=0.5e6,       # 转换速率 0.5V/us
        V_sat=13.5,     # 饱和电压
    )

    # ========================================
    # 1. 反相放大器
    # ========================================
    print("\n[1] 反相放大器 (Inverting Amplifier)")
    print("-" * 50)

    inv = InvertingAmp(R_in=10e3, R_f=100e3, opamp=opamp)

    print(f"  R_in = {inv.R_in/1e3:.0f} kOhm")
    print(f"  R_f = {inv.R_f/1e3:.0f} kOhm")
    print(f"  理想增益: Av = {inv.gain():.1f}")
    print(f"  实际增益: Av = {inv.gain_with_loading():.4f}")
    print(f"  输入阻抗: Zin = {inv.input_impedance()/1e3:.0f} kOhm")
    print(f"  带宽: BW = {inv.bandwidth()/1e3:.0f} kHz")

    # 频率响应
    f_test = np.array([100, 1000, 10000, 100000])
    H = inv.transfer_function(f_test)
    print(f"\n  频率响应:")
    for fi, Hi in zip(f_test, H):
        print(f"    f = {fi:>8.0f} Hz: |H| = {abs(Hi):.4f}, phase = {np.degrees(np.angle(Hi)):.1f}°")

    # ========================================
    # 2. 同相放大器
    # ========================================
    print("\n[2] 同相放大器 (Non-Inverting Amplifier)")
    print("-" * 50)

    ni = NonInvertingAmp(R_in=10e3, R_f=100e3, opamp=opamp)

    print(f"  R_in = {ni.R_in/1e3:.0f} kOhm")
    print(f"  R_f = {ni.R_f/1e3:.0f} kOhm")
    print(f"  理想增益: Av = {ni.gain():.1f}")
    print(f"  实际增益: Av = {ni.gain_with_loading():.4f}")
    print(f"  输入阻抗: Zin = {ni.input_impedance()/1e6:.0f} MOhm")
    print(f"  带宽: BW = {ni.bandwidth()/1e3:.0f} kHz")

    # ========================================
    # 3. 差分放大器
    # ========================================
    print("\n[3] 差分放大器 (Differential Amplifier)")
    print("-" * 50)

    diff = DifferentialAmp(R1=10e3, R_f=100e3, opamp=opamp)

    print(f"  差模增益: Ad = {diff.differential_gain():.1f}")
    print(f"  共模增益: Acm = {diff.common_mode_gain():.2e}")
    print(f"  CMRR = {diff.cmrr():.1f} dB")

    # 测试差分和共模
    v_diff = diff.output(V1=0.0, V2=0.1)
    v_cm = diff.output(V1=5.0, V2=5.0)
    print(f"\n  差分信号 (V1=0, V2=0.1V): Vout = {v_diff:.3f} V")
    print(f"  共模信号 (V1=5, V2=5V): Vout = {v_cm:.6f} V")

    # ========================================
    # 4. 仪表放大器
    # ========================================
    print("\n[4] 仪表放大器 (Instrumentation Amplifier)")
    print("-" * 50)

    inamp = InstrumentationAmp(R1=49.4e3, R_g=1e3, opamp=opamp)

    print(f"  R1 = {inamp.R1/1e3:.1f} kOhm")
    print(f"  Rg = {inamp.R_g/1e3:.1f} kOhm")
    print(f"  增益: G = {inamp.gain():.1f}")
    print(f"  带宽: BW = {inamp.bandwidth()/1e3:.1f} kHz")
    print(f"  输入阻抗: Zin ≈ {inamp.input_impedance()/1e9:.0f} GOhm")

    # 测试不同增益
    print(f"\n  增益设置:")
    for target_gain in [10, 50, 100, 500, 1000]:
        inamp.set_gain(target_gain)
        print(f"    目标增益 = {target_gain:>5}: Rg = {inamp.R_g:.1f} Ohm, 实际增益 = {inamp.gain():.1f}")

    # 恢复默认
    inamp = InstrumentationAmp(R1=49.4e3, R_g=1e3, opamp=opamp)

    # 测试差分信号
    v_out = inamp.output(V1=0.0, V2=0.005)
    print(f"\n  差分输入 5mV: Vout = {v_out*1e3:.1f} mV")

    # ========================================
    # 对比总结
    # ========================================
    print("\n" + "=" * 70)
    print("运放电路对比")
    print("=" * 70)
    print(f"{'配置':<18} {'增益':<10} {'Zin':<18} {'BW(kHz)':<12} {'相移':<8}")
    print("-" * 70)
    print(f"{'反相':<18} {inv.gain():<10.1f} {inv.input_impedance()/1e3:<18.0f} {inv.bandwidth()/1e3:<12.0f} {'180°':<8}")
    print(f"{'同相':<18} {ni.gain():<10.1f} {ni.input_impedance()/1e6:<18.0f} {ni.bandwidth()/1e3:<12.0f} {'0°':<8}")
    print(f"{'差分':<18} {diff.differential_gain():<10.1f} {'~10k':<18} {diff.bandwidth()/1e3:<12.0f} {'0°':<8}")
    print(f"{'仪表':<18} {inamp.gain():<10.1f} {'~GOhm':<18} {inamp.bandwidth()/1e3:<12.1f} {'0°':<8}")


if __name__ == '__main__':
    main()
