"""
傅里叶变换基础示例

演示 DFT、FFT 的基本用法和频谱分析。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dft import dft, idft
from src.fft import fft, ifft
from src.spectrum import magnitude_spectrum, power_spectrum, phase_spectrum, frequency_bins
from src.signals import sine_wave, composite_signal


def example_dft_basics():
    """DFT 基础示例"""
    print("=" * 60)
    print("DFT 基础示例")
    print("=" * 60)

    # 创建简单信号: 4 个采样点
    x = np.array([1.0, 2.0, 3.0, 4.0])
    print(f"\n输入信号 x = {x}")

    # DFT
    X = dft(x)
    print(f"\nDFT 结果 X = ")
    for k, val in enumerate(X):
        print(f"  X[{k}] = {val:.4f}  (幅度: {abs(val):.4f}, 相位: {np.angle(val):.4f} rad)")

    # IDFT 验证
    x_recovered = idft(X)
    print(f"\nIDFT 恢复信号 = {x_recovered.real}")
    print(f"恢复误差: {np.max(np.abs(x - x_recovered.real)):.2e}")


def example_fft_basics():
    """FFT 基础示例"""
    print("\n" + "=" * 60)
    print("FFT 基础示例")
    print("=" * 60)

    # 创建一个包含两个频率的信号
    sample_rate = 1000.0  # 1000 Hz 采样率
    duration = 1.0        # 1 秒

    # 50 Hz 和 120 Hz 的正弦波叠加
    t = np.arange(int(sample_rate * duration)) / sample_rate
    signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 120 * t)

    print(f"\n信号: 50 Hz (幅度 1.0) + 120 Hz (幅度 0.5)")
    print(f"采样率: {sample_rate} Hz, 时长: {duration} s, 采样点数: {len(signal)}")

    # FFT
    X = fft(signal)

    # 幅度谱
    N = len(signal)
    freqs = frequency_bins(N, sample_rate)
    mag = magnitude_spectrum(X)

    # 找到主要频率分量
    half = N // 2
    peak_indices = np.argsort(mag[:half])[-3:][::-1]
    print("\n主要频率分量:")
    for idx in peak_indices:
        print(f"  频率: {freqs[idx]:.1f} Hz, 幅度: {mag[idx]:.2f}")

    # IFFT 验证 (截断到原始长度)
    x_recovered = ifft(X)[:len(signal)]
    print(f"\nIFFT 恢复误差: {np.max(np.abs(signal - x_recovered.real)):.2e}")


def example_spectrum_analysis():
    """频谱分析示例"""
    print("\n" + "=" * 60)
    print("频谱分析示例")
    print("=" * 60)

    sample_rate = 1000.0

    # 创建复合信号
    signal = composite_signal(
        frequencies=[50, 150, 300],
        amplitudes=[1.0, 0.5, 0.25],
        sample_rate=sample_rate,
        duration=1.0,
    )

    X = fft(signal)

    # 幅度谱
    mag = magnitude_spectrum(X)
    print(f"\n最大幅度: {np.max(mag):.2f}")
    print(f"平均幅度: {np.mean(mag):.2f}")

    # 功率谱
    power = power_spectrum(X)
    print(f"\n总功率: {np.sum(power):.2f}")

    # 相位谱
    phase = phase_spectrum(X)
    print(f"相位范围: [{np.min(phase):.4f}, {np.max(phase):.4f}] rad")

    # Parseval 定理验证 (使用补零后的长度)
    N_padded = len(X)
    signal_padded = np.pad(signal, (0, N_padded - len(signal)))
    energy_time = np.sum(np.abs(signal_padded) ** 2)
    energy_freq = np.sum(np.abs(X) ** 2) / N_padded
    print(f"\nParseval 定理验证:")
    print(f"  时域能量: {energy_time:.2f}")
    print(f"  频域能量: {energy_freq:.2f}")
    print(f"  误差: {abs(energy_time - energy_freq):.2e}")


def example_dft_vs_fft_performance():
    """DFT vs FFT 性能对比"""
    print("\n" + "=" * 60)
    print("DFT vs FFT 性能对比")
    print("=" * 60)

    import time

    sizes = [64, 128, 256, 512, 1024]

    print(f"\n{'N':>6} | {'DFT (ms)':>10} | {'FFT (ms)':>10} | {'加速比':>8}")
    print("-" * 45)

    for N in sizes:
        x = np.random.randn(N)

        # DFT 计时
        start = time.perf_counter()
        dft(x)
        dft_time = (time.perf_counter() - start) * 1000

        # FFT 计时
        start = time.perf_counter()
        fft(x)
        fft_time = (time.perf_counter() - start) * 1000

        speedup = dft_time / fft_time if fft_time > 0 else float("inf")
        print(f"{N:>6} | {dft_time:>10.2f} | {fft_time:>10.2f} | {speedup:>7.1f}x")


def example_convolution_theorem():
    """卷积定理示例"""
    print("\n" + "=" * 60)
    print("卷积定理: 时域卷积 = 频域乘法")
    print("=" * 60)

    # 两个信号
    x = np.array([1.0, 2.0, 3.0, 4.0])
    h = np.array([1.0, 0.5, 0.25])

    # 时域卷积
    y_conv = np.convolve(x, h)
    print(f"\nx = {x}")
    print(f"h = {h}")
    print(f"时域卷积: {y_conv}")

    # 频域乘法
    N = len(y_conv)
    X = fft(np.pad(x, (0, N - len(x))))
    H = fft(np.pad(h, (0, N - len(h))))
    Y = X * H
    y_ifft = np.real(ifft(Y))[:N]

    print(f"频域乘法: {y_ifft}")
    print(f"误差: {np.max(np.abs(y_conv - y_ifft)):.2e}")


if __name__ == "__main__":
    example_dft_basics()
    example_fft_basics()
    example_spectrum_analysis()
    example_dft_vs_fft_performance()
    example_convolution_theorem()
    print("\n所有示例运行完成!")
