"""
Tests for FFT module
FFT 模块测试
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.fft import fft, fft_iterative, _bit_reverse_copy, fft_complexity_analysis
from src.fft import next_power_of_2
from src.dft import dft, magnitude_spectrum


class TestFFT:
    """Test FFT implementation."""

    def test_fft_equals_dft(self):
        """FFT should give the same result as DFT."""
        for N in [4, 8, 16, 32]:
            x = np.random.randn(N) + 1j * np.random.randn(N)
            X_fft = fft(x)
            X_dft = dft(x)
            assert np.allclose(X_fft, X_dft, atol=1e-10), f"Failed for N={N}"

    def test_fft_real_signal(self):
        """FFT of real signal should have conjugate symmetry."""
        N = 16
        x = np.random.randn(N)
        X = fft(x)
        for k in range(1, N):
            expected = np.conj(X[N - k])
            assert abs(X[k] - expected) < 1e-10

    def test_fft_power_conservation(self):
        """Parseval's theorem: energy in time == energy in frequency."""
        N = 16
        x = np.random.randn(N) + 1j * np.random.randn(N)
        X = fft(x)
        time_energy = np.sum(np.abs(x) ** 2)
        freq_energy = np.sum(np.abs(X) ** 2) / N  # Parseval's: sum(|x|²) = (1/N)*sum(|X|²)
        assert abs(time_energy - freq_energy) < 1e-8

    def test_fft_zero_signal(self):
        """FFT of all zeros should give all zeros."""
        N = 8
        x = np.zeros(N)
        X = fft(x)
        assert np.allclose(X, 0)

    def test_fft_single_impulse(self):
        """FFT of Kronecker delta should be all ones."""
        N = 8
        x = np.zeros(N)
        x[0] = 1.0
        X = fft(x)
        assert np.allclose(X, 1.0)

    def test_fft_autocorrelation(self):
        """FFT of autocorrelation should give power spectrum."""
        N = 16
        x = np.random.randn(N)
        X = fft(x)
        power = np.abs(X) ** 2
        # Autocorrelation at lag 0 should equal sum of power
        autocorr_0 = np.sum(np.conj(x) * x)
        assert abs(autocorr_0 - np.sum(power) / N) < 1e-8  # Parseval's theorem


class TestFFTIterative:
    """Test iterative FFT implementation."""

    def test_iterative_equals_recursive(self):
        """Iterative FFT should match recursive FFT."""
        for N in [4, 8, 16, 32]:
            x = np.random.randn(N) + 1j * np.random.randn(N)
            X_rec = fft(x)
            X_iter = fft_iterative(x)
            assert np.allclose(X_rec, X_iter, atol=1e-10), f"Failed for N={N}"

    def test_iterative_real_signal(self):
        """Iterative FFT of real signal should have conjugate symmetry."""
        N = 16
        x = np.random.randn(N)
        X = fft_iterative(x)
        for k in range(1, N):
            expected = np.conj(X[N - k])
            assert abs(X[k] - expected) < 1e-10


class TestBitReverse:
    """Test bit-reversal permutation."""

    def test_bit_reverse_identity(self):
        """Bit-reversal of already-reversed should give original (for symmetric indices)."""
        N = 8
        x = np.arange(N)
        result = _bit_reverse_copy(x)
        # Index 0 (000) -> 0 (000)
        assert result[0] == 0
        # Index 1 (001) -> 4 (100)
        assert result[4] == 1
        # Index 2 (010) -> 2 (010)
        assert result[2] == 2

    def test_bit_reverse_permutation(self):
        """Bit-reversal should be a permutation."""
        N = 16
        x = np.arange(N)
        result = _bit_reverse_copy(x)
        assert sorted(result) == list(range(N))


class TestComplexityAnalysis:
    """Test complexity analysis utility."""

    def test_complexity_analysis_values(self):
        """Complexity analysis should return correct values."""
        N = 256
        result = fft_complexity_analysis(N)
        assert result['N'] == N
        assert result['DFT_operations'] == N * N
        assert result['FFT_operations'] == N * int(np.log2(N))
        assert result['DFT_complexity'] == 'O(N^2)'
        assert result['FFT_complexity'] == 'O(N log N)'

    def test_complexity_speedup(self):
        """FFT should be faster than DFT for large N."""
        for N in [256, 1024, 4096]:
            result = fft_complexity_analysis(N)
            assert float(result['Speedup_factor'].replace('x', '')) > 1


class TestNextPowerOf2:
    """Test next power of 2 utility."""

    def test_next_power_of_2_values(self):
        """Should return correct powers of 2."""
        assert next_power_of_2(0) == 1
        assert next_power_of_2(1) == 1
        assert next_power_of_2(2) == 2
        assert next_power_of_2(3) == 4
        assert next_power_of_2(4) == 4
        assert next_power_of_2(5) == 8
        assert next_power_of_2(8) == 8
        assert next_power_of_2(9) == 16
