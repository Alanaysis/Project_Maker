"""
特征值分解模块

特征值分解是 PCA 的核心数学工具。对于一个实对称矩阵 C（协方差矩阵），
可以分解为：

    C = V * Λ * V^T

其中：
    - V 是特征向量矩阵（列向量），构成正交基
    - Λ 是特征值对角矩阵，表示各主成分方向上的方差

特征值越大，对应的特征向量方向上的数据方差越大，即该主成分越重要。

本模块实现两种特征值分解方法：
1. 幂迭代法（Power Iteration）：迭代求解最大特征值和对应特征向量
2. QR 分解法（QR Algorithm）：求解所有特征值和特征向量
"""

import numpy as np
from numpy.typing import NDArray


def power_iteration(
    A: NDArray[np.float64],
    max_iter: int = 1000,
    tol: float = 1e-10,
) -> tuple[float, NDArray[np.float64]]:
    """
    幂迭代法求解矩阵的最大特征值和对应特征向量。

    算法原理：
        从一个随机向量 v 开始，反复执行 v = A * v / ||A * v||，
        v 会收敛到最大特征值对应的特征向量。

    Parameters
    ----------
    A : np.ndarray of shape (n, n)
        实对称矩阵（如协方差矩阵）。
    max_iter : int
        最大迭代次数。
    tol : float
        收敛阈值，当特征向量变化小于此值时停止。

    Returns
    -------
    eigenvalue : float
        最大特征值。
    eigenvector : np.ndarray of shape (n,)
        对应的特征向量（单位向量）。
    """
    n = A.shape[0]

    # 随机初始化向量
    v = np.random.randn(n)
    v = v / np.linalg.norm(v)

    eigenvalue = 0.0

    for i in range(max_iter):
        # 矩阵向量乘法
        Av = A @ v

        # 计算特征值（Rayleigh quotient）
        eigenvalue_new = v @ Av

        # 归一化
        v_new = Av / np.linalg.norm(Av)

        # 检查收敛
        if np.abs(eigenvalue_new - eigenvalue) < tol:
            return eigenvalue_new, v_new

        v = v_new
        eigenvalue = eigenvalue_new

    return eigenvalue, v


def deflate(A: NDArray[np.float64], eigenvalue: float, eigenvector: NDArray[np.float64]) -> NDArray[np.float64]:
    """
    矩阵压缩（Deflation）：从矩阵中去除已求得的特征分量。

    通过 A' = A - λ * v * v^T，可以移除最大特征值对应的分量，
    使得下一次幂迭代可以求得次大特征值。

    Parameters
    ----------
    A : np.ndarray of shape (n, n)
        原矩阵。
    eigenvalue : float
        已求得的特征值。
    eigenvector : np.ndarray of shape (n,)
        对应的特征向量。

    Returns
    -------
    A_deflated : np.ndarray of shape (n, n)
        压缩后的矩阵。
    """
    return A - eigenvalue * np.outer(eigenvector, eigenvector)


