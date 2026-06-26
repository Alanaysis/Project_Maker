"""
Forced Vibration Response Demo
强迫振动响应演示

This example demonstrates various forced vibration scenarios:
- Harmonic excitation at different frequencies
- Step excitation response
- Impulse excitation
- Frequency sweep analysis
- Resonance avoidance
"""

import numpy as np
import matplotlib.pyplot as plt

from src.free_vibration import natural_frequency_hz, damping_ratio
from src.forced_vibration import (
    harmonic_force_response,
    step_force_response,
    impulse_response,
    frequency_response_function,
    steady_state_amplitude,
)
from src.frequency_response import (
    displacement_frf,
    velocity_frf,
    acceleration_frf,
    plot_frf_bode,
    plot_frf_nyquist,
)
from src.resonance import (
    find_resonance_frequency,
    quality_factor,
    resonance_safety_margin,
    avoid_resonance_design,
)


def example_harmonic_response():
    """简谐激励响应示例"""
    print("=" * 60)
    print("简谐激励响应 / Harmonic Excitation Response")
    print("=" * 60)

    mass = 1.0
    stiffness = 100.0
    damping = 2.0

    f_n = natural_frequency_hz(stiffness, mass)
    zeta = damping_ratio(damping, stiffness, mass)

    print(f"\n系统参数 System Parameters:")
    print(f"  质量 Mass: {mass} kg")
    print(f"  刚度 Stiffness: {stiffness} N/m")
    print(f"  阻尼 Damping: {damping} N*s/m")
    print(f"  固有频率 Natural Frequency: {f_n:.4f} Hz")
    print(f"  阻尼比 Damping Ratio: {zeta:.4f}")

    # 不同频率比的激励
    freq_ratios = [0.1, 0.5, 0.9, 1.0, 1.1, 1.5, 2.0, 5.0]
    force_amplitude = 10.0
    duration = 8.0

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    for idx, ratio in enumerate(freq_ratios):
        forcing_freq = f_n * ratio
        response = harmonic_force_response(
            stiffness, mass, damping,
            force_amplitude=force_amplitude,
            forcing_freq=forcing_freq,
            duration=duration,
            num_points=5000,
        )

        # 稳态幅值
        steady_amp = steady_state_amplitude(stiffness, mass, damping, forcing_freq)
        static_disp = force_amplitude / stiffness

        ax_idx = idx
        if ax_idx < 4:
            row, col = 0, ax_idx
        else:
            row, col = 1, ax_idx - 4

        axes[row, col].plot(response.time, response.displacement, 'b-', linewidth=1.0)
        axes[row, col].axhline(y=0, color='k', linestyle='--', alpha=0.3)
        axes[row, col].set_xlabel('时间 Time (s)')
        axes[row, col].set_ylabel('位移 Displacement (m)')
        axes[row, col].set_title(f'r = {ratio:.1f} (f = {forcing_freq:.2f} Hz)\n'
                                f'稳态幅值 = {steady_amp * static_disp:.4f} m')
        axes[row, col].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/tmp/harmonic_response.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: /tmp/harmonic_response.png")
    plt.close()

    # 频率响应曲线
    print(f"\n频率响应 Frequency Response:")
    print(f"  {'频率比 r':<10} {'激励频率 (Hz)':<15} {'稳态幅值 (m)':<15} {'放大因子':<10}")
    print("  " + "-" * 55)

    for ratio in freq_ratios:
        forcing_freq = f_n * ratio
        amp = steady_state_amplitude(stiffness, mass, damping, forcing_freq)
        print(f"  {ratio:<10.2f} {forcing_freq:<15.4f} {amp * (force_amplitude/stiffness):<15.6f} {amp:<10.4f}")

    return f_n


