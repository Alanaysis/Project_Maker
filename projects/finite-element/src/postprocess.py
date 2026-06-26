"""
后处理模块 (Post-processing Module)

实现应力计算、Von Mises应力、结果可视化等功能。

FEM理论背景:
- 应变-位移关系: epsilon = B * u (B是应变-位移矩阵, u是节点位移)
- 应力-应变关系: sigma = D * epsilon = D * B * u (D是弹性矩阵)
- Von Mises应力: sigma_v = sqrt(sigma_x^2 - sigma_x*sigma_y + sigma_y^2 + 3*tau_xy^2)
  - 用于判断屈服 (yield criterion)
  - 各向同性材料: sigma_yield = sigma_v at yield
"""

import numpy as np
from typing import Tuple, List, Optional
from src.elements import (
    plane_stress_matrix, plane_strain_matrix, hooke_3d_matrix,
    cst_stiffness_matrix
)


# =============================================================================
# 应变计算 (Strain Calculation)
# =============================================================================

def compute_strain_cst(nodes: np.ndarray, displacement: np.ndarray) -> np.ndarray:
    """
    计算CST单元的应变 (Compute strain for CST element)

    对于常应变三角形单元，应变在单元内为常数:
      epsilon = B * u

    参数:
        nodes: 单元节点坐标 (3, 2)
        displacement: 单元节点位移 (6,) = [ux1, uy1, ux2, uy2, ux3, uy3]

    返回:
        epsilon: 应变向量 [eps_x, eps_y, gamma_xy]
    """
    x1, y1 = nodes[0]
    x2, y2 = nodes[1]
    x3, y3 = nodes[2]

    area = 0.5 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))

    b1 = y2 - y3
    b2 = y3 - y1
    b3 = y1 - y2
    c1 = x3 - x2
    c2 = x1 - x3
    c3 = x2 - x1

    B = np.array([
        [b1, 0, b2, 0, b3, 0],
        [0, c1, 0, c2, 0, c3],
        [c1, b1, c2, b2, c3, b3]
    ]) / (2.0 * area)

    epsilon = B @ displacement
    return epsilon


def compute_strain_quad(nodes: np.ndarray, displacement: np.ndarray) -> np.ndarray:
    """
    计算四边形单元的应变 (Compute strain for quad element)

    在积分点处计算应变。

    参数:
        nodes: 单元节点坐标 (4, 2)
        displacement: 单元节点位移 (8,)

    返回:
        epsilon: 平均应变向量 [eps_x, eps_y, gamma_xy]
    """
    # 使用2x2高斯积分
    gauss_points = [(-1/np.sqrt(3), 1/np.sqrt(3)), (1/np.sqrt(3), 1/np.sqrt(3)),
                    (-1/np.sqrt(3), -1/np.sqrt(3)), (1/np.sqrt(3), -1/np.sqrt(3))]

    epsilon_sum = np.zeros(3)

    for r, s in gauss_points:
        # 形函数
        N = np.array([
            0.25 * (1 - r) * (1 - s),
            0.25 * (1 + r) * (1 - s),
            0.25 * (1 + r) * (1 + s),
            0.25 * (1 - r) * (1 + s)
        ])

        # 形函数导数
        dNdr = np.array([
            [-(1 - s), -(1 - r)],
            [(1 - s), -(1 + r)],
            [(1 + s), (1 + r)],
            [-(1 + s), (1 - r)]
        ]) * 0.25

        # 雅可比矩阵
        J = np.zeros((2, 2))
        for i in range(4):
            J[0, 0] += dNdr[i, 0] * nodes[i, 0]
            J[0, 1] += dNdr[i, 0] * nodes[i, 1]
            J[1, 0] += dNdr[i, 1] * nodes[i, 0]
            J[1, 1] += dNdr[i, 1] * nodes[i, 1]

        inv_J = np.linalg.inv(J)
        dNdx = dNdr @ inv_J

        # B矩阵
        B = np.zeros((3, 8))
        for i in range(4):
            B[0, 2*i] = dNdx[i, 0]
            B[1, 2*i + 1] = dNdx[i, 1]
            B[2, 2*i] = dNdx[i, 1]
            B[2, 2*i + 1] = dNdx[i, 0]

        epsilon = B @ displacement
        epsilon_sum += epsilon

    return epsilon_sum / len(gauss_points)


