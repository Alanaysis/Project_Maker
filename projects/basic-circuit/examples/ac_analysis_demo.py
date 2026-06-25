"""
交流电路分析示例

演示阻抗计算、频率响应、滤波器特性等交流电路分析。
"""

import numpy as np
import matplotlib.pyplot as plt
from src.circuit import Circuit
from src.ac_analysis import ACAnalyzer, resonance_frequency, quality_factor
from src.components import Resistor, Capacitor, Inductor


def example_impedance():
    """阻抗计算示例"""
    print("=" * 60)
    print("阻抗计算示例")
    print("=" * 60)

    f = 1000  # 1kHz

    # 电阻阻抗
    r = Resistor("R", 0, 1, 1000)
    print(f"R=1kΩ @ {f}Hz: Z = {r.impedance(f)}")

    # 电容阻抗
    c = Capacitor("C", 0, 1, 1e-6)
    print(f"C=1μF @ {f}Hz: Z = {c.impedance(f):.2f}")
    print(f"  容抗 = {c.reactance(f):.2f}Ω")

    # 电感阻抗
    l = Inductor("L", 0, 1, 1e-3)
    print(f"L=1mH @ {f}Hz: Z = {l.impedance(f):.4f}")
    print(f"  感抗 = {l.reactance(f):.4f}Ω")


def example_resonance():
    """谐振电路示例"""
    print("\n" + "=" * 60)
    print("谐振电路示例")
    print("=" * 60)

    l = 1e-3   # 1mH
    c = 1e-6   # 1μF
    r = 10     # 10Ω

    f_r = resonance_frequency(l, c)
    q = quality_factor(l, r, f_r)
    bw = r / (2 * np.pi * l)

    print(f"L = {l*1000:.1f}mH, C = {c*1e6:.1f}μF, R = {r}Ω")
    print(f"谐振频率: {f_r:.2f} Hz")
    print(f"品质因数: {q:.2f}")
    print(f"带宽: {bw:.2f} Hz")


def example_rc_filter():
    """RC滤波器频率响应示例"""
    print("\n" + "=" * 60)
    print("RC滤波器频率响应")
    print("=" * 60)

    # 创建RC低通滤波器电路
    circuit = Circuit("RC Low Pass")
    n0 = circuit.add_node("GND")
    n1 = circuit.add_node("IN")
    n2 = circuit.add_node("OUT")
    circuit.set_ground(n0)

    r_val = 1000   # 1kΩ
    c_val = 1e-6   # 1μF

    circuit.add_voltage_source("V1", n0, n1, 1)
    circuit.add_resistor("R1", n1, n2, r_val)
    circuit.add_capacitor("C1", n2, n0, c_val)

    analyzer = ACAnalyzer(circuit)

    # 计算频率响应
    f_start = 10
    f_stop = 1e6
    f_points = 1000
    fr = analyzer.frequency_response(f_start, f_stop, f_points, node_id=n2)

    # 计算截止频率
    f_c = 1.0 / (2 * np.pi * r_val * c_val)
    print(f"R = {r_val}Ω, C = {c_val*1e6:.1f}μF")
    print(f"截止频率: {f_c:.2f} Hz")

    # 绘制频率响应
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # 幅频响应
    ax1.semilogx(fr.frequencies, 20 * np.log10(fr.magnitude), 'b-', linewidth=2)
    ax1.axvline(f_c, color='r', linestyle='--', label=f'f_c = {f_c:.0f} Hz')
    ax1.axhline(-3, color='g', linestyle=':', label='-3 dB')
    ax1.set_xlabel('频率 (Hz)')
    ax1.set_ylabel('增益 (dB)')
    ax1.set_title('RC低通滤波器 - 幅频响应')
    ax1.legend()
    ax1.grid(True, which='both', alpha=0.3)
    ax1.set_xlim(f_start, f_stop)
    ax1.set_ylim(-40, 5)

    # 相频响应
    ax2.semilogx(fr.frequencies, fr.phase, 'r-', linewidth=2)
    ax2.axvline(f_c, color='r', linestyle='--', label=f'f_c = {f_c:.0f} Hz')
    ax2.set_xlabel('频率 (Hz)')
    ax2.set_ylabel('相位 (度)')
    ax2.set_title('RC低通滤波器 - 相频响应')
    ax2.legend()
    ax2.grid(True, which='both', alpha=0.3)
    ax2.set_xlim(f_start, f_stop)

    plt.tight_layout()
    plt.savefig('rc_filter_response.png', dpi=150)
    plt.close()
    print("已保存: rc_filter_response.png")


def example_rlc_resonance():
    """RLC谐振电路示例"""
    print("\n" + "=" * 60)
    print("RLC谐振电路")
    print("=" * 60)

    # 创建RLC串联电路
    circuit = Circuit("RLC Series")
    n0 = circuit.add_node("GND")
    n1 = circuit.add_node("IN")
    n2 = circuit.add_node("L_out")
    n3 = circuit.add_node("C_out")
    circuit.set_ground(n0)

    r_val = 100     # 100Ω
    l_val = 1e-3    # 1mH
    c_val = 1e-6    # 1μF

    circuit.add_voltage_source("V1", n0, n1, 1)
    circuit.add_resistor("R1", n1, n2, r_val)
    circuit.add_inductor("L1", n2, n3, l_val)
    circuit.add_capacitor("C1", n3, n0, c_val)

    analyzer = ACAnalyzer(circuit)

    # 计算频率响应
    f_r = resonance_frequency(l_val, c_val)
    f_start = f_r / 100
    f_stop = f_r * 100

    fr = analyzer.frequency_response(f_start, f_stop, 1000, node_id=n3)

    print(f"R = {r_val}Ω, L = {l_val*1000:.1f}mH, C = {c_val*1e6:.1f}μF")
    print(f"谐振频率: {f_r:.2f} Hz")

    # 绘制频率响应
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # 幅频响应
    ax1.semilogx(fr.frequencies, 20 * np.log10(np.maximum(fr.magnitude, 1e-10)), 'b-', linewidth=2)
    ax1.axvline(f_r, color='r', linestyle='--', label=f'f_r = {f_r:.0f} Hz')
    ax1.set_xlabel('频率 (Hz)')
    ax1.set_ylabel('增益 (dB)')
    ax1.set_title('RLC串联谐振电路 - 幅频响应')
    ax1.legend()
    ax1.grid(True, which='both', alpha=0.3)

    # 相频响应
    ax2.semilogx(fr.frequencies, fr.phase, 'r-', linewidth=2)
    ax2.axvline(f_r, color='r', linestyle='--', label=f'f_r = {f_r:.0f} Hz')
    ax2.axhline(0, color='gray', linestyle=':')
    ax2.set_xlabel('频率 (Hz)')
    ax2.set_ylabel('相位 (度)')
    ax2.set_title('RLC串联谐振电路 - 相频响应')
    ax2.legend()
    ax2.grid(True, which='both', alpha=0.3)

    plt.tight_layout()
    plt.savefig('rlc_resonance_response.png', dpi=150)
    plt.close()
    print("已保存: rlc_resonance_response.png")


if __name__ == "__main__":
    example_impedance()
    example_resonance()
    example_rc_filter()
    example_rlc_resonance()
