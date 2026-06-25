# 逻辑门测试

"""
逻辑门测试模块

测试所有基本逻辑门的功能。
"""

import pytest
from src.gates import (
    Gate,
    AndGate,
    OrGate,
    NotGate,
    XorGate,
    NandGate,
    NorGate,
    CustomGate,
)
from src.exceptions import InvalidInputError


class TestAndGate:
    """AND门测试"""

    def setup_method(self):
        """测试前准备"""
        self.gate = AndGate()

    def test_name(self):
        """测试门名称"""
        assert self.gate.name == "AND"

    def test_num_inputs(self):
        """测试输入数量"""
        assert self.gate.num_inputs == 2

    def test_evaluate_00(self):
        """测试输入00"""
        assert self.gate.evaluate(0, 0) == 0

    def test_evaluate_01(self):
        """测试输入01"""
        assert self.gate.evaluate(0, 1) == 0

    def test_evaluate_10(self):
        """测试输入10"""
        assert self.gate.evaluate(1, 0) == 0

    def test_evaluate_11(self):
        """测试输入11"""
        assert self.gate.evaluate(1, 1) == 1

    def test_invalid_input_count(self):
        """测试无效输入数量"""
        with pytest.raises(InvalidInputError):
            self.gate.evaluate(0)

    def test_invalid_input_value(self):
        """测试无效输入值"""
        with pytest.raises(InvalidInputError):
            self.gate.evaluate(0, 2)

    def test_callable(self):
        """测试可调用接口"""
        assert self.gate(1, 1) == 1
        assert self.gate(0, 1) == 0

    def test_truth_table(self):
        """测试真值表"""
        table = self.gate.truth_table()
        assert len(table) == 4
        assert ([0, 0], 0) in table
        assert ([0, 1], 0) in table
        assert ([1, 0], 0) in table
        assert ([1, 1], 1) in table

    def test_repr(self):
        """测试repr"""
        assert "AndGate" in repr(self.gate)

    def test_str(self):
        """测试str"""
        assert "AND" in str(self.gate)


class TestOrGate:
    """OR门测试"""

    def setup_method(self):
        """测试前准备"""
        self.gate = OrGate()

    def test_name(self):
        """测试门名称"""
        assert self.gate.name == "OR"

    def test_num_inputs(self):
        """测试输入数量"""
        assert self.gate.num_inputs == 2

    def test_evaluate_00(self):
        """测试输入00"""
        assert self.gate.evaluate(0, 0) == 0

    def test_evaluate_01(self):
        """测试输入01"""
        assert self.gate.evaluate(0, 1) == 1

    def test_evaluate_10(self):
        """测试输入10"""
        assert self.gate.evaluate(1, 0) == 1

    def test_evaluate_11(self):
        """测试输入11"""
        assert self.gate.evaluate(1, 1) == 1

    def test_truth_table(self):
        """测试真值表"""
        table = self.gate.truth_table()
        assert len(table) == 4
        assert ([0, 0], 0) in table
        assert ([1, 1], 1) in table


class TestNotGate:
    """NOT门测试"""

    def setup_method(self):
        """测试前准备"""
        self.gate = NotGate()

    def test_name(self):
        """测试门名称"""
        assert self.gate.name == "NOT"

    def test_num_inputs(self):
        """测试输入数量"""
        assert self.gate.num_inputs == 1

    def test_evaluate_0(self):
        """测试输入0"""
        assert self.gate.evaluate(0) == 1

    def test_evaluate_1(self):
        """测试输入1"""
        assert self.gate.evaluate(1) == 0

    def test_truth_table(self):
        """测试真值表"""
        table = self.gate.truth_table()
        assert len(table) == 2
        assert ([0], 1) in table
        assert ([1], 0) in table


