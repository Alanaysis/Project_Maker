"""
压力降分析 (Pressure Drop Analysis)

分析管道系统中不同因素导致的压力降。

压力降来源：
    1. 沿程摩擦损失 (Frictional Loss)
    2. 高程变化 (Elevation Change)
    3. 加速度效应 (Acceleration Effect)
    4. 局部损失 (Minor Loss)

总压力降：
    ΔP_total = ΔP_friction + ΔP_elevation + ΔP_acceleration + ΔP_minor
"""

import numpy as np
from .pipe_flow import darcy_weisbach_pressure_drop, darcy_weisbach_head_loss
from .head_loss import total_head_loss, major_loss, minor_loss
from .reynolds import reynolds_number


def elevation_pressure_change(density: float, gravity: float,
                              height_change: float) -> float:
    """计算高程变化引起的压力变化

    ΔP = ρgΔh

    当流体向上流动时，压力降低；向下流动时，压力增加。

    Args:
        density: 流体密度 (kg/m³)
        gravity: 重力加速度 (m/s²)
        height_change: 高程变化 (m), 向上为正

    Returns:
        压力变化 (Pa), 正值表示压力增加
    """
    return density * gravity * height_change


def frictional_pressure_drop(length: float, diameter: float, velocity: float,
                             reynolds: float, density: float,
                             roughness: float = 0.0,
                             gravity: float = 9.81) -> float:
    """计算摩擦引起的压力降

    使用 Darcy-Weisbach 方程：
        ΔP = f × (L/D) × (ρv²/2)

    Args:
        length: 管道长度 (m)
        diameter: 管道内径 (m)
        velocity: 流速 (m/s)
        reynolds: Reynolds 数
        density: 流体密度 (kg/m³)
        roughness: 管道粗糙度 (m)
        gravity: 重力加速度 (m/s²)

    Returns:
        摩擦压力降 (Pa)
    """
    return darcy_weisbach_pressure_drop(length, diameter, velocity,
                                        reynolds, density, roughness, gravity)


def acceleration_pressure_drop(density: float, v1: float, v2: float) -> float:
    """计算加速度引起的压力降

    ΔP = ½ρ(v₁² - v₂²)

    当流体加速时（如通过收缩段），压力降低。

    Args:
        density: 流体密度 (kg/m³)
        v1: 入口速度 (m/s)
        v2: 出口速度 (m/s)

    Returns:
        加速度压力降 (Pa)
    """
    return 0.5 * density * (v1**2 - v2**2)


def total_pressure_drop(density: float, gravity: float,
                        length: float, diameter: float, velocity: float,
                        reynolds: float, roughness: float = 0.0,
                        minor_components: list = None,
                        height_change: float = 0.0) -> dict:
    """计算总压力降

    Args:
        density: 流体密度 (kg/m³)
        gravity: 重力加速度 (m/s²)
        length: 管道长度 (m)
        diameter: 管道内径 (m)
        velocity: 流速 (m/s)
        reynolds: Reynolds 数
        roughness: 管道粗糙度 (m)
        minor_components: 局部损失组件列表
        height_change: 高程变化 (m)

    Returns:
        压力降分析结果字典
    """
    friction_drop = frictional_pressure_drop(
        length, diameter, velocity, reynolds, density, roughness, gravity
    )
    elevation_change = elevation_pressure_change(density, gravity, height_change)
    minor_result = {"total_minor_loss": 0.0}
    if minor_components:
        from .head_loss import total_minor_loss
        minor_result = total_minor_loss(velocity, minor_components, gravity)
        minor_drop = density * gravity * minor_result["total_minor_loss"]
    else:
        minor_drop = 0.0

    total = friction_drop + minor_drop + elevation_change

    return {
        "friction_drop": friction_drop,
        "minor_drop": minor_drop,
        "elevation_change": elevation_change,
        "total_drop": total,
        "inlet_pressure": 0,  # 相对压力
        "outlet_pressure": -total,  # 相对压力
        "pressure_drop_ratio": {
            "friction": friction_drop / total if total != 0 else 0,
            "minor": minor_drop / total if total != 0 else 0,
            "elevation": elevation_change / total if total != 0 else 0,
        },
    }


class PressureDropAnalyzer:
    """压力降分析器

    用于分析长管道或多段管道的压力分布。
    """

    def __init__(self, fluid_density: float = 1000.0,
                 fluid_viscosity: float = 1.002e-3,
                 gravity: float = 9.81):
        """初始化分析器

        Args:
            fluid_density: 流体密度 (kg/m³)
            fluid_viscosity: 流体动力粘度 (Pa·s)
            gravity: 重力加速度 (m/s²)
        """
        self.fluid_density = fluid_density
        self.fluid_viscosity = fluid_viscosity
        self.gravity = gravity
        self.segments = []

    def add_segment(self, length: float, diameter: float, roughness: float = 0.0,
                    elevation_change: float = 0.0) -> dict:
        """添加管道段

        Args:
            length: 管道长度 (m)
            diameter: 管道内径 (m)
            roughness: 管道粗糙度 (m)
            elevation_change: 高程变化 (m)

        Returns:
            管道段配置字典
        """
        segment = {
            "length": length,
            "diameter": diameter,
            "roughness": roughness,
            "elevation_change": elevation_change,
        }
        self.segments.append(segment)
        return segment

    def analyze(self, flow_rate: float) -> dict:
        """分析整个系统的压力分布

        Args:
            flow_rate: 体积流量 (m³/s)

        Returns:
            压力分布分析结果
        """
        if not self.segments:
            return {"error": "没有添加任何管道段"}

        pressure_profile = [{"position": 0.0, "pressure": 0.0, "elevation": 0.0}]
        cumulative_length = 0.0
        cumulative_elevation = 0.0
        current_pressure = 0.0

        for i, seg in enumerate(self.segments):
            area = np.pi * (seg["diameter"] / 2)**2
            velocity = flow_rate / area
            re = reynolds_number(velocity, seg["diameter"],
                                self.fluid_density, self.fluid_viscosity)

            friction_drop = frictional_pressure_drop(
                seg["length"], seg["diameter"], velocity, re,
                self.fluid_density, seg["roughness"], self.gravity
            )

            elevation_change = elevation_pressure_change(
                self.fluid_density, self.gravity, seg["elevation_change"]
            )

            cumulative_length += seg["length"]
            cumulative_elevation += seg["elevation_change"]
            current_pressure -= friction_drop + elevation_change

            pressure_profile.append({
                "position": cumulative_length,
                "pressure": current_pressure,
                "elevation": cumulative_elevation,
                "velocity": velocity,
                "reynolds": re,
            })

        return {
            "flow_rate": flow_rate,
            "velocity": flow_rate / (np.pi * (self.segments[0]["diameter"] / 2)**2),
            "segments": len(self.segments),
            "total_length": cumulative_length,
            "total_elevation_change": cumulative_elevation,
            "pressure_profile": pressure_profile,
            "total_pressure_drop": -current_pressure,
        }

    def find_required_pressure(self, flow_rate: float,
                               min_outlet_pressure: float = 0.0) -> float:
        """计算满足出口最小压力要求所需的入口压力

        Args:
            flow_rate: 体积流量 (m³/s)
            min_outlet_pressure: 最小出口压力 (Pa)

        Returns:
            所需入口压力 (Pa)
        """
        analysis = self.analyze(flow_rate)
        if "error" in analysis:
            raise ValueError(analysis["error"])
        return min_outlet_pressure + analysis["total_pressure_drop"]
