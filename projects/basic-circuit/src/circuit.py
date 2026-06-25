"""
电路网络模块

实现电路的构建、节点管理、网孔分析等功能。
"""

import numpy as np
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from .components import (
    Component, Resistor, Capacitor, Inductor,
    VoltageSource, CurrentSource, ComponentType
)


@dataclass
class Node:
    """
    电路节点

    参数:
        id: 节点编号
        name: 节点名称
        voltage: 节点电压 (分析结果)
    """
    id: int
    name: str = ""
    voltage: complex = 0.0

    def __post_init__(self):
        if not self.name:
            self.name = f"Node_{self.id}"


@dataclass
class Branch:
    """
    电路支路

    参数:
        component: 支路中的元件
        current: 支路电流 (分析结果)
    """
    component: Component
    current: complex = 0.0


class Circuit:
    """
    电路网络

    支持添加元件、构建电路、进行DC/AC分析。

    示例:
        >>> circuit = Circuit()
        >>> circuit.add_node("VCC")
        >>> circuit.add_node("GND")
        >>> circuit.add_resistor("R1", 0, 1, 1000)
        >>> circuit.add_voltage_source("V1", 0, 1, 5)
    """

    def __init__(self, name: str = "Circuit"):
        self.name = name
        self.nodes: Dict[int, Node] = {}
        self.components: List[Component] = []
        self._node_counter = 0
        self._ground_node: Optional[int] = None

    def add_node(self, name: str = "") -> int:
        """
        添加节点

        参数:
            name: 节点名称

        返回:
            int: 节点编号
        """
        node_id = self._node_counter
        self.nodes[node_id] = Node(id=node_id, name=name or f"Node_{node_id}")
        self._node_counter += 1
        return node_id

    def set_ground(self, node_id: int):
        """
        设置接地点 (参考节点)

        参数:
            node_id: 节点编号
        """
        if node_id not in self.nodes:
            raise ValueError(f"节点 {node_id} 不存在")
        self._ground_node = node_id
        self.nodes[node_id].name = "GND"

    def get_ground(self) -> Optional[int]:
        """获取接地点编号"""
        return self._ground_node

    def add_resistor(self, name: str, node1: int, node2: int, resistance: float) -> Resistor:
        """
        添加电阻

        参数:
            name: 元件名称
            node1: 节点1编号
            node2: 节点2编号
            resistance: 电阻值 (欧姆)

        返回:
            Resistor: 电阻元件
        """
        self._validate_nodes(node1, node2)
        r = Resistor(name=name, node1=node1, node2=node2, resistance=resistance)
        self.components.append(r)
        return r

    def add_capacitor(self, name: str, node1: int, node2: int, capacitance: float) -> Capacitor:
        """
        添加电容

        参数:
            name: 元件名称
            node1: 节点1编号
            node2: 节点2编号
            capacitance: 电容值 (法拉)

        返回:
            Capacitor: 电容元件
        """
        self._validate_nodes(node1, node2)
        c = Capacitor(name=name, node1=node1, node2=node2, capacitance=capacitance)
        self.components.append(c)
        return c

    def add_inductor(self, name: str, node1: int, node2: int, inductance: float) -> Inductor:
        """
        添加电感

        参数:
            name: 元件名称
            node1: 节点1编号
            node2: 节点2编号
            inductance: 电感值 (亨利)

        返回:
            Inductor: 电感元件
        """
        self._validate_nodes(node1, node2)
        l = Inductor(name=name, node1=node1, node2=node2, inductance=inductance)
        self.components.append(l)
        return l

    def add_voltage_source(self, name: str, node1: int, node2: int,
                           voltage: float, frequency: float = 0, phase: float = 0) -> VoltageSource:
        """
        添加电压源

        参数:
            name: 元件名称
            node1: 正极节点
            node2: 负极节点
            voltage: 电压值 (伏特)
            frequency: 频率 (赫兹)
            phase: 相位 (弧度)

        返回:
            VoltageSource: 电压源元件
        """
        self._validate_nodes(node1, node2)
        v = VoltageSource(name=name, node1=node1, node2=node2,
                         voltage=voltage, frequency=frequency, phase=phase)
        self.components.append(v)
        return v

    def add_current_source(self, name: str, node1: int, node2: int,
                           current: float, frequency: float = 0, phase: float = 0) -> CurrentSource:
        """
        添加电流源

        参数:
            name: 元件名称
            node1: 电流流入节点
            node2: 电流流出节点
            current: 电流值 (安培)
            frequency: 频率 (赫兹)
            phase: 相位 (弧度)

        返回:
            CurrentSource: 电流源元件
        """
        self._validate_nodes(node1, node2)
        i = CurrentSource(name=name, node1=node1, node2=node2,
                         current=current, frequency=frequency, phase=phase)
        self.components.append(i)
        return i

    def _validate_nodes(self, *node_ids):
        """验证节点是否存在"""
        for nid in node_ids:
            if nid not in self.nodes:
                raise ValueError(f"节点 {nid} 不存在")

    def get_components_between(self, node1: int, node2: int) -> List[Component]:
        """获取两个节点之间的元件"""
        result = []
        for comp in self.components:
            if (comp.node1 == node1 and comp.node2 == node2) or \
               (comp.node1 == node2 and comp.node2 == node1):
                result.append(comp)
        return result

    def get_node_components(self, node_id: int) -> List[Component]:
        """获取连接到指定节点的所有元件"""
        return [c for c in self.components if c.node1 == node_id or c.node2 == node_id]

    def get_resistors(self) -> List[Resistor]:
        """获取所有电阻"""
        return [c for c in self.components if isinstance(c, Resistor)]

    def get_capacitors(self) -> List[Capacitor]:
        """获取所有电容"""
        return [c for c in self.components if isinstance(c, Capacitor)]

    def get_inductors(self) -> List[Inductor]:
        """获取所有电感"""
        return [c for c in self.components if isinstance(c, Inductor)]

    def get_voltage_sources(self) -> List[VoltageSource]:
        """获取所有电压源"""
        return [c for c in self.components if isinstance(c, VoltageSource)]

    def get_current_sources(self) -> List[CurrentSource]:
        """获取所有电流源"""
        return [c for c in self.components if isinstance(c, CurrentSource)]

    def summary(self) -> str:
        """输出电路摘要"""
        lines = [f"电路: {self.name}"]
        lines.append(f"节点数: {len(self.nodes)}")
        lines.append(f"元件数: {len(self.components)}")
        lines.append("\n节点:")
        for nid, node in self.nodes.items():
            ground = " (GND)" if nid == self._ground_node else ""
            lines.append(f"  {node.name}{ground}")
        lines.append("\n元件:")
        for comp in self.components:
            lines.append(f"  {comp}")
        return "\n".join(lines)

    def __repr__(self):
        return f"Circuit({self.name}: {len(self.nodes)} nodes, {len(self.components)} components)"
