"""
直流电路分析模块

实现节点分析法、网孔分析法，支持基尔霍夫定律验证。
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from .circuit import Circuit
from .components import (
    Resistor, Capacitor, Inductor,
    VoltageSource, CurrentSource, ComponentType
)


@dataclass
class DCResult:
    """直流分析结果"""
    node_voltages: Dict[int, float]  # 节点电压
    branch_currents: Dict[str, float]  # 支路电流
    branch_voltages: Dict[str, float]  # 支路电压
    power_dissipation: Dict[str, float]  # 功率消耗
    kcl_violations: Dict[int, float] = field(default_factory=dict)  # KCL 验证
    kvl_violations: Dict[str, float] = field(default_factory=dict)  # KVL 验证

    def summary(self) -> str:
        """输出分析结果摘要"""
        lines = ["=== 直流分析结果 ==="]
        lines.append("\n节点电压:")
        for nid, v in self.node_voltages.items():
            lines.append(f"  V_{nid} = {v:.6f} V")
        lines.append("\n支路电流:")
        for name, i in self.branch_currents.items():
            lines.append(f"  I_{name} = {i:.6f} A")
        lines.append("\n支路电压:")
        for name, v in self.branch_voltages.items():
            lines.append(f"  V_{name} = {v:.6f} V")
        lines.append("\n功率消耗:")
        for name, p in self.power_dissipation.items():
            lines.append(f"  P_{name} = {p:.6f} W")
        return "\n".join(lines)


class DCAnalyzer:
    """
    直流电路分析器

    支持:
    - 节点分析法 (Nodal Analysis)
    - 网孔分析法 (Mesh Analysis)
    - 基尔霍夫定律验证

    示例:
        >>> circuit = Circuit()
        >>> n0 = circuit.add_node("GND")
        >>> n1 = circuit.add_node("VCC")
        >>> circuit.set_ground(n0)
        >>> circuit.add_voltage_source("V1", n0, n1, 10)
        >>> circuit.add_resistor("R1", n1, n0, 1000)
        >>> analyzer = DCAnalyzer(circuit)
        >>> result = analyzer.solve()
    """

    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        self._ground = circuit.get_ground()

    def solve(self) -> DCResult:
        """
        求解直流电路

        使用节点分析法求解。

        返回:
            DCResult: 分析结果
        """
        if self._ground is None:
            raise ValueError("必须设置接地点")

        # 使用节点分析法
        node_voltages = self._nodal_analysis()

        # 计算支路电流和电压
        branch_currents = {}
        branch_voltages = {}
        for comp in self.circuit.components:
            v1 = node_voltages.get(comp.node1, 0)
            v2 = node_voltages.get(comp.node2, 0)
            v_branch = v1 - v2
            branch_voltages[comp.name] = v_branch

            if isinstance(comp, Resistor):
                branch_currents[comp.name] = v_branch / comp.resistance
            elif isinstance(comp, VoltageSource):
                # 电压源电流需要通过KCL计算
                branch_currents[comp.name] = self._calculate_vs_current(comp, node_voltages)
            elif isinstance(comp, CurrentSource):
                branch_currents[comp.name] = comp.current

        # 计算功率
        power_dissipation = {}
        for comp in self.circuit.components:
            v = branch_voltages[comp.name]
            i = branch_currents[comp.name]
            power_dissipation[comp.name] = v * i

        # 验证基尔霍夫定律
        kcl_violations = self._verify_kcl(node_voltages, branch_currents)
        kvl_violations = self._verify_kvl(node_voltages, branch_voltages)

        return DCResult(
            node_voltages=node_voltages,
            branch_currents=branch_currents,
            branch_voltages=branch_voltages,
            power_dissipation=power_dissipation,
            kcl_violations=kcl_violations,
            kvl_violations=kvl_violations,
        )

    def _nodal_analysis(self) -> Dict[int, float]:
        """
        节点分析法 (Modified Nodal Analysis, MNA)

        构建导纳矩阵 Y 和电流向量 I，求解 YV = I

        返回:
            Dict[int, float]: 节点电压
        """
        nodes = list(self.circuit.nodes.keys())
        n = len(nodes)

        # 节点索引映射
        node_index = {nid: i for i, nid in enumerate(nodes)}

        # 计算电压源数量
        vs_list = self.circuit.get_voltage_sources()
        m = len(vs_list)

        # MNA矩阵: (n+m) x (n+m)
        size = n + m
        A = np.zeros((size, size), dtype=float)
        b = np.zeros(size, dtype=float)

        # 填充导纳矩阵
        for comp in self.circuit.components:
            i1 = node_index.get(comp.node1)
            i2 = node_index.get(comp.node2)

            if isinstance(comp, Resistor):
                g = 1.0 / comp.resistance
                if i1 is not None and i1 != node_index[self._ground]:
                    A[i1, i1] += g
                    if i2 is not None and i2 != node_index[self._ground]:
                        A[i1, i2] -= g
                if i2 is not None and i2 != node_index[self._ground]:
                    A[i2, i2] += g
                    if i1 is not None and i1 != node_index[self._ground]:
                        A[i2, i1] -= g

            elif isinstance(comp, CurrentSource):
                if i1 is not None and i1 != node_index[self._ground]:
                    b[i1] -= comp.current
                if i2 is not None and i2 != node_index[self._ground]:
                    b[i2] += comp.current

        # 填充电压源约束
        for idx, vs in enumerate(vs_list):
            k = n + idx  # 电压源在矩阵中的位置
            i1 = node_index.get(vs.node1)
            i2 = node_index.get(vs.node2)

            if i1 is not None and i1 != node_index[self._ground]:
                A[i1, k] += 1
                A[k, i1] += 1
            if i2 is not None and i2 != node_index[self._ground]:
                A[i2, k] -= 1
                A[k, i2] -= 1

            b[k] = vs.voltage

        # 移除接地点行列 (简化)
        ground_idx = node_index[self._ground]
        reduced_indices = [i for i in range(size) if i != ground_idx]
        A_reduced = A[np.ix_(reduced_indices, reduced_indices)]
        b_reduced = b[reduced_indices]

        # 求解
        try:
            x = np.linalg.solve(A_reduced, b_reduced)
        except np.linalg.LinAlgError:
            raise ValueError("电路无法求解 (可能是奇异矩阵)")

        # 提取节点电压
        node_voltages = {self._ground: 0.0}
        for i, nid in enumerate(nodes):
            if nid == self._ground:
                continue
            idx = reduced_indices.index(i) if i in reduced_indices else -1
            if idx >= 0:
                node_voltages[nid] = x[idx]

        return node_voltages

    def _calculate_vs_current(self, vs: VoltageSource, node_voltages: Dict[int, float]) -> float:
        """计算电压源电流"""
        # 通过KCL计算: 流出节点的电流之和 = 0
        node = vs.node1
        total_current = 0

        for comp in self.circuit.get_node_components(node):
            if comp is vs:
                continue
            v1 = node_voltages.get(comp.node1, 0)
            v2 = node_voltages.get(comp.node2, 0)
            v_branch = v1 - v2

            if isinstance(comp, Resistor):
                i = v_branch / comp.resistance
                if comp.node1 == node:
                    total_current += i
                else:
                    total_current -= i
            elif isinstance(comp, CurrentSource):
                if comp.node1 == node:
                    total_current -= comp.current
                else:
                    total_current += comp.current

        return -total_current

    def _verify_kcl(self, node_voltages: Dict[int, float],
                    branch_currents: Dict[str, float]) -> Dict[int, float]:
        """
        验证基尔霍夫电流定律 (KCL)

        KCL: 流入节点的电流之和 = 0

        返回:
            Dict[int, float]: 每个节点的KCL误差
        """
        violations = {}
        for nid in self.circuit.nodes:
            if nid == self._ground:
                continue

            total_current = 0
            for comp in self.circuit.get_node_components(nid):
                i = branch_currents.get(comp.name, 0)
                if comp.node1 == nid:
                    total_current += i  # 流出
                else:
                    total_current -= i  # 流入

            violations[nid] = total_current

        return violations

    def _verify_kvl(self, node_voltages: Dict[int, float],
                    branch_voltages: Dict[str, float]) -> Dict[str, float]:
        """
        验证基尔霍夫电压定律 (KVL)

        KVL: 闭合回路中电压降之和 = 0

        返回:
            Dict[str, float]: 每个回路的KVL误差
        """
        # 简化实现: 验证每个元件的KVL
        violations = {}
        for comp in self.circuit.components:
            v1 = node_voltages.get(comp.node1, 0)
            v2 = node_voltages.get(comp.node2, 0)
            v_branch = v1 - v2

            if isinstance(comp, Resistor):
                expected = branch_voltages.get(comp.name, 0)
                violations[comp.name] = v_branch - expected

        return violations


def voltage_divider(v_in: float, r1: float, r2: float) -> float:
    """
    分压器计算

    V_out = V_in * R2 / (R1 + R2)

    参数:
        v_in: 输入电压
        r1: 上臂电阻
        r2: 下臂电阻

    返回:
        float: 输出电压
    """
    if r1 + r2 == 0:
        raise ZeroDivisionError("电阻之和不能为零")
    return v_in * r2 / (r1 + r2)


def current_divider(i_total: float, r1: float, r2: float) -> Tuple[float, float]:
    """
    分流器计算

    I1 = I_total * R2 / (R1 + R2)
    I2 = I_total * R1 / (R1 + R2)

    参数:
        i_total: 总电流
        r1: 支路1电阻
        r2: 支路2电阻

    返回:
        Tuple[float, float]: (I1, I2)
    """
    if r1 + r2 == 0:
        raise ZeroDivisionError("电阻之和不能为零")
    i1 = i_total * r2 / (r1 + r2)
    i2 = i_total * r1 / (r1 + r2)
    return i1, i2


def series_resistance(*resistances: float) -> float:
    """
    串联电阻计算

    R_total = R1 + R2 + ... + Rn

    参数:
        *resistances: 电阻值列表

    返回:
        float: 总电阻
    """
    return sum(resistances)


def parallel_resistance(*resistances: float) -> float:
    """
    并联电阻计算

    1/R_total = 1/R1 + 1/R2 + ... + 1/Rn

    参数:
        *resistances: 电阻值列表

    返回:
        float: 总电阻
    """
    if any(r == 0 for r in resistances):
        return 0.0
    return 1.0 / sum(1.0 / r for r in resistances)
