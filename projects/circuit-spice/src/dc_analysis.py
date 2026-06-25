"""
直流分析模块 - DC Analysis

实现 Modified Nodal Analysis (MNA) 求解直流电路：
- 节点电压
- 支路电流
- 电压源电流
"""

import numpy as np
from typing import Dict, Optional

from .circuit import Circuit, DCOperatingPoint
from .components import VoltageSource, CurrentSource, Resistor, Capacitor, Inductor


class DCAnalysis:
    """
    直流分析器

    使用 Modified Nodal Analysis (MNA) 求解直流电路

    MNA 矩阵形式:
    [G  B] [v]   [i]
    [C  D] [j] = [e]

    其中:
    - G: 电导矩阵 (n×n)
    - B, C: 电压源连接矩阵
    - D: 通常为零矩阵
    - v: 节点电压向量
    - j: 电压源电流向量
    - i: 电流源向量
    - e: 电压源向量
    """

    def __init__(self, circuit: Circuit):
        self.circuit = circuit
        self.circuit.build_node_map()

    def solve(self) -> DCOperatingPoint:
        """
        求解直流工作点

        Returns:
            DCOperatingPoint: 直流工作点结果
        """
        n = self.circuit.num_nodes
        m = self.circuit.num_v_sources
        size = n + m

        # 初始化矩阵
        A = np.zeros((size, size), dtype=float)
        b = np.zeros(size, dtype=float)

        # 印记元件
        for comp in self.circuit.components:
            v_idx = -1
            if isinstance(comp, VoltageSource):
                v_idx = n + self.circuit.voltage_sources.index(comp)

            comp.stamp_dc(A, b, self.circuit.node_map, v_idx)

        # 求解线性方程组
        try:
            x = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            # 矩阵奇异，尝试最小二乘解
            x, residuals, rank, sv = np.linalg.lstsq(A, b, rcond=None)

        # 提取结果
        node_voltages = {self.circuit.ground_node: 0.0}
        branch_currents = {}

        for node, idx in self.circuit.node_map.items():
            node_voltages[node] = x[idx]

        for i, v_source in enumerate(self.circuit.voltage_sources):
            branch_currents[v_source.name] = x[n + i]

        # 计算电阻电流
        for comp in self.circuit.components:
            if isinstance(comp, Resistor):
                v1 = node_voltages.get(comp.node1, 0)
                v2 = node_voltages.get(comp.node2, 0)
                branch_currents[comp.name] = (v1 - v2) / comp.resistance

        return DCOperatingPoint(node_voltages, branch_currents)

    def solve_with_source_sweep(self, source_name: str, start: float, stop: float,
                                step: float) -> list:
        """
        直流扫描分析

        Args:
            source_name: 扫描的源名称
            start: 起始值
            stop: 终止值
            step: 步长

        Returns:
            list: 每个扫描点的 DCOperatingPoint
        """
        # 找到扫描源
        source = None
        for comp in self.circuit.components:
            if comp.name == source_name:
                source = comp
                break

        if source is None:
            raise ValueError(f"找不到源: {source_name}")

        original_value = source.voltage if isinstance(source, VoltageSource) else source.current
        results = []

        sweep_values = np.arange(start, stop + step / 2, step)

        for value in sweep_values:
            # 修改源值
            if isinstance(source, VoltageSource):
                source.voltage = value
            elif isinstance(source, CurrentSource):
                source.current = value

            # 求解
            result = self.solve()
            results.append((value, result))

        # 恢复原始值
        if isinstance(source, VoltageSource):
            source.voltage = original_value
        elif isinstance(source, CurrentSource):
            source.current = original_value

        return results


