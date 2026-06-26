"""
Inverse FFT/DFT Implementation
逆 FFT/DFT 实现

This module provides functions for converting frequency-domain data
back to the time domain.

Mathematical Background / 数学背景:
    The Inverse DFT (IDFT) reconstructs the original time-domain signal
    from its frequency-domain representation.

    x[n] = (1/N) * sum_{k=0}^{N-1} X[k] * exp(j * 2*pi*k*n/N)

    Key relationship:
        IDFT(X) = conjugate(DFT(conjugate(X))) / N

    This means we can compute IDFT using our DFT function by:
        1. Conjugate the input
        2. Apply DFT
        3. Conjugate the result
        4. Divide by N
"""

import numpy as np
from .dft import dft, idft as _dft_idft
from .fft import fft as _fft
from typing import Union


def inverse_fft(X: np.ndarray, method: str = 'fft') -> np.ndarray:
    """
    Compute the inverse FFT to recover the time-domain signal.

    Uses the mathematical relationship between FFT and IFFT:
        IFFT(X) = conjugate(FFT(conjugate(X))) / N

    Args:
        X: Input frequency-domain signal (complex numpy array)
        method: 'fft' for conjugate method, 'direct' for direct IDFT

    Returns:
        Time-domain signal as complex numpy array

    Example:
        >>> signal = np.array([1, 2, 3, 4])
        >>> freq = fft(signal)
        >>> recovered = inverse_fft(freq)
        >>> np.allclose(signal, recovered)
        True
    """
    X = np.asarray(X, dtype=np.complex128)
    N = len(X)

    if method == 'fft':
        # Use the conjugate property: IFFT(X) = conj(FFT(conj(X))) / N
        X_conj = np.conj(X)
        fft_result = _fft(X_conj)
        return np.conj(fft_result) / N

    elif method == 'direct':
        # Direct IDFT computation
        return _dft_idft(X)

    else:
        raise ValueError(f"Unknown method: {method}. Use 'fft' or 'direct'.")


def inverse_dft(X: np.ndarray) -> np.ndarray:
    """
    Compute the inverse DFT (discrete computation).

    Args:
        X: Input frequency-domain signal

    Returns:
        Time-domain signal
    """
    return _dft_idft(X)


def ifft_shift(X: np.ndarray) -> np.ndarray:
    """
    Perform IFFT and shift zero-frequency to center.

    This is useful for visualizing the spectrum with zero frequency
    in the middle.

    Args:
        X: Frequency-domain signal (should be fftshifted first)

    Returns:
        Time-domain signal
    """
    # First undo the fftshift
    X_unshifted = np.fft.ifftshift(X) if hasattr(np.fft, 'ifftshift') else _ifftshift(X)
    return inverse_fft(X_unshifted)


def _ifftshift(X: np.ndarray) -> np.ndarray:
    """Inverse of fftshift for 1D arrays."""
    n = len(X)
    n_half = (n + 1) // 2
    return np.roll(X, n_half)


def reconstruct_signal(magnitude: np.ndarray, phase: np.ndarray) -> np.ndarray:
    """
    Reconstruct a time-domain signal from magnitude and phase spectra.

    Given |X[k]| and angle(X[k]), reconstruct X[k] = |X[k]| * exp(j * angle(X[k]))
    then compute the inverse FFT.

    Args:
        magnitude: Magnitude spectrum |X[k]|
        phase: Phase spectrum angle(X[k]) in radians

    Returns:
        Reconstructed time-domain signal (real part)
    """
    # Combine magnitude and phase to get complex spectrum
    X = magnitude * np.exp(1j * phase)

    # Compute inverse FFT
    x = inverse_fft(X)

    # For real signals, take the real part (imaginary part should be ~0)
    return np.real(x)


def reconstruct_with_hilbert(magnitude: np.ndarray, phase: np.ndarray) -> np.ndarray:
    """
    Reconstruct signal and verify the imaginary part is negligible.

    Args:
        magnitude: Magnitude spectrum
        phase: Phase spectrum

    Returns:
        Tuple of (real_signal, max_imaginary_error)
    """
    x = reconstruct_signal(magnitude, phase)
    # Also get the imaginary part to check reconstruction quality
    X = magnitude * np.exp(1j * phase)
    x_full = inverse_fft(X)
    max_imag = np.max(np.abs(np.imag(x_full)))

    return x, max_imag
