"""
傅里叶变换可视化工具

使用 matplotlib 绘制时域信号、频域信号、频谱图等。
"""

import numpy as np

try:
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from .dft import dft
from .fft import fft
from .spectrum import (
    magnitude_spectrum,
    power_spectrum,
    phase_spectrum,
    frequency_bins,
)


def _check_matplotlib():
    """检查 matplotlib 是否可用"""
    if not HAS_MATPLOTLIB:
        raise ImportError(
            "matplotlib 未安装。请运行: pip install matplotlib"
        )


def plot_time_domain(
    signal: np.ndarray,
    sample_rate: float = 1.0,
    title: str = "时域信号",
    ax=None,
):
    """
    绘制时域信号

    参数:
        signal: 时域信号
        sample_rate: 采样率
        title: 图表标题
        ax: matplotlib Axes 对象（可选）

    返回:
        matplotlib Axes 对象
    """
    _check_matplotlib()

    N = len(signal)
    t = np.arange(N) / sample_rate

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 4))

    ax.plot(t, signal.real, "b-", linewidth=1.0, label="实部")
    if np.iscomplexobj(signal):
        ax.plot(t, signal.imag, "r--", linewidth=1.0, label="虚部")
        ax.legend()

    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("幅度")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    return ax


def plot_spectrum(
    X: np.ndarray,
    sample_rate: float = 1.0,
    spectrum_type: str = "magnitude",
    one_sided: bool = True,
    log_scale: bool = False,
    title: str = None,
    ax=None,
):
    """
    绘制频谱

    参数:
        X: FFT 输出（频域信号）
        sample_rate: 采样率
        spectrum_type: 频谱类型 ('magnitude', 'power', 'phase')
        one_sided: 是否只显示正频率
        log_scale: 是否使用对数刻度
        title: 图表标题
        ax: matplotlib Axes 对象

    返回:
        matplotlib Axes 对象
    """
    _check_matplotlib()

    N = len(X)

    if one_sided:
        half = N // 2 + 1
        X_half = X[:half]
        freqs = frequency_bins(N, sample_rate)[:half]
    else:
        X_half = X
        freqs = frequency_bins(N, sample_rate)

    if spectrum_type == "magnitude":
        data = magnitude_spectrum(X_half)
        ylabel = "幅度"
        default_title = "幅度谱"
    elif spectrum_type == "power":
        data = power_spectrum(X_half)
        ylabel = "功率"
        default_title = "功率谱"
    elif spectrum_type == "phase":
        data = phase_spectrum(X_half)
        ylabel = "相位 (rad)"
        default_title = "相位谱"
    else:
        raise ValueError(f"未知频谱类型: {spectrum_type}")

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 4))

    if log_scale and spectrum_type != "phase":
        data = np.maximum(data, 1e-10)
        ax.semilogy(freqs, data, "b-", linewidth=1.0)
    else:
        ax.plot(freqs, data, "b-", linewidth=1.0)

    ax.set_xlabel("频率 (Hz)")
    ax.set_ylabel(ylabel)
    ax.set_title(title or default_title)
    ax.grid(True, alpha=0.3)

    return ax


def plot_full_analysis(
    signal: np.ndarray,
    sample_rate: float = 1.0,
    title: str = "傅里叶变换分析",
    figsize: tuple = (14, 10),
):
    """
    完整的傅里叶变换分析图

    包含: 时域信号、幅度谱、功率谱、相位谱

    参数:
        signal: 时域信号
        sample_rate: 采样率
        title: 总标题
        figsize: 图表大小

    返回:
        matplotlib Figure 对象
    """
    _check_matplotlib()

    X = fft(signal)

    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle(title, fontsize=14, fontweight="bold")

    # 时域信号
    plot_time_domain(signal, sample_rate, "时域信号", ax=axes[0, 0])

    # 幅度谱
    plot_spectrum(X, sample_rate, "magnitude", ax=axes[0, 1])

    # 功率谱 (对数)
    plot_spectrum(X, sample_rate, "power", log_scale=True, ax=axes[1, 0])

    # 相位谱
    plot_spectrum(X, sample_rate, "phase", ax=axes[1, 1])

    plt.tight_layout()
    return fig


