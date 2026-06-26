"""
Module: Spur Gear Geometry and Calculations
模块: 直齿轮几何与计算

Spur gear (直齿轮) is the simplest type of gear with straight teeth
parallel to the rotation axis. This module implements the fundamental
geometry and calculations for spur gears.

直齿轮是最简单的齿轮类型，齿与旋转轴平行。本模块实现直齿轮的基本
几何和计算。
"""

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class SpurGear:
    """
    Represents a spur gear with all its geometric parameters.

    表示具有所有几何参数的直齿轮。

    Key geometric relationships:
    关键几何关系:
        - Pitch diameter: d = m * z
          分度圆直径 = 模数 * 齿数
        - Base circle diameter: db = d * cos(pressure_angle)
          基圆直径 = 分度圆直径 * cos(压力角)
        - Addendum: a = m
          齿顶高 = 模数
        - Dedendum: b = 1.25 * m (standard)
          齿根高 = 1.25 * 模数 (标准)
        - Outside diameter: do = d + 2*m
          齿顶圆直径 = 分度圆直径 + 2*模数
        - Root diameter: df = d - 2.5*m
          齿根圆直径 = 分度圆直径 - 2.5*模数
    """

    # Module (模数) - standard parameter defining tooth size
    module: float
    # Number of teeth (齿数)
    num_teeth: int
    # Pressure angle (压力角) - standard values: 14.5°, 20°, 25°
    pressure_angle_deg: float = 20.0
    # Addendum coefficient (齿顶高系数) - standard is 1.0
    addendum_coefficient: float = 1.0
    # Dedendum coefficient (齿根高系数) - standard is 1.25
    dedendum_coefficient: float = 1.25
    # Clearance (顶隙) - standard is 0.25 * module
    clearance: Optional[float] = None
    # Gear face width (齿宽)
    face_width: float = 10.0
    # Material density (kg/mm^3) for weight calculation
    material_density: float = 7.85e-6  # Steel ~7850 kg/m^3
    # Gear name for identification
    name: str = "gear"

    def __post_init__(self):
        """Validate parameters after initialization."""
        if self.module <= 0:
            raise ValueError("Module must be positive")
        if self.num_teeth <= 0:
            raise ValueError("Number of teeth must be positive")
        if self.num_teeth < 17 and self.pressure_angle_deg == 20.0:
            pass  # Warning for undercutting - handled in properties
        if self.pressure_angle_deg <= 0 or self.pressure_angle_deg >= 90:
            raise ValueError("Pressure angle must be between 0 and 90 degrees")
        if self.clearance is None:
            self.clearance = 0.25 * self.module

    @property
    def pressure_angle_rad(self) -> float:
        """Convert pressure angle to radians."""
        return math.radians(self.pressure_angle_deg)

    @property
    def pitch_diameter(self) -> float:
        """
        Pitch diameter (分度圆直径).

        The pitch circle is the reference circle for gear dimensions.
        分度圆是齿轮尺寸的参考圆。

        Formula: d = m * z
        """
        return self.module * self.num_teeth

    @property
    def base_circle_diameter(self) -> float:
        """
        Base circle diameter (基圆直径).

        The base circle is used to generate the involute tooth profile.
        基圆用于生成渐开线齿廓。

        Formula: db = d * cos(phi)
        """
        return self.pitch_diameter * math.cos(self.pressure_angle_rad)

    @property
    def addendum(self) -> float:
        """
        Addendum (齿顶高).

        The radial distance from the pitch circle to the tip circle.
        从分度圆到齿顶圆的径向距离。

        Formula: a = ha* * m
        """
        return self.addendum_coefficient * self.module

    @property
    def dedendum(self) -> float:
        """
        Dedendum (齿根高).

        The radial distance from the pitch circle to the root circle.
        从分度圆到齿根圆的径向距离。

        Formula: b = (ha* + c*) * m
        """
        return (self.addendum_coefficient + self.dedendum_coefficient) * self.module

    @property
    def outside_diameter(self) -> float:
        """
        Outside diameter / Addendum circle diameter (齿顶圆直径).

        Formula: do = d + 2*ha*m
        """
        return self.pitch_diameter + 2 * self.addendum

    @property
    def root_diameter(self) -> float:
        """
        Root diameter / Dedendum circle diameter (齿根圆直径).

        Formula: df = d - 2*(ha*+c*)*m
        """
        return self.pitch_diameter - 2 * (self.addendum_coefficient + self.dedendum_coefficient) * self.module

    @property
    def root_diameter_standard(self) -> float:
        """
        Root diameter using standard coefficients (df = d - 2.5*m).
        使用标准系数的齿根圆直径。
        """
        return self.pitch_diameter - 2.5 * self.module

    @property
    def tooth_thickness(self) -> float:
        """
        Tooth thickness at pitch circle (分度圆齿厚).

        For standard gears: s = pi * m / 2
        """
        return math.pi * self.module / 2

    @property
    def tooth_space(self) -> float:
        """
        Tooth space width at pitch circle (分度圆齿槽宽).

        For standard gears: e = pi * m / 2
        """
        return math.pi * self.module / 2

    @property
    def circular_pitch(self) -> float:
        """
        Circular pitch (齿距).

        The distance along the pitch circle between corresponding points
        on adjacent teeth.

        沿分度圆相邻齿对应点之间的距离。

        Formula: p = pi * m
        """
        return math.pi * self.module

    @property
    def diametral_pitch(self) -> float:
        """
        Diametral pitch (径节).

        Used primarily in inch-based systems.

        Formula: P = z / d = 1/m (when m in mm, P in 1/mm)
        """
        return self.num_teeth / self.pitch_diameter

    @property
    def module_pitch(self) -> float:
        """Pitch per tooth (每齿节距)."""
        return self.pitch_diameter / self.num_teeth

    @property
    def pitch_circle_area(self) -> float:
        """Area of the pitch circle."""
        r = self.pitch_diameter / 2
        return math.pi * r ** 2

    @property
    def volume(self) -> float:
        """
        Estimated gear volume (estimated as cylinder between root and tip).

        齿轮体积估算（按齿根到齿顶的圆柱体估算）。
        """
        r_outer = self.outside_diameter / 2
        r_root = self.root_diameter / 2
        return math.pi * (r_outer ** 2 - r_root ** 2) / 4 * self.face_width

    @property
    def mass(self) -> float:
        """Estimated gear mass (kg)."""
        return self.volume * self.material_density

    @property
    def undercut_warning(self) -> bool:
        """
        Check for undercutting risk.

        Undercutting occurs when the number of teeth is too small,
        causing the cutting tool to remove material from the root
        of the tooth profile, weakening the gear.

        当齿数过少时会发生根切，导致齿根强度降低。

        Minimum teeth to avoid undercutting (标准压力角20度):
            z_min = 2 / sin^2(phi) ≈ 17 teeth
        """
        z_min = 2 / (math.sin(self.pressure_angle_rad) ** 2)
        return self.num_teeth < z_min

    @property
    def standard_min_teeth(self) -> int:
        """Minimum teeth to avoid undercutting for given pressure angle."""
        return max(1, math.ceil(2 / (math.sin(self.pressure_angle_rad) ** 2)))

    def generate_involute_profile(self, num_points: int = 100) -> tuple:
        """
        Generate involute gear tooth profile points.

        生成渐开线齿轮齿廓点。

        The involute curve is generated by unwrapping a string from
        the base circle.

        渐开线曲线由从基圆展开的直线生成。

        Parametric equations:
            x = rb * (cos(t) + t*sin(t))
            y = rb * (sin(t) - t*cos(t))

        where t is the involute parameter (展开角).

        Returns:
            (x_coords, y_coords) tuples for the profile
        """
        rb = self.base_circle_diameter / 2  # base circle radius
        ra = self.outside_diameter / 2  # outside circle radius

        # Calculate the involute angle at the outside circle
        # cos(alpha_a) = rb / ra
        alpha_a = math.acos(rb / ra)

        # The involute parameter t ranges from 0 to alpha_a
        t_values = [alpha_a * i / (num_points - 1) for i in range(num_points)]

        x_coords = []
        y_coords = []
        for t in t_values:
            x = rb * (math.cos(t) + t * math.sin(t))
            y = rb * (math.sin(t) - t * math.cos(t))
            x_coords.append(x)
            y_coords.append(y)

        return (x_coords, y_coords)

    def get_geometry_summary(self) -> dict:
        """
        Get a summary of all gear geometry parameters.

        获取所有齿轮几何参数的摘要。
        """
        return {
            "name": self.name,
            "module (m)": self.module,
            "num_teeth (z)": self.num_teeth,
            "pressure_angle (deg)": self.pressure_angle_deg,
            "pitch_diameter (d)": round(self.pitch_diameter, 4),
            "base_circle_diameter (db)": round(self.base_circle_diameter, 4),
            "addendum (ha)": round(self.addendum, 4),
            "dedendum (h):": round(self.dedendum, 4),
            "outside_diameter (da)": round(self.outside_diameter, 4),
            "root_diameter (df)": round(self.root_diameter, 4),
            "circular_pitch (p)": round(self.circular_pitch, 4),
            "tooth_thickness (s)": round(self.tooth_thickness, 4),
            "face_width (b)": self.face_width,
            "undercut_warning": self.undercut_warning,
            "min_teeth_no_undercut": self.standard_min_teeth,
            "estimated_mass_kg": round(self.mass * 1000, 4),  # convert to grams
        }

    def __repr__(self) -> str:
        return (
            f"SpurGear(name='{self.name}', m={self.module}, z={self.num_teeth}, "
            f"phi={self.pressure_angle_deg}°)"
        )
