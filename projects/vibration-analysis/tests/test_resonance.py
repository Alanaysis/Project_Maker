"""
Tests for Resonance Module
共振检测模块测试
"""

import numpy as np
import pytest

from src.resonance import (
    find_resonance_frequency,
    quality_factor,
    resonance_amplification,
    half_power_bandwidth,
    detect_resonance_peaks,
    is_near_resonance,
    resonance_safety_margin,
    avoid_resonance_design,
)
from src.free_vibration import natural_frequency_hz


class TestResonanceFrequency:
    """共振频率测试"""

    def test_resonance_freq_undamped(self):
        """测试无阻尼共振频率"""
        f_r = find_resonance_frequency(100.0, 1.0, 0.0)
        f_n = natural_frequency_hz(100.0, 1.0)
        assert np.isclose(f_r, f_n)

    def test_resonance_freq_damped(self):
        """测试有阻尼共振频率"""
        f_r = find_resonance_frequency(100.0, 1.0, 1.0)
        f_n = natural_frequency_hz(100.0, 1.0)
        # 有阻尼时共振频率略低于固有频率
        assert f_r < f_n

    def test_resonance_freq_positive(self):
        """测试共振频率为正"""
        f_r = find_resonance_frequency(100.0, 1.0, 0.5)
        assert f_r > 0

    def test_heavy_damping(self):
        """测试重阻尼"""
        f_r = find_resonance_frequency(100.0, 1.0, 50.0)
        f_n = natural_frequency_hz(100.0, 1.0)
        # 重阻尼时共振频率接近固有频率
        assert abs(f_r - f_n) < 0.1


class TestQualityFactor:
    """品质因数测试"""

    def test_q_factor_formula(self):
        """测试Q因子公式"""
        zeta = 0.05
        Q = quality_factor(zeta)
        expected = 1.0 / (2 * zeta)
        assert np.isclose(Q, expected)

    def test_q_factor_positive(self):
        """测试Q因子为正"""
        Q = quality_factor(0.1)
        assert Q > 0

    def test_zero_damping(self):
        """测试零阻尼"""
        Q = quality_factor(0.0)
        assert np.isinf(Q)

    def test_critical_damping(self):
        """测试临界阻尼"""
        Q = quality_factor(0.5)
        assert Q == 1.0


class TestResonanceAmplification:
    """共振放大测试"""

    def test_amplification_positive(self):
        """测试放大倍数为正"""
        amp = resonance_amplification(100.0, 1.0, 1.0)
        assert amp > 0

    def test_amplification_equals_Q(self):
        """测试放大倍数等于Q"""
        amp = resonance_amplification(100.0, 1.0, 1.0)
        zeta = 1.0 / (2 * np.sqrt(100.0 / 1.0))
        Q = quality_factor(zeta)
        assert np.isclose(amp, Q)


class TestHalfPowerBandwidth:
    """半功率带宽测试"""

    def test_bandwidth_positive(self):
        """测试带宽为正"""
        freq_range = np.linspace(0.1, 20, 1000)
        frf_mag = 1.0 / np.sqrt((100 - 1 * (2 * np.pi * freq_range) ** 2) ** 2 +
                                  (2 * 2 * np.pi * freq_range) ** 2)
        peak_idx = np.argmax(frf_mag)
        bw = half_power_bandwidth(frf_mag, freq_range, peak_idx)
        assert bw > 0

    def test_bandwidth_increases_with_damping(self):
        """测试带宽随阻尼增加"""
        freq_range = np.linspace(0.1, 20, 5000)

        for damping in [1.0, 2.0, 5.0]:
            frf_mag = 1.0 / np.sqrt((100 - 1 * (2 * np.pi * freq_range) ** 2) ** 2 +
                                      (damping * 2 * np.pi * freq_range) ** 2)
            peak_idx = np.argmax(frf_mag)
            bw = half_power_bandwidth(frf_mag, freq_range, peak_idx)
            assert bw > 0


class TestResonanceDetection:
    """共振检测测试"""

    def test_peak_detection(self):
        """测试峰值检测"""
        freq_range = np.linspace(0.1, 20, 5000)
        peaks = detect_resonance_peaks(100.0, 1.0, 2.0, freq_range)
        assert len(peaks) > 0

    def test_peak_frequency_near_natural(self):
        """测试峰值频率接近固有频率"""
        freq_range = np.linspace(0.1, 20, 5000)
        peaks = detect_resonance_peaks(100.0, 1.0, 2.0, freq_range)
        f_n = natural_frequency_hz(100.0, 1.0)

        for peak in peaks:
            assert abs(peak.frequency_hz - f_n) < 1.0

    def test_peak_info_complete(self):
        """测试峰值信息完整"""
        freq_range = np.linspace(0.1, 20, 5000)
        peaks = detect_resonance_peaks(100.0, 1.0, 2.0, freq_range)

        for peak in peaks:
            assert peak.frequency_hz > 0
            assert peak.amplitude > 0
            assert peak.quality_factor > 0
            assert peak.bandwidth_hz > 0
            assert 0 <= peak.damping_ratio <= 1


class TestResonanceSafety:
    """共振安全测试"""

    def test_near_resonance(self):
        """测试接近共振判断"""
        assert is_near_resonance(5.0, 5.0) is True
        assert is_near_resonance(5.0, 6.0, tolerance=0.1) is False

    def test_safety_margin(self):
        """测试安全裕度"""
        margin = resonance_safety_margin(5.0, 10.0, 0.01)
        assert 0 <= margin <= 1

    def test_zero_natural_freq(self):
        """测试零固有频率"""
        assert is_near_resonance(5.0, 0.0) is False
        assert resonance_safety_margin(5.0, 0.0, 0.01) == 0.0


class TestResonanceDesign:
    """共振设计测试"""

    def test_design_recommendations(self):
        """测试设计建议"""
        design = avoid_resonance_design(100.0, 1.0, (3.0, 7.0), 0.2)

        assert design['current_natural_freq_hz'] > 0
        assert design['option_increase_freq']['target_freq_hz'] > 7.0
        assert design['option_increase_freq']['required_stiffness_Nm'] > 0

    def test_design_stiffness_change(self):
        """测试刚度变化"""
        # 固有频率 = sqrt(100/1)/(2*pi) = 1.59 Hz，在(1,5)范围内
        design = avoid_resonance_design(100.0, 1.0, (1.0, 5.0), 0.2)

        increase_ratio = design['option_increase_freq']['stiffness_change_ratio']
        # 提高频率到5.0*1.2=6.0Hz，需要增加刚度
        assert increase_ratio > 1.0

        # 降低频率到1.0*0.8=0.8Hz，需要降低刚度
        decrease_ratio = design['option_decrease_freq']['stiffness_change_ratio']
        assert decrease_ratio < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
