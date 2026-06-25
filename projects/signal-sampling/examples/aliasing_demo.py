"""
混叠演示
=========

演示混叠现象和抗混叠滤波。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.aliasing import (
    demonstrate_aliasing,
    anti_aliasing_filter,
    compute_spectrum,
    show_aliasing_effect,
    create_anti_aliasing_demo,
)


def demo_aliasing_phenomenon():
    """混叠现象演示"""
    print("=" * 60)
    print("混叠现象演示")
    print("=" * 60)

    f_signal = 100
    fs = 80  # 低于奈奎斯特率

    print(f"信号频率: {f_signal} Hz")
    print(f"采样频率: {fs} Hz")
    print(f"奈奎斯特率: {2 * f_signal} Hz")
    print()

    result = demonstrate_aliasing(f_signal=f_signal, fs=fs, duration=0.05)

    print(f"混叠频率: {result['alias_freq']} Hz")
    print()
    print("解释:")
    print(f"  原始信号频率: {f_signal} Hz")
    print(f"  采样频率: {fs} Hz")
    k = round(f_signal / fs)
    print(f"  k = round({f_signal}/{fs}) = {k}")
    print(f"  混叠频率 = |{f_signal} - {k}*{fs}| = {result['alias_freq']} Hz")
    print()
    print("混叠效果:")
    print(f"  {f_signal} Hz 的信号在 {fs} Hz 采样后")
    print(f"  看起来像 {result['alias_freq']} Hz 的信号")


def demo_aliasing_different_frequencies():
    """不同频率的混叠演示"""
    print("\n" + "=" * 60)
    print("不同频率的混叠演示")
    print("=" * 60)

    fs = 100
    f_list = [30, 60, 80, 120, 150, 250]

    print(f"采样频率: {fs} Hz")
    print(f"奈奎斯特频率: {fs/2} Hz")
    print()
    print("信号频率 | 混叠频率 | 是否混叠")
    print("-" * 40)

    for f in f_list:
        alias = abs(f - round(f / fs) * fs)
        is_aliasing = f > fs / 2
        status = "是" if is_aliasing else "否"
        print(f"  {f:5d} Hz | {alias:6.1f} Hz | {status}")


def demo_anti_aliasing_filter():
    """抗混叠滤波演示"""
    print("\n" + "=" * 60)
    print("抗混叠滤波演示")
    print("=" * 60)

    # 创建混合信号
    fs = 1000
    t = np.linspace(0, 1, fs)

    f_low = 50
    f_high = 300

    signal = np.sin(2 * np.pi * f_low * t) + 0.5 * np.sin(2 * np.pi * f_high * t)

    print(f"采样频率: {fs} Hz")
    print(f"低频分量: {f_low} Hz")
    print(f"高频分量: {f_high} Hz")
    print()

    # 计算原始频谱
    freqs_orig, mag_orig = compute_spectrum(signal, fs)

    # 抗混叠滤波
    cutoff = 100  # 截止频率
    filtered = anti_aliasing_filter(signal, fs=fs, cutoff_freq=cutoff)

    # 计算滤波后频谱
    freqs_filt, mag_filt = compute_spectrum(filtered, fs)

    print(f"抗混叠滤波器截止频率: {cutoff} Hz")
    print()

    # 找峰值频率
    peak_orig = freqs_orig[np.argmax(mag_orig)]
    peak_filt = freqs_filt[np.argmax(mag_filt)]

    print(f"原始信号峰值频率: {peak_orig:.1f} Hz")
    print(f"滤波后峰值频率: {peak_filt:.1f} Hz")

    # 计算高频衰减
    high_mask = freqs_orig > 200
    attenuation = np.mean(mag_filt[high_mask]) / np.mean(mag_orig[high_mask])
    print(f"高频衰减: {attenuation:.2%}")


def demo_anti_aliasing_in_sampling():
    """采样中的抗混叠演示"""
    print("\n" + "=" * 60)
    print("采样中的抗混叠演示")
    print("=" * 60)

    result = create_anti_aliasing_demo(
        f_high=200,
        f_low=30,
        fs=100,
        duration=0.1,
    )

    print(f"低频分量: {result['f_low']} Hz")
    print(f"高频分量: {result['f_high']} Hz")
    print(f"采样频率: {result['fs']} Hz")
    print(f"奈奎斯特频率: {result['fs']/2} Hz")
    print()
    print("分析:")
    print(f"  高频分量 {result['f_high']} Hz > 奈奎斯特频率 {result['fs']/2} Hz")
    print(f"  直接采样会产生混叠")
    print(f"  抗混叠滤波器先滤除高频分量")
    print(f"  然后再进行采样")


def demo_spectrum_analysis():
    """频谱分析演示"""
    print("\n" + "=" * 60)
    print("频谱分析演示")
    print("=" * 60)

    fs = 1000
    t = np.linspace(0, 1, fs, endpoint=False)

    # 多频率信号
    signal = (
        np.sin(2 * np.pi * 50 * t) +
        0.5 * np.sin(2 * np.pi * 120 * t) +
        0.3 * np.sin(2 * np.pi * 200 * t)
    )

    freqs, magnitude = compute_spectrum(signal, fs)

    print(f"采样频率: {fs} Hz")
    print(f"采样点数: {len(signal)}")
    print()
    print("频谱分析结果:")

    # 找峰值
    from scipy.signal import find_peaks
    peaks, properties = find_peaks(magnitude, height=np.max(magnitude) * 0.1)

    print("峰值频率:")
    for peak in peaks:
        print(f"  {freqs[peak]:.1f} Hz (幅度: {magnitude[peak]:.4f})")


if __name__ == "__main__":
    demo_aliasing_phenomenon()
    demo_aliasing_different_frequencies()
    demo_anti_aliasing_filter()
    demo_anti_aliasing_in_sampling()
    demo_spectrum_analysis()
