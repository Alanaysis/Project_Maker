"""
Modal Analysis Module
模态分析模块

This module implements modal analysis for multi-degree-of-freedom (MDOF) systems.
Modal analysis determines the natural frequencies and mode shapes of a system.

核心特征值问题: (K - omega^2 * M) * phi = 0

其中:
    K = 刚度矩阵 (stiffness matrix)
    M = 质量矩阵 (mass matrix)
    omega = 固有频率 (natural frequency)
    phi = 模态振型 (mode shape)

模态特性:
    1. 正交性 (Orthogonality): 不同模态之间关于 M 和 K 正交
    2. 归一化 (Normalization): 通常按模态质量归一化
    3. 完备性 (Completeness): 所有模态构成完备基
"""

import numpy as np
from scipy.linalg import eig, eigh
from typing import NamedTuple, Tuple, Callable


class ModalResult(NamedTuple):
    """模态分析结果 / Modal analysis result"""
    natural_freq_hz: np.ndarray  # 固有频率 (Hz)
    natural_freq_rad: np.ndarray  # 固有频率 (rad/s)
    mode_shapes: np.ndarray  # 模态振型矩阵 [n_modes x n_dof]
    damping_ratios: np.ndarray  # 各阶模态阻尼比
    modal_masses: np.ndarray  # 模态质量
    modal_stiffness: np.ndarray  # 模态刚度
    modal_damping: np.ndarray  # 模态阻尼


def modal_analysis(
    mass_matrix: np.ndarray,
    stiffness_matrix: np.ndarray,
    damping_matrix: np.ndarray = None,
) -> ModalResult:
    """
    执行模态分析 (modal analysis)

    求解广义特征值问题: (K - omega^2 * M) * phi = 0

    对于无阻尼系统，使用特征值分解:
        1. 求解 det(K - omega^2 * M) = 0
        2. 得到固有频率 omega_i 和模态振型 phi_i

    正交性验证:
        phi_i^T * M * phi_j = 0 (i != j)
        phi_i^T * K * phi_j = 0 (i != j)

    Args:
        mass_matrix: 质量矩阵 M (n x n), 对称正定
        stiffness_matrix: 刚度矩阵 K (n x n), 对称正定
        damping_matrix: 阻尼矩阵 C (n x n), 可选

    Returns:
        ModalResult 包含固有频率、模态振型、模态参数
    """
    if mass_matrix.shape[0] != mass_matrix.shape[1]:
        raise ValueError("质量矩阵必须是方阵 / Mass matrix must be square")
    if stiffness_matrix.shape != mass_matrix.shape:
        raise ValueError("刚度矩阵和质量矩阵维度不匹配 / Matrix dimension mismatch")

    n = mass_matrix.shape[0]

    # 使用 eigh 求解广义特征值问题 (对称矩阵)
    # K * phi = omega^2 * M * phi
    # 返回特征值 lamda = omega^2 和特征向量 phi
    eigenvalues, eigenvectors = eigh(stiffness_matrix, mass_matrix)

    # 固有频率 (rad/s) = sqrt(特征值)
    natural_freq_rad = np.sqrt(np.maximum(eigenvalues, 0))  # 防止负值

    # 固有频率 (Hz)
    natural_freq_hz = natural_freq_rad / (2 * np.pi)

    # 按频率从小到大排序
    sort_idx = np.argsort(natural_freq_hz)
    natural_freq_hz = natural_freq_hz[sort_idx]
    natural_freq_rad = natural_freq_rad[sort_idx]
    mode_shapes = eigenvectors[:, sort_idx]

    # 计算模态参数
    modal_masses = np.array([
        mode_shapes[:, i].T @ mass_matrix @ mode_shapes[:, i]
        for i in range(n)
    ])

    modal_stiffness = np.array([
        mode_shapes[:, i].T @ stiffness_matrix @ mode_shapes[:, i]
        for i in range(n)
    ])

    # 阻尼比
    if damping_matrix is not None:
        modal_damping = np.array([
            mode_shapes[:, i].T @ damping_matrix @ mode_shapes[:, i]
            for i in range(n)
        ])
        # 模态阻尼比: zeta_i = c_i / (2 * m_i * omega_i)
        modal_damping_ratios = np.array([
            modal_damping[i] / (2 * modal_masses[i] * natural_freq_rad[i])
            if natural_freq_rad[i] > 1e-10 else 0.0
            for i in range(n)
        ])
    else:
        modal_damping = np.zeros(n)
        modal_damping_ratios = np.zeros(n)

    return ModalResult(
        natural_freq_hz=natural_freq_hz,
        natural_freq_rad=natural_freq_rad,
        mode_shapes=mode_shapes,
        damping_ratios=modal_damping_ratios,
        modal_masses=modal_masses,
        modal_stiffness=modal_stiffness,
        modal_damping=modal_damping,
    )


