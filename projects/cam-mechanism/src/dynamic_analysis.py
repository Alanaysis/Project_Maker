"""Dynamic Analysis Module.

This module implements dynamic analysis of cam mechanisms, including:
- Inertia force calculation
- Natural frequency estimation
- Dynamic amplification factor
- Resonance analysis
- Dynamic load analysis

动力学分析模块
实现凸轮机构的动力学分析，包括惯性力计算、固有频率估计、
动态放大系数、共振分析和动态载荷分析
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional
from .motion_laws import MotionLaw, MotionLawCalculator, MotionResult
from .cam_profile import CamGeometry, FollowerType


@dataclass
class DynamicResult:
    """Stores dynamic analysis results.
    
    存储动力学分析结果
    """
    inertia_force: np.ndarray       # 惯性力 [N]
    spring_force: np.ndarray        # 弹簧力 [N]
    total_force: np.ndarray         # 总接触力 [N]
    max_dynamic_factor: float       # 最大动态放大系数
    natural_frequency: float        # 固有频率 [Hz]
    jerk: np.ndarray                # 跃度 [mm/s^3]


@dataclass
class SystemParameters:
    """System dynamic parameters.
    
    系统动力学参数
    """
    follower_mass: float = 0.1          # 从动件质量 [kg]
    cam_mass: float = 0.5               # 凸轮质量 [kg]
    spring_stiffness: float = 500.0     # 弹簧刚度 [N/mm]
    spring_preload: float = 10.0        # 弹簧预紧力 [N]
    damping_ratio: float = 0.05         # 阻尼比
    equivalent_mass: float = 0.1        # 等效质量 [kg]
    equivalent_stiffness: float = 500.0 # 等效刚度 [N/mm]


class DynamicAnalyzer:
    """Performs dynamic analysis of cam-follower systems.
    
    凸轮-从动件系统动力学分析器
    
    Dynamic effects become important at high speeds:
    1. Inertia forces increase with the square of angular velocity
    2. Elastic deformation of components causes vibration
    3. Spring force must overcome inertia to maintain contact
    4. Resonance can occur at certain speeds
    
    Key equations:
    - Inertia force: F_i = m * a (m = mass, a = acceleration)
    - Natural frequency: f_n = (1/2pi) * sqrt(k/m)
    - Dynamic amplification: D = 1 / sqrt((1-r^2)^2 + (2*zeta*r)^2)
      where r = omega/omega_n, zeta = damping ratio
    """

    def __init__(self, params: Optional[SystemParameters] = None):
        """Initialize the dynamic analyzer.
        
        Args:
            params: System dynamic parameters
        """
        self.params = params or SystemParameters()

    def calculate_inertia_force(
        self,
        acceleration: float,
        mass: Optional[float] = None
    ) -> float:
        """Calculate inertia force from follower acceleration.
        
        从从动件加速度计算惯性力
        
        F_inertia = m * a
        
        Args:
            acceleration: Follower acceleration [mm/s^2]
            mass: Mass of the follower [kg]
            
        Returns:
            Inertia force [N]
        """
        m = mass or self.params.follower_mass
        # Convert mm/s^2 to m/s^2
        accel_ms2 = acceleration / 1000.0
        return m * accel_ms2

    def analyze_dynamic_forces(
        self,
        geometry: CamGeometry,
        params: Optional[SystemParameters] = None,
        n_points: int = 360
    ) -> DynamicResult:
        """Analyze dynamic forces throughout the cam rotation cycle.
        
        分析凸轮旋转周期内的动态力
        
        Args:
            geometry: Cam geometry
            params: System parameters (overrides defaults)
            n_points: Number of calculation points
            
        Returns:
            DynamicResult with force analysis
        """
        p = params or self.params
        angles = np.linspace(0, geometry.total_angle, n_points)
        
        inertia_force = np.zeros(n_points)
        spring_force = np.zeros(n_points)
        total_force = np.zeros(n_points)
        jerk = np.zeros(n_points)
        
        calc = MotionLawCalculator(geometry.lift, 1.0)  # omega=1 for normalized
        max_accel = 0.0
        
        # First pass: calculate accelerations
        accelerations = np.zeros(n_points)
        for i, theta in enumerate(angles):
            if theta < geometry.lift:
                result = calc.calculate(MotionLaw.CYCLOIDAL, geometry.lift, theta)
                accelerations[i] = result.acceleration
                max_accel = max(max_accel, abs(result.acceleration))
            elif theta < geometry.lift + 90:
                accelerations[i] = 0.0
            elif theta < 2 * geometry.lift + 90:
                result = calc.calculate(MotionLaw.CYCLOIDAL, geometry.lift,
                                       theta - geometry.lift - 90)
                accelerations[i] = -result.acceleration
                max_accel = max(max_accel, abs(result.acceleration))
            else:
                accelerations[i] = 0.0
        
        # Calculate inertia forces
        for i in range(n_points):
            inertia_force[i] = self.calculate_inertia_force(accelerations[i], p.follower_mass)
            # Spring force varies to maintain contact
            spring_force[i] = p.spring_preload + p.spring_stiffness * geometry.lift * 0.1
            total_force[i] = spring_force[i] + inertia_force[i]
            
            # Jerk calculation
            if i > 0:
                jerk[i] = (accelerations[i] - accelerations[i-1]) / (angles[1] - angles[0])

        # Calculate natural frequency
        k = p.equivalent_stiffness * 1000.0  # N/m
        m = p.equivalent_mass
        omega_n = np.sqrt(k / m) if m > 0 else 0.0
        natural_freq = omega_n / (2 * np.pi) if omega_n > 0 else 0.0
        
        # Calculate dynamic amplification factor
        omega_operating = 1.0  # Normalized
        r = omega_operating / omega_n if omega_n > 0 else 0.0
        zeta = p.damping_ratio
        denom = np.sqrt((1 - r**2)**2 + (2 * zeta * r)**2)
        max_dynamic_factor = 1.0 / denom if denom > 1e-10 else 1.0

        return DynamicResult(
            inertia_force=inertia_force,
            spring_force=spring_force,
            total_force=total_force,
            max_dynamic_factor=float(max_dynamic_factor),
            natural_frequency=float(natural_freq),
            jerk=jerk
        )

    def calculate_natural_frequency(
        self,
        mass: Optional[float] = None,
        stiffness: Optional[float] = None
    ) -> float:
        """Calculate the natural frequency of the follower system.
        
        计算从动件系统的固有频率
        
        f_n = (1/2*pi) * sqrt(k/m)
        
        Args:
            mass: Mass [kg]
            stiffness: Stiffness [N/mm]
            
        Returns:
            Natural frequency [Hz]
        """
        m = mass or self.params.equivalent_mass
        k = (stiffness or self.params.equivalent_stiffness) * 1000.0  # N/m
        
        if m <= 0 or k <= 0:
            return 0.0
        
        omega_n = np.sqrt(k / m)
        return omega_n / (2 * np.pi)

    def check_contact_loss(
        self,
        geometry: CamGeometry,
        params: Optional[SystemParameters] = None,
        omega: float = 1.0,
        n_points: int = 360
    ) -> Tuple[np.ndarray, bool]:
        """Check if contact loss occurs during the cam cycle.
        
        检查凸轮周期内是否发生脱离接触
        
        Contact is lost when the spring force cannot overcome the inertia force.
        This happens when: F_spring < F_inertia
        
        Args:
            geometry: Cam geometry
            params: System parameters
            omega: Cam angular velocity [rad/s]
            n_points: Number of points
            
        Returns:
            Tuple of (contact_status, has_loss)
            contact_status: 1 = in contact, 0 = lost contact
        """
        p = params or self.params
        angles = np.linspace(0, geometry.total_angle, n_points)
        contact_status = np.ones(n_points)
        has_loss = False
        
        calc = MotionLawCalculator(geometry.lift, omega)
        
        for i, theta in enumerate(angles):
            if theta < geometry.lift:
                result = calc.calculate(MotionLaw.CYCLOIDAL, geometry.lift, theta)
                accel = result.acceleration
            elif theta < geometry.lift + 90:
                accel = 0.0
            elif theta < 2 * geometry.lift + 90:
                result = calc.calculate(MotionLaw.CYCLOIDAL, geometry.lift,
                                       theta - geometry.lift - 90)
                accel = -result.acceleration
            else:
                accel = 0.0
            
            # Inertia force
            F_inertia = p.follower_mass * accel / 1000.0  # Convert to N
            
            # Net force (spring must overcome inertia)
            F_net = p.spring_preload - F_inertia
            if F_net <= 0:
                contact_status[i] = 0.0
                has_loss = True
        
        return contact_status, has_loss

    def calculate_dynamic_amplification(
        self,
        omega: float,
        natural_freq: Optional[float] = None,
        damping_ratio: Optional[float] = None
    ) -> float:
        """Calculate the dynamic amplification factor.
        
        计算动态放大系数
        
        D = 1 / sqrt((1 - r^2)^2 + (2*zeta*r)^2)
        where r = omega / omega_n
        
        Args:
            omega: Operating angular velocity [rad/s]
            natural_freq: Natural frequency [Hz]
            damping_ratio: Damping ratio
            
        Returns:
            Dynamic amplification factor
        """
        omega_n = (natural_freq or self.calculate_natural_frequency()) * 2 * np.pi
        zeta = damping_ratio or self.params.damping_ratio
        
        if omega_n <= 0:
            return 1.0
        
        r = omega / omega_n
        
        denom = np.sqrt((1 - r**2)**2 + (2 * zeta * r)**2)
        if denom < 1e-10:
            return 1.0
        
        return 1.0 / denom

    def get_dynamic_info(self) -> dict:
        """Get information about dynamic effects in cam mechanisms."""
        return {
            "dynamic_effects": "高速时动态效应变得重要",
            "english_effects": "Dynamic effects become important at high speeds",
            "key_factors": [
                "惯性力 (Inertia forces) - proportional to omega^2",
                "弹性振动 (Elastic vibration) - depends on stiffness and mass",
                "弹簧刚度 (Spring stiffness) - must maintain contact",
                "共振 (Resonance) - occurs when omega approaches omega_n"
            ],
            "design_recommendations": [
                "增加弹簧刚度 (Increase spring stiffness)",
                "减小从动件质量 (Reduce follower mass)",
                "避免工作频率接近固有频率 (Avoid operating near natural frequency)",
                "使用阻尼 (Add damping)",
                "选择平滑的运动规律 (Choose smooth motion laws)"
            ]
        }
