"""
Tests for Free Vibration Module
自由振动模块测试
"""

import numpy as np
import pytest

from src.free_vibration import (
    natural_frequency,
    natural_frequency_hz,
    damping_ratio,
    damped_natural_frequency,
    free_vibration_undamped,
    free_vibration_damped,
    logarithmic_decrement,
    estimate_damping_from_decrement,
    energy_dissipation_rate,
)


class TestNaturalFrequency:
    """固有频率测试"""

    def test_undamped_natural_freq(self):
        """测试无阻尼固有频率计算"""
        omega_n = natural_frequency(100.0, 1.0)
        expected = np.sqrt(100.0 / 1.0)
        assert np.isclose(omega_n, expected)

    def test_natural_freq_hz(self):
        """测试固有频率(Hz)计算"""
        f_n = natural_frequency_hz(100.0, 1.0)
        expected = np.sqrt(100.0 / 1.0) / (2 * np.pi)
        assert np.isclose(f_n, expected)

    def test_invalid_mass(self):
        """测试无效质量"""
        with pytest.raises(ValueError):
            natural_frequency(100.0, 0.0)
        with pytest.raises(ValueError):
            natural_frequency(100.0, -1.0)

    def test_invalid_stiffness(self):
        """测试无效刚度"""
        with pytest.raises(ValueError):
            natural_frequency(0.0, 1.0)
        with pytest.raises(ValueError):
            natural_frequency(-100.0, 1.0)

    def test_dimensional_analysis(self):
        """测试量纲分析"""
        # [k] = N/m = kg/s^2
        # [m] = kg
        # [omega_n] = sqrt(k/m) = 1/s = rad/s ✓
        omega_n = natural_frequency(1000.0, 10.0)
        assert omega_n > 0


class TestDampingRatio:
    """阻尼比测试"""

    def test_critical_damping(self):
        """测试临界阻尼"""
        mass = 1.0
        stiffness = 100.0
        omega_n = np.sqrt(stiffness / mass)
        c_critical = 2 * mass * omega_n
        zeta = damping_ratio(c_critical, stiffness, mass)
        assert np.isclose(zeta, 1.0)

    def test_underdamped(self):
        """测试欠阻尼"""
        zeta = damping_ratio(1.0, 100.0, 1.0)
        assert 0 < zeta < 1

    def test_overdamped(self):
        """测试过阻尼"""
        zeta = damping_ratio(50.0, 100.0, 1.0)
        assert zeta > 1

    def test_zero_damping(self):
        """测试零阻尼"""
        zeta = damping_ratio(0.0, 100.0, 1.0)
        assert zeta == 0.0


class TestDampedNaturalFrequency:
    """有阻尼固有频率测试"""

    def test_damped_freq_less_than_undamped(self):
        """测试有阻尼频率小于无阻尼频率"""
        omega_d = damped_natural_frequency(100.0, 1.0, 2.0)
        omega_n = natural_frequency(100.0, 1.0)
        assert omega_d < omega_n

    def test_damped_freq_formula(self):
        """测试有阻尼频率公式"""
        omega_n = np.sqrt(100.0 / 1.0)
        zeta = damping_ratio(2.0, 100.0, 1.0)
        expected = omega_n * np.sqrt(1 - zeta ** 2)
        omega_d = damped_natural_frequency(100.0, 1.0, 2.0)
        assert np.isclose(omega_d, expected)

    def test_overdamped_raises(self):
        """测试过阻尼抛出异常"""
        with pytest.raises(ValueError):
            damped_natural_frequency(100.0, 1.0, 50.0)