def verify_orthogonality(mode_shapes: np.ndarray, mass_matrix: np.ndarray,
                         stiffness_matrix: np.ndarray) -> dict:
    """
    验证模态正交性 (verify modal orthogonality)

    模态关于质量矩阵和刚度矩阵的正交性:
        phi_i^T * M * phi_j = 0 (i != j)
        phi_i^T * K * phi_j = 0 (i != j)

    Args:
        mode_shapes: 模态振型矩阵 [n_modes x n_dof]
        mass_matrix: 质量矩阵
        stiffness_matrix: 刚度矩阵

    Returns:
        dict 包含质量正交性和刚度正交性的验证结果
    """
    n_modes = mode_shapes.shape[1]

    # 质量正交性
    m_orth = np.zeros((n_modes, n_modes))
    for i in range(n_modes):
        for j in range(n_modes):
            m_orth[i, j] = mode_shapes[:, i].T @ mass_matrix @ mode_shapes[:, j]

    # 刚度正交性
    k_orth = np.zeros((n_modes, n_modes))
    for i in range(n_modes):
        for j in range(n_modes):
            k_orth[i, j] = mode_shapes[:, i].T @ stiffness_matrix @ mode_shapes[:, j]

    return {
        "mass_orthogonality": m_orth,
        "stiffness_orthogonality": k_orth,
        "mass_ortho_max_offdiag": np.max(np.abs(m_orth - np.diag(np.diag(m_orth)))),
        "stiff_ortho_max_offdiag": np.max(np.abs(k_orth - np.diag(np.diag(k_orth)))),
    }


def modal_participation_factor(mode_shapes: np.ndarray, mass_matrix: np.ndarray,
                               force_direction: np.ndarray) -> np.ndarray:
    """
    计算模态参与系数 (modal participation factor)

    模态参与系数衡量各阶模态对给定方向激励的响应贡献:
        Gamma_i = phi_i^T * M * r

    其中 r 是力方向向量。

    Args:
        mode_shapes: 模态振型矩阵 [n_modes x n_dof]
        mass_matrix: 质量矩阵
        force_direction: 力方向向量

    Returns:
        模态参与系数向量
    """
    n_modes = mode_shapes.shape[1]
    gamma = np.zeros(n_modes)

    for i in range(n_modes):
        gamma[i] = mode_shapes[:, i].T @ mass_matrix @ force_direction

    return gamma


