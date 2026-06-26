"""
SNR vs 位数关系分析
==================

分析 ADC 位数对信噪比 (SNR) 的影响，验证理论公式:
SNR = 6.02 * B + 1.76 (dB)

其中 B 是量化位数。
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.adc import IdealADC
from src.dac import IdealDAC
from src.metrics import comprehensive_adc_analysis, calculate_snr
from src.quantization import uniform_quantize, calculate_quantization_snr


def generate_test_signal(t: np.ndarray, freq: float = 1.0) -> np.ndarray:
    """生成满量程正弦波"""
    return np.sin(2 * np.pi * freq * t)


def analyze_snr_vs_bits(num_bits_range: list = None, signal_freq: float = 1.0,
                        fs: float = 1000.0):
    """
    分析 SNR 与位数的关系

    参数:
        num_bits_range: 位数范围
        signal_freq: 信号频率
        fs: 采样频率

    返回:
        分析结果
    """
    if num_bits_range is None:
        num_bits_range = range(2, 17)

    print("\n" + "=" * 70)
    print("  SNR vs 量化位数分析")
    print("=" * 70)
    print(f"  信号频率: {signal_freq} Hz, 采样频率: {fs} Hz")
    print("-" * 70)
    print(f"  {'位数':>5s} | {'实测SNR':>10s} | {'理论SNR':>10s} | {'ENOB':>8s} | {'理论ENOB':>10s} | {'THD':>10s}")
    print("-" * 70)

    results = []

    for bits in num_bits_range:
        # 生成信号
        t = np.linspace(0, 1, 10000)
        signal = generate_test_signal(t, signal_freq)

        # ADC
        adc = IdealADC(bits, (-1.0, 1.0), fs)
        adc_result = adc.convert(signal, 0, 1)

        # DAC
        dac = IdealDAC(bits, (-1.0, 1.0), fs)
        dac_result = dac.convert(adc_result["digital_codes"], adc_result["sample_times"], 0, 1, "zoh")

        # 分析
        analysis = comprehensive_adc_analysis(signal, dac_result["analog_signal"], fs, bits)

        results.append({
            "bits": bits,
            "snr": analysis["snr"],
            "theoretical_snr": analysis["theoretical_snr"],
            "enob": analysis["enob"],
            "theoretical_enob": analysis["theoretical_enob"],
            "thd_percent": analysis["thd"]["thd_percent"],
            "sinad": analysis["sinad"],
        })

        print(f"  {bits:5d} | {analysis['snr']:10.2f} | {analysis['theoretical_snr']:10.2f} | "
              f"{analysis['enob']:8.2f} | {analysis['theoretical_enob']:10.2f} | "
              f"{analysis['thd']['thd_percent']:10.4f}")

    print("=" * 70)
    return results, t, signal


def visualize_snr_vs_bits(results, t, signal):
    """可视化 SNR 与位数的关系"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    bits = [r["bits"] for r in results]
    measured_snr = [r["snr"] for r in results]
    theoretical_snr = [r["theoretical_snr"] for r in results]
    measured_enob = [r["enob"] for r in results]
    theoretical_enob = [r["theoretical_enob"] for r in results]
    thd_vals = [r["thd_percent"] for r in results]
    sinad_vals = [r["sinad"] for r in results]

    # 1. SNR vs 位数
    ax = axes[0, 0]
    ax.plot(bits, measured_snr, "bo-", label="实测 SNR", linewidth=2, markersize=6)
    ax.plot(bits, theoretical_snr, "r--", label="理论 SNR (6.02B+1.76)", linewidth=2)
    ax.set_xlabel("量化位数 (bit)")
    ax.set_ylabel("SNR (dB)")
    ax.set_title("SNR vs 量化位数")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 添加标注
    for b, s, st in zip(bits, measured_snr, theoretical_snr):
        if b in [4, 8, 12, 16]:
            ax.annotate(f"{b}bit\n{st:.1f}dB", (b, st), textcoords="offset points",
                        xytext=(10, 10), fontsize=8)

    # 2. ENOB vs 位数
    ax = axes[0, 1]
    ax.plot(bits, measured_enob, "go-", label="实测 ENOB", linewidth=2, markersize=6)
    ax.plot(bits, theoretical_enob, "r--", label="理论 ENOB", linewidth=2)
    ax.set_xlabel("量化位数 (bit)")
    ax.set_ylabel("ENOB (bit)")
    ax.set_title("ENOB vs 量化位数")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. THD vs 位数
    ax = axes[1, 0]
    ax.semilogy(bits, thd_vals, "m^-", linewidth=2, markersize=6)
    ax.set_xlabel("量化位数 (bit)")
    ax.set_ylabel("THD (%)")
    ax.set_title("总谐波失真 (THD) vs 位数")
    ax.grid(True, alpha=0.3, which="both")

    # 4. SINAD vs 位数
    ax = axes[1, 1]
    ax.plot(bits, sinad_vals, "cs-", linewidth=2, markersize=6)
    ax.set_xlabel("量化位数 (bit)")
    ax.set_ylabel("SINAD (dB)")
    ax.set_title("信纳比 (SINAD) vs 位数")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("snr_vs_bits.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n图表已保存到: snr_vs_bits.png")


def show_formula_derivation():
    """展示 SNR 公式推导"""
    print("\n" + "=" * 70)
    print("  SNR 公式推导")
    print("=" * 70)
    print("""
  对于满量程正弦波输入，理想 ADC 的 SNR 为:

  SNR = 6.02 * B + 1.76 (dB)

  推导:
  1. 量化步长: delta = V_range / 2^B
  2. 量化噪声功率: P_n = delta^2 / 12
  3. 满量程正弦波功率: P_s = (V_range/2)^2 / 2 = V_range^2 / 8
  4. SNR = 10 * log10(P_s / P_n)
        = 10 * log10((V_range^2/8) / (V_range^2 / (12 * 2^(2B))))
        = 10 * log10(3 * 2^(2B))
        = 10 * log10(3) + 20 * B * log10(2)
        = 4.77 + 6.02 * B
        ≈ 6.02 * B + 1.76
  其中 1.76 = 10 * log10(3) - 10 * log10(8) = 10 * log10(3/8) + 10 = 4.77 - 3 + 10 = 1.76

  关键点:
  - 每增加 1 bit，SNR 提高约 6 dB
  - 16-bit ADC 的理论 SNR 约为 99 dB
  - 实际 ADC 的 SNR 通常低于理论值 (由于非理想因素)
  """)
    print("=" * 70)


if __name__ == "__main__":
    print("SNR vs 量化位数关系分析")
    print("-" * 40)

    show_formula_derivation()

    results, t, signal = analyze_snr_vs_bits()
    visualize_snr_vs_bits(results, t, signal)