def example_step_response():
    """阶跃响应示例"""
    print("\n" + "=" * 60)
    print("阶跃响应 / Step Response")
    print("=" * 60)

    mass = 1.0
    stiffness = 100.0
    damping = 2.0

    f_n = natural_frequency_hz(stiffness, mass)
    zeta = damping_ratio(damping, stiffness, mass)

    # 不同阻尼比的阶跃响应
    damping_values = [0.0, 0.1, 0.3, 0.5, 1.0]
    force_magnitude = 10.0
    duration = 10.0

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for damping in damping_values:
        zeta_check = damping / (2 * mass * np.sqrt(stiffness / mass))
        response = step_force_response(
            stiffness, mass, damping,
            force_magnitude=force_magnitude,
            duration=duration,
            num_points=5000,
        )

        static_disp = force_magnitude / stiffness
        label = f'c={diameter} (zeta={zeta_check:.3f})' if damping != 0 else '无阻尼 Undamped'
        label = f'c={damping} (zeta={zeta_check:.3f})'

        axes[0].plot(response.time, response.displacement, linewidth=1.5, label=label)
        axes[0].axhline(y=static_disp, color='r', linestyle='--', alpha=0.5,
                       label=f'稳态 Steady-state = {static_disp:.4f} m')

    axes[0].set_xlabel('时间 Time (s)')
    axes[0].set_ylabel('位移 Displacement (m)')
    axes[0].set_title('不同阻尼比的阶跃响应 Step Responses')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # 上升时间和超调量
    for damping in [0.1, 0.3, 0.5]:
        zeta_check = damping / (2 * mass * np.sqrt(stiffness / mass))
        response = step_force_response(stiffness, mass, damping,
                                       force_magnitude=force_magnitude, duration=duration)
        static_disp = force_magnitude / stiffness

        # 上升时间 (10%到90%)
        t_10 = response.time[np.searchsorted(np.abs(response.displacement), 0.1 * static_disp)]
        t_90 = response.time[np.searchsorted(np.abs(response.displacement), 0.9 * static_disp)]
        rise_time = t_90 - t_10

        # 超调量
        overshoot = (np.max(np.abs(response.displacement)) - static_disp) / static_disp * 100

        axes[1].plot([zeta_check], [rise_time], 'bo', markersize=8)
        axes[1].plot([zeta_check], [overshoot], 'rs', markersize=8)

    axes[1].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[1].set_xlabel('阻尼比 Damping Ratio zeta')
    axes[1].set_ylabel('值 Value')
    axes[1].set_title('上升时间和超调量 vs 阻尼比')
    axes[1].legend(['上升时间 Rise Time', '超调量 Overshoot'])
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/tmp/step_response.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: /tmp/step_response.png")
    plt.close()

    return f_n


def example_impulse_response():
    """脉冲响应示例"""
    print("\n" + "=" * 60)
    print("脉冲响应 / Impulse Response")
    print("=" * 60)

    mass = 1.0
    stiffness = 100.0
    damping = 2.0

    f_n = natural_frequency_hz(stiffness, mass)
    print(f"\n固有频率 Natural Frequency: {f_n:.4f} Hz")

    # 脉冲响应
    impulse_mag = 5.0  # N*s
    response = impulse_response(
        stiffness, mass, damping,
        impulse_magnitude=impulse_mag,
        duration=5.0,
        num_points=5000,
    )

    print(f"\n冲量 Impulse: {impulse_mag} N*s")
    print(f"初始速度 Initial velocity: {impulse_mag / mass:.4f} m/s")
    print(f"最大位移 Max displacement: {np.max(np.abs(response.displacement)):.4f} m")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(response.time, response.displacement, 'b-', linewidth=1.5)
    axes[0].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[0].set_xlabel('时间 Time (s)')
    axes[0].set_ylabel('位移 Displacement (m)')
    axes[0].set_title('脉冲响应位移 Impulse Response Displacement')
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(response.time, np.abs(response.displacement), 'r-', linewidth=1.5)
    # 包络线
    omega_n = np.sqrt(stiffness / mass)
    zeta = damping / (2 * mass * omega_n)
    envelope = (impulse_mag / mass / (omega_n * np.sqrt(1 - zeta**2))) * np.exp(-zeta * omega_n * response.time)
    axes[1].plot(response.time, envelope, 'r--', linewidth=1, alpha=0.7, label='理论包络 Theoretical Envelope')
    axes[1].set_xlabel('时间 Time (s)')
    axes[1].set_ylabel('振幅 Amplitude (m)')
    axes[1].set_title('振幅衰减 Amplitude Decay')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/tmp/impulse_response.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: /tmp/impulse_response.png")
    plt.close()

    return f_n


