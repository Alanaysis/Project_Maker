"""
信号采样实现
=============

实现奈奎斯特定理、过采样和欠采样。

核心原理:
- 奈奎斯特定理: 采样率 >= 2 * 最高频率分量
- 过采样: 采样率 >> 奈奎斯特率，降低混叠风险
- 欠采样: 采样率 < 奈奎斯特率，产生混叠

数学基础:
- 采样: x[n] = x(n * Ts), Ts = 1/fs
- 奈奎斯特率: fs_min = 2 * fmax
- 混叠频率: f_alias = |f - k * fs|, k 为整数
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class SamplingConfig:
    """采样配置

    Parameters
    ----------
    fs : float
        采样频率 (Hz)
    duration : float
        采样持续时间 (秒)
    f_signal : float
        信号频率 (Hz)
    """
    fs: float
    duration: float
    f_signal: float

    @property
    def nyquist_rate(self) -> float:
        """奈奎斯特率"""
        return 2.0 * self.f_signal

    @property
    def oversampling_ratio(self) -> float:
        """过采样率"""
        return self.fs / self.nyquist_rate

    @property
    def is_nyquist_satisfied(self) -> bool:
        """是否满足奈奎斯特定理"""
        return self.fs >= self.nyquist_rate


def calculate_nyquist_rate(fmax: float) -> float:
    """计算奈奎斯特率

    Parameters
    ----------
    fmax : float
        信号最高频率分量 (Hz)

    Returns
    -------
    float
        奈奎斯特率 (Hz)

    Examples
    --------
    >>> calculate_nyquist_rate(1000)
    2000.0
    """
    if fmax <= 0:
        raise ValueError("最高频率必须为正数")
    return 2.0 * fmax


def nyquist_sample(
    signal_func,
    f_signal: float,
    fs: float,
    duration: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """奈奎斯特采样

    以奈奎斯特率进行采样，理论上可以完美重建信号。

    Parameters
    ----------
    signal_func : callable
        信号函数，接受时间数组作为参数
    f_signal : float
        信号频率 (Hz)
    fs : float
        采样频率 (Hz)
    duration : float
        采样持续时间 (秒)

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        (采样时间点, 采样值)
    """
    if fs < 2 * f_signal:
        raise ValueError(
            f"采样率 {fs} Hz 低于奈奎斯特率 {2*f_signal} Hz，会产生混叠"
        )

    n_samples = int(fs * duration)
    t_sampled = np.arange(n_samples) / fs
    samples = signal_func(t_sampled)

    return t_sampled, samples


def oversample(
    signal_func,
    f_signal: float,
    oversampling_factor: int,
    duration: float,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """过采样

    以远高于奈奎斯特率的频率进行采样，降低混叠风险。

    Parameters
    ----------
    signal_func : callable
        信号函数
    f_signal : float
        信号频率 (Hz)
    oversampling_factor : int
        过采样倍数 (相对于奈奎斯特率)
    duration : float
        采样持续时间 (秒)

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, float]
        (采样时间点, 采样值, 采样频率)
    """
    if oversampling_factor < 1:
        raise ValueError("过采样倍数必须 >= 1")

    fs = 2 * f_signal * oversampling_factor
    n_samples = int(fs * duration)
    t_sampled = np.arange(n_samples) / fs
    samples = signal_func(t_sampled)

    return t_sampled, samples, fs


def undersample(
    signal_func,
    f_signal: float,
    fs: float,
    duration: float,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """欠采样

    以低于奈奎斯特率的频率进行采样，会产生混叠。

    Parameters
    ----------
    signal_func : callable
        信号函数
    f_signal : float
        信号频率 (Hz)
    fs : float
        采样频率 (Hz)
    duration : float
        采样持续时间 (秒)

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, float]
        (采样时间点, 采样值, 混叠频率)
    """
    if fs >= 2 * f_signal:
        raise ValueError(
            f"采样率 {fs} Hz >= 奈奎斯特率 {2*f_signal} Hz，不是欠采样"
        )

    n_samples = int(fs * duration)
    t_sampled = np.arange(n_samples) / fs
    samples = signal_func(t_sampled)

    # 计算混叠频率
    alias_freq = _calculate_alias_frequency(f_signal, fs)

    return t_sampled, samples, alias_freq


def sample_signal(
    t_continuous: np.ndarray,
    signal: np.ndarray,
    fs: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """对连续信号进行采样

    Parameters
    ----------
    t_continuous : np.ndarray
        连续时间轴
    signal : np.ndarray
        连续信号值
    fs : float
        采样频率 (Hz)

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        (采样时间点, 采样值)
    """
    dt = t_continuous[1] - t_continuous[0]
    step = max(1, int(1.0 / (fs * dt)))

    t_sampled = t_continuous[::step]
    samples = signal[::step]

    return t_sampled, samples


def _calculate_alias_frequency(f_signal: float, fs: float) -> float:
    """计算混叠频率

    当 fs < 2*f_signal 时，信号频率 f_signal 会混叠到:
    f_alias = |f_signal - k * fs|, 其中 k = round(f_signal / fs)

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


def get_sampling_info(config: SamplingConfig) -> dict:
    """获取采样信息

    Parameters
    ----------
    config : SamplingConfig
        采样配置

    Returns
    -------
    dict
        采样信息字典
    """
    return {
        "采样频率": f"{config.fs:.1f} Hz",
        "信号频率": f"{config.f_signal:.1f} Hz",
        "奈奎斯特率": f"{config.nyquist_rate:.1f} Hz",
        "过采样率": f"{config.oversampling_ratio:.2f}",
        "是否满足奈奎斯特": config.is_nyquist_satisfied,
        "采样点数": int(config.fs * config.duration),
        "持续时间": f"{config.duration:.3f} s",
    }
