#!/usr/bin/env python3
"""
音频滤波示例

演示如何使用滤波器处理音频信号。
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audio_signal import AudioSignal
from src.filters import LowPassFilter, HighPassFilter, BandPassFilter, NotchFilter


def lowpass_filter_example():
    """低通滤波示例"""
    print("=" * 60)
    print("低通滤波示例")
    print("=" * 60)

    sample_rate = 44100
    duration = 0.5

    # 创建包含高低频的信号
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    low_freq = np.sin(2 * np.pi * 200 * t)   # 200 Hz
    high_freq = np.sin(2 * np.pi * 5000 * t)  # 5000 Hz
    signal = AudioSignal(low_freq + high_freq, sample_rate)

    print(f"原始信号: {signal}")
    print("包含 200 Hz 和 5000 Hz 两个频率成分")

    # 低通滤波
    cutoff = 1000
    lpf = LowPassFilter(cutoff_freq=cutoff, rolloff_width=200, sample_rate=sample_rate)
    filtered = lpf.apply(signal)

    print(f"\n低通滤波 (截止频率: {cutoff} Hz)")
    print(f"滤波后信号: {filtered}")

    # 分析频谱
    freqs_orig, mag_orig = signal.get_spectrum()
    freqs_filt, mag_filt = filtered.get_spectrum()

    # 找到主要频率成分
    def find_peaks(freqs, magnitude, n=3):
        idx = np.argsort(magnitude)[-n:][::-1]
        return [(freqs[i], magnitude[i]) for i in idx]

    print("\n原始信号主要频率:")
    for freq, mag in find_peaks(freqs_orig, mag_orig):
        print(f"  {freq:.1f} Hz: {mag:.4f}")

    print("\n滤波后主要频率:")
    for freq, mag in find_peaks(freqs_filt, mag_filt):
        print(f"  {freq:.1f} Hz: {mag:.4f}")


def highpass_filter_example():
    """高通滤波示例"""
    print("\n" + "=" * 60)
    print("高通滤波示例")
    print("=" * 60)

    sample_rate = 44100
    duration = 0.5

    # 创建信号
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    low_freq = np.sin(2 * np.pi * 100 * t)   # 100 Hz
    high_freq = np.sin(2 * np.pi * 3000 * t)  # 3000 Hz
    signal = AudioSignal(low_freq + high_freq, sample_rate)

    # 高通滤波
    cutoff = 500
    hpf = HighPassFilter(cutoff_freq=cutoff, rolloff_width=200, sample_rate=sample_rate)
    filtered = hpf.apply(signal)

    print(f"高通滤波 (截止频率: {cutoff} Hz)")
    print("应该去除 100 Hz，保留 3000 Hz")

    freqs_orig, mag_orig = signal.get_spectrum()
    freqs_filt, mag_filt = filtered.get_spectrum()

    def find_peaks(freqs, magnitude, n=3):
        idx = np.argsort(magnitude)[-n:][::-1]
        return [(freqs[i], magnitude[i]) for i in idx]

    print("\n原始信号主要频率:")
    for freq, mag in find_peaks(freqs_orig, mag_orig):
        print(f"  {freq:.1f} Hz: {mag:.4f}")

    print("\n滤波后主要频率:")
    for freq, mag in find_peaks(freqs_filt, mag_filt):
        print(f"  {freq:.1f} Hz: {mag:.4f}")


def bandpass_filter_example():
    """带通滤波示例"""
    print("\n" + "=" * 60)
    print("带通滤波示例")
    print("=" * 60)

    sample_rate = 44100
    duration = 0.5

    # 创建信号
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    signal_data = (np.sin(2 * np.pi * 100 * t) +   # 100 Hz
                   np.sin(2 * np.pi * 1000 * t) +   # 1000 Hz
                   np.sin(2 * np.pi * 5000 * t))    # 5000 Hz
    signal = AudioSignal(signal_data, sample_rate)

    # 带通滤波
    low_freq = 500
    high_freq = 2000
    bpf = BandPassFilter(low_freq=low_freq, high_freq=high_freq, sample_rate=sample_rate)
    filtered = bpf.apply(signal)

    print(f"带通滤波 (通带: {low_freq}-{high_freq} Hz)")
    print("应该保留 1000 Hz，去除 100 Hz 和 5000 Hz")

    freqs_orig, mag_orig = signal.get_spectrum()
    freqs_filt, mag_filt = filtered.get_spectrum()

    def find_peaks(freqs, magnitude, n=3):
        idx = np.argsort(magnitude)[-n:][::-1]
        return [(freqs[i], magnitude[i]) for i in idx]

    print("\n原始信号主要频率:")
    for freq, mag in find_peaks(freqs_orig, mag_orig):
        print(f"  {freq:.1f} Hz: {mag:.4f}")

    print("\n滤波后主要频率:")
    for freq, mag in find_peaks(freqs_filt, mag_filt):
        print(f"  {freq:.1f} Hz: {mag:.4f}")


def notch_filter_example():
    """陷波滤波示例"""
    print("\n" + "=" * 60)
    print("陷波滤波示例（去除工频干扰）")
    print("=" * 60)

    sample_rate = 44100
    duration = 0.5

    # 创建信号 + 50Hz 工频干扰
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    signal_freq = np.sin(2 * np.pi * 440 * t)  # 440 Hz
    interference = 0.5 * np.sin(2 * np.pi * 50 * t)  # 50 Hz 干扰
    signal = AudioSignal(signal_freq + interference, sample_rate)

    print("原始信号: 440 Hz 信号 + 50 Hz 工频干扰")

    # 陷波滤波
    notch = NotchFilter(center_freq=50, bandwidth=20, sample_rate=sample_rate)
    filtered = notch.apply(signal)

    print("陷波滤波: 去除 50 Hz 干扰")

    freqs_orig, mag_orig = signal.get_spectrum()
    freqs_filt, mag_filt = filtered.get_spectrum()

    # 检查 50 Hz 和 440 Hz
    idx_50_orig = np.argmin(np.abs(freqs_orig - 50))
    idx_440_orig = np.argmin(np.abs(freqs_orig - 440))
    idx_50_filt = np.argmin(np.abs(freqs_filt - 50))
    idx_440_filt = np.argmin(np.abs(freqs_filt - 440))

    print(f"\n原始信号:")
    print(f"  50 Hz 幅度: {mag_orig[idx_50_orig]:.4f}")
    print(f"  440 Hz 幅度: {mag_orig[idx_440_orig]:.4f}")

    print(f"\n滤波后:")
    print(f"  50 Hz 幅度: {mag_filt[idx_50_filt]:.4f}")
    print(f"  440 Hz 幅度: {mag_filt[idx_440_filt]:.4f}")

    print(f"\n50 Hz 衰减: {mag_filt[idx_50_filt] / mag_orig[idx_50_orig] * 100:.1f}%")
    print(f"440 Hz 保留: {mag_filt[idx_440_filt] / mag_orig[idx_440_orig] * 100:.1f}%")


def filter_cascade_example():
    """滤波器级联示例"""
    print("\n" + "=" * 60)
    print("滤波器级联示例")
    print("=" * 60)

    sample_rate = 44100
    duration = 0.5

    # 创建信号
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    signal_data = (np.sin(2 * np.pi * 100 * t) +
                   np.sin(2 * np.pi * 500 * t) +
                   np.sin(2 * np.pi * 2000 * t) +
                   np.sin(2 * np.pi * 8000 * t))
    signal = AudioSignal(signal_data, sample_rate)

    print("原始信号包含: 100, 500, 2000, 8000 Hz")

    # 级联滤波：先低通再高通（带通效果）
    lpf = LowPassFilter(cutoff_freq=3000, sample_rate=sample_rate)
    hpf = HighPassFilter(cutoff_freq=300, sample_rate=sample_rate)

    filtered = lpf.apply(signal)
    filtered = hpf.apply(filtered)

    print("级联滤波: 高通(300Hz) + 低通(3000Hz)")
    print("应该保留 500 Hz 和 2000 Hz")

    freqs, mag = filtered.get_spectrum()

    # 找峰值
    peaks = np.argsort(mag)[-4:][::-1]
    print("\n滤波后主要频率:")
    for idx in peaks:
        print(f"  {freqs[idx]:.1f} Hz: {mag[idx]:.4f}")


if __name__ == "__main__":
    lowpass_filter_example()
    highpass_filter_example()
    bandpass_filter_example()
    notch_filter_example()
    filter_cascade_example()
