"""
信号分析示例

演示如何使用傅里叶变换分析各种信号。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.fft import fft, ifft
from src.spectrum import (
    magnitude_spectrum,
    power_spectrum,
    phase_spectrum,
    frequency_bins,
    find_peaks,
    spectral_centroid,
    bandwidth,
    peak_frequencies,
)
from src.signals import (
    sine_wave,
    composite_signal,
    square_wave,
    sawtooth_wave,
    white_noise,
)


def analyze_signal(signal, sample_rate, name):
    """分析一个信号的频谱特性"""
    N = len(signal)
    X = fft(signal)
    freqs = frequency_bins(N, sample_rate)
    mag = magnitude_spectrum(X)

    print(f"\n{'=' * 50}")
    print(f"信号: {name}")
    print(f"{'=' * 50}")
    print(f"采样点数: {N}")
    print(f"采样率: {sample_rate} Hz")
    print(f"时长: {N / sample_rate:.3f} s")
    print(f"时域统计: 均值={np.mean(signal):.4f}, 标准差={np.std(signal):.4f}")
    print(f"频域统计: 最大幅度={np.max(mag):.2f}")

    # 频谱质心
    centroid = spectral_centroid(X, sample_rate)
    print(f"频谱质心: {centroid:.1f} Hz")

    # 带宽
    bw = bandwidth(X, sample_rate, threshold=0.5)
    print(f"带宽 (50%): {bw:.1f} Hz")

    # 峰值频率
    peaks = peak_frequencies(X, sample_rate, threshold=0.1, min_distance=10)
    if peaks:
        print(f"主要频率分量:")
        for freq, amp in peaks[:5]:
            if freq >= 0:
                print(f"  {freq:8.1f} Hz  幅度: {amp:.2f}")


def example_pure_tone():
    """纯音分析"""
    sample_rate = 44100.0
    signal = sine_wave(440, sample_rate, 0.1)  # A4 音符
    analyze_signal(signal, sample_rate, "A4 音符 (440 Hz)")


def example_chord():
    """和弦分析"""
    sample_rate = 44100.0
    # C 大三和弦: C4(261.63), E4(329.63), G4(392.00)
    signal = composite_signal(
        frequencies=[261.63, 329.63, 392.00],
        amplitudes=[1.0, 0.8, 0.6],
        sample_rate=sample_rate,
        duration=0.1,
    )
    analyze_signal(signal, sample_rate, "C 大三和弦 (C-E-G)")


def example_square_wave_harmonics():
    """方波谐波分析"""
    sample_rate = 10000.0
    signal = square_wave(100, sample_rate, 0.1)
    analyze_signal(signal, sample_rate, "方波 (100 Hz)")

    print("\n理论分析: 方波由奇次谐波组成")
    print("  x(t) = (4/π) * [sin(2πft) + sin(6πft)/3 + sin(10πft)/5 + ...]")


def example_sawtooth_harmonics():
    """锯齿波谐波分析"""
    sample_rate = 10000.0
    signal = sawtooth_wave(100, sample_rate, 0.1)
    analyze_signal(signal, sample_rate, "锯齿波 (100 Hz)")

    print("\n理论分析: 锯齿波包含所有谐波")
    print("  x(t) = (2/π) * [sin(2πft) - sin(4πft)/2 + sin(6πft)/3 - ...]")


def example_noise_analysis():
    """噪声分析"""
    sample_rate = 1000.0
    np.random.seed(42)
    signal = white_noise(sample_rate, 1.0)
    analyze_signal(signal, sample_rate, "白噪声")

    print("\n理论分析: 白噪声的功率谱应该是平坦的")


def example_musical_scale():
    """音阶分析"""
    sample_rate = 44100.0

    # C 大调音阶频率
    notes = {
        "C4": 261.63,
        "D4": 293.66,
        "E4": 329.63,
        "F4": 349.23,
        "G4": 392.00,
        "A4": 440.00,
        "B4": 493.88,
        "C5": 523.25,
    }

    print(f"\n{'=' * 50}")
    print("C 大调音阶频率分析")
    print(f"{'=' * 50}")

    for note_name, freq in notes.items():
        signal = sine_wave(freq, sample_rate, 0.05)
        X = fft(signal)
        peaks = peak_frequencies(X, sample_rate, threshold=0.1, min_distance=5)
        detected_freq = peaks[0][0] if peaks else 0
        error = abs(detected_freq - freq)
        print(f"  {note_name}: 理论 {freq:7.2f} Hz, 检测 {detected_freq:7.2f} Hz, 误差 {error:.2f} Hz")


def example_sampling_theorem():
    """采样定理演示"""
    print(f"\n{'=' * 50}")
    print("奈奎斯特采样定理演示")
    print(f"{'=' * 50}")

    freq = 100.0  # 信号频率 100 Hz

    # 正确采样: 采样率 > 2 * 频率
    print(f"\n信号频率: {freq} Hz")
    print(f"奈奎斯特频率: {2 * freq} Hz")

    for sample_rate in [500, 250, 200, 150]:
        signal = sine_wave(freq, sample_rate, 0.1)
        X = fft(signal)
        N_padded = len(X)
        mag = magnitude_spectrum(X[:N_padded//2])
        freqs = np.abs(frequency_bins(N_padded, sample_rate)[:N_padded//2])
        peak_freq = freqs[np.argmax(mag)]

        status = "正确" if sample_rate > 2 * freq else "混叠!"
        print(f"  采样率 {sample_rate:4d} Hz: 检测到 {peak_freq:6.1f} Hz [{status}]")


if __name__ == "__main__":
    example_pure_tone()
    example_chord()
    example_square_wave_harmonics()
    example_sawtooth_harmonics()
    example_noise_analysis()
    example_musical_scale()
    example_sampling_theorem()
    print("\n所有信号分析示例运行完成!")
