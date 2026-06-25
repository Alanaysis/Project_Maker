"""
电路元件测试
"""

import pytest
import numpy as np
from src.components import (
    Resistor, Capacitor, Inductor, VoltageSource, CurrentSource,
    ComponentType, ohms_law, power
)


class TestResistor:
    """电阻测试"""

    def test_create_resistor(self):
        r = Resistor(name="R1", node1=0, node2=1, resistance=1000)
        assert r.name == "R1"
        assert r.resistance == 1000
        assert r.component_type == ComponentType.RESISTOR

    def test_invalid_resistance(self):
        with pytest.raises(ValueError):
            Resistor(name="R1", node1=0, node2=1, resistance=0)
        with pytest.raises(ValueError):
            Resistor(name="R1", node1=0, node2=1, resistance=-100)

    def test_impedance(self):
        r = Resistor(name="R1", node1=0, node2=1, resistance=1000)
        assert r.impedance(0) == complex(1000, 0)
        assert r.impedance(1000) == complex(1000, 0)  # 与频率无关

    def test_conductance(self):
        r = Resistor(name="R1", node1=0, node2=1, resistance=1000)
        assert r.conductance() == 0.001


class TestCapacitor:
    """电容测试"""

    def test_create_capacitor(self):
        c = Capacitor(name="C1", node1=0, node2=1, capacitance=1e-6)
        assert c.name == "C1"
        assert c.capacitance == 1e-6
        assert c.component_type == ComponentType.CAPACITOR

    def test_invalid_capacitance(self):
        with pytest.raises(ValueError):
            Capacitor(name="C1", node1=0, node2=1, capacitance=0)

    def test_impedance(self):
        c = Capacitor(name="C1", node1=0, node2=1, capacitance=1e-6)
        # Z = 1/(jωC) = -j/(2πfC)
        f = 1000
        expected = -1j / (2 * np.pi * f * 1e-6)
        z = c.impedance(f)
        assert abs(z - expected) < 1e-6

    def test_dc_open_circuit(self):
        c = Capacitor(name="C1", node1=0, node2=1, capacitance=1e-6)
        z = c.impedance(0)
        assert abs(z) == float('inf')

    def test_reactance(self):
        c = Capacitor(name="C1", node1=0, node2=1, capacitance=1e-6)
        f = 1000
        expected = -1.0 / (2 * np.pi * f * 1e-6)
        assert abs(c.reactance(f) - expected) < 1e-6


class TestInductor:
    """电感测试"""

    def test_create_inductor(self):
        l = Inductor(name="L1", node1=0, node2=1, inductance=1e-3)
        assert l.name == "L1"
        assert l.inductance == 1e-3
        assert l.component_type == ComponentType.INDUCTOR

    def test_invalid_inductance(self):
        with pytest.raises(ValueError):
            Inductor(name="L1", node1=0, node2=1, inductance=0)

    def test_impedance(self):
        l = Inductor(name="L1", node1=0, node2=1, inductance=1e-3)
        f = 1000
        expected = 1j * 2 * np.pi * f * 1e-3
        z = l.impedance(f)
        assert abs(z - expected) < 1e-6

    def test_dc_short_circuit(self):
        l = Inductor(name="L1", node1=0, node2=1, inductance=1e-3)
        z = l.impedance(0)
        assert abs(z) < 1e-10

    def test_reactance(self):
        l = Inductor(name="L1", node1=0, node2=1, inductance=1e-3)
        f = 1000
        expected = 2 * np.pi * f * 1e-3
        assert abs(l.reactance(f) - expected) < 1e-6


class TestVoltageSource:
    """电压源测试"""

    def test_dc_source(self):
        v = VoltageSource(name="V1", node1=0, node2=1, voltage=5)
        assert v.voltage == 5
        assert v.frequency == 0
        assert v.phasor() == complex(5, 0)

    def test_ac_source(self):
        v = VoltageSource(name="V1", node1=0, node2=1, voltage=10,
                         frequency=1000, phase=np.pi/4)
        phasor = v.phasor()
        assert abs(abs(phasor) - 10) < 1e-10
        assert abs(np.angle(phasor) - np.pi/4) < 1e-10

    def test_time_value(self):
        v = VoltageSource(name="V1", node1=0, node2=1, voltage=10,
                         frequency=1000, phase=0)
        t = 0.00025  # T/4
        assert abs(v.time_value(t)) < 0.01  # 接近0


class TestCurrentSource:
    """电流源测试"""

    def test_dc_source(self):
        i = CurrentSource(name="I1", node1=0, node2=1, current=0.01)
        assert i.current == 0.01
        assert i.phasor() == complex(0.01, 0)

    def test_ac_source(self):
        i = CurrentSource(name="I1", node1=0, node2=1, current=0.01,
                         frequency=1000, phase=0)
        phasor = i.phasor()
        assert abs(phasor - 0.01) < 1e-10


class TestOhmsLaw:
    """欧姆定律测试"""

    def test_voltage(self):
        result = ohms_law(current=0.01, resistance=1000)
        assert abs(result['voltage'] - 10) < 1e-10

    def test_current(self):
        result = ohms_law(voltage=10, resistance=1000)
        assert abs(result['current'] - 0.01) < 1e-10

    def test_resistance(self):
        result = ohms_law(voltage=10, current=0.01)
        assert abs(result['resistance'] - 1000) < 1e-10

    def test_insufficient_values(self):
        with pytest.raises(ValueError):
            ohms_law(voltage=10)


class TestPower:
    """功率计算测试"""

    def test_power_vi(self):
        assert abs(power(voltage=10, current=0.01) - 0.1) < 1e-10

    def test_power_i2r(self):
        assert abs(power(current=0.01, resistance=1000) - 0.1) < 1e-10

    def test_power_v2r(self):
        assert abs(power(voltage=10, resistance=1000) - 0.1) < 1e-10
