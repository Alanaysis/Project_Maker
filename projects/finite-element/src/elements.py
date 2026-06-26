"""
单元刚度矩阵模块 (Element Stiffness Matrix Module)

实现常见有限单元的刚度矩阵计算。

FEM理论背景:
- 单元刚度矩阵 k 将单元节点位移与节点力联系起来: f = k * u
- 对于线弹性材料: k = integral(B^T * D * B * t * dA) over element
  - B: 应变-位移矩阵 (strain-displacement matrix)
  - D: 弹性矩阵 (constitutive matrix)
  - t: 厚度
- 2D问题: 平面应力 (plane stress) 或 平面应变 (plane strain)
- 3D问题: 空间应力/应变
- 常应变三角形(CST)单元使用1点高斯积分(解析积分也可)
"""

import numpy as np
from typing import Tuple


# =============================================================================
# 材料本构关系 (Constitutive Relations)
# =============================================================================

def plane_stress_matrix(E: float, nu: float) -> np.ndarray:
    """
    平面应力弹性矩阵 (Plane stress constitutive matrix)

    对于薄板结构，垂直于板面的应力为零。

    D = E/(1-nu^2) * [[1, nu, 0],
                        [nu, 1, 0],
                        [0, 0, (1-nu)/2]]

    参数:
        E: 杨氏模量 (Young's modulus)
        nu: 泊松比 (Poisson's ratio)

    返回:
        D: 3x3 弹性矩阵
    """
    factor = E / (1 - nu**2)
    D = factor * np.array([
        [1.0, nu, 0.0],
        [nu, 1.0, 0.0],
        [0.0, 0.0, (1 - nu) / 2.0]
    ])
    return D


def plane_strain_matrix(E: float, nu: float) -> np.ndarray:
    """
    平面应变弹性矩阵 (Plane strain constitutive matrix)

    对于厚结构，垂直于平面的应变为零。

    D = E/((1+nu)(1-2nu)) * [[1-nu, nu, 0],
                               [nu, 1-nu, 0],
                               [0, 0, (1-2nu)/2]]

    参数:
        E: 杨氏模量
        nu: 泊松比

    返回:
        D: 3x3 弹性矩阵
    """
    factor = E / ((1 + nu) * (1 - 2 * nu))
    D = factor * np.array([
        [1 - nu, nu, 0.0],
        [nu, 1 - nu, 0.0],
        [0.0, 0.0, (1 - 2 * nu) / 2.0]
    ])
    return D


def hooke_3d_matrix(E: float, nu: float) -> np.ndarray:
    """
    三维弹性矩阵 (3D constitutive matrix)

    参数:
        E: 杨氏模量
        nu: 泊松比

    返回:
        D: 6x6 弹性矩阵
    """
    factor = E / ((1 + nu) * (1 - 2 * nu))
    D = factor * np.array([
        [1 - nu, nu, nu, 0, 0, 0],
        [nu, 1 - nu, nu, 0, 0, 0],
        [nu, nu, 1 - nu, 0, 0, 0],
        [0, 0, 0, (1 - 2 * nu) / 2, 0, 0],
        [0, 0, 0, 0, (1 - 2 * nu) / 2, 0],
        [0, 0, 0, 0, 0, (1 - 2 * nu) / 2]
    ])
    return D


# =============================================================================
# 2D 常应变三角形单元 (CST - Constant Strain Triangle)
# =============================================================================

def cst_stiffness_matrix(nodes: np.ndarray, E: float, nu: float, thickness: float = 1.0) -> np.ndarray:
    """
    常应变三角形单元刚度矩阵 (CST element stiffness matrix)

    CST单元有3个节点，每个节点2个自由度(ux, uy)，共6个自由度。
    应变在单元内为常数。

    刚度矩阵: k = A * t * B^T * D * B

    其中:
        A: 单元面积
        t: 厚度
        B: 应变-位移矩阵 (3x6)
        D: 弹性矩阵 (3x3)

    参数:
        nodes: 单元节点坐标 (3, 2)
        E: 杨氏模量
        nu: 泊松比
        thickness: 厚度

    返回:
        k: 6x6 单元刚度矩阵
    """
    # 节点坐标
    x1, y1 = nodes[0]
    x2, y2 = nodes[1]
    x3, y3 = nodes[2]

    # 计算三角形面积 (Area = 0.5 * |det|)
    # 面积公式: A = 0.5 * (x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2))
    area = 0.5 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))

    if area <= 0:
        raise ValueError("Degenerate triangle: zero or negative area")

    # 计算B矩阵的系数 (strain-displacement matrix coefficients)
    # 对于CST单元，B矩阵是常数
    # B = 1/(2A) * [[b1, 0, b2, 0, b3, 0],
    #                [0, c1, 0, c2, 0, c3],
    #                [c1, b1, c2, b2, c3, b3]]
    # 其中: bi = yi+1 - yi+2 (循环), ci = xi+2 - xi+1
    b1 = y2 - y3
    b2 = y3 - y1
    b3 = y1 - y2
    c1 = x3 - x2
    c2 = x1 - x3
    c3 = x2 - x1

    # 建立弹性矩阵 (平面应力)
    D = plane_stress_matrix(E, nu)

    # 构建B矩阵 (3x6)
    B = np.array([
        [b1, 0, b2, 0, b3, 0],
        [0, c1, 0, c2, 0, c3],
        [c1, b1, c2, b2, c3, b3]
    ]) / (2.0 * area)

    # 计算刚度矩阵: k = A * t * B^T * D * B
    k = area * thickness * B.T @ D @ B

    return k


