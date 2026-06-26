"""
Spring-Mass System Simulation
弹簧-质量系统仿真

This example demonstrates free and forced vibration of spring-mass systems.
It covers:
- Single degree-of-freedom (SDOF) system
- Undamped and damped free vibration
- Forced vibration response
- Resonance phenomenon
"""

import numpy as np
import matplotlib.pyplot as plt

from src.free_vibration import (
    natural_frequency,
    natural_frequency_hz,
    damping_ratio,
    free_vibration_undamped,
    free_vibration_damped,
    logarithmic_decrement,
    estimate_damping_from_decrement,
)
from src.forced_vibration import (
    harmonic_force_response,
    step_force_response,
    frequency_response_function,
)
from src.resonance import (
    find_resonance_frequency,
    quality_factor,
    detect_resonance_peaks,
)
from src.multi_dof import (
    build_spring_mass_matrices,
    create_mdof_system,
    mdof_free_vibration,
    modal_analysis,
)


def plot_spring_mass_system():
    """绘制弹簧-质量系统示意图"""
    fig, ax = plt.subplots(figsize=(10, 4))

    # 弹簧绘制
    n_coils = 12
    spring_start = 1.0
    spring_end = 4.0
    amplitude = 0.3
    x_spring = np.linspace(spring_start, spring_end, n_coils * 10)
    y_spring = amplitude * np.sin(n_coils * np.pi * (x_spring - spring_start) / (spring_end - spring_start))

    ax.plot(x_spring, y_spring, 'b-', linewidth=2, label='弹簧 Spring')
    ax.plot([spring_end, spring_end + 0.8], [0, 0], 'k-', linewidth=3)  # 质量块

    # 质量块
    rect = plt.Rectangle((spring_end + 0.8, -0.3), 0.8, 0.6,
                         facecolor='gray', edgecolor='black', linewidth=2)
    ax.add_patch(rect)
    ax.text(spring_end + 1.2, 0, f'm = {1.0} kg', ha='center', va='center', fontsize=12)

    # 固定端
    ax.plot([spring_start, spring_start], [-0.5, 0.5], 'k-', linewidth=4)
    for x in [spring_start]:
        for y in np.linspace(-0.5, 0.5, 5):
            ax.plot([x - 0.1, x], [y, y + 0.1], 'k-', linewidth=1)

    # 地面
    ax.plot([0, 5], [-0.8, -0.8], 'k-', linewidth=2)
    for x in np.linspace(0, 5, 11):
        ax.plot([x, x - 0.05], [-0.8, -0.9], 'k-', linewidth=1)

    ax.set_xlim(0, 5)
    ax.set_ylim(-1.2, 1.0)
    ax.set_aspect('equal')
    ax.set_xlabel('位置 Position (m)', fontsize=12)
    ax.set_ylabel('位移 Displacement (m)', fontsize=12)
    ax.set_title('弹簧-质量系统 Spring-Mass System', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()
    plt.savefig('/tmp/spring_mass_diagram.png', dpi=150, bbox_inches='tight')
    print("系统示意图已保存: /tmp/spring_mass_diagram.png")
    plt.close()


def example_1d_free_vibration():
    """示例1: 单自由度自由振动"""
    print("=" * 60)
    print("示例1: 单自由度自由振动 / SDOF Free Vibration")
    print("=" * 60)

    # 系统参数
    mass = 1.0  # kg
    stiffness = 100.0  # N/m
    damping = 2.0  # N*s/m

    # 固有频率
    omega_n = natural_frequency(stiffness, mass)
    f_n = natural_frequency_hz(stiffness, mass)
    print(f"\n固有频率 Natural Frequency:")
    print(f"  omega_n = {omega_n:.4f} rad/s")
    print(f"  f_n = {f_n:.4f} Hz")

    # 阻尼比
    zeta = damping_ratio(damping, stiffness, mass)
    print(f"\n阻尼比 Damping Ratio:")
    print(f"  zeta = {zeta:.4f}")
    if zeta < 1:
        print(f"  系统类型: 欠阻尼 (Underdamped)")
    elif zeta == 1:
        print(f"  系统类型: 临界阻尼 (Critically Damped)")
    else:
        print(f"  系统类型: 过阻尼 (Overdamped)")

    # 无阻尼自由振动
    undamped = free_vibration_undamped(stiffness, mass, initial_displacement=1.0, duration=5.0)
    print(f"\n无阻尼振动 Undamped Free Vibration:")
    print(f"  固有频率: {undamped.natural_freq_hz:.4f} Hz")
    print(f"  最大位移: {np.max(np.abs(undamped.displacement)):.4f} m")

    # 有阻尼自由振动
    damped = free_vibration_damped(stiffness, mass, damping, initial_displacement=1.0, duration=5.0)
    print(f"\n有阻尼振动 Damped Free Vibration:")
    print(f"  固有频率: {damped.natural_freq_hz:.4f} Hz")
    print(f"  阻尼比: {damped.damping_ratio:.4f}")
    print(f"  最大位移: {np.max(np.abs(damped.displacement)):.4f} m")
    print(f"  5秒后位移: {damped.displacement[-1]:.6f} m")

    # 对数衰减率
    try:
        delta = logarithmic_decrement(damped)
        estimated_zeta = estimate_damping_from_decrement(delta)
        print(f"\n对数衰减率 Logarithmic Decrement:")
        print(f"  delta = {delta:.4f}")
        print(f"  估计阻尼比 estimated zeta = {estimated_zeta:.4f}")
        print(f"  实际阻尼比 actual zeta = {zeta:.4f}")
    except ValueError as e:
        print(f"\n无法计算对数衰减率: {e}")

    # 绘图
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 位移对比
    axes[0, 0].plot(undamped.time, undamped.displacement, 'b-', linewidth=1.5, label='无阻尼 Undamped')
    axes[0, 0].plot(damped.time, damped.displacement, 'r-', linewidth=1.5, label='有阻尼 Damped')
    axes[0, 0].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[0, 0].set_xlabel('时间 Time (s)')
    axes[0, 0].set_ylabel('位移 Displacement (m)')
    axes[0, 0].set_title('自由振动位移对比 Free Vibration Displacement')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 速度对比
    axes[0, 1].plot(undamped.time, undamped.velocity, 'b-', linewidth=1.5, label='无阻尼 Undamped')
    axes[0, 1].plot(damped.time, damped.velocity, 'r-', linewidth=1.5, label='有阻尼 Damped')
    axes[0, 1].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[0, 1].set_xlabel('时间 Time (s)')
    axes[0, 1].set_ylabel('速度 Velocity (m/s)')
    axes[0, 1].set_title('自由振动速度对比 Free Vibration Velocity')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # 加速度对比
    axes[1, 0].plot(undamped.time, undamped.acceleration, 'b-', linewidth=1.5, label='无阻尼 Undamped')
    axes[1, 0].plot(damped.time, damped.acceleration, 'r-', linewidth=1.5, label='有阻尼 Damped')
    axes[1, 0].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[1, 0].set_xlabel('时间 Time (s)')
    axes[1, 0].set_ylabel('加速度 Acceleration (m/s^2)')
    axes[1, 0].set_title('自由振动加速度对比 Free Vibration Acceleration')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # 振幅衰减曲线
    axes[1, 1].plot(damped.time, np.abs(damped.displacement), 'r-', linewidth=1.5, label='位移幅值')
    # 包络线
    envelope = 1.0 * np.exp(-zeta * omega_n * damped.time / 2)
    axes[1, 1].plot(damped.time, envelope, 'r--', linewidth=1, alpha=0.7, label='包络线 Envelope')
    axes[1, 1].plot(damped.time, -envelope, 'r--', linewidth=1, alpha=0.7)
    axes[1, 1].set_xlabel('时间 Time (s)')
    axes[1, 1].set_ylabel('振幅 Amplitude (m)')
    axes[1, 1].set_title('振幅衰减 Amplitude Decay')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/tmp/1d_free_vibration.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: /tmp/1d_free_vibration.png")
    plt.close()

    return damped


def example_forced_vibration():
    """示例2: 强迫振动"""
    print("\n" + "=" * 60)
    print("示例2: 强迫振动 / Forced Vibration")
    print("=" * 60)

    mass = 1.0
    stiffness = 100.0
    damping = 2.0

    # 固有频率
    f_n = natural_frequency_hz(stiffness, mass)
    print(f"\n固有频率 Natural Frequency: {f_n:.4f} Hz")

    # 简谐激励
    forcing_freq = f_n * 0.5  # 激励频率 = 0.5 * 固有频率
    harmonic = harmonic_force_response(
        stiffness, mass, damping,
        force_amplitude=10.0,
        forcing_freq=forcing_freq,
        duration=5.0,
    )
    print(f"\n简谐激励 Harmonic Excitation:")
    print(f"  激励频率 Forcing Frequency: {forcing_freq:.4f} Hz")
    print(f"  力幅值 Force Amplitude: {10.0} N")
    print(f"  最大位移 Max Displacement: {np.max(np.abs(harmonic.displacement)):.4f} m")

    # 阶跃激励
    step = step_force_response(
        stiffness, mass, damping,
        force_magnitude=10.0,
        duration=5.0,
    )
    static_disp = 10.0 / stiffness  # 静态位移
    print(f"\n阶跃激励 Step Excitation:")
    print(f"  力幅值 Force Magnitude: {10.0} N")
    print(f"  静态位移 Static Displacement: {static_disp:.4f} m")
    print(f"  最大位移 Max Displacement: {np.max(np.abs(step.displacement)):.4f} m")
    print(f"  稳态位移 Steady-state: {step.displacement[-1]:.4f} m")

    # 频响函数
    freq_range = np.linspace(0.1, 30, 1000)
    frf = frequency_response_function(stiffness, mass, damping, freq_range)

    # 共振频率
    resonance_freq = find_resonance_frequency(stiffness, mass, damping)
    Q = quality_factor(damping_ratio(damping, stiffness, mass))
    print(f"\n共振特性 Resonance Characteristics:")
    print(f"  共振频率 Resonance Frequency: {resonance_freq:.4f} Hz")
    print(f"  品质因数 Quality Factor Q: {Q:.2f}")

    # 绘图
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 简谐响应
    axes[0, 0].plot(harmonic.time, harmonic.displacement, 'b-', linewidth=1.5, label='位移 Displacement')
    axes[0, 0].plot(harmonic.time, harmonic.force / stiffness, 'r--', linewidth=1, alpha=0.5,
                    label='归一化力 F0/k')
    axes[0, 0].set_xlabel('时间 Time (s)')
    axes[0, 0].set_ylabel('位移 Displacement (m)')
    axes[0, 0].set_title('简谐激励响应 Harmonic Response')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # 阶跃响应
    axes[0, 1].plot(step.time, step.displacement, 'g-', linewidth=1.5, label='位移 Displacement')
    axes[0, 1].axhline(y=static_disp, color='r', linestyle='--', linewidth=1,
                       label=f'稳态值 Steady-state = {static_disp:.4f} m')
    axes[0, 1].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[0, 1].set_xlabel('时间 Time (s)')
    axes[0, 1].set_ylabel('位移 Displacement (m)')
    axes[0, 1].set_title('阶跃激励响应 Step Response')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # FRF 幅频特性
    axes[1, 0].plot(frf['freq'], frf['magnitude'], 'b-', linewidth=1.5)
    axes[1, 0].axvline(x=f_n, color='r', linestyle='--', alpha=0.7, label=f'固有频率 f_n = {f_n:.2f} Hz')
    axes[1, 0].axvline(x=resonance_freq, color='g', linestyle='--', alpha=0.7,
                      label=f'共振频率 f_r = {resonance_freq:.2f} Hz')
    axes[1, 0].set_xlabel('频率 Frequency (Hz)')
    axes[1, 0].set_ylabel('幅值 Magnitude')
    axes[1, 0].set_title('幅频特性 Frequency Response (Magnitude)')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_ylim(0, 10)

    # FRF 相频特性
    axes[1, 1].plot(frf['freq'], np.degrees(frf['phase']), 'purple', linewidth=1.5)
    axes[1, 1].axvline(x=f_n, color='r', linestyle='--', alpha=0.5)
    axes[1, 1].set_xlabel('频率 Frequency (Hz)')
    axes[1, 1].set_ylabel('相位 Phase (deg)')
    axes[1, 1].set_title('相频特性 Phase Response')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/tmp/forced_vibration.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: /tmp/forced_vibration.png")
    plt.close()

    return harmonic, step, frf


def example_resonance():
    """示例3: 共振分析"""
    print("\n" + "=" * 60)
    print("示例3: 共振分析 / Resonance Analysis")
    print("=" * 60)

    mass = 1.0
    stiffness = 100.0

    # 不同阻尼比的共振曲线
    damping_values = [0.0, 0.5, 1.0, 2.0, 5.0]
    freq_range = np.linspace(0.1, 20, 2000)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for damping in damping_values:
        if damping == 0:
            label = f'无阻尼 Undamped (c=0)'
        else:
            zeta = damping / (2 * mass * np.sqrt(stiffness / mass))
            label = f'c={diameter} N*s/m (zeta={zeta:.3f})' if damping != 2.0 else f'c={damping} N*s/m'
            label = f'c={damping} N*s/m (zeta={damping/(2*mass*np.sqrt(stiffness/mass)):.3f})'

        frf = frequency_response_function(stiffness, mass, damping, freq_range)
        axes[0].plot(frf['freq'], frf['magnitude'], linewidth=1.5, label=label)

    f_n = natural_frequency_hz(stiffness, mass)
    axes[0].axvline(x=f_n, color='k', linestyle='--', alpha=0.5, label=f'固有频率 f_n = {f_n:.2f} Hz')
    axes[0].set_xlabel('频率 Frequency (Hz)')
    axes[0].set_ylabel('幅值 Magnitude')
    axes[0].set_title('不同阻尼比的共振曲线 Resonance Curves')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    axes[0].set_ylim(0, 15)

    # Q因子与阻尼比关系
    zeta_values = np.linspace(0.01, 0.5, 100)
    Q_values = [quality_factor(z) for z in zeta_values]
    axes[1].plot(zeta_values, Q_values, 'b-', linewidth=2)
    axes[1].axhline(y=10, color='r', linestyle='--', alpha=0.5, label='Q = 10')
    axes[1].axhline(y=1, color='g', linestyle='--', alpha=0.5, label='Q = 1')
    axes[1].set_xlabel('阻尼比 Damping Ratio zeta')
    axes[1].set_ylabel('品质因数 Quality Factor Q')
    axes[1].set_title('Q因子与阻尼比关系 Q vs Damping Ratio')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    axes[1].set_yscale('log')

    plt.tight_layout()
    plt.savefig('/tmp/resonance_analysis.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: /tmp/resonance_analysis.png")
    plt.close()

    # 共振峰检测
    for damping in [0.5, 1.0, 2.0]:
        peaks = detect_resonance_peaks(stiffness, mass, damping, freq_range)
        zeta = damping / (2 * mass * np.sqrt(stiffness / mass))
        print(f"\n阻尼 c={damping} N*s/m (zeta={zeta:.4f}):")
        for peak in peaks:
            print(f"  共振频率: {peak.frequency_hz:.4f} Hz")
            print(f"  幅值: {peak.amplitude:.4f}")
            print(f"  Q因子: {peak.quality_factor:.2f}")
            print(f"  带宽: {peak.bandwidth_hz:.4f} Hz")


def example_multidof():
    """示例4: 多自由度系统"""
    print("\n" + "=" * 60)
    print("示例4: 多自由度系统 / MDOF System")
    print("=" * 60)

    # 两自由度弹簧-质量系统
    # 固定端 - k1 - m1 - k2 - m2 - k3 - 固定端
    masses = [1.0, 2.0]
    springs = [(0, 1, 200.0)]  # m1 和 m2 之间的弹簧
    ground_springs = [(0, 100.0), (1, 150.0)]  # 接地弹簧

    mass_matrix, stiffness_matrix = build_spring_mass_matrices(masses, springs, ground_springs)
    print("\n质量矩阵 Mass Matrix:")
    print(mass_matrix)
    print("\n刚度矩阵 Stiffness Matrix:")
    print(stiffness_matrix)

    # 模态分析
    modal = modal_analysis(mass_matrix, stiffness_matrix)
    print("\n" + modal_analysis.summarize_modes(modal))

    # 验证正交性
    ortho = modal_analysis.verify_orthogonality(modal.mode_shapes, mass_matrix, stiffness_matrix)
    print(f"\n质量正交性验证 Mass Orthogonality (max off-diagonal): {ortho['mass_ortho_max_offdiag']:.2e}")
    print(f"刚度正交性验证 Stiffness Orthogonality (max off-diagonal): {ortho['stiff_ortho_max_offdiag']:.2e}")

    # 模态振型可视化
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for i in range(2):
        axes[i].bar([1, 2], modal.mode_shapes[:, i], color=['blue', 'red'][i], alpha=0.7)
        axes[i].set_xlabel('自由度 DOF')
        axes[i].set_ylabel('振型振幅 Mode Shape Amplitude')
        axes[i].set_title(f'第{i+1}阶模态 Mode {i+1}\n'
                         f'频率: {modal.natural_freq_hz[i]:.2f} Hz')
        axes[i].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/tmp/mdof_modes.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: /tmp/mdof_modes.png")
    plt.close()

    # MDOF 自由振动
    system = create_mdof_system(mass_matrix, stiffness_matrix,
                                damping_matrix=np.zeros((2, 2)),
                                system_name="Two-DOF Spring-Mass")

    initial_disp = np.array([1.0, 0.5])
    initial_vel = np.array([0.0, 0.0])
    time = np.linspace(0, 5, 2000)

    response = mdof_free_vibration(system, initial_disp, initial_vel, time)

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    axes[0].plot(time, response[:, 0], 'b-', linewidth=1.5, label='质量1 Mass 1')
    axes[0].set_xlabel('时间 Time (s)')
    axes[0].set_ylabel('位移1 Displacement 1 (m)')
    axes[0].set_title('多自由度自由振动 MDOF Free Vibration - Mass 1')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(time, response[:, 1], 'r-', linewidth=1.5, label='质量2 Mass 2')
    axes[1].set_xlabel('时间 Time (s)')
    axes[1].set_ylabel('位移2 Displacement 2 (m)')
    axes[1].set_title('多自由度自由振动 MDOF Free Vibration - Mass 2')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    plt.tight_layout()
    plt.savefig('/tmp/mdof_response.png', dpi=150, bbox_inches='tight')
    print("图表已保存: /tmp/mdof_response.png")
    plt.close()


def main():
    """主函数 / Main function"""
    print("=" * 60)
    print("弹簧-质量系统仿真 / Spring-Mass System Simulation")
    print("=" * 60)

    # 系统示意图
    plot_spring_mass_system()

    # 示例1: 自由振动
    example_1d_free_vibration()

    # 示例2: 强迫振动
    example_forced_vibration()

    # 示例3: 共振分析
    example_resonance()

    # 示例4: 多自由度系统
    example_multidof()

    print("\n" + "=" * 60)
    print("仿真完成! / Simulation Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
