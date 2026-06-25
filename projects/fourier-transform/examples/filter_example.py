"""
频域滤波示例

演示如何使用 FFT 进行频域滤波（低通、高通、带通）。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.fft import fft, ifft
from src.spectrum import magnitude_spectrum, frequency_bins
from src.signals import composite_signal, white_noise


def lowpass_filter(signal, sample_rate, cutoff_freq):
    """
    低通滤波器

    保留低于截止频率的分量，去除高频分量。

    参数:
        signal: 输入信号
        sample_rate: 采样率
        cutoff_freq: 截止频率 (Hz)

    返回:
        滤波后的信号
    """
    X = fft(signal)
    N_padded = len(X)  # FFT may pad to power of 2
    freqs = frequency_bins(N_padded, sample_rate)

    # 创建滤波器: 保留低频，去除高频
    H = np.zeros(N_padded, dtype=complex)
    for i in range(N_padded):
        if abs(freqs[i]) <= cutoff_freq:
            H[i] = 1.0

    # 频域滤波
    Y = X * H
    return np.real(ifft(Y))[:len(signal)]


def highpass_filter(signal, sample_rate, cutoff_freq):
    """
    高通滤波器

    保留高于截止频率的分量，去除低频分量。
    """
    X = fft(signal)
    N_padded = len(X)
    freqs = frequency_bins(N_padded, sample_rate)

    H = np.zeros(N_padded, dtype=complex)
    for i in range(N_padded):
        if abs(freqs[i]) >= cutoff_freq:
            H[i] = 1.0

    Y = X * H
    return np.real(ifft(Y))[:len(signal)]


def bandpass_filter(signal, sample_rate, low_freq, high_freq):
    """
    带通滤波器

    保留指定频带内的分量。
    """
    X = fft(signal)
    N_padded = len(X)
    freqs = frequency_bins(N_padded, sample_rate)

    H = np.zeros(N_padded, dtype=complex)
    for i in range(N_padded):
        if low_freq <= abs(freqs[i]) <= high_freq:
            H[i] = 1.0

    Y = X * H
    return np.real(ifft(Y))[:len(signal)]


def notch_filter(signal, sample_rate, center_freq, width=5.0):
    """
    陷波滤波器 (Notch Filter)

    去除指定频率及其附近的分量。
    """
    X = fft(signal)
    N_padded = len(X)
    freqs = frequency_bins(N_padded, sample_rate)

    H = np.ones(N_padded, dtype=complex)
    for i in range(N_padded):
        if abs(abs(freqs[i]) - center_freq) <= width:
            H[i] = 0.0

    Y = X * H
    return np.real(ifft(Y))[:len(signal)]


def print_signal_stats(signal, name):
    """打印信号统计信息"""
    print(f"  {name}: 均值={np.mean(signal):.4f}, 标准差={np.std(signal):.4f}, "
          f"范围=[{np.min(signal):.4f}, {np.max(signal):.4f}]")


def example_lowpass():
    """低通滤波示例"""
    print("=" * 60)
    print("低通滤波示例")
    print("=" * 60)

    sample_rate = 1000.0

    # 信号: 低频 (10 Hz) + 高频 (200 Hz)
    signal = composite_signal([10, 200], [1.0, 0.5], sample_rate, 1.0)
    print(f"\n原始信号: 10 Hz (幅度 1.0) + 200 Hz (幅度 0.5)")
    print_signal_stats(signal, "原始")

    # 低通滤波，截止 50 Hz
    filtered = lowpass_filter(signal, sample_rate, cutoff_freq=50.0)
    print(f"\n低通滤波 (截止 50 Hz):")
    print_signal_stats(filtered, "滤波后")

    # 验证: 高频分量应被去除
    X_orig = fft(signal)
    X_filt = fft(filtered)
    mag_orig = magnitude_spectrum(X_orig[:len(X_orig)//2])
    mag_filt = magnitude_spectrum(X_filt[:len(X_filt)//2])
    freqs = frequency_bins(len(signal), sample_rate)[:len(X_orig)//2]

    idx_10 = np.argmin(np.abs(freqs - 10))
    idx_200 = np.argmin(np.abs(freqs - 200))

    print(f"\n  10 Hz 分量: 原始={mag_orig[idx_10]:.2f}, 滤波后={mag_filt[idx_10]:.2f} (应保留)")
    print(f"  200 Hz 分量: 原始={mag_orig[idx_200]:.2f}, 滤波后={mag_filt[idx_200]:.2f} (应去除)")


def example_highpass():
    """高通滤波示例"""
    print("\n" + "=" * 60)
    print("高通滤波示例")
    print("=" * 60)

    sample_rate = 1000.0
    signal = composite_signal([10, 200], [1.0, 0.5], sample_rate, 1.0)
    print(f"\n原始信号: 10 Hz (幅度 1.0) + 200 Hz (幅度 0.5)")

    filtered = highpass_filter(signal, sample_rate, cutoff_freq=100.0)
    print(f"高通滤波 (截止 100 Hz):")
    print_signal_stats(filtered, "滤波后")


def example_bandpass():
    """带通滤波示例"""
    print("\n" + "=" * 60)
    print("带通滤波示例")
    print("=" * 60)

    sample_rate = 1000.0
    signal = composite_signal(
        [10, 100, 300, 450], [1.0, 1.0, 1.0, 1.0], sample_rate, 1.0
    )
    print(f"\n原始信号: 10, 100, 300, 450 Hz")

    # 带通: 只保留 50-200 Hz
    filtered = bandpass_filter(signal, sample_rate, low_freq=50.0, high_freq=200.0)
    print(f"带通滤波 (50-200 Hz):")
    print_signal_stats(filtered, "滤波后")

    X = fft(filtered)
    mag = magnitude_spectrum(X[:len(X)//2])
    freqs = frequency_bins(len(signal), sample_rate)[:len(X)//2]

    for target in [10, 100, 300, 450]:
        idx = np.argmin(np.abs(freqs - target))
        print(f"  {target} Hz: 幅度={mag[idx]:.2f}")


def example_noise_removal():
    """噪声去除示例"""
    print("\n" + "=" * 60)
    print("噪声去除示例")
    print("=" * 60)

    sample_rate = 1000.0
    np.random.seed(42)

    # 干净信号 + 噪声
    clean = composite_signal([50, 150], [1.0, 0.5], sample_rate, 1.0)
    noise = white_noise(sample_rate, 1.0, amplitude=0.5)
    noisy = clean + noise

    print(f"\n干净信号: 50 Hz + 150 Hz")
    print(f"添加噪声 (幅度 0.5)")
    print_signal_stats(noisy, "含噪信号")

    # 低通滤波去噪 (信号在 200 Hz 以下)
    denoised = lowpass_filter(noisy, sample_rate, cutoff_freq=200.0)
    print(f"\n低通滤波后:")
    print_signal_stats(denoised, "去噪信号")

    # 计算 SNR 改善
    snr_before = 10 * np.log10(np.sum(clean**2) / np.sum((noisy - clean)**2))
    snr_after = 10 * np.log10(np.sum(clean**2) / np.sum((denoised - clean)**2))
    print(f"\n  滤波前 SNR: {snr_before:.1f} dB")
    print(f"  滤波后 SNR: {snr_after:.1f} dB")
    print(f"  SNR 改善: {snr_after - snr_before:.1f} dB")


def example_notch_filter():
    """陷波滤波示例"""
    print("\n" + "=" * 60)
    print("陷波滤波示例 (去除工频干扰)")
    print("=" * 60)

    sample_rate = 1000.0

    # 信号 + 50 Hz 工频干扰
    signal = composite_signal([20, 80], [1.0, 0.5], sample_rate, 1.0)
    interference = 0.3 * np.sin(2 * np.pi * 50 * np.arange(int(sample_rate)) / sample_rate)
    corrupted = signal + interference

    print(f"\n有用信号: 20 Hz + 80 Hz")
    print(f"干扰: 50 Hz (幅度 0.3)")

    # 陷波滤波去除 50 Hz
    filtered = notch_filter(corrupted, sample_rate, center_freq=50.0, width=3.0)
    print(f"陷波滤波 (中心 50 Hz, 带宽 6 Hz):")
    print_signal_stats(filtered, "滤波后")


if __name__ == "__main__":
    example_lowpass()
    example_highpass()
    example_bandpass()
    example_noise_removal()
    example_notch_filter()
    print("\n所有滤波示例运行完成!")
