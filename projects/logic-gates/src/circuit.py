# 电路实现

"""
电路模块

本模块实现了电路类，用于组合多个逻辑门并模拟电路运行。
"""

from collections import defaultdict
from itertools import product
from typing import Dict, List, Optional, Set, Tuple

from .signal import Signal
from .gates import Gate
from .exceptions import CircuitError, ConnectionError, InvalidInputError


class Circuit:
    """电路类

    用于组合多个逻辑门并模拟电路运行。

    Examples:
        >>> from logic_gates import Circuit, AndGate, OrGate
        >>> circuit = Circuit("My Circuit")
        >>> and_gate = circuit.add_gate(AndGate(), "AND1")
        >>> or_gate = circuit.add_gate(OrGate(), "OR1")
        >>> circuit.connect("A", "AND1", 0)
        >>> circuit.connect("B", "AND1", 1)
        >>> circuit.set_inputs({"A": 1, "B": 1})
        >>> results = circuit.evaluate()
        >>> results["AND1"]
        1
    """

    def __init__(self, name: str = "Circuit"):
        """初始化电路

        Args:
            name: 电路名称
        """
        self.name = name
        self._gates: Dict[str, Gate] = {}
        self._connections: List[Tuple[str, str, int]] = []
        self._inputs: Dict[str, int] = {}
        self._input_gates: Set[str] = set()
        self._output_gates: Set[str] = set()
        self._gate_outputs: Dict[str, int] = {}

    def add_gate(self, gate: Gate, name: Optional[str] = None) -> str:
        """添加逻辑门到电路

        Args:
            gate: 逻辑门实例
            name: 门的名称（可选，默认使用门的类型名+序号）

        Returns:
            str: 门的名称

        Raises:
            CircuitError: 名称已存在

        Examples:
            >>> circuit = Circuit()
            >>> and_gate = AndGate()
            >>> name = circuit.add_gate(and_gate, "AND1")
            >>> name
            'AND1'
        """
        if name is None:
            name = f"{gate.name}_{len(self._gates)}"

        if name in self._gates:
            raise CircuitError(f"Gate '{name}' already exists in circuit")

        self._gates[name] = gate
        return name

    def connect(self, from_name: str, to_name: str, input_idx: int = 0):
        """连接两个逻辑门

        Args:
            from_name: 源门名称（或输入名称）
            to_name: 目标门名称
            input_idx: 目标门的输入索引

        Raises:
            CircuitError: 门不存在
            ConnectionError: 连接无效

        Examples:
            >>> circuit = Circuit()
            >>> circuit.add_gate(AndGate(), "AND1")
            >>> circuit.connect("A", "AND1", 0)  # 连接输入A到AND1的第0个输入
        """
        # 验证目标门存在
        if to_name not in self._gates:
            raise CircuitError(f"Target gate '{to_name}' not found")

        # 验证输入索引
        target_gate = self._gates[to_name]
        if input_idx >= target_gate.num_inputs:
            raise ConnectionError(
                f"Input index {input_idx} out of range for gate '{to_name}' "
                f"(max: {target_gate.num_inputs - 1})"
            )

        # 如果源是门，验证存在
        if from_name in self._gates:
            pass  # OK
        else:
            # 视为外部输入
            self._inputs.setdefault(from_name, 0)

        self._connections.append((from_name, to_name, input_idx))

    def set_input(self, name: str, value: int):
        """设置输入信号

        Args:
            name: 输入名称
            value: 信号值（0或1）

        Raises:
            InvalidInputError: 信号值无效

        Examples:
            >>> circuit = Circuit()
            >>> circuit.set_input("A", 1)
        """
        Signal.validate(value)
        self._inputs[name] = value

    def set_inputs(self, inputs: Dict[str, int]):
        """批量设置输入信号

        Args:
            inputs: 输入字典，键为名称，值为信号

        Raises:
            InvalidInputError: 信号值无效

        Examples:
            >>> circuit = Circuit()
            >>> circuit.set_inputs({"A": 1, "B": 0})
        """
        for name, value in inputs.items():
            self.set_input(name, value)

    def mark_as_input(self, gate_name: str):
        """标记门为输入门

        Args:
            gate_name: 门名称

        Raises:
            CircuitError: 门不存在

        Examples:
            >>> circuit = Circuit()
            >>> circuit.add_gate(AndGate(), "AND1")
            >>> circuit.mark_as_input("AND1")
        """
        if gate_name not in self._gates and gate_name not in self._inputs:
            raise CircuitError(f"Gate '{gate_name}' not found")
        self._input_gates.add(gate_name)

    def mark_as_output(self, gate_name: str):
        """标记门为输出门

        Args:
            gate_name: 门名称

        Raises:
            CircuitError: 门不存在

        Examples:
            >>> circuit = Circuit()
            >>> circuit.add_gate(AndGate(), "AND1")
            >>> circuit.mark_as_output("AND1")
        """
        if gate_name not in self._gates:
            raise CircuitError(f"Gate '{gate_name}' not found")
        self._output_gates.add(gate_name)

    def evaluate(self) -> Dict[str, int]:
        """计算电路输出

        Returns:
            Dict[str, int]: 所有门的输出字典

        Raises:
            CircuitError: 电路配置错误

        Examples:
            >>> circuit = Circuit()
            >>> circuit.add_gate(AndGate(), "AND1")
            >>> circuit.connect("A", "AND1", 0)
            >>> circuit.connect("B", "AND1", 1)
            >>> circuit.set_inputs({"A": 1, "B": 1})
            >>> results = circuit.evaluate()
            >>> results["AND1"]
            1
        """
        # 构建依赖图
        dependencies = self._build_dependency_graph()

        # 拓扑排序
        order = self._topological_sort(dependencies)

        # 按顺序计算
        results = {}
        for gate_name in order:
            if gate_name in self._inputs and gate_name not in self._gates:
                # 外部输入
                results[gate_name] = self._inputs[gate_name]
            elif gate_name in self._gates:
                # 逻辑门
                gate = self._gates[gate_name]
                inputs = self._get_gate_inputs(gate_name, results)
                output = gate.evaluate(*inputs)
                results[gate_name] = output
                self._gate_outputs[gate_name] = output

        return results

    def _build_dependency_graph(self) -> Dict[str, Set[str]]:
        """构建依赖图

        Returns:
            Dict[str, Set[str]]: 依赖图
        """
        deps = defaultdict(set)
        for from_name, to_name, _ in self._connections:
            deps[to_name].add(from_name)
        return deps

    def _topological_sort(self, dependencies: Dict[str, Set[str]]) -> List[str]:
        """拓扑排序

        Args:
            dependencies: 依赖图

        Returns:
            List[str]: 排序后的节点列表

        Raises:
            CircuitError: 电路包含环
        """
        visited = set()
        order = []

        def visit(node):
            if node in visited:
                return
            visited.add(node)
            for dep in dependencies.get(node, set()):
                visit(dep)
            order.append(node)

        # 收集所有节点
        all_nodes = set(self._gates.keys()) | set(self._inputs.keys())
        for _, to_name, _ in self._connections:
            all_nodes.add(to_name)

        for node in all_nodes:
            visit(node)

        return order

    def _get_gate_inputs(self, gate_name: str, results: Dict[str, int]) -> List[int]:
        """获取门的输入

        Args:
            gate_name: 门名称
            results: 已计算的结果

        Returns:
            List[int]: 输入列表
        """
        gate = self._gates[gate_name]
        inputs = [0] * gate.num_inputs

        for from_name, to_name, input_idx in self._connections:
            if to_name == gate_name:
                if from_name in results:
                    inputs[input_idx] = results[from_name]
                elif from_name in self._inputs:
                    inputs[input_idx] = self._inputs[from_name]

        return inputs

    def get_truth_table(self) -> List[Dict]:
        """生成完整真值表

        Returns:
            List[Dict]: 真值表，每个元素为一行

        Raises:
            CircuitError: 没有定义输入门

        Examples:
            >>> circuit = Circuit()
            >>> circuit.add_gate(AndGate(), "AND1")
            >>> circuit.connect("A", "AND1", 0)
            >>> circuit.connect("B", "AND1", 1)
            >>> circuit.mark_as_input("A")
            >>> circuit.mark_as_input("B")
            >>> circuit.mark_as_output("AND1")
            >>> table = circuit.get_truth_table()
            >>> len(table)
            4
        """
        # 获取所有输入
        input_names = list(self._input_gates)
        if not input_names:
            # 尝试从连接中推断输入
            input_names = list(set(self._inputs.keys()))

        if not input_names:
            raise CircuitError("No input gates defined")

        # 生成所有输入组合
        table = []
        for inputs in product([0, 1], repeat=len(input_names)):
            # 设置输入
            input_dict = dict(zip(input_names, inputs))
            self.set_inputs(input_dict)

            # 计算输出
            results = self.evaluate()

            # 收集输出
            outputs = {}
            if self._output_gates:
                for gate_name in self._output_gates:
                    outputs[gate_name] = results.get(gate_name, 0)
            else:
                # 返回所有门的输出
                outputs = {name: results.get(name, 0) for name in self._gates}

            table.append({
                "inputs": input_dict,
                "outputs": outputs
            })

        return table

    def get_gate(self, name: str) -> Optional[Gate]:
        """获取门实例

        Args:
            name: 门名称

        Returns:
            Optional[Gate]: 门实例，如果不存在返回None
        """
        return self._gates.get(name)

    def list_gates(self) -> List[str]:
        """列出所有门名称

        Returns:
            List[str]: 门名称列表
        """
        return list(self._gates.keys())

    def list_connections(self) -> List[Tuple[str, str, int]]:
        """列出所有连接

        Returns:
            List[Tuple[str, str, int]]: 连接列表
        """
        return self._connections.copy()

    def __repr__(self) -> str:
        return f"Circuit(name='{self.name}', gates={len(self._gates)})"

    def __str__(self) -> str:
        return f"Circuit '{self.name}' with {len(self._gates)} gates"