def modal_superposition_response(
    mass_matrix: np.ndarray,
    stiffness_matrix: np.ndarray,
    damping_matrix: np.ndarray,
    force_func: Callable[[float], np.ndarray],
    initial_displacement: np.ndarray,
    initial_velocity: np.ndarray,
    time: np.ndarray,
) -> np.ndarray:
    """
    模态叠加法计算响应 (modal superposition method)

    将物理坐标下的响应表示为模态坐标的线性组合:
        x(t) = sum_i phi_i * q_i(t)

    其中 q_i(t) 是第 i 阶模态的广义坐标，满足:
        q_i'' + 2*zeta_i*omega_i*q_i' + omega_i^2*q_i = Gamma_i * F(t) / M_i

    Args:
        mass_matrix: 质量矩阵
        stiffness_matrix: 刚度矩阵
        damping_matrix: 阻尼矩阵
        force_func: 外力函数 F(t) -> [n_dof]
        initial_displacement: 初始位移 [n_dof]
        initial_velocity: 初始速度 [n_dof]
        time: 时间数组

    Returns:
        位移响应 [n_time x n_dof]
    """
    n_dof = mass_matrix.shape[0]
    n_modes = min(n_dof, 20)  # 最多取前20阶模态

    # 模态分析
    modal = modal_analysis(mass_matrix, stiffness_matrix, damping_matrix)

    # 解耦为单自由度方程
    displacement = np.zeros((len(time), n_dof))

    # 初始条件的模态坐标
    modal_initial_disp = np.array([
        modal.mode_shapes[:, i].T @ mass_matrix @ initial_displacement
        for i in range(n_modes)
    ])
    modal_initial_vel = np.array([
        modal.mode_shapes[:, i].T @ mass_matrix @ initial_velocity
        for i in range(n_modes)
    ])

    # 模态质量
    modal_masses = modal.modal_masses[:n_modes]

    # 对每个模态求解
    for i in range(n_modes):
        omega_i = modal.natural_freq_rad[i]
        zeta_i = modal.damping_ratios[i]

        if omega_i < 1e-10:
            continue  # 刚体模态，跳过

        # 模态力参与系数
        # Gamma_i(t) = phi_i^T * F(t)
        # 这里 force_func 返回 [n_dof]，需要逐时刻计算
        # 为简化，假设力方向固定，力幅随时间变化
        # 实际应用中需要更复杂的处理

        # 使用数值积分求解每个模态
        from scipy.integrate import odeint

        def modal_ode(q_state, t):
            q, dq = q_state
            # 模态力 (简化: 假设力方向为单位向量)
            force_dir = np.ones(n_dof) / np.sqrt(n_dof)
            F_modal = modal.mode_shapes[:, i].T @ mass_matrix @ force_dir * 1.0
            F_t = force_func(t)
            F_modal = modal.mode_shapes[:, i].T @ mass_matrix @ F_t

            d2q = (F_modal - 2 * zeta_i * omega_i * dq - omega_i ** 2 * q) / modal_masses[i]
            return [dq, d2q]

        q0 = [modal_initial_disp[i], modal_initial_vel[i]]
        q_sol = odeint(modal_ode, q0, time)

        # 叠加模态响应
        for j, t_idx in enumerate(range(len(time))):
            displacement[t_idx, :] += modal.mode_shapes[:, i] * q_sol[t_idx, 0]

    return displacement


def summarize_modes(modal: ModalResult) -> str:
    """
    生成模态分析摘要报告

    Args:
        modal: 模态分析结果

    Returns:
        报告字符串
    """
    lines = [
        "=" * 60,
        "模态分析摘要报告 / Modal Analysis Summary",
        "=" * 60,
        f"自由度数量 (DOF): {len(modal.natural_freq_hz)}",
        f"总模态数 (Total modes): {len(modal.natural_freq_hz)}",
        "-" * 60,
        f"{'阶次':<6} {'频率 (Hz)':<15} {'阻尼比':<12} {'模态质量':<15}",
        "-" * 60,
    ]

    for i in range(len(modal.natural_freq_hz)):
        lines.append(
            f"{i+1:<6} {modal.natural_freq_hz[i]:<15.4f} "
            f"{modal.damping_ratios[i]:<12.4f} "
            f"{modal.modal_masses[i]:<15.4f}"
        )

    lines.append("-" * 60)
    lines.append("=" * 60)

    return "\n".join(lines)
