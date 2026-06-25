"""
可视化示例

演示如何使用 matplotlib 可视化傅里叶变换结果。
如果 matplotlib 不可用，会输出提示信息。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.signals import (
    sine_wave,
    composite_signal,
    square_wave,
    sawtooth_wave,
    chirp_signal,
)
from src.fft import fft, ifft
from src.spectrum import magnitude_spectrum, frequency_bins


def check_matplotlib():
    """检查 matplotlib 是否可用"""
    try:
        import matplotlib.pyplot as plt
        return True
    except ImportError:
        print("matplotlib 未安装，跳过可视化示例。")
        print("安装命令: pip install matplotlib")
        return False


def example_basic_plots():
    """基础绘图示例"""
    if not check_matplotlib():
        return

    import matplotlib.pyplot as plt

    sample_rate = 1000.0
    duration = 0.1

    # 创建信号
    signal = composite_signal(
        [50, 150, 300], [1.0, 0.5, 0.25], sample_rate, duration
    )
    X = fft(signal)

    N = len(signal)
    t = np.arange(N) / sample_rate
    freqs = frequency_bins(N, sample_rate)[:N//2]
    mag = magnitude_spectrum(X[:N//2])

    fig, axes = plt.subplots(2, 1, figsize=(12, 6))

    # 时域
    axes[0].plot(t, signal, "b-", linewidth=0.8)
    axes[0].set_xlabel("时间 (s)")
    axes[0].set_ylabel("幅度")
    axes[0].set_title("时域信号: 50 Hz + 150 Hz + 300 Hz")
    axes[0].grid(True, alpha=0.3)

    # 频域
    axes[1].plot(freqs, mag, "r-", linewidth=0.8)
    axes[1].set_xlabel("频率 (Hz)")
    axes[1].set_ylabel("幅度")
    axes[1].set_title("幅度谱")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("/tmp/fourier_basic.png", dpi=100)
    print("已保存: /tmp/fourier_basic.png")
    plt.close()


def example_waveform_comparison():
    """波形对比示例"""
    if not check_matplotlib():
        return

    import matplotlib.pyplot as plt

    sample_rate = 1000.0
    duration = 0.05
    freq = 50

    signals = {
        "正弦波": sine_wave(freq, sample_rate, duration),
        "方波": square_wave(freq, sample_rate, duration),
        "锯齿波": sawtooth_wave(freq, sample_rate, duration),
    }

    fig, axes = plt.subplots(len(signals), 2, figsize=(14, 8))

    for i, (name, sig) in enumerate(signals.items()):
        N = len(sig)
        t = np.arange(N) / sample_rate
        X = fft(sig)
        freqs = frequency_bins(N, sample_rate)[:N//2]
        mag = magnitude_spectrum(X[:N//2])

        axes[i, 0].plot(t, sig, "b-", linewidth=0.8)
        axes[i, 0].set_ylabel(name)
        axes[i, 0].grid(True, alpha=0.3)
        if i == 0:
            axes[i, 0].set_title("时域")

        axes[i, 1].plot(freqs, mag, "r-", linewidth=0.8)
        axes[i, 1].set_ylabel(name)
        axes[i, 1].grid(True, alpha=0.3)
        if i == 0:
            axes[i, 1].set_title("频域")

    axes[-1, 0].set_xlabel("时间 (s)")
    axes[-1, 1].set_xlabel("频率 (Hz)")

    plt.tight_layout()
    plt.savefig("/tmp/fourier_waveforms.png", dpi=100)
    print("已保存: /tmp/fourier_waveforms.png")
    plt.close()


def example_spectrogram():
    """频谱图示例"""
    if not check_matplotlib():
        return

    import matplotlib.pyplot as plt
    from src.visualization import plot_spectrogram

    sample_rate = 1000.0
    duration = 2.0

    # Chirp 信号 (频率随时间变化)
    signal = chirp_signal(10, 200, sample_rate, duration)

    fig, ax = plt.subplots(figsize=(12, 6))
    plot_spectrogram(signal, sample_rate, window_size=128, hop_size=32, ax=ax)
    ax.set_title("Chirp 信号频谱图 (10 Hz -> 200 Hz)")

    plt.tight_layout()
    plt.savefig("/tmp/fourier_spectrogram.png", dpi=100)
    print("已保存: /tmp/fourier_spectrogram.png")
    plt.close()


def example_full_analysis():
    """完整分析示例"""
    if not check_matplotlib():
        return

    from src.visualization import plot_full_analysis

    sample_rate = 1000.0
    signal = composite_signal(
        [50, 120, 300], [1.0, 0.6, 0.3], sample_rate, 0.5
    )

    fig = plot_full_analysis(
        signal, sample_rate, title="复合信号傅里叶变换分析"
    )
    fig.savefig("/tmp/fourier_analysis.png", dpi=100)
    print("已保存: /tmp/fourier_analysis.png")

    import matplotlib.pyplot as plt
    plt.close()


if __name__ == "__main__":
    example_basic_plots()
    example_waveform_comparison()
    example_spectrogram()
    example_full_analysis()
    print("\n可视化示例运行完成!")
