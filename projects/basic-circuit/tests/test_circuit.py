"""
电路网络测试
"""

import pytest
from src.circuit import Circuit, Node


class TestCircuit:
    """电路测试"""

    def test_create_circuit(self):
        circuit = Circuit("Test Circuit")
        assert circuit.name == "Test Circuit"
        assert len(circuit.nodes) == 0
        assert len(circuit.components) == 0

    def test_add_nodes(self):
        circuit = Circuit()
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        assert n0 == 0
        assert n1 == 1
        assert len(circuit.nodes) == 2

    def test_set_ground(self):
        circuit = Circuit()
        n0 = circuit.add_node("GND")
        circuit.set_ground(n0)
        assert circuit.get_ground() == n0
        assert circuit.nodes[n0].name == "GND"

    def test_invalid_ground(self):
        circuit = Circuit()
        with pytest.raises(ValueError):
            circuit.set_ground(99)

    def test_add_resistor(self):
        circuit = Circuit()
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        r = circuit.add_resistor("R1", n0, n1, 1000)
        assert r.name == "R1"
        assert r.resistance == 1000
        assert len(circuit.components) == 1

    def test_add_capacitor(self):
        circuit = Circuit()
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        c = circuit.add_capacitor("C1", n0, n1, 1e-6)
        assert c.name == "C1"
        assert c.capacitance == 1e-6

    def test_add_inductor(self):
        circuit = Circuit()
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        l = circuit.add_inductor("L1", n0, n1, 1e-3)
        assert l.name == "L1"
        assert l.inductance == 1e-3

    def test_add_voltage_source(self):
        circuit = Circuit()
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        v = circuit.add_voltage_source("V1", n0, n1, 5)
        assert v.voltage == 5
        assert v.frequency == 0

    def test_add_current_source(self):
        circuit = Circuit()
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        i = circuit.add_current_source("I1", n0, n1, 0.01)
        assert i.current == 0.01

    def test_invalid_node(self):
        circuit = Circuit()
        n0 = circuit.add_node("GND")
        with pytest.raises(ValueError):
            circuit.add_resistor("R1", n0, 99, 1000)

    def test_get_components_between(self):
        circuit = Circuit()
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        circuit.add_resistor("R1", n0, n1, 1000)
        circuit.add_capacitor("C1", n0, n1, 1e-6)

        comps = circuit.get_components_between(n0, n1)
        assert len(comps) == 2

    def test_get_node_components(self):
        circuit = Circuit()
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        n2 = circuit.add_node("MID")
        circuit.add_resistor("R1", n0, n1, 1000)
        circuit.add_resistor("R2", n1, n2, 2000)

        comps = circuit.get_node_components(n1)
        assert len(comps) == 2

    def test_get_resistors(self):
        circuit = Circuit()
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        circuit.add_resistor("R1", n0, n1, 1000)
        circuit.add_capacitor("C1", n0, n1, 1e-6)

        resistors = circuit.get_resistors()
        assert len(resistors) == 1
        assert resistors[0].name == "R1"

    def test_get_voltage_sources(self):
        circuit = Circuit()
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        circuit.add_voltage_source("V1", n0, n1, 5)
        circuit.add_resistor("R1", n0, n1, 1000)

        vs_list = circuit.get_voltage_sources()
        assert len(vs_list) == 1
        assert vs_list[0].name == "V1"

    def test_summary(self):
        circuit = Circuit("Test")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        circuit.set_ground(n0)
        circuit.add_resistor("R1", n0, n1, 1000)

        summary = circuit.summary()
        assert "Test" in summary
        assert "R1" in summary
        assert "GND" in summary

    def test_repr(self):
        circuit = Circuit("Test")
        n0 = circuit.add_node("GND")
        n1 = circuit.add_node("VCC")
        circuit.add_resistor("R1", n0, n1, 1000)

        assert "Test" in repr(circuit)
        assert "2 nodes" in repr(circuit)
        assert "1 components" in repr(circuit)
