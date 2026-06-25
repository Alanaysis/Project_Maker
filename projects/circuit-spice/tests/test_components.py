"""
电路元件测试
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.components import Resistor, Capacitor, Inductor, VoltageSource, CurrentSource


class TestResistor:
    """电阻测试"""

    def test_creation(self):
        """测试电阻创建"""
        r = Resistor("R1", 0, 1, 1000)
        assert r.name == "R1"
        assert r.node1 == 0
        assert r.node2 == 1
        assert r.resistance == 1000
        assert r.conductance == 0.001

    def test_invalid_resistance(self):
        """测试无效电阻值"""
        with pytest.raises(ValueError):
            Resistor("R1", 0, 1, -100)
        with pytest.raises(ValueError):
            Resistor("R1", 0, 1, 0)

    def test_impedance(self):
        """测试阻抗计算"""
        r = Resistor("R1", 0, 1, 1000)
        z = r.impedance(1000)
        assert z == complex(1000, 0)

    def test_dc_stamp(self):
        """测试直流印记"""
        r = Resistor("R1", 0, 1, 1000)
        G = np.zeros((2, 2))
        I = np.zeros(2)
        node_map = {1: 0, 0: 1}

        r.stamp_dc(G, I, node_map)

        # 验证电导矩阵
        assert G[0, 0] == pytest.approx(0.001)
        assert G[1, 1] == pytest.approx(0.001)
        assert G[0, 1] == pytest.approx(-0.001)
        assert G[1, 0] == pytest.approx(-0.001)


class TestCapacitor:
    """电容测试"""

    def test_creation(self):
        """测试电容创建"""
        c = Capacitor("C1", 0, 1, 1e-6)
        assert c.name == "C1"
        assert c.capacitance == 1e-6

    def test_invalid_capacitance(self):
        """测试无效电容值"""
        with pytest.raises(ValueError):
            Capacitor("C1", 0, 1, -1e-6)

    def test_impedance(self):
        """测试阻抗计算"""
        c = Capacitor("C1", 0, 1, 1e-6)
        z = c.impedance(1000)
        expected = 1.0 / (2j * np.pi * 1000 * 1e-6)
        assert abs(z - expected) < 1e-6

    def test_dc_stamp(self):
        """测试直流印记 (开路)"""
        c = Capacitor("C1", 0, 1, 1e-6)
        G = np.zeros((2, 2))
        I = np.zeros(2)
        node_map = {1: 0, 0: 1}

        c.stamp_dc(G, I, node_map)

        # 直流下电容开路
        assert np.all(G == 0)

    def test_ac_stamp(self):
        """测试交流印记"""
        c = Capacitor("C1", 0, 1, 1e-6)
        G = np.zeros((2, 2), dtype=complex)
        node_map = {1: 0, 0: 1}

        c.stamp_ac(G, 1000, node_map)

        omega = 2 * np.pi * 1000
        expected_y = 1j * omega * 1e-6
        assert G[0, 0] == pytest.approx(expected_y)
        assert G[1, 1] == pytest.approx(expected_y)
        assert G[0, 1] == pytest.approx(-expected_y)


class TestInductor:
    """电感测试"""

    def test_creation(self):
        """测试电感创建"""
        l = Inductor("L1", 0, 1, 1e-3)
        assert l.name == "L1"
        assert l.inductance == 1e-3

    def test_impedance(self):
        """测试阻抗计算"""
        l = Inductor("L1", 0, 1, 1e-3)
        z = l.impedance(1000)
        expected = 2j * np.pi * 1000 * 1e-3
        assert abs(z - expected) < 1e-6

    def test_dc_stamp(self):
        """测试直流印记 (短路)"""
        l = Inductor("L1", 0, 1, 1e-3)
        G = np.zeros((2, 2))
        I = np.zeros(2)
        node_map = {1: 0, 0: 1}

        l.stamp_dc(G, I, node_map)

        # 直流下电感短路 (大电导)
        assert G[0, 0] == pytest.approx(1e9)


class TestVoltageSource:
    """电压源测试"""

    def test_creation(self):
        """测试电压源创建"""
        v = VoltageSource("V1", 0, 1, 10)
        assert v.name == "V1"
        assert v.voltage == 10

    def test_ac_voltage(self):
        """测试交流电压源"""
        v = VoltageSource("V1", 0, 1, 0, frequency=1000, ac_mag=5)
        assert v.ac_mag == 5
        assert v.frequency == 1000

    def test_voltage_at(self):
        """测试时间相关电压"""
        v = VoltageSource("V1", 0, 1, 0, frequency=1000, ac_mag=5)
        t = 0.00025  # 1/4 周期
        expected = 5 * np.sin(2 * np.pi * 1000 * t)
        assert v.voltage_at(t) == pytest.approx(expected, rel=1e-6)

    def test_dc_voltage_at(self):
        """测试直流电压"""
        v = VoltageSource("V1", 0, 1, 10)
        assert v.voltage_at(0) == 10
        assert v.voltage_at(1) == 10


class TestCurrentSource:
    """电流源测试"""

    def test_creation(self):
        """测试电流源创建"""
        i = CurrentSource("I1", 0, 1, 0.01)
        assert i.name == "I1"
        assert i.current == 0.01

    def test_current_at(self):
        """测试时间相关电流"""
        i = CurrentSource("I1", 0, 1, 0.01, frequency=1000)
        t = 0.00025
        expected = 0.01 * np.sin(2 * np.pi * 1000 * t)
        assert i.current_at(t) == pytest.approx(expected, rel=1e-6)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
