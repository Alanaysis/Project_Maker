# 电路测试

"""
电路测试模块

测试电路的组合和模拟功能。
"""

import pytest
from src.circuit import Circuit
from src.gates import AndGate, OrGate, NotGate, XorGate
from src.exceptions import CircuitError, ConnectionError


class TestCircuit:
    """电路测试"""

    def setup_method(self):
        """测试前准备"""
        self.circuit = Circuit("Test Circuit")

    def test_add_gate(self):
        """测试添加门"""
        and_gate = AndGate()
        name = self.circuit.add_gate(and_gate, "AND1")
        assert name == "AND1"
        assert "AND1" in self.circuit.list_gates()

    def test_add_gate_auto_name(self):
        """测试自动命名"""
        and_gate = AndGate()
        name = self.circuit.add_gate(and_gate)
        assert name == "AND_0"

    def test_add_gate_duplicate(self):
        """测试重复添加"""
        and_gate = AndGate()
        self.circuit.add_gate(and_gate, "AND1")
        with pytest.raises(CircuitError):
            self.circuit.add_gate(and_gate, "AND1")

    def test_connect(self):
        """测试连接"""
        self.circuit.add_gate(AndGate(), "AND1")
        self.circuit.connect("A", "AND1", 0)
        self.circuit.connect("B", "AND1", 1)

    def test_connect_invalid_target(self):
        """测试无效目标"""
        with pytest.raises(CircuitError):
            self.circuit.connect("A", "INVALID", 0)

    def test_connect_invalid_index(self):
        """测试无效索引"""
        self.circuit.add_gate(AndGate(), "AND1")
        with pytest.raises(ConnectionError):
            self.circuit.connect("A", "AND1", 5)

    def test_set_input(self):
        """测试设置输入"""
        self.circuit.set_input("A", 1)
        self.circuit.set_input("B", 0)

    def test_set_input_invalid(self):
        """测试无效输入"""
        from src.exceptions import InvalidInputError
        with pytest.raises(InvalidInputError):
            self.circuit.set_input("A", 2)

    def test_set_inputs(self):
        """测试批量设置输入"""
        self.circuit.set_inputs({"A": 1, "B": 0})

    def test_evaluate_simple(self):
        """测试简单电路"""
        self.circuit.add_gate(AndGate(), "AND1")
        self.circuit.connect("A", "AND1", 0)
        self.circuit.connect("B", "AND1", 1)

        self.circuit.set_inputs({"A": 1, "B": 1})
        results = self.circuit.evaluate()
        assert results["AND1"] == 1

        self.circuit.set_inputs({"A": 0, "B": 1})
        results = self.circuit.evaluate()
        assert results["AND1"] == 0

    def test_evaluate_multi_gate(self):
        """测试多门电路"""
        self.circuit.add_gate(AndGate(), "AND1")
        self.circuit.add_gate(OrGate(), "OR1")
        self.circuit.add_gate(NotGate(), "NOT1")

        # AND1 = A AND B
        self.circuit.connect("A", "AND1", 0)
        self.circuit.connect("B", "AND1", 1)

        # OR1 = A OR B
        self.circuit.connect("A", "OR1", 0)
        self.circuit.connect("B", "OR1", 1)

        # NOT1 = NOT AND1
        self.circuit.connect("AND1", "NOT1", 0)

        # 测试 A=1, B=1
        self.circuit.set_inputs({"A": 1, "B": 1})
        results = self.circuit.evaluate()
        assert results["AND1"] == 1
        assert results["OR1"] == 1
        assert results["NOT1"] == 0

        # 测试 A=0, B=1
        self.circuit.set_inputs({"A": 0, "B": 1})
        results = self.circuit.evaluate()
        assert results["AND1"] == 0
        assert results["OR1"] == 1
        assert results["NOT1"] == 1


class TestHalfAdder:
    """半加器测试"""

    def setup_method(self):
        """创建半加器电路"""
        self.circuit = Circuit("Half Adder")

        # 添加门
        self.circuit.add_gate(XorGate(), "XOR")
        self.circuit.add_gate(AndGate(), "AND")

        # 连接
        self.circuit.connect("A", "XOR", 0)
        self.circuit.connect("B", "XOR", 1)
        self.circuit.connect("A", "AND", 0)
        self.circuit.connect("B", "AND", 1)

        # 标记输入输出
        self.circuit.mark_as_input("A")
        self.circuit.mark_as_input("B")
        self.circuit.mark_as_output("XOR")
        self.circuit.mark_as_output("AND")

    def test_00(self):
        """测试输入A=0, B=0"""
        self.circuit.set_inputs({"A": 0, "B": 0})
        results = self.circuit.evaluate()
        assert results["XOR"] == 0  # Sum
        assert results["AND"] == 0  # Carry

    def test_01(self):
        """测试输入A=0, B=1"""
        self.circuit.set_inputs({"A": 0, "B": 1})
        results = self.circuit.evaluate()
        assert results["XOR"] == 1
        assert results["AND"] == 0

    def test_10(self):
        """测试输入A=1, B=0"""
        self.circuit.set_inputs({"A": 1, "B": 0})
        results = self.circuit.evaluate()
        assert results["XOR"] == 1
        assert results["AND"] == 0

    def test_11(self):
        """测试输入A=1, B=1"""
        self.circuit.set_inputs({"A": 1, "B": 1})
        results = self.circuit.evaluate()
        assert results["XOR"] == 0
        assert results["AND"] == 1

    def test_truth_table(self):
        """测试真值表"""
        table = self.circuit.get_truth_table()
        assert len(table) == 4

        # 验证每一行
        for row in table:
            a = row["inputs"]["A"]
            b = row["inputs"]["B"]
            sum_out = row["outputs"]["XOR"]
            carry_out = row["outputs"]["AND"]

            # 验证半加器逻辑
            assert sum_out == (a ^ b)
            assert carry_out == (a & b)


class TestCircuitComponents:
    """电路组件测试"""

    def test_list_gates(self):
        """测试列出门"""
        circuit = Circuit("Test")
        circuit.add_gate(AndGate(), "AND1")
        circuit.add_gate(OrGate(), "OR1")

        gates = circuit.list_gates()
        assert "AND1" in gates
        assert "OR1" in gates

    def test_list_connections(self):
        """测试列出连接"""
        circuit = Circuit("Test")
        circuit.add_gate(AndGate(), "AND1")
        circuit.connect("A", "AND1", 0)
        circuit.connect("B", "AND1", 1)

        connections = circuit.list_connections()
        assert len(connections) == 2

    def test_get_gate(self):
        """测试获取门"""
        circuit = Circuit("Test")
        and_gate = AndGate()
        circuit.add_gate(and_gate, "AND1")

        gate = circuit.get_gate("AND1")
        assert gate is and_gate

    def test_get_gate_not_found(self):
        """测试门不存在"""
        circuit = Circuit("Test")
        gate = circuit.get_gate("INVALID")
        assert gate is None

    def test_repr(self):
        """测试repr"""
        circuit = Circuit("Test")
        assert "Test" in repr(circuit)

    def test_str(self):
        """测试str"""
        circuit = Circuit("Test")
        assert "Test" in str(circuit)
