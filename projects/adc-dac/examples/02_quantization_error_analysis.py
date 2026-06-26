"""
量化误差分析
============

分析均匀量化和非均匀量化的误差特性，比较不同量化位数
和量化方法对信号质量的影响。
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.quantization import (
    uniform_quantize,
    non_uniform_quantize_a_law,
    non_uniform_quantize_mu_law,
    quantization_noise_analysis,
    calculate_quantization_snr,
)


def generate_test_signal(t: np.ndarray, freq: float = 1.0) -> np.ndarray:
    """生成测试信号"""
    return np.sin(2 * np.pi * freq * t)


def run_quantization_analysis(num_bits_list: list = None):
    """
    运行量化分析

    参数:
        num_bits_list: 要分析的位数列表
    """
    if num_bits_list is None:
        num_bits_list = [4, 6, 8, 10, 12]

    t = np.linspace(0, 1, 1000)
    signal = generate_test_signal(t, 1.0)

    print("\n" + "=" * 70)
    print("  量化误差分析")
    print("=" * 70)

    results = {}

    for bits in num_bits_list:
        # 均匀量化
        uniform_result = uniform_quantize(signal, bits)
        uniform_snr = calculate_quantization_snr(signal, uniform_result["quantized"])

        # A-law 量化
        a_law_result = non_uniform_quantize_a_law(signal, bits)
        a_law_snr = calculate_quantization_snr(signal, a_law_result["quantized"])

        # mu-law 量化
        mu_law_result = non_uniform_quantize_mu_law(signal, bits)
        mu_law_snr = calculate_quantization_snr(signal, mu_law_result["quantized"])

        # 噪声分析
        uniform_noise = quantization_noise_analysis(signal, uniform_result["quantized"])

        results[bits] = {
            "uniform": uniform_result,
            "a_law": a_law_result,
            "mu_law": mu_law_result,
            "uniform_snr": uniform_snr,
            "a_law_snr": a_law_snr,
            "mu_law_snr": mu_law_snr,
            "noise_analysis": uniform_noise,
        }

        print(f"\n  {bits:2d} bit:")
        print(f"    均匀量化 SNR:     {uniform_snr:8.2f} dB (理论: {uniform_result['snr_theoretical']:8.2f} dB)")
        print(f"    A-law SNR:        {a_law_snr:8.2f} dB")
        print(f"    mu-law SNR:       {mu_law_snr:8.2f} dB")
        print(f"    量化步长:         {uniform_result['step_size']:.6f} V")
        print(f"    量化级数:         {uniform_result['num_levels']}")
        print(f"    噪声 RMS:         {uniform_noise['rms_error']:.6f}")
        print(f"    噪声均值:         {uniform_noise['mean_error']:.8f}")

    print("=" * 70)
    return results, t, signal


def visualize_quantization(results: dict, t: np.ndarray, signal: np.ndarray):
    """可视化量化结果"""
    fig, axes = plt.subplots(3, 2, figsize=(14, 12))

    # 1. 不同位数的量化效果对比 (选择 4bit 和 8bit)
    ax = axes[0, 0]
    for bits in [4, 8]:
        if bits in results:
            q = results[bits]["uniform"]["quantized"]
            ax.plot(t, q, linewidth=1, alpha=0.7, label=f"{bits} bit")
    ax.plot(t, signal, "k--", linewidth=1, alpha=0.5, label="原始信号")
    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("幅度")
    ax.set_title("不同位数量化效果对比")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. 量化电平可视化 (8bit)
    ax = axes[0, 1]
    if 8 in results:
        num_levels = results[8]["uniform"]["num_levels"]
        levels = results[8]["uniform"]["levels"]
        ax.hlines(levels, 0, 1, colors="gray", linewidth=0.3, alpha=0.3)
        ax.plot(t, results[8]["uniform"]["quantized"], "b.", markersize=3, alpha=0.5)
        ax.plot(t, signal, "k-", linewidth=0.5, alpha=0.3)
        ax.set_xlabel("时间 (s)")
        ax.set_ylabel("电压 (V)")
        ax.set_title("8bit 量化电平 (256级)")
        ax.set_ylim(-1.1, 1.1)
        ax.grid(True, alpha=0.3)

    # 3. SNR 对比
    ax = axes[1, 0]
    bits = list(results.keys())
    uniform_snrs = [results[b]["uniform_snr"] for b in bits]
    alaw_snrs = [results[b]["a_law_snr"] for b in bits]
    mulaw_snrs = [results[b]["mu_law_snr"] for b in bits]
    theoretical_snrs = [6.02 * b + 1.76 for b in bits]

    ax.plot(bits, uniform_snrs, "bo-", label="均匀量化", linewidth=2)
    ax.plot(bits, alaw_snrs, "rs-", label="A-law", linewidth=2)
    ax.plot(bits, mulaw_snrs, "g^--", label="mu-law", linewidth=2)
    ax.plot(bits, theoretical_snrs, "k--", label="理论 SNR", linewidth=1.5)
    ax.set_xlabel("量化位数 (bit)")
    ax.set_ylabel("SNR (dB)")
    ax.set_title("量化位数 vs SNR")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 4. 量化误差分布
    ax = axes[1, 1]
    if 8 in results:
        error = results[8]["noise_analysis"]["error_hist"][0]
        bins = results[8]["noise_analysis"]["error_hist"][1]
        ax.bar((bins[1:] + bins[:-1]) / 2, error, width=error.max()/50,
               color="steelblue", alpha=0.7, edgecolor="white")
        ax.axhline(y=0, color="k", linestyle="--", alpha=0.5)
        ax.set_xlabel("量化误差 (V)")
        ax.set_ylabel("概率密度")
        ax.set_title("8bit 均匀量化误差分布")
        ax.grid(True, alpha=0.3)

    # 5. 非均匀量化对比
    ax = axes[2, 0]
    if 8 in results:
        ax.plot(t, signal, "k--", linewidth=1, alpha=0.5, label="原始信号")
        ax.plot(t, results[8]["a_law"]["quantized"], "r-", linewidth=1.5, label="A-law 量化")
        ax.plot(t, results[8]["mu_law"]["quantized"], "b-", linewidth=1.5, label="mu-law 量化")
        ax.set_xlabel("时间 (s)")
        ax.set_ylabel("幅度")
        ax.set_title("非均匀量化对比 (A-law vs mu-law)")
        ax.legend()
        ax.grid(True, alpha=0.3)

    # 6. 量化步长 vs 位数
    ax = axes[2, 1]
    step_sizes = [results[b]["uniform"]["step_size"] for b in bits]
    ax.semilogy(bits, step_sizes, "mo-", linewidth=2, markersize=8)
    ax.set_xlabel("量化位数 (bit)")
    ax.set_ylabel("量化步长 (V, 对数坐标)")
    ax.set_title("量化步长 vs 位数")
    ax.grid(True, alpha=0.3, which="both")

    for i, (b, s) in enumerate(zip(bits, step_sizes)):
        ax.annotate(f"{s:.4f}", (b, s), textcoords="offset points",
                    xytext=(10, 10), fontsize=8)

    plt.tight_layout()
    plt.savefig("quantization_analysis.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n图表已保存到: quantization_analysis.png")


if __name__ == "__main__":
    print("量化误差分析")
    print("-" * 40)
    results, t, signal = run_quantization_analysis()
    visualize_quantization(results, t, signal)
