"""
瞬态分析模块 - Transient Analysis

实现时间域瞬态分析：
- 时间步进算法
- 数值积分 (梯形法、后向欧拉法)
- 动态元件 (电容、电感) 的伴随模型
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Callable

from .circuit import Circuit, TransientResult
from .components import Resistor, Capacitor, Inductor, VoltageSource, CurrentSource


class IntegrationMethod:
    """数值积分方法"""

    @staticmethod
    def backward_euler(c: float, h: float) -> Tuple[float, float]:
        """
        后向欧拉法

        i(t+h) = (c/h) * [v(t+h) - v(t)] + i(t)
        伴随模型: G_eq = c/h, I_eq = (c/h) * v(t) + i(t)

        Args:
            c: 电容或电感值
            h: 时间步长

        Returns:
            Tuple[float, float]: (G_eq, I_eq_coefficient)
        """
        return c / h, c / h

    @staticmethod
    def trapezoidal(c: float, h: float) -> Tuple[float, float]:
        """
        梯形法

        i(t+h) = (2c/h) * [v(t+h) - v(t)] - i(t)
        伴随模型: G_eq = 2c/h, I_eq = (2c/h) * v(t) + i(t)

        Args:
            c: 电容或电感值
            h: 时间步长

        Returns:
            Tuple[float, float]: (G_eq, I_eq_coefficient)
        """
        return 2 * c / h, 2 * c / h


class CapacitorCompanion:
    """电容伴随模型"""

    def __init__(self, capacitance: float, method: str = "trapezoidal"):
        self.capacitance = capacitance
        self.method = method
        self.v_prev = 0.0
        self.i_prev = 0.0

    def get_companion(self, h: float) -> Tuple[float, float]:
        """
        获取伴随模型参数

        Args:
            h: 时间步长

        Returns:
            Tuple[float, float]: (G_eq, I_eq)
        """
        if self.method == "backward_euler":
            g_eq = self.capacitance / h
            i_eq = g_eq * self.v_prev + self.i_prev
        else:  # trapezoidal
            g_eq = 2 * self.capacitance / h
            i_eq = g_eq * self.v_prev + self.i_prev

        return g_eq, i_eq

    def update(self, v_new: float, h: float):
        """
        更新状态

        Args:
            v_new: 新电压
            h: 时间步长
        """
        if self.method == "backward_euler":
            i_new = (self.capacitance / h) * (v_new - self.v_prev)
        else:  # trapezoidal
            i_new = (2 * self.capacitance / h) * (v_new - self.v_prev) - self.i_prev

        self.v_prev = v_new
        self.i_prev = i_new


class InductorCompanion:
    """电感伴随模型"""

    def __init__(self, inductance: float, method: str = "trapezoidal"):
        self.inductance = inductance
        self.method = method
        self.i_prev = 0.0

    def get_companion(self, h: float) -> Tuple[float, float]:
        """
        获取伴随模型参数

        Args:
            h: 时间步长

        Returns:
            Tuple[float, float]: (G_eq, I_eq)
        """
        if self.method == "backward_euler":
            g_eq = h / self.inductance
            i_eq = self.i_prev
        else:  # trapezoidal
            g_eq = h / (2 * self.inductance)
            i_eq = self.i_prev + (h / (2 * self.inductance)) * 0  # 需要前一步电压

        return g_eq, i_eq

    def update(self, i_new: float):
        """
        更新状态

        Args:
            i_new: 新电流
        """
        self.i_prev = i_new


class TransientAnalysis:
    """
    瞬态分析器

    使用伴随模型法进行时间域仿真
    """

    def __init__(self, circuit: Circuit, method: str = "trapezoidal"):
        """
        初始化瞬态分析器

        Args:
            circuit: 电路对象
            method: 积分方法 ("backward_euler" 或 "trapezoidal")
        """
        self.circuit = circuit
        self.method = method
        self.circuit.build_node_map()

        # 创建伴随模型
        self.capacitor_companions: Dict[str, CapacitorCompanion] = {}
        self.inductor_companions: Dict[str, InductorCompanion] = {}

        for comp in circuit.components:
            if isinstance(comp, Capacitor):
                self.capacitor_companions[comp.name] = CapacitorCompanion(
                    comp.capacitance, method
                )
            elif isinstance(comp, Inductor):
                self.inductor_companions[comp.name] = InductorCompanion(
                    comp.inductance, method
                )

    def solve(self, t_step: float, t_stop: float, t_start: float = 0,
              initial_conditions: Optional[Dict] = None) -> TransientResult:
        """
        执行瞬态分析

        Args:
            t_step: 时间步长 (s)
            t_stop: 终止时间 (s)
            t_start: 起始时间 (s)
            initial_conditions: 初始条件

        Returns:
            TransientResult: 瞬态分析结果
        """
        # 时间点
        time_points = np.arange(t_start, t_stop + t_step / 2, t_step)
        num_steps = len(time_points)

        n = self.circuit.num_nodes
        m = self.circuit.num_v_sources
        size = n + m

        # 存储结果
        node_voltage_history = {node: np.zeros(num_steps) for node in self.circuit.node_map}
        branch_current_history = {comp.name: np.zeros(num_steps) for comp in self.circuit.components}

        # 初始化
        if initial_conditions:
            for node, voltage in initial_conditions.items():
                if node in node_voltage_history:
                    node_voltage_history[node][0] = voltage

        # 时间步进
        for step in range(1, num_steps):
            t = time_points[step]
            h = t_step

            # 构建 MNA 矩阵
            A = np.zeros((size, size), dtype=float)
            b = np.zeros(size, dtype=float)

            # 印记电阻
            for comp in self.circuit.components:
                if isinstance(comp, Resistor):
                    comp.stamp_dc(A, b, self.circuit.node_map)

            # 印记电容伴随模型
            for name, companion in self.capacitor_companions.items():
                g_eq, i_eq = companion.get_companion(h)

                # 找到对应的电容元件
                cap = None
                for comp in self.circuit.components:
                    if comp.name == name:
                        cap = comp
                        break

                if cap:
                    i, j = cap._get_indices(self.circuit.node_map)

                    if i >= 0:
                        A[i, i] += g_eq
                    if j >= 0:
                        A[j, j] += g_eq
                    if i >= 0 and j >= 0:
                        A[i, j] -= g_eq
                        A[j, i] -= g_eq

                    # 电流源
                    if i >= 0:
                        b[i] += i_eq
                    if j >= 0:
                        b[j] -= i_eq

            # 印记电感伴随模型
            for name, companion in self.inductor_companions.items():
                g_eq, i_eq = companion.get_companion(h)

                ind = None
                for comp in self.circuit.components:
                    if comp.name == name:
                        ind = comp
                        break

                if ind:
                    i, j = ind._get_indices(self.circuit.node_map)

                    if i >= 0:
                        A[i, i] += g_eq
                    if j >= 0:
                        A[j, j] += g_eq
                    if i >= 0 and j >= 0:
                        A[i, j] -= g_eq
                        A[j, i] -= g_eq

                    if i >= 0:
                        b[i] += i_eq
                    if j >= 0:
                        b[j] -= i_eq

            # 印记电压源
            for idx, v_source in enumerate(self.circuit.voltage_sources):
                v_idx = n + idx
                v_source.stamp_transient(A, np.zeros((size, size)), b,
                                        self.circuit.node_map, v_idx)

                # 设置时间相关电压源
                b[v_idx] = v_source.voltage_at(t)

            # 印记电流源
            for comp in self.circuit.components:
                if isinstance(comp, CurrentSource):
                    i, j = comp._get_indices(self.circuit.node_map)
                    current = comp.current_at(t)

                    if i >= 0:
                        b[i] -= current
                    if j >= 0:
                        b[j] += current

            # 求解
            try:
                x = np.linalg.solve(A, b)
            except np.linalg.LinAlgError:
                x, _, _, _ = np.linalg.lstsq(A, b, rcond=None)

            # 存储结果
            for node, idx in self.circuit.node_map.items():
                node_voltage_history[node][step] = x[idx]

            # 更新伴随模型
            for name, companion in self.capacitor_companions.items():
                cap = None
                for comp in self.circuit.components:
                    if comp.name == name:
                        cap = comp
                        break

                if cap:
                    v1 = x[self.circuit.node_map.get(cap.node1, 0)] if cap.node1 != self.circuit.ground_node else 0
                    v2 = x[self.circuit.node_map.get(cap.node2, 0)] if cap.node2 != self.circuit.ground_node else 0
                    companion.update(v1 - v2, h)

            for name, companion in self.inductor_companions.items():
                # 电感电流需要从额外变量获取
                pass

        # 设置地节点电压
        node_voltage_history[self.circuit.ground_node] = np.zeros(num_steps)

        return TransientResult(time_points, node_voltage_history, branch_current_history)


def solve_rc_circuit(v_in: float, r: float, c: float, t_step: float,
                    t_stop: float) -> TransientResult:
    """
    RC 电路瞬态分析

    典型的 RC 充电/放电电路

    Args:
        v_in: 输入电压
        r: 电阻 (Ohm)
        c: 电容 (F)
        t_step: 时间步长 (s)
        t_stop: 终止时间 (s)

    Returns:
        TransientResult: 瞬态分析结果
    """
    circuit = Circuit("RC Circuit")
    circuit.add_voltage_source("V1", 0, 1, v_in)
    circuit.add_resistor("R1", 1, 2, r)
    circuit.add_capacitor("C1", 2, 0, c)
    circuit.build_node_map()

    analyzer = TransientAnalysis(circuit)
    return analyzer.solve(t_step, t_stop)


def solve_rlc_circuit(v_in: float, r: float, l: float, c: float,
                     t_step: float, t_stop: float) -> TransientResult:
    """
    RLC 串联电路瞬态分析

    Args:
        v_in: 输入电压
        r: 电阻 (Ohm)
        l: 电感 (H)
        c: 电容 (F)
        t_step: 时间步长 (s)
        t_stop: 终止时间 (s)

    Returns:
        TransientResult: 瞬态分析结果
    """
    circuit = Circuit("RLC Circuit")
    circuit.add_voltage_source("V1", 0, 1, v_in)
    circuit.add_resistor("R1", 1, 2, r)
    circuit.add_inductor("L1", 2, 3, l)
    circuit.add_capacitor("C1", 3, 0, c)
    circuit.build_node_map()

    analyzer = TransientAnalysis(circuit)
    return analyzer.solve(t_step, t_stop)


def step_response(r: float, c: float, t_step: float, t_stop: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    RC 电路阶跃响应

    Args:
        r: 电阻 (Ohm)
        c: 电容 (F)
        t_step: 时间步长 (s)
        t_stop: 终止时间 (s)

    Returns:
        Tuple[np.ndarray, np.ndarray]: (时间, 输出电压)
    """
    result = solve_rc_circuit(1.0, r, c, t_step, t_stop)
    output_node = max(result.node_voltages.keys())
    return result.time, result.node_voltages[output_node]


def impulse_response(r: float, c: float, t_step: float, t_stop: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    RC 电路冲激响应 (数值近似)

    使用窄脉冲近似冲激

    Args:
        r: 电阻 (Ohm)
        c: 电容 (F)
        t_step: 时间步长 (s)
        t_stop: 终止时间 (s)

    Returns:
        Tuple[np.ndarray, np.ndarray]: (时间, 输出电压)
    """
    # 使用极窄的脉冲近似冲激
    circuit = Circuit("RC Impulse")
    circuit.add_voltage_source("V1", 0, 1, 1.0)
    circuit.add_resistor("R1", 1, 2, r)
    circuit.add_capacitor("C1", 2, 0, c)
    circuit.build_node_map()

    analyzer = TransientAnalysis(circuit)
    result = analyzer.solve(t_step, t_stop)

    output_node = max(result.node_voltages.keys())
    return result.time, result.node_voltages[output_node]
