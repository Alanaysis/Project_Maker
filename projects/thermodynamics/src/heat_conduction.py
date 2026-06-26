"""
热传导方程求解器模块

热传导方程（傅里叶热传导方程）描述了热量在介质中的传播过程：

    ρc ∂T/∂t = ∇·(k∇T) + Q

其中：
    T  - 温度 (K 或 °C)
    t  - 时间 (s)
    ρ  - 密度 (kg/m³)
    c  - 比热容 (J/(kg·K))
    k  - 热导率 (W/(m·K))
    Q  - 热源功率密度 (W/m³)
    ∇·(k∇T) - 热扩散项

当材料均匀且无热源时，方程简化为：
    ∂T/∂t = α∇²T

其中 α = k/(ρc) 是热扩散系数 (m²/s)
"""

import numpy as np
from typing import Callable, Optional, Tuple


def heat_conduction_1d(
    L: float,
    nx: int,
    alpha: float,
    dt: float,
    nt: int,
    T_left: float = 0.0,
    T_right: float = 0.0,
    T_initial: float = 0.0,
    heat_source: Optional[Callable[[float], float]] = None,
    method: str = "explicit",
) -> Tuple[np.ndarray, np.ndarray]:
    """
    一维热传导方程求解器

    使用有限差分法求解一维热传导方程：
        ∂T/∂t = α ∂²T/∂x² + Q/(ρc)

    参数
    ----------
    L : float
        杆的长度 (m)
    nx : int
        空间离散点数
    alpha : float
        热扩散系数 (m²/s)
    dt : float
        时间步长 (s)
    nt : int
        时间步数
    T_left : float, optional
        左边界温度 (°C), 默认 0.0
    T_right : float, optional
        右边界温度 (°C), 默认 0.0
    T_initial : float, optional
        初始温度 (°C), 默认 0.0
    heat_source : callable, optional
        热源函数 f(x) -> W/m³, 默认无热源
    method : str, optional
        求解方法: "explicit" (显式) 或 "implicit" (隐式), 默认 "explicit"

    返回
    -------
    x : np.ndarray
        空间节点坐标
    T_history : np.ndarray
        温度随时间变化 (nt+1, nx)

    示例
    ----
    >>> x, T = heat_conduction_1d(L=1.0, nx=50, alpha=1e-5, dt=0.1, nt=1000)
    >>> print(f"最终温度分布范围: [{T[-1].min():.2f}, {T[-1].max():.2f}] °C")
    """
    dx = L / (nx - 1)
    x = np.linspace(0, L, nx)

    # 初始化温度场
    T = np.full(nx, T_initial)

    # 存储温度历史
    T_history = np.zeros((nt + 1, nx))
    T_history[0] = T.copy()

    # 网格傅里叶数 (稳定性判据)
    # 显式方法要求: Fo = α*dt/dx² ≤ 0.5
    Fo = alpha * dt / (dx ** 2)

    if method == "explicit":
        # ===== 显式有限差分法 (Forward-Time Central-Space, FTCS) =====
        # 时间导数: ∂T/∂t ≈ (T^{n+1}_i - T^n_i) / dt
        # 空间导数: ∂²T/∂x² ≈ (T^n_{i+1} - 2T^n_i + T^n_{i-1}) / dx²
        #
        # 显式格式:
        # T^{n+1}_i = T^n_i + Fo * (T^n_{i+1} - 2T^n_i + T^n_{i-1})
        #
        # 稳定性条件: Fo ≤ 0.5
        # 如果 Fo > 0.5, 数值解会发散!

        if Fo > 0.5:
            raise ValueError(
                f"显式方法不稳定! 傅里叶数 Fo={Fo:.4f} > 0.5. "
                f"请减小 dt 或增大 dx."
            )

        for n in range(nt):
            T_new = T.copy()

            # 内部节点更新
            for i in range(1, nx - 1):
                # 二阶中心差分近似 ∂²T/∂x²
                d2T_dx2 = (T[i + 1] - 2 * T[i] + T[i - 1]) / (dx ** 2)

                # 添加热源项 (如果有)
                source = heat_source(x[i]) / (1.0) if heat_source else 0.0

                # 更新温度
                T_new[i] = T[i] + alpha * dt * d2T_dx2 + alpha * dt * source

            # 应用边界条件 (Dirichlet 边界)
            T_new[0] = T_left
            T_new[-1] = T_right

            T = T_new
            T_history[n + 1] = T.copy()

    elif method == "implicit":
        # ===== 隐式有限差分法 (Backward-Time Central-Space, BTCS) =====
        # 在时间步 n+1 处计算空间导数:
        # T^{n+1}_i = T^n_i + Fo * (T^{n+1}_{i+1} - 2T^{n+1}_i + T^{n+1}_{i-1})
        #
        # 整理后得到线性方程组:
        # -Fo * T^{n+1}_{i-1} + (1 + 2Fo) * T^{n+1}_i - Fo * T^{n+1}_{i+1} = T^n_i
        #
        # 隐式方法无条件稳定! 可以使用更大的时间步长

        # 构建三对角矩阵
        main_diag = np.full(nx - 2, 1 + 2 * Fo)
        lower_diag = np.full(nx - 3, -Fo)
        upper_diag = np.full(nx - 3, -Fo)

        for n in range(nt):
            # 右端项 (已知的时间步 n)
            rhs = T[1:-1].copy()

            # 添加热源项
            if heat_source:
                for i in range(1, nx - 1):
                    rhs[i - 1] += alpha * dt * heat_source(x[i])

            # 处理边界条件
            rhs[0] += Fo * T_left
            rhs[-1] += Fo * T_right

            # 求解三对角方程组
            T_interior = _solve_tridiagonal(lower_diag, main_diag, upper_diag, rhs)

            T = np.zeros(nx)
            T[0] = T_left
            T[1:-1] = T_interior
            T[-1] = T_right

            T_history[n + 1] = T.copy()

    else:
        raise ValueError(f"未知的方法: {method}. 请选择 'explicit' 或 'implicit'.")

    return x, T_history


