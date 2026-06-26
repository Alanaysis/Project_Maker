"""Cam Profile Generation Module.

This module implements cam profile generation for different types of cam-follower
systems. It handles the geometric computation of cam profiles based on the
follower type and motion law.

凸轮轮廓生成模块
实现不同类型的凸轮-从动件系统的凸轮轮廓生成
"""

import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple
from .motion_laws import MotionLaw, MotionLawCalculator, MotionResult


class FollowerType(Enum):
    """Types of followers in cam mechanisms.
    
    从动件类型
    """
    ROLLER = "roller"           # 滚子从动件
    FLAT_FOOT = "flat_foot"     # 平底从动件
    PIN = "pin"                 # 尖顶从动件


class FollowerMotion(Enum):
    """Types of follower motion relative to the cam.
    
    从动件运动方式
    """
    TRANSLATING = "translating"       # 对心移动从动件
    OFFSET_TRANSLATING = "offset"      # 偏置移动从动件
    OSCILLATING = "oscillating"       # 摆动从动件


@dataclass
class CamGeometry:
    """Stores cam geometry parameters.
    
    存储凸轮几何参数
    """
    # Base circle
    base_radius: float          # 基圆半径 rb [mm]
    
    # Cam profile
    profile_x: np.ndarray       # 凸轮轮廓 X 坐标
    profile_y: np.ndarray       # 凸轮轮廓 Y 坐标
    
    # Follower data
    follower_type: FollowerType
    follower_motion: FollowerMotion
    
    # Operating parameters
    lift: float                 # 升程 [mm]
    total_angle: float          # 总转角 [degrees]
    
    # Additional parameters
    roller_radius: float = 0.0  # 滚子半径 rr [mm] (for roller follower)
    offset: float = 0.0         # 偏置距 e [mm] (for offset translating follower)
    link_length: float = 0.0    # 摆杆长度 L [mm] (for oscillating follower)


