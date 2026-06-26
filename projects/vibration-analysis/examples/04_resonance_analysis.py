"""
Resonance Analysis Demo
共振分析演示

This example demonstrates resonance phenomena and analysis:
- Resonance curve identification
- Quality factor measurement
- Bandwidth analysis
- Resonance hazard assessment
- Design recommendations
"""

import numpy as np
import matplotlib.pyplot as plt

from src.free_vibration import natural_frequency_hz, damping_ratio
from src.forced_vibration import harmonic_force_response, frequency_response_function
from src.frequency_response import displacement_frf, velocity_frf, acceleration_frf
from src.resonance import (
    find_resonance_frequency,
    quality_factor,
    detect_resonance_peaks,
    resonance_amplification,
    half_power_bandwidth,
    avoid_resonance_design,
    is_near_resonance,
)


def example_resonance_curves():
    """共振曲线示例"""
    print("=" * 60)
    print("共振曲线 / Resonance Curves")
    print("=" * 60)

    mass = 1.0
    stiffness = 100.0
    f_n = natural_frequency_hz(stiffness, mass)

    print(f"\n系统参数 System Parameters:")
    print(f"  质量 Mass: {mass} kg")
    print(f"  刚度 Stiffness: {stiffness} N/m")
    print(f"  固有频率 Natural Frequency: {f_n:.4f} Hz")

    # 不同阻尼比的共振曲线
    damping_values = [0.0, 0.5, 1.0, 2.0, 5.0, 10.0]
    freq_range = np.linspace(0.1, 20, 3000)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 幅频特性
    for damping in damping_values:
        zeta = damping_ratio(damping, stiffness, mass)
        frf = displacement_frf(stiffness, mass, damping, freq_range)
        label = f'c={diameter} (zeta={zeta:.3f})' if damping != 0 else '无阻尼 Undamped'
        label = f'c={damping} (zeta={zeta:.3f})'
        axes[0, 0].plot(frf.frequency, frf.magnitude, linewidth=1.5, label=label)

    axes[0, 0].axvline(x=f_n, color='k', linestyle='--', alpha=0.5, label=f'f_n = {f_n:.2f} Hz')
    axes[0, 0].set_xlabel('频率 Frequency (Hz)')
    axes[0, 0].set_ylabel('幅值 Magnitude')
    axes[0, 0].set_title('位移频响位移 FRF Magnitude')
    axes[0, 0].legend(fontsize=8)
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].set_ylim(0, None)

    # 相频特性
    for damping in damping_values:
        zeta = damping_ratio(damping, stiffness, mass)
        frf = displacement_frf(stiffness, mass, damping, freq_range)
        label = f'c={damping}' if damping != 0 else 'Undamped'
        axes[0, 1].plot(frf.frequency, np.degrees(frf.phase), linewidth=1.5, label=label)

    axes[0, 1].axvline(x=f_n, color='k', linestyle='--', alpha=0.5)
    axes[0, 1].set_xlabel('频率 Frequency (Hz)')
    axes[0, 1].set_ylabel('相位 Phase (deg)')
    axes[0, 1].set_title('位移频响相位 FRF Phase')
    axes[0, 1].legend(fontsize=8)
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_ylim(-180, 10)

    # Q因子与阻尼比关系
    zeta_values = np.linspace(0.001, 0.5, 500)
    Q_values = [quality_factor(z) for z in zeta_values]
    axes[1, 0].plot(zeta_values, Q_values, 'b-', linewidth=2)
    axes[1, 0].axvline(x=0.05, color='r', linestyle='--', alpha=0.5, label='zeta = 0.05')
    axes[1, 0].axhline(y=10, color='g', linestyle='--', alpha=0.5, label='Q = 10')
    axes[1, 0].set_xlabel('阻尼比 Damping Ratio zeta')
    axes[1, 0].set_ylabel('品质因数 Quality Factor Q')
    axes[1, 0].set_title('Q因子与阻尼比 Q vs Damping Ratio')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_yscale('log')

    # 共振放大倍数
    amplification_values = []
    zeta_plot = []
    for damping in damping_values:
        zeta = damping_ratio(damping, stiffness, mass)
        amp = resonance_amplification(stiffness, mass, damping)
        amplification_values.append(amp)
        zeta_plot.append(zeta)

    axes[1, 1].bar([str(d) for d in damping_values], amplification_values,
                   color=['blue', 'steelblue', 'skyblue', 'lightblue', 'cyan', 'lightcyan'])
    axes[1, 1].set_xlabel('阻尼系数 Damping c (N*s/m)')
    axes[1, 1].set_ylabel('共振放大倍数 Resonance Amplification')
    axes[1, 1].set_title('共振放大倍数 vs 阻尼系数')
    axes[1, 1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('/tmp/resonance_curves.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: /tmp/resonance_curves.png")
    plt.close()


def example_resonance_peak_detection():
    """共振峰检测示例"""
    print("\n" + "=" * 60)
    print("共振峰检测 / Resonance Peak Detection")
    print("=" * 60)

    mass = 1.0
    stiffness = 100.0
    freq_range = np.linspace(0.1, 20, 5000)

    print(f"\n固有频率 Natural Frequency: {natural_frequency_hz(stiffness, mass):.4f} Hz")

    for damping in [0.5, 1.0, 2.0, 5.0]:
        zeta = damping_ratio(damping, stiffness, mass)
        print(f"\n阻尼 c={diameter} N*s/m (zeta={zeta:.4f}):")

        peaks = detect_resonance_peaks(stiffness, mass, damping, freq_range)
        resonance_freq = find_resonance_frequency(stiffness, mass, damping)
        Q = quality_factor(zeta)
        amp = resonance_amplification(stiffness, mass, damping)

        print(f"  共振频率 Resonance Freq: {resonance_freq:.4f} Hz")
        print(f"  Q因子 Quality Factor: {Q:.2f}")
        print(f"  放大倍数 Amplification: {amp:.2f}x")

        for peak in peaks:
            print(f"  检测峰 Detected peak:")
            print(f"    频率: {peak.frequency_hz:.4f} Hz")
            print(f"    幅值: {peak.amplitude:.4f}")
            print(f"    带宽: {peak.bandwidth_hz:.4f} Hz")


def example_resonance_harmonic_response():
    """共振时简谐响应示例"""
    print("\n" + "=" * 60)
    print("共振时简谐响应 / Harmonic Response at Resonance")
    print("=" * 60)

    mass = 1.0
    stiffness = 100.0

    f_n = natural_frequency_hz(stiffness, mass)

    # 不同阻尼比在共振时的响应
    damping_values = [0.5, 1.0, 2.0, 5.0]
    duration = 10.0

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for damping in damping_values:
        zeta = damping_ratio(damping, stiffness, mass)
        resonance_freq = find_resonance_frequency(stiffness, mass, damping)

        response = harmonic_force_response(
            stiffness, mass, damping,
            force_amplitude=10.0,
            forcing_freq=resonance_freq,
            duration=duration,
            num_points=5000,
        )

        label = f'c={damping} (zeta={zeta:.3f})'
        axes[0].plot(response.time, response.displacement, linewidth=1.5, label=label)

    axes[0].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[0].set_xlabel('时间 Time (s)')
    axes[0].set_ylabel('位移 Displacement (m)')
    axes[0].set_title('共振时响应 Response at Resonance')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # 稳态幅值对比
    steady_amps = []
    for damping in damping_values:
        zeta = damping_ratio(damping, stiffness, mass)
        resonance_freq = find_resonance_frequency(stiffness, mass, damping)
        amp = steady_state_amplitude(stiffness, mass, damping, resonance_freq)
        static_disp = 10.0 / stiffness
        steady_amps.append(amp * static_disp)

    axes[1].bar([str(d) for d in damping_values], steady_amps,
               color=['blue', 'steelblue', 'skyblue', 'lightblue'])
    axes[1].set_xlabel('阻尼系数 Damping c (N*s/m)')
    axes[1].set_ylabel('稳态幅值 Steady-state Amplitude (m)')
    axes[1].set_title('共振幅值 vs 阻尼系数')
    axes[1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('/tmp/resonance_response.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: /tmp/resonance_response.png")
    plt.close()


def steady_state_amplitude(stiffness, mass, damping, forcing_freq):
    """计算稳态幅值放大因子"""
    from src.forced_vibration import steady_state_amplitude as ssa
    return ssa(stiffness, mass, damping, forcing_freq)


def example_bandwidth_analysis():
    """带宽分析示例"""
    print("\n" + "=" * 60)
    print("带宽分析 / Bandwidth Analysis")
    print("=" * 60)

    mass = 1.0
    stiffness = 100.0
    freq_range = np.linspace(0.1, 20, 5000)

    print(f"\n固有频率 Natural Frequency: {natural_frequency_hz(stiffness, mass):.4f} Hz")

    for damping in [0.5, 1.0, 2.0]:
        zeta = damping_ratio(damping, stiffness, mass)
        frf = displacement_frf(stiffness, mass, damping, freq_range)

        # 找到峰值
        peak_idx = np.argmax(frf.magnitude)
        peak_freq = frf.frequency[peak_idx]
        peak_amp = frf.magnitude[peak_idx]

        # 带宽
        bw = half_power_bandwidth(frf.magnitude, frf.frequency, peak_idx)

        # 理论带宽
        theoretical_bw = 2 * zeta * natural_frequency_hz(stiffness, mass)

        print(f"\n阻尼 c={diameter} N*s/m (zeta={zeta:.4f}):")
        print(f"  峰值频率 Peak Freq: {peak_freq:.4f} Hz")
        print(f"  峰值幅值 Peak Amp: {peak_amp:.4f}")
        print(f"  半功率带宽 Half-power BW: {bw:.4f} Hz")
        print(f"  理论带宽 Theoretical BW: {theoretical_bw:.4f} Hz")
        print(f"  Q因子: {quality_factor(zeta):.2f}")


def example_resonance_design():
    """共振设计示例"""
    print("\n" + "=" * 60)
    print("共振设计 / Resonance Design")
    print("=" * 60)

    mass = 1.0
    stiffness = 100.0
    forcing_freq_range = (3.0, 8.0)

    f_n = natural_frequency_hz(stiffness, mass)
    print(f"\n当前系统 Current System:")
    print(f"  固有频率 Natural Frequency: {f_n:.4f} Hz")
    print(f"  激励范围 Forcing Range: {forcing_freq_range} Hz")

    # 检查是否接近共振
    for f_forcing in forcing_freq_range:
        near = is_near_resonance(f_forcing, f_n)
        margin = resonance_safety_margin(f_forcing, f_n, 0.01)
        print(f"  f={f_forcing} Hz: 接近共振={near}, 安全裕度={margin:.4f}")

    # 设计建议
    design = avoid_resonance_design(stiffness, mass, forcing_freq_range, 0.2)
    print(f"\n设计建议 Design Recommendations:")
    print(f"  提高固有频率方案:")
    print(f"    目标频率: {design['option_increase_freq']['target_freq_hz']:.2f} Hz")
    print(f"    所需刚度: {design['option_increase_freq']['required_stiffness_Nm']:.2f} N/m")
    print(f"    刚度变化: {design['option_increase_freq']['stiffness_change_ratio']:.2f}x")
    print(f"  降低固有频率方案:")
    print(f"    目标频率: {design['option_decrease_freq']['target_freq_hz']:.2f} Hz")
    print(f"    所需刚度: {design['option_decrease_freq']['required_stiffness_Nm']:.2f} N/m")
    print(f"    刚度变化: {design['option_decrease_freq']['stiffness_change_ratio']:.2f}x")


def main():
    """主函数 / Main function"""
    print("=" * 60)
    print("共振分析演示 / Resonance Analysis Demo")
    print("=" * 60)

    example_resonance_curves()
    example_resonance_peak_detection()
    example_resonance_harmonic_response()
    example_bandwidth_analysis()
    example_resonance_design()

    print("\n" + "=" * 60)
    print("演示完成! / Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
