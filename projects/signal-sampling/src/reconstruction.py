"""
信号重建实现
=============

实现零阶保持、一阶保持和理想重建 (sinc 插值)。

核心原理:
- 零阶保持 (ZOH): 每个采样值保持到下一个采样点
- 一阶保持 (FOH): 采样点之间线性插值
- 理想重建: sinc 插值，完美重建带限信号

重建公式:
- ZOH: x(t) = x[n], nTs <= t < (n+1)Ts
- FOH: x(t) = x[n] + (x[n+1]-x[n])*(t-nTs)/Ts
- sinc: x(t) = sum(x[n] * sinc((t-nTs)/Ts))
"""

import numpy as np
from typing import Tuple, Optional


def zero_order_hold(
    t_sampled: np.ndarray,
    samples: np.ndarray,
    t_continuous: np.ndarray,
) -> np.ndarray:
    """零阶保持重建

    每个采样值保持到下一个采样点，产生阶梯状波形。

    Parameters
    ----------
    t_sampled : np.ndarray
        采样时间点
    samples : np.ndarray
        采样值
    t_continuous : np.ndarray
        重建的时间轴

    Returns
    -------
    np.ndarray
        重建的信号
    """
    if len(t_sampled) != len(samples):
        raise ValueError("采样时间和采样值长度必须一致")

    result = np.zeros_like(t_continuous)
    fs = 1.0 / (t_sampled[1] - t_sampled[0]) if len(t_sampled) > 1 else 1.0

    for i, t in enumerate(t_continuous):
        # 找到最近的采样点 (向下取整)
        idx = int(t * fs)
        idx = np.clip(idx, 0, len(samples) - 1)
        result[i] = samples[idx]

    return result


def first_order_hold(
    t_sampled: np.ndarray,
    samples: np.ndarray,
    t_continuous: np.ndarray,
) -> np.ndarray:
    """一阶保持重建

    采样点之间线性插值，产生折线波形。

    Parameters
    ----------
    t_sampled : np.ndarray
        采样时间点
    samples : np.ndarray
        采样值
    t_continuous : np.ndarray
        重建的时间轴

    Returns
    -------
    np.ndarray
        重建的信号
    """
    if len(t_sampled) != len(samples):
        raise ValueError("采样时间和采样值长度必须一致")

    result = np.interp(t_continuous, t_sampled, samples)
    return result


def sinc_interpolation(
    t_sampled: np.ndarray,
    samples: np.ndarray,
    t_continuous: np.ndarray,
    fs: Optional[float] = None,
) -> np.ndarray:
    """sinc 插值重建 (理想重建)

    使用 sinc 函数进行理想重建，理论上可以完美重建带限信号。

    重建公式: x(t) = sum(x[n] * sinc(pi*(t-nTs)/(Ts)))

    Parameters
    ----------
    t_sampled : np.ndarray
        采样时间点
    samples : np.ndarray
        采样值
    t_continuous : np.ndarray
        重建的时间轴
    fs : float, optional
        采样频率，如果不提供则从采样时间推算

    Returns
    -------
    np.ndarray
        重建的信号
    """
    if len(t_sampled) != len(samples):
        raise ValueError("采样时间和采样值长度必须一致")

    if fs is None:
        fs = 1.0 / (t_sampled[1] - t_sampled[0])

    Ts = 1.0 / fs
    result = np.zeros_like(t_continuous)

    for i, t in enumerate(t_continuous):
        # sinc 插值
        sinc_vals = np.sinc((t - t_sampled) / Ts)
        result[i] = np.sum(samples * sinc_vals)

    return result


