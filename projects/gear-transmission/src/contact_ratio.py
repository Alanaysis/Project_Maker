"""
Module: Contact Ratio Calculation
模块: 重合度计算

Contact ratio (重合度) is a critical parameter in gear design.
It represents the average number of tooth pairs in contact during
meshing.

重合度是齿轮设计中的关键参数。它表示啮合过程中齿对接触的平均数量。

Requirements:
    - Contact ratio >= 1.2 for smooth operation (标准齿轮要求 >= 1.2)
    - Higher contact ratio = smoother operation, better load distribution
      更高的重合度 = 更平稳的运行，更好的载荷分布
    - For spur gears, typical contact ratio is 1.4 to 1.8

Key formulas:
    - Path of contact length: L = sqrt(ra1^2 - rb1^2) + sqrt(ra2^2 - rb2^2) - a*sin(phi)
    - Base pitch: pb = pi * m * cos(phi)
    - Contact ratio: epsilon = L / pb
"""

import math
from dataclasses import dataclass
from typing import List
from .spur_gear import SpurGear


@dataclass
class ContactRatioResult:
    """Result of contact ratio calculation."""
    contact_ratio: float
    path_of_contact: float
    base_pitch: float
    path_of_approach: float
    path_of_recess: float
    max_contact_length: float
    min_required: float
    is_adequate: bool
    gear1_name: str
    gear2_name: str

    def summary(self) -> dict:
        """Get a summary of the contact ratio result."""
        return {
            "gear_pair": f"{self.gear1_name} <-> {self.gear2_name}",
            "contact_ratio": round(self.contact_ratio, 4),
            "path_of_contact_mm": round(self.path_of_contact, 4),
            "base_pitch_mm": round(self.base_pitch, 4),
            "path_of_approach_mm": round(self.path_of_approach, 4),
            "path_of_recess_mm": round(self.path_of_recess, 4),
            "is_adequate": self.is_adequate,
            "recommendation": (
                "满足要求，运行平稳" if self.is_adequate
                else f"不足！需要增大齿数或减小压力角（当前最小值: {self.min_required}）"
            ),
        }


