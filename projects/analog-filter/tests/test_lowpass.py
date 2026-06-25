"""
低通滤波器单元测试
==================

测试 RC 低通和 RL 低通滤波器的各项功能。
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.lowpass import RCLowPass, RLLowPass


class TestRCLowPass:
    """RC 低通滤波器测试"""

    def test_init(self):
        """测试初始化"""
        filt = RCLowPass(R=1000, C=1e-6)
        assert filt.R == 1000
        assert filt.C == 1e-6
        assert filt.tau == pytest.approx(1e-3, rel=1e-6)
        assert filt.fc == pytest.approx(1.0 / (2 * np.pi * 1e-3), rel=1e-6)

    def test_init_invalid(self):
        """测试无效参数"""
        with pytest.raises(ValueError):
            RCLowPass(R=-1, C=1e-6)
        with pytest.raises(ValueError):
            RCLowPass(R=1000, C=0)

    def test_dc_gain(self):
        """测试直流增益应为 0dB (增益为1)"""
        filt = RCLowPass(R=1000, C=1e-6)
        f = np.array([0.001])  # 近似直流
        mag = filt.magnitude(f)
        assert mag[0] == pytest.approx(1.0, abs=1e-3)

    def test_cutoff_frequency(self):
        """测试截止频率处增益应为 -3dB"""
        filt = RCLowPass(R=1000, C=1e-6)
        f = np.array([filt.fc])
        mag_db = filt.magnitude_db(f)
        assert mag_db[0] == pytest.approx(-3.01, abs=0.1)

    def test_high_freq_attenuation(self):
        """测试高频衰减特性 (-20dB/decade)"""
        filt = RCLowPass(R=1000, C=1e-6)
        f1 = filt.fc * 10
        f2 = filt.fc * 100
        mag_db_1 = filt.magnitude_db(np.array([f1]))[0]
        mag_db_2 = filt.magnitude_db(np.array([f2]))[0]
        # 每十倍频应衰减约 20dB
        assert (mag_db_1 - mag_db_2) == pytest.approx(20.0, abs=1.0)

    def test_phase_at_cutoff(self):
        """测试截止频率处相位应为 -45 度"""
        filt = RCLowPass(R=1000, C=1e-6)
        f = np.array([filt.fc])
        phase = filt.phase(f)
        assert phase[0] == pytest.approx(-45.0, abs=0.5)

    def test_phase_range(self):
        """测试相位范围 0 到 -90 度"""
        filt = RCLowPass(R=1000, C=1e-6)
        f = np.array([0.001, filt.fc, filt.fc * 1000])
        phase = filt.phase(f)
        assert phase[0] == pytest.approx(0.0, abs=1.0)  # 低频接近0
        assert phase[2] == pytest.approx(-90.0, abs=1.0)  # 高频接近-90

    def test_step_response(self):
        """测试阶跃响应"""
        filt = RCLowPass(R=1000, C=1e-6)
        # 在 1τ 时应达到 63.2%
        t = np.array([filt.tau])
        step = filt.step_response(t)
        assert step[0] == pytest.approx(0.632, abs=0.01)

    def test_step_response_final_value(self):
        """测试阶跃响应最终值为 1"""
        filt = RCLowPass(R=1000, C=1e-6)
        t = np.array([filt.tau * 10])
        step = filt.step_response(t)
        assert step[0] == pytest.approx(1.0, abs=0.01)

    def test_magnitude_array(self):
        """测试数组输入"""
        filt = RCLowPass(R=1000, C=1e-6)
        f = np.logspace(0, 6, 100)
        mag = filt.magnitude(f)
        assert len(mag) == 100
        assert np.all(mag >= 0)
        assert np.all(mag <= 1)

    def test_repr(self):
        """测试字符串表示"""
        filt = RCLowPass(R=1000, C=1e-6)
        s = repr(filt)
        assert "RCLowPass" in s
        assert "1000" in s
        assert "1e-06" in s


class TestRLLowPass:
    """RL 低通滤波器测试"""

    def test_init(self):
        """测试初始化"""
        filt = RLLowPass(R=100, L=0.1)
        assert filt.R == 100
        assert filt.L == 0.1
        assert filt.tau == pytest.approx(0.001, rel=1e-6)
        assert filt.fc == pytest.approx(100 / (2 * np.pi * 0.1), rel=1e-6)

    def test_init_invalid(self):
        """测试无效参数"""
        with pytest.raises(ValueError):
            RLLowPass(R=-1, L=0.1)
        with pytest.raises(ValueError):
            RLLowPass(R=100, L=0)

    def test_dc_gain(self):
        """测试直流增益应为 1"""
        filt = RLLowPass(R=100, L=0.1)
        f = np.array([0.001])
        mag = filt.magnitude(f)
        assert mag[0] == pytest.approx(1.0, abs=1e-3)

    def test_cutoff_frequency(self):
        """测试截止频率处增益应为 -3dB"""
        filt = RLLowPass(R=100, L=0.1)
        f = np.array([filt.fc])
        mag_db = filt.magnitude_db(f)
        assert mag_db[0] == pytest.approx(-3.01, abs=0.1)

    def test_phase_at_cutoff(self):
        """测试截止频率处相位应为 -45 度"""
        filt = RLLowPass(R=100, L=0.1)
        f = np.array([filt.fc])
        phase = filt.phase(f)
        assert phase[0] == pytest.approx(-45.0, abs=0.5)

    def test_step_response(self):
        """测试阶跃响应在 1τ 时达到 63.2%"""
        filt = RLLowPass(R=100, L=0.1)
        t = np.array([filt.tau])
        step = filt.step_response(t)
        assert step[0] == pytest.approx(0.632, abs=0.01)


class TestLowPassEquivalence:
    """测试 RC 和 RL 低通滤波器的等价性"""

    def test_same_cutoff(self):
        """相同截止频率下，RC 和 RL 的频率响应应相同"""
        # 设计相同截止频率 1000Hz
        fc = 1000
        R_rc = 1000
        C = 1.0 / (2 * np.pi * R_rc * fc)

        R_rl = 100
        L = R_rl / (2 * np.pi * fc)

        rc_filt = RCLowPass(R_rc, C)
        rl_filt = RLLowPass(R_rl, L)

        f = np.logspace(1, 5, 100)
        mag_rc = rc_filt.magnitude(f)
        mag_rl = rl_filt.magnitude(f)

        np.testing.assert_allclose(mag_rc, mag_rl, rtol=1e-6)