# =============================================================================
# 应力计算 (Stress Calculation)
# =============================================================================

def compute_stress_cst(
    nodes: np.ndarray,
    displacement: np.ndarray,
    E: float,
    nu: float,
    stress_type: str = "plane_stress"
) -> np.ndarray:
    """
    计算CST单元的应力 (Compute CST element stress)

    sigma = D * epsilon = D * B * u

    参数:
        nodes: 单元节点坐标 (3, 2)
        displacement: 单元节点位移 (6,)
        E: 杨氏模量
        nu: 泊松比
        stress_type: 'plane_stress' 或 'plane_strain'

    返回:
        stress: 应力向量 [sigma_x, sigma_y, tau_xy]
    """
    epsilon = compute_strain_cst(nodes, displacement)

    if stress_type == "plane_stress":
        D = plane_stress_matrix(E, nu)
    else:
        D = plane_strain_matrix(E, nu)

    stress = D @ epsilon
    return stress


def compute_stress_quad(
    nodes: np.ndarray,
    displacement: np.ndarray,
    E: float,
    nu: float,
    stress_type: str = "plane_stress"
) -> np.ndarray:
    """
    计算四边形单元的应力 (Compute quad element stress)

    返回平均应力。

    参数:
        nodes: 单元节点坐标 (4, 2)
        displacement: 单元节点位移 (8,)
        E: 杨氏模量
        nu: 泊松比
        stress_type: 'plane_stress' 或 'plane_strain'

    返回:
        stress: 平均应力向量 [sigma_x, sigma_y, tau_xy]
    """
    epsilon = compute_strain_quad(nodes, displacement)

    if stress_type == "plane_stress":
        D = plane_stress_matrix(E, nu)
    else:
        D = plane_strain_matrix(E, nu)

    stress = D @ epsilon
    return stress


# =============================================================================
# Von Mises 应力 (Von Mises Stress)
# =============================================================================

def von_mises_stress_2d(
    sigma_x: float,
    sigma_y: float,
    tau_xy: float
) -> float:
    """
    计算2D Von Mises等效应力 (Compute 2D Von Mises equivalent stress)

    sigma_v = sqrt(sigma_x^2 - sigma_x*sigma_y + sigma_y^2 + 3*tau_xy^2)

    Von Mises屈服准则:
    - 当 sigma_v >= sigma_yield 时，材料屈服
    - 适用于延性材料 (ductile materials)

    参数:
        sigma_x: x方向正应力
        sigma_y: y方向正应力
        tau_xy: xy平面剪应力

    返回:
        sigma_v: Von Mises等效应力
    """
    sigma_v = np.sqrt(sigma_x**2 - sigma_x * sigma_y + sigma_y**2 + 3 * tau_xy**2)
    return sigma_v


def von_mises_stress_3d(
    sigma_x: float,
    sigma_y: float,
    sigma_z: float,
    tau_xy: float,
    tau_yz: float,
    tau_zx: float
) -> float:
    """
    计算3D Von Mises等效应力 (Compute 3D Von Mises equivalent stress)

    sigma_v = sqrt(0.5 * ((sigma_x-sigma_y)^2 + (sigma_y-sigma_z)^2 + (sigma_z-sigma_x)^2 + 6*(tau_xy^2 + tau_yz^2 + tau_zx^2)))

    参数:
        sigma_x, sigma_y, sigma_z: 正应力
        tau_xy, tau_yz, tau_zx: 剪应力

    返回:
        sigma_v: Von Mises等效应力
    """
    sigma_v = np.sqrt(
        0.5 * (
            (sigma_x - sigma_y)**2 +
            (sigma_y - sigma_z)**2 +
            (sigma_z - sigma_x)**2 +
            6 * (tau_xy**2 + tau_yz**2 + tau_zx**2)
        )
    )
    return sigma_v


