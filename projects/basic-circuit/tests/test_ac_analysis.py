"""
交流电路分析测试
"""

import pytest
import numpy as np
from src.circuit import Circuit
from src.ac_analysis import (
    ACAnalyzer, Phasor, impedance_series, impedance_parallel,
    resonance_frequency, quality_factor
)


class TestPhasor:
    """相量测试"""

    def test_create_phasor(self):
        p = Phasor(magnitude=10, phase=np.pi/4)
        assert p.magnitude == 10
        assert abs(p.phase - np.pi/4) < 1e-10

    def test_to_complex(self):
        p = Phasor(magnitude=10, phase=0)
        z = p.to_complex()
        assert abs(z - 10) < 1e-10

    def test_from_complex(self):
        z = complex(3, 4)
        p = Phasor.from_complex(z)
        assert abs(p.magnitude - 5) < 1e-10
        assert abs(p.phase - np.arctan2(4, 3)) < 1e-10


class TestACAnalyzer:
    """交流分析器测试"""

    def test_resistor_ac(self):
        """测试纯电阻电路的交流分析"""
        circuit = Circuit("AC Resistor")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("IN")
        circuit.set_ground(n0)

        circuit.add_voltage_source("V1", n1, n0, 10, frequency=1000)
        circuit.add_resistor("R1", n1, n0, 1000)

        analyzer = ACAnalyzer(circuit)
        result = analyzer.solve(1000)

        # 电压应为10V
        assert abs(abs(result.node_voltages[n1]) - 10) < 1e-6

        # 电流应为10mA
        assert abs(abs(result.branch_currents["R1"]) - 0.01) < 1e-6

    def test_rc_circuit(self):
        """测试RC电路"""
        circuit = Circuit("RC Circuit")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("IN")
        circuit.set_ground(n0)

        circuit.add_voltage_source("V1", n1, n0, 10, frequency=1000)
        circuit.add_resistor("R1", n1, n0, 1000)
        circuit.add_capacitor("C1", n1, n0, 1e-6)

        analyzer = ACAnalyzer(circuit)
        result = analyzer.solve(1000)

        # 验证阻抗
        z_r = result.impedances["R1"]
        z_c = result.impedances["C1"]
        assert abs(z_r - 1000) < 1e-6
        assert abs(z_c.imag + 1/(2*np.pi*1000*1e-6)) < 1e-6

    def test_inductor_ac(self):
        """测试电感的交流特性"""
        circuit = Circuit("AC Inductor")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("IN")
        circuit.set_ground(n0)

        circuit.add_voltage_source("V1", n1, n0, 10, frequency=1000)
        circuit.add_inductor("L1", n1, n0, 1e-3)

        analyzer = ACAnalyzer(circuit)
        result = analyzer.solve(1000)

        # 电感阻抗应为 jωL
        z_l = result.impedances["L1"]
        expected = 1j * 2 * np.pi * 1000 * 1e-3
        assert abs(z_l - expected) < 1e-6

    def test_frequency_response(self):
        """测试频率响应计算"""
        circuit = Circuit("RC Low Pass")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("IN")
        n2 = circuit.add_node("OUT")
        circuit.set_ground(n0)

        circuit.add_voltage_source("V1", n1, n0, 1)
        circuit.add_resistor("R1", n1, n2, 1000)
        circuit.add_capacitor("C1", n2, n0, 1e-6)

        analyzer = ACAnalyzer(circuit)
        fr = analyzer.frequency_response(10, 1e6, 1000, node_id=n2)

        # 低频时增益接近1
        assert fr.magnitude[0] > 0.9

        # 高频时增益接近0
        assert fr.magnitude[-1] < 0.1

    def test_no_ground_error(self):
        """测试未设置接地点时报错"""
        circuit = Circuit()
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("IN")
        circuit.add_voltage_source("V1", n1, n0, 10)
        circuit.add_resistor("R1", n1, n0, 1000)

        analyzer = ACAnalyzer(circuit)
        with pytest.raises(ValueError):
            analyzer.solve(1000)


class TestImpedanceFunctions:
    """阻抗函数测试"""

    def test_series_impedance(self):
        z1 = complex(100, 0)
        z2 = complex(0, 100)
        z_total = impedance_series(z1, z2)
        assert abs(z_total - complex(100, 100)) < 1e-10

    def test_parallel_impedance(self):
        z1 = complex(100, 0)
        z2 = complex(100, 0)
        z_total = impedance_parallel(z1, z2)
        assert abs(z_total - 50) < 1e-10

    def test_parallel_zero_impedance(self):
        z1 = complex(100, 0)
        z2 = complex(0, 0)
        z_total = impedance_parallel(z1, z2)
        assert abs(z_total) < 1e-10


class TestResonanceFrequency:
    """谐振频率测试"""

    def test_basic_resonance(self):
        # f = 1/(2π√(LC))
        l = 1e-3  # 1mH
        c = 1e-6  # 1μF
        f = resonance_frequency(l, c)
        expected = 1.0 / (2 * np.pi * np.sqrt(l * c))
        assert abs(f - expected) < 1e-6

    def test_invalid_values(self):
        with pytest.raises(ValueError):
            resonance_frequency(0, 1e-6)
        with pytest.raises(ValueError):
            resonance_frequency(1e-3, 0)


class TestQualityFactor:
    """品质因数测试"""

    def test_basic_q_factor(self):
        l = 1e-3  # 1mH
        r = 10    # 10Ω
        f = 1000  # 1kHz
        q = quality_factor(l, r, f)
        expected = 2 * np.pi * f * l / r
        assert abs(q - expected) < 1e-6

    def test_invalid_resistance(self):
        with pytest.raises(ValueError):
            quality_factor(1e-3, 0, 1000)
