"""Contact Stress Analysis Module.

This module implements contact stress calculations for cam-follower systems
using Hertz contact theory. Contact stress is critical for determining
the fatigue life and load capacity of cam mechanisms.

接触应力分析模块
使用赫兹接触理论计算凸轮-从动件系统的接触应力
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional
from .motion_laws import MotionLaw, MotionLawCalculator
from .cam_profile import CamGeometry, CamProfileGenerator, FollowerType


@dataclass
class ContactStressResult:
    """Stores contact stress analysis results.
    
    存储接触应力分析结果
    """
    max_hertz_stress: float       # 最大赫兹接触应力 [MPa]
    contact_half_width: float     # 接触区半宽 [mm]
    max_allowed_stress: float     # 许用接触应力 [MPa]
    is_safe: bool                 # 是否安全
    stress_distribution: np.ndarray  # 应力分布 [MPa]


class ContactStressAnalyzer:
    """Analyzes contact stresses in cam-follower systems.
    
    凸轮-从动件系统接触应力分析器
    
    Uses Hertz contact theory to calculate:
    - Maximum contact stress (Hertz stress)
    - Contact patch dimensions
    - Factor of safety against surface fatigue
    
    Hertz contact theory applies to curved surfaces in contact under load.
    For cam mechanisms, we typically model:
    - Roller follower on cam: cylinder-on-cylinder contact
    - Flat-foot follower on cam: cylinder-on-plane contact
    - Pin follower on cam: cylinder-on-cylinder contact
    """

    # Material properties (typical values for hardened steel)
    DEFAULT_ELASTIC_MODULUS = 206000.0    # 弹性模量 E [MPa] (206 GPa for steel)
    DEFAULT_POISSON_RATIO = 0.3             # 泊松比 nu
    DEFAULT_ALLOWABLE_STRESS = 1400.0       # 许用接触应力 [MPa]

    def __init__(
        self,
        elastic_modulus: float = DEFAULT_ELASTIC_MODULUS,
        poisson_ratio: float = DEFAULT_POISSON_RATIO,
        allowable_stress: float = DEFAULT_ALLOWABLE_STRESS
    ):
        """Initialize the contact stress analyzer.
        
        Args:
            elastic_modulus: Young's modulus [MPa]
            poisson_ratio: Poisson's ratio
            allowable_stress: Allowable contact stress [MPa]
        """
        self.E = elastic_modulus
        self.nu = poisson_ratio
        self.allowable_stress = allowable_stress

    def calculate_contact_stress(
        self,
        normal_force: float,
        roller_radius: float,
        cam_radius: float,
        follower_width: float = 10.0,
        follower_type: FollowerType = FollowerType.ROLLER
    ) -> ContactStressResult:
        """Calculate Hertz contact stress for cam-follower system.
        
        计算凸轮-从动件系统的赫兹接触应力
        
        Args:
            normal_force: Normal force between cam and follower [N]
            roller_radius: Roller or equivalent radius [mm]
            cam_radius: Cam curvature radius at contact point [mm]
            follower_width: Contact width (face width) [mm]
            follower_type: Type of follower
            
        Returns:
            ContactStressResult with stress analysis
        """
        if normal_force <= 0 or roller_radius <= 0 or cam_radius <= 0:
            return ContactStressResult(
                max_hertz_stress=0.0,
                contact_half_width=0.0,
                max_allowed_stress=self.allowable_stress,
                is_safe=True,
                stress_distribution=np.array([0.0])
            )

        # Calculate equivalent radius of curvature
        # For cylinder contact: 1/R_eq = 1/R1 + 1/R2
        if follower_type == FollowerType.FLAT_FOOT:
            # Cylinder on plane: R_eq = roller_radius
            R_eq = roller_radius
        else:
            # Cylinder on cylinder (or similar)
            if cam_radius > 0:
                R_eq = (roller_radius * cam_radius) / (roller_radius + cam_radius)
            else:
                R_eq = roller_radius

        # Calculate material constant
        # For two identical materials:
        pi_E = np.pi * self.E
        nu_sq = self.nu ** 2
        denom = 1 - nu_sq
        material_const = (1 - nu_sq) / pi_E
        
        # Hertz contact half-width for cylinder contact
        # a = sqrt((2 * F * material_const * R_eq) / (pi * L * E'))
        # Simplified for similar materials:
        a = np.sqrt(
            (2.0 * normal_force * (1 - self.nu ** 2) * R_eq) /
            (np.pi * self.E * follower_width)
        )

        # Maximum Hertz contact stress
        # p_max = 2 * F / (pi * a * L)
        p_max = (2.0 * normal_force) / (np.pi * a * follower_width) if a > 1e-10 else 1e10

        # Create stress distribution (elliptical)
        x = np.linspace(-a, a, 100)
        stress_dist = p_max * np.sqrt(1 - (x / a) ** 2) if a > 1e-10 else np.zeros_like(x)

        return ContactStressResult(
            max_hertz_stress=float(p_max),
            contact_half_width=float(a),
            max_allowed_stress=self.allowable_stress,
            is_safe=p_max < self.allowable_stress,
            stress_distribution=stress_dist
        )

    def calculate_dynamic_force(
        self,
        follower_mass: float,
        acceleration: float,
        spring_force: float = 10.0,
        gravity: float = 9.81
    ) -> float:
        """Calculate the total dynamic force on the follower.
        
        计算从动件的总动态力
        
        F_total = F_spring + F_inertia + F_gravity
        F_inertia = m * a
        
        Args:
            follower_mass: Mass of the follower [kg]
            acceleration: Follower acceleration [mm/s^2]
            spring_force: Return spring force [N]
            gravity: Gravitational acceleration [m/s^2]
            
        Returns:
            Total normal force [N]
        """
        # Convert acceleration to m/s^2
        accel_ms2 = acceleration / 1000.0
        
        # Inertia force (F = ma, direction opposes acceleration)
        F_inertia = follower_mass * accel_ms2
        
        # Total force (spring always pushes, gravity depends on orientation)
        # For vertical follower: gravity adds to spring force during rise
        F_total = spring_force + F_inertia + follower_mass * gravity
        
        return max(F_total, 0.0)  # Force cannot be negative (loss of contact)

    def analyze_full_cycle(
        self,
        geometry: CamGeometry,
        follower_mass: float = 0.1,
        spring_force: float = 10.0,
        omega: float = 1.0,
        n_points: int = 360
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Analyze contact stress over the full cam rotation cycle.
        
        分析整个凸轮旋转周期的接触应力
        
        Args:
            geometry: Cam geometry
            follower_mass: Follower mass [kg]
            spring_force: Return spring force [N]
            omega: Cam angular velocity [rad/s]
            n_points: Number of analysis points
            
        Returns:
            Tuple of (angles, forces, stresses)
        """
        angles = np.linspace(0, geometry.total_angle, n_points)
        forces = np.zeros(n_points)
        stresses = np.zeros(n_points)
        
        calc = MotionLawCalculator(geometry.lift, omega)
        
        for i, theta in enumerate(angles):
            if theta < geometry.lift:  # Simplified
                pass
            
            # Get acceleration at this angle
            if theta < 90:  # Rise phase
                result = calc.calculate(
                    MotionLaw.CYCLOIDAL, 90, theta
                )
                accel = result.acceleration
            elif theta < 180:  # Dwell
                accel = 0.0
            elif theta < 270:  # Return
                result = calc.calculate(
                    MotionLaw.CYCLOIDAL, 90, theta - 180
                )
                accel = -result.acceleration
            else:  # Dwell
                accel = 0.0
            
            # Calculate dynamic force
            forces[i] = self.calculate_dynamic_force(
                follower_mass, accel, spring_force
            )
            
            # Calculate contact stress
            result = self.calculate_contact_stress(
                forces[i],
                geometry.roller_radius if geometry.roller_radius > 0 else 5.0,
                geometry.base_radius,
                10.0,
                geometry.follower_type
            )
            stresses[i] = result.max_hertz_stress

        return angles, forces, stresses

    def get_stress_info(self) -> dict:
        """Get information about contact stress in cam mechanisms."""
        return {
            "hertz_theory": "赫兹接触理论用于计算曲面接触的应力分布",
            "english_theory": "Hertz contact theory calculates stress distribution "
                            "for curved surfaces in contact",
            "max_stress_location": "接触区中心 (Center of contact zone)",
            "failure_modes": [
                "表面疲劳点蚀 (Surface fatigue pitting)",
                "接触磨损 (Contact wear)",
                "塑性变形 (Plastic deformation)"
            ],
            "mitigation": [
                "增大曲率半径 (Increase curvature radius)",
                "使用硬化处理 (Use hardened materials)",
                "改善润滑条件 (Improve lubrication)",
                "降低接触应力 (Reduce contact stress)"
            ]
        }