def voltage_divider(v_in: float, r1: float, r2: float) -> DCOperatingPoint:
    """
    分压器分析

    Args:
        v_in: 输入电压
        r1: 上臂电阻
        r2: 下臂电阻

    Returns:
        DCOperatingPoint: 直流工作点
    """
    circuit = Circuit("Voltage Divider")
    n0 = circuit.add_resistor("R1", 1, 2, r1)  # 占位
    circuit = Circuit("Voltage Divider")

    # 创建节点
    circuit.add_voltage_source("V1", 0, 1, v_in)
    circuit.add_resistor("R1", 1, 2, r1)
    circuit.add_resistor("R2", 2, 0, r2)

    circuit.build_node_map()
    analyzer = DCAnalysis(circuit)
    return analyzer.solve()


def wheatstone_bridge(v_in: float, r1: float, r2: float, r3: float, r4: float) -> DCOperatingPoint:
    """
    惠斯通电桥分析

    Args:
        v_in: 输入电压
        r1, r2, r3, r4: 电桥四个臂的电阻

    Returns:
        DCOperatingPoint: 直流工作点
    """
    circuit = Circuit("Wheatstone Bridge")

    # 节点: 0=GND, 1=VCC, 2=左中点, 3=右中点
    circuit.add_voltage_source("V1", 0, 1, v_in)
    circuit.add_resistor("R1", 1, 2, r1)
    circuit.add_resistor("R2", 2, 0, r2)
    circuit.add_resistor("R3", 1, 3, r3)
    circuit.add_resistor("R4", 3, 0, r4)

    circuit.build_node_map()
    analyzer = DCAnalysis(circuit)
    return analyzer.solve()


def thevenin_equivalent(circuit: Circuit, node_a: int, node_b: int) -> tuple:
    """
    戴维南等效电路计算

    Args:
        circuit: 电路对象
        node_a: 端口节点 a
        node_b: 端口节点 b

    Returns:
        tuple: (Vth, Rth) 戴维南电压和电阻
    """
    # 计算开路电压
    analyzer = DCAnalysis(circuit)
    result = analyzer.solve()
    v_th = result.node_voltages.get(node_a, 0) - result.node_voltages.get(node_b, 0)

    # 计算等效电阻 (通过外加测试电流源)
    # 创建副本并添加测试电流源
    test_circuit = Circuit(circuit.name + " (test)")
    test_circuit.ground_node = circuit.ground_node

    # 复制元件
    for comp in circuit.components:
        if isinstance(comp, Resistor):
            test_circuit.add_resistor(comp.name, comp.node1, comp.node2, comp.resistance)
        elif isinstance(comp, VoltageSource):
            test_circuit.add_voltage_source(comp.name, comp.node1, comp.node2, 0)  # 电压源置零

    # 添加测试电流源
    test_circuit.add_current_source("I_test", node_b, node_a, 1.0)
    test_circuit.build_node_map()

    # 求解
    test_analyzer = DCAnalysis(test_circuit)
    test_result = test_analyzer.solve()

    v_test = test_result.node_voltages.get(node_a, 0) - test_result.node_voltages.get(node_b, 0)
    r_th = v_test / 1.0  # 测试电流为 1A

    return v_th, r_th


def maximum_power_transfer(v_source: float, r_source: float, r_load_range: tuple) -> list:
    """
    最大功率传输分析

    Args:
        v_source: 源电压
        r_source: 源内阻
        r_load_range: 负载电阻范围 (start, stop, num_points)

    Returns:
        list: (R_load, P_load, efficiency) 元组列表
    """
    r_load_values = np.linspace(r_load_range[0], r_load_range[1], r_load_range[2])
    results = []

    for r_load in r_load_values:
        circuit = Circuit("Max Power Transfer")
        circuit.add_voltage_source("V1", 0, 1, v_source)
        circuit.add_resistor("R1", 1, 2, r_source)
        circuit.add_resistor("R2", 2, 0, r_load)
        circuit.build_node_map()

        analyzer = DCAnalysis(circuit)
        result = analyzer.solve()

        v_load = result.node_voltages.get(2, 0)
        i_load = result.branch_currents.get("R2", 0)
        p_load = v_load * i_load
        p_total = v_source * result.branch_currents.get("V1", 0)
        efficiency = p_load / p_total if p_total > 0 else 0

        results.append((r_load, p_load, efficiency))

    return results
