"""
连续性方程 (Continuity Equation)

连续性方程是质量守恒在流体力学中的表达：

对于不可压缩流体：
    A₁v₁ = A₂v₂ = Q = constant

其中：
    A = 截面积 (m²)
    v = 平均流速 (m/s)
    Q = 体积流量 (m³/s)

对于可压缩流体：
    ρ₁A₁v₁ = ρ₂A₂v₂ = ṁ = constant

其中 ṁ 为质量流量 (kg/s)。
"""

import numpy as np


def cross_sectional_area(diameter: float) -> float:
    """计算圆形管道截面积

    A = π(D/2)²

    Args:
        diameter: 管道直径 (m)

    Returns:
        截面积 (m²)
    """
    return np.pi * (diameter / 2)**2


def volumetric_flow_rate(area: float, velocity: float) -> float:
    """计算体积流量

    Q = A × v

    Args:
        area: 截面积 (m²)
        velocity: 流速 (m/s)

    Returns:
        体积流量 (m³/s)
    """
    return area * velocity


def average_velocity(flow_rate: float, area: float) -> float:
    """计算平均流速

    v = Q / A

    Args:
        flow_rate: 体积流量 (m³/s)
        area: 截面积 (m²)

    Returns:
        平均流速 (m/s)
    """
    if area <= 0:
        raise ValueError("截面积必须为正数")
    return flow_rate / area


def diameter_from_flow(flow_rate: float, velocity: float) -> float:
    """根据流量和流速计算所需管径

    D = √(4Q/(πv))

    Args:
        flow_rate: 体积流量 (m³/s)
        velocity: 目标流速 (m/s)

    Returns:
        所需管径 (m)
    """
    if velocity <= 0:
        raise ValueError("流速必须为正数")
    return np.sqrt(4 * flow_rate / (np.pi * velocity))


def continuity_solver(d1: float, v1: float, d2: float) -> float:
    """连续性方程求解器

    已知管道1的直径和流速，求管道2的流速

    A₁v₁ = A₂v₂
    v₂ = v₁ × (A₁/A₂) = v₁ × (D₁/D₂)²

    Args:
        d1: 管道1直径 (m)
        v1: 管道1流速 (m/s)
        d2: 管道2直径 (m)

    Returns:
        管道2流速 (m/s)
    """
    if d1 <= 0 or d2 <= 0:
        raise ValueError("直径必须为正数")
    return v1 * (d1 / d2)**2


class ContinuityAnalyzer:
    """连续性方程分析器

    用于分析管道系统中不同截面处的流速和流量关系。
    """

    def __init__(self):
        self.sections = []

    def add_section(self, diameter: float, velocity: float = None,
                    flow_rate: float = None) -> dict:
        """添加管道截面

        Args:
            diameter: 管道直径 (m)
            velocity: 流速 (m/s), 与 flow_rate 二选一
            flow_rate: 体积流量 (m³/s), 与 velocity 二选一

        Returns:
            截面信息字典
        """
        area = cross_sectional_area(diameter)

        if velocity is not None and flow_rate is not None:
            raise ValueError("velocity 和 flow_rate 只能指定一个")
        elif velocity is not None:
            flow = volumetric_flow_rate(area, velocity)
        elif flow_rate is not None:
            flow = flow_rate
            velocity = average_velocity(flow, area)
        else:
            raise ValueError("必须指定 velocity 或 flow_rate")

        section = {
            "diameter": diameter,
            "area": area,
            "velocity": velocity,
            "flow_rate": flow,
        }
        self.sections.append(section)
        return section

    def analyze(self) -> dict:
        """分析所有截面的连续性

        Returns:
            分析结果字典
        """
        if not self.sections:
            return {"error": "没有添加任何截面"}

        flow_rates = [s["flow_rate"] for s in self.sections]
        velocities = [s["velocity"] for s in self.sections]
        diameters = [s["diameter"] for s in self.sections]

        return {
            "sections": self.sections,
            "total_flow_rate": flow_rates[0],  # 对于不可压缩流体，流量守恒
            "all_flows_equal": all(abs(f - flow_rates[0]) < 1e-10 for f in flow_rates),
            "velocity_ratio": velocities[0] / velocities[-1] if velocities[-1] != 0 else float('inf'),
            "diameter_ratio": diameters[0] / diameters[-1] if diameters[-1] != 0 else float('inf'),
        }

    def find_velocity(self, target_diameter: float) -> float:
        """根据流量守恒，计算目标直径处的流速

        Args:
            target_diameter: 目标直径 (m)

        Returns:
            目标直径处的流速 (m/s)
        """
        if not self.sections:
            raise ValueError("没有添加任何截面")

        reference_flow = self.sections[0]["flow_rate"]
        target_area = cross_sectional_area(target_diameter)
        return average_velocity(reference_flow, target_area)

    def find_diameter(self, target_velocity: float) -> float:
        """根据目标流速，计算所需直径

        Args:
            target_velocity: 目标流速 (m/s)

        Returns:
            所需直径 (m)
        """
        if not self.sections:
            raise ValueError("没有添加任何截面")

        reference_flow = self.sections[0]["flow_rate"]
        return diameter_from_flow(reference_flow, target_velocity)
