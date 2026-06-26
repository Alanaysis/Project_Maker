"""
Free Vibration Analysis Module
自由振动分析模块

This module implements free vibration analysis for single-degree-of-freedom (SDOF) systems.
Free vibration occurs when a system oscillates without external forces after an initial
disturbance (initial displacement, velocity, or both).

核心方程: m*x'' + c*x' + k*x = 0

其中:
  m = 质量 (mass)
  c = 阻尼系数 (damping coefficient)
  k = 刚度系数 (stiffness coefficient)
  x = 位移 (displacement)
"""

import numpy as np
from scipy.linalg import eig
from typing import Tuple, NamedTuple


class VibrationResult(NamedTuple):
    """振动分析结果 / Vibration analysis result"""
    time: np.ndarray
    displacement: np.ndarray
    velocity: np.ndarray
    acceleration: np.ndarray
    natural_freq_hz: float
    damping_ratio: float
    damped_freq_hz: float


def natural_frequency(stiffness: float, mass: float) -> float:
    """
    计算无阻尼固有频率 (undamped natural frequency)

    公式: omega_n = sqrt(k/m)
    单位: rad/s

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)

    Returns:
        固有频率 omega_n (rad/s)
    """
    if mass <= 0:
        raise ValueError("质量必须为正数 / Mass must be positive")
    if stiffness <= 0:
        raise ValueError("刚度必须为正数 / Stiffness must be positive")
    return np.sqrt(stiffness / mass)


def natural_frequency_hz(stiffness: float, mass: float) -> float:
    """
    计算固有频率 (Hz)

    公式: f_n = omega_n / (2*pi) = (1/(2*pi)) * sqrt(k/m)

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)

    Returns:
        固有频率 f_n (Hz)
    """
    return natural_frequency(stiffness, mass) / (2 * np.pi)


def damping_ratio(damping: float, stiffness: float, mass: float) -> float:
    """
    计算临界阻尼比 (damping ratio)

    临界阻尼: c_c = 2 * sqrt(k*m) = 2 * m * omega_n
    阻尼比: zeta = c / c_c = c / (2 * m * omega_n)

    阻尼分类:
    - zeta = 0: 无阻尼 (undamped) - 持续振荡
    - 0 < zeta < 1: 欠阻尼 (underdamped) - 衰减振荡
    - zeta = 1: 临界阻尼 (critically damped) - 最快回到平衡
    - zeta > 1: 过阻尼 (overdamped) - 缓慢回到平衡

    Args:
        damping: 阻尼系数 c (N*s/m)
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)

    Returns:
        阻尼比 zeta (无量纲)
    """
    omega_n = natural_frequency(stiffness, mass)
    critical_damping = 2 * mass * omega_n
    if critical_damping == 0:
        raise ValueError("系统参数无效 / Invalid system parameters")
    return damping / critical_damping


def damped_natural_frequency(stiffness: float, mass: float, damping: float) -> float:
    """
    计算有阻尼固有频率 (damped natural frequency)

    仅适用于欠阻尼系统 (zeta < 1)
    公式: omega_d = omega_n * sqrt(1 - zeta^2)

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)

    Returns:
        有阻尼固有频率 omega_d (rad/s)
    """
    omega_n = natural_frequency(stiffness, mass)
    zeta = damping_ratio(damping, stiffness, mass)
    if zeta >= 1.0:
        raise ValueError(
            f"系统为过阻尼或临界阻尼 (zeta={zeta:.4f} >= 1), 不存在有阻尼频率"
        )
    return omega_n * np.sqrt(1 - zeta ** 2)


