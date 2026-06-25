"""
RLC 带通滤波器单元测试
======================

测试 RLC 带通滤波器的各项功能。
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.bandpass import RLCBandPass


class TestRLCBandPass:
    """RLC 带通滤波器测试"""

    def test_init(self):
        """测试初始化"""
        filt = RLCBandPass(R=100, L=0.01, C=1e-6)
        assert filt.R == 100
        assert filt.L == 0.01
        assert filt.C == 1e-6

    def test_init_invalid(self):
        """测试无效参数"""
        with pytest.raises(ValueError):
            RLCBandPass(R=-1, L=0.01, C=1e-6)
        with pytest.raises(ValueError):
            RLCBandPass(R=100, L=0, C=1e-6)
        with pytest.raises(ValueError):
            RLCBandPass(R=100, L=0.01, C=-1)

    def test_center_frequency(self):
        """测试中心频率计算"""
        filt = RLCBandPass(R=100, L=0.01, C=1e-6)
        expected_f0 = 1.0 / (2 * np.pi * np.sqrt(0.01 * 1e-6))
        assert filt.f0 == pytest.approx(expected_f0, rel=1e-6)

    def test_bandwidth(self):
        """测试带宽计算"""
        filt = RLCBandPass(R=100, L=0.01, C=1e-6)
        expected_bw = 1.0 / (2 * np.pi * 100 * 1e-6)
        assert filt.bw == pytest.approx(expected_bw, rel=1e-6)

    def test_quality_factor(self):
        """测试品质因数"""
        filt = RLCBandPass(R=100, L=0.01, C=1e-6)
        expected_Q = filt.omega0 * filt.R * filt.C
        assert filt.Q == pytest.approx(expected_Q, rel=1e-6)

    def test_gain_at_center(self):
        """测试中心频率处增益应为 1 (0dB)"""
        filt = RLCBandPass(R=100, L=0.01, C=1e-6)
        f = np.array([filt.f0])
        mag = filt.magnitude(f)
        assert mag[0] == pytest.approx(1.0, abs=1e-3)

    def test_gain_at_dc(self):
        """测试直流增益应为 0"""
        filt = RLCBandPass(R=100, L=0.01, C=1e-6)
        f = np.array([0.001])
        mag = filt.magnitude(f)
        assert mag[0] == pytest.approx(0.0, abs=1e-3)

    def test_gain_at_high_freq(self):
        """测试极高频增益应趋近于 0"""
        filt = RLCBandPass(R=100, L=0.01, C=1e-6)
        f = np.array([filt.f0 * 1000])
        mag = filt.magnitude(f)
        assert mag[0] < 0.01

    def test_phase_at_center(self):
        """测试中心频率处相位应为 0 度"""
        filt = RLCBandPass(R=100, L=0.01, C=1e-6)
        f = np.array([filt.f0])
        phase = filt.phase(f)
        assert phase[0] == pytest.approx(0.0, abs=1.0)

    def test_phase_range(self):
        """测试相位范围 +90 到 -90 度"""
        filt = RLCBandPass(R=100, L=0.01, C=1e-6)
        f = np.array([filt.f0 / 100, filt.f0, filt.f0 * 100])
        phase = filt.phase(f)
        assert phase[0] == pytest.approx(90.0, abs=5.0)   # 低频接近+90
        assert phase[2] == pytest.approx(-90.0, abs=5.0)   # 高频接近-90

    def test_bandwidth_definition(self):
        """测试带宽定义 (-3dB 点)"""
        filt = RLCBandPass(R=100, L=0.01, C=1e-6)

        # 计算上截止频率和下截止频率处的增益
        f_low = filt.lower_cutoff()
        f_high = filt.upper_cutoff()

        mag_low = filt.magnitude_db(np.array([f_low]))[0]
        mag_high = filt.magnitude_db(np.array([f_high]))[0]
        mag_center = filt.magnitude_db(np.array([filt.f0]))[0]

        # 截止频率处应比中心频率低约 3dB
        assert (mag_center - mag_low) == pytest.approx(3.0, abs=0.5)
        assert (mag_center - mag_high) == pytest.approx(3.0, abs=0.5)

    def test_bandwidth_consistency(self):
        """测试带宽一致性"""
        filt = RLCBandPass(R=100, L=0.01, C=1e-6)
        bw_calc = filt.upper_cutoff() - filt.lower_cutoff()
        assert bw_calc == pytest.approx(filt.bw, rel=0.01)

    def test_magnitude_array(self):
        """测试数组输入"""
        filt = RLCBandPass(R=100, L=0.01, C=1e-6)
        f = np.logspace(1, 6, 100)
        mag = filt.magnitude(f)
        assert len(mag) == 100
        assert np.all(mag >= 0)

    def test_repr(self):
        """测试字符串表示"""
        filt = RLCBandPass(R=100, L=0.01, C=1e-6)
        s = repr(filt)
        assert "RLCBandPass" in s
        assert "100" in s
