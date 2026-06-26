"""
Module: Torque and Speed Transmission
模块: 扭矩与速度传递

This module calculates how torque and rotational speed are transmitted
through gear systems, accounting for efficiency losses.

本模块计算扭矩和转速如何通过齿轮系统传递，考虑效率损失。

Key formulas:
    - Speed: n_driven = n_driver / i
      转速: 从动轮转速 = 主动轮转速 / 传动比

    - Torque: T_driven = T_driver * i * eta
      扭矩: 从动轮扭矩 = 主动轮扭矩 * 传动比 * 效率

    - Power: P = T * omega = T * 2*pi*n/60
      功率: P = 扭矩 * 角速度

    - Where omega is angular velocity in rad/s
      其中 omega 是角速度（弧度/秒）
"""

from dataclasses import dataclass
from typing import List, Optional
import math
from .spur_gear import SpurGear
from .gear_ratio import GearRatioCalculator, GearPair


@dataclass
class RotationalState:
    """
    Represents the rotational state of a shaft or gear.

    表示轴或齿轮的旋转状态。
    """
    name: str
    speed_rpm: float  # Speed in revolutions per minute (转速，RPM)
    torque_nm: float  # Torque in Newton-meters (扭矩，N·m)
    power_w: float = 0.0  # Power in Watts (功率，W)
    angular_velocity_rads: float = 0.0  # Angular velocity in rad/s (角速度，rad/s)

    def __post_init__(self):
        """Calculate derived values."""
        # Convert RPM to rad/s: omega = 2*pi*n/60
        self.angular_velocity_rads = 2 * 3.14159265359 * self.speed_rpm / 60
        # Calculate power: P = T * omega
        self.power_w = self.torque_nm * self.angular_velocity_rads


@dataclass
class TransmissionResult:
    """
    Result of a transmission calculation.

    传动计算的结果。
    """
    input_speed_rpm: float
    output_speed_rpm: float
    input_torque_nm: float
    output_torque_nm: float
    input_power_w: float
    output_power_w: float
    overall_ratio: float
    efficiency: float
    speed_reduction: float
    torque_amplification: float

    @property
    def power_loss_w(self) -> float:
        """Power loss in watts."""
        return self.input_power_w - self.output_power_w

    @property
    def power_loss_pct(self) -> float:
        """Power loss as percentage."""
        if self.input_power_w == 0:
            return 0.0
        return (self.power_loss_w / self.input_power_w) * 100

    def summary(self) -> dict:
        """Get a summary of the transmission result."""
        return {
            "input_speed_rpm": round(self.input_speed_rpm, 2),
            "output_speed_rpm": round(self.output_speed_rpm, 2),
            "speed_ratio": round(self.speed_reduction, 4),
            "input_torque_nm": round(self.input_torque_nm, 4),
            "output_torque_nm": round(self.output_torque_nm, 4),
            "torque_amplification": round(self.torque_amplification, 4),
            "input_power_w": round(self.input_power_w, 2),
            "output_power_w": round(self.output_power_w, 2),
            "power_loss_w": round(self.power_loss_w, 2),
            "power_loss_pct": round(self.power_loss_pct, 2),
            "overall_ratio": round(self.overall_ratio, 4),
            "efficiency": round(self.efficiency * 100, 2),
        }


