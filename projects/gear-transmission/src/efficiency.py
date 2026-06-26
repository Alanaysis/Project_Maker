"""
Module: Efficiency Analysis
模块: 效率分析

This module provides comprehensive efficiency analysis for gear systems,
including:
    - Mesh efficiency models
    - Power loss calculation
    - Thermal considerations
    - Efficiency comparison across configurations

本模块提供齿轮系统的全面效率分析，包括：
    - 啮合效率模型
    - 功率损失计算
    - 热力学考虑
    - 不同配置的效率对比
"""

import math
from dataclasses import dataclass
from typing import List, Dict, Optional
from .spur_gear import SpurGear


@dataclass
class EfficiencyResult:
    """Result of an efficiency analysis."""
    input_power_w: float
    output_power_w: float
    total_loss_w: float
    mesh_losses: List[dict]
    bearing_loss_w: float
    seal_loss_w: float
    windage_loss_w: float
    overall_efficiency: float
    efficiency_by_stage: List[float]

    @property
    def total_loss_pct(self) -> float:
        if self.input_power_w == 0:
            return 0.0
        return (self.total_loss_w / self.input_power_w) * 100

    def summary(self) -> dict:
        """Get efficiency analysis summary."""
        return {
            "input_power_w": round(self.input_power_w, 2),
            "output_power_w": round(self.output_power_w, 2),
            "total_loss_w": round(self.total_loss_w, 2),
            "total_loss_pct": round(self.total_loss_pct, 2),
            "overall_efficiency_pct": round(self.overall_efficiency * 100, 2),
            "bearing_loss_w": round(self.bearing_loss_w, 2),
            "seal_loss_w": round(self.seal_loss_w, 2),
            "windage_loss_w": round(self.windage_loss_w, 2),
            "efficiency_by_stage": [round(e * 100, 2) for e in self.efficiency_by_stage],
            "mesh_losses": self.mesh_losses,
        }


