"""
采样率效应分析
==============

分析不同采样频率对信号重建质量的影响，展示混叠现象
和奈奎斯特采样定理的重要性。
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.sampling import ideal_sampling, check_aliasing, calculate_nyquist
from src.adc import IdealADC
from src.dac import IdealDAC
from src.metrics import calculate_snr, calculate_thd


def generate_test_signal(t: np.ndarray, freq: float = 1.0) -> np.ndarray:
    """生成测试信号"""
    return np.sin(2 * np.pi * freq * t)


def analyze_sampling_rate(signal_freq: float, fs_values: list):
    """
    分析不同采样率的影响

    参数:
        signal_freq: 信号频率 (Hz)
        fs_values: 要分析的采样频率列表 (Hz)

    返回:
        分析结果列表
    """
    print("\n" + "=" * 70)
    print(f"  采样率效应分析 (信号频率: {signal_freq} Hz)")
    print("=" * 70)

    nyquist = calculate_nyquist(signal_freq)
    print(f"  奈奎斯特频率: {nyquist} Hz")
    print("-" * 70)

    results = []
    for fs in fs_values:
        # 生成连续信号
        t_continuous = np.linspace(0, 1, 10000)
        signal = generate_test_signal(t_continuous, signal_freq)

        # ADC 转换
        adc = IdealADC(12, (-1.0, 1.0), fs)
        adc_result = adc.convert(signal, 0, 1)

        # DAC 重建
        dac = IdealDAC(12, (-1.0, 1.0), fs)
        dac_result = dac.convert(adc_result["digital_codes"], adc_result["sample_times"], 0, 1, "zoh")

        # 计算 SNR
        snr = calculate_snr(signal, signal - dac_result["analog_signal"])

        # 混叠检测
        alias_check = check_aliasing(signal_freq, fs)

        # FFT 分析
        fft_orig = np.fft.fft(signal)
        fft_orig_mag = np.abs(fft_orig) / len(signal)
        fft_recon = np.fft.fft(dac_result["analog_signal"])
        fft_recon_mag = np.abs(fft_recon) / len(dac_result["analog_signal"])
        freqs = np.fft.fftfreq(len(signal), 1.0 / 10000)

        results.append({
            "fs": fs,
            "snr": snr,
            "aliased": alias_check["aliased"],
            "fs_ratio": alias_check["fs_ratio"],
            "fft_orig_mag": fft_orig_mag,
            "fft_recon_mag": fft_recon_mag,
            "freqs": freqs,
            "num_samples": adc_result["num_samples"],
        })

        status = "混叠!" if alias_check["aliased"] else "OK"
        print(f"  fs={fs:6.0f} Hz | 采样点={adc_result['num_samples']:5d} | "
              f"SNR={snr:8.2f} dB | 混叠={status}")

    print("=" * 70)
    return results, t_continuous, signal


def visualize_sampling_effects(results, t_continuous, signal):
    """可视化采样率效应"""
    fig = plt.figure(figsize=(16, 12))

    # 创建网格布局
    gs = fig.add_gridspec(4, 3, hspace=0.35, wspace=0.3)

    # 1. 原始信号
    ax = fig.add_subplot(gs[0, :])
    ax.plot(t_continuous, signal, "b-", linewidth=1.5)
    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("幅度")
    ax.set_title("原始模拟信号 (1 Hz 正弦波)")
    ax.grid(True, alpha=0.3)

    # 2. 各采样率的重建效果
    for i, res in enumerate(results):
        ax = fig.add_subplot(gs[i + 1, 0])

        # 绘制重建信号
        ax.plot(res["freqs"], res["fft_recon_mag"], "r-", linewidth=0.5, alpha=0.7)
        ax.plot(res["freqs"], res["fft_orig_mag"], "b-", linewidth=0.5, alpha=0.5)
        ax.set_xlabel("频率 (Hz)")
        ax.set_ylabel("幅值")
        status = "混叠" if res["aliased"] else "正常"
        ax.set_title(f"fs = {res['fs']} Hz ({status})")
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, res["fs"] * 0.6)

    # 3. SNR vs 采样率
    ax = fig.add_subplot(gs[:, 1])
    fs_vals = [r["fs"] for r in results]
    snr_vals = [r["snr"] for r in results]
    ax.semilogy(fs_vals, snr_vals, "bo-", linewidth=2, markersize=8)
    ax.axvline(x=calculate_nyquist(1.0), color="r", linestyle="--",
               label="奈奎斯特频率", alpha=0.7)
    ax.set_xlabel("采样频率 (Hz)")
    ax.set_ylabel("SNR (dB)")
    ax.set_title("采样频率 vs SNR")
    ax.legend()
    ax.grid(True, alpha=0.3, which="both")

    # 4. 混叠检测结果
    ax = fig.add_subplot(gs[:, 2])
    aliased = [r["aliased"] for r in results]
    colors = ["#e74c3c" if a else "#2ecc71" for a in aliased]
    ax.barh(fs_vals, [1] * len(fs_vals), color=colors, alpha=0.7)
    ax.set_yticks(fs_vals)
    ax.set_xlabel("状态")
    ax.set_title("混叠检测")
    ax.set_xticks([])
    ax.set_yticklabels([f"{int(f)} Hz" for f in fs_vals])
    for i, (f, a) in enumerate(zip(fs_vals, aliased)):
        ax.text(0.5, i, "混叠" if a else "正常", ha="center", va="center",
                fontweight="bold", fontsize=9)

    plt.savefig("sampling_effects.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n图表已保存到: sampling_effects.png")


if __name__ == "__main__":
    print("采样率效应分析")
    print("-" * 40)

    signal_freq = 1.0  # 1 Hz 信号
    fs_values = [3, 5, 8, 10, 15, 20, 50, 100, 500, 1000]

    results, t, signal = analyze_sampling_rate(signal_freq, fs_values)
    visualize_sampling_effects(results, t, signal)
