"""
Resonance Detection Module
共振检测模块

This module implements resonance detection and analysis for vibration systems.
Resonance occurs when the forcing frequency matches (or is close to) a natural frequency,
causing large amplitude responses.

共振条件: 激励频率 = 固有频率
共振危害: 结构破坏、疲劳失效、噪声增加
"""

import numpy as np
from typing import NamedTuple, Optional


class ResonanceInfo(NamedTuple):
    """共振信息 / Resonance information"""
    frequency_hz: float  # 共振频率 (Hz)
    amplitude: float  # 共振幅值
    quality_factor: float  # 品质因数 Q
    bandwidth_hz: float  # 共振峰带宽 (Hz)
    damping_ratio: float  # 阻尼比


def find_resonance_frequency(stiffness: float, mass: float,
                             damping: float) -> float:
    """
    计算共振频率 (resonance frequency)

    对于有阻尼系统，共振频率略低于固有频率:
        omega_r = omega_n * sqrt(1 - 2*zeta^2)  (zeta < 1/sqrt(2))

    对于无阻尼系统:
        omega_r = omega_n

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)

    Returns:
        共振频率 (Hz)
    """
    omega_n = np.sqrt(stiffness / mass)
    zeta = damping / (2 * mass * omega_n)

    if zeta >= 1.0 / np.sqrt(2):
        # 阻尼过大，无共振峰
        return omega_n / (2 * np.pi)

    omega_r = omega_n * np.sqrt(1 - 2 * zeta ** 2)
    return omega_r / (2 * np.pi)


def quality_factor(damping_ratio: float) -> float:
    """
    计算品质因数 (quality factor Q)

    Q = 1 / (2*zeta)

    物理意义:
    - Q 越大，共振峰越尖锐
    - Q 越小，阻尼越大，共振峰越平缓
    - Q = 1/(2*zeta) 表示共振时振幅放大倍数

    Args:
        damping_ratio: 阻尼比 zeta

    Returns:
        品质因数 Q
    """
    if damping_ratio <= 0:
        return float('inf')
    return 1.0 / (2 * damping_ratio)


def resonance_amplification(stiffness: float, mass: float, damping: float) -> float:
    """
    计算共振时的振幅放大倍数

    在共振频率处:
        X_resonance / X_static = Q = 1 / (2*zeta)

    其中 X_static = F0/k 是静态位移。

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)

    Returns:
        共振放大倍数 (Q因子)
    """
    omega_n = np.sqrt(stiffness / mass)
    zeta = damping / (2 * mass * omega_n)
    return quality_factor(zeta)


def half_power_bandwidth(frf_magnitude: np.ndarray, freq: np.ndarray,
                         peak_idx: int) -> float:
    """
    计算共振峰的半功率带宽 (half-power bandwidth)

    半功率点: 幅值下降到峰值的 1/sqrt(2) (即 -3dB) 时的频率点。

    带宽 B = omega_2 - omega_1
    阻尼比 zeta = B / (2 * omega_n)

    Args:
        frf_magnitude: FRF幅值数组
        freq: 频率数组 (Hz)
        peak_idx: 共振峰索引

    Returns:
        半功率带宽 (Hz)
    """
    peak_magnitude = frf_magnitude[peak_idx]
    threshold = peak_magnitude / np.sqrt(2)

    # 找峰值左侧的半功率点
    left_bandwidth = 0.0
    for i in range(peak_idx, -1, -1):
        if frf_magnitude[i] <= threshold:
            # 线性插值
            if i < peak_idx and frf_magnitude[i + 1] > threshold:
                frac = (threshold - frf_magnitude[i]) / (frf_magnitude[i + 1] - frf_magnitude[i])
                left_bandwidth = freq[i] + frac * (freq[i + 1] - freq[i])
            else:
                left_bandwidth = freq[i]
            break

    # 找峰值右侧的半功率点
    right_bandwidth = 0.0
    for i in range(peak_idx, len(frf_magnitude)):
        if frf_magnitude[i] <= threshold:
            if i > peak_idx and frf_magnitude[i - 1] > threshold:
                frac = (threshold - frf_magnitude[i]) / (frf_magnitude[i - 1] - frf_magnitude[i])
                right_bandwidth = freq[i] - frac * (freq[i] - freq[i - 1])
            else:
                right_bandwidth = freq[i]
            break

    return right_bandwidth - left_bandwidth


def detect_resonance_peaks(
    stiffness: float,
    mass: float,
    damping: float,
    freq_range: np.ndarray,
) -> list:
    """
    检测共振峰 (detect resonance peaks)

    通过计算 FRF 幅值并寻找峰值来检测共振频率。

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)
        freq_range: 频率范围 (Hz)

    Returns:
        共振峰列表，每个峰包含频率、幅值、Q因子等信息
    """
    # 计算 FRF 幅值
    omega = 2 * np.pi * freq_range
    denom = np.sqrt((stiffness - mass * omega ** 2) ** 2 + (damping * omega) ** 2)
    magnitude = 1.0 / np.maximum(denom, 1e-12)

    # 找峰值
    peaks_idx = np.where(
        (magnitude[1:-1] > magnitude[:-2]) & (magnitude[1:-1] > magnitude[2:])
    )[0] + 1

    peaks = []
    for idx in peaks_idx:
        peak_freq = freq_range[idx]
        peak_amp = magnitude[idx]

        zeta = damping / (2 * mass * np.sqrt(stiffness / mass))
        Q = quality_factor(zeta)

        # 计算带宽
        bw = half_power_bandwidth(magnitude, freq_range, idx)

        resonance_info = ResonanceInfo(
            frequency_hz=peak_freq,
            amplitude=peak_amp,
            quality_factor=Q,
            bandwidth_hz=bw,
            damping_ratio=zeta,
        )
        peaks.append(resonance_info)

    return peaks


def is_near_resonance(forcing_freq: float, natural_freq_hz: float,
                      tolerance: float = 0.1) -> bool:
    """
    判断激励频率是否接近共振频率

    Args:
        forcing_freq: 激励频率 (Hz)
        natural_freq_hz: 固有频率 (Hz)
        tolerance: 容差比例 (默认 10%)

    Returns:
        是否接近共振
    """
    if natural_freq_hz < 1e-10:
        return False
    rel_diff = abs(forcing_freq - natural_freq_hz) / natural_freq_hz
    return rel_diff < tolerance


def resonance_safety_margin(
    forcing_freq: float,
    natural_freq_hz: float,
    damping_ratio: float,
) -> float:
    """
    计算共振安全裕度

    安全裕度 = |f_forcing - f_natural| / f_natural

    Args:
        forcing_freq: 激励频率 (Hz)
        natural_freq_hz: 固有频率 (Hz)
        damping_ratio: 阻尼比

    Returns:
        安全裕度 (0-1), 越接近0越危险
    """
    if natural_freq_hz < 1e-10:
        return 0.0
    return abs(forcing_freq - natural_freq_hz) / natural_freq_hz


def avoid_resonance_design(stiffness: float, mass: float,
                           forcing_freq_range: tuple,
                           margin: float = 0.2) -> dict:
    """
    提供避免共振的设计建议

    通过调整刚度或质量来改变固有频率，使其远离激励频率范围。

    Args:
        stiffness: 当前刚度 (N/m)
        mass: 当前质量 (kg)
        forcing_freq_range: 激励频率范围 (f_min, f_max)
        margin: 安全裕度比例 (默认 20%)

    Returns:
        设计建议字典
    """
    f_natural = np.sqrt(stiffness / mass) / (2 * np.pi)
    f_min, f_max = forcing_freq_range

    # 需要固有频率远离 [f_min, f_max]
    # 方案1: 提高固有频率到 f_max * (1 + margin)
    f_target_high = f_max * (1 + margin)
    k_needed_high = mass * (2 * np.pi * f_target_high) ** 2

    # 方案2: 降低固有频率到 f_min * (1 - margin)
    f_target_low = f_min * (1 - margin) if f_min * (1 - margin) > 0 else 0.0
    k_needed_low = mass * (2 * np.pi * f_target_low) ** 2 if f_target_low > 0 else 0

    return {
        "current_natural_freq_hz": f_natural,
        "forcing_freq_range": (f_min, f_max),
        "safety_margin": margin,
        "option_increase_freq": {
            "target_freq_hz": f_target_high,
            "required_stiffness_Nm": k_needed_high,
            "stiffness_change_ratio": k_needed_high / stiffness if stiffness > 0 else float('inf'),
        },
        "option_decrease_freq": {
            "target_freq_hz": f_target_low,
            "required_stiffness_Nm": k_needed_low,
            "stiffness_change_ratio": k_needed_low / stiffness if stiffness > 0 else 0,
        },
    }
