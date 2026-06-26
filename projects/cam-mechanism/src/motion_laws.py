"""Follower Motion Laws Module.

This module implements various motion laws for cam follower systems.
Motion laws define how the follower displacement, velocity, and acceleration
vary with the cam rotation angle during each phase of motion.

从动件运动规律模块
实现凸轮从动件的各种运动规律
"""

import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MotionLaw(Enum):
    """Enumeration of available motion laws for cam followers.
    
    运动规律枚举
    """
    UNIFORM = "uniform"           # 等速运动
    PARABOLIC = "parabolic"       # 等加速/等减速运动
    CYCLOIDAL = "cycloidal"       # 摆线运动
    POLYNOMIAL_3 = "polynomial_3" # 三次多项式
    POLYNOMIAL_4 = "polynomial_4" # 四次多项式
    POLYNOMIAL_5 = "polynomial_5" # 五次多项式
    SINUSOIDAL = "sinusoidal"     # 简谐运动
    MODIFIED_SINE = "modified_sine"      # 改良正弦运动
    MODIFIED_TRAP = "modified_trap"      # 改良梯形运动


@dataclass
class MotionResult:
    """Stores the motion analysis results for a given angle.
    
    存储运动分析结果
    """
    displacement: float      # 位移 s [mm]
    velocity: float          # 速度 v [mm/s]
    acceleration: float      # 加速度 a [mm/s^2]
    jerk: float              # 跃度 j [mm/s^3]


