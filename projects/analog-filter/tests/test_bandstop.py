"""
RLC 带阻滤波器单元测试
======================

测试 RLC 带阻滤波器的各项功能。
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.bandstop import RLCBandStop


class TestRLCBandStop:
    """RLC 带阻滤波器测试"""

    def test_init(self):
        """测试初始化"""
        filt = RLCBandStop(R=100, L=0.01, C=1e-6)
        assert filt.R == 100
        assert filt.L == 0.01
        assert filt.C == 1e-6

    def test_init_invalid(self):
        """测试无效参数"""
        with pytest.raises(ValueError):
            RLCBandStop(R=-1, L=0.01, C=1e-6)
        with pytest.raises(ValueError):
            RLCBandStop(R=100, L=0, C=1e-6)
        with pytest.raises(ValueError):
            RLCBandStop(R=100, L=0.01, C=0)

    def test_center_frequency(self):
        """测试中心频率计算"""
        filt = RLCBandStop(R=100, L=0.01, C=1e-6)
        expected_f0 = 1.0 / (2 * np.pi * np.sqrt(0.01 * 1e-6))
        assert filt.f0 == pytest.approx(expected_f0, rel=1e-6)

    def test_gain_at_center(self):
        """测试中心频率处增益应为 0 (陷波)"""
        filt = RLCBandStop(R=100, L=0.01, C=1e-6)
        f = np.array([filt.f0])
        mag = filt.magnitude(f)
        assert mag[0] < 1e-6

    def test_gain_at_dc(self):
        """测试直流增益应为 1"""
        filt = RLCBandStop(R=100, L=0.01, C=1e-6)
        f = np.array([0.001])
        mag = filt.magnitude(f)
        assert mag[0] == pytest.approx(1.0, abs=1e-3)

    def test_gain_at_high_freq(self):
        """测试极高频增益应趋近于 1"""
        filt = RLCBandStop(R=100, L=0.01, C=1e-6)
        f = np.array([filt.f0 * 1000])
        mag = filt.magnitude(f)
        assert mag[0] == pytest.approx(1.0, abs=0.01)

    def test_phase_at_dc(self):
        """测试直流相位应为 0 度"""
        filt = RLCBandStop(R=100, L=0.01, C=1e-6)
        f = np.array([0.001])
        phase = filt.phase(f)
        assert phase[0] == pytest.approx(0.0, abs=1.0)

    def test_bandwidth_definition(self):
        """测试带宽定义"""
        filt = RLCBandStop(R=100, L=0.01, C=1e-6)

        f_low = filt.lower_cutoff()
        f_high = filt.upper_cutoff()

        # 截止频率处应比 1 (0dB) 低约 3dB
        mag_low = filt.magnitude_db(np.array([f_low]))[0]
        mag_high = filt.magnitude_db(np.array([f_high]))[0]

        assert mag_low == pytest.approx(-3.0, abs=0.5)
        assert mag_high == pytest.approx(-3.0, abs=0.5)

    def test_bandwidth_consistency(self):
        """测试带宽一致性"""
        filt = RLCBandStop(R=100, L=0.01, C=1e-6)
        bw_calc = filt.upper_cutoff() - filt.lower_cutoff()
        assert bw_calc == pytest.approx(filt.bw, rel=0.01)

    def test_quality_factor(self):
        """测试品质因数"""
        filt = RLCBandStop(R=100, L=0.01, C=1e-6)
        expected_Q = filt.omega0 * filt.R * filt.C
        assert filt.Q == pytest.approx(expected_Q, rel=1e-6)

    def test_magnitude_array(self):
        """测试数组输入"""
        filt = RLCBandStop(R=100, L=0.01, C=1e-6)
        f = np.logspace(1, 6, 100)
        mag = filt.magnitude(f)
        assert len(mag) == 100
        assert np.all(mag >= 0)
        assert np.all(mag <= 1.0 + 1e-10)

    def test_repr(self):
        """测试字符串表示"""
        filt = RLCBandStop(R=100, L=0.01, C=1e-6)
        s = repr(filt)
        assert "RLCBandStop" in s

    def test_bandpass_bandstop_complementarity(self):
        """测试带通和带阻的互补性

        对于相同的 RLC 参数:
        |H_bp(f)|² + |H_bs(f)|² ≈ 1  (在理想情况下)
        这是一个近似关系，用于验证两者的设计一致性。
        """
        R, L, C = 100, 0.01, 1e-6

        from src.bandpass import RLCBandPass
        bp = RLCBandPass(R, L, C)
        bs = RLCBandStop(R, L, C)

        # 测试远离中心频率的点 (近似成立)
        f = np.array([bp.f0 / 10, bp.f0 * 10])
        mag_bp = bp.magnitude(f)
        mag_bs = bs.magnitude(f)

        # 在远离中心频率处，一个趋近1另一个趋近0
        # 所以它们的平方和应该接近 1
        sum_sq = mag_bp ** 2 + mag_bs ** 2
        np.testing.assert_allclose(sum_sq, 1.0, atol=0.01)