def heat_conduction_2d(
    Lx: float,
    Ly: float,
    nx: int,
    ny: int,
    alpha: float,
    dt: float,
    nt: int,
    T_bottom: float = 0.0,
    T_top: float = 0.0,
    T_left: float = 0.0,
    T_right: float = 0.0,
    T_initial: float = 0.0,
    heat_source: Optional[Callable[[float, float], float]] = None,
    method: str = "explicit",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    二维热传导方程求解器

    求解二维热传导方程：
        ∂T/∂t = α(∂²T/∂x² + ∂²T/∂y²) + Q/(ρc)

    参数
    ----------
    Lx, Ly : float
        区域在 x 和 y 方向的尺寸 (m)
    nx, ny : int
        x 和 y 方向的网格点数
    alpha : float
        热扩散系数 (m²/s)
    dt : float
        时间步长 (s)
    nt : int
        时间步数
    T_bottom, T_top : float, optional
        上下边界温度 (°C)
    T_left, T_right : float, optional
        左右边界温度 (°C)
    T_initial : float, optional
        初始温度 (°C)
    heat_source : callable, optional
        热源函数 f(x, y) -> W/m³
    method : str, optional
        求解方法: "explicit" 或 "crank_nicolson"

    返回
    -------
    x, y : np.ndarray
        空间网格坐标
    T_history : np.ndarray
        温度分布 (nt+1, ny, nx)
    """
    dx = Lx / (nx - 1)
    dy = Ly / (ny - 1)
    x = np.linspace(0, Lx, nx)
    y = np.linspace(0, Ly, ny)

    # 初始化温度场 (2D)
    T = np.full((ny, nx), T_initial)
    T_history = np.zeros((nt + 1, ny, nx))
    T_history[0] = T.copy()

    # 二维稳定性条件: Fo_x + Fo_y ≤ 0.5
    Fo_x = alpha * dt / (dx ** 2)
    Fo_y = alpha * dt / (dy ** 2)

    if method == "explicit":
        # ===== 二维显式方法 =====
        # 稳定性条件: Fo_x + Fo_y ≤ 0.5
        if Fo_x + Fo_y > 0.5:
            raise ValueError(
                f"二维显式方法不稳定! Fo_x + Fo_y = {Fo_x + Fo_y:.4f} > 0.5. "
                f"请减小 dt."
            )

        for n in range(nt):
            T_new = T.copy()

            for i in range(1, nx - 1):
                for j in range(1, ny - 1):
                    # 二阶中心差分: ∂²T/∂x² + ∂²T/∂y²
                    d2T_dx2 = (T[j, i + 1] - 2 * T[j, i] + T[j, i - 1]) / (dx ** 2)
                    d2T_dy2 = (T[j + 1, i] - 2 * T[j, i] + T[j - 1, i]) / (dy ** 2)

                    source = heat_source(x[i], y[j]) / 1.0 if heat_source else 0.0

                    T_new[j, i] = (
                        T[j, i]
                        + alpha * dt * (d2T_dx2 + d2T_dy2)
                        + alpha * dt * source
                    )

            # 应用边界条件
            T_new[0, :] = T_bottom      # 下边界
            T_new[-1, :] = T_top        # 上边界
            T_new[:, 0] = T_left        # 左边界
            T_new[:, -1] = T_right      # 右边界

            T = T_new
            T_history[n + 1] = T.copy()

    elif method == "crank_nicolson":
        # ===== Crank-Nicolson 方法 (二维) =====
        # Crank-Nicolson 是隐式方法，对时间采用梯形规则：
        # (T^{n+1} - T^n)/dt = 0.5 * L(T^{n+1} + T^n)
        #
        # 其中 L 是空间离散算子
        # 无条件稳定，精度 O(dt², dx², dy²)
        # 注意：二维 Crank-Nicolson 需要求解大型稀疏系统
        # 这里使用迭代法近似求解

        omega_x = alpha * dt / (2 * dx ** 2)
        omega_y = alpha * dt / (2 * dy ** 2)

        for n in range(nt):
            T_new = T.copy()

            for i in range(1, nx - 1):
                for j in range(1, ny - 1):
                    source = heat_source(x[i], y[j]) / 1.0 if heat_source else 0.0

                    # Crank-Nicolson 格式
                    T_new[j, i] = (
                        T[j, i]
                        + omega_x * (
                            T[j, i + 1] - 2 * T[j, i] + T[j, i - 1]
                            + T_new[j, i + 1] - 2 * T_new[j, i] + T_new[j, i - 1]
                        )
                        + omega_y * (
                            T[j + 1, i] - 2 * T[j, i] + T[j - 1, i]
                            + T_new[j + 1, i] - 2 * T_new[j, i] + T_new[j - 1, i]
                        )
                        + alpha * dt * source
                    )

            # 应用边界条件
            T_new[0, :] = T_bottom
            T_new[-1, :] = T_top
            T_new[:, 0] = T_left
            T_new[:, -1] = T_right

            T = T_new
            T_history[n + 1] = T.copy()

    else:
        raise ValueError(f"未知的方法: {method}")

    return x, y, T_history


def _solve_tridiagonal(
    lower: np.ndarray,
    main: np.ndarray,
    upper: np.ndarray,
    rhs: np.ndarray,
) -> np.ndarray:
    """
    托马斯算法 (Thomas Algorithm) 求解三对角线性方程组

    求解形式: A * x = b, 其中 A 是三对角矩阵

    参数
    ----------
    lower : np.ndarray
        下对角线元素 (长度 n-1)
    main : np.ndarray
        主对角线元素 (长度 n)
    upper : np.ndarray
        上对角线元素 (长度 n-1)
    rhs : np.ndarray
        右端项 (长度 n)

    返回
    -------
    x : np.ndarray
        方程组的解
    """
    n = len(main)
    c = np.zeros(n - 1)
    d = np.zeros(n)

    # 前向消元
    c[0] = upper[0] / main[0]
    d[0] = rhs[0] / main[0]

    for i in range(1, n):
        denom = main[i] - lower[i - 1] * c[i - 1]
        if i < n - 1:
            c[i] = upper[i] / denom
        d[i] = (rhs[i] - lower[i - 1] * d[i - 1]) / denom

    # 回代
    x = np.zeros(n)
    x[-1] = d[-1]
    for i in range(n - 2, -1, -1):
        x[i] = d[i] - c[i] * x[i + 1]

    return x
