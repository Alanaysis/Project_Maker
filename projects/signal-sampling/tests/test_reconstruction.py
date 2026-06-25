"""
重建模块测试
=============

测试零阶保持、一阶保持、sinc 插值重建等功能。
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.reconstruction import (
    zero_order_hold,
    first_order_hold,
    sinc_interpolation,
    reconstruct_signal,
    compare_reconstruction,
    sinc_pulse,
    ideal_lowpass_reconstruction,
)


class TestZeroOrderHold:
    """零阶保持测试"""

    def test_basic(self):
        """测试基本零阶保持"""
        t_sampled = np.array([0, 0.1, 0.2, 0.3, 0.4])
        samples = np.array([0, 1, 0, -1, 0])
        t_continuous = np.linspace(0, 0.4, 100)

        result = zero_order_hold(t_sampled, samples, t_continuous)

        assert len(result) == len(t_continuous)

        # 验证阶梯特性
        # 在 [0, 0.1) 区间应为 0
        mask = (t_continuous >= 0) & (t_continuous < 0.1)
        assert np.allclose(result[mask], 0)

        # 在 [0.1, 0.2) 区间应为 1
        mask = (t_continuous >= 0.1) & (t_continuous < 0.2)
        assert np.allclose(result[mask], 1)

    def test_constant_signal(self):
        """测试常数信号"""
        t_sampled = np.array([0, 0.1, 0.2])
        samples = np.array([0.5, 0.5, 0.5])
        t_continuous = np.linspace(0, 0.2, 50)

        result = zero_order_hold(t_sampled, samples, t_continuous)

        assert np.allclose(result, 0.5)

    def test_length_mismatch_raises(self):
        """测试长度不匹配"""
        t_sampled = np.array([0, 0.1, 0.2])
        samples = np.array([0, 1])  # 长度不匹配
        t_continuous = np.linspace(0, 0.2, 50)

        with pytest.raises(ValueError):
            zero_order_hold(t_sampled, samples, t_continuous)


class TestFirstOrderHold:
    """一阶保持测试"""

    def test_basic(self):
        """测试基本一阶保持"""
        t_sampled = np.array([0, 0.1, 0.2, 0.3, 0.4])
        samples = np.array([0, 1, 0, -1, 0])
        t_continuous = np.linspace(0, 0.4, 100)

        result = first_order_hold(t_sampled, samples, t_continuous)

        assert len(result) == len(t_continuous)

        # 验证线性插值 - 在 t=0.05 时，应为 0.5 (0 和 1 的中间)
        # 使用更宽的容差，因为 linspace 可能不在精确的 0.05 处
        idx = np.argmin(np.abs(t_continuous - 0.05))
        assert np.isclose(result[idx], 0.5, atol=0.02)

    def test_constant_signal(self):
        """测试常数信号"""
        t_sampled = np.array([0, 0.1, 0.2])
        samples = np.array([0.5, 0.5, 0.5])
        t_continuous = np.linspace(0, 0.2, 50)

        result = first_order_hold(t_sampled, samples, t_continuous)

        assert np.allclose(result, 0.5)

    def test_linear_signal(self):
        """测试线性信号"""
        t_sampled = np.array([0, 0.1, 0.2, 0.3, 0.4])
        samples = np.array([0, 0.1, 0.2, 0.3, 0.4])
        t_continuous = np.linspace(0, 0.4, 100)

        result = first_order_hold(t_sampled, samples, t_continuous)

        # 线性信号应完美重建
        assert np.allclose(result, t_continuous, atol=0.01)

    def test_length_mismatch_raises(self):
        """测试长度不匹配"""
        t_sampled = np.array([0, 0.1, 0.2])
        samples = np.array([0, 1])  # 长度不匹配
        t_continuous = np.linspace(0, 0.2, 50)

        with pytest.raises(ValueError):
            first_order_hold(t_sampled, samples, t_continuous)


class TestSincInterpolation:
    """sinc 插值测试"""

    def test_basic(self):
        """测试基本 sinc 插值"""
        fs = 100
        f_signal = 10
        duration = 0.5

        t_sampled = np.arange(int(fs * duration)) / fs
        samples = np.sin(2 * np.pi * f_signal * t_sampled)
        t_continuous = np.linspace(0, duration, 500)

        result = sinc_interpolation(t_sampled, samples, t_continuous, fs)

        assert len(result) == len(t_continuous)

    def test_perfect_reconstruction(self):
        """测试完美重建 (奈奎斯特条件下)"""
        fs = 100
        f_signal = 10  # 远低于奈奎斯特频率
        duration = 0.5

        # 采样
        t_sampled = np.arange(int(fs * duration)) / fs
        samples = np.sin(2 * np.pi * f_signal * t_sampled)

        # 重建
        t_continuous = np.linspace(0.1, duration - 0.1, 300)  # 避免边界
        reconstructed = sinc_interpolation(t_sampled, samples, t_continuous, fs)
        original = np.sin(2 * np.pi * f_signal * t_continuous)

        # 在信号内部应完美重建
        assert np.allclose(reconstructed, original, atol=0.05)

    def test_length_mismatch_raises(self):
        """测试长度不匹配"""
        t_sampled = np.array([0, 0.1, 0.2])
        samples = np.array([0, 1])  # 长度不匹配
        t_continuous = np.linspace(0, 0.2, 50)

        with pytest.raises(ValueError):
            sinc_interpolation(t_sampled, samples, t_continuous)


class TestReconstructSignal:
    """统一重建接口测试"""

    def test_zoh(self):
        """测试 ZOH 重建"""
        t_sampled = np.array([0, 0.1, 0.2])
        samples = np.array([0, 1, 0])
        t_continuous = np.linspace(0, 0.2, 50)

        result = reconstruct_signal(t_sampled, samples, t_continuous, method='zoh')
        assert len(result) == len(t_continuous)

    def test_foh(self):
        """测试 FOH 重建"""
        t_sampled = np.array([0, 0.1, 0.2])
        samples = np.array([0, 1, 0])
        t_continuous = np.linspace(0, 0.2, 50)

        result = reconstruct_signal(t_sampled, samples, t_continuous, method='foh')
        assert len(result) == len(t_continuous)

    def test_sinc(self):
        """测试 sinc 重建"""
        t_sampled = np.array([0, 0.1, 0.2])
        samples = np.array([0, 1, 0])
        t_continuous = np.linspace(0, 0.2, 50)

        result = reconstruct_signal(t_sampled, samples, t_continuous, method='sinc')
        assert len(result) == len(t_continuous)

    def test_invalid_method(self):
        """测试无效方法"""
        t_sampled = np.array([0, 0.1, 0.2])
        samples = np.array([0, 1, 0])
        t_continuous = np.linspace(0, 0.2, 50)

        with pytest.raises(ValueError):
            reconstruct_signal(t_sampled, samples, t_continuous, method='invalid')


class TestCompareReconstruction:
    """重建方法比较测试"""

    def test_basic_comparison(self):
        """测试基本比较"""
        fs = 100
        f_signal = 10
        duration = 0.2

        t_sampled = np.arange(int(fs * duration)) / fs
        samples = np.sin(2 * np.pi * f_signal * t_sampled)
        t_continuous = np.linspace(0, duration, 200)
        original = np.sin(2 * np.pi * f_signal * t_continuous)

        results = compare_reconstruction(t_sampled, samples, t_continuous, original, fs)

        assert 'zoh' in results
        assert 'foh' in results
        assert 'sinc' in results

        for method, data in results.items():
            assert 'signal' in data
            assert 'mse' in data
            assert 'max_error' in data
            assert 'snr_db' in data
            assert data['mse'] >= 0

    def test_sinc_best_for_bandlimited(self):
        """测试 sinc 重建对带限信号最优"""
        fs = 100
        f_signal = 10
        duration = 0.2

        t_sampled = np.arange(int(fs * duration)) / fs
        samples = np.sin(2 * np.pi * f_signal * t_sampled)
        t_continuous = np.linspace(0.05, duration - 0.05, 100)  # 避免边界
        original = np.sin(2 * np.pi * f_signal * t_continuous)

        results = compare_reconstruction(t_sampled, samples, t_continuous, original, fs)

        # sinc 重建应有最小的 MSE (在信号内部)
        assert results['sinc']['mse'] <= results['zoh']['mse'] + 1e-10


class TestSincPulse:
    """sinc 脉冲测试"""

    def test_peak_at_origin(self):
        """测试原点峰值"""
        Ts = 1.0
        t = np.array([0])
        result = sinc_pulse(Ts, t)
        assert np.isclose(result[0], 1.0)

    def test_zeros_at_multiples(self):
        """测试整数倍为零"""
        Ts = 1.0
        t = np.array([1, 2, 3, -1, -2, -3])
        result = sinc_pulse(Ts, t)
        assert np.allclose(result, 0, atol=1e-10)

    def test_symmetry(self):
        """测试对称性"""
        Ts = 1.0
        t = np.linspace(-5, 5, 101)
        result = sinc_pulse(Ts, t)

        # sinc 函数应关于原点对称
        assert np.allclose(result[:50], result[-1:50:-1], atol=1e-10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
