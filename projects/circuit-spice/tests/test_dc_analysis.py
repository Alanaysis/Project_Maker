"""
直流分析测试
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.circuit import Circuit
from src.dc_analysis import DCAnalysis, voltage_divider, wheatstone_bridge, thevenin_equivalent


class TestDCAnalysis:
    """直流分析测试"""

    def test_voltage_divider(self):
        """测试分压器"""
        circuit = Circuit("Voltage Divider")
        circuit.add_voltage_source("V1", 0, 1, 12)
        circuit.add_resistor("R1", 1, 2, 1000)
        circuit.add_resistor("R2", 2, 0, 2000)
        circuit.build_node_map()

        analyzer = DCAnalysis(circuit)
        result = analyzer.solve()

        # 验证节点电压
        assert result.node_voltages[1] == pytest.approx(12.0)
        assert result.node_voltages[2] == pytest.approx(8.0)  # 12 * 2000/3000
        assert result.node_voltages[0] == pytest.approx(0.0)

        # 验证支路电流
        expected_current = 12.0 / 3000  # 4mA
        assert result.branch_currents['R1'] == pytest.approx(expected_current)
        assert result.branch_currents['R2'] == pytest.approx(expected_current)

    def test_series_resistors(self):
        """测试串联电阻"""
        circuit = Circuit("Series Resistors")
        circuit.add_voltage_source("V1", 0, 1, 10)
        circuit.add_resistor("R1", 1, 2, 1000)
        circuit.add_resistor("R2", 2, 3, 2000)
        circuit.add_resistor("R3", 3, 0, 3000)
        circuit.build_node_map()

        analyzer = DCAnalysis(circuit)
        result = analyzer.solve()

        # 总电阻 = 1000 + 2000 + 3000 = 6000
        expected_current = 10.0 / 6000

        assert result.node_voltages[1] == pytest.approx(10.0)
        assert result.node_voltages[2] == pytest.approx(10.0 - 1000 * expected_current)
        assert result.node_voltages[3] == pytest.approx(3000 * expected_current)

    def test_parallel_resistors(self):
        """测试并联电阻"""
        circuit = Circuit("Parallel Resistors")
        circuit.add_voltage_source("V1", 0, 1, 10)
        circuit.add_resistor("R1", 1, 0, 1000)
        circuit.add_resistor("R2", 1, 0, 2000)
        circuit.build_node_map()

        analyzer = DCAnalysis(circuit)
        result = analyzer.solve()

        # 并联电阻: 1/R = 1/1000 + 1/2000 = 3/2000
        # R_eq = 2000/3 ≈ 666.67
        # 总电流 = 10 / (2000/3) = 15mA
        expected_total_current = 10.0 / (2000.0 / 3.0)
        expected_i_r1 = 10.0 / 1000
        expected_i_r2 = 10.0 / 2000

        assert result.node_voltages[1] == pytest.approx(10.0)
        assert result.branch_currents['R1'] == pytest.approx(expected_i_r1)
        assert result.branch_currents['R2'] == pytest.approx(expected_i_r2)

    def test_wheatstone_bridge(self):
        """测试惠斯通电桥"""
        v_in = 10
        r1, r2, r3, r4 = 1000, 2000, 1000, 2000

        result = wheatstone_bridge(v_in, r1, r2, r3, r4)

        # 平衡电桥: R1/R2 = R3/R4
        # 1000/2000 = 1000/2000 -> 平衡
        # 中点电压应相等
        v2 = result.node_voltages[2]  # 左中点
        v3 = result.node_voltages[3]  # 右中点

        assert v2 == pytest.approx(v3, abs=1e-10)

    def test_unbalanced_bridge(self):
        """测试非平衡电桥"""
        v_in = 10
        r1, r2, r3, r4 = 1000, 2000, 3000, 4000

        result = wheatstone_bridge(v_in, r1, r2, r3, r4)

        # 非平衡电桥
        v2 = result.node_voltages[2]  # 左中点
        v3 = result.node_voltages[3]  # 右中点

        # R1/R2 ≠ R3/R4, 所以 v2 ≠ v3
        assert abs(v2 - v3) > 0.01

    def test_voltage_divider_function(self):
        """测试分压器函数"""
        result = voltage_divider(12, 1000, 2000)

        assert result.node_voltages[1] == pytest.approx(12.0)
        assert result.node_voltages[2] == pytest.approx(8.0)

    def test_dc_source_sweep(self):
        """测试 DC 扫描"""
        circuit = Circuit("DC Sweep")
        circuit.add_voltage_source("V1", 0, 1, 0)
        circuit.add_resistor("R1", 1, 0, 1000)
        circuit.build_node_map()

        analyzer = DCAnalysis(circuit)
        results = analyzer.solve_with_source_sweep("V1", 0, 10, 1)

        assert len(results) == 11

        for i, (voltage, result) in enumerate(results):
            assert result.node_voltages[1] == pytest.approx(voltage)

    def test_current_source(self):
        """测试电流源"""
        circuit = Circuit("Current Source")
        circuit.add_current_source("I1", 0, 1, 0.01)
        circuit.add_resistor("R1", 1, 0, 1000)
        circuit.build_node_map()

        analyzer = DCAnalysis(circuit)
        result = analyzer.solve()

        # I * R = 0.01 * 1000 = 10V
        assert result.node_voltages[1] == pytest.approx(10.0)

    def test_multiple_sources(self):
        """测试多个源"""
        circuit = Circuit("Multiple Sources")
        circuit.add_voltage_source("V1", 0, 1, 10)
        circuit.add_voltage_source("V2", 0, 2, 5)
        circuit.add_resistor("R1", 1, 2, 1000)
        circuit.build_node_map()

        analyzer = DCAnalysis(circuit)
        result = analyzer.solve()

        # V1 - V2 = 10 - 5 = 5V across R1
        # I = 5V / 1000 = 5mA
        expected_current = 5.0 / 1000
        assert result.branch_currents['R1'] == pytest.approx(expected_current)


class TestTheveninEquivalent:
    """戴维南等效测试"""

    def test_simple_thevenin(self):
        """测试简单戴维南等效"""
        circuit = Circuit("Thevenin Test")
        circuit.add_voltage_source("V1", 0, 1, 12)
        circuit.add_resistor("R1", 1, 2, 1000)
        circuit.add_resistor("R2", 2, 0, 2000)
        circuit.build_node_map()

        v_th, r_th = thevenin_equivalent(circuit, 2, 0)

        # 戴维南电压 = 分压器输出 = 8V
        assert v_th == pytest.approx(8.0, abs=0.1)

        # 戴维南电阻 = R1 || R2 = 1000 || 2000 = 666.67
        assert r_th == pytest.approx(666.67, abs=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
