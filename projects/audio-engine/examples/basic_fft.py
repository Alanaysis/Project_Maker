#!/usr/bin/env python3
"""
FFT 基础示例

演示如何使用 FFT 进行频域分析。
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fft import FFT, IFFT


def basic_fft_example():
    """基本 FFT 使用示例"""
    print("=" * 60)
    print("FFT 基础示例")
    print("=" * 60)

    # 创建信号参数
    sample_rate = 44100
    duration = 0.1  # 100ms
    N = int(sample_rate * duration)

    # 创建包含多个频率的信号
    t = np.linspace(0, duration, N, endpoint=False)
    signal = (np.sin(2 * np.pi * 440 * t) +  # A4 (440 Hz)
              0.5 * np.sin(2 * np.pi * 880 * t) +  # A5 (880 Hz)
              0.3 * np.sin(2 * np.pi * 1320 * t))  # E6 (1320 Hz)

    print(f"信号长度: {N} 采样点")
    print(f"采样率: {sample_rate} Hz")
    print(f"时长: {duration} 秒")
    print()

    # FFT 变换
    spectrum = FFT.transform(signal)
    print(f"FFT 结果长度: {len(spectrum)}")

    # 幅度谱
    magnitude = FFT.magnitude_spectrum(signal)
    freqs = np.fft.fftfreq(N, 1.0 / sample_rate)[:N // 2]

    # 找到峰值频率
    peaks = np.argsort(magnitude)[-3:][::-1]
    print("\n检测到的频率成分:")
    for i, idx in enumerate(peaks):
        freq = freqs[idx]
        amp = magnitude[idx]
        print(f"  {i + 1}. {freq:.1f} Hz, 幅度: {amp:.4f}")

    # IFFT 验证
    reconstructed = IFFT.transform_real(spectrum)
    error = np.max(np.abs(signal - reconstructed[:N]))
    print(f"\nFFT -> IFFT 最大误差: {error:.2e}")


def demonstrate_linearity():
    """演示 FFT 的线性性质"""
    print("\n" + "=" * 60)
    print("FFT 线性性质演示")
    print("=" * 60)

    N = 64
    x = np.random.randn(N)
    y = np.random.randn(N)
    a, b = 2.0, 3.0

    # FFT(a*x + b*y)
    direct = FFT.transform(a * x + b * y)

    # a*FFT(x) + b*FFT(y)
    linear = a * FFT.transform(x) + b * FFT.transform(y)

    error = np.max(np.abs(direct - linear))
    print(f"FFT(a*x + b*y) vs a*FFT(x) + b*FFT(y)")
    print(f"最大误差: {error:.2e}")
    print(f"验证线性: {'通过' if error < 1e-10 else '失败'}")


def demonstrate_parseval():
    """演示帕塞瓦尔定理"""
    print("\n" + "=" * 60)
    print("帕塞瓦尔定理演示")
    print("=" * 60)

    N = 128
    signal = np.random.randn(N)

    # 时域能量
    time_energy = np.sum(signal ** 2)

    # 频域能量
    spectrum = FFT.transform(signal)
    freq_energy = np.sum(np.abs(spectrum) ** 2) / N

    print(f"时域能量: {time_energy:.6f}")
    print(f"频域能量: {freq_energy:.6f}")
    print(f"差异: {abs(time_energy - freq_energy):.2e}")
    print(f"能量守恒: {'通过' if abs(time_energy - freq_energy) < 1e-10 else '失败'}")


def demonstrate_frequency_resolution():
    """演示频率分辨率"""
    print("\n" + "=" * 60)
    print("频率分辨率演示")
    print("=" * 60)

    sample_rate = 1000  # 1000 Hz
    duration = 1.0  # 1 秒
    N = int(sample_rate * duration)

    # 创建两个相近频率的信号
    t = np.linspace(0, duration, N, endpoint=False)
    f1, f2 = 100, 105  # 100 Hz 和 105 Hz
    signal = np.sin(2 * np.pi * f1 * t) + np.sin(2 * np.pi * f2 * t)

    # FFT
    spectrum = FFT.transform(signal)
    magnitude = np.abs(spectrum[:N // 2]) * 2.0 / N
    freqs = np.fft.fftfreq(N, 1.0 / sample_rate)[:N // 2]

    # 频率分辨率
    freq_resolution = sample_rate / N
    print(f"采样率: {sample_rate} Hz")
    print(f"信号长度: {N} 采样点 ({duration} 秒)")
    print(f"频率分辨率: {freq_resolution} Hz")
    print(f"两个频率差: {f2 - f1} Hz")
    print(f"能否分辨: {'可以' if (f2 - f1) > freq_resolution else '困难'}")

    # 找到峰值
    peaks = np.argsort(magnitude)[-2:]
    peak_freqs = freqs[peaks]
    print(f"\n检测到的峰值频率: {peak_freqs}")


if __name__ == "__main__":
    basic_fft_example()
    demonstrate_linearity()
    demonstrate_parseval()
    demonstrate_frequency_resolution()