class CamProfileGenerator:
    """Generates cam profiles for various cam-follower configurations.
    
    凸轮轮廓生成器
    根据不同的凸轮-从动件配置生成凸轮轮廓
    """

    def __init__(self, base_radius: float, roller_radius: float = 0.0):
        """Initialize the cam profile generator.
        
        Args:
            base_radius: Base circle radius of the cam (凸轮基圆半径) in mm
            roller_radius: Roller radius for roller followers (滚子半径) in mm
        """
        self.base_radius = base_radius
        self.roller_radius = roller_radius

    def generate_profile(
        self,
        follower_type: FollowerType,
        follower_motion: FollowerMotion,
        motion_law: MotionLaw,
        lift: float,
        rise_angle: float,
        rise_dwell_angle: float,
        return_angle: float,
        return_dwell_angle: float,
        omega: float = 1.0,
        offset: float = 0.0,
        link_length: float = 0.0,
        oscillation_angle: float = 0.0,
        initial_angle: float = 0.0,
        n_points: int = 360
    ) -> CamGeometry:
        """Generate the complete cam profile.
        
        Args:
            follower_type: Type of follower (从动件类型)
            follower_motion: Type of follower motion (从动件运动方式)
            motion_law: Motion law for rise and return (运动规律)
            lift: Total lift during rise (升程) in mm
            rise_angle: Cam angle for rise phase (升程阶段角度) in degrees
            rise_dwell_angle: Cam angle for rise dwell (升程休止角度) in degrees
            return_angle: Cam angle for return phase (回程阶段角度) in degrees
            return_dwell_angle: Cam angle for return dwell (回程休止角度) in degrees
            omega: Cam angular velocity (角速度) in rad/s
            offset: Offset distance for offset translating follower (偏置距) in mm
            link_length: Length of oscillating follower link (摆杆长度) in mm
            oscillation_angle: Total oscillation angle of follower (摆杆摆角) in degrees
            initial_angle: Initial angle of the cam (初始安装角) in degrees
            n_points: Number of points for profile discretization (采样点数)
            
        Returns:
            CamGeometry with computed profile coordinates
        """
        if follower_motion == FollowerMotion.OSCILLATING:
            return self._generate_oscillating_profile(
                motion_law, lift, rise_angle, rise_dwell_angle,
                return_angle, return_dwell_angle, omega,
                link_length, oscillation_angle, initial_angle, n_points
            )
        elif follower_motion == FollowerMotion.OFFSET_TRANSLATING:
            return self._generate_offset_translating_profile(
                follower_type, motion_law, lift, rise_angle, rise_dwell_angle,
                return_angle, return_dwell_angle, omega, offset, initial_angle, n_points
            )
        else:
            return self._generate_translating_profile(
                follower_type, motion_law, lift, rise_angle, rise_dwell_angle,
                return_angle, return_dwell_angle, omega, initial_angle, n_points
            )

    def _generate_translating_profile(
        self,
        follower_type: FollowerType,
        motion_law: MotionLaw,
        lift: float,
        rise_angle: float,
        rise_dwell_angle: float,
        return_angle: float,
        return_dwell_angle: float,
        omega: float,
        initial_angle: float,
        n_points: int
    ) -> CamGeometry:
        """Generate profile for a translating (reciprocating) follower.
        
        生成移动从动件凸轮轮廓
        
        For a translating follower:
        - The follower moves along a straight line passing through the cam center
        - The cam profile is computed by inverting the motion (fixing the follower,
          rotating the cam in the opposite direction)
        """
        total_angle = rise_angle + rise_dwell_angle + return_angle + return_dwell_angle
        angles = np.linspace(0, total_angle, n_points)
        
        # Compute follower displacement at each angle
        displacements = np.zeros(n_points)
        calc = MotionLawCalculator(lift, omega)
        
        for i, theta in enumerate(angles):
            if theta < rise_angle:
                # 升程阶段 (Rise phase)
                result = calc.calculate(motion_law, rise_angle, theta)
                displacements[i] = result.displacement
            elif theta < rise_angle + rise_dwell_angle:
                # 升程休止 (Rise dwell)
                displacements[i] = lift
            elif theta < rise_angle + rise_dwell_angle + return_angle:
                # 回程阶段 (Return phase)
                return_theta = theta - (rise_angle + rise_dwell_angle)
                result = calc.calculate(motion_law, return_angle, return_theta)
                displacements[i] = lift - result.displacement
            else:
                # 回程休止 (Return dwell)
                displacements[i] = 0.0

        # Generate cam profile coordinates
        # For a translating follower, the profile is generated by:
        # 1. Starting with the base circle
        # 2. Adding the follower displacement in the radial direction
        # 3. Rotating by the negative of the cam angle (inversion principle)
        r_base = self.base_radius
        profile_x = np.zeros(n_points)
        profile_y = np.zeros(n_points)
        
        if follower_type == FollowerType.ROLLER:
            # 滚子从动件 (Roller follower)
            # The pitch curve is at distance (rb + s) from the center
            # The actual profile is offset by the roller radius
            for i, (theta, s) in enumerate(zip(angles, displacements)):
                theta_rad = np.radians(theta + initial_angle)
                r = r_base + s
                # Pitch curve point
                px = r * np.sin(theta_rad)
                py = r * np.cos(theta_rad)
                # Apply roller offset (normal direction)
                nx = np.cos(theta_rad)
                ny = np.sin(theta_rad)
                profile_x[i] = px - self.roller_radius * nx
                profile_y[i] = py - self.roller_radius * ny
        elif follower_type == FollowerType.FLAT_FOOT:
            # 平底从动件 (Flat-foot follower)
            # For a flat-foot follower, the profile depends on the derivative
            # of the displacement
            calc = MotionLawCalculator(lift, omega)
            for i, (theta, s) in enumerate(zip(angles, displacements)):
                theta_rad = np.radians(theta + initial_angle)
                # Get velocity for flat-foot calculation
                if theta < rise_angle:
                    result = calc.calculate(motion_law, rise_angle, theta)
                    ds_dtheta = result.velocity * rise_angle / (omega * np.pi / 180.0) / lift
                elif theta < rise_angle + rise_dwell_angle:
                    ds_dtheta = 0.0
                elif theta < rise_angle + rise_dwell_angle + return_angle:
                    return_theta = theta - (rise_angle + rise_dwell_angle)
                    result = calc.calculate(motion_law, return_angle, return_theta)
                    ds_dtheta = result.velocity * return_angle / (omega * np.pi / 180.0) / lift
                else:
                    ds_dtheta = 0.0
                
                # Flat-foot follower profile
                # x = (rb + s) * sin(theta) + ds/dtheta * cos(theta)
                # y = (rb + s) * cos(theta) - ds/dtheta * sin(theta)
                r = r_base + s
                profile_x[i] = r * np.sin(theta_rad) + ds_dtheta * np.cos(theta_rad)
                profile_y[i] = r * np.cos(theta_rad) - ds_dtheta * np.sin(theta_rad)
        else:
            # 尖顶从动件 (Pin/pointed follower)
            for i, (theta, s) in enumerate(zip(angles, displacements)):
                theta_rad = np.radians(theta + initial_angle)
                r = r_base + s
                profile_x[i] = r * np.sin(theta_rad)
                profile_y[i] = r * np.cos(theta_rad)

        return CamGeometry(
            base_radius=r_base,
            profile_x=profile_x,
            profile_y=profile_y,
            follower_type=follower_type,
            follower_motion=FollowerMotion.TRANSLATING,
            lift=lift,
            total_angle=total_angle,
            roller_radius=self.roller_radius
        )

    def _generate_offset_translating_profile(
        self,
        follower_type: FollowerType,
        motion_law: MotionLaw,
        lift: float,
        rise_angle: float,
        rise_dwell_angle: float,
        return_angle: float,
        return_dwell_angle: float,
        omega: float,
        offset: float,
        initial_angle: float,
        n_points: int
    ) -> CamGeometry:
        """Generate profile for an offset translating follower.
        
        生成偏置移动从动件凸轮轮廓
        
        The follower path is offset from the cam center by distance e.
        """
        total_angle = rise_angle + rise_dwell_angle + return_angle + return_dwell_angle
        angles = np.linspace(0, total_angle, n_points)
        
        displacements = np.zeros(n_points)
        calc = MotionLawCalculator(lift, omega)
        
        for i, theta in enumerate(angles):
            if theta < rise_angle:
                result = calc.calculate(motion_law, rise_angle, theta)
                displacements[i] = result.displacement
            elif theta < rise_angle + rise_dwell_angle:
                displacements[i] = lift
            elif theta < rise_angle + rise_dwell_angle + return_angle:
                return_theta = theta - (rise_angle + rise_dwell_angle)
                result = calc.calculate(motion_law, return_angle, return_theta)
                displacements[i] = lift - result.displacement
            else:
                displacements[i] = 0.0

        r_base = self.base_radius
        profile_x = np.zeros(n_points)
        profile_y = np.zeros(n_points)
        
        if follower_type == FollowerType.ROLLER:
            for i, (theta, s) in enumerate(zip(angles, displacements)):
                theta_rad = np.radians(theta + initial_angle)
                
                # Offset translating roller follower
                # The offset changes the geometry of the profile
                r = np.sqrt((r_base + s) ** 2 - offset ** 2)
                phi = np.arcsin(offset / (r_base + s)) if (r_base + s) > abs(offset) else 0.0
                
                # Pitch curve
                px = r * np.sin(theta_rad + phi) + offset * np.cos(theta_rad)
                py = r * np.cos(theta_rad + phi) - offset * np.sin(theta_rad)
                
                # Normal direction for roller offset
                nx = np.cos(theta_rad)
                ny = np.sin(theta_rad)
                profile_x[i] = px - self.roller_radius * nx
                profile_y[i] = py - self.roller_radius * ny
                
        elif follower_type == FollowerType.FLAT_FOOT:
            calc = MotionLawCalculator(lift, omega)
            for i, (theta, s) in enumerate(zip(angles, displacements)):
                theta_rad = np.radians(theta + initial_angle)
                
                # Offset flat-foot follower
                r_eff = np.sqrt((r_base + s) ** 2 - offset ** 2)
                phi = np.arcsin(offset / (r_base + s)) if (r_base + s) > abs(offset) else 0.0
                
                if theta < rise_angle:
                    result = calc.calculate(motion_law, rise_angle, theta)
                    ds_dtheta = result.velocity * rise_angle / (omega * np.pi / 180.0) / lift
                elif theta < rise_angle + rise_dwell_angle:
                    ds_dtheta = 0.0
                elif theta < rise_angle + rise_dwell_angle + return_angle:
                    return_theta = theta - (rise_angle + rise_dwell_angle)
                    result = calc.calculate(motion_law, return_angle, return_theta)
                    ds_dtheta = result.velocity * return_angle / (omega * np.pi / 180.0) / lift
                else:
                    ds_dtheta = 0.0
                
                profile_x[i] = (r_eff + ds_dtheta) * np.sin(theta_rad + phi) + offset * np.cos(theta_rad)
                profile_y[i] = (r_eff + ds_dtheta) * np.cos(theta_rad + phi) - offset * np.sin(theta_rad)
        else:
            for i, (theta, s) in enumerate(zip(angles, displacements)):
                theta_rad = np.radians(theta + initial_angle)
                r = np.sqrt((r_base + s) ** 2 - offset ** 2)
                phi = np.arcsin(offset / (r_base + s)) if (r_base + s) > abs(offset) else 0.0
                profile_x[i] = r * np.sin(theta_rad + phi) + offset * np.cos(theta_rad)
                profile_y[i] = r * np.cos(theta_rad + phi) - offset * np.sin(theta_rad)

        return CamGeometry(
            base_radius=r_base,
            profile_x=profile_x,
            profile_y=profile_y,
            follower_type=follower_type,
            follower_motion=FollowerMotion.OFFSET_TRANSLATING,
            lift=lift,
            total_angle=total_angle,
            roller_radius=self.roller_radius,
            offset=offset
        )

    def _generate_oscillating_profile(
        self,
        motion_law: MotionLaw,
        lift: float,
        rise_angle: float,
        rise_dwell_angle: float,
        return_angle: float,
        return_dwell_angle: float,
        omega: float,
        link_length: float,
        oscillation_angle: float,
        initial_angle: float,
        n_points: int
    ) -> CamGeometry:
        """Generate profile for an oscillating (pivoted) follower.
        
        生成摆动从动件凸轮轮廓
        
        The oscillating follower pivots about a fixed point at distance L from
        the cam center. The follower angular displacement follows the motion law.
        """
        total_angle = rise_angle + rise_dwell_angle + return_angle + return_dwell_angle
        angles = np.linspace(0, total_angle, n_points)
        
        # Calculate follower angular displacement
        follower_angles = np.zeros(n_points)
        calc = MotionLawCalculator(oscillation_angle, omega)
        
        for i, theta in enumerate(angles):
            if theta < rise_angle:
                result = calc.calculate(motion_law, rise_angle, theta)
                follower_angles[i] = result.displacement
            elif theta < rise_angle + rise_dwell_angle:
                follower_angles[i] = oscillation_angle
            elif theta < rise_angle + rise_dwell_angle + return_angle:
                return_theta = theta - (rise_angle + rise_dwell_angle)
                result = calc.calculate(motion_law, return_angle, return_theta)
                follower_angles[i] = oscillation_angle - result.displacement
            else:
                follower_angles[i] = 0.0

        # Generate cam profile for oscillating roller follower
        # The follower pivot is located at distance L from cam center
        r_base = self.base_radius
        profile_x = np.zeros(n_points)
        profile_y = np.zeros(n_points)
        
        # For oscillating follower, we need to find the cam profile that
        # would produce the desired follower motion
        for i, (theta, phi_f) in enumerate(zip(angles, follower_angles)):
            theta_rad = np.radians(theta + initial_angle)
            phi_rad = np.radians(phi_f)
            
            # Distance from cam center to follower pivot
            L = link_length
            
            # Position of the follower roller center in the inverted system
            # The follower angle is measured from the line connecting cam center to pivot
            # Initial position of roller center
            init_angle = np.arccos((L ** 2 + r_base ** 2 - r_base ** 2) / (2 * L * r_base))
            
            # For oscillating follower, the profile generation is more complex
            # We use the inversion method: fix the follower, rotate the cam
            
            # Distance from pivot to roller center
            dist_to_roller = np.sqrt(L ** 2 + r_base ** 2 - 2 * L * r_base * np.cos(np.pi/2 - phi_rad))
            
            # Angle from pivot to roller center
            angle_from_pivot = np.arcsin(r_base * np.sin(np.pi/2 - phi_rad) / dist_to_roller)
            
            # Convert to cam-centered coordinates
            # The pivot is at (0, L) in the cam frame
            # Roller center position relative to pivot
            roller_x_rel = dist_to_roller * np.sin(angle_from_pivot)
            roller_y_rel = dist_to_roller * np.cos(angle_from_pivot)
            
            # Inverted rotation (cam rotates by theta, so we rotate by -theta)
            rot_x = roller_x_rel * np.cos(theta_rad) + roller_y_rel * np.sin(theta_rad)
            rot_y = -roller_x_rel * np.sin(theta_rad) + roller_y_rel * np.cos(theta_rad)
            
            # Apply roller offset
            nx = np.cos(theta_rad)
            ny = np.sin(theta_rad)
            profile_x[i] = rot_x - self.roller_radius * nx
            profile_y[i] = rot_y - self.roller_radius * ny

        return CamGeometry(
            base_radius=r_base,
            profile_x=profile_x,
            profile_y=profile_y,
            follower_type=FollowerType.ROLLER,
            follower_motion=FollowerMotion.OSCILLATING,
            lift=lift,
            total_angle=total_angle,
            roller_radius=self.roller_radius,
            link_length=link_length
        )

    def calculate_pressure_angle(
        self,
        geometry: CamGeometry,
        n_points: int = 360
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate the pressure angle along the cam profile.
        
        计算凸轮轮廓上的压力角
        
        The pressure angle is the angle between the direction of follower motion
        and the normal to the cam profile at the contact point.
        
        A smaller pressure angle is better (more efficient force transmission).
        Maximum allowable pressure angle depends on the application:
        - Translating roller follower: typically <= 30 degrees
        - Translating flat-foot follower: typically <= 30 degrees
        - Oscillating roller follower: typically <= 35-40 degrees
        
        Args:
            geometry: Cam geometry from profile generation
            n_points: Number of points for calculation
            
        Returns:
            Tuple of (angles_degrees, pressure_angles_degrees)
        """
        angles = np.linspace(0, geometry.total_angle, n_points)
        pressure_angles = np.zeros(n_points)
        
        if geometry.follower_motion == FollowerMotion.TRANSLATING:
            for i, theta in enumerate(angles):
                # Calculate pressure angle using numerical differentiation
                if i > 0 and i < n_points - 1:
                    dx = geometry.profile_x[i + 1] - geometry.profile_x[i - 1]
                    dy = geometry.profile_y[i + 1] - geometry.profile_y[i - 1]
                    
                    # Normal to the profile
                    normal_x = dy
                    normal_y = -dx
                    
                    # Normalize
                    norm = np.sqrt(normal_x ** 2 + normal_y ** 2)
                    if norm > 1e-10:
                        normal_x /= norm
                        normal_y /= norm
                    
                    # For a vertical translating follower, the force direction is vertical
                    # Pressure angle is the angle between normal and vertical direction
                    cos_angle = abs(normal_y)
                    cos_angle = np.clip(cos_angle, -1.0, 1.0)
                    pressure_angles[i] = np.degrees(np.arccos(cos_angle))
                    
                    # Adjust sign based on geometry
                    if geometry.offset != 0:
                        center_x = geometry.profile_x[i]
                        if (normal_x > 0 and center_x > 0) or (normal_x < 0 and center_x < 0):
                            pressure_angles[i] = -pressure_angles[i]
                            
        elif geometry.follower_motion == FollowerMotion.OSCILLATING:
            for i, theta in enumerate(angles):
                if i > 0 and i < n_points - 1:
                    dx = geometry.profile_x[i + 1] - geometry.profile_x[i - 1]
                    dy = geometry.profile_y[i + 1] - geometry.profile_y[i - 1]
                    
                    normal_x = dy
                    normal_y = -dx
                    
                    norm = np.sqrt(normal_x ** 2 + normal_y ** 2)
                    if norm > 1e-10:
                        normal_x /= norm
                        normal_y /= norm
                    
                    # For oscillating follower, the direction is tangential to the arc
                    theta_rad = np.radians(theta)
                    tangent_x = np.cos(theta_rad)
                    tangent_y = -np.sin(theta_rad)
                    
                    cos_angle = abs(normal_x * tangent_x + normal_y * tangent_y)
                    cos_angle = np.clip(cos_angle, -1.0, 1.0)
                    pressure_angles[i] = np.degrees(np.arccos(cos_angle))
        else:
            # Flat-foot or pin follower - pressure angle calculation differs
            for i, theta in enumerate(angles):
                if i > 0 and i < n_points - 1:
                    dx = geometry.profile_x[i + 1] - geometry.profile_x[i - 1]
                    dy = geometry.profile_y[i + 1] - geometry.profile_y[i - 1]
                    
                    normal_x = dy
                    normal_y = -dx
                    
                    norm = np.sqrt(normal_x ** 2 + normal_y ** 2)
                    if norm > 1e-10:
                        normal_x /= norm
                        normal_y /= norm
                    
                    cos_angle = abs(normal_y)
                    cos_angle = np.clip(cos_angle, -1.0, 1.0)
                    pressure_angles[i] = np.degrees(np.arccos(cos_angle))

        return angles, pressure_angles

    def calculate_curvature(
        self,
        geometry: CamGeometry
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate the radius of curvature of the cam profile.
        
        计算凸轮轮廓的曲率半径
        
        The curvature radius must be positive to avoid undercutting (轮廓失真).
        For a roller follower, the condition is: rho_min > rr (曲率半径 > 滚子半径)
        
        Args:
            geometry: Cam geometry from profile generation
            
        Returns:
            Tuple of (curvature_radius, curvature_center_x, curvature_center_y)
        """
        n = len(geometry.profile_x)
        curvature_radius = np.zeros(n)
        center_x = np.zeros(n)
        center_y = np.zeros(n)
        
        # Use numerical differentiation to compute curvature
        dx = np.zeros(n)
        dy = np.zeros(n)
        d2x = np.zeros(n)
        d2y = np.zeros(n)
        
        # First derivatives
        for i in range(1, n - 1):
            dx[i] = (geometry.profile_x[i + 1] - geometry.profile_x[i - 1]) / 2.0
            dy[i] = (geometry.profile_y[i + 1] - geometry.profile_y[i - 1]) / 2.0
        
        # Second derivatives
        for i in range(1, n - 1):
            d2x[i] = (geometry.profile_x[i + 1] - 2 * geometry.profile_x[i] + geometry.profile_x[i - 1])
            d2y[i] = (geometry.profile_y[i + 1] - 2 * geometry.profile_y[i] + geometry.profile_y[i - 1])
        
        # Handle boundaries
        dx[0] = geometry.profile_x[1] - geometry.profile_x[0]
        dy[0] = geometry.profile_y[1] - geometry.profile_y[0]
        d2x[0] = geometry.profile_x[2] - 2 * geometry.profile_x[1] + geometry.profile_x[0]
        d2y[0] = geometry.profile_y[2] - 2 * geometry.profile_y[1] + geometry.profile_y[0]
        
        dx[-1] = geometry.profile_x[-1] - geometry.profile_x[-2]
        dy[-1] = geometry.profile_y[-1] - geometry.profile_y[-2]
        d2x[-1] = geometry.profile_x[-1] - 2 * geometry.profile_x[-2] + geometry.profile_x[-3]
        d2y[-1] = geometry.profile_y[-1] - 2 * geometry.profile_y[-2] + geometry.profile_y[-3]
        
        # Compute curvature radius
        for i in range(n):
            denom = dx[i] ** 2 + dy[i] ** 2
            if denom > 1e-10:
                kappa = abs(dx[i] * d2y[i] - dy[i] * d2x[i]) / (denom ** 1.5)
                curvature_radius[i] = 1.0 / kappa if kappa > 1e-10 else 1e10
                
                # Center of curvature
                if abs(dy[i]) > 1e-10:
                    center_x[i] = geometry.profile_x[i] - (dx[i] ** 2 + dy[i] ** 2) * dy[i] / (dx[i] ** 2 + dy[i] ** 2 + 1e-10)
                    center_y[i] = geometry.profile_y[i] + (dx[i] ** 2 + dy[i] ** 2) * dx[i] / (dx[i] ** 2 + dy[i] ** 2 + 1e-10)
                else:
                    center_x[i] = geometry.profile_x[i]
                    center_y[i] = geometry.profile_y[i]
            else:
                curvature_radius[i] = 1e10
                center_x[i] = geometry.profile_x[i]
                center_y[i] = geometry.profile_y[i]
        
        return curvature_radius, center_x, center_y
