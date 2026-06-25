"""
直流电路分析测试
"""

import pytest
import numpy as np
from src.circuit import Circuit
from src.dc_analysis import (
    DCAnalyzer, voltage_divider, current_divider,
    series_resistance, parallel_resistance
)


class TestDCAnalyzer:
    """直流分析器测试"""

    def test_simple_resistor_circuit(self):
        """测试简单电阻电路: V=10V, R=1000Ω -> I=10mA"""
        circuit = Circuit("Simple Resistor")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        circuit.set_ground(n0)

        circuit.add_voltage_source("V1", n1, n0, 10)
        circuit.add_resistor("R1", n1, n0, 1000)

        analyzer = DCAnalyzer(circuit)
        result = analyzer.solve()

        assert abs(result.node_voltages[n1] - 10) < 1e-6
        assert abs(result.branch_currents["R1"] - 0.01) < 1e-6
        assert abs(result.branch_voltages["R1"] - 10) < 1e-6

    def test_series_resistors(self):
        """测试串联电阻: V=10V, R1=1000Ω, R2=2000Ω"""
        circuit = Circuit("Series Resistors")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        n2 = circuit.add_node("MID")
        circuit.set_ground(n0)

        circuit.add_voltage_source("V1", n1, n0, 10)
        circuit.add_resistor("R1", n1, n2, 1000)
        circuit.add_resistor("R2", n2, n0, 2000)

        analyzer = DCAnalyzer(circuit)
        result = analyzer.solve()

        # 电流应为 10/3000 = 3.33mA
        expected_current = 10.0 / 3000
        assert abs(result.branch_currents["R1"] - expected_current) < 1e-6
        assert abs(result.branch_currents["R2"] - expected_current) < 1e-6

        # 中间节点电压应为 10 * 2000/3000 = 6.67V
        expected_voltage = 10.0 * 2000 / 3000
        assert abs(result.node_voltages[n2] - expected_voltage) < 1e-6

    def test_parallel_resistors(self):
        """测试并联电阻: V=10V, R1=1000Ω, R2=1000Ω"""
        circuit = Circuit("Parallel Resistors")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        circuit.set_ground(n0)

        circuit.add_voltage_source("V1", n1, n0, 10)
        circuit.add_resistor("R1", n1, n0, 1000)
        circuit.add_resistor("R2", n1, n0, 1000)

        analyzer = DCAnalyzer(circuit)
        result = analyzer.solve()

        # 每个电阻电流应为 10mA
        assert abs(result.branch_currents["R1"] - 0.01) < 1e-6
        assert abs(result.branch_currents["R2"] - 0.01) < 1e-6

    def test_voltage_divider_circuit(self):
        """测试分压器电路"""
        circuit = Circuit("Voltage Divider")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        n2 = circuit.add_node("OUT")
        circuit.set_ground(n0)

        circuit.add_voltage_source("V1", n1, n0, 12)
        circuit.add_resistor("R1", n1, n2, 1000)
        circuit.add_resistor("R2", n2, n0, 2000)

        analyzer = DCAnalyzer(circuit)
        result = analyzer.solve()

        # 输出电压应为 12 * 2000/3000 = 8V
        expected = 12.0 * 2000 / 3000
        assert abs(result.node_voltages[n2] - expected) < 1e-6

    def test_with_current_source(self):
        """测试含电流源的电路"""
        circuit = Circuit("Current Source")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        circuit.set_ground(n0)

        circuit.add_current_source("I1", n0, n1, 0.01)
        circuit.add_resistor("R1", n1, n0, 1000)

        analyzer = DCAnalyzer(circuit)
        result = analyzer.solve()

        # V = IR = 0.01 * 1000 = 10V
        assert abs(result.node_voltages[n1] - 10) < 1e-6

    def test_no_ground_error(self):
        """测试未设置接地点时报错"""
        circuit = Circuit()
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        circuit.add_voltage_source("V1", n1, n0, 10)
        circuit.add_resistor("R1", n1, n0, 1000)

        analyzer = DCAnalyzer(circuit)
        with pytest.raises(ValueError):
            analyzer.solve()

    def test_kcl_verification(self):
        """测试KCL验证"""
        circuit = Circuit("KCL Test")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        circuit.set_ground(n0)

        circuit.add_voltage_source("V1", n1, n0, 10)
        circuit.add_resistor("R1", n1, n0, 1000)

        analyzer = DCAnalyzer(circuit)
        result = analyzer.solve()

        # KCL误差应接近0
        for nid, violation in result.kcl_violations.items():
            assert abs(violation) < 1e-6


class TestVoltageDivider:
    """分压器计算测试"""

    def test_basic_divider(self):
        assert abs(voltage_divider(10, 1000, 1000) - 5) < 1e-10
        assert abs(voltage_divider(12, 1000, 2000) - 8) < 1e-10

    def test_zero_resistance(self):
        with pytest.raises(ZeroDivisionError):
            voltage_divider(10, 0, 0)


class TestCurrentDivider:
    """分流器计算测试"""

    def test_basic_divider(self):
        i1, i2 = current_divider(0.01, 1000, 1000)
        assert abs(i1 - 0.005) < 1e-10
        assert abs(i2 - 0.005) < 1e-10

    def test_unequal_resistors(self):
        i1, i2 = current_divider(0.01, 1000, 2000)
        assert abs(i1 - 0.01 * 2000/3000) < 1e-10
        assert abs(i2 - 0.01 * 1000/3000) < 1e-10


class TestSeriesResistance:
    """串联电阻测试"""

    def test_two_resistors(self):
        assert series_resistance(1000, 2000) == 3000

    def test_multiple_resistors(self):
        assert series_resistance(100, 200, 300, 400) == 1000


class TestParallelResistance:
    """并联电阻测试"""

    def test_two_equal_resistors(self):
        assert abs(parallel_resistance(1000, 1000) - 500) < 1e-10

    def test_two_unequal_resistors(self):
        expected = 1.0 / (1/1000 + 1/2000)
        assert abs(parallel_resistance(1000, 2000) - expected) < 1e-10

    def test_zero_resistance(self):
        assert parallel_resistance(1000, 0) == 0
