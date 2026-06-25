"""
电路网络模块 - Circuit Network

电路的构建和管理，支持：
- 节点管理
- 元件添加
- 矩阵构建
- 电路验证
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import OrderedDict

from .components import Resistor, Capacitor, Inductor, VoltageSource, CurrentSource
from .netlist import NetlistData, AnalysisType


class Circuit:
    """
    电路网络类

    管理电路中的节点和元件，构建分析所需的矩阵
    """

    def __init__(self, name: str = ""):
        self.name = name
        self.nodes = set()
        self.ground_node = 0
        self.components = []
        self.voltage_sources = []
        self.node_map = {}  # 节点到矩阵索引的映射
        self.num_nodes = 0
        self.num_v_sources = 0

    def add_resistor(self, name: str, node1: int, node2: int, resistance: float) -> Resistor:
        """添加电阻"""
        r = Resistor(name, node1, node2, resistance)
        self.components.append(r)
        self._update_nodes(node1, node2)
        return r

    def add_capacitor(self, name: str, node1: int, node2: int, capacitance: float) -> Capacitor:
        """添加电容"""
        c = Capacitor(name, node1, node2, capacitance)
        self.components.append(c)
        self._update_nodes(node1, node2)
        return c

    def add_inductor(self, name: str, node1: int, node2: int, inductance: float) -> Inductor:
        """添加电感"""
        l = Inductor(name, node1, node2, inductance)
        self.components.append(l)
        self._update_nodes(node1, node2)
        return l

    def add_voltage_source(self, name: str, node1: int, node2: int, voltage: float,
                          frequency: float = 0, phase: float = 0, ac_mag: float = 0) -> VoltageSource:
        """添加电压源"""
        v = VoltageSource(name, node1, node2, voltage, frequency, phase, ac_mag)
        self.components.append(v)
        self.voltage_sources.append(v)
        self._update_nodes(node1, node2)
        return v

    def add_current_source(self, name: str, node1: int, node2: int, current: float,
                          frequency: float = 0, phase: float = 0) -> CurrentSource:
        """添加电流源"""
        i = CurrentSource(name, node1, node2, current, frequency, phase)
        self.components.append(i)
        self._update_nodes(node1, node2)
        return i

    def _update_nodes(self, *nodes):
        """更新节点集合"""
        for node in nodes:
            if node != self.ground_node:
                self.nodes.add(node)

    def set_ground(self, node: int):
        """设置地节点"""
        self.ground_node = node
        if node in self.nodes:
            self.nodes.remove(node)

    def build_node_map(self):
        """构建节点到矩阵索引的映射"""
        sorted_nodes = sorted(self.nodes)
        self.node_map = {}
        for idx, node in enumerate(sorted_nodes):
            self.node_map[node] = idx

        self.num_nodes = len(sorted_nodes)
        self.num_v_sources = len(self.voltage_sources)

        return self.node_map

    def matrix_size(self) -> int:
        """返回矩阵大小 (节点数 + 电压源数)"""
        return self.num_nodes + self.num_v_sources

    def summary(self) -> str:
        """返回电路摘要信息"""
        lines = [
            f"电路名称: {self.name}",
            f"节点数: {len(self.nodes) + 1} (含地节点 {self.ground_node})",
            f"元件数: {len(self.components)}",
            "",
            "元件列表:"
        ]

        for comp in self.components:
            if isinstance(comp, Resistor):
                lines.append(f"  {comp.name}: 节点 {comp.node1} -> {comp.node2}, {comp.resistance} Ohm")
            elif isinstance(comp, Capacitor):
                lines.append(f"  {comp.name}: 节点 {comp.node1} -> {comp.node2}, {comp.capacitance} F")
            elif isinstance(comp, Inductor):
                lines.append(f"  {comp.name}: 节点 {comp.node1} -> {comp.node2}, {comp.inductance} H")
            elif isinstance(comp, VoltageSource):
                lines.append(f"  {comp.name}: 节点 {comp.node1} -> {comp.node2}, {comp.voltage} V")
            elif isinstance(comp, CurrentSource):
                lines.append(f"  {comp.name}: 节点 {comp.node1} -> {comp.node2}, {comp.current} A")

        return '\n'.join(lines)

    @classmethod
    def from_netlist(cls, netlist_data: NetlistData) -> 'Circuit':
        """
        从网表数据创建电路

        Args:
            netlist_data: 解析后的网表数据

        Returns:
            Circuit: 电路对象
        """
        circuit = cls(netlist_data.title)
        circuit.set_ground(netlist_data.ground_node)

        for comp_data in netlist_data.components:
            comp_type = comp_data['type']
            name = comp_data['name']
            node1 = comp_data['node1']
            node2 = comp_data['node2']

            if comp_type == 'R':
                circuit.add_resistor(name, node1, node2, comp_data['value'])
            elif comp_type == 'C':
                circuit.add_capacitor(name, node1, node2, comp_data['value'])
            elif comp_type == 'L':
                circuit.add_inductor(name, node1, node2, comp_data['value'])
            elif comp_type == 'V':
                voltage = comp_data.get('value', 0)
                freq = 0
                phase = 0
                ac_mag = 0

                if 'sin' in comp_data:
                    sin = comp_data['sin']
                    voltage = sin['offset']
                    freq = sin['frequency']
                    ac_mag = sin['amplitude']
                elif 'ac' in comp_data:
                    ac_mag = comp_data.get('ac_mag', 0)
                    phase = comp_data.get('ac_phase', 0)

                circuit.add_voltage_source(name, node1, node2, voltage, freq, phase, ac_mag)
            elif comp_type == 'I':
                circuit.add_current_source(name, node1, node2, comp_data['value'])

        circuit.build_node_map()
        return circuit

    def validate(self) -> Tuple[bool, List[str]]:
        """
        验证电路的有效性

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []

        # 检查是否有元件
        if not self.components:
            errors.append("电路没有元件")

        # 检查是否有地节点
        if self.ground_node is None:
            errors.append("电路没有定义地节点")

        # 检查是否有电压源
        if not self.voltage_sources:
            # 检查是否有足够的约束
            pass

        # 检查节点连通性
        connected_nodes = set()
        for comp in self.components:
            connected_nodes.add(comp.node1)
            connected_nodes.add(comp.node2)

        if self.ground_node not in connected_nodes:
            errors.append(f"地节点 {self.ground_node} 未连接到任何元件")

        return len(errors) == 0, errors


