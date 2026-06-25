"""
FFT 测试

测试快速傅里叶变换的正确性、性能和边界情况。
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.fft import fft, ifft, fft_radix2, fft2d
from src.dft import dft


class TestFFT:
    """FFT 基本功能测试"""

    def test_empty_input(self):
        """空输入"""
        result = fft(np.array([]))
        assert len(result) == 0

    def test_single_element(self):
        """单元素"""
        result = fft(np.array([5.0]))
        assert np.isclose(result[0], 5.0)

    def test_two_elements(self):
        """两元素"""
        x = np.array([1.0, 2.0])
        X = fft(x)
        assert np.isclose(X[0], 3.0)  # 1 + 2
        assert np.isclose(X[1], -1.0)  # 1 - 2

    def test_power_of_two(self):
        """2 的幂长度"""
        for power in range(1, 11):
            N = 2 ** power
            x = np.random.randn(N)
            X_fft = fft(x)
            X_numpy = np.fft.fft(x)
            assert np.allclose(X_fft, X_numpy, atol=1e-10), f"Failed for N={N}"

    def test_non_power_of_two(self):
        """非 2 的幂长度（自动补零）"""
        x = np.random.randn(10)
        X_fft = fft(x)
        # 补零后的长度应该是 16
        assert len(X_fft) == 16
        # 与 numpy 的 rfft 对比前 10 个频率分量
        X_numpy = np.fft.fft(x, n=16)
        assert np.allclose(X_fft, X_numpy, atol=1e-10)

    def test_fft_matches_dft(self):
        """FFT 结果应该与 DFT 一致（补零到相同长度）"""
        np.random.seed(42)
        x = np.random.randn(8)
        X_fft = fft(x)
        X_dft = dft(x)
        assert np.allclose(X_fft, X_dft, atol=1e-10)

    def test_fft_matches_numpy(self):
        """FFT 结果应该与 numpy.fft.fft 一致"""
        np.random.seed(42)
        for N in [4, 8, 16, 32, 64, 128]:
            x = np.random.randn(N)
            X_ours = fft(x)
            X_numpy = np.fft.fft(x)
            assert np.allclose(X_ours, X_numpy, atol=1e-10), f"Failed for N={N}"

    def test_linearity(self):
        """FFT 线性性质"""
        np.random.seed(42)
        x = np.random.randn(16)
        y = np.random.randn(16)
        a, b = 2.5, 3.7

        X = fft(a * x + b * y)
        X_expected = a * fft(x) + b * fft(y)
        assert np.allclose(X, X_expected, atol=1e-10)

    def test_pure_frequency(self):
        """纯频率信号"""
        N = 64
        k = 8
        n = np.arange(N)
        x = np.cos(2 * np.pi * k * n / N)

        X = fft(x)
        mag = np.abs(X)

        # 应该在 k 和 N-k 处有峰值
        assert mag[k] > N / 2 - 0.01
        assert mag[N - k] > N / 2 - 0.01

    def test_complex_input(self):
        """复数输入"""
        np.random.seed(42)
        x = np.random.randn(16) + 1j * np.random.randn(16)
        X = fft(x)
        X_numpy = np.fft.fft(x)
        assert np.allclose(X, X_numpy, atol=1e-10)


class TestFFTIterative:
    """FFT 迭代实现测试"""

    def test_radix2_basic(self):
        """Radix-2 FFT 基本测试"""
        x = np.array([1.0, 2.0, 3.0, 4.0])
        X = fft_radix2(x)
        X_numpy = np.fft.fft(x)
        assert np.allclose(X, X_numpy, atol=1e-10)

    def test_radix2_power_of_two(self):
        """多种 2 的幂长度"""
        np.random.seed(42)
        for power in range(2, 10):
            N = 2 ** power
            x = np.random.randn(N)
            X_ours = fft_radix2(x)
            X_numpy = np.fft.fft(x)
            assert np.allclose(X_ours, X_numpy, atol=1e-10), f"Failed for N={N}"

    def test_radix2_non_power_raises(self):
        """非 2 的幂长度应该抛出异常"""
        x = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="2 的幂"):
            fft_radix2(x)

    def test_radix2_matches_recursive(self):
        """迭代和递归实现应该一致"""
        np.random.seed(42)
        x = np.random.randn(32)
        X_recursive = fft(x)
        X_iterative = fft_radix2(x)
        assert np.allclose(X_recursive, X_iterative, atol=1e-10)

    def test_radix2_empty(self):
        """空输入"""
        result = fft_radix2(np.array([]))
        assert len(result) == 0


class TestIFFT:
    """IFFT 测试"""

    def test_empty_input(self):
        """空输入"""
        result = ifft(np.array([]))
        assert len(result) == 0

    def test_single_element(self):
        """单元素"""
        result = ifft(np.array([5.0]))
        assert np.isclose(result[0], 5.0)

    def test_fft_ifft_roundtrip(self):
        """FFT 后 IFFT 应该恢复原始信号"""
        np.random.seed(42)
        x = np.random.randn(16)
        X = fft(x)
        x_recovered = ifft(X)
        assert np.allclose(x, x_recovered, atol=1e-10)

    def test_fft_ifft_roundtrip_complex(self):
        """复数信号的 FFT/IFFT 往返"""
        np.random.seed(42)
        x = np.random.randn(16) + 1j * np.random.randn(16)
        X = fft(x)
        x_recovered = ifft(X)
        assert np.allclose(x, x_recovered, atol=1e-10)

    def test_ifft_matches_numpy(self):
        """IFFT 结果应该与 numpy.fft.ifft 一致"""
        np.random.seed(42)
        X = np.random.randn(16) + 1j * np.random.randn(16)
        x_ours = ifft(X)
        x_numpy = np.fft.ifft(X)
        assert np.allclose(x_ours, x_numpy, atol=1e-10)

    def test_non_power_of_two_ifft(self):
        """非 2 的幂长度的 IFFT"""
        np.random.seed(42)
        x = np.random.randn(10)
        X = fft(x)  # 补零到 16
        x_recovered = ifft(X)
        # 恢复的是补零后的信号
        x_padded = np.pad(x, (0, 6))
        assert np.allclose(x_padded, x_recovered, atol=1e-10)

    def test_constant_spectrum(self):
        """常数频谱"""
        X = np.ones(8)
        x = ifft(X)
        assert np.isclose(x[0], 1.0)
        assert np.allclose(x[1:], 0.0, atol=1e-10)


class TestFFT2D:
    """二维 FFT 测试"""

    def test_constant_2d(self):
        """常数矩阵"""
        x = np.ones((4, 4))
        X = fft2d(x)
        assert np.isclose(X[0, 0], 16.0)
        assert np.allclose(X[1:, :], 0.0, atol=1e-10)

    def test_matches_numpy(self):
        """与 numpy.fft.fft2 一致"""
        np.random.seed(42)
        x = np.random.randn(8, 8)
        X_ours = fft2d(x)
        X_numpy = np.fft.fft2(x)
        assert np.allclose(X_ours, X_numpy, atol=1e-10)

    def test_non_2d_raises(self):
        """非 2D 输入应该抛出异常"""
        x = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="2D"):
            fft2d(x)

    def test_separability(self):
        """2D FFT = 先对行做 FFT，再对列做 FFT"""
        np.random.seed(42)
        x = np.random.randn(4, 8)

        # 一次性 2D FFT
        X_2d = fft2d(x)

        # 分步：先行后列
        X_rows = np.array([fft(row) for row in x])
        X_step = np.array([fft(col) for col in X_rows.T]).T

        assert np.allclose(X_2d, X_step, atol=1e-10)


class TestFFTEdgeCases:
    """边界情况测试"""

    def test_all_zeros(self):
        """全零信号"""
        x = np.zeros(16)
        X = fft(x)
        assert np.allclose(X, 0.0)

    def test_very_small_values(self):
        """非常小的值"""
        x = np.ones(16) * 1e-15
        X = fft(x)
        assert np.isclose(X[0], 16e-15, atol=1e-20)

    def test_very_large_values(self):
        """非常大的值"""
        x = np.ones(16) * 1e15
        X = fft(x)
        assert np.isclose(X[0], 16e15, atol=1e5)

    def test_alternating_signal(self):
        """交替信号 (+1, -1, +1, -1, ...)"""
        N = 8
        x = np.array([1.0, -1.0] * (N // 2))
        X = fft(x)
        # 应该只在 N/2 频率处有能量
        assert np.isclose(X[0], 0.0, atol=1e-10)
        assert np.isclose(np.abs(X[N // 2]), N, atol=1e-10)

    def test_unit_impulse(self):
        """单位脉冲的 FFT 应该是全频段"""
        N = 16
        x = np.zeros(N)
        x[0] = 1.0
        X = fft(x)
        assert np.allclose(np.abs(X), 1.0, atol=1e-10)

    def test_dc_signal(self):
        """直流信号"""
        N = 16
        x = np.ones(N) * 3.0
        X = fft(x)
        assert np.isclose(X[0], 3.0 * N)
        assert np.allclose(np.abs(X[1:]), 0.0, atol=1e-10)


class TestFFTBenchmark:
    """FFT 性能基准测试（标记为慢测试）"""

    @pytest.mark.slow
    def test_fft_faster_than_dft(self):
        """FFT 应该比 DFT 快"""
        import time

        N = 1024
        x = np.random.randn(N)

        # DFT
        start = time.perf_counter()
        for _ in range(3):
            dft(x)
        dft_time = (time.perf_counter() - start) / 3

        # FFT
        start = time.perf_counter()
        for _ in range(100):
            fft(x)
        fft_time = (time.perf_counter() - start) / 100

        # FFT 应该至少快 5 倍
        assert fft_time < dft_time / 5, (
            f"FFT ({fft_time*1000:.2f}ms) should be much faster than "
            f"DFT ({dft_time*1000:.2f}ms)"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
