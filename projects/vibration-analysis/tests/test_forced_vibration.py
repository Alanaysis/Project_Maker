"""
Tests for Forced Vibration Module
强迫振动模块测试
"""

import numpy as np
import pytest

from src.forced_vibration import (
    harmonic_force_response,
    step_force_response,
    impulse_response,
    frequency_response_function,
    steady_state_amplitude,
)


class TestHarmonicForceResponse:
    """简谐激励响应测试"""

    def test_initial_conditions(self):
        """测试初始条件"""
        result = harmonic_force_response(100.0, 1.0, 2.0, 10.0, 1.0,
                                         initial_displacement=0.5, initial_velocity=0.0)
        assert np.isclose(result.displacement[0], 0.5)
        assert np.isclose(result.velocity[0], 0.0)

    def test_force_shape(self):
        """测试力波形为正弦"""
        result = harmonic_force_response(100.0, 1.0, 2.0, 10.0, 1.0, duration=1.0)
        # 力应该是正弦波
        assert np.max(result.force) > 0
        assert np.min(result.force) < 0
        assert np.isclose(np.max(result.force) - np.min(result.force), 20.0, rtol=0.01)

    def test_response_shape(self):
        """测试响应形状"""
        result = harmonic_force_response(100.0, 1.0, 2.0, 10.0, 1.0, duration=5.0)
        assert len(result.time) == len(result.displacement)
        assert len(result.time) == len(result.velocity)
        assert len(result.time) == len(result.acceleration)


class TestStepForceResponse:
    """阶跃激励响应测试"""

    def test_initial_conditions(self):
        """测试初始条件"""
        result = step_force_response(100.0, 1.0, 2.0, 10.0,
                                     initial_displacement=0.0, initial_velocity=0.0)
        assert np.isclose(result.displacement[0], 0.0)

    def test_steady_state(self):
        """测试稳态"""
        result = step_force_response(100.0, 1.0, 2.0, 10.0, duration=10.0)
        static_disp = 10.0 / 100.0
        # 稳态时应接近静态位移
        assert np.isclose(result.displacement[-1], static_disp, rtol=0.1)

    def test_force_is_step(self):
        """测试力为阶跃"""
        result = step_force_response(100.0, 1.0, 2.0, 10.0, duration=1.0)
        assert np.all(result.force >= 0)
        assert np.all(result.force <= 10.0)


class TestImpulseResponse:
    """脉冲响应测试"""

    def test_initial_velocity(self):
        """测试初始速度"""
        impulse = 5.0
        mass = 1.0
        result = impulse_response(100.0, mass, 2.0, impulse)
        # 脉冲产生初始速度 v0 = I/m
        assert np.isclose(result.velocity[0], impulse / mass)

    def test_response_shape(self):
        """测试响应形状"""
        result = impulse_response(100.0, 1.0, 2.0, 5.0, duration=5.0)
        assert len(result.time) == len(result.displacement)


class TestFrequencyResponseFunction:
    """频响函数测试"""

    def test_frf_shape(self):
        """测试FRF形状"""
        freq_range = np.linspace(0.1, 20, 100)
        frf = frequency_response_function(100.0, 1.0, 2.0, freq_range)
        assert len(frf['freq']) == 100
        assert len(frf['magnitude']) == 100
        assert len(frf['phase']) == 100

    def test_frf_magnitude_positive(self):
        """测试FRF幅值为正"""
        freq_range = np.linspace(0.1, 20, 100)
        frf = frequency_response_function(100.0, 1.0, 2.0, freq_range)
        assert np.all(frf['magnitude'] > 0)

    def test_frf_at_resonance(self):
        """测试共振时FRF"""
        freq_range = np.linspace(0.1, 20, 1000)
        frf = frequency_response_function(100.0, 1.0, 2.0, freq_range)
        # 共振时幅值最大
        peak_idx = np.argmax(frf['magnitude'])
        # 共振频率约1.57 Hz
        assert 1.0 < freq_range[peak_idx] < 3.0


class TestSteadyStateAmplitude:
    """稳态幅值测试"""

    def test_amplification_factor(self):
        """测试放大因子"""
        amp = steady_state_amplitude(100.0, 1.0, 2.0, 1.0 / (2 * np.pi))
        # 在共振频率附近，放大因子应该较大
        assert amp > 0

    def test_off_resonance(self):
        """测试远离共振"""
        amp_low = steady_state_amplitude(100.0, 1.0, 2.0, 0.01)
        amp_high = steady_state_amplitude(100.0, 1.0, 2.0, 10.0)
        # 低频和高频时放大因子都较小
        assert amp_low < 2.0
        assert amp_high < 1.0

    def test_dimensional_consistency(self):
        """测试量纲一致性"""
        # 放大因子应该是无量纲的
        amp = steady_state_amplitude(100.0, 1.0, 2.0, 1.0)
        assert amp > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
