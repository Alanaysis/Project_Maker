"""
交流分析测试
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.circuit import Circuit
from src.ac_analysis import (
    ACAnalysis, impedance_resistor, impedance_capacitor, impedance_inductor,
    resonance_frequency, rc_cutoff_frequency, rl_cutoff_frequency,
    rc_lowpass_response, rc_highpass_response, quality_factor, bandwidth,
    voltage_gain_db, phase_degrees
)


class TestImpedance:
    """阻抗计算测试"""

    def test_resistor_impedance(self):
        """测试电阻阻抗"""
        z = impedance_resistor(1000, 1000)
        assert z == complex(1000, 0)

    def test_capacitor_impedance(self):
        """测试电容阻抗"""
        c = 1e-6
        f = 1000
        z = impedance_capacitor(c, f)
        expected = 1.0 / (2j * np.pi * f * c)
        assert abs(z - expected) < 1e-6

    def test_inductor_impedance(self):
        """测试电感阻抗"""
        l = 1e-3
        f = 1000
        z = impedance_inductor(l, f)
        expected = 2j * np.pi * f * l
        assert abs(z - expected) < 1e-6

    def test_capacitor_dc_impedance(self):
        """测试电容直流阻抗"""
        z = impedance_capacitor(1e-6, 0)
        assert abs(z) == float('inf')


class TestCutoffFrequencies:
    """截止频率测试"""

    def test_rc_cutoff(self):
        """测试 RC 截止频率"""
        r = 1000
        c = 1e-6
        f_c = rc_cutoff_frequency(r, c)
        expected = 1.0 / (2 * np.pi * r * c)
        assert f_c == pytest.approx(expected)

    def test_rl_cutoff(self):
        """测试 RL 截止频率"""
        r = 1000
        l = 1e-3
        f_c = rl_cutoff_frequency(r, l)
        expected = r / (2 * np.pi * l)
        assert f_c == pytest.approx(expected)

    def test_resonance(self):
        """测试 LC 谐振频率"""
        l = 1e-3
        c = 1e-6
        f_r = resonance_frequency(l, c)
        expected = 1.0 / (2 * np.pi * np.sqrt(l * c))
        assert f_r == pytest.approx(expected)


class TestFilterResponses:
    """滤波器响应测试"""

    def test_rc_lowpass_dc(self):
        """测试 RC 低通直流响应"""
        frequencies = np.array([0])
        r = 1000
        c = 1e-6
        h = rc_lowpass_response(frequencies, r, c)
        assert abs(h[0]) == pytest.approx(1.0)

    def test_rc_lowpass_cutoff(self):
        """测试 RC 低通截止频率处响应"""
        r = 1000
        c = 1e-6
        f_c = rc_cutoff_frequency(r, c)
        frequencies = np.array([f_c])
        h = rc_lowpass_response(frequencies, r, c)
        # 截止频率处增益为 -3dB (0.707)
        assert abs(h[0]) == pytest.approx(0.707, abs=0.01)

    def test_rc_highpass_dc(self):
        """测试 RC 高通直流响应"""
        frequencies = np.array([0])
        r = 1000
        c = 1e-6
        h = rc_highpass_response(frequencies, r, c)
        assert abs(h[0]) == pytest.approx(0.0)

    def test_rc_highpass_cutoff(self):
        """测试 RC 高通截止频率处响应"""
        r = 1000
        c = 1e-6
        f_c = rc_cutoff_frequency(r, c)
        frequencies = np.array([f_c])
        h = rc_highpass_response(frequencies, r, c)
        assert abs(h[0]) == pytest.approx(0.707, abs=0.01)


class TestQualityFactor:
    """品质因数测试"""

    def test_q_factor(self):
        """测试品质因数"""
        r = 10
        l = 1e-3
        c = 1e-6
        q = quality_factor(r, l, c)
        expected = (1.0 / r) * np.sqrt(l / c)
        assert q == pytest.approx(expected)

    def test_bandwidth(self):
        """测试带宽"""
        f0 = 1000
        q = 10
        bw = bandwidth(f0, q)
        assert bw == pytest.approx(100)


class TestACAnalysis:
    """交流分析测试"""

    def test_rc_lowpass_circuit(self):
        """测试 RC 低通滤波器"""
        circuit = Circuit("RC Low Pass")
        circuit.add_voltage_source("V1", 0, 1, 0, ac_mag=1)
        circuit.add_resistor("R1", 1, 2, 1000)
        circuit.add_capacitor("C1", 2, 0, 1e-6)
        circuit.build_node_map()

        analyzer = ACAnalysis(circuit)

        # 直流附近，输出应接近输入
        result = analyzer.solve(1)
        assert result.magnitude(2) == pytest.approx(1.0, abs=0.01)

        # 截止频率处，输出应为 0.707
        f_c = rc_cutoff_frequency(1000, 1e-6)
        result = analyzer.solve(f_c)
        assert result.magnitude(2) == pytest.approx(0.707, abs=0.01)

        # 高频处，输出应接近 0
        result = analyzer.solve(1e6)
        assert result.magnitude(2) < 0.01

    def test_ac_magnitude(self):
        """测试 AC 幅度"""
        circuit = Circuit("AC Test")
        circuit.add_voltage_source("V1", 0, 1, 0, ac_mag=5)
        circuit.add_resistor("R1", 1, 0, 1000)
        circuit.build_node_map()

        analyzer = ACAnalysis(circuit)
        result = analyzer.solve(1000)

        assert result.magnitude(1) == pytest.approx(5.0)

    def test_frequency_response(self):
        """测试频率响应"""
        circuit = Circuit("Freq Response")
        circuit.add_voltage_source("V1", 0, 1, 0, ac_mag=1)
        circuit.add_resistor("R1", 1, 2, 1000)
        circuit.add_capacitor("C1", 2, 0, 1e-6)
        circuit.build_node_map()

        analyzer = ACAnalysis(circuit)
        fr = analyzer.frequency_response(1, 1e6, 100)

        # 频率响应应包含正确的点数
        assert len(fr.frequencies) == 100
        assert len(fr.responses) == 100

        # 低频处幅度应接近 1
        low_freq_mag = fr.get_magnitude(2)[0]
        assert low_freq_mag == pytest.approx(1.0, abs=0.1)

    def test_db_calculation(self):
        """测试分贝计算"""
        circuit = Circuit("DB Test")
        circuit.add_voltage_source("V1", 0, 1, 0, ac_mag=1)
        circuit.add_resistor("R1", 1, 0, 1000)
        circuit.build_node_map()

        analyzer = ACAnalysis(circuit)
        result = analyzer.solve(1000)

        # 1V 输入，分贝应为 0
        assert result.db(1) == pytest.approx(0.0, abs=0.01)


class TestGainAndPhase:
    """增益和相位测试"""

    def test_voltage_gain_db(self):
        """测试电压增益分贝"""
        # 10x 增益 = 20dB
        gain_db = voltage_gain_db(10, 1)
        assert gain_db == pytest.approx(20.0)

        # -3dB
        gain_db = voltage_gain_db(0.707, 1)
        assert gain_db == pytest.approx(-3.0, abs=0.1)

    def test_phase_degrees(self):
        """测试相位度数"""
        # 同相
        phase = phase_degrees(1, 1)
        assert phase == pytest.approx(0.0)

        # 90度相移
        phase = phase_degrees(1j, 1)
        assert phase == pytest.approx(90.0)

        # -90度相移
        phase = phase_degrees(-1j, 1)
        assert phase == pytest.approx(-90.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
