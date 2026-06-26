"""
ADC/DAC 仿真演示
================

演示完整的 ADC/DAC 转换流程，包括信号生成、采样、量化、编码、
解码、重建和可视化。
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.adc import IdealADC
from src.dac import IdealDAC
from src.metrics import comprehensive_adc_analysis, calculate_snr, calculate_thd
from src.sampling import check_aliasing


def generate_test_signal(t: np.ndarray, freq: float = 1.0, amplitude: float = 1.0,
                         phase: float = 0.0) -> np.ndarray:
    """生成测试信号 (支持多频率叠加)"""
    return amplitude * np.sin(2 * np.pi * freq * t + phase)


def run_adc_dac_demo(num_bits: int = 8, signal_freq: float = 1.0,
                     fs: float = 1000.0) -> dict:
    """
    运行 ADC/DAC 仿真演示

    参数:
        num_bits: ADC/DAC 位数
        signal_freq: 信号频率 (Hz)
        fs: 采样频率 (Hz)

    返回:
        仿真结果 dict
    """
    t_continuous = np.linspace(0, 1, 10000)
    original_signal = generate_test_signal(t_continuous, signal_freq)

    # ADC 转换
    adc = IdealADC(num_bits, (-1.0, 1.0), fs)
    adc_result = adc.convert(original_signal, 0, 1)

    # DAC 重建
    dac = IdealDAC(num_bits, (-1.0, 1.0), fs)
    dac_result = dac.convert(adc_result["digital_codes"], adc_result["sample_times"], 0, 1, "zoh")

    # 分析
    analysis = comprehensive_adc_analysis(
        original_signal, dac_result["analog_signal"], fs, num_bits
    )

    return {
        "original_signal": original_signal,
        "t_continuous": t_continuous,
        "adc_result": adc_result,
        "dac_result": dac_result,
        "analysis": analysis,
    }


def visualize_adc_dac(result: dict, save_path: str = "adc_dac_demo.png"):
    """可视化 ADC/DAC 仿真结果"""
    fig, axes = plt.subplots(4, 1, figsize=(14, 10))

    t_cont = result["t_continuous"]
    original = result["original_signal"]
    adc_result = result["adc_result"]
    dac_result = result["dac_result"]
    analysis = result["analysis"]

    # 1. 原始信号 vs 重建信号
    ax = axes[0]
    ax.plot(t_cont, original, "b-", linewidth=1.5, label="原始模拟信号", alpha=0.7)
    ax.plot(dac_result["reconstruction_times"], dac_result["analog_signal"],
            "r-", linewidth=1, label="重建信号 (ZOH)", alpha=0.7)
    ax.plot(adc_result["sample_times"], adc_result["digital_signal"],
            "go", markersize=3, label="ADC 采样点", alpha=0.5)
    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("幅度")
    ax.set_title(f"ADC/DAC 仿真结果 (B={adc_result['num_levels']-1}bit, fs={adc_result['fs']}Hz)")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    # 2. 量化误差
    ax = axes[1]
    ax.plot(adc_result["sample_times"], adc_result["quantization_error"],
            "m-", linewidth=1, alpha=0.7)
    ax.axhline(y=0, color="k", linestyle="--", alpha=0.5)
    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("量化误差")
    ax.set_title(f"量化误差 (SNR={analysis['snr']:.2f}dB)")
    ax.grid(True, alpha=0.3)

    # 3. 量化电平分布
    ax = axes[2]
    num_levels = adc_result["num_levels"]
    levels = adc_result.get("levels", np.linspace(-1, 1, num_levels))
    ax.hlines(levels, 0, 1, colors="gray", linewidth=0.5, alpha=0.3)
    ax.plot(adc_result["sample_times"], adc_result["digital_signal"],
            "b.", markersize=3, alpha=0.5)
    ax.plot(t_cont, original, "k-", linewidth=0.5, alpha=0.3)
    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("电压 (V)")
    ax.set_title(f"量化电平 (共{num_levels}级, 步长={adc_result['step_size']:.6f}V)")
    ax.set_ylim(-1.1, 1.1)
    ax.grid(True, alpha=0.3)

    # 4. 指标对比
    ax = axes[3]
    metrics = ["SNR (dB)", "理论SNR", "ENOB (bit)", "理论ENOB"]
    values = [analysis["snr"], analysis["theoretical_snr"],
              analysis["enob"], analysis["theoretical_enob"]]
    colors = ["#2ecc71", "#3498db", "#e74c3c", "#9b59b6"]
    bars = ax.bar(metrics, values, color=colors, alpha=0.7, edgecolor="white")

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{val:.2f}", ha="center", va="bottom", fontweight="bold")

    ax.set_ylabel("值")
    ax.set_title("信号质量指标对比")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"图表已保存到: {save_path}")


def print_analysis(analysis: dict):
    """打印分析结果"""
    print("\n" + "=" * 60)
    print("  ADC/DAC 仿真分析结果")
    print("=" * 60)
    print(f"  SNR (信噪比):         {analysis['snr']:.2f} dB")
    print(f"  理论 SNR:             {analysis['theoretical_snr']:.2f} dB")
    print(f"  SINAD (信纳比):       {analysis['sinad']:.2f} dB")
    print(f"  ENOB (有效位数):      {analysis['enob']:.2f} bit")
    print(f"  理论 ENOB:            {analysis['theoretical_enob']:.2f} bit")
    print(f"  THD (总谐波失真):     {analysis['thd']['thd_percent']:.4f}%")
    print(f"  SFDR (无杂散动态范围): {analysis['sfdr']['sfdr_db']:.2f} dB")
    print(f"  RMS 误差:             {analysis['rms_error']:.6f}")
    print(f"  最大误差:             {analysis['max_error']:.6f}")
    print(f"  噪声底:               {analysis['noise_floor_dbm']:.2f} dBm")
    print("=" * 60)


if __name__ == "__main__":
    print("ADC/DAC 仿真演示")
    print("-" * 40)

    # 运行仿真
    result = run_adc_dac_demo(num_bits=8, signal_freq=1.0, fs=1000)

    # 打印分析
    print_analysis(result["analysis"])

    # 可视化
    visualize_adc_dac(result)

    # 不同位数的对比
    print("\n\n不同位数对 SNR 的影响:")
    print("-" * 40)
    for bits in [4, 6, 8, 10, 12]:
        result_bits = run_adc_dac_demo(num_bits=bits, signal_freq=1.0, fs=1000)
        print(f"  {bits:2d} bit: SNR = {result_bits['analysis']['snr']:8.2f} dB, "
              f"ENOB = {result_bits['analysis']['enob']:.2f} bit, "
              f"THD = {result_bits['analysis']['thd']['thd_percent']:.4f}%")
