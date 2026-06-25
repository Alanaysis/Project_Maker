"""
仿真电路模块

实现带延迟的电路仿真。
"""

from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

from ..gates import Gate
from ..exceptions import CircuitError
from .wire import Wire


class Component:
    """电路组件

    封装逻辑门，添加延迟和状态信息。
    """

    def __init__(self, gate: Gate, name: str, delay: int = 1):
        """初始化组件

        Args:
            gate: 逻辑门
            name: 组件名称
            delay: 传播延迟
        """
        self.gate = gate
        self.name = name
        self.delay = delay
        self.inputs: Dict[int, str] = {}  # input_idx -> wire_name
        self.output: Optional[str] = None
        self.output_value: int = 0
        self.last_update_time: int = 0

    def __repr__(self) -> str:
        return f"Component(name='{self.name}', gate={self.gate.name}, delay={self.delay})"


class Circuit:
    """仿真电路

    支持延迟和信号追踪的电路仿真。

    Examples:
        >>> circuit = Circuit("Test")
        >>> wire_a = circuit.add_wire("A")
        >>> wire_b = circuit.add_wire("B")
        >>> wire_out = circuit.add_wire("OUT")
        >>> and_gate = circuit.add_component(AndGate(), "AND1")
        >>> circuit.connect("A", "AND1", 0)
        >>> circuit.connect("B", "AND1", 1)
        >>> circuit.connect_output("AND1", "OUT")
        >>> circuit.set_wire("A", 1)
        >>> circuit.set_wire("B", 1)
        >>> results = circuit.simulate(10)
        >>> results["OUT"][-1]
        1
    """

    def __init__(self, name: str = "Circuit"):
        """初始化电路

        Args:
            name: 电路名称
        """
        self.name = name
        self._wires: Dict[str, Wire] = {}
        self._components: Dict[str, Component] = {}
        self._connections: List[Tuple[str, str, int]] = []  # (wire, component, input_idx)
        self._output_connections: List[Tuple[str, str]] = []  # (component, wire)

    def add_wire(self, name: str, delay: int = 0) -> Wire:
        """添加连线

        Args:
            name: 连线名称
            delay: 传播延迟

        Returns:
            Wire: 连线实例
        """
        if name in self._wires:
            raise CircuitError(f"Wire '{name}' already exists")

        wire = Wire(name, delay)
        self._wires[name] = wire
        return wire

    def add_component(self, gate: Gate, name: str, delay: int = 1) -> Component:
        """添加组件

        Args:
            gate: 逻辑门
            name: 组件名称
            delay: 传播延迟

        Returns:
            Component: 组件实例
        """
        if name in self._components:
            raise CircuitError(f"Component '{name}' already exists")

        component = Component(gate, name, delay)
        self._components[name] = component
        return component

    def connect(self, wire_name: str, component_name: str, input_idx: int):
        """连接连线到组件输入

        Args:
            wire_name: 连线名称
            component_name: 组件名称
            input_idx: 输入索引
        """
        if wire_name not in self._wires:
            raise CircuitError(f"Wire '{wire_name}' not found")
        if component_name not in self._components:
            raise CircuitError(f"Component '{component_name}' not found")

        component = self._components[component_name]
        if input_idx >= component.gate.num_inputs:
            raise CircuitError(f"Input index {input_idx} out of range")

        component.inputs[input_idx] = wire_name
        self._connections.append((wire_name, component_name, input_idx))

    def connect_output(self, component_name: str, wire_name: str):
        """连接组件输出到连线

        Args:
            component_name: 组件名称
            wire_name: 连线名称
        """
        if component_name not in self._components:
            raise CircuitError(f"Component '{component_name}' not found")
        if wire_name not in self._wires:
            raise CircuitError(f"Wire '{wire_name}' not found")

        self._components[component_name].output = wire_name
        self._output_connections.append((component_name, wire_name))

    def set_wire(self, name: str, value: int, time: int = 0):
        """设置连线值

        Args:
            name: 连线名称
            value: 信号值
            time: 时间戳
        """
        if name not in self._wires:
            raise CircuitError(f"Wire '{name}' not found")

        self._wires[name].set_value(value, time)

    def get_wire(self, name: str) -> int:
        """获取连线值

        Args:
            name: 连线名称

        Returns:
            int: 信号值
        """
        if name not in self._wires:
            raise CircuitError(f"Wire '{name}' not found")

        return self._wires[name].get_value()

    def simulate(self, num_cycles: int) -> Dict[str, List[int]]:
        """运行仿真

        Args:
            num_cycles: 仿真周期数

        Returns:
            Dict[str, List[int]]: 每个连线的信号历史
        """
        history: Dict[str, List[int]] = {name: [] for name in self._wires}

        for time in range(num_cycles):
            # 更新所有组件
            for comp_name, component in self._components.items():
                # 获取输入值
                inputs = []
                for i in range(component.gate.num_inputs):
                    wire_name = component.inputs.get(i)
                    if wire_name:
                        # 使用延迟后的值
                        wire = self._wires[wire_name]
                        inputs.append(wire.get_delayed_value(time))
                    else:
                        inputs.append(0)

                # 计算输出
                try:
                    output = component.gate.evaluate(*inputs)
                except Exception:
                    output = 0

                # 更新输出连线
                if component.output:
                    output_wire = self._wires[component.output]
                    # 延迟更新
                    delayed_time = time + component.delay
                    output_wire.set_value(output, delayed_time)

            # 记录历史
            for name, wire in self._wires.items():
                history[name].append(wire.get_value())

        return history

    def get_state(self) -> Dict[str, int]:
        """获取当前状态

        Returns:
            Dict[str, int]: 所有连线的当前值
        """
        return {name: wire.get_value() for name, wire in self._wires.items()}

    def reset(self):
        """重置电路"""
        for wire in self._wires.values():
            wire.reset()
        for component in self._components.values():
            component.output_value = 0
            component.last_update_time = 0
