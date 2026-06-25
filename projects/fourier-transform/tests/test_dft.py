"""
DFT 测试

测试离散傅里叶变换的基本功能、正确性和逆变换。
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dft import dft, idft, dft_slow
from src.fft import fft


class TestDFT:
    """DFT 基本功能测试"""

    def test_empty_input(self):
        """空输入应返回空数组"""
        result = dft(np.array([]))
        assert len(result) == 0

    def test_single_element(self):
        """单元素输入"""
        result = dft(np.array([5.0]))
        assert len(result) == 1
        assert np.isclose(result[0], 5.0)

    def test_constant_signal(self):
        """常数信号的 DFT：只有 DC 分量"""
        x = np.ones(8)
        X = dft(x)
        # DC 分量应该等于 N
        assert np.isclose(X[0], 8.0)
        # 其他分量应该接近 0
        assert np.allclose(X[1:], 0.0, atol=1e-10)

    def test_pure_sine(self):
        """纯正弦波的 DFT：应该在对应频率处有峰值"""
        N = 64
        k = 5  # 频率索引
        n = np.arange(N)
        x = np.sin(2 * np.pi * k * n / N)

        X = dft(x)
        mag = np.abs(X)

        # 在 k 和 N-k 处应该有峰值
        assert mag[k] > N / 2 - 0.01
        assert mag[N - k] > N / 2 - 0.01

    def test_complex_input(self):
        """复数输入"""
        x = np.array([1 + 1j, 2 + 0j, 0 + 1j, 1 - 1j])
        X = dft(x)
        assert len(X) == 4
        assert np.iscomplexobj(X)

    def test_dft_slow_matches_dft(self):
        """dft_slow 应该与 dft 结果一致"""
        x = np.random.randn(8)
        X_matrix = dft(x)
        X_loop = dft_slow(x)
        assert np.allclose(X_matrix, X_loop, atol=1e-10)

    def test_dft_matches_numpy(self):
        """DFT 结果应该与 numpy.fft.fft 一致"""
        np.random.seed(42)
        x = np.random.randn(16)
        X_ours = dft(x)
        X_numpy = np.fft.fft(x)
        assert np.allclose(X_ours, X_numpy, atol=1e-10)

    def test_linearity(self):
        """DFT 的线性性质: DFT(a*x + b*y) = a*DFT(x) + b*DFT(y)"""
        np.random.seed(42)
        x = np.random.randn(8)
        y = np.random.randn(8)
        a, b = 2.0, 3.0

        X = dft(a * x + b * y)
        X_expected = a * dft(x) + b * dft(y)
        assert np.allclose(X, X_expected, atol=1e-10)

    def test_parseval_theorem(self):
        """Parseval 定理: Σ|x[n]|^2 = (1/N) * Σ|X[k]|^2"""
        np.random.seed(42)
        x = np.random.randn(16)
        X = dft(x)

        energy_time = np.sum(np.abs(x) ** 2)
        energy_freq = np.sum(np.abs(X) ** 2) / len(x)

        assert np.isclose(energy_time, energy_freq, atol=1e-10)

    def test_circular_shift(self):
        """时域循环移位 = 频域乘以旋转因子"""
        np.random.seed(42)
        x = np.random.randn(8)
        X = dft(x)

        # 循环移位 2
        x_shifted = np.roll(x, 2)
        X_shifted = dft(x_shifted)

        # 旋转因子
        N = len(x)
        k = np.arange(N)
        twiddle = np.exp(-2j * np.pi * k * 2 / N)

        assert np.allclose(X_shifted, X * twiddle, atol=1e-10)


class TestIDFT:
    """IDFT 测试"""

    def test_empty_input(self):
        """空输入"""
        result = idft(np.array([]))
        assert len(result) == 0

    def test_single_element(self):
        """单元素"""
        result = idft(np.array([5.0]))
        assert np.isclose(result[0], 5.0)

    def test_dft_idft_roundtrip(self):
        """DFT 后 IDFT 应该恢复原始信号"""
        np.random.seed(42)
        x = np.random.randn(16)
        X = dft(x)
        x_recovered = idft(X)
        assert np.allclose(x, x_recovered.real, atol=1e-10)

    def test_idft_matches_numpy(self):
        """IDFT 结果应该与 numpy.fft.ifft 一致"""
        np.random.seed(42)
        X = np.random.randn(16) + 1j * np.random.randn(16)
        x_ours = idft(X)
        x_numpy = np.fft.ifft(X)
        assert np.allclose(x_ours, x_numpy, atol=1e-10)

    def test_constant_spectrum(self):
        """常数频谱对应脉冲信号"""
        X = np.ones(8)
        x = idft(X)
        # 只有第一个样本非零
        assert np.isclose(x[0], 1.0)
        assert np.allclose(x[1:], 0.0, atol=1e-10)

    def test_impulse(self):
        """脉冲信号的 DFT 应该是常数"""
        x = np.zeros(8)
        x[0] = 1.0
        X = dft(x)
        assert np.allclose(np.abs(X), 1.0, atol=1e-10)

    def test_time_shift_property(self):
        """验证时移特性"""
        np.random.seed(42)
        x = np.random.randn(8)
        shift = 3

        X = dft(x)
        k = np.arange(len(x))
        X_shifted = X * np.exp(-2j * np.pi * k * shift / len(x))
        x_shifted = idft(X_shifted)

        x_expected = np.roll(x, shift)
        assert np.allclose(x_shifted.real, x_expected, atol=1e-10)


class TestDFTProperties:
    """DFT 数学性质测试"""

    def test_conjugate_symmetry(self):
        """实数信号的共轭对称性: X[k] = conj(X[N-k])"""
        np.random.seed(42)
        x = np.random.randn(16)  # 实数信号
        X = dft(x)

        for k in range(1, len(x) // 2):
            assert np.isclose(X[k], np.conj(X[len(x) - k]), atol=1e-10)

    def test_frequency_resolution(self):
        """频率分辨率 = sample_rate / N"""
        N = 100
        sample_rate = 1000.0
        freq_resolution = sample_rate / N

        # 创建一个恰好在一个频率 bin 上的信号
        k = 10
        n = np.arange(N)
        x = np.sin(2 * np.pi * k * n / N)
        X = dft(x)

        # 只在 k 和 N-k 处有能量
        mag = np.abs(X)
        assert mag[k] > 40  # N/2 - epsilon
        assert mag[N - k] > 40

    def test_dc_component(self):
        """DC 分量等于信号的均值乘以 N"""
        np.random.seed(42)
        x = np.random.randn(16)
        X = dft(x)

        assert np.isclose(X[0], np.sum(x), atol=1e-10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
