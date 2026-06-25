"""
离散傅里叶变换 (DFT) 实现

朴素 DFT 实现，时间复杂度 O(N^2)，用于理解傅里叶变换的基本原理。

数学定义:
  X[k] = Σ_{n=0}^{N-1} x[n] * e^{-j*2*π*k*n/N},  k = 0, 1, ..., N-1

逆变换:
  x[n] = (1/N) * Σ_{k=0}^{N-1} X[k] * e^{j*2*π*k*n/N},  n = 0, 1, ..., N-1
"""

import numpy as np


def dft(x: np.ndarray) -> np.ndarray:
    """
    离散傅里叶变换 (DFT)

    将时域信号转换为频域表示。使用朴素的 O(N^2) 算法。

    参数:
        x: 输入时域信号，一维 numpy 数组（可以是实数或复数）

    返回:
        X: 频域表示，复数 numpy 数组，长度与输入相同

    示例:
        >>> import numpy as np
        >>> x = np.array([1.0, 2.0, 3.0, 4.0])
        >>> X = dft(x)
        >>> X.shape
        (4,)
    """
    x = np.asarray(x, dtype=complex)
    N = len(x)

    if N == 0:
        return np.array([], dtype=complex)

    if N == 1:
        return x.copy()

    # 构建 DFT 矩阵
    # W[n,k] = e^{-j*2*π*k*n/N}
    n = np.arange(N)
    k = n.reshape((N, 1))
    W = np.exp(-2j * np.pi * k * n / N)

    # 矩阵乘法: X = W @ x
    return W @ x


def idft(X: np.ndarray) -> np.ndarray:
    """
    离散傅里叶逆变换 (IDFT)

    将频域信号转换回时域表示。使用朴素的 O(N^2) 算法。

    参数:
        X: 频域信号，复数 numpy 数组

    返回:
        x: 时域表示，复数 numpy 数组

    示例:
        >>> import numpy as np
        >>> X = np.array([10+0j, -2+2j, -2+0j, -2-2j])
        >>> x = idft(X)
        >>> np.allclose(x, [1, 2, 3, 4])
        True
    """
    X = np.asarray(X, dtype=complex)
    N = len(X)

    if N == 0:
        return np.array([], dtype=complex)

    if N == 1:
        return X.copy()

    # 构建 IDFT 矩阵
    # W_inv[n,k] = e^{j*2*π*k*n/N} / N
    n = np.arange(N)
    k = n.reshape((N, 1))
    W_inv = np.exp(2j * np.pi * k * n / N) / N

    # 矩阵乘法: x = W_inv @ X
    return W_inv @ X


def dft_slow(x: np.ndarray) -> np.ndarray:
    """
    使用双重循环的 DFT 实现（更慢但更直观）

    直接按照数学定义逐元素计算，便于理解原理。

    参数:
        x: 输入时域信号

    返回:
        X: 频域表示
    """
    x = np.asarray(x, dtype=complex)
    N = len(x)
    X = np.zeros(N, dtype=complex)

    for k in range(N):
        for n in range(N):
            X[k] += x[n] * np.exp(-2j * np.pi * k * n / N)

    return X