# =============================================================================
# 2D 梁单元 (Beam Element)
# =============================================================================

def beam_stiffness_matrix(E: float, I: float, L: float, A: float = 1.0) -> np.ndarray:
    """
    Euler-Bernoulli 梁单元刚度矩阵 (Euler-Bernoulli beam element stiffness matrix)

    每个节点有3个自由度: 轴向位移u、横向位移v、转角theta
    共6个自由度。

    k = [[EA/L, 0, 0, -EA/L, 0, 0],
         [0, 12EI/L^3, 6EI/L^2, 0, -12EI/L^3, 6EI/L^2],
         [0, 6EI/L^2, 4EI/L, 0, -6EI/L^2, 2EI/L],
         [-EA/L, 0, 0, EA/L, 0, 0],
         [0, -12EI/L^3, -6EI/L^2, 0, 12EI/L^3, -6EI/L^2],
         [0, 6EI/L^2, 2EI/L, 0, -6EI/L^2, 4EI/L]]

    参数:
        E: 杨氏模量
        I: 截面惯性矩 (moment of inertia)
        L: 梁长度
        A: 截面积

    返回:
        k: 6x6 梁单元刚度矩阵
    """
    EA_L = E * A / L
    EI_L3 = E * I / (L ** 3)
    EI_L2 = E * I / (L ** 2)
    EI_L = E * I / L

    k = np.array([
        [EA_L, 0, 0, -EA_L, 0, 0],
        [0, 12 * EI_L3, 6 * EI_L2, 0, -12 * EI_L3, 6 * EI_L2],
        [0, 6 * EI_L2, 4 * EI_L, 0, -6 * EI_L2, 2 * EI_L],
        [-EA_L, 0, 0, EA_L, 0, 0],
        [0, -12 * EI_L3, -6 * EI_L2, 0, 12 * EI_L3, -6 * EI_L2],
        [0, 6 * EI_L2, 2 * EI_L, 0, -6 * EI_L2, 4 * EI_L]
    ])

    return k


def truss_stiffness_matrix(E: float, A: float, nodes: np.ndarray) -> np.ndarray:
    """
    桁架单元刚度矩阵 (Truss element stiffness matrix)

    桁架单元只承受轴向力，每个节点2个自由度(ux, uy)。

    局部坐标系: k_local = EA/L * [[1], [-1]] * [[1, -1]]
    全局坐标系: k = T^T * k_local * T

    参数:
        E: 杨氏模量
        A: 截面积
        nodes: 单元节点坐标 (2, 2)

    返回:
        k: 4x4 桁架单元刚度矩阵
    """
    n1, n2 = nodes[0], nodes[1]
    L = np.linalg.norm(n2 - n1)

    if L < 1e-10:
        raise ValueError("Zero length truss element")

    # 方向余弦
    c = (n2[0] - n1[0]) / L  # cos(theta)
    s = (n2[1] - n1[1]) / L  # sin(theta)

    # 桁架单元刚度矩阵
    EA_L = E * A / L
    k = EA_L * np.array([
        [c**2, c*s, -c**2, -c*s],
        [c*s, s**2, -c*s, -s**2],
        [-c**2, -c*s, c**2, c*s],
        [-c*s, -s**2, c*s, s**2]
    ])

    return k


# =============================================================================
# 3D 桁架单元
# =============================================================================

def truss_3d_stiffness_matrix(E: float, A: float, nodes: np.ndarray) -> np.ndarray:
    """
    3D 桁架单元刚度矩阵 (3D truss element stiffness matrix)

    每个节点3个自由度(ux, uy, uz)，共6个自由度。

    参数:
        E: 杨氏模量
        A: 截面积
        nodes: 单元节点坐标 (2, 3)

    返回:
        k: 6x6 单元刚度矩阵
    """
    n1, n2 = nodes[0], nodes[1]
    L = np.linalg.norm(n2 - n1)

    if L < 1e-10:
        raise ValueError("Zero length truss element")

    # 方向余弦
    c = (n2[0] - n1[0]) / L
    s = (n2[1] - n1[1]) / L
    t = (n2[2] - n1[2]) / L

    EA_L = E * A / L

    # 6x6 刚度矩阵
    k = EA_L * np.array([
        [c**2, c*s, c*t, -c**2, -c*s, -c*t],
        [c*s, s**2, s*t, -c*s, -s**2, -s*t],
        [c*t, s*t, t**2, -c*t, -s*t, -t**2],
        [-c**2, -c*s, -c*t, c**2, c*s, c*t],
        [-c*s, -s**2, -s*t, c*s, s**2, s*t],
        [-c*t, -s*t, -t**2, c*t, s*t, t**2]
    ])

    return k


