"""
FFT (Fast Fourier Transform) - Cooley-Tukey Algorithm Implementation
FFT (快速傅里叶变换) - Cooley-Tukey 算法实现

The Cooley-Tukey FFT is the most common FFT algorithm. It uses a
divide-and-conquer approach to reduce the complexity of DFT from O(N^2)
to O(N log N).

Key Idea / 核心思想:
    Split the DFT computation into smaller DFTs of even and odd indexed
    elements, then combine the results.

    X[k] = sum_even + exp(-j*2*pi*k/N) * sum_odd

This recursive splitting continues until we reach base cases of size 1.
"""

import numpy as np
from typing import Optional


def fft(x: np.ndarray) -> np.ndarray:
    """
    Compute the FFT using the Cooley-Tukey radix-2 decimation-in-time algorithm.

    This is a recursive implementation that splits the input into even and
    odd indexed elements, computes FFT on each half, and combines the results.

    Complexity: O(N log N) vs O(N^2) for direct DFT

    Args:
        x: Input time-domain signal (1D numpy array)

    Returns:
        FFT result as complex numpy array

    Note:
        Input length must be a power of 2. If not, it will be zero-padded.
    """
    x = np.asarray(x, dtype=np.complex128)
    N = len(x)

    # Base case: DFT of length 1 is just the element itself
    if N <= 1:
        return x.copy()

    # If N is not a power of 2, zero-pad to next power of 2
    if (N & (N - 1)) != 0:
        next_pow2 = 1
        while next_pow2 < N:
            next_pow2 <<= 1
        padded = np.zeros(next_pow2, dtype=np.complex128)
        padded[:N] = x
        return fft(padded)

    # Divide: split into even and odd indexed elements
    even = fft(x[0::2])  # Even-indexed elements
    odd = fft(x[1::2])   # Odd-indexed elements

    # Combine: use the "butterfly" operation
    # X[k] = E[k] + W_N^k * O[k]
    # X[k+N/2] = E[k] - W_N^k * O[k]
    # where W_N^k = exp(-j * 2*pi*k/N) is the "twiddle factor"
    T = np.exp(-2j * np.pi * np.arange(N // 2) / N)
    combined = np.empty(N, dtype=np.complex128)
    for k in range(N // 2):
        combined[k] = even[k] + T[k] * odd[k]
        combined[k + N // 2] = even[k] - T[k] * odd[k]

    return combined


def fft_iterative(x: np.ndarray) -> np.ndarray:
    """
    Compute the FFT using an iterative (non-recursive) Cooley-Tukey approach
    with bit-reversal permutation.

    This version avoids recursion overhead and is more practical for production use.

    Algorithm steps:
        1. Bit-reverse the input order
        2. Perform butterfly operations in log2(N) stages
        3. Each stage combines pairs of elements using twiddle factors

    Args:
        x: Input time-domain signal

    Returns:
        FFT result as complex numpy array
    """
    x = np.asarray(x, dtype=np.complex128)
    N = len(x)

    if N <= 1:
        return x.copy()

    # Find next power of 2
    if (N & (N - 1)) != 0:
        next_pow2 = 1
        while next_pow2 < N:
            next_pow2 <<= 1
        padded = np.zeros(next_pow2, dtype=np.complex128)
        padded[:N] = x
        return fft_iterative(padded)

    # Step 1: Bit-reversal permutation
    x = _bit_reverse_copy(x)

    # Step 2: Butterfly operations
    # Process log2(N) stages, each with increasing group sizes
    num_stages = int(np.log2(N))
    stage_size = 2  # Start with pairs

    for _ in range(num_stages):
        half_size = stage_size // 2
        # Twiddle factor step for this stage
        angle_step = -2.0 * np.pi / stage_size

        for start in range(0, N, stage_size):
            for k in range(half_size):
                # Compute twiddle factor
                twiddle = np.exp(1j * angle_step * k)

                # Butterfly operation
                even_idx = start + k
                odd_idx = start + k + half_size

                even_val = x[even_idx]
                odd_val = x[odd_idx] * twiddle

                x[even_idx] = even_val + odd_val
                x[odd_idx] = even_val - odd_val

        stage_size *= 2

    return x


def _bit_reverse_copy(x: np.ndarray) -> np.ndarray:
    """
    Permute array elements according to bit-reversed indices.

    For example, with N=8:
        index 0 (000) -> 0 (000)
        index 1 (001) -> 4 (100)
        index 2 (010) -> 2 (010)
        index 3 (011) -> 6 (110)
        ...

    Args:
        x: Input array

    Returns:
        Bit-reversed copy of input
    """
    N = len(x)
    num_bits = int(np.log2(N))
    result = np.empty_like(x)

    for i in range(N):
        # Reverse the bits of index i
        rev_i = 0
        temp = i
        for _ in range(num_bits):
            rev_i = (rev_i << 1) | (temp & 1)
            temp >>= 1

        result[rev_i] = x[i]

    return result


def fft_complexity_analysis(N: int) -> dict:
    """
    Analyze and compare the complexity of DFT vs FFT.

    Args:
        N: Number of samples

    Returns:
        Dictionary with complexity information
    """
    dft_ops = N * N
    fft_ops = N * int(np.log2(N)) if N > 0 else 0
    speedup = dft_ops / fft_ops if fft_ops > 0 else float('inf')

    return {
        'N': N,
        'DFT_operations': dft_ops,
        'FFT_operations': fft_ops,
        'Speedup_factor': f"{speedup:.1f}x",
        'DFT_complexity': 'O(N^2)',
        'FFT_complexity': 'O(N log N)',
    }


def next_power_of_2(n: int) -> int:
    """
    Find the smallest power of 2 greater than or equal to n.

    Args:
        n: Input number

    Returns:
        Next power of 2
    """
    if n <= 1:
        return 1
    power = 1
    while power < n:
        power <<= 1
    return power
