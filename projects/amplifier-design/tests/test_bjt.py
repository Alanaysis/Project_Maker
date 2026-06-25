"""BJT 放大器测试"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.bjt import BJTParams, CommonEmitter, CommonCollector, CommonBase


class TestBJTParams:
    """BJT 参数测试"""

    def test_default_params(self):
        bjt = BJTParams()
        assert bjt.beta == 100.0
        assert bjt.V_A == 100.0
        assert bjt.V_BE == 0.7
        assert bjt.V_T == 0.026

    def test_transconductance(self):
        bjt = BJTParams()
        gm = bjt.transconductance(1e-3)  # 1mA
        assert abs(gm - 1e-3 / 0.026) < 0.01

    def test_r_pi(self):
        bjt = BJTParams(beta=100)
        r_pi = bjt.r_pi_from_ic(1e-3)  # 1mA
        expected = 100 * 0.026 / 1e-3
        assert abs(r_pi - expected) < 0.01

    def test_output_resistance(self):
        bjt = BJTParams(V_A=100)
        r_o = bjt.output_resistance(1e-3)
        assert abs(r_o - 100e3) < 1.0

    def test_output_resistance_zero_current(self):
        bjt = BJTParams()
        r_o = bjt.output_resistance(0)
        assert r_o == float('inf')


class TestCommonEmitter:
    """共射放大器测试"""

    @pytest.fixture
    def ce_amp(self):
        """标准共射放大器: VCC=12V, IC≈1mA"""
        return CommonEmitter(
            R_B1=47e3, R_B2=10e3, R_C=4.7e3, R_E=2.2e3,
            V_CC=12.0, bjt=BJTParams(beta=100)
        )

    def test_operating_point(self, ce_amp):
        op = ce_amp.operating_point()
        # V_B = 12 * 10k / 57k ≈ 2.1V
        assert abs(op['V_B'] - 2.105) < 0.05
        # V_E = V_B - 0.7 ≈ 1.4V
        assert abs(op['V_E'] - 1.405) < 0.05
        # I_C ≈ V_E / R_E ≈ 0.64mA
        assert 0.5e-3 < op['I_C'] < 1.0e-3
        # V_CE 应在合理范围
        assert op['V_CE'] > 1.0

    def test_voltage_gain_negative(self, ce_amp):
        """共射放大器增益为负 (反相)"""
        Av = ce_amp.voltage_gain()
        assert Av < 0

    def test_voltage_gain_magnitude(self, ce_amp):
        """增益幅度合理 (约10~100)"""
        Av = abs(ce_amp.voltage_gain())
        assert 5 < Av < 200

    def test_voltage_gain_with_load(self, ce_amp):
        """带负载增益小于空载增益"""
        Av_no_load = abs(ce_amp.voltage_gain())
        Av_with_load = abs(ce_amp.voltage_gain(R_L=4.7e3))
        assert Av_with_load < Av_no_load

    def test_input_impedance(self, ce_amp):
        """输入阻抗在合理范围"""
        Z_in = ce_amp.input_impedance()
        assert Z_in > 0
        assert Z_in < 1e6

    def test_output_impedance(self, ce_amp):
        """输出阻抗约等于 R_C"""
        Z_out = ce_amp.output_impedance()
        assert abs(Z_out - ce_amp.R_C) / ce_amp.R_C < 0.5

    def test_summary(self, ce_amp):
        s = ce_amp.summary()
        assert s['type'] == '共射放大器 (Common Emitter)'
        assert s['phase_shift'] == 180.0

    def test_rb_parallel(self, ce_amp):
        R_B = ce_amp.R_B
        expected = 47e3 * 10e3 / (47e3 + 10e3)
        assert abs(R_B - expected) < 1.0


class TestCommonCollector:
    """共集放大器测试"""

    @pytest.fixture
    def cc_amp(self):
        return CommonCollector(
            R_B1=47e3, R_B2=10e3, R_E=2.2e3,
            V_CC=12.0, bjt=BJTParams(beta=100)
        )

    def test_voltage_gain_near_one(self, cc_amp):
        """共集增益接近1"""
        Av = cc_amp.voltage_gain()
        assert 0.9 < Av < 1.0

    def test_voltage_gain_with_load(self, cc_amp):
        """带负载时增益略低于1"""
        Av = cc_amp.voltage_gain(R_L=1e3)
        assert 0.8 < Av < 1.0

    def test_phase_shift_zero(self, cc_amp):
        """同相输出"""
        s = cc_amp.summary()
        assert s['phase_shift'] == 0.0

    def test_high_input_impedance(self, cc_amp):
        """输入阻抗高 (高于 CE 配置)"""
        Z_in = cc_amp.input_impedance()
        assert Z_in > 1e3

    def test_low_output_impedance(self, cc_amp):
        """输出阻抗低"""
        Z_out = cc_amp.output_impedance(R_s=1e3)
        assert Z_out < 1e3

    def test_operating_point(self, cc_amp):
        op = cc_amp.operating_point()
        assert op['I_C'] > 0
        assert op['V_CE'] > 1.0

    def test_summary(self, cc_amp):
        s = cc_amp.summary()
        assert '共集' in s['type']


class TestCommonBase:
    """共基放大器测试"""

    @pytest.fixture
    def cb_amp(self):
        return CommonBase(
            R_E=2.2e3, R_C=4.7e3, V_CC=12.0,
            I_C_bias=1e-3, bjt=BJTParams(beta=100)
        )

    def test_voltage_gain_positive(self, cb_amp):
        """共基放大器增益为正 (同相)"""
        Av = cb_amp.voltage_gain()
        assert Av > 0

    def test_voltage_gain_magnitude(self, cb_amp):
        """增益幅度合理"""
        Av = cb_amp.voltage_gain()
        assert 10 < Av < 500

    def test_low_input_impedance(self, cb_amp):
        """输入阻抗低"""
        Z_in = cb_amp.input_impedance()
        assert Z_in < 100  # 通常在几十欧姆以内

    def test_high_output_impedance(self, cb_amp):
        """输出阻抗约等于 R_C"""
        Z_out = cb_amp.output_impedance()
        assert abs(Z_out - cb_amp.R_C) / cb_amp.R_C < 0.5

    def test_operating_point(self, cb_amp):
        op = cb_amp.operating_point()
        assert abs(op['I_C'] - 1e-3) < 1e-6

    def test_summary(self, cb_amp):
        s = cb_amp.summary()
        assert '共基' in s['type']
        assert s['phase_shift'] == 0.0


class TestAmplifierComparison:
    """三种放大器对比测试"""

    def test_gain_comparison(self):
        """比较三种放大器的增益特性"""
        bjt = BJTParams(beta=100)
        ce = CommonEmitter(R_B1=47e3, R_B2=10e3, R_C=4.7e3, R_E=2.2e3, V_CC=12, bjt=bjt)
        cc = CommonCollector(R_B1=47e3, R_B2=10e3, R_E=2.2e3, V_CC=12, bjt=bjt)
        cb = CommonBase(R_E=2.2e3, R_C=4.7e3, V_CC=12, I_C_bias=1e-3, bjt=bjt)

        # CE: 高增益，反相
        assert abs(ce.voltage_gain()) > 1
        assert ce.voltage_gain() < 0

        # CC: 增益约1，同相
        assert abs(cc.voltage_gain() - 1) < 0.1

        # CB: 高增益，同相
        assert abs(cb.voltage_gain()) > 1
        assert cb.voltage_gain() > 0

    def test_impedance_comparison(self):
        """比较三种放大器的阻抗特性"""
        bjt = BJTParams(beta=100)
        ce = CommonEmitter(R_B1=47e3, R_B2=10e3, R_C=4.7e3, R_E=2.2e3, V_CC=12, bjt=bjt)
        cc = CommonCollector(R_B1=47e3, R_B2=10e3, R_E=2.2e3, V_CC=12, bjt=bjt)
        cb = CommonBase(R_E=2.2e3, R_C=4.7e3, V_CC=12, I_C_bias=1e-3, bjt=bjt)

        # CC 输入阻抗最高
        assert cc.input_impedance() > ce.input_impedance()
        assert cc.input_impedance() > cb.input_impedance()

        # CB 输入阻抗最低
        assert cb.input_impedance() < ce.input_impedance()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
