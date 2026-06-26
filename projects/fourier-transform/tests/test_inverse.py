"""
Tests for Inverse FFT module
逆 FFT 模块测试
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.fft import fft
from src.inverse import inverse_fft, inverse_dft, reconstruct_signal, reconstruct_with_hilbert
from src.dft import dft, magnitude_spectrum


class TestInverseFFT:
    """Test inverse FFT implementation."""

    def test_ifft_roundtrip_complex(self):
        """IFFT(FFT(x)) should recover the original signal."""
        for N in [4, 8, 16, 32]:
            x = np.random.randn(N) + 1j * np.random.randn(N)
            X = fft(x)
            x_recovered = inverse_fft(X)
            assert np.allclose(x, x_recovered, atol=1e-10), f"Failed for N={N}"

    def test_ifft_roundtrip_real(self):
        """IFFT(FFT(x)) should recover real signal."""
        for N in [4, 8, 16, 32]:
            x = np.random.randn(N)
            X = fft(x)
            x_recovered = inverse_fft(X)
            assert np.allclose(np.real(x_recovered), x, atol=1e-10), f"Failed for N={N}"
            assert np.max(np.abs(np.imag(x_recovered))) < 1e-10

    def test_ifft_equals_idft(self):
        """IFFT via conjugate method should match direct IDFT."""
        N = 16
        X = np.random.randn(N) + 1j * np.random.randn(N)
        X_ifft = inverse_fft(X, method='fft')
        X_idft = inverse_dft(X)
        assert np.allclose(X_ifft, X_idft, atol=1e-10)

    def test_ifft_zero_spectrum(self):
        """IFFT of zero spectrum should give zero signal."""
        N = 8
        X = np.zeros(N, dtype=np.complex128)
        x = inverse_fft(X)
        assert np.allclose(x, 0)

    def test_ifft_single_bin(self):
        """IFFT of single bin should give a complex exponential."""
        N = 16
        k = 3
        X = np.zeros(N, dtype=np.complex128)
        X[k] = 1.0
        x = inverse_fft(X)
        # Should be exp(j * 2*pi * k * n / N) / N
        for n in range(N):
            expected = np.exp(2j * np.pi * k * n / N) / N
            assert abs(x[n] - expected) < 1e-10


class TestReconstructSignal:
    """Test signal reconstruction from magnitude and phase."""

    def test_reconstruct_roundtrip(self):
        """Reconstructing from magnitude and phase should recover the signal."""
        N = 16
        x = np.random.randn(N) + 1j * np.random.randn(N)
        X = fft(x)
        mag = magnitude_spectrum(X)
        phase = np.angle(X)
        x_recovered = reconstruct_signal(mag, phase)
        assert np.allclose(x_recovered, np.real(x), atol=1e-10)

    def test_reconstruct_real_signal(self):
        """Reconstruction of real signal should have negligible imaginary part."""
        N = 16
        x = np.random.randn(N)
        X = fft(x)
        mag = magnitude_spectrum(X)
        phase = np.angle(X)
        x_recovered, max_imag = reconstruct_with_hilbert(mag, phase)
        assert np.allclose(x_recovered, x, atol=1e-10)
        assert max_imag < 1e-10