class DCOperatingPoint:
    """直流工作点结果"""

    def __init__(self, node_voltages: Dict[int, float], branch_currents: Dict[str, float]):
        self.node_voltages = node_voltages
        self.branch_currents = branch_currents

    def __repr__(self):
        lines = ["直流工作点:"]
        lines.append("  节点电压:")
        for node, voltage in sorted(self.node_voltages.items()):
            lines.append(f"    V({node}) = {voltage:.6f} V")
        lines.append("  支路电流:")
        for name, current in self.branch_currents.items():
            lines.append(f"    I({name}) = {current:.6f} A")
        return '\n'.join(lines)


class ACSolution:
    """交流分析结果"""

    def __init__(self, frequency: float, node_voltages: Dict[int, complex]):
        self.frequency = frequency
        self.node_voltages = node_voltages

    def magnitude(self, node: int) -> float:
        """获取节点电压幅度"""
        return abs(self.node_voltages.get(node, 0))

    def phase(self, node: int) -> float:
        """获取节点电压相位 (度)"""
        v = self.node_voltages.get(node, 0)
        return np.degrees(np.angle(v))

    def db(self, node: int) -> float:
        """获取节点电压分贝值"""
        mag = self.magnitude(node)
        return 20 * np.log10(mag) if mag > 0 else float('-inf')


class FrequencyResponse:
    """频率响应结果"""

    def __init__(self, frequencies: np.ndarray, responses: List[ACSolution]):
        self.frequencies = frequencies
        self.responses = responses

    def get_magnitude(self, node: int) -> np.ndarray:
        """获取幅度响应"""
        return np.array([r.magnitude(node) for r in self.responses])

    def get_phase(self, node: int) -> np.ndarray:
        """获取相位响应"""
        return np.array([r.phase(node) for r in self.responses])

    def get_db(self, node: int) -> np.ndarray:
        """获取分贝响应"""
        return np.array([r.db(node) for r in self.responses])


class TransientResult:
    """瞬态分析结果"""

    def __init__(self, time: np.ndarray, node_voltages: Dict[int, np.ndarray],
                 branch_currents: Dict[str, np.ndarray]):
        self.time = time
        self.node_voltages = node_voltages
        self.branch_currents = branch_currents

    def voltage_at(self, node: int, time_idx: int) -> float:
        """获取指定时间点的节点电压"""
        return self.node_voltages[node][time_idx]

    def current_at(self, branch: str, time_idx: int) -> float:
        """获取指定时间点的支路电流"""
        return self.branch_currents[branch][time_idx]