class TestFreeVibrationUndamped:
    """无阻尼自由振动测试"""

    def test_initial_conditions(self):
        """测试初始条件"""
        x0, v0 = 1.0, 0.0
        result = free_vibration_undamped(100.0, 1.0, x0, v0, duration=0.01)
        assert np.isclose(result.displacement[0], x0)
        assert np.isclose(result.velocity[0], v0)

    def test_energy_conservation(self):
        """测试能量守恒"""
        result = free_vibration_undamped(100.0, 1.0, 1.0, 0.0, duration=1.0)
        # 总能量: E = 0.5*m*v^2 + 0.5*k*x^2
        energy = 0.5 * 1.0 * result.velocity ** 2 + 0.5 * 100.0 * result.displacement ** 2
        assert np.allclose(energy, energy[0], rtol=1e-5)

    def test_period(self):
        """测试振动周期"""
        f_n = natural_frequency_hz(100.0, 1.0)
        period = 1.0 / f_n
        result = free_vibration_undamped(100.0, 1.0, 1.0, 0.0, duration=2 * period)
        # 一个周期后回到初始状态
        assert np.isclose(result.displacement[-1], 1.0, rtol=0.01)

    def test_amplitude_preserved(self):
        """测试振幅保持不变"""
        result = free_vibration_undamped(100.0, 1.0, 1.0, 0.0, duration=10.0)
        max_disp = np.max(np.abs(result.displacement))
        assert np.isclose(max_disp, 1.0, rtol=0.01)


class TestFreeVibrationDamped:
    """有阻尼自由振动测试"""

    def test_amplitude_decay(self):
        """测试振幅衰减"""
        result = free_vibration_damped(100.0, 1.0, 2.0, 1.0, 0.0, duration=5.0)
        # 振幅应逐渐减小
        assert result.displacement[-1] < result.displacement[0]

    def test_initial_conditions(self):
        """测试初始条件"""
        result = free_vibration_damped(100.0, 1.0, 2.0, 1.0, 0.0, duration=0.01)
        assert np.isclose(result.displacement[0], 1.0)
        assert np.isclose(result.velocity[0], 0.0)

    def test_damping_ratio_correct(self):
        """测试阻尼比正确"""
        result = free_vibration_damped(100.0, 1.0, 2.0, 1.0, 0.0)
        expected_zeta = damping_ratio(2.0, 100.0, 1.0)
        assert np.isclose(result.damping_ratio, expected_zeta)

    def test_energy_decrease(self):
        """测试能量减少"""
        result = free_vibration_damped(100.0, 1.0, 2.0, 1.0, 0.0, duration=5.0)
        energy = 0.5 * 1.0 * result.velocity ** 2 + 0.5 * 100.0 * result.displacement ** 2
        assert energy[-1] < energy[0]


class TestLogarithmicDecrement:
    """对数衰减率测试"""

    def test_log_decrement_calculation(self):
        """测试对数衰减率计算"""
        result = free_vibration_damped(100.0, 1.0, 2.0, 1.0, 0.0, duration=5.0)
        delta = logarithmic_decrement(result)
        assert delta > 0

    def test_damping_estimation(self):
        """测试阻尼估计"""
        zeta_true = 0.1
        delta = zeta_true * np.sqrt(4 * np.pi ** 2 + zeta_true ** 2)
        zeta_est = estimate_damping_from_decrement(delta)
        assert np.isclose(zeta_est, zeta_true, rtol=0.01)


class TestEnergyDissipation:
    """能量耗散测试"""

    def test_energy_dissipation_positive(self):
        """测试能量耗散率为正"""
        rate = energy_dissipation_rate(2.0, 100.0, 1.0)
        assert rate > 0

    def test_zero_damping_no_dissipation(self):
        """测试零阻尼无耗散"""
        rate = energy_dissipation_rate(0.0, 100.0, 1.0)
        assert rate == 0.0

    def test_formula(self):
        """测试公式: Delta_E/E = 2*pi*zeta"""
        zeta = damping_ratio(2.0, 100.0, 1.0)
        expected = 2 * np.pi * zeta
        rate = energy_dissipation_rate(2.0, 100.0, 1.0)
        assert np.isclose(rate, expected)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
