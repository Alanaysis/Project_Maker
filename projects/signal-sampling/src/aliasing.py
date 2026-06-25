"""
混叠与抗混叠滤波实现
======================

实现混叠现象演示和抗混叠滤波。

核心原理:
- 混叠: 当采样率不足时，高频分量会伪装成低频分量
- 混叠频率: f_alias = |f - k * fs|, k = round(f/fs)
- 抗混叠滤波: 在采样前使用低通滤波器限制信号带宽

奈奎斯特定理:
- 采样率 fs >= 2 * fmax 时，可以完美重建信号
- 采样率 fs < 2 * fmax 时，产生混叠
"""

import numpy as np
from typing import Tuple, Optional


def demonstrate_aliasing(
    f_signal: float,
    fs: float,
    duration: float = 1.0,
) -> dict:
    """演示混叠现象

    将高频信号以低采样率采样，展示混叠效果。

    Parameters
    ----------
    f_signal : float
        信号频率 (Hz)
    fs : float
        采样频率 (Hz)
    duration : float
        采样持续时间 (秒)

    Returns
    -------
    dict
        包含原始信号、采样点、混叠频率等信息
    """
    if fs <= 0:
        raise ValueError("采样频率必须为正数")

    # 连续时间轴 (高分辨率)
    t_continuous = np.linspace(0, duration, 10000)
    signal_continuous = np.sin(2 * np.pi * f_signal * t_continuous)

    # 采样
    n_samples = int(fs * duration)
    t_sampled = np.arange(n_samples) / fs
    samples = np.sin(2 * np.pi * f_signal * t_sampled)

    # 计算混叠频率
    alias_freq = _calculate_alias_frequency(f_signal, fs)

    # 混叠后的信号
    alias_signal = np.sin(2 * np.pi * alias_freq * t_continuous)

    return {
        "t_continuous": t_continuous,
        "signal_continuous": signal_continuous,
        "t_sampled": t_sampled,
        "samples": samples,
        "alias_freq": alias_freq,
        "alias_signal": alias_signal,
        "f_signal": f_signal,
        "fs": fs,
    }


def anti_aliasing_filter(
    signal: np.ndarray,
    fs: float,
    cutoff_freq: float,
    filter_order: int = 4,
) -> np.ndarray:
    """抗混叠低通滤波器

    使用巴特沃斯低通滤波器进行抗混叠滤波。

    Parameters
    ----------
    signal : np.ndarray
        输入信号
    fs : float
        采样频率 (Hz)
    cutoff_freq : float
        截止频率 (Hz)
    filter_order : int
        滤波器阶数

    Returns
    -------
    np.ndarray
        滤波后的信号
    """
    if cutoff_freq >= fs / 2:
        raise ValueError(
            f"截止频率 {cutoff_freq} Hz 必须小于奈奎斯特频率 {fs/2} Hz"
        )

    # 设计巴特沃斯滤波器
    from scipy.signal import butter, filtfilt

    nyquist = fs / 2
    normalized_cutoff = cutoff_freq / nyquist

    # 确保归一化截止频率在有效范围内
    normalized_cutoff = min(normalized_cutoff, 0.99)
    normalized_cutoff = max(normalized_cutoff, 0.01)

    b, a = butter(filter_order, normalized_cutoff, btype='low')

    # 零相位滤波
    filtered = filtfilt(b, a, signal)

    return filtered


def compute_spectrum(
    signal: np.ndarray,
    fs: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """计算信号频谱

    Parameters
    ----------
    signal : np.ndarray
        输入信号
    fs : float
        采样频率 (Hz)

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        (频率数组, 幅度谱)
    """
    n = len(signal)

    # FFT
    spectrum = np.fft.fft(signal)
    freqs = np.fft.fftfreq(n, 1.0 / fs)

    # 取正频率部分
    positive_mask = freqs >= 0
    freqs = freqs[positive_mask]
    magnitude = np.abs(spectrum[positive_mask]) / n * 2

    return freqs, magnitude


def show_aliasing_effect(
    f_signal: float,
    fs_list: list,
    duration: float = 0.01,
) -> dict:
    """展示不同采样率下的混叠效果

    Parameters
    ----------
    f_signal : float
        信号频率 (Hz)
    fs_list : list
        采样频率列表
    duration : float
        采样持续时间 (秒)

    Returns
    -------
    dict
        各采样率下的采样结果
    """
    results = {}

    # 高分辨率原始信号
    t_ref = np.linspace(0, duration, 10000)
    signal_ref = np.sin(2 * np.pi * f_signal * t_ref)
    results["reference"] = {
        "t": t_ref,
        "signal": signal_ref,
        "label": f"原始信号 ({f_signal} Hz)",
    }

    for fs in fs_list:
        n_samples = int(fs * duration)
        if n_samples < 2:
            continue

        t_sampled = np.arange(n_samples) / fs
        samples = np.sin(2 * np.pi * f_signal * t_sampled)
        alias_freq = _calculate_alias_frequency(f_signal, fs)

        is_aliasing = fs < 2 * f_signal

        results[f"fs={fs}"] = {
            "t": t_sampled,
            "signal": samples,
            "alias_freq": alias_freq,
            "is_aliasing": is_aliasing,
            "label": f"fs={fs} Hz (混叠={alias_freq:.1f} Hz)" if is_aliasing else f"fs={fs} Hz",
        }

    return results


def _calculate_alias_frequency(f_signal: float, fs: float) -> float:
    """计算混叠频率

    Parameters
    ----------
    f_signal : float
        原始信号频率
    fs : float
        采样频率

    Returns
    -------
    float
        混叠后的频率
    """
    k = round(f_signal / fs)
    alias = abs(f_signal - k * fs)
    return alias


def create_anti_aliasing_demo(
    f_high: float,
    f_low: float,
    fs: float,
    duration: float = 0.1,
) -> dict:
    """创建抗混叠滤波演示

    Parameters
    ----------
    f_high : float
        高频分量频率 (Hz)
    f_low : float
        低频分量频率 (Hz)
    fs : float
        采样频率 (Hz)
    duration : float
        采样持续时间 (秒)

    Returns
    -------
    dict
        演示结果
    """
    # 连续时间轴
    t_continuous = np.linspace(0, duration, 10000)

    # 混合信号 (低频 + 高频)
    signal_mixed = (
        np.sin(2 * np.pi * f_low * t_continuous) +
        0.5 * np.sin(2 * np.pi * f_high * t_continuous)
    )

    # 直接采样 (会产生混叠)
    n_samples = int(fs * duration)
    t_sampled = np.arange(n_samples) / fs
    samples_direct = (
        np.sin(2 * np.pi * f_low * t_sampled) +
        0.5 * np.sin(2 * np.pi * f_high * t_sampled)
    )

    # 抗混叠滤波后采样
    filtered_signal = anti_aliasing_filter(
        signal_mixed,
        fs=10000,  # 使用高采样率模拟连续信号
        cutoff_freq=fs / 2,
    )

    # 对滤波后的信号采样
    samples_filtered = np.interp(t_sampled, t_continuous, filtered_signal)

    return {
        "t_continuous": t_continuous,
        "signal_mixed": signal_mixed,
        "t_sampled": t_sampled,
        "samples_direct": samples_direct,
        "samples_filtered": samples_filtered,
        "filtered_signal": filtered_signal,
        "f_high": f_high,
        "f_low": f_low,
        "fs": fs,
    }
