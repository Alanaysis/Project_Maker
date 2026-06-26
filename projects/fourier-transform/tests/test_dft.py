"""
Tests for DFT module
DFT 模块测试
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.dft import dft, idft, dft_matrix, magnitude_spectrum, phase_spectrum
from src.dft import frequency_axis, frequency_axis_positive, fftshift, ifftshift
from src.dft import dft_2d


class TestDFT:
    """Test DFT implementation against known results."""

    def test_dft_constant_signal(self):
        """DFT of a constant signal should have energy only at DC (k=0)."""
        N = 16
        x = np.ones(N)
        X = dft(x)
        # DC component should be N, all others should be ~0
        assert abs(X[0] - N) < 1e-10
        assert np.max(np.abs(X[1:])) < 1e-10

    def test_dft_single_frequency(self):
        """DFT of a sine wave should have peaks at the sine frequency."""
        sample_rate = 100
        duration = 1.0
        N = int(sample_rate * duration)
        freq = 5  # 5 Hz
        t = np.arange(N) / sample_rate
        x = np.sin(2 * np.pi * freq * t)
        X = dft(x)
        mag = magnitude_spectrum(X)
        # For real signals, DFT has peaks at both k and N-k
        peak_idx = np.argmax(mag[:N // 2])
        assert abs(peak_idx - freq) < 1

    def test_dft_complex_signal(self):
        """DFT should work on complex input."""
        N = 8
        x = np.array([1, 1j, -1, -1j, 0, 0, 0, 0], dtype=np.complex128)
        X = dft(x)
        assert len(X) == N
        assert X.dtype == np.complex128

    def test_dft_linear_combination(self):
        """DFT is linear: DFT(a*x + b*y) = a*DFT(x) + b*DFT(y)."""
        N = 16
        x1 = np.random.randn(N)
        x2 = np.random.randn(N)
        a, b = 2.5, -1.3
        X_sum = dft(a * x1 + b * x2)
        X_expected = a * dft(x1) + b * dft(x2)
        assert np.allclose(X_sum, X_expected, atol=1e-10)


class TestIDFT:
    """Test Inverse DFT implementation."""

    def test_idft_roundtrip(self):
        """IDFT(DFT(x)) should recover the original signal."""
        N = 16
        x = np.random.randn(N) + 1j * np.random.randn(N)
        X = dft(x)
        x_recovered = idft(X)
        assert np.allclose(x, x_recovered, atol=1e-10)

    def test_idft_real_signal(self):
        """IDFT of conjugate-symmetric spectrum should give real signal."""
        N = 16
        x = np.random.randn(N)
        X = dft(x)
        x_recovered = idft(X)
        # Real part should match original
        assert np.allclose(np.real(x_recovered), x, atol=1e-10)
        # Imaginary part should be ~0
        assert np.max(np.abs(np.imag(x_recovered))) < 1e-10

    def test_idft_zero_spectrum(self):
        """IDFT of all zeros should give all zeros."""
        N = 8
        X = np.zeros(N, dtype=np.complex128)
        x = idft(X)
        assert np.allclose(x, 0)


class TestDFTMatrix:
    """Test DFT matrix construction."""

    def test_dft_matrix_shape(self):
        """DFT matrix should be N x N."""
        for N in [4, 8, 16]:
            F = dft_matrix(N)
            assert F.shape == (N, N)

    def test_dft_matrix_multiply(self):
        """DFT via matrix multiplication should match direct DFT."""
        N = 8
        x = np.random.randn(N) + 1j * np.random.randn(N)
        F = dft_matrix(N)
        X_matrix = F @ x
        X_direct = dft(x)
        assert np.allclose(X_matrix, X_direct, atol=1e-10)


class TestSpectrumFunctions:
    """Test spectrum utility functions."""

    def test_magnitude_spectrum(self):
        """Magnitude spectrum should be non-negative."""
        X = np.array([1+1j, 2-1j, 0+0j, 3+3j])
        mag = magnitude_spectrum(X)
        assert np.all(mag >= 0)
        assert abs(mag[0] - np.sqrt(2)) < 1e-10

    def test_phase_spectrum(self):
        """Phase spectrum should return values in [-pi, pi]."""
        X = np.array([1+0j, 0+1j, -1+0j, 0-1j])
        phase = phase_spectrum(X)
        assert np.all(phase >= -np.pi)
        assert np.all(phase <= np.pi)
        assert abs(phase[1] - np.pi / 2) < 1e-10

    def test_frequency_axis(self):
        """Frequency axis should be correctly spaced."""
        N = 100
        sr = 1000
        freqs = frequency_axis(N, sr)
        assert freqs[0] == 0
        assert abs(freqs[-1] - (N - 1) * sr / N) < 1e-10
        assert abs(freqs[1] - freqs[0] - sr / N) < 1e-10

    def test_frequency_axis_positive(self):
        """Positive frequency axis should have correct length."""
        for N in [8, 16, 32, 100]:
            freqs, n_pos = frequency_axis_positive(N, 1000)
            assert n_pos == N // 2 + 1
            assert len(freqs) == n_pos


class TestShiftFunctions:
    """Test fftshift and ifftshift."""

    def test_fftshift_ifftshift(self):
        """ifftshift(fftshift(x)) should recover x."""
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8])
        assert np.array_equal(ifftshift(fftshift(x)), x)

    def test_fftshift_zero_freq_center(self):
        """fftshift should move zero-freq component to center."""
        X = np.array([10, 1, 2, 3, 4, 5, 6, 7])  # DC at index 0
        X_shifted = fftshift(X)
        # DC should now be near the center
        assert X_shifted[len(X) // 2] == 10


class TestDFT2D:
    """Test 2D DFT."""

    def test_dft_2d_identity(self):
        """2D DFT of a delta function should be all ones."""
        N = 4
        matrix = np.zeros((N, N))
        matrix[0, 0] = 1.0
        result = dft_2d(matrix)
        assert np.allclose(result, 1.0)

    def test_dft_2d_shape(self):
        """2D DFT should preserve shape."""
        matrix = np.random.randn(4, 6)
        result = dft_2d(matrix)
        assert result.shape == (4, 6)