def reconstruct_signal(
    t_sampled: np.ndarray,
    samples: np.ndarray,
    t_continuous: np.ndarray,
    method: str = 'sinc',
    fs: Optional[float] = None,
) -> np.ndarray:
    """信号重建 (统一接口)

    Parameters
    ----------
    t_sampled : np.ndarray
        采样时间点
    samples : np.ndarray
        采样值
    t_continuous : np.ndarray
        重建的时间轴
    method : str
        重建方法: 'zoh', 'foh', 'sinc'
    fs : float, optional
        采样频率

    Returns
    -------
    np.ndarray
        重建的信号

    Examples
    --------
    >>> t_sampled = np.array([0, 0.1, 0.2, 0.3])
    >>> samples = np.array([0, 0.5, 1.0, 0.5])
    >>> t_continuous = np.linspace(0, 0.3, 100)
    >>> reconstructed = reconstruct_signal(t_sampled, samples, t_continuous, method='sinc')
    """
    methods = {
        'zoh': zero_order_hold,
        'foh': first_order_hold,
        'sinc': sinc_interpolation,
    }

    if method not in methods:
        raise ValueError(f"不支持的重建方法: {method}，可选: {list(methods.keys())}")

    if method == 'sinc':
        return sinc_interpolation(t_sampled, samples, t_continuous, fs)
    else:
        return methods[method](t_sampled, samples, t_continuous)


def compare_reconstruction(
    t_sampled: np.ndarray,
    samples: np.ndarray,
    t_continuous: np.ndarray,
    signal_original: np.ndarray,
    fs: Optional[float] = None,
) -> dict:
    """比较不同重建方法的效果

    Parameters
    ----------
    t_sampled : np.ndarray
        采样时间点
    samples : np.ndarray
        采样值
    t_continuous : np.ndarray
        重建的时间轴
    signal_original : np.ndarray
        原始信号
    fs : float, optional
        采样频率

    Returns
    -------
    dict
        各方法的重建结果和误差
    """
    results = {}

    for method in ['zoh', 'foh', 'sinc']:
        reconstructed = reconstruct_signal(
            t_sampled, samples, t_continuous, method, fs
        )
        mse = np.mean((signal_original - reconstructed) ** 2)
        max_error = np.max(np.abs(signal_original - reconstructed))

        results[method] = {
            'signal': reconstructed,
            'mse': mse,
            'max_error': max_error,
            'snr_db': 10 * np.log10(
                np.mean(signal_original ** 2) / mse if mse > 0 else float('inf')
            ),
        }

    return results


def sinc_pulse(Ts: float, t: np.ndarray) -> np.ndarray:
    """生成 sinc 脉冲

    sinc(t/Ts) = sin(pi*t/Ts) / (pi*t/Ts)

    Parameters
    ----------
    Ts : float
        采样周期
    t : np.ndarray
        时间数组

    Returns
    -------
    np.ndarray
        sinc 脉冲
    """
    return np.sinc(t / Ts)


def ideal_lowpass_reconstruction(
    samples: np.ndarray,
    fs: float,
    t_continuous: np.ndarray,
    cutoff_ratio: float = 1.0,
) -> np.ndarray:
    """理想低通滤波重建

    在频域进行理想低通滤波，然后逆变换回时域。

    Parameters
    ----------
    samples : np.ndarray
        采样值
    fs : float
        采样频率
    t_continuous : np.ndarray
        重建的时间轴
    cutoff_ratio : float
        截止频率比例 (相对于奈奎斯特频率)

    Returns
    -------
    np.ndarray
        重建的信号
    """
    n = len(samples)

    # FFT
    spectrum = np.fft.fft(samples)
    freqs = np.fft.fftfreq(n, 1.0 / fs)

    # 理想低通滤波
    nyquist = fs / 2
    cutoff = cutoff_ratio * nyquist
    mask = np.abs(freqs) <= cutoff
    filtered_spectrum = spectrum * mask

    # 补零到目标长度
    n_target = len(t_continuous)
    if n_target > n:
        padded_spectrum = np.zeros(n_target, dtype=complex)
        half_n = n // 2
        padded_spectrum[:half_n] = filtered_spectrum[:half_n]
        padded_spectrum[-(n - half_n):] = filtered_spectrum[half_n:]
        filtered_spectrum = padded_spectrum

    # IFFT
    reconstructed = np.fft.ifft(filtered_spectrum).real

    return reconstructed[:len(t_continuous)]
