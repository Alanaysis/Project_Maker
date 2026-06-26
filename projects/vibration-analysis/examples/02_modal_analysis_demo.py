"""
Modal Analysis Demo
模态分析演示

This example demonstrates modal analysis for various systems:
- Single degree-of-freedom (SDOF) modal analysis
- Multi-degree-of-freedom (MDOF) modal analysis
- Mode shape visualization
- Modal orthogonality verification
- Modal superposition
"""

import numpy as np
import matplotlib.pyplot as plt

from src.modal_analysis import (
    modal_analysis,
    verify_orthogonality,
    modal_participation_factor,
    summarize_modes,
)
from src.multi_dof import (
    build_spring_mass_matrices,
    build_cantilever_beam_matrix,
    build_fixed_fixed_beam_matrix,
    create_mdof_system,
    mdof_free_vibration,
)
from src.free_vibration import natural_frequency_hz


def demo_sdof_modal():
    """单自由度模态分析演示"""
    print("=" * 60)
    print("单自由度模态分析 / SDOF Modal Analysis")
    print("=" * 60)

    mass = 1.0
    stiffness = 100.0
    damping = 2.0

    # SDOF 系统矩阵
    mass_matrix = np.array([[mass]])
    stiffness_matrix = np.array([[stiffness]])
    damping_matrix = np.array([[damping]])

    # 模态分析
    modal = modal_analysis(mass_matrix, stiffness_matrix, damping_matrix)

    print(f"\n固有频率: {modal.natural_freq_hz[0]:.4f} Hz")
    print(f"固有频率 (rad/s): {modal.natural_freq_rad[0]:.4f} rad/s")
    print(f"模态振型: {modal.mode_shapes[:, 0]}")
    print(f"阻尼比: {modal.damping_ratios[0]:.4f}")

    return modal


def demo_two_dof_modal():
    """两自由度模态分析演示"""
    print("\n" + "=" * 60)
    print("两自由度模态分析 / Two-DOF Modal Analysis")
    print("=" * 60)

    # 两自由度系统: 固定端 - k1 - m1 - k2 - m2 - k3 - 固定端
    masses = [1.0, 2.0]
    springs = [(0, 1, 200.0)]
    ground_springs = [(0, 100.0), (1, 150.0)]

    mass_matrix, stiffness_matrix = build_spring_mass_matrices(masses, springs, ground_springs)

    print("\n质量矩阵:")
    print(mass_matrix)
    print("\n刚度矩阵:")
    print(stiffness_matrix)

    # 模态分析
    modal = modal_analysis(mass_matrix, stiffness_matrix)

    # 摘要
    print("\n" + summarize_modes(modal))

    # 验证正交性
    ortho = verify_orthogonality(modal.mode_shapes, mass_matrix, stiffness_matrix)
    print(f"\n质量正交性验证 (最大非对角元): {ortho['mass_ortho_max_offdiag']:.2e}")
    print(f"刚度正交性验证 (最大非对角元): {ortho['stiff_ortho_max_offdiag']:.2e}")

    # 模态振型可视化
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # 模态振型
    for i in range(2):
        axes[i].bar([1, 2], modal.mode_shapes[:, i],
                   color=['blue', 'red'][i], alpha=0.7, edgecolor='black', linewidth=1.5)
        axes[i].axhline(y=0, color='k', linestyle='--', alpha=0.3)
        axes[i].set_xlabel('自由度 DOF')
        axes[i].set_ylabel('振型振幅 Mode Shape')
        axes[i].set_title(f'第{i+1}阶模态 Mode {i+1}\nf = {modal.natural_freq_hz[i]:.2f} Hz')
        axes[i].grid(True, alpha=0.3)

    # 模态振型图 (条形图)
    axes[2].bar([1, 2], modal.mode_shapes[:, 0], color='blue', alpha=0.7, label='Mode 1')
    axes[2].bar([3, 4], modal.mode_shapes[:, 1], color='red', alpha=0.7, label='Mode 2')
    axes[2].set_xlabel('自由度 DOF')
    axes[2].set_ylabel('振型振幅 Mode Shape')
    axes[2].set_title('模态振型对比 Mode Shapes Comparison')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/tmp/two_dof_modes.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: /tmp/two_dof_modes.png")
    plt.close()

    return modal, mass_matrix, stiffness_matrix


