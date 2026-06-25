"""
频率响应分析工具
================

提供通用的频率响应分析功能，包括:
- 幅频响应计算
- 相频响应计算
- 波特图数据生成
- 截止频率检测
- 系统级联分析
"""

import numpy as np
from typing import List, Tuple, Optional


def generate_log_freq(start: float = 1.0, stop: float = 1e6,
                      num_points: int = 1000) -> np.ndarray:
    """生成对数间隔的频率数组

    Parameters
    ----------
    start : float
        起始频率 (Hz)
    stop : float
        终止频率 (Hz)
    num_points : int
        频率点数

    Returns
    -------
    np.ndarray
        对数间隔的频率数组
    """
    return np.logspace(np.log10(start), np.log10(stop), num_points)


def generate_linear_freq(start: float = 0.0, stop: float = 1e4,
                         num_points: int = 1000) -> np.ndarray:
    """生成线性间隔的频率数组

    Parameters
    ----------
    start : float
        起始频率 (Hz)
    stop : float
        终止频率 (Hz)
    num_points : int
        频率点数

    Returns
    -------
    np.ndarray
        线性间隔的频率数组
    """
    return np.linspace(start, stop, num_points)


def find_cutoff_frequency(f: np.ndarray, mag_db: np.ndarray,
                          attenuation_db: float = -3.0) -> float:
    """查找截止频率

    截止频率定义为幅频响应下降到指定衰减量的频率点。

    Parameters
    ----------
    f : np.ndarray
        频率数组 (Hz)
    mag_db : np.ndarray
        幅度响应 (dB)
    attenuation_db : float
        衰减量 (dB), 默认 -3dB

    Returns
    -------
    float
        截止频率 (Hz)
    """
    # 找到最大增益
    max_gain = np.max(mag_db)
    target = max_gain + attenuation_db  # attenuation_db 为负值

    # 找到第一个低于目标的频率点
    for i in range(len(mag_db) - 1):
        if mag_db[i] >= target and mag_db[i + 1] < target:
            # 线性插值
            ratio = (target - mag_db[i]) / (mag_db[i + 1] - mag_db[i])
            return f[i] + ratio * (f[i + 1] - f[i])

    # 如果是高通滤波器，从后往前找
    for i in range(len(mag_db) - 1, 0, -1):
        if mag_db[i] >= target and mag_db[i - 1] < target:
            ratio = (target - mag_db[i]) / (mag_db[i - 1] - mag_db[i])
            return f[i] + ratio * (f[i - 1] - f[i])

    return np.nan


def find_bandwidth(f: np.ndarray, mag_db: np.ndarray,
                   attenuation_db: float = -3.0) -> Tuple[float, float, float]:
    """查找带通滤波器的带宽

    Parameters
    ----------
    f : np.ndarray
        频率数组 (Hz)
    mag_db : np.ndarray
        幅度响应 (dB)
    attenuation_db : float
        衰减量 (dB), 默认 -3dB

    Returns
    -------
    Tuple[float, float, float]
        (下截止频率, 上截止频率, 带宽)
    """
    max_gain = np.max(mag_db)
    target = max_gain + attenuation_db

    # 找峰值位置
    peak_idx = np.argmax(mag_db)

    # 向左找下截止频率
    f_low = np.nan
    for i in range(peak_idx, 0, -1):
        if mag_db[i] >= target and mag_db[i - 1] < target:
            ratio = (target - mag_db[i]) / (mag_db[i - 1] - mag_db[i])
            f_low = f[i] + ratio * (f[i - 1] - f[i])
            break

    # 向右找上截止频率
    f_high = np.nan
    for i in range(peak_idx, len(mag_db) - 1):
        if mag_db[i] >= target and mag_db[i + 1] < target:
            ratio = (target - mag_db[i]) / (mag_db[i + 1] - mag_db[i])
            f_high = f[i] + ratio * (f[i + 1] - f[i])
            break

    bandwidth = f_high - f_low if not (np.isnan(f_low) or np.isnan(f_high)) else np.nan
    return f_low, f_high, bandwidth


def cascade_transfer_functions(filters: list, f: np.ndarray) -> np.ndarray:
    """级联多个滤波器的传递函数

    Parameters
    ----------
    filters : list
        滤波器对象列表，每个对象需要有 transfer_function 方法
    f : np.ndarray
        频率数组 (Hz)

    Returns
    -------
    np.ndarray
        级联后的传递函数值
    """
    H_total = np.ones(len(f), dtype=complex)
    for filt in filters:
        H_total *= filt.transfer_function(f)
    return H_total


def analyze_filter(filter_obj, f: np.ndarray) -> dict:
    """全面分析滤波器特性

    Parameters
    ----------
    filter_obj
        滤波器对象
    f : np.ndarray
        频率数组 (Hz)

    Returns
    -------
    dict
        包含频率响应各项数据的字典
    """
    H = filter_obj.transfer_function(f)
    mag = np.abs(H)
    mag_db = 20.0 * np.log10(np.maximum(mag, 1e-30))
    phase_deg = np.degrees(np.angle(H))

    result = {
        'frequency': f,
        'transfer_function': H,
        'magnitude': mag,
        'magnitude_db': mag_db,
        'phase_deg': phase_deg,
        'phase_rad': np.angle(H),
    }

    # 查找截止频率
    fc = find_cutoff_frequency(f, mag_db)
    if not np.isnan(fc):
        result['cutoff_frequency'] = fc

    # 查找带宽 (用于带通/带阻)
    f_low, f_high, bw = find_bandwidth(f, mag_db)
    if not np.isnan(bw):
        result['lower_cutoff'] = f_low
        result['upper_cutoff'] = f_high
        result['bandwidth'] = bw

    return result


def db_to_linear(db: float) -> float:
    """dB 转线性值

    Parameters
    ----------
    db : float
        dB 值

    Returns
    -------
    float
        线性值
    """
    return 10.0 ** (db / 20.0)


def linear_to_db(linear: float) -> float:
    """线性值转 dB

    Parameters
    ----------
    linear : float
        线性值

    Returns
    -------
    float
        dB 值
    """
    return 20.0 * np.log10(max(linear, 1e-30))