def free_vibration_undamped(
    stiffness: float,
    mass: float,
    initial_displacement: float = 1.0,
    initial_velocity: float = 0.0,
    duration: float = 10.0,
    num_points: int = 10000,
) -> VibrationResult:
    """
    无阻尼自由振动分析 (undamped free vibration analysis)

    运动方程: m*x'' + k*x = 0
    解: x(t) = A*cos(omega_n*t) + B*sin(omega_n*t)

    其中:
        A = x(0) = 初始位移
        B = v(0) / omega_n = 初始速度 / 固有频率
        omega_n = sqrt(k/m) = 固有频率

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        initial_displacement: 初始位移 x(0) (m)
        initial_velocity: 初始速度 v(0) (m/s)
        duration: 仿真时长 (s)
        num_points: 采样点数

    Returns:
        VibrationResult 包含时间、位移、速度、加速度和频率信息
    """
    omega_n = natural_frequency(stiffness, mass)
    f_n = natural_frequency_hz(stiffness, mass)

    t = np.linspace(0, duration, num_points)

    # 无阻尼响应: x(t) = x0*cos(omega_n*t) + (v0/omega_n)*sin(omega_n*t)
    displacement = initial_displacement * np.cos(omega_n * t) + \
                   (initial_velocity / omega_n) * np.sin(omega_n * t)

    # 速度: v(t) = -A*omega_n*sin(omega_n*t) + B*omega_n*cos(omega_n*t)
    velocity = -initial_displacement * omega_n * np.sin(omega_n * t) + \
               initial_velocity * np.cos(omega_n * t)

    # 加速度: a(t) = -omega_n^2 * x(t)
    acceleration = -omega_n ** 2 * displacement

    return VibrationResult(
        time=t,
        displacement=displacement,
        velocity=velocity,
        acceleration=acceleration,
        natural_freq_hz=f_n,
        damping_ratio=0.0,
        damped_freq_hz=f_n,
    )


def free_vibration_damped(
    stiffness: float,
    mass: float,
    damping: float,
    initial_displacement: float = 1.0,
    initial_velocity: float = 0.0,
    duration: float = 10.0,
    num_points: int = 10000,
) -> VibrationResult:
    """
    有阻尼自由振动分析 (damped free vibration analysis)

    运动方程: m*x'' + c*x' + k*x = 0

    对于欠阻尼系统 (0 < zeta < 1):
    x(t) = exp(-zeta*omega_n*t) * [x0*cos(omega_d*t) + ((v0+zeta*omega_n*x0)/omega_d)*sin(omega_d*t)]

    其中:
        zeta = c / (2*m*omega_n) = 阻尼比
        omega_n = sqrt(k/m) = 固有频率
        omega_d = omega_n * sqrt(1 - zeta^2) = 有阻尼固有频率

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)
        initial_displacement: 初始位移 x(0) (m)
        initial_velocity: 初始速度 v(0) (m/s)
        duration: 仿真时长 (s)
        num_points: 采样点数

    Returns:
        VibrationResult 包含时间、位移、速度、加速度和频率信息
    """
    omega_n = natural_frequency(stiffness, mass)
    zeta = damping_ratio(damping, stiffness, mass)
    f_n = natural_frequency_hz(stiffness, mass)

    t = np.linspace(0, duration, num_points)

    if zeta >= 1.0:
        # 临界阻尼或过阻尼: x(t) = (x0 + (v0 + omega_n*x0)*(t)) * exp(-omega_n*t)
        # 对于临界阻尼情况 (zeta = 1):
        # x(t) = (x0 + (v0 + omega_n*x0)*t) * exp(-omega_n*t)
        envelope = initial_displacement + (initial_velocity + omega_n * initial_displacement) * t
        displacement = envelope * np.exp(-omega_n * t)
        velocity = (initial_velocity + omega_n * initial_displacement -
                    omega_n * (initial_displacement + (initial_velocity + omega_n * initial_displacement) * t)
                    ) * np.exp(-omega_n * t)
        acceleration = (-omega_n * (initial_velocity + omega_n * initial_displacement) -
                        omega_n * (initial_velocity + omega_n * initial_displacement -
                                   omega_n * (initial_displacement + (initial_velocity + omega_n * initial_displacement) * t)
                                   )
                        ) * np.exp(-omega_n * t)
        damped_freq = 0.0
    else:
        # 欠阻尼情况
        omega_d = damped_natural_frequency(stiffness, mass, damping)
        decay_rate = zeta * omega_n

        # 振幅包络: exp(-zeta*omega_n*t)
        envelope = np.exp(-decay_rate * t)

        # 系数 A 和 B
        A = initial_displacement
        B = (initial_velocity + decay_rate * initial_displacement) / omega_d

        # 位移
        displacement = envelope * (A * np.cos(omega_d * t) + B * np.sin(omega_d * t))

        # 速度 (对位移求导)
        velocity = (-decay_rate * envelope * (A * np.cos(omega_d * t) + B * np.sin(omega_d * t)) +
                    envelope * (-A * omega_d * np.sin(omega_d * t) + B * omega_d * np.cos(omega_d * t)))

        # 加速度 (对速度求导)
        acceleration = (decay_rate ** 2 * envelope * (A * np.cos(omega_d * t) + B * np.sin(omega_d * t)) -
                        2 * decay_rate * envelope * (-A * omega_d * np.sin(omega_d * t) +
                                                      B * omega_d * np.cos(omega_d * t)) -
                        envelope * (A * omega_d ** 2 * np.cos(omega_d * t) +
                                    B * omega_d ** 2 * np.sin(omega_d * t)))

        damped_freq = omega_d / (2 * np.pi)

    return VibrationResult(
        time=t,
        displacement=displacement,
        velocity=velocity,
        acceleration=acceleration,
        natural_freq_hz=f_n,
        damping_ratio=zeta,
        damped_freq_hz=damped_freq,
    )


