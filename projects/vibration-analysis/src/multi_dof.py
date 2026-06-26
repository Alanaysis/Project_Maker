"""
Multi-Degree-of-Freedom (MDOF) System Module
多自由度系统模块

This module implements MDOF vibration analysis, including:
- System matrix construction for spring-mass systems
- Free vibration analysis for MDOF systems
- Forced vibration analysis for MDOF systems
- Coupled and uncoupled equations of motion
"""

import numpy as np
from scipy.linalg import eig, eigh
from typing import List, Tuple, NamedTuple, Optional
from .modal_analysis import modal_analysis, ModalResult


class MDOFSystem(NamedTuple):
    """多自由度系统 / MDOF system"""
    mass_matrix: np.ndarray  # 质量矩阵 M
    damping_matrix: np.ndarray  # 阻尼矩阵 C
    stiffness_matrix: np.ndarray  # 刚度矩阵 K
    dof: int  # 自由度数量
    system_name: str = "MDOF System"


def build_spring_mass_matrices(
    masses: List[float],
    springs: List[Tuple[int, int, float]],
    ground_springs: Optional[List[Tuple[int, float]]] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    从弹簧-质量系统参数构建质量矩阵和刚度矩阵

    弹簧-质量系统:
    - masses: 质量列表 [m1, m2, ..., mn]
    - springs: 弹簧连接列表 [(node_i, node_j, k)]
        node_i, node_j 是连接该弹簧的两个节点索引
        k 是弹簧刚度
    - ground_springs: 接地弹簧 [(node_index, k)]

    刚度矩阵组装规则:
    - K[i,i] += k (连接节点 i 的弹簧刚度之和)
    - K[i,j] -= k (节点 i 和 j 之间的弹簧刚度)

    Args:
        masses: 质量列表
        springs: 弹簧连接列表
        ground_springs: 接地弹簧列表

    Returns:
        (mass_matrix, stiffness_matrix)
    """
    n = len(masses)

    # 质量矩阵 (对角矩阵)
    mass_matrix = np.diag(masses)

    # 刚度矩阵 (零矩阵开始)
    stiffness_matrix = np.zeros((n, n))

    # 组装弹簧连接
    for i, j, k in springs:
        if i < 0 or i >= n or j < 0 or j >= n:
            raise ValueError(f"弹簧连接索引超出范围: ({i}, {j})")
        if k <= 0:
            raise ValueError(f"弹簧刚度必须为正: k = {k}")

        # 对角元素累加
        stiffness_matrix[i, i] += k
        stiffness_matrix[j, j] += k
        # 非对角元素
        stiffness_matrix[i, j] -= k
        stiffness_matrix[j, i] -= k

    # 组装接地弹簧
    if ground_springs:
        for node_idx, k in ground_springs:
            if node_idx < 0 or node_idx >= n:
                raise ValueError(f"接地弹簧索引超出范围: {node_idx}")
            if k <= 0:
                raise ValueError(f"接地弹簧刚度必须为正: k = {k}")
            stiffness_matrix[node_idx, node_idx] += k

    return mass_matrix, stiffness_matrix


def build_cantilever_beam_matrix(n_masses: int, mass: float,
                                  stiffness: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    构建悬臂梁离散质量-弹簧系统矩阵

    将悬臂梁离散为 n 个质量块和 n+1 个弹簧:
    固定端 |弹簧|质量|弹簧|质量| ... |弹簧|质量|自由端

    Args:
        n_masses: 质量块数量
        mass: 每个质量块的质量
        stiffness: 每个弹簧的刚度

    Returns:
        (mass_matrix, stiffness_matrix)
    """
    masses = [mass] * n_masses

    # 弹簧连接: 相邻质量块之间，以及第一个质量块到固定端
    springs = []
    for i in range(n_masses - 1):
        springs.append((i, i + 1, stiffness))

    # 固定端弹簧 (第一个质量块到固定端)
    ground_springs = [(0, stiffness)]

    return build_spring_mass_matrices(masses, springs, ground_springs)


def build_fixed_fixed_beam_matrix(n_masses: int, mass: float,
                                  stiffness: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    构建两端固定梁离散质量-弹簧系统矩阵

    固定端 |弹簧|质量|弹簧|质量| ... |弹簧|质量|弹簧|固定端

    Args:
        n_masses: 质量块数量
        mass: 每个质量块的质量
        stiffness: 每个弹簧的刚度

    Returns:
        (mass_matrix, stiffness_matrix)
    """
    masses = [mass] * n_masses

    springs = []
    for i in range(n_masses - 1):
        springs.append((i, i + 1, stiffness))

    # 两端接地弹簧
    ground_springs = [(0, stiffness), (n_masses - 1, stiffness)]

    return build_spring_mass_matrices(masses, springs, ground_springs)


def create_mdof_system(
    mass_matrix: np.ndarray,
    stiffness_matrix: np.ndarray,
    damping_matrix: Optional[np.ndarray] = None,
    system_name: str = "MDOF System",
) -> MDOFSystem:
    """
    创建 MDOF 系统对象

    Args:
        mass_matrix: 质量矩阵
        stiffness_matrix: 刚度矩阵
        damping_matrix: 阻尼矩阵 (可选)
        system_name: 系统名称

    Returns:
        MDOFSystem
    """
    n = mass_matrix.shape[0]
    if damping_matrix is None:
        damping_matrix = np.zeros((n, n))
    return MDOFSystem(
        mass_matrix=mass_matrix,
        damping_matrix=damping_matrix,
        stiffness_matrix=stiffness_matrix,
        dof=n,
        system_name=system_name,
    )


def mdof_free_vibration(
    system: MDOFSystem,
    initial_displacement: np.ndarray,
    initial_velocity: np.ndarray,
    time: np.ndarray,
) -> np.ndarray:
    """
    MDOF 自由振动响应 (MDOF free vibration response)

    通过模态叠加法求解:
    1. 模态分析得到固有频率和模态振型
    2. 将初始条件投影到模态坐标
    3. 对每个模态求解 SDOF 方程
    4. 叠加模态响应

    Args:
        system: MDOF系统
        initial_displacement: 初始位移 [n_dof]
        initial_velocity: 初始速度 [n_dof]
        time: 时间数组

    Returns:
        位移响应 [n_time x n_dof]
    """
    modal = modal_analysis(system.mass_matrix, system.stiffness_matrix,
                           system.damping_matrix)

    n_dof = system.dof
    n_modes = min(n_dof, 20)

    displacement = np.zeros((len(time), n_dof))

    # 初始条件的模态坐标
    modal_init_disp = np.array([
        modal.mode_shapes[:, i].T @ system.mass_matrix @ initial_displacement
        for i in range(n_modes)
    ])
    modal_init_vel = np.array([
        modal.mode_shapes[:, i].T @ system.mass_matrix @ initial_velocity
        for i in range(n_modes)
    ])

    from .free_vibration import damped_natural_frequency

    for i in range(n_modes):
        omega_n = modal.natural_freq_rad[i]
        zeta = modal.damping_ratios[i]

        if omega_n < 1e-10:
            # 刚体模态
            for j in range(len(time)):
                displacement[j, :] += modal.mode_shapes[:, i] * (
                    modal_init_disp[i] + modal_init_vel[i] * time[j]
                )
            continue

        if zeta >= 1.0:
            # 临界/过阻尼
            for j, t in enumerate(time):
                env = modal_init_disp[i] + modal_init_vel[i] * t
                displacement[j, :] += modal.mode_shapes[:, i] * env * np.exp(-omega_n * t)
        else:
            # 欠阻尼
            omega_d = omega_n * np.sqrt(1 - zeta ** 2)
            decay = zeta * omega_n

            for j, t in enumerate(time):
                exp_term = np.exp(-decay * t)
                q_i = exp_term * (
                    modal_init_disp[i] * np.cos(omega_d * t) +
                    (modal_init_vel[i] + decay * modal_init_disp[i]) / omega_d * np.sin(omega_d * t)
                )
                displacement[j, :] += modal.mode_shapes[:, i] * q_i

    return displacement


def mdof_forced_response(
    system: MDOFSystem,
    force_func: callable,
    initial_displacement: np.ndarray,
    initial_velocity: np.ndarray,
    time: np.ndarray,
) -> np.ndarray:
    """
    MDOF 强迫振动响应 (MDOF forced vibration response)

    使用模态叠加法求解强迫振动:
    x'' + 2*zeta*omega*x' + omega^2*x = F(t)/m

    Args:
        system: MDOF系统
        force_func: 力函数 F(t) -> [n_dof]
        initial_displacement: 初始位移 [n_dof]
        initial_velocity: 初始速度 [n_dof]
        time: 时间数组

    Returns:
        位移响应 [n_time x n_dof]
    """
    from scipy.integrate import odeint
    from .modal_analysis import modal_analysis

    modal = modal_analysis(system.mass_matrix, system.stiffness_matrix,
                           system.damping_matrix)

    n_dof = system.dof
    n_modes = min(n_dof, 20)

    displacement = np.zeros((len(time), n_dof))

    for i in range(n_modes):
        omega_n = modal.natural_freq_rad[i]
        zeta = modal.damping_ratios[i]
        m_modal = modal.modal_masses[i]

        if omega_n < 1e-10:
            continue

        def modal_ode(q_state, t):
            q, dq = q_state
            F_t = force_func(t)
            F_modal = modal.mode_shapes[:, i].T @ system.mass_matrix @ F_t
            d2q = (F_modal - 2 * zeta * omega_n * dq - omega_n ** 2 * q) / m_modal
            return [dq, d2q]

        # 初始条件投影到模态坐标
        q0 = [
            modal.mode_shapes[:, i].T @ system.mass_matrix @ initial_displacement,
            modal.mode_shapes[:, i].T @ system.mass_matrix @ initial_velocity,
        ]

        q_sol = odeint(modal_ode, q0, time)

        for j in range(len(time)):
            displacement[j, :] += modal.mode_shapes[:, i] * q_sol[j, 0]

    return displacement


def build_mass_spring_chain(
    n_masses: int,
    masses: List[float],
    spring_constants: List[float],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    构建串联质量-弹簧系统矩阵

    串联系统: 固定端 - k1 - m1 - k2 - m2 - ... - kn - mn - 自由端

    Args:
        n_masses: 质量块数量
        masses: 各质量块质量列表
        spring_constants: 各弹簧刚度列表 (长度 = n_masses + 1)

    Returns:
        (mass_matrix, stiffness_matrix)
    """
    if len(masses) != n_masses:
        raise ValueError(f"质量数量不匹配: {len(masses)} != {n_masses}")
    if len(spring_constants) != n_masses + 1:
        raise ValueError(f"弹簧数量不匹配: {len(spring_constants)} != {n_masses + 1}")

    mass_matrix = np.diag(masses)
    stiffness_matrix = np.zeros((n_masses, n_masses))

    # 第一个弹簧 (固定端到第一个质量)
    stiffness_matrix[0, 0] += spring_constants[0]

    # 中间弹簧
    for i in range(n_masses - 1):
        stiffness_matrix[i, i] += spring_constants[i + 1]
        stiffness_matrix[i + 1, i + 1] += spring_constants[i + 1]
        stiffness_matrix[i, i + 1] -= spring_constants[i + 1]
        stiffness_matrix[i + 1, i] -= spring_constants[i + 1]

    # 最后一个弹簧 (最后一个质量到自由端，不接地)
    # 实际上最后一个弹簧一端接最后一个质量，一端自由
    # 自由端不贡献刚度到系统矩阵
    # 所以最后一个弹簧不影响刚度矩阵 (它只是末端弹簧)

    return mass_matrix, stiffness_matrix


def build_series_mass_spring(
    n_masses: int,
    masses: List[float],
    spring_constants: List[float],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    构建串联质量-弹簧系统 (两端均有弹簧)

    固定端 - k0 - m1 - k1 - m2 - ... - kn - mn - kn+1 - 固定端

    Args:
        n_masses: 质量块数量
        masses: 各质量块质量列表
        spring_constants: 弹簧刚度列表 (长度 = n_masses + 1)

    Returns:
        (mass_matrix, stiffness_matrix)
    """
    if len(masses) != n_masses:
        raise ValueError("质量数量不匹配")
    if len(spring_constants) != n_masses + 1:
        raise ValueError("弹簧数量不匹配")

    mass_matrix = np.diag(masses)
    stiffness_matrix = np.zeros((n_masses, n_masses))

    # 左端弹簧
    stiffness_matrix[0, 0] += spring_constants[0]

    # 中间弹簧
    for i in range(n_masses - 1):
        stiffness_matrix[i, i] += spring_constants[i + 1]
        stiffness_matrix[i + 1, i + 1] += spring_constants[i + 1]
        stiffness_matrix[i, i + 1] -= spring_constants[i + 1]
        stiffness_matrix[i + 1, i] -= spring_constants[i + 1]

    # 右端弹簧
    stiffness_matrix[n_masses - 1, n_masses - 1] += spring_constants[n_masses]

    return mass_matrix, stiffness_matrix