class TestXorGate:
    """XOR门测试"""

    def setup_method(self):
        """测试前准备"""
        self.gate = XorGate()

    def test_name(self):
        """测试门名称"""
        assert self.gate.name == "XOR"

    def test_num_inputs(self):
        """测试输入数量"""
        assert self.gate.num_inputs == 2

    def test_evaluate_00(self):
        """测试输入00"""
        assert self.gate.evaluate(0, 0) == 0

    def test_evaluate_01(self):
        """测试输入01"""
        assert self.gate.evaluate(0, 1) == 1

    def test_evaluate_10(self):
        """测试输入10"""
        assert self.gate.evaluate(1, 0) == 1

    def test_evaluate_11(self):
        """测试输入11"""
        assert self.gate.evaluate(1, 1) == 0

    def test_truth_table(self):
        """测试真值表"""
        table = self.gate.truth_table()
        assert len(table) == 4
        assert ([0, 0], 0) in table
        assert ([0, 1], 1) in table
        assert ([1, 0], 1) in table
        assert ([1, 1], 0) in table


class TestNandGate:
    """NAND门测试"""

    def setup_method(self):
        """测试前准备"""
        self.gate = NandGate()

    def test_name(self):
        """测试门名称"""
        assert self.gate.name == "NAND"

    def test_num_inputs(self):
        """测试输入数量"""
        assert self.gate.num_inputs == 2

    def test_evaluate_00(self):
        """测试输入00"""
        assert self.gate.evaluate(0, 0) == 1

    def test_evaluate_01(self):
        """测试输入01"""
        assert self.gate.evaluate(0, 1) == 1

    def test_evaluate_10(self):
        """测试输入10"""
        assert self.gate.evaluate(1, 0) == 1

    def test_evaluate_11(self):
        """测试输入11"""
        assert self.gate.evaluate(1, 1) == 0

    def test_truth_table(self):
        """测试真值表"""
        table = self.gate.truth_table()
        assert len(table) == 4
        assert ([0, 0], 1) in table
        assert ([1, 1], 0) in table


class TestNorGate:
    """NOR门测试"""

    def setup_method(self):
        """测试前准备"""
        self.gate = NorGate()

    def test_name(self):
        """测试门名称"""
        assert self.gate.name == "NOR"

    def test_num_inputs(self):
        """测试输入数量"""
        assert self.gate.num_inputs == 2

    def test_evaluate_00(self):
        """测试输入00"""
        assert self.gate.evaluate(0, 0) == 1

    def test_evaluate_01(self):
        """测试输入01"""
        assert self.gate.evaluate(0, 1) == 0

    def test_evaluate_10(self):
        """测试输入10"""
        assert self.gate.evaluate(1, 0) == 0

    def test_evaluate_11(self):
        """测试输入11"""
        assert self.gate.evaluate(1, 1) == 0

    def test_truth_table(self):
        """测试真值表"""
        table = self.gate.truth_table()
        assert len(table) == 4
        assert ([0, 0], 1) in table
        assert ([1, 1], 0) in table


class TestCustomGate:
    """自定义门测试"""

    def test_custom_gate(self):
        """测试自定义门"""
        def majority(*inputs):
            return int(sum(inputs) > len(inputs) / 2)

        gate = CustomGate("MAJ", 3, majority)
        assert gate.name == "MAJ"
        assert gate.num_inputs == 3

        # 测试所有输入组合
        assert gate.evaluate(0, 0, 0) == 0
        assert gate.evaluate(0, 0, 1) == 0
        assert gate.evaluate(0, 1, 0) == 0
        assert gate.evaluate(0, 1, 1) == 1
        assert gate.evaluate(1, 0, 0) == 0
        assert gate.evaluate(1, 0, 1) == 1
        assert gate.evaluate(1, 1, 0) == 1
        assert gate.evaluate(1, 1, 1) == 1

    def test_custom_gate_invalid_output(self):
        """测试自定义门无效输出"""
        def bad_func(*inputs):
            return 2  # 无效输出

        gate = CustomGate("BAD", 2, bad_func)
        with pytest.raises(InvalidInputError):
            gate.evaluate(0, 0)

    def test_custom_gate_truth_table(self):
        """测试自定义门真值表"""
        def xor(*inputs):
            return int(sum(inputs) % 2 == 1)

        gate = CustomGate("XOR", 2, xor)
        table = gate.truth_table()
        assert len(table) == 4
