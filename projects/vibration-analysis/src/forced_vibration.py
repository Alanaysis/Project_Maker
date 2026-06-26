"""
Forced Vibration Response Module
强迫振动响应模块

This module implements forced vibration analysis for SDOF systems.
Forced vibration occurs when an external time-varying force acts on the system.

核心方程: m*x'' + c*x' + k*x = F(t)

常见激励类型:
1. 简谐激励 (Harmonic): F(t) = F0 * sin(omega*t)
2. 阶跃激励 (Step): F(t) = F0 * H(t)
3. 脉冲激励 (Impulse): F(t) = I * delta(t)
4. 周期激励 (Periodic): 傅里叶级数表示
5. 随机激励 (Random): 功率谱密度描述
"""

import numpy as np
from scipy.integrate import odeint
from typing import Callable, NamedTuple


class ForcedResponse(NamedTuple):
    """强迫振动响应结果 / Forced vibration response result"""
    time: np.ndarray
    displacement: np.ndarray
    velocity: np.ndarray
    acceleration: np.ndarray
    force: np.ndarray


def _sdof_ode(state, t, mass, damping, stiffness, force_func):
    """
    SDOF系统常微分方程 (SDOF system ODE)

    将二阶方程 m*x'' + c*x' + k*x = F(t) 转换为两个一阶方程:
        x' = v
        v' = (F(t) - c*v - k*x) / m

    Args:
        state: [x, v] 位移和速度
        t: 时间
        mass: 质量
        damping: 阻尼系数
        stiffness: 刚度系数
        force_func: 外力函数 F(t)

    Returns:
        [x', v'] 导数
    """
    x, v = state
    dxdt = v
    dvdt = (force_func(t) - damping * v - stiffness * x) / mass
    return [dxdt, dvdt]


def harmonic_force_response(
    stiffness: float,
    mass: float,
    damping: float,
    force_amplitude: float,
    forcing_freq: float,
    initial_displacement: float = 0.0,
    initial_velocity: float = 0.0,
    duration: float = 10.0,
    num_points: int = 10000,
) -> ForcedResponse:
    """
    简谐激励下的强迫振动响应 (forced vibration under harmonic excitation)

    激励: F(t) = F0 * sin(omega_f * t)

    稳态响应幅值:
        X = F0/k / sqrt((1-r^2)^2 + (2*zeta*r)^2)

    其中:
        r = omega_f / omega_n = 频率比
        zeta = c / (2*m*omega_n) = 阻尼比
        F0/k = 静态位移

    相位角:
        phi = atan(2*zeta*r / (1-r^2))

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)
        force_amplitude: 力幅值 F0 (N)
        forcing_freq: 激励频率 omega_f / (2*pi) (Hz)
        initial_displacement: 初始位移 (m)
        initial_velocity: 初始速度 (m/s)
        duration: 仿真时长 (s)
        num_points: 采样点数

    Returns:
        ForcedResponse 包含时间、位移、速度、加速度和力
    """
    omega_f = 2 * np.pi * forcing_freq

    def force_func(t):
        return force_amplitude * np.sin(omega_f * t)

    state0 = [initial_displacement, initial_velocity]
    t = np.linspace(0, duration, num_points)

    # 使用 odeint 求解
    def deriv(state, time):
        return _sdof_ode(state, time, mass, damping, stiffness, force_func)

    solution = odeint(deriv, state0, t)
    displacement = solution[:, 0]
    velocity = solution[:, 1]

    # 数值计算加速度
    acceleration = np.gradient(velocity, t)

    force = force_func(t)

    return ForcedResponse(
        time=t,
        displacement=displacement,
        velocity=velocity,
        acceleration=acceleration,
        force=force,
    )


def step_force_response(
    stiffness: float,
    mass: float,
    damping: float,
    force_magnitude: float,
    initial_displacement: float = 0.0,
    initial_velocity: float = 0.0,
    duration: float = 10.0,
    num_points: int = 10000,
) -> ForcedResponse:
    """
    阶跃激励下的强迫振动响应 (forced vibration under step excitation)

    激励: F(t) = F0 for t >= 0

    欠阻尼响应:
        x(t) = F0/k * (1 - exp(-zeta*omega_n*t) *
                      (cos(omega_d*t) + (zeta/sqrt(1-zeta^2))*sin(omega_d*t)))

    静态位移: x_static = F0/k

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)
        force_magnitude: 阶跃力幅值 F0 (N)
        initial_displacement: 初始位移 (m)
        initial_velocity: 初始速度 (m/s)
        duration: 仿真时长 (s)
        num_points: 采样点数

    Returns:
        ForcedResponse
    """
    omega_n = np.sqrt(stiffness / mass)
    zeta = damping / (2 * mass * omega_n)

    def force_func(t):
        t_arr = np.asarray(t)
        return force_magnitude * (t_arr >= 0).astype(float)

    state0 = [initial_displacement, initial_velocity]
    t = np.linspace(0, duration, num_points)

    def deriv(state, time):
        return _sdof_ode(state, time, mass, damping, stiffness, force_func)

    solution = odeint(deriv, state0, t)
    displacement = solution[:, 0]
    velocity = solution[:, 1]
    acceleration = np.gradient(velocity, t)

    force = force_func(t)

    return ForcedResponse(
        time=t,
        displacement=displacement,
        velocity=velocity,
        acceleration=acceleration,
        force=force,
    )


