"""运算放大器电路测试"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.opamp import (
    OpAmpParams, InvertingAmp, NonInvertingAmp,
    DifferentialAmp, InstrumentationAmp
)


class TestOpAmpParams:
    """运放参数测试"""

    def test_default_params(self):
        op = OpAmpParams()
        assert op.A_OL == 1e5
        assert op.GBW == 1e6
        assert op.SR == 0.5e6

    def test_cmrr_linear(self):
        op = OpAmpParams(CMRR=90)
        assert abs(op.CMRR_linear - 10 ** 4.5) < 1

    def test_psrr_linear(self):
        op = OpAmpParams(PSRR=90)
        assert abs(op.PSRR_linear - 10 ** 4.5) < 1


class TestInvertingAmp:
    """反相放大器测试"""

    @pytest.fixture
    def inv_amp(self):
        """增益为 -10 的反相放大器"""
        return InvertingAmp(R_in=10e3, R_f=100e3)

    def test_gain(self, inv_amp):
        assert inv_amp.gain() == -10.0

    def test_gain_with_loading(self, inv_amp):
        """实际增益接近理想值"""
        actual = inv_amp.gain_with_loading()
        assert abs(actual - (-10.0)) < 0.1

    def test_input_impedance(self, inv_amp):
        """输入阻抗等于 Rin"""
        assert inv_amp.input_impedance() == 10e3

    def test_bandwidth(self, inv_amp):
        """带宽 = GBW / |Av|"""
        bw = inv_amp.bandwidth()
        assert abs(bw - 1e6 / 10) < 1

    def test_max_output_swing(self, inv_amp):
        """转换速率限制"""
        Vmax = inv_amp.max_output_swing(1000)
        expected = 0.5e6 / (2 * np.pi * 1000)
        assert abs(Vmax - min(expected, 13.5)) < 0.1

    def test_transfer_function_dc(self, inv_amp):
        """DC 传递函数应等于增益"""
        f = np.array([0.001])  # 近似 DC
        H = inv_amp.transfer_function(f)
        assert abs(np.real(H[0]) - (-10.0)) < 0.01

    def test_transfer_function_unity(self):
        """增益为 -1 的反相放大器"""
        amp = InvertingAmp(R_in=10e3, R_f=10e3)
        assert amp.gain() == -1.0

    def test_transfer_function_high_gain(self):
        """高增益反相放大器"""
        amp = InvertingAmp(R_in=1e3, R_f=1e6)
        assert amp.gain() == -1000.0

    def test_summary(self, inv_amp):
        s = inv_amp.summary()
        assert s['type'] == '反相放大器 (Inverting Amplifier)'
        assert s['ideal_gain'] == -10.0
        assert s['phase_shift'] == 180.0


class TestNonInvertingAmp:
    """同相放大器测试"""

    @pytest.fixture
    def ni_amp(self):
        """增益为 11 的同相放大器"""
        return NonInvertingAmp(R_in=10e3, R_f=100e3)

    def test_gain(self, ni_amp):
        assert ni_amp.gain() == 11.0

    def test_gain_with_loading(self, ni_amp):
        actual = ni_amp.gain_with_loading()
        assert abs(actual - 11.0) < 0.1

    def test_high_input_impedance(self, ni_amp):
        """输入阻抗非常高"""
        Z_in = ni_amp.input_impedance()
        assert Z_in > 1e6

    def test_bandwidth(self, ni_amp):
        bw = ni_amp.bandwidth()
        assert abs(bw - 1e6 / 11) < 100

    def test_unity_gain(self):
        """增益为1的同相放大器 (缓冲器)"""
        amp = NonInvertingAmp(R_in=10e3, R_f=0)
        assert amp.gain() == 1.0

    def test_transfer_function_dc(self, ni_amp):
        f = np.array([0.001])
        H = ni_amp.transfer_function(f)
        assert abs(np.real(H[0]) - 11.0) < 0.1

    def test_summary(self, ni_amp):
        s = ni_amp.summary()
        assert s['ideal_gain'] == 11.0
        assert s['phase_shift'] == 0.0


class TestDifferentialAmp:
    """差分放大器测试"""

    @pytest.fixture
    def diff_amp(self):
        """增益为10的差分放大器"""
        return DifferentialAmp(R1=10e3, R_f=100e3)

    def test_differential_gain(self, diff_amp):
        assert diff_amp.differential_gain() == 10.0

    def test_output_pure_differential(self, diff_amp):
        """纯差分信号"""
        Vout = diff_amp.output(V1=0.0, V2=0.1)
        assert abs(Vout - 1.0) < 0.01

    def test_output_common_mode(self, diff_amp):
        """共模信号被抑制"""
        Vout = diff_amp.output(V1=5.0, V2=5.0)
        assert abs(Vout) < 0.01

    def test_output_saturation(self, diff_amp):
        """大信号饱和"""
        Vout = diff_amp.output(V1=0.0, V2=10.0)
        assert abs(Vout) <= diff_amp.opamp.V_sat + 0.01

    def test_cmrr_ideal(self, diff_amp):
        """理想匹配时CMRR非常高"""
        cmrr = diff_amp.cmrr()
        assert cmrr > 200  # 理想情况下非常高

    def test_cmrr_mismatch(self):
        """电阻失配降低CMRR"""
        amp = DifferentialAmp(R1=10e3, R_f=100e3, R2=10.1e3, R_g=100e3)
        cmrr = amp.cmrr()
        assert cmrr < 200

    def test_bandwidth(self, diff_amp):
        bw = diff_amp.bandwidth()
        assert abs(bw - 1e6 / 10) < 1

    def test_summary(self, diff_amp):
        s = diff_amp.summary()
        assert '差分放大器' in s['type']
        assert s['differential_gain'] == 10.0


class TestInstrumentationAmp:
    """仪表放大器测试"""

    @pytest.fixture
    def inamp(self):
        """增益为100的仪表放大器"""
        return InstrumentationAmp(R1=49.4e3, R_g=1e3)

    def test_gain(self, inamp):
        expected = 1 + 2 * 49.4e3 / 1e3
        assert abs(inamp.gain() - expected) < 0.1

    def test_gain_formula(self, inamp):
        """G = 1 + 2*R1/Rg"""
        G = inamp.gain()
        assert G == 1 + 2 * 49.4e3 / 1e3

    def test_set_gain(self, inamp):
        """动态设置增益"""
        inamp.set_gain(50)
        expected_Rg = 2 * 49.4e3 / (50 - 1)
        assert abs(inamp.R_g - expected_Rg) < 1.0
        assert abs(inamp.gain() - 50) < 0.1

    def test_set_gain_error(self, inamp):
        """增益不能小于等于1"""
        with pytest.raises(ValueError):
            inamp.set_gain(1.0)

    def test_output_differential(self, inamp):
        """差分输出"""
        Vout = inamp.output(V1=0.0, V2=0.01)
        expected = inamp.gain() * 0.01
        assert abs(Vout - expected) < 0.1

    def test_output_saturation(self, inamp):
        """大信号饱和"""
        Vout = inamp.output(V1=0.0, V2=1.0)
        assert abs(Vout) <= inamp.opamp.V_sat + 0.01

    def test_high_input_impedance(self, inamp):
        Z_in = inamp.input_impedance()
        assert Z_in > 1e10

    def test_bandwidth(self, inamp):
        bw = inamp.bandwidth()
        assert bw > 0
        assert bw < inamp.opamp.GBW

    def test_summary(self, inamp):
        s = inamp.summary()
        assert '仪表放大器' in s['type']
        assert s['gain'] > 1


class TestOpAmpComparison:
    """运放电路对比测试"""

    def test_inverting_vs_noninverting_gain(self):
        """反相和同相放大器增益关系"""
        inv = InvertingAmp(R_in=10e3, R_f=100e3)
        ni = NonInvertingAmp(R_in=10e3, R_f=100e3)

        # |Av_inv| = Rf/Rin = 10
        # Av_ni = 1 + Rf/Rin = 11
        assert abs(inv.gain()) == 10.0
        assert ni.gain() == 11.0

    def test_bandwidth_gain_tradeoff(self):
        """增益越高，带宽越窄"""
        amp_low = InvertingAmp(R_in=10e3, R_f=10e3)   # gain = -1
        amp_high = InvertingAmp(R_in=10e3, R_f=1e6)   # gain = -100

        assert amp_low.bandwidth() > amp_high.bandwidth()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