def logarithmic_decrement(damped_vibration: VibrationResult) -> float:
    """
    通过衰减振动数据计算对数衰减率 (logarithmic decrement)

    对数衰减率 delta = ln(x(t1) / x(t2))

    其中 x(t1) 和 x(t2) 是两个相邻峰值的振幅。

    阻尼比与对数衰减率的关系:
        zeta = delta / sqrt(4*pi^2 + delta^2)

    适用于欠阻尼系统。

    Args:
        damped_vibration: 有阻尼自由振动结果

    Returns:
        对数衰减率 delta
    """
    disp = damped_vibration.displacement
    time = damped_vibration.time

    # 找到峰值 (局部极大值)
    peaks_idx = np.where((disp[1:-1] > disp[:-2]) & (disp[1:-1] > disp[2:]))[0] + 1

    if len(peaks_idx) < 2:
        # 尝试找谷值
        valleys_idx = np.where((disp[1:-1] < disp[:-2]) & (disp[1:-1] < disp[2:]))[0] + 1
        if len(valleys_idx) < 2:
            raise ValueError("无法找到足够的极值点 / Not enough extrema found")
        peaks_idx = valleys_idx

    # 取连续峰值计算对数衰减率
    peak_values = np.abs(disp[peaks_idx])
    if np.any(peak_values[:-1] < 1e-12):
        raise ValueError("峰值接近零，无法计算对数衰减率 / Peak values too small")

    deltas = np.log(peak_values[:-1] / peak_values[1:])

    # 取平均对数衰减率
    return float(np.mean(deltas))


def estimate_damping_from_decrement(delta: float) -> float:
    """
    从对数衰减率估计阻尼比

    公式: zeta = delta / sqrt(4*pi^2 + delta^2)

    Args:
        delta: 对数衰减率

    Returns:
        阻尼比 zeta
    """
    if delta < 0:
        raise ValueError("对数衰减率必须为非负数 / Logarithmic decrement must be non-negative")
    return delta / np.sqrt(4 * np.pi ** 2 + delta ** 2)


def energy_dissipation_rate(damping: float, stiffness: float, mass: float) -> float:
    """
    计算能量耗散率

    每周期能量耗散: Delta_E / E = 2*pi*zeta

    Args:
        damping: 阻尼系数 c (N*s/m)
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)

    Returns:
        每周期相对能量耗散率 (2*pi*zeta)
    """
    zeta = damping_ratio(damping, stiffness, mass)
    return 2 * np.pi * zeta
