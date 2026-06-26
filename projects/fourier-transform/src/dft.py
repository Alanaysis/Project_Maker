"""
DFT (Discrete Fourier Transform) Implementation
离散傅里叶变换实现

Mathematical Background / 数学背景:
    DFT transforms a finite sequence of N time-domain samples into
    a finite sequence of N frequency-domain coefficients.

    X[k] = sum(x[n] * exp(-j * 2 * pi * k * n / N)) for n = 0 to N-1

    Where:
        x[n]     - input time-domain signal
        X[k]     - output frequency-domain representation
        N        - number of samples
        k        - frequency index (0 to N-1)
        j        - imaginary unit (sqrt(-1))
"""

import numpy as np
from typing import Tuple


def dft(x: np.ndarray) -> np.ndarray:
    """
    Compute the DFT of a signal using the direct definition.

    Args:
        x: Input time-domain signal (1D numpy array)

    Returns:
        DFT result as complex numpy array

    Formula:
        X[k] = sum_{n=0}^{N-1} x[n] * exp(-j * 2*pi*k*n/N)
    """
    x = np.asarray(x, dtype=np.complex128)
    N = len(x)
    X = np.zeros(N, dtype=np.complex128)

    for k in range(N):
        for n in range(N):
            # exp(-j * 2*pi*k*n/N) = cos(2*pi*k*n/N) - j*sin(2*pi*k*n/N)
            angle = -2.0 * np.pi * k * n / N
            X[k] += x[n] * np.exp(1j * angle)

    return X


def dft_matrix(N: int) -> np.ndarray:
    """
    Construct the DFT matrix of size N x N.

    The DFT matrix F has elements:
        F[k, n] = exp(-j * 2*pi*k*n/N)

    This matrix can be used to compute DFT via matrix multiplication:
        X = F @ x

    Args:
        N: Size of the DFT matrix

    Returns:
        N x N DFT matrix (complex)
    """
    k = np.arange(N).reshape(-1, 1)  # Column vector
    n = np.arange(N).reshape(1, -1)  # Row vector
    # Compute the exponent matrix
    exponent = -2j * np.pi * k * n / N
    return np.exp(exponent)


def idft(X: np.ndarray) -> np.ndarray:
    """
    Compute the Inverse DFT to recover the time-domain signal.

    Args:
        X: Input frequency-domain signal (1D numpy array)

    Returns:
        Inverse DFT result as complex numpy array

    Formula:
        x[n] = (1/N) * sum_{k=0}^{N-1} X[k] * exp(j * 2*pi*k*n/N)
    """
    X = np.asarray(X, dtype=np.complex128)
    N = len(X)
    x = np.zeros(N, dtype=np.complex128)

    for n in range(N):
        for k in range(N):
            angle = 2.0 * np.pi * k * n / N
            x[n] += X[k] * np.exp(1j * angle)

    return x / N


def dft_2d(matrix: np.ndarray) -> np.ndarray:
    """
    Compute the 2D DFT of a matrix (e.g., an image).

    The 2D DFT applies DFT along rows and then along columns:
        X[u, v] = sum_{m} sum_{n} x[m, n] * exp(-j*2*pi*u*m/M) * exp(-j*2*pi*v*n/N)

    Args:
        matrix: 2D input matrix

    Returns:
        2D DFT result as complex matrix
    """
    matrix = np.asarray(matrix, dtype=np.complex128)
    M, N = matrix.shape

    # Apply DFT along rows first
    row_dft = np.zeros((M, N), dtype=np.complex128)
    for m in range(M):
        row_dft[m, :] = dft(matrix[m, :])

    # Apply DFT along columns
    result = np.zeros((M, N), dtype=np.complex128)
    for n in range(N):
        result[:, n] = dft(row_dft[:, n])

    return result


def magnitude_spectrum(X: np.ndarray) -> np.ndarray:
    """
    Compute the magnitude spectrum from DFT output.

    |X[k]| = sqrt(re(X[k])^2 + im(X[k])^2)

    Args:
        X: DFT output (complex array)

    Returns:
        Magnitude spectrum (real array)
    """
    return np.abs(X)


def phase_spectrum(X: np.ndarray) -> np.ndarray:
    """
    Compute the phase spectrum from DFT output.

    angle(X[k]) = arctan(im(X[k]) / re(X[k]))

    Args:
        X: DFT output (complex array)

    Returns:
        Phase spectrum in radians (real array)
    """
    return np.angle(X)


def frequency_axis(N: float, sample_rate: float) -> np.ndarray:
    """
    Compute the frequency axis corresponding to DFT bins.

    For a signal of length N sampled at sample_rate Hz:
        frequency[k] = k * sample_rate / N  for k = 0, 1, ..., N-1

    Args:
        N: Number of samples
        sample_rate: Sampling rate in Hz

    Returns:
        Frequency axis array
    """
    return np.arange(N) * sample_rate / N


def frequency_axis_positive(N: float, sample_rate: float) -> Tuple[np.ndarray, int]:
    """
    Compute the positive frequency axis for real signals.

    For real signals, the DFT is symmetric, so we only show the
    first half (positive frequencies).

    Args:
        N: Number of samples
        sample_rate: Sampling rate in Hz

    Returns:
        Tuple of (positive frequencies, number of positive freq bins)
    """
    n_positive = N // 2 + 1
    freqs = np.arange(n_positive) * sample_rate / N
    return freqs, n_positive


def fftshift(X: np.ndarray, axes: Tuple[int, ...] = None) -> np.ndarray:
    """
    Shift zero-frequency component to the center of the spectrum.

    This rearranges DFT output so that zero frequency is in the middle,
    making it easier to visualize symmetric spectra.

    Args:
        X: Input array (frequency domain)
        axes: Axes along which to perform the shift

    Returns:
        Shifted array
    """
    X = np.asarray(X)
    if axes is None:
        axes = tuple(range(X.ndim))

    result = X.copy()
    for ax in axes:
        n = X.shape[ax]
        n_half = n // 2
        # Swap first half with second half along the given axis
        indices = np.concatenate([np.arange(n_half, n), np.arange(n_half)])
        result = np.roll(result, -n_half, axis=ax)

    return result


def ifftshift(X: np.ndarray, axes: Tuple[int, ...] = None) -> np.ndarray:
    """
    Inverse of fftshift: move zero-frequency component back to corners.

    Args:
        X: Input array
        axes: Axes along which to perform the inverse shift

    Returns:
        Unshifted array
    """
    X = np.asarray(X)
    if axes is None:
        axes = tuple(range(X.ndim))

    result = X.copy()
    for ax in axes:
        n = X.shape[ax]
        n_half = (n + 1) // 2
        result = np.roll(result, n_half, axis=ax)

    return result
