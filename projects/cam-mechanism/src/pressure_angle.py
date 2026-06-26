"""Pressure Angle Analysis Module.

This module provides tools for calculating and analyzing the pressure angle
of cam mechanisms. The pressure angle is a critical parameter that affects
the force transmission efficiency and the likelihood of jamming.

压力角分析模块
提供凸轮机构压力角计算和分析工具
"""

import numpy as np
from typing import Tuple, Optional
from .cam_profile import CamGeometry, CamProfileGenerator, FollowerType, FollowerMotion


class PressureAngleAnalyzer:
    """Analyzes pressure angles in cam mechanisms.
    
    凸轮机构压力角分析器
    
    The pressure angle (mu) is the angle between:
    - The direction of follower velocity
    - The normal to the cam profile at the contact point
    
    Key considerations:
    - Smaller pressure angle = better force transmission
    - If pressure angle approaches 90 degrees, the mechanism jams (自锁)
    - Maximum allowable pressure angle depends on application:
      * Translating roller follower: mu_max <= 30 degrees
      * Translating flat-foot follower: mu_max <= 30 degrees  
      * Oscillating roller follower: mu_max <= 35-40 degrees
    """

    def __init__(self, generator: Optional[CamProfileGenerator] = None):
        """Initialize the pressure angle analyzer.
        
        Args:
            generator: Optional cam profile generator for analytical calculations
        """
        self.generator = generator

    def calculate_pressure_angle_analytical(
        self,
        follower_motion: FollowerMotion,
        base_radius: float,
        lift: float,
        rise_angle: float,
        return_angle: float,
        omega: float = 1.0,
        offset: float = 0.0,
        link_length: float = 0.0,
        oscillation_angle: float = 0.0,
        n_points: int = 360
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate pressure angle using analytical formulas.
        
        使用解析公式计算压力角
        
        Returns:
            Tuple of (angles, pressure_angles, max_pressure_angles)
        """
        angles = np.linspace(0, rise_angle + 90 + return_angle + 90, n_points)
        pressure_angles = np.zeros(n_points)
        max_pressure_angles = np.zeros(n_points)
        
        if follower_motion == FollowerMotion.TRANSLATING:
            # For translating roller follower:
            # mu = arctan((ds/dtheta - e) / sqrt((rb + s)^2 - e^2))
            # where e is the offset
            for i, theta in enumerate(angles):
                if theta < rise_angle:
                    # Rise phase
                    x = theta / rise_angle
                    # ds/dtheta for different motion laws
                    ds_dx = self._ds_dx(rise_angle, x)
                    ds_dtheta = ds_dx * lift / rise_angle
                    denom = base_radius + 0  # simplified
                    if denom > 0:
                        pressure_angles[i] = np.degrees(np.arctan(
                            (ds_dtheta * omega / (np.pi / 180) - offset) / base_radius
                        ))
                elif theta < rise_angle + 90:
                    # Rise dwell - pressure angle is zero (no motion)
                    pressure_angles[i] = 0.0
                elif theta < rise_angle + 90 + return_angle:
                    # Return phase
                    ret_theta = theta - (rise_angle + 90)
                    x = ret_theta / return_angle
                    ds_dx = self._ds_dx(return_angle, x)
                    ds_dtheta = -ds_dx * lift / return_angle
                    pressure_angles[i] = np.degrees(np.arctan(
                        (ds_dtheta * omega / (np.pi / 180) - offset) / base_radius
                    ))
                else:
                    # Return dwell
                    pressure_angles[i] = 0.0
                    
                max_pressure_angles[i] = max(abs(pressure_angles[i]), 
                                            max_pressure_angles[max(0, i-1)] if i > 0 else 0.0)
                
        elif follower_motion == FollowerMotion.OFFSET_TRANSLATING:
            for i, theta in enumerate(angles):
                if theta < rise_angle:
                    x = theta / rise_angle
                    ds_dx = self._ds_dx(rise_angle, x)
                    ds_dtheta = ds_dx * lift / rise_angle
                    denom = np.sqrt((base_radius + lift * x) ** 2 - offset ** 2)
                    if denom > 1e-10:
                        pressure_angles[i] = np.degrees(np.arctan(
                            (ds_dtheta * omega / (np.pi / 180) - offset) / denom
                        ))
                elif theta < rise_angle + 90 + return_angle:
                    ret_theta = theta - (rise_angle + 90)
                    x = ret_theta / return_angle
                    ds_dx = self._ds_dx(return_angle, x)
                    ds_dtheta = -ds_dx * lift / return_angle
                    denom = np.sqrt((base_radius + lift * (1-x)) ** 2 - offset ** 2)
                    if denom > 1e-10:
                        pressure_angles[i] = np.degrees(np.arctan(
                            (ds_dtheta * omega / (np.pi / 180) - offset) / denom
                        ))
                else:
                    pressure_angles[i] = 0.0
        elif follower_motion == FollowerMotion.OSCILLATING:
            for i, theta in enumerate(angles):
                if theta < rise_angle:
                    x = theta / rise_angle
                    ds_dx = self._ds_dx(rise_angle, x)
                    ds_dtheta = ds_dx * oscillation_angle / rise_angle
                    # For oscillating follower
                    denom = link_length - base_radius
                    if denom > 1e-10:
                        pressure_angles[i] = np.degrees(np.arctan(
                            ds_dtheta * omega / (np.pi / 180) / denom
                        ))
                elif theta < rise_angle + 90 + return_angle:
                    ret_theta = theta - (rise_angle + 90)
                    x = ret_theta / return_angle
                    ds_dx = self._ds_dx(return_angle, x)
                    ds_dtheta = -ds_dx * oscillation_angle / return_angle
                    denom = link_length - base_radius
                    if denom > 1e-10:
                        pressure_angles[i] = np.degrees(np.arctan(
                            ds_dtheta * omega / (np.pi / 180) / denom
                        ))
                else:
                    pressure_angles[i] = 0.0
                    
                max_pressure_angles[i] = max(abs(pressure_angles[i]),
                                            max_pressure_angles[max(0, i-1)] if i > 0 else 0.0)

        return angles, pressure_angles, max_pressure_angles

    def _ds_dx(self, phi: float, x: float) -> float:
        """Get ds/dx for a given normalized position."""
        eps = 1e-6
        x1 = x + eps
        x2 = x - eps
        # Simple approximation for different motion laws
        if x < 0 or x > 1:
            return 0.0
        # Approximate based on position
        if x < 0.01:
            return 2 * x
        elif x > 0.99:
            return 2 * (1 - x)
        return 1.0  # Default approximation

    def check_pressure_angle_limit(
        self,
        pressure_angles: np.ndarray,
        max_allowed: float = 30.0,
        follower_type: FollowerType = FollowerType.ROLLER
    ) -> dict:
        """Check if pressure angles are within acceptable limits.
        
        检查压力角是否在允许范围内
        
        Args:
            pressure_angles: Array of pressure angles in degrees
            max_allowed: Maximum allowable pressure angle in degrees
            follower_type: Type of follower (defaults to roller)
            
        Returns:
            Dictionary with analysis results
        """
        max_pa = np.max(np.abs(pressure_angles))
        mean_pa = np.mean(np.abs(pressure_angles))
        
        # Determine if the design is acceptable
        is_acceptable = max_pa <= max_allowed
        
        return {
            "max_pressure_angle": float(max_pa),
            "mean_pressure_angle": float(mean_pa),
            "max_allowed": max_allowed,
            "is_acceptable": is_acceptable,
            "margin": float(max_allowed - max_pa),
            "violation_count": int(np.sum(np.abs(pressure_angles) > max_allowed))
        }

    def get_pressure_angle_info(self) -> dict:
        """Get information about pressure angles in cam mechanisms.
        
        Returns descriptive information about pressure angles.
        """
        return {
            "definition": "压力角是从动件受力方向与受力点速度方向之间的夹角",
            "english_definition": "Angle between the direction of follower motion "
                                  "and the normal to the cam profile at the contact point",
            "importance": "压力角越小，传力性能越好。压力角过大会导致自锁",
            "english_importance": "Smaller pressure angle means better force transmission. "
                                  "Excessive pressure angle can cause jamming (自锁)",
            "typical_limits": {
                "translating_roller": "<= 30 degrees",
                "translating_flat_foot": "<= 30 degrees",
                "oscillating_roller": "<= 35-40 degrees"
            }
        }
