"""
实际应用测试
"""

import pytest
import numpy as np
from src.applications import (
    VoltageDivider, RCFilter, RLCFilter, Amplifier,
    Integrator, Differentiator
)


class TestVoltageDivider:
    """分压器测试"""

    def test_basic_divider(self):
        divider = VoltageDivider(v_in=12, r1=1000, r2=2000)
        assert abs(divider.output_voltage() - 8.0) < 1e-10
        assert abs(divider.transfer_ratio() - 2/3) < 1e-10

    def test_equal_resistors(self):
        divider = VoltageDivider(v_in=10, r1=1000, r2=1000)
        assert abs(divider.output_voltage() - 5.0) < 1e-10

    def test_with_load(self):
        divider = VoltageDivider(v_in=12, r1=1000, r2=2000, r_load=2000)
        # R2与R_load并联 = 2000*2000/(2000+2000) = 1000
        # V_out = 12 * 1000/(1000+1000) = 6V
        assert abs(divider.output_voltage() - 6.0) < 1e-10

    def test_output_impedance(self):
        divider = VoltageDivider(v_in=12, r1=1000, r2=2000)
        # R1||R2 = 1000*2000/3000 = 666.67
        expected = 1000 * 2000 / 3000
        assert abs(divider.output_impedance() - expected) < 1e-10

    def test_current(self):
        divider = VoltageDivider(v_in=12, r1=1000, r2=2000)
        assert abs(divider.current() - 12/3000) < 1e-10

    def test_power_dissipation(self):
        divider = VoltageDivider(v_in=12, r1=1000, r2=2000)
        p_r1, p_r2 = divider.power_dissipation()
        i = 12 / 3000
        assert abs(p_r1 - i**2 * 1000) < 1e-10
        assert abs(p_r2 - i**2 * 2000) < 1e-10


class TestRCFilter:
    """RC滤波器测试"""

    def test_low_pass_cutoff(self):
        lpf = RCFilter(r=1000, c=1e-6, filter_type='low')
        f_c = lpf.cutoff_frequency()
        expected = 1.0 / (2 * np.pi * 1000 * 1e-6)
        assert abs(f_c - expected) < 1e-6

    def test_high_pass_cutoff(self):
        hpf = RCFilter(r=1000, c=1e-6, filter_type='high')
        f_c = hpf.cutoff_frequency()
        expected = 1.0 / (2 * np.pi * 1000 * 1e-6)
        assert abs(f_c - expected) < 1e-6

    def test_time_constant(self):
        lpf = RCFilter(r=1000, c=1e-6)
        assert abs(lpf.time_constant() - 1e-3) < 1e-10

    def test_low_pass_transfer(self):
        lpf = RCFilter(r=1000, c=1e-6, filter_type='low')
        f_c = lpf.cutoff_frequency()

        # 在截止频率处，增益为 -3dB
        gain_at_fc = lpf.gain_dB(f_c)
        assert abs(gain_at_fc - (-3)) < 0.1

        # 低频时增益接近0dB
        gain_low = lpf.gain_dB(f_c / 10)
        assert gain_low > -1

        # 高频时增益下降
        gain_high = lpf.gain_dB(f_c * 10)
        assert gain_high < -10

    def test_high_pass_transfer(self):
        hpf = RCFilter(r=1000, c=1e-6, filter_type='high')
        f_c = hpf.cutoff_frequency()

        # 在截止频率处，增益为 -3dB
        gain_at_fc = hpf.gain_dB(f_c)
        assert abs(gain_at_fc - (-3)) < 0.1

        # 高频时增益接近0dB
        gain_high = hpf.gain_dB(f_c * 10)
        assert gain_high > -1

        # 低频时增益下降
        gain_low = hpf.gain_dB(f_c / 10)
        assert gain_low < -10

    def test_invalid_type(self):
        with pytest.raises(ValueError):
            RCFilter(r=1000, c=1e-6, filter_type='invalid')

    def test_frequency_response(self):
        lpf = RCFilter(r=1000, c=1e-6, filter_type='low')
        fr = lpf.frequency_response(10, 1e6, 100)
        assert len(fr.frequencies) == 100
        assert len(fr.magnitude) == 100