def demo_three_dof_modal():
    """三自由度模态分析演示"""
    print("\n" + "=" * 60)
    print("三自由度模态分析 / Three-DOF Modal Analysis")
    print("=" * 60)

    # 三自由度串联系统
    n_masses = 3
    masses_list = [1.0, 1.5, 2.0]
    spring_k = 100.0

    # 固定端 - k - m1 - k - m2 - k - m3 - k - 固定端
    springs = [(0, 1, spring_k), (1, 2, spring_k)]
    ground_springs = [(0, spring_k), (2, spring_k)]

    mass_matrix, stiffness_matrix = build_spring_mass_matrices(masses_list, springs, ground_springs)

    print("\n质量矩阵:")
    print(mass_matrix)
    print("\n刚度矩阵:")
    print(stiffness_matrix)

    # 模态分析
    modal = modal_analysis(mass_matrix, stiffness_matrix)

    print("\n" + summarize_modes(modal))

    # 模态振型可视化
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for i in range(3):
        axes[i].bar([1, 2, 3], modal.mode_shapes[:, i],
                   color=['blue', 'red', 'green'][i], alpha=0.7, edgecolor='black', linewidth=1.5)
        axes[i].axhline(y=0, color='k', linestyle='--', alpha=0.3)
        axes[i].set_xlabel('自由度 DOF')
        axes[i].set_ylabel('振型振幅 Mode Shape')
        axes[i].set_title(f'第{i+1}阶模态 Mode {i+1}\nf = {modal.natural_freq_hz[i]:.2f} Hz')
        axes[i].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/tmp/three_dof_modes.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: /tmp/three_dof_modes.png")
    plt.close()

    return modal, mass_matrix, stiffness_matrix


def demo_cantilever_beam():
    """悬臂梁模态分析演示"""
    print("\n" + "=" * 60)
    print("悬臂梁模态分析 / Cantilever Beam Modal Analysis")
    print("=" * 60)

    n_masses = 5
    mass = 0.5
    stiffness = 500.0

    mass_matrix, stiffness_matrix = build_cantilever_beam_matrix(n_masses, mass, stiffness)

    print(f"\n悬臂梁离散: {n_masses} 个质量块")
    print("固定端 |弹簧|质量|弹簧|质量|...|弹簧|质量|自由端")

    # 模态分析
    modal = modal_analysis(mass_matrix, stiffness_matrix)

    print("\n" + summarize_modes(modal))

    # 与理论值对比 (悬臂梁)
    print("\n理论近似 (悬臂梁):")
    for i in range(min(3, len(modal.natural_freq_hz))):
        # 悬臂梁第i阶固有频率近似: f_i = (beta_i*L)^2 / (2*pi) * sqrt(EI/rho*A)
        # 这里用离散模型的结果
        print(f"  第{i+1}阶: {modal.natural_freq_hz[i]:.2f} Hz")

    # 模态振型可视化
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for i in range(3):
        axes[i].bar(range(1, n_masses + 1), modal.mode_shapes[:, i],
                   color='steelblue', alpha=0.7, edgecolor='black', linewidth=1.5)
        axes[i].axhline(y=0, color='k', linestyle='--', alpha=0.3)
        axes[i].set_xlabel('质量块编号 Mass Block Index')
        axes[i].set_ylabel('振型振幅 Mode Shape')
        axes[i].set_title(f'第{i+1}阶模态 Mode {i+1}\nf = {modal.natural_freq_hz[i]:.2f} Hz')
        axes[i].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/tmp/cantilever_modes.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: /tmp/cantilever_modes.png")
    plt.close()

    return modal, mass_matrix, stiffness_matrix


