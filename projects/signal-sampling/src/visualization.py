"""
信号采样重建可视化工具
========================

提供采样、量化、重建、混叠等过程的可视化。
"""

import numpy as np
from typing import Optional, List, Tuple, Dict


def plot_sampling(
    t_continuous: np.ndarray,
    signal: np.ndarray,
    t_sampled: np.ndarray,
    samples: np.ndarray,
    title: str = "信号采样",
    save_path: Optional[str] = None,
) -> None:
    """绘制采样过程

    Parameters
    ----------
    t_continuous : np.ndarray
        连续时间轴
    signal : np.ndarray
        连续信号
    t_sampled : np.ndarray
        采样时间点
    samples : np.ndarray
        采样值
    title : str
        图标题
    save_path : str, optional
        保存路径
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib 未安装，跳过绘图")
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(t_continuous, signal, 'b-', linewidth=1.5, label='原始信号')
    ax.stem(t_sampled, samples, linefmt='r-', markerfmt='ro', basefmt='k-',
            label='采样点')
    ax.plot(t_sampled, samples, 'ro', markersize=6)

    ax.set_xlabel('时间 (s)')
    ax.set_ylabel('幅度')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(t_continuous[0], t_continuous[-1])

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_quantization(
    signal: np.ndarray,
    quantized: np.ndarray,
    bits: int,
    title: str = "信号量化",
    save_path: Optional[str] = None,
) -> None:
    """绘制量化过程

    Parameters
    ----------
    signal : np.ndarray
        原始信号
    quantized : np.ndarray
        量化后的信号
    bits : int
        量化位数
    title : str
        图标题
    save_path : str, optional
        保存路径
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib 未安装，跳过绘图")
        return

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    # 信号对比
    t = np.arange(len(signal))
    axes[0].plot(t, signal, 'b-', linewidth=1.5, label='原始信号')
    axes[0].plot(t, quantized, 'r-', linewidth=1.0, label=f'量化信号 ({bits} bit)')
    axes[0].set_xlabel('样本')
    axes[0].set_ylabel('幅度')
    axes[0].set_title(title)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # 量化误差
    error = signal - quantized
    axes[1].plot(t, error, 'g-', linewidth=1.0)
    axes[1].set_xlabel('样本')
    axes[1].set_ylabel('误差')
    axes[1].set_title('量化误差')
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_reconstruction(
    t_sampled: np.ndarray,
    samples: np.ndarray,
    t_continuous: np.ndarray,
    reconstructed_dict: Dict[str, np.ndarray],
    original: Optional[np.ndarray] = None,
    title: str = "信号重建",
    save_path: Optional[str] = None,
) -> None:
    """绘制重建结果对比

    Parameters
    ----------
    t_sampled : np.ndarray
        采样时间点
    samples : np.ndarray
        采样值
    t_continuous : np.ndarray
        连续时间轴
    reconstructed_dict : Dict[str, np.ndarray]
        各方法的重建结果
    original : np.ndarray, optional
        原始信号
    title : str
        图标题
    save_path : str, optional
        保存路径
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib 未安装，跳过绘图")
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    if original is not None:
        ax.plot(t_continuous, original, 'k--', linewidth=2, alpha=0.5, label='原始信号')

    ax.plot(t_sampled, samples, 'ko', markersize=8, label='采样点')

    colors = ['r', 'g', 'b', 'm']
    for i, (method, signal) in enumerate(reconstructed_dict.items()):
        color = colors[i % len(colors)]
        ax.plot(t_continuous, signal, color=color, linewidth=1.5, label=method)

    ax.set_xlabel('时间 (s)')
    ax.set_ylabel('幅度')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_aliasing(
    demo_result: dict,
    title: str = "混叠现象",
    save_path: Optional[str] = None,
) -> None:
    """绘制混叠现象

    Parameters
    ----------
    demo_result : dict
        demonstrate_aliasing 的返回结果
    title : str
        图标题
    save_path : str, optional
        保存路径
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib 未安装，跳过绘图")
        return

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    t_continuous = demo_result["t_continuous"]
    signal_continuous = demo_result["signal_continuous"]
    t_sampled = demo_result["t_sampled"]
    samples = demo_result["samples"]
    alias_signal = demo_result["alias_signal"]
    f_signal = demo_result["f_signal"]
    fs = demo_result["fs"]
    alias_freq = demo_result["alias_freq"]

    # 原始信号和采样点
    axes[0].plot(t_continuous, signal_continuous, 'b-', linewidth=1.5,
                 label=f'原始信号 ({f_signal} Hz)')
    axes[0].stem(t_sampled, samples, linefmt='r-', markerfmt='ro', basefmt='k-',
                 label=f'采样 (fs={fs} Hz)')
    axes[0].set_xlabel('时间 (s)')
    axes[0].set_ylabel('幅度')
    axes[0].set_title(f'{title} - 原始信号和采样')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # 混叠信号
    axes[1].plot(t_continuous, signal_continuous, 'b-', linewidth=1.5, alpha=0.5,
                 label=f'原始信号 ({f_signal} Hz)')
    axes[1].plot(t_continuous, alias_signal, 'r-', linewidth=1.5,
                 label=f'混叠信号 ({alias_freq:.1f} Hz)')
    axes[1].stem(t_sampled, samples, linefmt='g-', markerfmt='go', basefmt='k-',
                 label='采样点')
    axes[1].set_xlabel('时间 (s)')
    axes[1].set_ylabel('幅度')
    axes[1].set_title(f'{title} - 混叠效果')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_spectrum(
    signal: np.ndarray,
    fs: float,
    title: str = "信号频谱",
    save_path: Optional[str] = None,
) -> None:
    """绘制信号频谱

    Parameters
    ----------
    signal : np.ndarray
        输入信号
    fs : float
        采样频率
    title : str
        图标题
    save_path : str, optional
        保存路径
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib 未安装，跳过绘图")
        return

    n = len(signal)
    spectrum = np.fft.fft(signal)
    freqs = np.fft.fftfreq(n, 1.0 / fs)
    magnitude = np.abs(spectrum) / n * 2

    positive_mask = freqs >= 0

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(freqs[positive_mask], magnitude[positive_mask], 'b-', linewidth=1.5)
    ax.set_xlabel('频率 (Hz)')
    ax.set_ylabel('幅度')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_audio_quantization_comparison(
    demo_result: dict,
    save_path: Optional[str] = None,
) -> None:
    """绘制音频量化对比

    Parameters
    ----------
    demo_result : dict
        demonstrate_audio_quantization 的返回结果
    save_path : str, optional
        保存路径
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib 未安装，跳过绘图")
        return

    t = demo_result["t"]
    signal = demo_result["signal"]
    results = demo_result["quantization_results"]

    n_plots = len(results) + 1
    fig, axes = plt.subplots(n_plots, 1, figsize=(12, 3 * n_plots))

    # 原始信号
    axes[0].plot(t[:1000], signal[:1000], 'b-', linewidth=1.5)
    axes[0].set_title('原始信号')
    axes[0].grid(True, alpha=0.3)

    # 各量化位数
    for i, (key, data) in enumerate(results.items()):
        axes[i + 1].plot(t[:1000], data["quantized"][:1000], 'r-', linewidth=1.0)
        axes[i + 1].set_title(f'{key} 量化 (SQNR={data["sqnr"]:.1f} dB)')
        axes[i + 1].grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