class MotionLawCalculator:
    """Calculates follower motion parameters for different motion laws.
    
    运动规律计算器
    根据凸轮转角计算从动件的位移、速度、加速度和跃度
    
    The cam rotates at constant angular velocity omega.
    The follower motion is divided into phases:
    - Rise (升程): follower moves from minimum to maximum displacement
    - Dwell (近休止): follower holds at minimum displacement
    - Return (回程): follower moves from maximum to minimum displacement
    - Dwell (远休止): follower holds at maximum displacement
    """

    def __init__(self, lift: float, omega: float = 1.0):
        """Initialize the motion law calculator.
        
        Args:
            lift: Total follower lift (总升程) in mm
            omega: Cam angular velocity (凸轮角速度) in rad/s
        """
        self.lift = lift        # 升程 [mm]
        self.omega = omega      # 角速度 [rad/s]

    def calculate(self, law: MotionLaw, phase_angle: float, theta: float) -> MotionResult:
        """Calculate motion parameters for a given motion law.
        
        Args:
            law: The motion law to use
            phase_angle: Total angle of the current phase (当前阶段总角度) in degrees
            theta: Current cam rotation angle within the phase (当前阶段内的转角) in degrees
            
        Returns:
            MotionResult with displacement, velocity, acceleration, and jerk
        """
        # Normalize theta to the range [0, phase_angle]
        theta = np.clip(theta, 0, phase_angle)
        
        # Calculate normalized position within the phase [0, 1]
        # This represents how far through the phase we are
        x = theta / phase_angle if phase_angle > 0 else 0.0

        # Calculate based on the selected motion law
        s, v, a, j = self._compute_motion(law, x, phase_angle)

        # Scale displacement by lift
        s *= self.lift

        # Scale velocity by omega (since theta is in degrees, convert to rad/s scaling)
        # v = ds/dt = ds/dtheta * dtheta/dt = ds/dtheta * omega
        # But x = theta/phi, so ds/dx = ds/dtheta * phi
        # Therefore v = (ds/dx) * (omega / phi) * (180/pi) to handle degree conversion
        scale_factor = self.omega * np.pi / (180.0 * phase_angle) if phase_angle > 0 else 0.0
        v *= scale_factor * self.lift

        # Scale acceleration: a = d²s/dt² = d²s/dx² * (omega/phi)²
        accel_scale = (self.omega * np.pi / (180.0 * phase_angle)) ** 2
        a *= accel_scale * self.lift

        # Scale jerk: j = d³s/dt³ = d³s/dx³ * (omega/phi)³
        jerk_scale = (self.omega * np.pi / (180.0 * phase_angle)) ** 3
        j *= jerk_scale * self.lift

        return MotionResult(displacement=s, velocity=v, acceleration=a, jerk=j)

    def _compute_motion(self, law: MotionLaw, x: float, phi: float):
        """Compute displacement, velocity, acceleration, and jerk for a given law.
        
        Internal computation using normalized position x in [0, 1].
        
        Returns:
            Tuple of (s_norm, ds_dx, d2s_dx2, d3s_dx3)
        """
        if x < 0 or x > 1:
            return 0.0, 0.0, 0.0, 0.0

        if law == MotionLaw.UNIFORM:
            return self._uniform_motion(x)
        elif law == MotionLaw.PARABOLIC:
            return self._parabolic_motion(x)
        elif law == MotionLaw.CYCLOIDAL:
            return self._cycloidal_motion(x)
        elif law == MotionLaw.POLYNOMIAL_3:
            return self._polynomial_3(x)
        elif law == MotionLaw.POLYNOMIAL_4:
            return self._polynomial_4(x)
        elif law == MotionLaw.POLYNOMIAL_5:
            return self._polynomial_5(x)
        elif law == MotionLaw.SINUSOIDAL:
            return self._sinusoidal_motion(x)
        elif law == MotionLaw.MODIFIED_SINE:
            return self._modified_sine_motion(x)
        elif law == MotionLaw.MODIFIED_TRAP:
            return self._modified_trap_motion(x)
        else:
            return 0.0, 0.0, 0.0, 0.0

    # ---- Motion Law Implementations ----

    @staticmethod
    def _uniform_motion(x: float):
        """等速运动 (Uniform motion / Constant velocity)
        
        Displacement: s = h * theta / phi
        Velocity: constant
        Acceleration: zero (except at boundaries where it's infinite - causes impact)
        
        Simple but causes rigid impact at start/end of motion.
        Only suitable for low-speed applications.
        """
        s = x
        ds_dx = 1.0
        d2s_dx2 = 0.0
        d3s_dx3 = 0.0
        return s, ds_dx, d2s_dx2, d3s_dx3

    @staticmethod
    def _parabolic_motion(x: float):
        """等加速/等减速运动 (Parabolic motion / Constant acceleration)
        
        Divided into two halves:
        - First half: constant positive acceleration
        - Second half: constant negative acceleration
        
        Finite acceleration but discontinuous acceleration at boundaries
        causes mild impact (soft impact).
        """
        if x <= 0.5:
            # 加速段 (Acceleration phase)
            s = 2.0 * x ** 2
            ds_dx = 4.0 * x
            d2s_dx2 = 4.0
            d3s_dx3 = 0.0
        else:
            # 减速段 (Deceleration phase)
            x2 = x - 0.5
            s = 1.0 - 2.0 * (1.0 - x) ** 2
            ds_dx = 4.0 * (1.0 - x)
            d2s_dx2 = -4.0
            d3s_dx3 = 0.0
        return s, ds_dx, d2s_dx2, d3s_dx3

    def _cycloidal_motion(self, x: float):
        """摆线运动 (Cycloidal motion)
        
        Displacement follows a cycloid curve: s = h * (theta/phi - sin(2*pi*theta/phi) / (2*pi))
        
        Smooth acceleration profile with zero velocity and acceleration at boundaries.
        No impact - suitable for medium to high speed applications.
        Maximum acceleration is moderate.
        """
        s = x - np.sin(2.0 * np.pi * x) / (2.0 * np.pi)
        ds_dx = 1.0 - np.cos(2.0 * np.pi * x)
        d2s_dx2 = 2.0 * np.pi * np.sin(2.0 * np.pi * x)
        d3s_dx3 = 4.0 * np.pi ** 2 * np.cos(2.0 * np.pi * x)
        return s, ds_dx, d2s_dx2, d3s_dx3

    @staticmethod
    def _polynomial_3(x: float):
        """三次多项式运动 (Third-order polynomial motion)
        
        s = 3x² - 2x³
        
        Boundary conditions: s(0)=0, s(1)=1, ds/dx(0)=0, ds/dx(1)=0
        Smooth start and end but acceleration is discontinuous at boundaries.
        """
        s = 3.0 * x ** 2 - 2.0 * x ** 3
        ds_dx = 6.0 * x - 6.0 * x ** 2
        d2s_dx2 = 6.0 - 12.0 * x
        d3s_dx3 = -12.0
        return s, ds_dx, d2s_dx2, d3s_dx3

    @staticmethod
    def _polynomial_4(x: float):
        """四次多项式运动 (Fourth-order polynomial motion)
        
        s = 6x⁵ - 15x⁴ + 10x³
        
        Boundary conditions: s(0)=0, s(1)=1, ds/dx(0)=0, ds/dx(1)=0,
        d²s/dx²(0)=0, d²s/dx²(1)=0
        Smooth acceleration at boundaries.
        """
        s = 6.0 * x ** 5 - 15.0 * x ** 4 + 10.0 * x ** 3
        ds_dx = 30.0 * x ** 4 - 60.0 * x ** 3 + 30.0 * x ** 2
        d2s_dx2 = 120.0 * x ** 3 - 180.0 * x ** 2 + 60.0 * x
        d3s_dx3 = 360.0 * x ** 2 - 360.0 * x + 60.0
        return s, ds_dx, d2s_dx2, d3s_dx3

    @staticmethod
    def _polynomial_5(x: float):
        """五次多项式运动 (Fifth-order polynomial motion)
        
        s = 10x³ - 15x⁴ + 6x⁵
        
        Boundary conditions: s(0)=0, s(1)=1, ds/dx(0)=0, ds/dx(1)=0,
        d²s/dx²(0)=0, d²s/dx²(1)=0, d³s/dx³(0)=0, d³s/dx³(1)=0
        All derivatives continuous at boundaries - best for high speed.
        """
        s = 10.0 * x ** 3 - 15.0 * x ** 4 + 6.0 * x ** 5
        ds_dx = 30.0 * x ** 2 - 60.0 * x ** 3 + 30.0 * x ** 4
        d2s_dx2 = 60.0 * x - 180.0 * x ** 2 + 120.0 * x ** 3
        d3s_dx3 = 60.0 - 360.0 * x + 360.0 * x ** 2
        return s, ds_dx, d2s_dx2, d3s_dx3

    @staticmethod
    def _sinusoidal_motion(x: float):
        """简谐运动 (Harmonic / Simple harmonic motion)
        
        Displacement follows a cosine curve (projection of uniform circular motion).
        
        s = h/2 * (1 - cos(pi*theta/phi))
        
        Smooth at boundaries for rise-dwell-rise but has infinite jerk
        at boundaries causing mild impact.
        """
        s = 0.5 * (1.0 - np.cos(np.pi * x))
        ds_dx = 0.5 * np.pi * np.sin(np.pi * x)
        d2s_dx2 = 0.5 * np.pi ** 2 * np.cos(np.pi * x)
        d3s_dx3 = -0.5 * np.pi ** 3 * np.sin(np.pi * x)
        return s, ds_dx, d2s_dx2, d3s_dx3

    def _modified_sine_motion(self, x: float):
        """改良正弦运动 (Modified sine motion)
        
        Combines sinusoidal acceleration in the middle portion with
        constant acceleration at the ends.
        
        Reduces peak acceleration compared to pure harmonic motion
        while maintaining finite jerk at all points.
        """
        # Modified sine uses different formulas for different regions
        # Typical modification points at x=0.09 and x=0.91
        x1, x2 = 0.09, 0.91
        if x <= x1:
            # Constant acceleration region (start)
            s = 1.5673 * x ** 2
            ds_dx = 3.1346 * x
            d2s_dx2 = 3.1346
            d3s_dx3 = 0.0
        elif x <= x2:
            # Modified sine region (middle)
            xm = (x - x1) / (x2 - x1)
            s_part = 0.1035 + 0.7744 * xm - 0.2256 * np.sin(2.3562 * xm)
            ds_part = 0.7744 - 0.5307 * np.cos(2.3562 * xm)
            d2s_part = 1.2500 * np.sin(2.3562 * xm)
            d3s_part = 2.9436 * np.cos(2.3562 * xm)
            # Add the start portion contribution
            s = 0.0127 + 0.2844 * xm + s_part - 0.1035 * xm
            ds_dx = 0.2844 + ds_part - 0.1035
            d2s_dx2 = d2s_part
            d3s_dx3 = d3s_part
        else:
            # Constant acceleration region (end)
            xm = x - x2
            s = 0.8863 + 0.4137 * xm + 0.5 * 3.1346 * xm ** 2
            ds_dx = 0.4137 + 3.1346 * xm
            d2s_dx2 = 3.1346
            d3s_dx3 = 0.0
        return s, ds_dx, d2s_dx2, d3s_dx3

    def _modified_trap_motion(self, x: float):
        """改良梯形运动 (Modified trapezoidal motion)
        
        Acceleration curve follows a trapezoidal shape with rounded corners.
        Combines constant acceleration (trapezoidal) with sinusoidal transitions.
        
        Good balance of peak acceleration and smoothness.
        Widely used in industrial cam design.
        """
        # Modified trapezoidal uses transition points
        x1, x2, x3, x4 = 0.05, 0.25, 0.75, 0.95
        if x <= x1:
            # Sinusoidal acceleration start
            s = 0.01697 + 0.06787 * x - 0.02154 * np.cos(15.708 * x)
            ds_dx = 0.06787 + 0.33837 * np.sin(15.708 * x)
            d2s_dx2 = 5.3128 * np.cos(15.708 * x)
            d3s_dx3 = -83.454 * np.sin(15.708 * x)
        elif x <= x2:
            # Constant acceleration (trapezoidal top)
            xm = x - x1
            s = 0.08484 + 0.33935 * xm + 0.49738 * xm ** 2
            ds_dx = 0.33935 + 0.99476 * xm
            d2s_dx2 = 0.99476
            d3s_dx3 = 0.0
        elif x <= x3:
            # Sinusoidal acceleration middle (peak)
            xm = (x - x2) / (x3 - x2)
            s_part = 0.25 - 0.25 * np.cos(np.pi * xm)
            ds_part = 0.5 * np.pi * np.sin(np.pi * xm)
            d2s_part = 0.5 * np.pi ** 2 * np.cos(np.pi * xm)
            d3s_part = -0.5 * np.pi ** 3 * np.sin(np.pi * xm)
            s = 0.33484 + s_part
            ds_dx = ds_part
            d2s_dx2 = d2s_part
            d3s_dx3 = d3s_part
        elif x <= x4:
            # Constant acceleration (trapezoidal descending)
            xm = x - x3
            s = 0.66516 + 0.66065 * xm - 0.49738 * xm ** 2
            ds_dx = 0.66065 - 0.99476 * xm
            d2s_dx2 = -0.99476
            d3s_dx3 = 0.0
        else:
            # Sinusoidal acceleration end
            xm = x - x4
            s = 0.91516 + 0.06787 * xm + 0.02154 * np.cos(15.708 * xm)
            ds_dx = 0.06787 - 0.33837 * np.sin(15.708 * xm)
            d2s_dx2 = -5.3128 * np.cos(15.708 * xm)
            d3s_dx3 = 83.454 * np.sin(15.708 * xm)
        return s, ds_dx, d2s_dx2, d3s_dx3

    def get_motion_law_info(self, law: MotionLaw) -> dict:
        """Get descriptive information about a motion law.
        
        Returns:
            Dictionary with properties of the motion law
        """
        info = {
            MotionLaw.UNIFORM: {
                "name": "等速运动 / Uniform Motion",
                "smoothness": "低 (Low) - 刚性冲击",
                "speed_range": "低速 (Low speed only)",
                "peak_acc_factor": "无穷 (Infinite at boundaries)",
                "description": "最简单但冲击最大，仅适用于极低速场合"
            },
            MotionLaw.PARABOLIC: {
                "name": "等加速等减速 / Parabolic Motion",
                "smoothness": "中 (Medium) - 柔性冲击",
                "speed_range": "中速 (Medium speed)",
                "peak_acc_factor": "8h/phi²",
                "description": "加速度有突变，产生柔性冲击"
            },
            MotionLaw.CYCLOIDAL: {
                "name": "摆线运动 / Cycloidal Motion",
                "smoothness": "高 (High) - 无冲击",
                "speed_range": "中高速 (Medium to high speed)",
                "peak_acc_factor": "2pi*h/phi² ≈ 6.28h/phi²",
                "description": "速度和加速度连续，适用于中高速"
            },
            MotionLaw.POLYNOMIAL_3: {
                "name": "三次多项式 / 3rd Order Polynomial",
                "smoothness": "中 (Medium)",
                "speed_range": "中速 (Medium speed)",
                "peak_acc_factor": "6h/phi²",
                "description": "起点终点速度为零，加速度不连续"
            },
            MotionLaw.POLYNOMIAL_4: {
                "name": "四次多项式 / 4th Order Polynomial",
                "smoothness": "中高 (Medium-High)",
                "speed_range": "中高速 (Medium to high speed)",
                "peak_acc_factor": "约 12h/phi²",
                "description": "加速度在边界连续"
            },
            MotionLaw.POLYNOMIAL_5: {
                "name": "五次多项式 / 5th Order Polynomial",
                "smoothness": "很高 (Very High)",
                "speed_range": "高速 (High speed)",
                "peak_acc_factor": "约 13.6h/phi²",
                "description": "位移、速度、加速度在边界都连续"
            },
            MotionLaw.SINUSOIDAL: {
                "name": "简谐运动 / Harmonic Motion",
                "smoothness": "中 (Medium) - 边界有柔性冲击",
                "speed_range": "中速 (Medium speed)",
                "peak_acc_factor": "pi²h/(2phi²) ≈ 4.93h/phi²",
                "description": "加速度曲线为余弦，边界处跃度无穷"
            },
            MotionLaw.MODIFIED_SINE: {
                "name": "改良正弦 / Modified Sine",
                "smoothness": "很高 (Very High)",
                "speed_range": "高速 (High speed)",
                "peak_acc_factor": "约 5.5h/phi²",
                "description": "峰值加速度较低，适用于高速"
            },
            MotionLaw.MODIFIED_TRAP: {
                "name": "改良梯形 / Modified Trapezoidal",
                "smoothness": "很高 (Very High)",
                "speed_range": "高速 (High speed)",
                "peak_acc_factor": "约 5.5h/phi²",
                "description": "工业凸轮设计中最常用的运动规律之一"
            }
        }
        return info.get(law, {"name": "Unknown", "smoothness": "?", "speed_range": "?",
                              "peak_acc_factor": "?", "description": "?"})