class EfficiencyAnalyzer:
    """
    Analyzes efficiency of gear systems.

    Efficiency factors in gear systems:
    齿轮系统中的效率因素:

    1. Mesh efficiency (啮合效率):
       - Rolling friction between teeth
       - Sliding friction between teeth
       - Gear type: spur, helical, worm, bevel

    2. Bearing losses (轴承损失):
       - Rolling element bearing friction
       - Depends on load, speed, and bearing type

    3. Seal losses (密封损失):
       - Oil seal friction
       - Depends on seal type and lubrication

    4. Windage/drag losses (风阻损失):
       - Air resistance on rotating gears
       - Depends on speed and gear geometry
    """

    # Mesh efficiency by gear type (typical values)
    MESH_EFFICIENCY = {
        "spur": 0.98,
        "helical": 0.985,
        "double_helical": 0.99,
        "bevel": 0.97,
        "hypoid": 0.95,
        "worm_single": 0.75,
        "worm_double": 0.85,
        "rack_pinion": 0.97,
        "gear_rack": 0.97,
    }

    # Worm gear efficiency depends on lead angle and friction
    WORM_FRICTION_COEFF = {
        "good_lubrication": 0.015,
        "moderate_lubrication": 0.025,
        "poor_lubrication": 0.040,
    }

    def __init__(self):
        """Initialize analyzer with default parameters."""
        self.bearing_efficiency = 0.995  # Per bearing
        self.seal_efficiency = 0.99      # Per seal pair
        self.windage_model = "standard"  # "standard" or "high_speed"

    def analyze_mesh_efficiency(
        self,
        gear_type: str = "spur",
        pitch_line_velocity: float = 0.0,
        pressure_angle_deg: float = 20.0,
        module: float = 2.0,
    ) -> float:
        """
        Calculate mesh efficiency considering operating conditions.

        根据工作条件计算啮合效率。

        Args:
            gear_type: Type of gear mesh
            pitch_line_velocity: Pitch line velocity (m/s)
            pressure_angle_deg: Pressure angle in degrees
            module: Gear module (mm)

        Returns:
            Mesh efficiency (0 to 1)
        """
        base_eff = self.MESH_EFFICIENCY.get(gear_type, 0.97)

        # Adjust for pitch line velocity
        # Higher speeds can improve lubrication but increase windage
        if pitch_line_velocity > 10:
            # High speed: slight efficiency improvement due to hydrodynamic lubrication
            velocity_factor = 1.0 + 0.001 * (pitch_line_velocity - 10)
        elif pitch_line_velocity < 0.1:
            # Very low speed: boundary lubrication, more friction
            velocity_factor = 1.0 - 0.01 * (0.1 - pitch_line_velocity)
        else:
            velocity_factor = 1.0

        # Adjust for pressure angle
        # Higher pressure angle increases normal force, slightly reducing efficiency
        pa_factor = 1.0 - 0.001 * (pressure_angle_deg - 20.0)

        efficiency = base_eff * velocity_factor * pa_factor
        return max(0.5, min(0.999, efficiency))

    def calculate_worm_gear_efficiency(
        self,
        lead_angle_deg: float,
        friction_angle_deg: float = 3.0,
        lubrication: str = "good_lubrication",
    ) -> float:
        """
        Calculate worm gear efficiency.

        计算蜗轮蜗杆效率。

        Worm gear efficiency formula:
            eta = tan(lambda) / tan(lambda + phi)

        where:
            lambda = lead angle (导程角)
            phi = friction angle (摩擦角)

        Worm gears are self-locking when lambda < phi.
        当导程角小于摩擦角时，蜗轮蜗杆自锁。

        Args:
            lead_angle_deg: Lead angle in degrees
            friction_angle_deg: Friction angle in degrees
            lubrication: Lubrication condition

        Returns:
            Efficiency (0 to 1)
        """
        if lubrication in self.WORM_FRICTION_COEFF:
            friction_coeff = self.WORM_FRICTION_COEFF[lubrication]
            friction_angle_deg = math.degrees(math.atan(friction_coeff))

        lam = math.radians(lead_angle_deg)
        phi = math.radians(friction_angle_deg)

        if lam + phi >= math.pi / 2:
            return 0.0

        numerator = math.sin(lam) * math.cos(phi)
        denominator = math.sin(lam + phi) * math.cos(phi)

        if denominator == 0:
            return 0.0

        efficiency = numerator / denominator
        return max(0.0, min(1.0, efficiency))

    def analyze_gear_train_efficiency(
        self,
        gears: List[SpurGear],
        input_power_w: float,
        gear_type: str = "spur",
        num_bearings: Optional[int] = None,
        num_seals: Optional[int] = None,
        pitch_line_velocity: float = 5.0,
    ) -> EfficiencyResult:
        """
        Analyze efficiency of a complete gear train.

        分析整个齿轮系的效率。

        Args:
            gears: List of gears in the train
            input_power_w: Input power in Watts
            gear_type: Type of gear mesh
            num_bearings: Number of bearings (default: 2 per gear)
            num_seals: Number of seal pairs (default: 1 per shaft)
            pitch_line_velocity: Average pitch line velocity (m/s)

        Returns:
            EfficiencyResult with detailed breakdown
        """
        num_meshes = len(gears) - 1
        if num_meshes <= 0:
            raise ValueError("Need at least 2 gears")

        if num_bearings is None:
            num_bearings = 2 * len(gears)
        if num_seals is None:
            num_seals = len(gears) // 2

        # Calculate per-stage mesh efficiencies
        mesh_losses = []
        mesh_efficiencies = []
        cumulative_mesh_eff = 1.0

        for i in range(num_meshes):
            mesh_eff = self.analyze_mesh_efficiency(
                gear_type=gear_type,
                pitch_line_velocity=pitch_line_velocity,
                pressure_angle_deg=gears[i].pressure_angle_deg,
                module=gears[i].module,
            )
            mesh_losses.append({
                "stage": i + 1,
                "driver": gears[i].name,
                "driven": gears[i + 1].name,
                "mesh_efficiency": round(mesh_eff * 100, 2),
                "power_loss_w": round(input_power_w * (1 - mesh_eff) * cumulative_mesh_eff, 2),
            })
            mesh_efficiencies.append(mesh_eff)
            cumulative_mesh_eff *= mesh_eff

        # Calculate bearing losses
        bearing_eff = self.bearing_efficiency ** num_bearings
        bearing_loss = input_power_w * (1 - bearing_eff)

        # Calculate seal losses
        seal_eff = self.seal_efficiency ** num_seals
        seal_loss = input_power_w * (1 - seal_eff) * bearing_eff

        # Calculate windage/drag losses
        # Simplified model: proportional to speed^2 and gear size
        windage_loss = self._calculate_windage_loss(gears, pitch_line_velocity)

        # Total output power
        mesh_output = input_power_w * cumulative_mesh_eff
        output_power = mesh_output - bearing_loss - seal_loss - windage_loss
        output_power = max(0, output_power)

        total_loss = input_power_w - output_power
        overall_eff = output_power / input_power_w if input_power_w > 0 else 0

        # Calculate cumulative efficiency by stage
        eff_by_stage = []
        eff = 1.0
        for i in range(num_meshes):
            eff *= mesh_efficiencies[i]
            # Account for bearing and seal losses at each stage
            stage_bearing = self.bearing_efficiency ** (num_bearings // num_meshes)
            stage_seal = self.seal_efficiency ** (num_seals // num_meshes)
            eff_by_stage.append(eff * stage_bearing * stage_seal)

        return EfficiencyResult(
            input_power_w=input_power_w,
            output_power_w=output_power,
            total_loss_w=total_loss,
            mesh_losses=mesh_losses,
            bearing_loss_w=bearing_loss,
            seal_loss_w=seal_loss,
            windage_loss_w=windage_loss,
            overall_efficiency=overall_eff,
            efficiency_by_stage=eff_by_stage,
        )

    def compare_configurations(
        self,
        input_power_w: float,
        input_speed_rpm: float,
        target_ratio: float,
        configurations: List[dict],
    ) -> List[EfficiencyResult]:
        """
        Compare efficiency across different gear configurations.

        比较不同齿轮配置的效率。

        Args:
            input_power_w: Input power in Watts
            input_speed_rpm: Input speed in RPM
            target_ratio: Target overall gear ratio
            configurations: List of config dicts with:
                - 'name': Configuration name
                - 'gears': List of SpurGear objects
                - 'gear_type': Mesh type
                - 'num_bearings': Optional bearing count
                - 'num_seals': Optional seal count

        Returns:
            List of EfficiencyResult for each configuration
        """
        results = []
        for config in configurations:
            result = self.analyze_gear_train_efficiency(
                gears=config["gears"],
                input_power_w=input_power_w,
                gear_type=config.get("gear_type", "spur"),
                num_bearings=config.get("num_bearings"),
                num_seals=config.get("num_seals"),
            )
            result.config_name = config["name"]
            results.append(result)

        # Sort by efficiency (descending)
        results.sort(key=lambda r: r.overall_efficiency, reverse=True)
        return results

    def _calculate_windage_loss(
        self, gears: List[SpurGear], pitch_line_velocity: float
    ) -> float:
        """
        Calculate windage/drag losses.

        计算风阻损失。

        Simplified model based on gear geometry and speed.
        基于齿轮几何和速度的简化模型。
        """
        if not gears:
            return 0.0

        # Use the largest gear for windage estimation
        max_gear = max(gears, key=lambda g: g.outside_diameter)
        d_out = max_gear.outside_diameter / 1000  # Convert to meters
        b = max_gear.face_width / 1000  # Convert to meters

        # Windage power loss (simplified empirical formula)
        # P_windage = k * rho_air * v^3 * A
        # where k ~ 0.01 for open gears, rho_air ~ 1.2 kg/m^3
        rho_air = 1.2  # Air density kg/m^3
        area = d_out * b  # Projected area
        k_factor = 0.01 if self.windage_model == "standard" else 0.02

        windage_loss = k_factor * rho_air * (pitch_line_velocity ** 3) * area
        return max(0, windage_loss)

    @staticmethod
    def print_efficiency_report(result: EfficiencyResult) -> str:
        """Print a formatted efficiency report."""
        lines = [
            "=" * 60,
            " Gear Train Efficiency Report 齿轮传动效率报告",
            "=" * 60,
            f"Input Power (输入功率):     {result.input_power_w:.2f} W",
            f"Output Power (输出功率):    {result.output_power_w:.2f} W",
            f"Total Loss (总损失):        {result.total_loss_w:.2f} W ({result.total_loss_pct:.2f}%)",
            "",
            " Loss Breakdown (损失分解):",
            f"  Mesh Loss (啮合损失):     {sum(l['power_loss_w'] for l in result.mesh_losses):.2f} W",
            f"  Bearing Loss (轴承损失):   {result.bearing_loss_w:.2f} W",
            f"  Seal Loss (密封损失):      {result.seal_loss_w:.2f} W",
            f"  Windage Loss (风阻损失):   {result.windage_loss_w:.2f} W",
            "",
            " Mesh Efficiencies (啮合效率):",
        ]

        for loss in result.mesh_losses:
            lines.append(f"  Stage {loss['stage']}: {loss['mesh_efficiency']:.2f}% (loss: {loss['power_loss_w']:.2f} W)")

        lines.append("")
        lines.append(f" Overall Efficiency (总效率): {result.overall_efficiency * 100:.2f}%")
        lines.append("=" * 60)

        return "\n".join(lines)
