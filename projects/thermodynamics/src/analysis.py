"""
稳态和瞬态分析模块

稳态分析: 当时间 t → ∞ 时，温度分布不再变化 (∂T/∂t = 0)
    ∇·(k∇T) + Q = 0

瞬态分析: 温度随时间变化，研究温度场的演化过程
    ρc ∂T/∂t = ∇·(k∇T) + Q

关键概念：
- 热时间常数 τ = L²/α (特征时间尺度)
- 稳态达到时间 ~ 5τ
- 毕渥数 Bi = hL/k (对流 vs 传导)
- 傅里叶数 Fo = αt/L² (无量纲时间)
"""

import numpy as np
from typing import Optional, Tuple


def compute_steady_state_1d(
    L: float,
    nx: int,
    k: float,
    T_left: float,
    T_right: float,
    heat_source=None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    求解一维稳态热传导方程

    稳态方程: d²T/dx² + Q/k = 0

    解析解 (无热源): T(x) = T_left + (T_right - T_left) * x/L

    参数
    ----------
    L : float
        杆长 (m)
    nx : int
        网格点数
    k : float
        热导率 (W/(m·K))
    T_left, T_right : float
        边界温度 (°C)
    heat_source : callable, optional
        热源函数 f(x) -> W/m³

    返回
    -------
    x : np.ndarray
        空间坐标
    T : np.ndarray
        稳态温度分布
    """
    x = np.linspace(0, L, nx)
    dx = L / (nx - 1)

    # 构建线性方程组 Ax = b
    # 内部节点: (T_{i+1} - 2T_i + T_{i-1})/dx² + Q_i/k = 0
    n_internal = nx - 2
    A = np.zeros((n_internal, n_internal))
    b = np.zeros(n_internal)

    for i in range(n_internal):
        A[i, i] = -2.0 / (dx ** 2)
        if i > 0:
            A[i, i - 1] = 1.0 / (dx ** 2)
        if i < n_internal - 1:
            A[i, i + 1] = 1.0 / (dx ** 2)

        # 添加热源项
        xi = (i + 1) * dx
        if heat_source:
            b[i] = -heat_source(xi) / k

    # 处理边界条件
    b[0] -= T_left / (dx ** 2)
    b[-1] -= T_right / (dx ** 2)

    # 求解
    T_interior = np.linalg.solve(A, b)

    T = np.concatenate([[T_left], T_interior, [T_right]])

    return x, T


def compute_steady_state_2d(
    Lx: float,
    Ly: float,
    nx: int,
    ny: int,
    k: float,
    T_bottom: float = 0.0,
    T_top: float = 0.0,
    T_left: float = 0.0,
    T_right: float = 0.0,
    heat_source=None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    求解二维稳态热传导方程

    稳态方程: ∂²T/∂x² + ∂²T/∂y² + Q/k = 0

    使用有限差分法将 PDE 转化为线性方程组。

    参数
    ----------
    Lx, Ly : float
        区域尺寸 (m)
    nx, ny : int
        网格点数
    k : float
        热导率 (W/(m·K))
    T_bottom, T_top, T_left, T_right : float
        边界温度 (°C)
    heat_source : callable, optional
        热源函数 f(x, y) -> W/m³

    返回
    -------
    x, y : np.ndarray
        空间坐标
    T : np.ndarray
        稳态温度分布 (ny, nx)
    """
    dx = Lx / (nx - 1)
    dy = Ly / (ny - 1)
    x = np.linspace(0, Lx, nx)
    y = np.linspace(0, Ly, ny)

    # 内部节点数
    n_internal = (nx - 2) * (ny - 2)
    A = np.zeros((n_internal, n_internal))
    b = np.zeros(n_internal)

    def idx(i, j):
        """将二维索引映射到一维索引"""
        return (j - 1) * (nx - 2) + (i - 1)

    for j in range(1, ny - 1):
        for i in range(1, nx - 1):
            row = idx(i, j)
            A[row, row] = 2.0 / (dx ** 2) + 2.0 / (dy ** 2)
            A[row, idx(i - 1, j)] = -1.0 / (dx ** 2)
            A[row, idx(i + 1, j)] = -1.0 / (dx ** 2)
            A[row, idx(i, j - 1)] = -1.0 / (dy ** 2)
            A[row, idx(i, j + 1)] = -1.0 / (dy ** 2)

            if heat_source:
                b[row] = -heat_source(x[i], y[j]) / k

    # 处理边界条件
    for i in range(1, nx - 1):
        row = idx(i, 1)
        b[row] -= T_bottom / (dy ** 2)

        row = idx(i, ny - 2)
        b[row] -= T_top / (dy ** 2)

    for j in range(1, ny - 1):
        row = idx(1, j)
        b[row] -= T_left / (dx ** 2)

        row = idx(nx - 2, j)
        b[row] -= T_right / (dx ** 2)

    # 求解线性方程组
    T_interior = np.linalg.solve(A, b)

    # 重建二维温度场
    T = np.zeros((ny, nx))
    T[0, :] = T_bottom
    T[-1, :] = T_top
    T[:, 0] = T_left
    T[:, -1] = T_right

    for j in range(1, ny - 1):
        for i in range(1, nx - 1):
            T[j, i] = T_interior[idx(i, j)]

    return x, y, T


def thermal_time_constant(L: float, alpha: float) -> float:
    """
    计算热时间常数

    τ = L² / α

    特征时间尺度，表示温度扰动传播穿过尺寸 L 所需的时间。
    通常认为 5τ 后系统达到稳态。

    参数
    ----------
    L : float
        特征长度 (m)
    alpha : float
        热扩散系数 (m²/s)

    返回
    -------
    tau : float
        热时间常数 (s)
    """
    return L ** 2 / alpha


def fourier_number(L: float, alpha: float, t: float) -> float:
    """
    计算傅里叶数 (无量纲时间)

    Fo = αt / L²

    傅里叶数表示热扩散速率与储能速率的比值。
    - Fo << 1: 热扰动尚未传播到整个区域
    - Fo ~ 1: 热扰动正在传播
    - Fo >> 1: 接近稳态

    参数
    ----------
    L : float
        特征长度 (m)
    alpha : float
        热扩散系数 (m²/s)
    t : float
        时间 (s)

    返回
    -------
    Fo : float
        傅里叶数
    """
    return alpha * t / (L ** 2)


def biot_number(h: float, L: float, k: float) -> float:
    """
    计算毕渥数 (无量纲数)

    Bi = hL / k

    毕渥数表示表面对流换热与内部传导换热的比值。
    - Bi << 1: 内部温度均匀 (集总参数法适用)
    - Bi >> 1: 表面温度接近环境温度

    参数
    ----------
    h : float
        对流换热系数 (W/(m²·K))
    L : float
        特征长度 (m)
    k : float
        热导率 (W/(m·K))

    返回
    -------
    Bi : float
        毕渥数
    """
    return h * L / k


def analyze_steady_state_reached(
    T_prev: np.ndarray,
    T_curr: np.ndarray,
    tolerance: float = 1e-6,
) -> bool:
    """
    判断系统是否已达到稳态

    通过比较连续两个时间步的温度差异来判断。

    参数
    ----------
    T_prev : np.ndarray
        前一时间步的温度
    T_curr : np.ndarray
        当前时间步的温度
    tolerance : float
        容差

    返回
    -------
    reached : bool
        是否达到稳态
    """
    if T_prev.ndim == 1:
        max_diff = np.max(np.abs(T_curr - T_prev))
    else:
        max_diff = np.max(np.abs(T_curr - T_prev))
    return max_diff < tolerance


def compute_heat_flux_1d(T: np.ndarray, dx: float, k: float) -> np.ndarray:
    """
    计算一维热流密度 (W/m²)

    根据傅里叶定律: q = -k * dT/dx

    参数
    ----------
    T : np.ndarray
        温度数组
    dx : float
        空间步长 (m)
    k : float
        热导率 (W/(m·K))

    返回
    -------
    q : np.ndarray
        热流密度 (W/m²), 长度 nx-1
    """
    dT_dx = np.gradient(T, dx)
    return -k * dT_dx


def compute_total_heat_content(T: np.ndarray, rho: float, c: float, dx: float) -> float:
    """
    计算系统总热能 (J/m² for 1D, J/m for 2D surface)

    E = ∫ ρcT dV

    参数
    ----------
    T : np.ndarray
        温度数组
    rho : float
        密度 (kg/m³)
    c : float
        比热容 (J/(kg·K))
    dx : float
        空间步长 (m)

    返回
    -------
    E : float
        总热能
    """
    return rho * c * np.sum(T) * dx