def impulse_response(
    stiffness: float,
    mass: float,
    damping: float,
    impulse_magnitude: float,
    impulse_time: float = 0.0,
    initial_displacement: float = 0.0,
    initial_velocity: float = 0.0,
    duration: float = 10.0,
    num_points: int = 10000,
) -> ForcedResponse:
    """
    脉冲激励下的强迫振动响应 (forced vibration under impulse excitation)

    脉冲力: F(t) = I * delta(t - t_impulse)

    近似为短时间方波脉冲。
    脉冲响应即单位冲量下的自由振动 (由 Duhamel 积分可得)。

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)
        impulse_magnitude: 冲量 I (N*s)
        impulse_time: 脉冲作用时间 (s)
        initial_displacement: 初始位移 (m)
        initial_velocity: 初始速度 (m/s)
        duration: 仿真时长 (s)
        num_points: 采样点数

    Returns:
        ForcedResponse
    """
    pulse_width = duration / num_points * 10  # 10个时间步宽的脉冲
    omega_n = np.sqrt(stiffness / mass)
    zeta = damping / (2 * mass * omega_n)

    # 脉冲产生的初始速度: v0 = I / m
    effective_v0 = initial_velocity + impulse_magnitude / mass

    def force_func(t):
        t_arr = np.asarray(t)
        return impulse_magnitude / pulse_width * (
            (t_arr >= impulse_time) & (t_arr < impulse_time + pulse_width)
        ).astype(float)

    state0 = [initial_displacement, effective_v0]
    t = np.linspace(0, duration, num_points)

    def deriv(state, time):
        return _sdof_ode(state, time, mass, damping, stiffness, force_func)

    solution = odeint(deriv, state0, t)
    displacement = solution[:, 0]
    velocity = solution[:, 1]
    acceleration = np.gradient(velocity, t)

    force = force_func(t)

    return ForcedResponse(
        time=t,
        displacement=displacement,
        velocity=velocity,
        acceleration=acceleration,
        force=force,
    )


def frequency_response_function(stiffness: float, mass: float, damping: float,
                                freq_range: np.ndarray) -> dict:
    """
    计算频响函数 (Frequency Response Function, FRF)

    对于 SDOF 系统:
        H(omega) = X(omega) / F(omega) = 1 / (k - m*omega^2 + i*c*omega)

    幅频特性: |H(omega)| = 1 / sqrt((k - m*omega^2)^2 + (c*omega)^2)
    相频特性: phi(omega) = atan(c*omega / (k - m*omega^2))

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)
        freq_range: 频率范围数组 (Hz)

    Returns:
        dict 包含:
            - freq: 频率数组 (Hz)
            - omega: 角频率数组 (rad/s)
            - magnitude: FRF幅值
            - phase: FRF相位 (rad)
            - real_part: FRF实部
            - imag_part: FRF虚部
    """
    omega = 2 * np.pi * freq_range

    # 频响函数: H(omega) = 1 / (k - m*omega^2 + i*c*omega)
    denom_real = stiffness - mass * omega ** 2
    denom_imag = damping * omega

    # 避免除以零
    denom_mag = np.sqrt(denom_real ** 2 + denom_imag ** 2)
    denom_mag[denom_mag < 1e-12] = 1e-12

    magnitude = 1.0 / denom_mag
    phase = np.arctan2(-denom_imag, denom_real)  # 负号是因为分母的虚部取反
    real_part = denom_real / denom_mag ** 2
    imag_part = -denom_imag / denom_mag ** 2

    return {
        "freq": freq_range,
        "omega": omega,
        "magnitude": magnitude,
        "phase": phase,
        "real_part": real_part,
        "imag_part": imag_part,
    }


def steady_state_amplitude(stiffness: float, mass: float, damping: float,
                           forcing_freq: float) -> float:
    """
    计算简谐激励下的稳态响应幅值

    X = (F0/k) / sqrt((1-r^2)^2 + (2*zeta*r)^2)

    其中 r = omega_f/omega_n, 返回放大因子 (amplification factor):
        AF = 1 / sqrt((1-r^2)^2 + (2*zeta*r)^2)

    Args:
        stiffness: 刚度系数 k (N/m)
        mass: 质量 m (kg)
        damping: 阻尼系数 c (N*s/m)
        forcing_freq: 激励频率 (Hz)

    Returns:
        放大因子 (无量纲)
    """
    omega_n = np.sqrt(stiffness / mass)
    omega_f = 2 * np.pi * forcing_freq
    zeta = damping / (2 * mass * omega_n)

    r = omega_f / omega_n

    # 放大因子
    amplification = 1.0 / np.sqrt((1 - r ** 2) ** 2 + (2 * zeta * r) ** 2)

    return amplification