# =============================================================================
# 2D 四边形等参单元 (4-node Quad)
# =============================================================================

def quad_stiffness_matrix(nodes: np.ndarray, E: float, nu: float, thickness: float = 1.0) -> np.ndarray:
    """
    4节点四边形等参单元刚度矩阵 (4-node quad isoparametric element stiffness matrix)

    使用2x2高斯积分计算刚度矩阵。

    参数:
        nodes: 单元节点坐标 (4, 2)，按逆时针顺序 [n0, n1, n2, n3]
        E: 杨氏模量
        nu: 泊松比
        thickness: 厚度

    返回:
        k: 8x8 单元刚度矩阵
    """
    # 2x2 高斯积分点权重和坐标
    gauss_points = [(-1/np.sqrt(3), 1/np.sqrt(3)), (1/np.sqrt(3), 1/np.sqrt(3)),
                    (-1/np.sqrt(3), -1/np.sqrt(3)), (1/np.sqrt(3), -1/np.sqrt(3))]
    weights = [0.25, 0.25, 0.25, 0.25]  # 已包含Jacobian的近似

    k = np.zeros((8, 8))
    D = plane_stress_matrix(E, nu)

    for gp_idx, (r, s) in enumerate(gauss_points):
        # 计算形函数及其导数
        N, dNdr = _quad_shape_functions(r, s)

        # 计算雅可比矩阵
        J = _quad_jacobian(nodes, dNdr)

        # 计算B矩阵
        B = _quad_B_matrix(nodes, N, dNdr, J)

        # 计算Jacobian行列式
        det_J = np.linalg.det(J)

        if det_J <= 0:
            raise ValueError("Negative Jacobian determinant - invalid element geometry")

        # k += integral(B^T * D * B * det_J * dA)
        # 对于等参单元，dA = det_J * dr * ds
        k += weights[gp_idx] * B.T @ D @ B * det_J

    return k


def _quad_shape_functions(r: float, s: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    4节点四边形形函数 (4-node quad shape functions)

    返回:
        N: 形函数值 [N1, N2, N3, N4]
        dNdr: 形函数对自然坐标的导数 (4x2)
    """
    N = np.array([
        0.25 * (1 - r) * (1 - s),
        0.25 * (1 + r) * (1 - s),
        0.25 * (1 + r) * (1 + s),
        0.25 * (1 - r) * (1 + s)
    ])

    dNdr = np.array([
        [-(1 - s), -(1 - r)],
        [(1 - s), -(1 + r)],
        [(1 + s), (1 + r)],
        [-(1 + s), (1 - r)]
    ]) * 0.25

    return N, dNdr


def _quad_jacobian(nodes: np.ndarray, dNdr: np.ndarray) -> np.ndarray:
    """
    计算四边形单元的雅可比矩阵 (Compute Jacobian matrix for quad element)

    J = sum(dNi/d(r,s) * xi) 其中xi是节点坐标
    """
    J = np.zeros((2, 2))
    for i in range(4):
        J[0, 0] += dNdr[i, 0] * nodes[i, 0]
        J[0, 1] += dNdr[i, 0] * nodes[i, 1]
        J[1, 0] += dNdr[i, 1] * nodes[i, 0]
        J[1, 1] += dNdr[i, 1] * nodes[i, 1]
    return J


def _quad_B_matrix(nodes: np.ndarray, N: np.ndarray, dNdr: np.ndarray, J: np.ndarray) -> np.ndarray:
    """
    计算四边形单元的应变-位移矩阵 (Compute strain-displacement matrix for quad)

    B = dN * inv(J)
    其中 dN 是形函数导数矩阵，J 是雅可比矩阵
    """
    inv_J = np.linalg.inv(J)

    # dN/dx = dN/dr * inv(J)
    dNdx = dNdr @ inv_J

    B = np.zeros((3, 8))
    for i in range(4):
        B[0, 2*i] = dNdx[i, 0]     # du/dx
        B[1, 2*i + 1] = dNdx[i, 1]  # dv/dy
        B[2, 2*i] = dNdx[i, 1]      # du/dy
        B[2, 2*i + 1] = dNdx[i, 0]  # dv/dx

    return B
