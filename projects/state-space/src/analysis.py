"""
可控性、可观性和稳定性分析

可控性矩阵: C = [B, AB, A²B, ..., A^(n-1)B]
可观性矩阵: O = [C; CA; CA²; ...; CA^(n-1)]

系统可控 <=> rank(C) = n
系统可观 <=> rank(O) = n

稳定性:
  连续时间: 所有特征值实部 < 0
  离散时间: 所有特征值模 < 1
"""

import numpy as np
from typing import Tuple


def controllability_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    计算可控性矩阵

    C = [B, AB, A²B, ..., A^(n-1)B]

    Args:
        A: 状态转移矩阵 (n x n)
        B: 输入矩阵 (n x m)

    Returns:
        C: 可控性矩阵 (n x n*m)
    """
    A = np.atleast_2d(np.array(A, dtype=float))
    B = np.atleast_2d(np.array(B, dtype=float))
    n = A.shape[0]

    # 构建可控性矩阵
    C = B.copy()
    AB = B.copy()
    for _ in range(n - 1):
        AB = A @ AB
        C = np.hstack([C, AB])

    return C


def observability_matrix(A: np.ndarray, C: np.ndarray) -> np.ndarray:
    """
    计算可观性矩阵

    O = [C; CA; CA²; ...; CA^(n-1)]

    Args:
        A: 状态转移矩阵 (n x n)
        C: 输出矩阵 (p x n)

    Returns:
        O: 可观性矩阵 (n*p x n)
    """
    A = np.atleast_2d(np.array(A, dtype=float))
    C = np.atleast_2d(np.array(C, dtype=float))
    n = A.shape[0]

    # 构建可观性矩阵
    O = C.copy()
    CA = C.copy()
    for _ in range(n - 1):
        CA = CA @ A
        O = np.vstack([O, CA])

    return O


def is_controllable(A: np.ndarray, B: np.ndarray, tol: float = 1e-10) -> bool:
    """
    判断系统是否可控

    Args:
        A: 状态转移矩阵
        B: 输入矩阵
        tol: 秩判断容差

    Returns:
        是否可控
    """
    A = np.atleast_2d(np.array(A, dtype=float))
    n = A.shape[0]
    Co = controllability_matrix(A, B)
    return np.linalg.matrix_rank(Co, tol=tol) == n


def is_observable(A: np.ndarray, C: np.ndarray, tol: float = 1e-10) -> bool:
    """
    判断系统是否可观

    Args:
        A: 状态转移矩阵
        C: 输出矩阵
        tol: 秩判断容差

    Returns:
        是否可观
    """
    A = np.atleast_2d(np.array(A, dtype=float))
    n = A.shape[0]
    Ob = observability_matrix(A, C)
    return np.linalg.matrix_rank(Ob, tol=tol) == n


def check_stability_continuous(A: np.ndarray) -> bool:
    """
    检查连续时间系统的稳定性

    连续时间系统稳定当且仅当所有特征值的实部严格为负。

    Args:
        A: 状态转移矩阵 (n x n)

    Returns:
        是否稳定
    """
    A = np.atleast_2d(np.array(A, dtype=float))
    eigenvalues = np.linalg.eigvals(A)
    return bool(np.all(np.real(eigenvalues) < 0))


def check_stability_discrete(A: np.ndarray) -> bool:
    """
    检查离散时间系统的稳定性

    离散时间系统稳定当且仅当所有特征值的模严格小于1。

    Args:
        A: 状态转移矩阵 (n x n)

    Returns:
        是否稳定
    """
    A = np.atleast_2d(np.array(A, dtype=float))
    eigenvalues = np.linalg.eigvals(A)
    return bool(np.all(np.abs(eigenvalues) < 1.0))


def stability_margin(A: np.ndarray, is_discrete: bool = True) -> float:
    """
    计算稳定性裕度

    对于离散时间系统: margin = 1 - max(|eigenvalue|)
    对于连续时间系统: margin = -max(Re(eigenvalue))

    Args:
        A: 状态转移矩阵 (n x n)
        is_discrete: 是否为离散时间系统

    Returns:
        稳定性裕度（正值表示稳定，负值表示不稳定）
    """
    A = np.atleast_2d(np.array(A, dtype=float))
    eigenvalues = np.linalg.eigvals(A)

    if is_discrete:
        return 1.0 - np.max(np.abs(eigenvalues))
    else:
        return -np.max(np.real(eigenvalues))


def controllability_index(A: np.ndarray, B: np.ndarray) -> int:
    """
    计算可控性指数（最小的k使得rank[C, AB, ..., A^(k-1)B] = n）

    Args:
        A: 状态转移矩阵
        B: 输入矩阵

    Returns:
        可控性指数
    """
    A = np.atleast_2d(np.array(A, dtype=float))
    B = np.atleast_2d(np.array(B, dtype=float))
    n = A.shape[0]

    C = B.copy()
    AB = B.copy()

    for k in range(1, n + 1):
        if np.linalg.matrix_rank(C) == n:
            return k
        AB = A @ AB
        C = np.hstack([C, AB])

    return n


def observability_index(A: np.ndarray, C: np.ndarray) -> int:
    """
    计算可观性指数

    Args:
        A: 状态转移矩阵
        C: 输出矩阵

    Returns:
        可观性指数
    """
    A = np.atleast_2d(np.array(A, dtype=float))
    C = np.atleast_2d(np.array(C, dtype=float))
    n = A.shape[0]

    O = C.copy()
    CA = C.copy()

    for k in range(1, n + 1):
        if np.linalg.matrix_rank(O) == n:
            return k
        CA = CA @ A
        O = np.vstack([O, CA])

    return n


def decompose_controllable(
    A: np.ndarray, B: np.ndarray, C: np.ndarray, tol: float = 1e-10
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
    """
    可控性分解

    将系统分解为可控和不可控部分

    Args:
        A: 状态转移矩阵
        B: 输入矩阵
        C: 输出矩阵
        tol: 容差

    Returns:
        A_bar: 变换后的A矩阵
        B_bar: 变换后的B矩阵
        C_bar: 变换后的C矩阵
        T: 变换矩阵
        n_c: 可控状态数
    """
    A = np.atleast_2d(np.array(A, dtype=float))
    B = np.atleast_2d(np.array(B, dtype=float))
    C = np.atleast_2d(np.array(C, dtype=float))
    n = A.shape[0]

    # 计算可控性矩阵
    Co = controllability_matrix(A, B)

    # 找到线性无关列
    _, _, pivot_cols = np.linalg.qr(Co.T, pivoting=True)
    n_c = np.linalg.matrix_rank(Co, tol=tol)

    # 构建变换矩阵
    T_cols = list(pivot_cols[:n_c])

    # 补充剩余列
    remaining = [i for i in range(n) if i not in T_cols]
    T_cols.extend(remaining[:n - n_c])

    T = np.eye(n)[:, T_cols]
    T_inv = np.linalg.inv(T)

    A_bar = T_inv @ A @ T
    B_bar = T_inv @ B
    C_bar = C @ T

    return A_bar, B_bar, C_bar, T, n_c


def gramian_controllability(A: np.ndarray, B: np.ndarray, N: int = 100) -> np.ndarray:
    """
    计算有限时间可控性格拉姆矩阵

    W_c = Σ(k=0 to N-1) A^k * B * B^T * (A^T)^k

    Args:
        A: 状态转移矩阵
        B: 输入矩阵
        N: 时间步数

    Returns:
        W_c: 可控性格拉姆矩阵
    """
    A = np.atleast_2d(np.array(A, dtype=float))
    B = np.atleast_2d(np.array(B, dtype=float))
    n = A.shape[0]

    W_c = np.zeros((n, n))
    A_k = np.eye(n)

    for _ in range(N):
        W_c += A_k @ B @ B.T @ A_k.T
        A_k = A @ A_k

    return W_c


def gramian_observability(A: np.ndarray, C: np.ndarray, N: int = 100) -> np.ndarray:
    """
    计算有限时间可观性格拉姆矩阵

    W_o = Σ(k=0 to N-1) (A^T)^k * C^T * C * A^k

    Args:
        A: 状态转移矩阵
        C: 输出矩阵
        N: 时间步数

    Returns:
        W_o: 可观性格拉姆矩阵
    """
    A = np.atleast_2d(np.array(A, dtype=float))
    C = np.atleast_2d(np.array(C, dtype=float))
    n = A.shape[0]

    W_o = np.zeros((n, n))
    A_k = np.eye(n)

    for _ in range(N):
        W_o += A_k.T @ C.T @ C @ A_k
        A_k = A @ A_k

    return W_o