class TransmissionCalculator:
    """
    Calculator for torque and speed transmission through gear systems.

    齿轮系统扭矩和速度传递计算器。

    Efficiency model:
        Each gear mesh has an efficiency loss. Typical values:
        每个齿轮啮合都有效率损失。典型值：
            - Spur gears: 96-98% per mesh
            - Helical gears: 97-99% per mesh
            - Worm gears: 50-90% per mesh (depends on lead angle)
            - Bevel gears: 95-98% per mesh
    """

    # Standard mesh efficiency values
    MESH_EFFICIENCY = {
        "spur": 0.98,
        "helical": 0.985,
        "worm": 0.80,
        "bevel": 0.97,
        "rack_and_pinion": 0.97,
    }

    def __init__(self, default_mesh_type: str = "spur"):
        """
        Initialize with default mesh type.

        Args:
            default_mesh_type: Default gear mesh type efficiency
        """
        self.default_mesh_type = default_mesh_type

    def calculate_gear_pair(
        self,
        driver: SpurGear,
        driven: SpurGear,
        input_speed_rpm: float,
        input_torque_nm: float,
        mesh_type: Optional[str] = None,
    ) -> TransmissionResult:
        """
        Calculate transmission through a single gear pair.

        计算单级齿轮副的传动。

        Args:
            driver: Input gear
            driven: Output gear
            input_speed_rpm: Input shaft speed in RPM
            input_torque_nm: Input shaft torque in N·m
            mesh_type: Type of mesh for efficiency calculation

        Returns:
            TransmissionResult with calculations
        """
        if mesh_type is None:
            mesh_type = self.default_mesh_type

        # Calculate gear ratio
        ratio = driven.num_teeth / driver.num_teeth

        # Apply efficiency for this mesh
        mesh_eff = self.MESH_EFFICIENCY.get(mesh_type, 0.97)

        # Output speed (reduced by gear ratio)
        output_speed = input_speed_rpm / ratio

        # Output torque (increased by gear ratio, reduced by efficiency)
        output_torque = input_torque_nm * ratio * mesh_eff

        # Power calculation
        input_power = self._torque_to_power(input_torque_nm, input_speed_rpm)
        output_power = input_power * mesh_eff

        return TransmissionResult(
            input_speed_rpm=input_speed_rpm,
            output_speed_rpm=output_speed,
            input_torque_nm=input_torque_nm,
            output_torque_nm=output_torque,
            input_power_w=input_power,
            output_power_w=output_power,
            overall_ratio=ratio,
            efficiency=mesh_eff,
            speed_reduction=ratio,
            torque_amplification=ratio * mesh_eff,
        )

    def calculate_gear_train(
        self,
        gears: List[SpurGear],
        input_speed_rpm: float,
        input_torque_nm: float,
        mesh_type: Optional[str] = None,
    ) -> TransmissionResult:
        """
        Calculate transmission through a gear train.

        计算齿轮系的传动。

        For a train of n gears:
            i_total = (z2/z1) * (z3/z2) * ... * (zn/z(n-1))
            = zn / z1  (in simple train, idlers cancel)

        For compound train, multiply all stage ratios:
            i_total = (z2/z1) * (z4/z3) * ...
        """
        if len(gears) < 2:
            raise ValueError("Need at least 2 gears")

        if mesh_type is None:
            mesh_type = self.default_mesh_type

        mesh_eff = self.MESH_EFFICIENCY.get(mesh_type, 0.97)
        num_meshes = len(gears) - 1

        # Calculate total ratio
        total_ratio = 1.0
        cumulative_efficiency = 1.0

        for i in range(num_meshes):
            stage_ratio = gears[i + 1].num_teeth / gears[i].num_teeth
            total_ratio *= stage_ratio
            cumulative_efficiency *= mesh_eff

        # Calculate output values
        output_speed = input_speed_rpm / total_ratio
        output_torque = input_torque_nm * total_ratio * cumulative_efficiency

        input_power = self._torque_to_power(input_torque_nm, input_speed_rpm)
        output_power = input_power * cumulative_efficiency

        return TransmissionResult(
            input_speed_rpm=input_speed_rpm,
            output_speed_rpm=output_speed,
            input_torque_nm=input_torque_nm,
            output_torque_nm=output_torque,
            input_power_w=input_power,
            output_power_w=output_power,
            overall_ratio=total_ratio,
            efficiency=cumulative_efficiency,
            speed_reduction=total_ratio,
            torque_amplification=total_ratio * cumulative_efficiency,
        )

    def calculate_stage_by_stage(
        self,
        gears: List[SpurGear],
        input_speed_rpm: float,
        input_torque_nm: float,
        mesh_type: Optional[str] = None,
    ) -> List[dict]:
        """
        Calculate transmission stage by stage for detailed analysis.

        逐阶段计算传动以进行详细分析。

        Returns a list of dictionaries with per-stage results.
        """
        if mesh_type is None:
            mesh_type = self.default_mesh_type

        mesh_eff = self.MESH_EFFICIENCY.get(mesh_type, 0.97)
        results = []

        current_speed = input_speed_rpm
        current_torque = input_torque_nm
        cumulative_eff = 1.0

        for i in range(len(gears) - 1):
            stage_ratio = gears[i + 1].num_teeth / gears[i].num_teeth
            current_speed /= stage_ratio
            current_torque *= stage_ratio * mesh_eff
            cumulative_eff *= mesh_eff

            stage_power = self._torque_to_power(current_torque, current_speed)
            stage_power_in = self._torque_to_power(
                current_torque / (stage_ratio * mesh_eff),
                current_speed * stage_ratio,
            )

            results.append({
                "stage": i + 1,
                "driver": gears[i].name,
                "driver_teeth": gears[i].num_teeth,
                "driven": gears[i + 1].name,
                "driven_teeth": gears[i + 1].num_teeth,
                "stage_ratio": round(stage_ratio, 4),
                "speed_rpm": round(current_speed, 2),
                "torque_nm": round(current_torque, 4),
                "power_w": round(stage_power, 2),
                "cumulative_efficiency": round(cumulative_eff * 100, 2),
            })

        return results

    def _torque_to_power(self, torque_nm: float, speed_rpm: float) -> float:
        """Convert torque and speed to power."""
        omega = 2 * 3.14159265359 * speed_rpm / 60
        return torque_nm * omega

    @staticmethod
    def power_to_torque(power_w: float, speed_rpm: float) -> float:
        """
        Convert power and speed to torque.

        T = P / omega = P * 60 / (2 * pi * n)
        """
        omega = 2 * 3.14159265359 * speed_rpm / 60
        if omega == 0:
            return 0.0
        return power_w / omega

    @staticmethod
    def torque_to_power(torque_nm: float, speed_rpm: float) -> float:
        """Convert torque and speed to power."""
        omega = 2 * math.pi * speed_rpm / 60
        return torque_nm * omega
