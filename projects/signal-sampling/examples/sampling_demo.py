"""
采样演示
=========

演示奈奎斯特采样、过采样和欠采样。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.sampling import (
    SamplingConfig,
    nyquist_sample,
    oversample,
    undersample,
    calculate_nyquist_rate,
    get_sampling_info,
)


def demo_nyquist_sampling():
    """奈奎斯特采样演示"""
    print("=" * 60)
    print("奈奎斯特采样演示")
    print("=" * 60)

    f_signal = 100  # 信号频率 100 Hz
    fs = 250  # 采样频率 250 Hz (满足奈奎斯特)
    duration = 0.1

    print(f"信号频率: {f_signal} Hz")
    print(f"奈奎斯特率: {calculate_nyquist_rate(f_signal)} Hz")
    print(f"采样频率: {fs} Hz")

    # 创建采样配置
    config = SamplingConfig(fs=fs, duration=duration, f_signal=f_signal)
    info = get_sampling_info(config)
    print("\n采样信息:")
    for key, value in info.items():
        print(f"  {key}: {value}")

    # 采样
    signal_func = lambda t: np.sin(2 * np.pi * f_signal * t)
    t_sampled, samples = nyquist_sample(signal_func, f_signal, fs, duration)

    print(f"\n采样点数: {len(t_sampled)}")
    print(f"采样时间范围: [{t_sampled[0]:.4f}, {t_sampled[-1]:.4f}] s")
    print(f"采样值范围: [{samples.min():.4f}, {samples.max():.4f}]")


def demo_oversampling():
    """过采样演示"""
    print("\n" + "=" * 60)
    print("过采样演示")
    print("=" * 60)

    f_signal = 100
    oversampling_factor = 4
    duration = 0.05

    print(f"信号频率: {f_signal} Hz")
    print(f"过采样倍数: {oversampling_factor}")
    print(f"奈奎斯特率: {calculate_nyquist_rate(f_signal)} Hz")

    signal_func = lambda t: np.sin(2 * np.pi * f_signal * t)
    t_sampled, samples, fs = oversample(signal_func, f_signal, oversampling_factor, duration)

    print(f"采样频率: {fs} Hz")
    print(f"采样点数: {len(t_sampled)}")


def demo_undersampling():
    """欠采样演示"""
    print("\n" + "=" * 60)
    print("欠采样演示")
    print("=" * 60)

    f_signal = 100
    fs = 80  # 低于奈奎斯特率
    duration = 0.1

    print(f"信号频率: {f_signal} Hz")
    print(f"奈奎斯特率: {calculate_nyquist_rate(f_signal)} Hz")
    print(f"采样频率: {fs} Hz (欠采样!)")

    signal_func = lambda t: np.sin(2 * np.pi * f_signal * t)
    t_sampled, samples, alias_freq = undersample(signal_func, f_signal, fs, duration)

    print(f"混叠频率: {alias_freq} Hz")
    print(f"采样点数: {len(t_sampled)}")

    # 解释
    print("\n混叠解释:")
    print(f"  原始信号频率 {f_signal} Hz 以 {fs} Hz 采样")
    print(f"  混叠后表现为 {alias_freq} Hz 的信号")
    print(f"  因为 |{f_signal} - {round(f_signal/fs)}*{fs}| = {alias_freq}")


def demo_multiple_frequencies():
    """多频率信号采样演示"""
    print("\n" + "=" * 60)
    print("多频率信号采样演示")
    print("=" * 60)

    frequencies = [50, 100, 200, 500]
    fs = 300

    print(f"信号包含频率: {frequencies} Hz")
    print(f"采样频率: {fs} Hz")
    print(f"奈奎斯特频率: {fs/2} Hz")
    print()

    for f in frequencies:
        alias_freq = abs(f - round(f / fs) * fs)
        is_aliasing = f > fs / 2
        status = "混叠!" if is_aliasing else "正常"
        print(f"  {f} Hz -> 混叠频率: {alias_freq:.1f} Hz [{status}]")


if __name__ == "__main__":
    demo_nyquist_sampling()
    demo_oversampling()
    demo_undersampling()
    demo_multiple_frequencies()
