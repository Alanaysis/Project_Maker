"""
Module: Gear Train Analysis
模块: 齿轮系分析

This module implements three types of gear trains:
本模块实现三种齿轮系：

1. Simple Gear Train (简单齿轮系):
   - All gears rotate about fixed axes
   - Idler gears can be used to change direction or bridge distances
   - Total ratio = product of individual stage ratios

2. Compound Gear Train (复合齿轮系):
   - Multiple gears share common shafts
   - Allows large ratios in compact space
   - Each stage ratio multiplies together

3. Planetary Gear Train (行星齿轮系):
   - Sun gear, planet gears, and ring gear
   - Multiple power paths, high torque density
   - Analysis uses Willis equation

Key equations for planetary gears:
行星齿轮关键方程:
    (n_s - n_c) / (n_r - n_c) = -z_r / z_s
    where n_s = sun speed, n_r = ring speed, n_c = carrier speed
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from .spur_gear import SpurGear
from .gear_ratio import GearRatioCalculator, GearPair
from .transmission import TransmissionCalculator, TransmissionResult
from .efficiency import EfficiencyAnalyzer


# =============================================================================
# Simple Gear Train
# =============================================================================

@dataclass
class SimpleGearTrain:
    """
    Simple gear train: all gears have fixed axes.

    简单齿轮系：所有齿轮都有固定轴线。

        Driver -> Idler1 -> Idler2 -> ... -> Driven

    Key properties:
        - Overall ratio = (z_driven / z_driver) * (idler ratios cancel)
        - Direction changes with each mesh
        - Idlers don't affect ratio, only direction and center distance
    """

    gears: List[SpurGear] = field(default_factory=list)
    efficiency_analyzer: Optional[EfficiencyAnalyzer] = None

    def add_gear(self, gear: SpurGear):
        """Add a gear to the train."""
        self.gears.append(gear)

    @property
    def num_meshes(self) -> int:
        """Number of gear meshes."""
        return max(0, len(self.gears) - 1)

    @property
    def overall_ratio(self) -> float:
        """
        Overall gear ratio.

        For simple train: ratio = product of all stage ratios.
        Idler gears cancel out in the ratio calculation.
        """
        if len(self.gears) < 2:
            return 1.0

        ratio = 1.0
        for i in range(len(self.gears) - 1):
            ratio *= self.gears[i + 1].num_teeth / self.gears[i].num_teeth
        return ratio

    @property
    def output_direction(self) -> str:
        """Output direction relative to input."""
        return GearRatioCalculator.calculate_direction_changes(self.num_meshes)

    @property
    def center_distances(self) -> List[float]:
        """Center distances between consecutive gear pairs."""
        distances = []
        for i in range(len(self.gears) - 1):
            m = self.gears[i].module
            z1 = self.gears[i].num_teeth
            z2 = self.gears[i + 1].num_teeth
            distances.append(m * (z1 + z2) / 2)
        return distances

    def calculate_transmission(
        self,
        input_speed_rpm: float,
        input_torque_nm: float,
        mesh_type: str = "spur",
    ) -> TransmissionResult:
        """Calculate transmission through the gear train."""
        calc = TransmissionCalculator(mesh_type)
        return calc.calculate_gear_train(
            self.gears, input_speed_rpm, input_torque_nm, mesh_type
        )

    def summary(self) -> dict:
        """Get a summary of the simple gear train."""
        return {
            "type": "Simple Gear Train (简单齿轮系)",
            "num_gears": len(self.gears),
            "num_meshes": self.num_meshes,
            "overall_ratio": round(self.overall_ratio, 4),
            "output_direction": self.output_direction,
            "center_distances": [round(d, 4) for d in self.center_distances],
            "gears": [g.get_geometry_summary() for g in self.gears],
        }


# =============================================================================
# Compound Gear Train
# =============================================================================

@dataclass
class CompoundGearTrain:
    """
    Compound gear train: multiple gears on shared shafts.

    复合齿轮系：多个齿轮在共享轴上。

        Stage 1: z1 -> z2 (z2 and z3 on same shaft)
        Stage 2: z3 -> z4 (z4 and z5 on same shaft)
        Stage 3: z5 -> z6

    Key properties:
        - Each pair on a shared shaft has the same angular velocity
        - Total ratio = product of all stage ratios
        - Can achieve large ratios in compact space
    """

    # Each stage: (driver_teeth, driven_teeth, shared_shaft_gears)
    stages: List[tuple] = field(default_factory=list)
    modules: List[float] = field(default_factory=list)
    efficiency_analyzer: Optional[EfficiencyAnalyzer] = None

    def add_stage(self, driver_teeth: int, driven_teeth: int, module: float = 2.0):
        """Add a gear stage."""
        self.stages.append((driver_teeth, driven_teeth))
        self.modules.append(module)

    @property
    def overall_ratio(self) -> float:
        """Overall gear ratio for the compound train."""
        ratio = 1.0
        for driver_t, driven_t in self.stages:
            ratio *= driven_t / driver_t
        return ratio

    @property
    def num_stages(self) -> int:
        """Number of gear stages."""
        return len(self.stages)

    def create_gears(self, name_prefix: str = "gear") -> List[SpurGear]:
        """
        Create SpurGear objects from the stage definitions.

        从阶段定义创建SpurGear对象。
        """
        gears = []
        gear_num = 1

        for i, (driver_t, driven_t) in enumerate(self.stages):
            m = self.modules[i] if i < len(self.modules) else 2.0
            # Driver gear
            driver = SpurGear(
                module=m,
                num_teeth=driver_t,
                name=f"{name_prefix}_{gear_num}",
            )
            gears.append(driver)
            gear_num += 1
            # Driven gear
            driven = SpurGear(
                module=m,
                num_teeth=driven_t,
                name=f"{name_prefix}_{gear_num}",
            )
            gears.append(driven)
            gear_num += 1

        return gears

    def calculate_transmission(
        self,
        input_speed_rpm: float,
        input_torque_nm: float,
        mesh_type: str = "spur",
    ) -> TransmissionResult:
        """Calculate transmission through the compound gear train."""
        num_stages = len(self.stages)
        mesh_eff = EfficiencyAnalyzer.MESH_EFFICIENCY.get(mesh_type, 0.97)
        cumulative_eff = mesh_eff ** num_stages

        total_ratio = 1.0
        for driver_t, driven_t in self.stages:
            total_ratio *= driven_t / driver_t

        output_speed = input_speed_rpm / total_ratio
        output_torque = input_torque_nm * total_ratio * cumulative_eff
        input_power = self._torque_to_power(input_torque_nm, input_speed_rpm)
        output_power = input_power * cumulative_eff

        return TransmissionResult(
            input_speed_rpm=input_speed_rpm,
            output_speed_rpm=output_speed,
            input_torque_nm=input_torque_nm,
            output_torque_nm=output_torque,
            input_power_w=input_power,
            output_power_w=output_power,
            overall_ratio=total_ratio,
            efficiency=cumulative_eff,
            speed_reduction=total_ratio,
            torque_amplification=total_ratio * cumulative_eff,
        )

    @staticmethod
    def _torque_to_power(torque_nm: float, speed_rpm: float) -> float:
        """Convert torque and speed to power."""
        omega = 2 * math.pi * speed_rpm / 60
        return torque_nm * omega

    def stage_by_stage_analysis(
        self,
        input_speed_rpm: float,
        input_torque_nm: float,
        mesh_type: str = "spur",
    ) -> List[dict]:
        """Analyze each stage individually."""
        gears = self.create_gears()
        calc = TransmissionCalculator(mesh_type)
        return calc.calculate_stage_by_stage(gears, input_speed_rpm, input_torque_nm, mesh_type)

    @staticmethod
    def _torque_to_power(torque_nm: float, speed_rpm: float) -> float:
        """Convert torque and speed to power."""
        omega = 2 * math.pi * speed_rpm / 60
        return torque_nm * omega

    def summary(self) -> dict:
        """Get a summary of the compound gear train."""
        return {
            "type": "Compound Gear Train (复合齿轮系)",
            "num_stages": self.num_stages,
            "overall_ratio": round(self.overall_ratio, 4),
            "stages": [
                {
                    "stage": i + 1,
                    "driver_teeth": d[0],
                    "driven_teeth": d[1],
                    "stage_ratio": round(d[1] / d[0], 4),
                    "module": self.modules[i] if i < len(self.modules) else 2.0,
                }
                for i, d in enumerate(self.stages)
            ],
        }


# =============================================================================
# Planetary Gear Train
# =============================================================================

@dataclass
class PlanetaryGearTrain:
    """
    Planetary (epicyclic) gear train.

    行星（周转）齿轮系。

    Components:
        - Sun gear (太阳轮): central gear
        - Planet gears (行星轮): orbit around the sun
        - Ring gear (内齿轮/齿圈): outer gear with internal teeth
        - Carrier (行星架): holds the planet gears

    Willis equation (威利斯方程):
        (n_s - n_c) / (n_r - n_c) = -z_r / z_s

    where:
        n_s = sun gear speed
        n_r = ring gear speed
        n_c = carrier speed
        z_s = sun gear teeth
        z_r = ring gear teeth

    Key constraint: z_r = z_s + 2 * z_p (for proper meshing)
    """

    sun_teeth: int
    planet_teeth: int
    ring_teeth: int
    num_planets: int = 3
    sun_name: str = "sun"
    planet_name: str = "planet"
    ring_name: str = "ring"
    carrier_name: str = "carrier"

    def __post_init__(self):
        """Validate planetary gear geometry."""
        # Check that ring teeth = sun teeth + 2 * planet teeth
        expected_ring = self.sun_teeth + 2 * self.planet_teeth
        if self.ring_teeth != expected_ring:
            raise ValueError(
                f"Ring teeth ({self.ring_teeth}) must equal "
                f"sun teeth ({self.sun_teeth}) + 2 * planet teeth ({2 * self.planet_teeth})"
            )

        # Check assembly condition: (z_s + z_r) must be divisible by num_planets
        if (self.sun_teeth + self.ring_teeth) % self.num_planets != 0:
            raise ValueError(
                f"(z_s + z_r) = {self.sun_teeth + self.ring_teeth} "
                f"must be divisible by num_planets = {self.num_planets}"
            )

    @property
    def planet_module(self) -> float:
        """Module derived from gear geometry."""
        # d_r = d_s + 2 * d_p
        # m * z_r = m * z_s + 2 * m * z_p
        # This is always true, module is a design choice
        return 2.0  # Default module

    @property
    def pitch_radii(self) -> Dict[str, float]:
        """Pitch circle radii for each component."""
        m = self.planet_module
        return {
            "sun": m * self.sun_teeth / 2,
            "planet": m * self.planet_teeth / 2,
            "ring": m * self.ring_teeth / 2,
            "carrier": m * (self.sun_teeth + self.planet_teeth) / 2,
        }

    def solve_speed(
        self,
        fixed_component: str,
        input_speed: float,
        input_component: str = "sun",
    ) -> Dict[str, float]:
        """
        Solve speeds using Willis equation.

        使用威利斯方程求解转速。

        Args:
            fixed_component: Component held stationary ("sun", "ring", or "carrier")
            input_speed: Input speed in RPM
            input_component: Component receiving input ("sun", "ring", or "carrier")

        Returns:
            Dictionary of speeds for all components
        """
        zs = self.sun_teeth
        zr = self.ring_teeth
        alpha = -zr / zs  # Internal gear ratio

        speeds = {"sun": 0.0, "ring": 0.0, "carrier": 0.0}

        if fixed_component == "ring":
            # Ring fixed: n_r = 0
            # (n_s - n_c) / (0 - n_c) = alpha
            # n_s - n_c = -alpha * n_c
            # n_s = n_c * (1 - alpha)
            # n_c = n_s / (1 - alpha)
            speeds[input_component] = input_speed
            if input_component == "sun":
                speeds["sun"] = input_speed
                speeds["carrier"] = input_speed / (1 - alpha)
            elif input_component == "carrier":
                speeds["carrier"] = input_speed
                speeds["sun"] = input_speed * (1 - alpha)
            else:
                speeds["ring"] = 0.0  # Fixed
        elif fixed_component == "sun":
            # Sun fixed: n_s = 0
            # (0 - n_c) / (n_r - n_c) = alpha
            # -n_c = alpha * (n_r - n_c)
            # n_c * (alpha - 1) = alpha * n_r
            # n_c = alpha * n_r / (alpha - 1)
            speeds[input_component] = input_speed
            if input_component == "ring":
                speeds["ring"] = input_speed
                speeds["carrier"] = alpha * input_speed / (alpha - 1)
            elif input_component == "carrier":
                speeds["carrier"] = input_speed
                speeds["ring"] = input_speed * (alpha - 1) / alpha
            else:
                speeds["sun"] = 0.0  # Fixed
        elif fixed_component == "carrier":
            # Carrier fixed: n_c = 0
            # n_s / n_r = alpha
            speeds[input_component] = input_speed
            if input_component == "sun":
                speeds["sun"] = input_speed
                speeds["ring"] = input_speed / alpha
            elif input_component == "ring":
                speeds["ring"] = input_speed
                speeds["sun"] = input_speed * alpha
            else:
                speeds["carrier"] = 0.0  # Fixed
        else:
            raise ValueError(f"Unknown fixed component: {fixed_component}")

        # Planet speed relative to carrier
        # n_p = (n_s - n_c) * z_s / (2 * z_p)
        speeds["planet_relative"] = (speeds["sun"] - speeds["carrier"]) * zs / (2 * self.planet_teeth)

        return speeds

    def get_modes(self) -> List[dict]:
        """
        Get all possible operating modes.

        获取所有可能的运行模式。

        In a planetary gear set, any component can be:
        - Input
        - Output
        - Fixed (stationary)

        This gives 3! = 6 possible configurations.
        """
        modes = []
        components = ["sun", "ring", "carrier"]

        for fixed in components:
            for inp in components:
                if inp == fixed:
                    continue
                # Find the remaining component (not fixed, not input)
                remaining = [c for c in components if c != fixed and c != inp]
                if not remaining:
                    continue
                out = remaining[0]

                speeds = self.solve_speed(fixed, 1000.0, inp)
                ratio = speeds[inp] / speeds[out] if speeds[out] != 0 else float("inf")

                modes.append({
                    "fixed": fixed,
                    "input": inp,
                    "output": out,
                    "input_speed": 1000.0,
                    "output_speed": round(speeds[out], 2),
                    "ratio": round(ratio, 4),
                    "type": "reduction" if abs(ratio) > 1 else "increase",
                })

        return modes

    def create_gears(self) -> Dict[str, SpurGear]:
        """Create SpurGear objects for all components."""
        m = self.planet_module
        sun = SpurGear(module=m, num_teeth=self.sun_teeth, name=self.sun_name)
        ring = SpurGear(module=m, num_teeth=self.ring_teeth, name=self.ring_name)
        planets = [
            SpurGear(module=m, num_teeth=self.planet_teeth, name=f"{self.planet_name}_{i}")
            for i in range(self.num_planets)
        ]
        # Carrier is not a gear but can be represented
        carrier = SpurGear(
            module=m, num_teeth=self.sun_teeth + 2 * self.planet_teeth,
            name=self.carrier_name
        )
        return {
            "sun": sun,
            "ring": ring,
            "planets": planets,
            "carrier": carrier,
        }

    def summary(self) -> dict:
        """Get a summary of the planetary gear train."""
        return {
            "type": "Planetary Gear Train (行星齿轮系)",
            "sun_teeth": self.sun_teeth,
            "planet_teeth": self.planet_teeth,
            "ring_teeth": self.ring_teeth,
            "num_planets": self.num_planets,
            "pitch_radii": {k: round(v, 4) for k, v in self.pitch_radii.items()},
            "modes": self.get_modes(),
        }