def compute_von_mises_from_stress(stress: np.ndarray, dim: int = 2) -> float:
    """
    从应力向量计算Von Mises应力 (Compute Von Mises stress from stress vector)

    参数:
        stress: 应力向量
        dim: 维度 (2或3)

    返回:
        sigma_v: Von Mises等效应力
    """
    if dim == 2:
        return von_mises_stress_2d(stress[0], stress[1], stress[2])
    else:
        return von_mises_stress_3d(
            stress[0], stress[1], stress[2],
            stress[3], stress[4], stress[5]
        )


# =============================================================================
# 应变能 (Strain Energy)
# =============================================================================

def compute_strain_energy(
    nodes: np.ndarray,
    displacement: np.ndarray,
    E: float,
    nu: float,
    thickness: float = 1.0
) -> float:
    """
    计算单元应变能 (Compute element strain energy)

    U = 0.5 * u^T * k * u = 0.5 * integral(epsilon^T * D * epsilon * dV)

    参数:
        nodes: 单元节点坐标
        displacement: 节点位移向量
        E: 杨氏模量
        nu: 泊松比
        thickness: 厚度 (2D问题)

    返回:
        U: 应变能
    """
    # 计算单元刚度矩阵
    k = cst_stiffness_matrix(nodes, E, nu, thickness)

    # 应变能 = 0.5 * u^T * k * u
    U = 0.5 * displacement @ k @ displacement

    return U


# =============================================================================
# 节点力计算 (Nodal Forces)
# =============================================================================

def compute_nodal_forces(
    nodes: np.ndarray,
    displacement: np.ndarray,
    E: float,
    nu: float,
    thickness: float = 1.0
) -> np.ndarray:
    """
    计算单元节点力 (Compute element nodal forces)

    f = k * u

    参数:
        nodes: 单元节点坐标
        displacement: 节点位移向量
        E: 杨氏模量
        nu: 泊松比
        thickness: 厚度

    返回:
        f: 节点力向量
    """
    k = cst_stiffness_matrix(nodes, E, nu, thickness)
    f = k @ displacement
    return f


# =============================================================================
# 应力平均 (Stress Averaging)
# =============================================================================

def average_stresses_at_nodes(
    nodes: np.ndarray,
    elements: List[List[int]],
    element_stresses: List[np.ndarray],
    element_displacements: List[np.ndarray]
) -> np.ndarray:
    """
    在节点处平均应力 (Average stresses at nodes)

    将单元中心的应力平均到节点，获得更平滑的应力场。

    参数:
        nodes: 全局节点坐标
        elements: 单元连接表
        element_stresses: 每个单元的应力列表
        element_displacements: 每个单元的位移列表

    返回:
        nodal_stresses: 每个节点的应力 [sigma_x, sigma_y, tau_xy]
    """
    num_nodes = len(nodes)
    stress_sum = np.zeros((num_nodes, 3))
    count = np.zeros(num_nodes)

    for elem_nodes, stress, disp in zip(elements, element_stresses, element_displacements):
        for local_i, global_i in enumerate(elem_nodes):
            stress_sum[global_i] += stress
            count[global_i] += 1

    # 平均
    nodal_stresses = np.where(count[:, np.newaxis] > 0, stress_sum / count[:, np.newaxis], 0.0)

    return nodal_stresses


def compute_principal_stresses(sigma_x: float, sigma_y: float, tau_xy: float) -> Tuple[float, float, float]:
    """
    计算主应力 (Compute principal stresses)

    sigma_1,2 = (sigma_x + sigma_y)/2 +/- sqrt(((sigma_x - sigma_y)/2)^2 + tau_xy^2)

    参数:
        sigma_x: x方向正应力
        sigma_y: y方向正应力
        tau_xy: 剪应力

    返回:
        (sigma_1, sigma_2, theta_p): 主应力1, 主应力2, 主方向角度(弧度)
    """
    sigma_avg = (sigma_x + sigma_y) / 2.0
    R = np.sqrt(((sigma_x - sigma_y) / 2.0)**2 + tau_xy**2)

    sigma_1 = sigma_avg + R
    sigma_2 = sigma_avg - R
    theta_p = 0.5 * np.arctan2(2 * tau_xy, sigma_x - sigma_y)

    return sigma_1, sigma_2, theta_p