def plot_dft_vs_fft(
    signal: np.ndarray,
    sample_rate: float = 1.0,
    title: str = "DFT vs FFT 对比",
    figsize: tuple = (14, 5),
):
    """
    对比 DFT 和 FFT 的结果

    参数:
        signal: 时域信号
        sample_rate: 采样率
        title: 图表标题
        figsize: 图表大小

    返回:
        matplotlib Figure 对象
    """
    _check_matplotlib()

    import time

    # DFT
    start = time.perf_counter()
    X_dft = dft(signal)
    dft_time = time.perf_counter() - start

    # FFT
    start = time.perf_counter()
    X_fft = fft(signal)
    fft_time = time.perf_counter() - start

    N = len(signal)
    freqs = frequency_bins(N, sample_rate)[: N // 2 + 1]

    fig, axes = plt.subplots(1, 2, figsize=figsize)
    fig.suptitle(title, fontsize=14, fontweight="bold")

    # DFT 幅度谱
    mag_dft = magnitude_spectrum(X_dft[: N // 2 + 1])
    axes[0].plot(freqs, mag_dft, "b-", linewidth=1.0)
    axes[0].set_title(f"DFT (耗时: {dft_time*1000:.2f} ms)")
    axes[0].set_xlabel("频率 (Hz)")
    axes[0].set_ylabel("幅度")
    axes[0].grid(True, alpha=0.3)

    # FFT 幅度谱
    mag_fft = magnitude_spectrum(X_fft[: N // 2 + 1])
    axes[1].plot(freqs, mag_fft, "r-", linewidth=1.0)
    axes[1].set_title(f"FFT (耗时: {fft_time*1000:.2f} ms)")
    axes[1].set_xlabel("频率 (Hz)")
    axes[1].set_ylabel("幅度")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_spectrogram(
    signal: np.ndarray,
    sample_rate: float = 1.0,
    window_size: int = 256,
    hop_size: int = 128,
    title: str = "频谱图",
    ax=None,
):
    """
    绘制频谱图 (Spectrogram)

    使用短时傅里叶变换 (STFT) 计算频谱图。

    参数:
        signal: 时域信号
        sample_rate: 采样率
        window_size: 窗口大小
        hop_size: 帧移
        title: 图表标题
        ax: matplotlib Axes 对象

    返回:
        matplotlib Axes 对象
    """
    _check_matplotlib()

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))

    N = len(signal)
    window = np.hanning(window_size)

    # 计算帧数
    n_frames = (N - window_size) // hop_size + 1
    spectrogram = np.zeros((window_size // 2 + 1, n_frames))

    for i in range(n_frames):
        start = i * hop_size
        frame = signal[start : start + window_size] * window
        X = fft(frame)
        spectrogram[:, i] = magnitude_spectrum(X[: window_size // 2 + 1])

    # 时间和频率轴
    times = np.arange(n_frames) * hop_size / sample_rate
    freqs = np.arange(window_size // 2 + 1) * sample_rate / window_size

    # 绘制
    im = ax.pcolormesh(
        times,
        freqs,
        10 * np.log10(np.maximum(spectrogram, 1e-10)),
        shading="gouraud",
        cmap="viridis",
    )
    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("频率 (Hz)")
    ax.set_title(title)
    plt.colorbar(im, ax=ax, label="功率 (dB)")

    return ax


def plot_convolution_theorem(
    x: np.ndarray,
    h: np.ndarray,
    sample_rate: float = 1.0,
    figsize: tuple = (14, 8),
):
    """
    演示卷积定理: 时域卷积 = 频域乘法

    参数:
        x: 信号 1
        h: 信号 2（卷积核）
        sample_rate: 采样率
        figsize: 图表大小

    返回:
        matplotlib Figure 对象
    """
    _check_matplotlib()

    # 时域卷积
    y_conv = np.convolve(x, h, mode="full")

    # 补零到相同长度
    N = len(y_conv)
    x_padded = np.pad(x, (0, N - len(x)))
    h_padded = np.pad(h, (0, N - len(h)))

    # 频域乘法
    X = fft(x_padded)
    H = fft(h_padded)
    Y_mult = X * H
    y_ifft = np.real(np.fft.ifft(Y_mult))

    fig, axes = plt.subplots(2, 3, figsize=figsize)
    fig.suptitle("卷积定理: 时域卷积 = 频域乘法", fontsize=14, fontweight="bold")

    # 时域信号
    t_x = np.arange(len(x)) / sample_rate
    t_h = np.arange(len(h)) / sample_rate
    t_y = np.arange(len(y_conv)) / sample_rate

    axes[0, 0].plot(t_x, x, "b-")
    axes[0, 0].set_title("信号 x[n]")
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].plot(t_h, h, "r-")
    axes[0, 1].set_title("卷积核 h[n]")
    axes[0, 1].grid(True, alpha=0.3)

    axes[0, 2].plot(t_y, y_conv, "g-")
    axes[0, 2].set_title("时域卷积 y[n] = x[n] * h[n]")
    axes[0, 2].grid(True, alpha=0.3)

    # 频域
    freqs = frequency_bins(N, sample_rate)[: N // 2 + 1]

    axes[1, 0].plot(freqs, magnitude_spectrum(X[: N // 2 + 1]), "b-")
    axes[1, 0].set_title("|X[k]|")
    axes[1, 0].grid(True, alpha=0.3)

    axes[1, 1].plot(freqs, magnitude_spectrum(H[: N // 2 + 1]), "r-")
    axes[1, 1].set_title("|H[k]|")
    axes[1, 1].grid(True, alpha=0.3)

    axes[1, 2].plot(freqs, magnitude_spectrum(Y_mult[: N // 2 + 1]), "g-")
    axes[1, 2].set_title("|Y[k]| = |X[k]| * |H[k]|")
    axes[1, 2].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig
