"""
Frequency Response Function Module
频响函数模块

This module implements Frequency Response Function (FRF) analysis for SDOF and MDOF systems.
FRF describes the steady-state response of a system to harmonic excitation at different frequencies.

FRF定义: H(omega) = X(omega) / F(omega)

类型:
    - 位移频响函数 (Displacement FRF)
    - 速度频响函数 (Velocity FRF)
    - 加速度频响函数 (Acceleration FRF)
"""

import numpy as np
from typing import NamedTuple, Optional


class FRFResult(NamedTuple):
    """FRF分析结果 / FRF analysis result"""
    frequency: np.ndarray  # 频率 (Hz)
    omega: np.ndarray  # 角频率 (rad/s)
    magnitude: np.ndarray  # 幅值
    phase: np.ndarray  # 相位 (rad)
    real_part: np.ndarray  # 实部
    imag_part: np.ndarray  # 虚部
    frf_type: str  # FRF类型


def displacement_frf(
    stiffness: float,
    mass: float,
    damping: float,
    freq_range: np.ndarray,
) -> FRFResult:
    """
    位移频响函数 (Displacement FRF)

    H_x(omega) = 1 / (k - m*omega^2 + i*c*omega)

    幅值: |H_x| = 1 / sqrt((k - m*omega^2)^2 + (c*omega)^2)
    相位: phi = atan(c*omega / (k - m*omega^2))

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)
        freq_range: 频率范围 (Hz)

    Returns:
        FRFResult
    """
    omega = 2 * np.pi * freq_range

    denom_real = stiffness - mass * omega ** 2
    denom_imag = damping * omega

    denom_mag = np.sqrt(denom_real ** 2 + denom_imag ** 2)
    denom_mag[denom_mag < 1e-12] = 1e-12

    magnitude = 1.0 / denom_mag
    phase = np.arctan2(-denom_imag, denom_real)
    real_part = denom_real / denom_mag ** 2
    imag_part = -denom_imag / denom_mag ** 2

    return FRFResult(
        frequency=freq_range,
        omega=omega,
        magnitude=magnitude,
        phase=phase,
        real_part=real_part,
        imag_part=imag_part,
        frf_type="displacement",
    )


def velocity_frf(
    stiffness: float,
    mass: float,
    damping: float,
    freq_range: np.ndarray,
) -> FRFResult:
    """
    速度频响函数 (Velocity FRF)

    H_v(omega) = i*omega / (k - m*omega^2 + i*c*omega)

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)
        freq_range: 频率范围 (Hz)

    Returns:
        FRFResult
    """
    omega = 2 * np.pi * freq_range

    denom_real = stiffness - mass * omega ** 2
    denom_imag = damping * omega

    denom_mag = np.sqrt(denom_real ** 2 + denom_imag ** 2)
    denom_mag[denom_mag < 1e-12] = 1e-12

    # |H_v| = omega / |denominator|
    magnitude = omega / denom_mag
    # Phase: atan2(omega, denom_real) + phase_of_denominator
    phase = np.arctan2(omega, denom_real) + np.arctan2(-denom_imag, denom_real)
    real_part = denom_imag / denom_mag ** 2
    imag_part = denom_real / denom_mag ** 2

    return FRFResult(
        frequency=freq_range,
        omega=omega,
        magnitude=magnitude,
        phase=phase,
        real_part=real_part,
        imag_part=imag_part,
        frf_type="velocity",
    )


def acceleration_frf(
    stiffness: float,
    mass: float,
    damping: float,
    freq_range: np.ndarray,
) -> FRFResult:
    """
    加速度频响函数 (Acceleration FRF)

    H_a(omega) = -(omega^2) / (k - m*omega^2 + i*c*omega)

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)
        freq_range: 频率范围 (Hz)

    Returns:
        FRFResult
    """
    omega = 2 * np.pi * freq_range

    denom_real = stiffness - mass * omega ** 2
    denom_imag = damping * omega

    denom_mag = np.sqrt(denom_real ** 2 + denom_imag ** 2)
    denom_mag[denom_mag < 1e-12] = 1e-12

    # |H_a| = omega^2 / |denominator|
    magnitude = omega ** 2 / denom_mag
    # Phase: atan2(omega^2, -denom_real) + phase_of_denominator
    phase = np.arctan2(-omega ** 2, -denom_real) + np.arctan2(-denom_imag, denom_real)
    real_part = -denom_real / denom_mag ** 2
    imag_part = denom_imag / denom_mag ** 2

    return FRFResult(
        frequency=freq_range,
        omega=omega,
        magnitude=magnitude,
        phase=phase,
        real_part=real_part,
        imag_part=imag_part,
        frf_type="acceleration",
    )


def mobility_frf(
    stiffness: float,
    mass: float,
    damping: float,
    freq_range: np.ndarray,
) -> FRFResult:
    """
    导纳/机动率频响函数 (Mobility FRF)

    H_m(omega) = v / F = i*omega / (k - m*omega^2 + i*c*omega)

    与速度 FRF 相同，但物理意义不同。

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)
        freq_range: 频率范围 (Hz)

    Returns:
        FRFResult
    """
    return velocity_frf(stiffness, mass, damping, freq_range)


def admittance_frf(
    stiffness: float,
    mass: float,
    damping: float,
    freq_range: np.ndarray,
) -> FRFResult:
    """
    导纳频响函数 (Admittance FRF)

    与速度 FRF 相同。

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)
        freq_range: 频率范围 (Hz)

    Returns:
        FRFResult
    """
    return velocity_frf(stiffness, mass, damping, freq_range)


def receptance_frf(
    stiffness: float,
    mass: float,
    damping: float,
    freq_range: np.ndarray,
) -> FRFResult:
    """
     receptance 频响函数 (位移/力)

    即位移 FRF。

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)
        freq_range: 频率范围 (Hz)

    Returns:
        FRFResult
    """
    return displacement_frf(stiffness, mass, damping, freq_range)


def plot_frf_bode(frf: FRFResult, title: str = "FRF Bode Plot") -> dict:
    """
    生成 FRF 的 Bode 图数据 (幅值和相位)

    Args:
        frf: FRF分析结果
        title: 图表标题

    Returns:
        dict 包含幅值和相位数据
    """
    return {
        "title": title,
        "frequency": frf.frequency,
        "magnitude_db": 20 * np.log10(np.maximum(frf.magnitude, 1e-20)),
        "phase_deg": np.degrees(frf.phase),
        "magnitude_linear": frf.magnitude,
        "phase_rad": frf.phase,
    }


def plot_frf_nyquist(frf: FRFResult, title: str = "FRF Nyquist Plot") -> dict:
    """
    生成 FRF 的 Nyquist 图数据 (实部 vs 虚部)

    Args:
        frf: FRF分析结果
        title: 图表标题

    Returns:
        dict 包含 Nyquist 图数据
    """
    return {
        "title": title,
        "real_part": frf.real_part,
        "imag_part": frf.imag_part,
    }


def plot_frf_colormap(frf: FRFResult, title: str = "FRF Colormap") -> dict:
    """
    生成 FRF 的 Colormap 图数据

    Args:
        frf: FRF分析结果
        title: 图表标题

    Returns:
        dict 包含 Colormap 数据
    """
    return {
        "title": title,
        "frequency": frf.frequency,
        "magnitude_db": 20 * np.log10(np.maximum(frf.magnitude, 1e-20)),
    }
