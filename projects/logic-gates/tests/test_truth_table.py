# 真值表测试

"""
真值表测试模块

测试真值表生成功能。
"""

import pytest
from src.gates import AndGate, OrGate, NotGate, XorGate
from src.circuit import Circuit
from src.truth_table import TruthTableGenerator


class TestTruthTableGenerator:
    """真值表生成器测试"""

    def test_generate_and(self):
        """测试生成AND门真值表"""
        gate = AndGate()
        table = TruthTableGenerator.generate(gate)
        assert "AND" in table
        assert "IN0" in table
        assert "IN1" in table
        assert "OUT" in table

    def test_generate_or(self):
        """测试生成OR门真值表"""
        gate = OrGate()
        table = TruthTableGenerator.generate(gate)
        assert "OR" in table

    def test_generate_not(self):
        """测试生成NOT门真值表"""
        gate = NotGate()
        table = TruthTableGenerator.generate(gate)
        assert "NOT" in table

    def test_generate_xor(self):
        """测试生成XOR门真值表"""
        gate = XorGate()
        table = TruthTableGenerator.generate(gate)
        assert "XOR" in table

    def test_format_table(self):
        """测试格式化真值表"""
        table = [
            ([0, 0], 0),
            ([0, 1], 0),
            ([1, 0], 0),
            ([1, 1], 1),
        ]
        result = TruthTableGenerator.format_table(table, "AND")
        assert "AND" in result
        assert "0" in result
        assert "1" in result

    def test_format_empty_table(self):
        """测试格式化空表"""
        result = TruthTableGenerator.format_table([], "EMPTY")
        assert result == ""

    def test_to_dict(self):
        """测试转换为字典"""
        table = [
            ([0, 0], 0),
            ([1, 1], 1),
        ]
        result = TruthTableGenerator.to_dict(table)
        assert len(result) == 2
        assert result[0]["inputs"]["IN0"] == 0
        assert result[0]["output"] == 0
        assert result[1]["inputs"]["IN0"] == 1
        assert result[1]["output"] == 1

    def test_to_csv(self):
        """测试转换为CSV"""
        table = [
            ([0, 0], 0),
            ([1, 1], 1),
        ]
        result = TruthTableGenerator.to_csv(table, "AND")
        assert "IN0,IN1,OUT" in result
        assert "0,0,0" in result
        assert "1,1,1" in result

    def test_to_json(self):
        """测试转换为JSON"""
        table = [
            ([0, 0], 0),
            ([1, 1], 1),
        ]
        result = TruthTableGenerator.to_json(table)
        assert len(result) == 2
        assert result[0]["inputs"] == [0, 0]
        assert result[0]["output"] == 0


class TestCircuitTruthTable:
    """电路真值表测试"""

    def test_generate_circuit_table(self):
        """测试生成电路真值表"""
        circuit = Circuit("Test")
        circuit.add_gate(AndGate(), "AND1")
        circuit.connect("A", "AND1", 0)
        circuit.connect("B", "AND1", 1)
        circuit.mark_as_input("A")
        circuit.mark_as_input("B")
        circuit.mark_as_output("AND1")

        table = TruthTableGenerator.generate_circuit_table(circuit)
        assert "Test" in table
        assert "A" in table
        assert "B" in table
        assert "AND1" in table

    def test_format_circuit_table(self):
        """测试格式化电路真值表"""
        table = [
            {"inputs": {"A": 0, "B": 0}, "outputs": {"OUT": 0}},
            {"inputs": {"A": 1, "B": 1}, "outputs": {"OUT": 1}},
        ]
        result = TruthTableGenerator.format_circuit_table(table, "AND")
        assert "AND" in result
        assert "A" in result
        assert "B" in result
        assert "OUT" in result

    def test_format_empty_circuit_table(self):
        """测试格式化空电路表"""
        result = TruthTableGenerator.format_circuit_table([], "EMPTY")
        assert result == ""


class TestTruthTableAccuracy:
    """真值表准确性测试"""

    def test_and_accuracy(self):
        """测试AND门真值表准确性"""
        gate = AndGate()
        table = gate.truth_table()

        # 验证所有组合
        expected = [
            ([0, 0], 0),
            ([0, 1], 0),
            ([1, 0], 0),
            ([1, 1], 1),
        ]

        for inputs, output in expected:
            assert (inputs, output) in table

    def test_or_accuracy(self):
        """测试OR门真值表准确性"""
        gate = OrGate()
        table = gate.truth_table()

        expected = [
            ([0, 0], 0),
            ([0, 1], 1),
            ([1, 0], 1),
            ([1, 1], 1),
        ]

        for inputs, output in expected:
            assert (inputs, output) in table

    def test_not_accuracy(self):
        """测试NOT门真值表准确性"""
        gate = NotGate()
        table = gate.truth_table()

        expected = [
            ([0], 1),
            ([1], 0),
        ]

        for inputs, output in expected:
            assert (inputs, output) in table

    def test_xor_accuracy(self):
        """测试XOR门真值表准确性"""
        gate = XorGate()
        table = gate.truth_table()

        expected = [
            ([0, 0], 0),
            ([0, 1], 1),
            ([1, 0], 1),
            ([1, 1], 0),
        ]

        for inputs, output in expected:
            assert (inputs, output) in table

    def test_nand_accuracy(self):
        """测试NAND门真值表准确性"""
        from src.gates import NandGate
        gate = NandGate()
        table = gate.truth_table()

        expected = [
            ([0, 0], 1),
            ([0, 1], 1),
            ([1, 0], 1),
            ([1, 1], 0),
        ]

        for inputs, output in expected:
            assert (inputs, output) in table

    def test_nor_accuracy(self):
        """测试NOR门真值表准确性"""
        from src.gates import NorGate
        gate = NorGate()
        table = gate.truth_table()

        expected = [
            ([0, 0], 1),
            ([0, 1], 0),
            ([1, 0], 0),
            ([1, 1], 0),
        ]

        for inputs, output in expected:
            assert (inputs, output) in table