def demo_modal_superposition():
    """模态叠加法演示"""
    print("\n" + "=" * 60)
    print("模态叠加法演示 / Modal Superposition Demo")
    print("=" * 60)

    # 两自由度系统
    masses = [1.0, 1.0]
    springs = [(0, 1, 100.0)]
    ground_springs = [(0, 50.0), (1, 50.0)]

    mass_matrix, stiffness_matrix = build_spring_mass_matrices(masses, springs, ground_springs)

    # 添加小阻尼
    damping_matrix = mass_matrix * 0.01 + stiffness_matrix * 0.005

    # 模态分析
    modal = modal_analysis(mass_matrix, stiffness_matrix, damping_matrix)
    print("\n" + summarize_modes(modal))

    # 创建系统
    system = create_mdof_system(
        mass_matrix, stiffness_matrix, damping_matrix,
        system_name="Two-DOF with Modal Superposition"
    )

    # 初始条件
    initial_disp = np.array([1.0, 0.0])
    initial_vel = np.array([0.0, 0.0])
    time = np.linspace(0, 10, 3000)

    # 自由振动响应
    response = mdof_free_vibration(system, initial_disp, initial_vel, time)

    # 绘图
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    axes[0].plot(time, response[:, 0], 'b-', linewidth=1.5, label='质量1 Mass 1')
    axes[0].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[0].set_xlabel('时间 Time (s)')
    axes[0].set_ylabel('位移1 Displacement 1 (m)')
    axes[0].set_title('模态叠加法响应 - 质量1 (初始位移在质量1上)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(time, response[:, 1], 'r-', linewidth=1.5, label='质量2 Mass 2')
    axes[1].axhline(y=0, color='k', linestyle='--', alpha=0.3)
    axes[1].set_xlabel('时间 Time (s)')
    axes[1].set_ylabel('位移2 Displacement 2 (m)')
    axes[1].set_title('模态叠加法响应 - 质量2 (初始位移在质量1上)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/tmp/modal_superposition.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: /tmp/modal_superposition.png")
    plt.close()


def demo_modal_participation():
    """模态参与系数演示"""
    print("\n" + "=" * 60)
    print("模态参与系数 / Modal Participation Factors")
    print("=" * 60)

    masses = [1.0, 1.0, 1.0]
    springs = [(0, 1, 100.0), (1, 2, 100.0)]
    ground_springs = [(0, 50.0)]

    mass_matrix, stiffness_matrix = build_spring_mass_matrices(masses, springs, ground_springs)
    modal = modal_analysis(mass_matrix, stiffness_matrix)

    print("\n" + summarize_modes(modal))

    # 不同方向的力
    force_dirs = [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]),
        np.array([0.0, 0.0, 1.0]),
        np.array([1.0, 1.0, 1.0]) / np.sqrt(3),
    ]
    force_labels = ['F1方向', 'F2方向', 'F3方向', '均匀方向']

    for f_dir, label in zip(force_dirs, force_labels):
        gamma = modal_participation_factor(modal.mode_shapes, mass_matrix, f_dir)
        print(f"\n{label} 力方向模态参与系数:")
        for i, g in enumerate(gamma):
            print(f"  模态{i+1}: Gamma = {g:.4f}")


def main():
    """主函数 / Main function"""
    print("=" * 60)
    print("模态分析演示 / Modal Analysis Demo")
    print("=" * 60)

    # 单自由度
    demo_sdof_modal()

    # 两自由度
    demo_two_dof_modal()

    # 三自由度
    demo_three_dof_modal()

    # 悬臂梁
    demo_cantilever_beam()

    # 模态叠加
    demo_modal_superposition()

    # 模态参与系数
    demo_modal_participation()

    print("\n" + "=" * 60)
    print("演示完成! / Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