def eigen_decomposition_power(
    A: NDArray[np.float64],
    n_components: int | None = None,
    max_iter: int = 1000,
    tol: float = 1e-10,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """
    使用幂迭代+压缩法求解矩阵的前 k 个特征值和特征向量。

    Parameters
    ----------
    A : np.ndarray of shape (n, n)
        实对称矩阵。
    n_components : int or None
        要提取的特征值数量。默认为 n（全部）。
    max_iter : int
        每次幂迭代的最大迭代次数。
    tol : float
        收敛阈值。

    Returns
    -------
    eigenvalues : np.ndarray of shape (k,)
        从大到小排列的特征值。
    eigenvectors : np.ndarray of shape (n, k)
        对应的特征向量矩阵（列向量）。
    """
    n = A.shape[0]

    if n_components is None:
        n_components = n

    n_components = min(n_components, n)

    eigenvalues = np.zeros(n_components)
    eigenvectors = np.zeros((n, n_components))

    A_copy = A.copy()

    for i in range(n_components):
        eigenvalue, eigenvector = power_iteration(A_copy, max_iter, tol)
        eigenvalues[i] = eigenvalue
        eigenvectors[:, i] = eigenvector
        A_copy = deflate(A_copy, eigenvalue, eigenvector)

    return eigenvalues, eigenvectors


def qr_algorithm(
    A: NDArray[np.float64],
    max_iter: int = 1000,
    tol: float = 1e-10,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """
    QR 算法求解矩阵的所有特征值和特征向量。

    算法原理：
        反复执行 QR 分解：A_k = Q_k * R_k，然后令 A_{k+1} = R_k * Q_k。
        A_k 会收敛到上三角矩阵（或对角矩阵），对角线元素即为特征值。

    为了提高收敛速度，使用带位移的 QR 算法（Wilkinson shift）。

    Parameters
    ----------
    A : np.ndarray of shape (n, n)
        实对称矩阵。
    max_iter : int
        最大迭代次数。
    tol : float
        收敛阈值（非对角线元素的最大绝对值）。

    Returns
    -------
    eigenvalues : np.ndarray of shape (n,)
        从大到小排列的特征值。
    eigenvectors : np.ndarray of shape (n, n)
        对应的特征向量矩阵。
    """
    n = A.shape[0]
    A_k = A.copy().astype(np.float64)
    Q_total = np.eye(n, dtype=np.float64)

    for _ in range(max_iter):
        # 检查是否已收敛（非对角线元素足够小）
        off_diag = np.abs(A_k - np.diag(np.diag(A_k)))
        if np.max(off_diag) < tol:
            break

        # Wilkinson shift：使用右下角 2x2 子矩阵的特征值作为位移
        # 取最接近 A_k[-1, -1] 的那个特征值
        if n >= 2:
            a = A_k[-2, -2]
            b = A_k[-2, -1]
            d = A_k[-1, -1]
            # 2x2 矩阵 [[a, b], [b, d]] 的特征值
            delta = (a - d) / 2.0
            sign = 1.0 if delta >= 0 else -1.0
            # 避免除以零
            if abs(delta) < 1e-15:
                sigma = d - abs(b)
            else:
                sigma = d - sign * b**2 / (abs(delta) + np.sqrt(delta**2 + b**2))
        else:
            sigma = A_k[-1, -1]

        # QR 分解
        Q, R = np.linalg.qr(A_k - sigma * np.eye(n))

        # 更新
        A_k = R @ Q + sigma * np.eye(n)
        Q_total = Q_total @ Q

    eigenvalues = np.diag(A_k)

    # 按从大到小排序
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = Q_total[:, idx]

    return eigenvalues, eigenvectors


def eigen_decomposition(
    A: NDArray[np.float64],
    n_components: int | None = None,
    method: str = "qr",
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """
    对实对称矩阵进行特征值分解。

    Parameters
    ----------
    A : np.ndarray of shape (n, n)
        实对称矩阵（如协方差矩阵）。
    n_components : int or None
        要返回的特征值/向量数量。默认为全部。
    method : str
        分解方法："qr"（QR算法）或 "power"（幂迭代法）。

    Returns
    -------
    eigenvalues : np.ndarray of shape (k,)
        从大到小排列的特征值。
    eigenvectors : np.ndarray of shape (n, k)
        对应的特征向量矩阵（列向量）。
    """
    A = np.asarray(A, dtype=np.float64)

    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError(f"输入必须是方阵，当前形状: {A.shape}")

    # 确保矩阵对称（处理数值误差）
    A = (A + A.T) / 2.0

    if method == "qr":
        eigenvalues, eigenvectors = qr_algorithm(A)
    elif method == "power":
        eigenvalues, eigenvectors = eigen_decomposition_power(A, n_components)
    else:
        raise ValueError(f"未知的分解方法: {method}，支持 'qr' 或 'power'")

    if n_components is not None:
        eigenvalues = eigenvalues[:n_components]
        eigenvectors = eigenvectors[:, :n_components]

    return eigenvalues, eigenvectors
