"""
基本放大器演示

展示三种BJT放大器配置的特性和参数对比。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.bjt import BJTParams, CommonEmitter, CommonCollector, CommonBase


def main():
    print("=" * 70)
    print("BJT 基本放大器演示")
    print("=" * 70)

    # 创建 BJT 参数 (2N3904 类型)
    bjt = BJTParams(beta=100, V_A=100, V_BE=0.7)

    # ========================================
    # 1. 共射放大器
    # ========================================
    print("\n[1] 共射放大器 (Common Emitter)")
    print("-" * 50)

    ce = CommonEmitter(
        R_B1=47e3, R_B2=10e3, R_C=4.7e3, R_E=2.2e3,
        V_CC=12.0, bjt=bjt
    )

    op = ce.operating_point()
    print(f"  电源电压: {ce.V_CC} V")
    print(f"  基极偏置: VB = {op['V_B']:.3f} V")
    print(f"  发射极电压: VE = {op['V_E']:.3f} V")
    print(f"  集电极电流: IC = {op['I_C']*1e3:.3f} mA")
    print(f"  集电极-发射极电压: VCE = {op['V_CE']:.3f} V")

    print(f"\n  电压增益: Av = {ce.voltage_gain():.2f}")
    print(f"  电压增益 (带 4.7k 负载): Av = {ce.voltage_gain(R_L=4.7e3):.2f}")
    print(f"  输入阻抗: Zin = {ce.input_impedance():.0f} Ohm")
    print(f"  输出阻抗: Zout = {ce.output_impedance():.0f} Ohm")
    print(f"  相移: 180 度 (反相)")

    # ========================================
    # 2. 共集放大器
    # ========================================
    print("\n[2] 共集放大器 (Common Collector / Emitter Follower)")
    print("-" * 50)

    cc = CommonCollector(
        R_B1=47e3, R_B2=10e3, R_E=2.2e3,
        V_CC=12.0, bjt=bjt
    )

    op = cc.operating_point()
    print(f"  集电极电流: IC = {op['I_C']*1e3:.3f} mA")

    print(f"\n  电压增益: Av = {cc.voltage_gain():.4f}")
    print(f"  电压增益 (带 1k 负载): Av = {cc.voltage_gain(R_L=1e3):.4f}")
    print(f"  输入阻抗: Zin = {cc.input_impedance():.0f} Ohm")
    print(f"  输出阻抗 (Rs=1k): Zout = {cc.output_impedance(R_s=1e3):.1f} Ohm")
    print(f"  相移: 0 度 (同相)")

    # ========================================
    # 3. 共基放大器
    # ========================================
    print("\n[3] 共基放大器 (Common Base)")
    print("-" * 50)

    cb = CommonBase(
        R_E=2.2e3, R_C=4.7e3, V_CC=12.0,
        I_C_bias=1e-3, bjt=bjt
    )

    op = cb.operating_point()
    print(f"  集电极电流: IC = {op['I_C']*1e3:.3f} mA")

    print(f"\n  电压增益: Av = {cb.voltage_gain():.2f}")
    print(f"  输入阻抗: Zin = {cb.input_impedance():.1f} Ohm")
    print(f"  输出阻抗: Zout = {cb.output_impedance():.0f} Ohm")
    print(f"  相移: 0 度 (同相)")

    # ========================================
    # 对比总结
    # ========================================
    print("\n" + "=" * 70)
    print("三种 BJT 放大器对比")
    print("=" * 70)
    print(f"{'配置':<20} {'增益':<12} {'Zin':<15} {'Zout':<15} {'相移':<8}")
    print("-" * 70)
    print(f"{'共射 (CE)':<20} {ce.voltage_gain():<12.2f} {ce.input_impedance():<15.0f} {ce.output_impedance():<15.0f} {'180°':<8}")
    print(f"{'共集 (CC)':<20} {cc.voltage_gain():<12.4f} {cc.input_impedance():<15.0f} {cc.output_impedance(R_s=1e3):<15.1f} {'0°':<8}")
    print(f"{'共基 (CB)':<20} {cb.voltage_gain():<12.2f} {cb.input_impedance():<15.1f} {cb.output_impedance():<15.0f} {'0°':<8}")

    print("\n特点:")
    print("  共射: 高增益 + 反相 -> 电压放大")
    print("  共集: 增益≈1 + 高输入阻抗 + 低输出阻抗 -> 缓冲器")
    print("  共基: 高增益 + 同相 + 低输入阻抗 -> 高频放大")


if __name__ == '__main__':
    main()