def example_frequency_sweep():
    """频率扫描分析"""
    print("\n" + "=" * 60)
    print("频率扫描分析 / Frequency Sweep Analysis")
    print("=" * 60)

    mass = 1.0
    stiffness = 100.0
    damping = 2.0

    f_n = natural_frequency_hz(stiffness, mass)
    resonance_freq = find_resonance_frequency(stiffness, mass, damping)
    Q = quality_factor(damping / (2 * mass * np.sqrt(stiffness / mass)))

    print(f"\n固有频率 Natural Frequency: {f_n:.4f} Hz")
    print(f"共振频率 Resonance Frequency: {resonance_freq:.4f} Hz")
    print(f"品质因数 Quality Factor Q: {Q:.2f}")

    # 频率扫描
    freq_range = np.linspace(0.1, 20, 2000)

    # 位移FRF
    disp_frf = displacement_frf(stiffness, mass, damping, freq_range)
    vel_frf = velocity_frf(stiffness, mass, damping, freq_range)
    acc_frf = acceleration_frf(stiffness, mass, damping, freq_range)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 位移FRF
    axes[0, 0].semilogy(freq_range, np.abs(disp_frf.magnitude), 'b-', linewidth=1.5)
    axes[0, 0].axvline(x=f_n, color='r', linestyle='--', alpha=0.7, label=f'f_n = {f_n:.2f} Hz')
    axes[0, 0].axvline(x=resonance_freq, color='g', linestyle='--', alpha=0.7,
                      label=f'f_r = {resonance_freq:.2f} Hz')
    axes[0, 0].set_xlabel('频率 Frequency (Hz)')
    axes[0, 0].set_ylabel('幅值 Magnitude (log)')
    axes[0, 0].set_title('位移频响函数 Displacement FRF')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 速度FRF
    axes[0, 1].semilogy(freq_range, np.abs(vel_frf.magnitude), 'r-', linewidth=1.5)
    axes[0, 1].axvline(x=f_n, color='k', linestyle='--', alpha=0.5)
    axes[0, 1].set_xlabel('频率 Frequency (Hz)')
    axes[0, 1].set_ylabel('幅值 Magnitude (log)')
    axes[0, 1].set_title('速度频响函数 Velocity FRF')
    axes[0, 1].grid(True, alpha=0.3)

    # 加速度FRF
    axes[1, 0].semilogy(freq_range, np.abs(acc_frf.magnitude), 'g-', linewidth=1.5)
    axes[1, 0].axvline(x=f_n, color='k', linestyle='--', alpha=0.5)
    axes[1, 0].set_xlabel('频率 Frequency (Hz)')
    axes[1, 0].set_ylabel('幅值 Magnitude (log)')
    axes[1, 0].set_title('加速度频响函数 Acceleration FRF')
    axes[1, 0].grid(True, alpha=0.3)

    # Nyquist图
    nyquist = plot_frf_nyquist(disp_frf)
    axes[1, 1].plot(nyquist['real_part'], nyquist['imag_part'], 'b-', linewidth=1.0)
    axes[1, 1].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[1, 1].axvline(x=0, color='k', linestyle='--', alpha=0.3)
    axes[1, 1].set_xlabel('实部 Real Part')
    axes[1, 1].set_ylabel('虚部 Imaginary Part')
    axes[1, 1].set_title('Nyquist图 Nyquist Plot')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].set_aspect('equal')

    plt.tight_layout()
    plt.savefig('/tmp/frequency_sweep.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: /tmp/frequency_sweep.png")
    plt.close()


def example_resonance_avoidance():
    """共振避免设计示例"""
    print("\n" + "=" * 60)
    print("共振避免设计 / Resonance Avoidance Design")
    print("=" * 60)

    mass = 1.0
    stiffness = 100.0
    forcing_freq_range = (3.0, 7.0)
    margin = 0.2

    f_n = natural_frequency_hz(stiffness, mass)
    safety = resonance_safety_margin(5.0, f_n, 0.01)

    print(f"\n当前系统 Current System:")
    print(f"  固有频率 Natural Frequency: {f_n:.4f} Hz")
    print(f"  激励频率范围 Forcing Range: {forcing_freq_range} Hz")
    print(f"  安全裕度 Safety Margin: {safety:.4f}")

    if is_near_resonance(5.0, f_n):
        print(f"  警告: 接近共振! Warning: Near resonance!")

    # 设计建议
    design = avoid_resonance_design(stiffness, mass, forcing_freq_range, margin)
    print(f"\n设计建议 Design Recommendations:")
    print(f"  提高固有频率方案 (Increase freq):")
    print(f"    目标频率: {design['option_increase_freq']['target_freq_hz']:.2f} Hz")
    print(f"    所需刚度: {design['option_increase_freq']['required_stiffness_Nm']:.2f} N/m")
    print(f"    刚度变化: {design['option_increase_freq']['stiffness_change_ratio']:.2f}x")

    print(f"  降低固有频率方案 (Decrease freq):")
    print(f"    目标频率: {design['option_decrease_freq']['target_freq_hz']:.2f} Hz")
    print(f"    所需刚度: {design['option_decrease_freq']['required_stiffness_Nm']:.2f} N/m")
    print(f"    刚度变化: {design['option_decrease_freq']['stiffness_change_ratio']:.2f}x")


def is_near_resonance(forcing_freq, natural_freq, tolerance=0.1):
    """判断是否接近共振"""
    if natural_freq < 1e-10:
        return False
    return abs(forcing_freq - natural_freq) / natural_freq < tolerance


def main():
    """主函数 / Main function"""
    print("=" * 60)
    print("强迫振动响应演示 / Forced Vibration Response Demo")
    print("=" * 60)

    f_n = example_harmonic_response()
    f_n = example_step_response()
    f_n = example_impulse_response()
    example_frequency_sweep()
    example_resonance_avoidance()

    print("\n" + "=" * 60)
    print("演示完成! / Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
