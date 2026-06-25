"""
快速傅里叶变换 (FFT) 实现

Cooley-Tukey FFT 算法，时间复杂度 O(N log N)。

核心思想:
  将 DFT 分解为偶数索引和奇数索引两部分，递归计算:
    X[k] = E[k] + W_N^k * O[k]
    X[k + N/2] = E[k] - W_N^k * O[k]

  其中:
    E[k] = DFT of even-indexed samples
    O[k] = DFT of odd-indexed samples
    W_N^k = e^{-j*2*π*k/N} (twiddle factor)
"""

import numpy as np


def fft(x: np.ndarray) -> np.ndarray:
    """
    快速傅里叶变换 (FFT)

    使用 Cooley-Tukey 算法的递归实现。
    输入长度必须为 2 的幂，否则会自动补零。

    参数:
        x: 输入时域信号，一维 numpy 数组

    返回:
        X: 频域表示，复数 numpy 数组

    时间复杂度: O(N log N)
    空间复杂度: O(N)

    示例:
        >>> import numpy as np
        >>> x = np.array([1.0, 2.0, 3.0, 4.0])
        >>> X = fft(x)
        >>> X.shape
        (4,)
    """
    x = np.asarray(x, dtype=complex)
    N = len(x)

    if N == 0:
        return np.array([], dtype=complex)

    # 补零到 2 的幂
    if N & (N - 1) != 0:
        next_power = 1
        while next_power < N:
            next_power <<= 1
        x = np.pad(x, (0, next_power - N), mode="constant")
        N = next_power

    return _fft_recursive(x)


def _fft_recursive(x: np.ndarray) -> np.ndarray:
    """FFT 递归核心实现"""
    N = len(x)

    # 基础情况
    if N == 1:
        return x.copy()

    if N == 2:
        return np.array([x[0] + x[1], x[0] - x[1]], dtype=complex)

    # 分治: 偶数和奇数索引
    even = _fft_recursive(x[0::2])  # 偶数索引
    odd = _fft_recursive(x[1::2])   # 奇数索引

    # 旋转因子 (twiddle factors)
    # W_N^k = e^{-j*2*π*k/N}, k = 0, 1, ..., N/2-1
    k = np.arange(N // 2)
    twiddle = np.exp(-2j * np.pi * k / N)

    # 蝶形运算
    # X[k] = E[k] + W_N^k * O[k]
    # X[k + N/2] = E[k] - W_N^k * O[k]
    t = twiddle * odd
    X = np.concatenate([even + t, even - t])

    return X


def fft_radix2(x: np.ndarray) -> np.ndarray:
    """
    基于 2 的 Radix-2 FFT 迭代实现

    非递归版本，使用位反转和蝶形运算。
    输入长度必须为 2 的幂。

    参数:
        x: 输入时域信号，长度必须为 2 的幂

    返回:
        X: 频域表示

    示例:
        >>> import numpy as np
        >>> x = np.array([1.0, 2.0, 3.0, 4.0])
        >>> X = fft_radix2(x)
        >>> X.shape
        (4,)
    """
    x = np.asarray(x, dtype=complex)
    N = len(x)

    if N == 0:
        return np.array([], dtype=complex)

    # 验证长度是 2 的幂
    if N & (N - 1) != 0:
        raise ValueError(
            f"输入长度必须为 2 的幂，当前长度: {N}. "
            "请使用 fft() 函数（自动补零）或确保输入长度为 2 的幂。"
        )

    # 位反转排列
    X = _bit_reverse_copy(x)

    # 蝶形运算
    length = 2
    while length <= N:
        half = length // 2
        # 旋转因子
        k = np.arange(half)
        twiddle = np.exp(-2j * np.pi * k / length)

        for start in range(0, N, length):
            for j in range(half):
                idx_even = start + j
                idx_odd = start + j + half
                t = twiddle[j] * X[idx_odd]
                X[idx_odd] = X[idx_even] - t
                X[idx_even] = X[idx_even] + t

        length <<= 1

    return X


def _bit_reverse_copy(x: np.ndarray) -> np.ndarray:
    """位反转排列"""
    N = len(x)
    bits = int(np.log2(N))
    result = np.zeros(N, dtype=complex)

    for i in range(N):
        # 计算位反转索引
        rev = 0
        temp = i
        for _ in range(bits):
            rev = (rev << 1) | (temp & 1)
            temp >>= 1
        result[rev] = x[i]

    return result


def ifft(X: np.ndarray) -> np.ndarray:
    """
    快速傅里叶逆变换 (IFFT)

    使用 FFT 实现逆变换: x = (1/N) * conj(FFT(conj(X)))

    参数:
        X: 频域信号，复数 numpy 数组

    返回:
        x: 时域表示，复数 numpy 数组

    示例:
        >>> import numpy as np
        >>> X = np.array([10+0j, -2+2j, -2+0j, -2-2j])
        >>> x = ifft(X)
        >>> np.allclose(x.real, [1, 2, 3, 4])
        True
    """
    X = np.asarray(X, dtype=complex)
    N = len(X)

    if N == 0:
        return np.array([], dtype=complex)

    # 利用 FFT 计算 IFFT
    # x = (1/N) * conj(FFT(conj(X)))
    x = np.conj(fft(np.conj(X))) / N

    return x


def fft2d(x: np.ndarray) -> np.ndarray:
    """
    二维 FFT

    对 2D 数组先对每行做 FFT，再对每列做 FFT。

    参数:
        x: 二维输入数组, shape (M, N)

    返回:
        X: 二维频域表示

    示例:
        >>> import numpy as np
        >>> x = np.ones((4, 4))
        >>> X = fft2d(x)
        >>> X[0, 0]  # 直流分量
        (16+0j)
    """
    x = np.asarray(x, dtype=complex)

    if x.ndim != 2:
        raise ValueError(f"输入必须是 2D 数组，当前维度: {x.ndim}")

    # 对每行做 FFT
    X = np.array([fft(row) for row in x])

    # 对每列做 FFT
    X = np.array([fft(col) for col in X.T]).T

    return X