class ContactRatioCalculator:
    """
    Calculate contact ratio for spur gear pairs.

    计算直齿轮副的重合度。

    The contact ratio determines:
        1. Smoothness of operation
        2. Load distribution across teeth
        3. Noise level
        4. Gear life

    重合度决定：
        1. 运行平稳性
        2. 齿间载荷分布
        3. 噪声水平
        4. 齿轮寿命
    """

    # Minimum recommended contact ratio for different applications
    MIN_CONTACT_RATIO = {
        "general": 1.2,
        "smooth_operation": 1.4,
        "high_load": 1.5,
        "precision": 1.6,
        "automotive": 1.5,
        "aerospace": 1.8,
    }

    @staticmethod
    def calculate(
        gear1: SpurGear,
        gear2: SpurGear,
        application: str = "general",
    ) -> ContactRatioResult:
        """
        Calculate contact ratio for a pair of meshing spur gears.

        计算一对啮合直齿轮的重合度。

        The path of contact is the length of the line of action
        along which tooth profiles slide against each other.

        啮合路径是齿沿作用线滑动的长度。

        Formula:
            Pa = sqrt(ra1^2 - rb1^2) + sqrt(ra2^2 - rb2^2) - a*sin(phi)

        where:
            ra = outside radius (齿顶圆半径)
            rb = base circle radius (基圆半径)
            a = center distance (中心距)
            phi = pressure angle (压力角)
        """
        # Validate meshing compatibility
        if gear1.module != gear2.module:
            raise ValueError("Meshing gears must have the same module")
        if abs(gear1.pressure_angle_deg - gear2.pressure_angle_deg) > 0.01:
            raise ValueError("Meshing gears must have the same pressure angle")

        m = gear1.module
        phi = gear1.pressure_angle_rad
        z1 = gear1.num_teeth
        z2 = gear2.num_teeth

        # Calculate key geometric parameters
        r1 = gear1.pitch_diameter / 2  # Pitch radius
        r2 = gear2.pitch_diameter / 2
        rb1 = gear1.base_circle_diameter / 2  # Base circle radius
        rb2 = gear2.base_circle_diameter / 2
        ra1 = gear1.outside_diameter / 2  # Outside radius
        ra2 = gear2.outside_diameter / 2
        a = (gear1.pitch_diameter + gear2.pitch_diameter) / 2  # Center distance

        # Path of contact
        # Pa = sqrt(ra1^2 - rb1^2) + sqrt(ra2^2 - rb2^2) - a*sin(phi)
        path_approach = math.sqrt(ra2 ** 2 - rb2 ** 2)  # Path of approach (齿顶侧啮合段)
        path_recess = math.sqrt(ra1 ** 2 - rb1 ** 2)  # Path of recess (齿根侧啮合段)
        path_of_contact = path_approach + path_recess - a * math.sin(phi)

        # Base pitch
        base_pitch = math.pi * m * math.cos(phi)

        # Contact ratio
        if base_pitch > 0:
            contact_ratio = path_of_contact / base_pitch
        else:
            contact_ratio = 0.0

        # Maximum possible contact length
        max_contact = path_approach + path_recess

        # Minimum required
        min_required = ContactRatioCalculator.MIN_CONTACT_RATIO.get(application, 1.2)

        return ContactRatioResult(
            contact_ratio=contact_ratio,
            path_of_contact=path_of_contact,
            base_pitch=base_pitch,
            path_of_approach=path_approach,
            path_of_recess=path_recess,
            max_contact_length=max_contact,
            min_required=min_required,
            is_adequate=contact_ratio >= min_required,
            gear1_name=gear1.name,
            gear2_name=gear2.name,
        )

    @staticmethod
    def calculate_axial_contact_ratio(gear: SpurGear) -> float:
        """
        Calculate axial contact ratio (face contact ratio) for helical gears.

        计算斜齿轮的轴向重合度（面接触比）。

        For helical gears, there is an additional axial component:
        对于斜齿轮，还有额外的轴向分量：

            epsilon_beta = beta * b / (pi * m_n)

        where:
            beta = helix angle (螺旋角)
            b = face width (齿宽)
            m_n = normal module (法向模数)

        Total contact ratio = epsilon_alpha + epsilon_beta
        总重合度 = 端面重合度 + 轴向重合度
        """
        # For spur gears, helix angle is 0, so axial contact ratio is 0
        # This is primarily for helical gear calculations
        return 0.0

    @staticmethod
    def analyze_contact_quality(contact_ratio: float) -> dict:
        """
        Analyze the quality of gear contact based on contact ratio.

        根据重合度分析齿轮接触质量。
        """
        if contact_ratio < 1.0:
            quality = "poor"
            description = "啮合不良，齿对会完全脱离接触"
            recommendation = "增加齿数或减小压力角以提高重合度"
        elif contact_ratio < 1.1:
            quality = "marginal"
            description = "勉强可用，但会有冲击和噪声"
            recommendation = "建议增大齿数或采用斜齿轮"
        elif contact_ratio < 1.5:
            quality = "good"
            description = "良好，适用于一般应用"
            recommendation = "当前设计满足一般应用需求"
        elif contact_ratio < 2.0:
            quality = "excellent"
            description = "优秀，运行平稳，噪声低"
            recommendation = "适用于高要求应用"
        else:
            quality = "exceptional"
            description = "卓越，多对齿同时啮合"
            recommendation = "适用于极高载荷和精密应用"

        return {
            "contact_ratio": round(contact_ratio, 4),
            "quality": quality,
            "description": description,
            "recommendation": recommendation,
        }

    @staticmethod
    def find_gear_pairs_for_ratio(
        target_ratio: float,
        min_contact: float = 1.2,
        max_teeth: int = 100,
    ) -> List[dict]:
        """
        Find gear pairs that achieve a target ratio with adequate contact ratio.

        找到能达到目标传动比且具有足够重合度的齿轮对。
        """
        results = []

        for z1 in range(17, max_teeth):  # Start from minimum to avoid undercutting
            z2 = round(z1 * target_ratio)
            if z2 < 17 or z2 > max_teeth:
                continue

            # Create temporary gears for contact ratio calculation
            g1 = SpurGear(module=2.0, num_teeth=z1, name=f"z1_{z1}")
            g2 = SpurGear(module=2.0, num_teeth=z2, name=f"z2_{z2}")

            result = ContactRatioCalculator.calculate(g1, g2)

            if result.contact_ratio >= min_contact:
                results.append({
                    "driver_teeth": z1,
                    "driven_teeth": z2,
                    "actual_ratio": round(z2 / z1, 4),
                    "contact_ratio": round(result.contact_ratio, 4),
                    "quality": ContactRatioCalculator.analyze_contact_quality(result.contact_ratio)["quality"],
                })

            if len(results) >= 10:
                break

        return results

    @staticmethod
    def print_contact_report(result: ContactRatioResult):
        """Print a formatted contact ratio report."""
        lines = [
            "=" * 50,
            " Contact Ratio Report 重合度报告",
            "=" * 50,
            f"Gear Pair (齿轮副): {result.gear1_name} <-> {result.gear2_name}",
            f"Contact Ratio (重合度): {result.contact_ratio:.4f}",
            f"Path of Contact (啮合路径): {result.path_of_contact:.4f} mm",
            f"Base Pitch (基圆齿距): {result.base_pitch:.4f} mm",
            f"Path of Approach (啮合 approaches 段): {result.path_of_approach:.4f} mm",
            f"Path of Recess (啮合 recess 段): {result.path_of_recess:.4f} mm",
            f"Minimum Required (最小要求): {result.min_required}",
            f"Adequate (是否满足): {'Yes' if result.is_adequate else 'No'}",
            f"Recommendation (建议): {result.recommendation}",
            "=" * 50,
        ]
        print("\n".join(lines))