class TestRLCFilter:
    """RLC滤波器测试"""

    def test_resonance_frequency(self):
        bpf = RLCFilter(r=100, l=1e-3, c=1e-6, filter_type='bandpass')
        f_r = bpf.resonance_freq()
        expected = 1.0 / (2 * np.pi * np.sqrt(1e-3 * 1e-6))
        assert abs(f_r - expected) < 1e-6

    def test_quality_factor(self):
        bpf = RLCFilter(r=100, l=1e-3, c=1e-6, filter_type='bandpass')
        q = bpf.quality_factor()
        f_r = bpf.resonance_freq()
        expected = 2 * np.pi * f_r * 1e-3 / 100
        assert abs(q - expected) < 1e-6

    def test_bandwidth(self):
        bpf = RLCFilter(r=100, l=1e-3, c=1e-6, filter_type='bandpass')
        bw = bpf.bandwidth()
        expected = 100 / (2 * np.pi * 1e-3)
        assert abs(bw - expected) < 1e-6

    def test_bandpass_at_resonance(self):
        bpf = RLCFilter(r=100, l=1e-3, c=1e-6, filter_type='bandpass')
        f_r = bpf.resonance_freq()
        h = bpf.transfer_function(f_r)
        # 在谐振频率处，增益应等于Q
        q = bpf.quality_factor()
        assert abs(abs(h) - q) < 0.01

    def test_invalid_type(self):
        with pytest.raises(ValueError):
            RLCFilter(r=100, l=1e-3, c=1e-6, filter_type='invalid')


class TestAmplifier:
    """放大器测试"""

    def test_inverting_gain(self):
        amp = Amplifier(r_in=10000, r_f=100000, config='inverting')
        assert abs(amp.gain() - (-10)) < 1e-10

    def test_non_inverting_gain(self):
        amp = Amplifier(r_in=10000, r_f=100000, config='non_inverting')
        assert abs(amp.gain() - 11) < 1e-10

    def test_gain_dB(self):
        amp = Amplifier(r_in=10000, r_f=100000, config='inverting')
        gain_dB = amp.gain_dB()
        expected = 20 * np.log10(10)
        assert abs(gain_dB - expected) < 1e-10

    def test_output_voltage(self):
        amp = Amplifier(r_in=10000, r_f=100000, config='inverting')
        assert abs(amp.output_voltage(1) - (-10)) < 1e-10
        assert abs(amp.output_voltage(0.5) - (-5)) < 1e-10

    def test_input_impedance_inverting(self):
        amp = Amplifier(r_in=10000, r_f=100000, config='inverting')
        assert amp.input_impedance() == 10000

    def test_input_impedance_non_inverting(self):
        amp = Amplifier(r_in=10000, r_f=100000, config='non_inverting')
        assert amp.input_impedance() == float('inf')

    def test_bandwidth(self):
        amp = Amplifier(r_in=10000, r_f=100000, config='inverting')
        gbw = 1e6  # 1MHz
        bw = amp.bandwidth(gbw)
        assert abs(bw - 1e5) < 1e-10  # 100kHz

    def test_invalid_config(self):
        with pytest.raises(ValueError):
            Amplifier(r_in=10000, r_f=100000, config='invalid')


class TestIntegrator:
    """积分器测试"""

    def test_gain_at_freq(self):
        integrator = Integrator(r=10000, c=1e-6)
        f = 100
        gain = integrator.gain_at_freq(f)
        expected = -1.0 / (2 * np.pi * f * 10000 * 1e-6)
        assert abs(gain - expected) < 1e-6

    def test_dc_gain(self):
        integrator = Integrator(r=10000, c=1e-6)
        assert integrator.gain_at_freq(0) == float('inf')


class TestDifferentiator:
    """微分器测试"""

    def test_gain_at_freq(self):
        differentiator = Differentiator(r=10000, c=1e-6)
        f = 100
        gain = differentiator.gain_at_freq(f)
        expected = -2 * np.pi * f * 10000 * 1e-6
        assert abs(gain - expected) < 1e-6

    def test_dc_gain(self):
        differentiator = Differentiator(r=10000, c=1e-6)
        assert differentiator.gain_at_freq(0) == 0
