"""Four-bar linkage geometry and position analysis.

四连杆机构的几何与位置分析模块。

Grashof condition determines whether a four-bar linkage can rotate fully
or only oscillates. The analysis uses vector loop equations to find
unknown joint positions given input angles.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Optional

import numpy as np


class GrashofType(Enum):
    """Grashof condition classification (Grashof条件分类).

    A four-bar linkage satisfies the Grashof condition when:
        s + l <= p + q
    where s = shortest link, l = longest link, p, q = other two links.

    Types:
        GRASHOF: s + l < p + q (at least one link can rotate fully)
        SPECIAL: s + l == p + q (change-point mechanism)
        NON_GRASHOF: s + l > p + q (no link can rotate fully)
    """
    GRASHOF = "grashof"
    SPECIAL = "special"
    NON_GRASHOF = "non_grashof"


class LinkageType(Enum):
    """Mechanism type classification (机构类型分类).

    Based on which link is grounded (fixed) and the Grashof condition:
        CRANK_ROCKER: Input link rotates fully, output link oscillates
        DOUBLE_CRANK: Both input and output links rotate fully
        DOUBLE_ROCKER: Neither link rotates fully
        SLIDER_CRANK: Contains a sliding joint
    """
    CRANK_ROCKER = "crank_rocker"
    DOUBLE_CRANK = "double_crank"
    DOUBLE_ROCKER = "double_rocker"
    SLIDER_CRANK = "slider_crank"


@dataclass
class FourBarParams:
    """Four-bar linkage parameters (四连杆机构参数).

    Links are numbered:
        Link 1 (ground): Fixed link between ground joints
        Link 2 (crank): Input link connected to ground at O2
        Link 3 (coupler): Floating link connecting crank and rocker
        Link 4 (rocker): Output link connected to ground at O4

    Ground link length is inferred from the distance between ground joints.
    """
    # Link lengths (link lengths)
    a1: float  # Ground link length (ground link / 机架)
    a2: float  # Crank length (crank / 曲柄)
    a3: float  # Coupler length (coupler link / 连杆)
    a4: float  # Rocker length (rocker / 摇杆)

    # Ground joint positions (ground joint positions)
    o2: Tuple[float, float] = (0.0, 0.0)  # Fixed pivot for crank
    o4: Tuple[float, float] = (0.0, 0.0)  # Fixed pivot for rocker

    def __post_init__(self):
        """Validate parameters after initialization (参数验证)."""
        if self.a1 <= 0 or self.a2 <= 0 or self.a3 <= 0 or self.a4 <= 0:
            raise ValueError("All link lengths must be positive (所有杆长必须为正)")
        # Update ground link length from joint positions if not explicitly set
        dx = self.o4[0] - self.o2[0]
        dy = self.o4[1] - self.o2[1]
        computed_a1 = np.sqrt(dx**2 + dy**2)
        if computed_a1 > 0 and abs(computed_a1 - self.a1) > 1e-10:
            self.a1 = computed_a1


@dataclass
class PositionResult:
    """Position analysis result (位置分析结果).

    Contains the output angles and the coupler point position.
    """
    theta2: float  # Input crank angle (rad) (曲柄角度)
    theta3: float  # Coupler angle (rad) (连杆角度)
    theta4: float  # Rocker angle (rad) (摇杆角度)
    coupler_point: Tuple[float, float]  # Coupler point position (连杆上点位置)
    assembly_mode: str  # "open" or "crossed" assembly mode (装配模式)


def check_grashof(params: FourBarParams) -> GrashofType:
    """Check Grashof condition (检查Grashof条件).

    The Grashof condition determines if at least one link can rotate
    through a full revolution.

    Condition: s + l <= p + q
    where s = shortest link, l = longest link, p and q = other links.

    Args:
        params: Four-bar linkage parameters.

    Returns:
        GrashofType: The classification of the mechanism.
    """
    links = [params.a1, params.a2, params.a3, params.a4]
    s = min(links)
    l = max(links)
    p_q_sum = sum(links) - s - l

    if s + l < p_q_sum:
        return GrashofType.GRASHOF
    elif abs(s + l - p_q_sum) < 1e-10:
        return GrashofType.SPECIAL
    else:
        return GrashofType.NON_GRASHOF


def classify_linkage_type(params: FourBarParams) -> LinkageType:
    """Classify the linkage type based on Grashof condition and grounded link.

    Grashof classification rules:
        - Grashof: s + l < p + q
        - Shortest link adjacent to ground => crank-rocker (or rocker-crank)
        - Shortest link is ground => double-crank
        - Shortest link is coupler => double-rocker
        - Non-Grashof: no link can rotate fully => double-rocker

    Args:
        params: Four-bar linkage parameters.

    Returns:
        LinkageType: The classification of the mechanism.
    """
    grashof = check_grashof(params)

    if grashof == GrashofType.NON_GRASHOF:
        return LinkageType.DOUBLE_ROCKER

    # Grashof or special case: shortest link determines type
    links = [params.a1, params.a2, params.a3, params.a4]
    shortest_idx = links.index(min(links))

    if shortest_idx == 0:  # Ground (link 1) is shortest => double-crank
        return LinkageType.DOUBLE_CRANK
    elif shortest_idx == 1:  # Crank (link 2) is shortest => crank-rocker
        return LinkageType.CRANK_ROCKER
    elif shortest_idx == 3:  # Rocker (link 4) is shortest => rocker-crank (double-crank)
        return LinkageType.DOUBLE_CRANK
    else:  # Coupler (link 3) is shortest => double-rocker
        return LinkageType.DOUBLE_ROCKER


def position_analysis(params: FourBarParams, theta2: float,
                      coupler_point_ratio: Tuple[float, float] = (0.5, 0.5),
                      coupler_angle_offset: float = 0.0) -> PositionResult:
    """Perform position analysis using vector loop method (位置分析).

    Uses the vector loop equation:
        r2 + r3 = r1 + r4
    which gives two scalar equations:
        a2*cos(theta2) + a3*cos(theta3) = a1 + a4*cos(theta4)
        a2*sin(theta2) + a3*sin(theta3) = a4*sin(theta4)

    Solving for theta3 and theta4 using Freudenstein's equation approach.

    Args:
        params: Four-bar linkage parameters.
        theta2: Input crank angle in radians (曲柄输入角度).
        coupler_point_ratio: Point on coupler as ratio from B to C
            (e.g., (0.5, 0.5) = midpoint). Default (0.5, 0.5).
        coupler_angle_offset: Angle offset of coupler point from coupler link
            in radians. Default 0.0.

    Returns:
        PositionResult: Analysis results for the given input angle.

    Raises:
        ValueError: If the mechanism cannot be assembled at the given angle.
    """
    a1, a2, a3, a4 = params.a1, params.a2, params.a3, params.a4
    o2, o4 = params.o2, params.o4

    # Compute constants for Freudenstein's equation
    # K1 = a1/a2, K2 = a1/a4, K3 = (a2^2 - a3^2 + a4^2 + a1^2)/(2*a2*a4)
    K1 = a1 / a2
    K2 = a1 / a4
    K3 = (a2**2 - a3**2 + a4**2 + a1**2) / (2 * a2 * a4)

    # Coefficients for A*tan^2(theta4/2) + B*tan(theta4/2) + C = 0
    A = K3 - K2 * np.cos(theta2) - np.cos(theta2)
    B = -2 * np.sin(theta2)
    C = K3 - K2 * np.cos(theta2) + np.cos(theta2)

    # Wait, let me use the correct Freudenstein formulation
    # From: a2*cos(theta2) + a3*cos(theta3) = a1 + a4*cos(theta4)
    #       a2*sin(theta2) + a3*sin(theta3) = a4*sin(theta4)
    #
    # Using the standard approach:
    # J1*theta3 - J2*theta4 + J3 = cos(theta2) where J1, J2, J3 are Freudenstein constants

    # Alternative approach: use the loop closure with K constants
    # K1*theta4 - K2*theta3 + K3 = cos(theta2)
    # where K1 = a2/a1, K2 = a2/a4, K3 = (a4^2 - a3^2 + a2^2 + a1^2)/(2*a1*a4)

    K1_alt = a2 / a1
    K2_alt = a2 / a4
    K3_alt = (a4**2 - a3**2 + a2**2 + a1**2) / (2 * a1 * a4)

    # Using the standard vector loop solution
    # D = cos(theta2) - K1 + K2*cos(theta2) + K3
    # E = -2*cos(theta2)
    # F = cos(theta2) - K1 + K4*cos(theta2) + K5
    # where K1= a1/a2, K2=a1/a4, K3=(a2^2-a3^2+a4^2+a1^2)/(2*a2*a4)
    #       K4=a1/a4, K5=(a2^2+a3^2-a4^2+a1^2)/(2*a2*a1)

    D = np.cos(theta2) - K1 + K2 * np.cos(theta2) + K3
    E = -2 * np.cos(theta2)
    F = np.cos(theta2) - K1 + K4_const(a1, a2, a3, a4) * np.cos(theta2) + K5_const(a1, a2, a3, a4)

    # Solve for theta4 using tan-half substitution
    # A*sin(theta4) + B*cos(theta4) + C = 0
    # where A = a2*sin(theta2), B = a1 - a2*cos(theta2), C = (a2^2 + a1^2 + a4^2 - a3^2)/(2*a4)

    A_coeff = a2 * np.sin(theta2)
    B_coeff = a1 - a2 * np.cos(theta2)
    C_coeff = (a2**2 + a1**2 + a4**2 - a3**2) / (2 * a4)

    # Use the discriminant approach
    # Rewrite as: A*sin(theta4) + B*cos(theta4) = -C
    # Let t = tan(theta4/2), then sin(theta4) = 2t/(1+t^2), cos(theta4) = (1-t^2)/(1+t^2)
    # A*2t + B*(1-t^2) = -C*(1+t^2)
    # (B+C)*t^2 + (-2A)*t + (C-B) = 0

    a_quad = B_coeff + C_coeff
    b_quad = -2 * A_coeff
    c_quad = C_coeff - B_coeff

    if abs(a_quad) < 1e-15:
        # Linear case
        if abs(b_quad) < 1e-15:
            raise ValueError(f"Cannot assemble mechanism at theta2={theta2:.4f} rad")
        t = -c_quad / b_quad
        theta4 = 2 * np.arctan(t)
    else:
        disc = b_quad**2 - 4 * a_quad * c_quad
        if disc < 0:
            raise ValueError(
                f"Cannot assemble mechanism at theta2={theta2:.4f} rad. "
                f"Discriminant = {disc:.6f} < 0. "
                f"Input angle may be outside the working range."
            )
        t1 = (-b_quad + np.sqrt(disc)) / (2 * a_quad)
        t2 = (-b_quad - np.sqrt(disc)) / (2 * a_quad)

        # Open mode uses +, crossed mode uses -
        theta4_open = 2 * np.arctan(t1)
        theta4_crossed = 2 * np.arctan(t2)

        # Choose the appropriate solution
        # For open mode, we use the first solution
        theta4 = theta4_open

    # Solve for theta3
    # a3*cos(theta3) = a1 + a4*cos(theta4) - a2*cos(theta2)
    # a3*sin(theta3) = a4*sin(theta4) - a2*sin(theta2)
    cos_theta3 = (a1 + a4 * np.cos(theta4) - a2 * np.cos(theta2)) / a3
    sin_theta3 = (a4 * np.sin(theta4) - a2 * np.sin(theta2)) / a3

    # Use atan2 for correct quadrant
    theta3 = np.arctan2(sin_theta3, cos_theta3)

    # Compute coupler point position
    # B (joint between crank and coupler):
    #   Bx = a2*cos(theta2) + Ox2, By = a2*sin(theta2) + Oy2
    Bx = a2 * np.cos(theta2) + o2[0]
    By = a2 * np.sin(theta2) + o2[1]

    # C (joint between coupler and rocker):
    #   Cx = Bx + a3*cos(theta3), Cy = By + a3*sin(theta3)
    Cx = Bx + a3 * np.cos(theta3)
    Cy = By + a3 * np.sin(theta3)

    # Coupler point P divides BC in ratio (coupler_point_ratio)
    # P = B + ratio_from_B * (C - B) + offset perpendicular
    ratio = coupler_point_ratio[0]
    P_base_x = Bx + ratio * (Cx - Bx)
    P_base_y = By + ratio * (Cy - By)

    # Add perpendicular offset
    offset_ratio = coupler_point_ratio[1]
    perp_x = -(Cy - By)
    perp_y = (Cx - Bx)
    offset = offset_ratio * np.sqrt(perp_x**2 + perp_y**2)
    if abs(offset) > 1e-10:
        P_base_x += offset * np.cos(theta3 + coupler_angle_offset)
        P_base_y += offset * np.sin(theta3 + coupler_angle_offset)

    # Determine assembly mode
    # Check the sign of the cross product to determine mode
    cross_z = (a2 * np.sin(theta2)) * (a4 * np.sin(theta4)) - \
              (a2 * np.cos(theta2)) * (a4 * np.cos(theta4))
    assembly_mode = "open" if cross_z >= 0 else "crossed"

    return PositionResult(
        theta2=theta2,
        theta3=theta3,
        theta4=theta4,
        coupler_point=(P_base_x, P_base_y),
        assembly_mode=assembly_mode,
    )


def K4_const(a1: float, a2: float, a3: float, a4: float) -> float:
    """Helper: K4 = a4/a2."""
    return a4 / a2


def K5_const(a1: float, a2: float, a3: float, a4: float) -> float:
    """Helper: K5 = (a2^2 - a3^2 + a4^2 + a1^2)/(2*a2*a1)."""
    return (a2**2 - a3**2 + a4**2 + a1**2) / (2 * a2 * a1)


def compute_linkage_circles(params: FourBarParams) -> dict:
    """Compute Grashof linkage circles (Grashof连杆圆).

    Computes the crank circle and rocker circle for visualization.

    Args:
        params: Four-bar linkage parameters.

    Returns:
        dict with keys 'crank_circle' and 'rocker_circle', each containing:
            'center': (x, y) tuple
            'radius': float
    """
    grashof = check_grashof(params)
    linkage_type = classify_linkage_type(params)

    result = {
        'grashof_type': grashof,
        'linkage_type': linkage_type,
        'crank_circle': {
            'center': params.o2,
            'radius': params.a2,
        },
        'rocker_circle': {
            'center': params.o4,
            'radius': params.a4,
        },
    }

    if grashof == GrashofType.GRASHOF:
        # For Grashof mechanisms, compute the range of motion
        result['crank_can_rotate_full'] = True
        if linkage_type == LinkageType.CRANK_ROCKER:
            result['rocker_can_rotate_full'] = False
            # Compute rocker oscillation limits
            theta4_min, theta4_max = compute_rocker_limits(params)
            result['rocker_limits'] = (theta4_min, theta4_max)
        elif linkage_type == LinkageType.DOUBLE_CRANK:
            result['rocker_can_rotate_full'] = True
        else:
            result['rocker_can_rotate_full'] = False
    else:
        result['crank_can_rotate_full'] = False
        result['rocker_can_rotate_full'] = False

    return result


def compute_rocker_limits(params: FourBarParams) -> Tuple[float, float]:
    """Compute the oscillation limits of the rocker (摇杆摆动范围).

    Args:
        params: Four-bar linkage parameters.

    Returns:
        Tuple of (min_angle, max_angle) in radians.
    """
    a1, a2, a3, a4 = params.a1, params.a2, params.a3, params.a4

    # The rocker reaches its limits when the crank and coupler are collinear
    # i.e., when theta3 = theta2 or theta3 = theta2 + pi

    # Case 1: Crank and coupler extended (theta3 = theta2)
    # Using law of cosines on triangle formed by ground, extended link
    extended_len = a2 + a3
    # cos(theta4_limit1) = (a1^2 + a4^2 - extended_len^2) / (2*a1*a4)
    cos_val1 = (a1**2 + a4**2 - extended_len**2) / (2 * a1 * a4)
    cos_val1 = np.clip(cos_val1, -1.0, 1.0)
    theta4_limit1 = np.arccos(cos_val1)

    # Case 2: Crank and coupler folded (theta3 = theta2 + pi)
    folded_len = abs(a2 - a3)
    cos_val2 = (a1**2 + a4**2 - folded_len**2) / (2 * a1 * a4)
    cos_val2 = np.clip(cos_val2, -1.0, 1.0)
    theta4_limit2 = np.arccos(cos_val2)

    theta4_min = min(theta4_limit1, theta4_limit2)
    theta4_max = max(theta4_limit1, theta4_limit2)

    return theta4_min, theta4_max


def generate_coupler_curve(params: FourBarParams, num_points: int = 360,
                           coupler_point_ratio: Tuple[float, float] = (0.5, 0.3),
                           coupler_angle_offset: float = 0.0) -> np.ndarray:
    """Generate the coupler curve (连杆曲线).

    The coupler curve is the path traced by a point on the coupler link
    as the input crank rotates through 360 degrees.

    Args:
        params: Four-bar linkage parameters.
        num_points: Number of sample points. Default 360.
        coupler_point_ratio: Point location on coupler.
        coupler_angle_offset: Offset angle for the coupler point.

    Returns:
        np.ndarray of shape (N, 2) containing the coupler curve points.
    """
    curve_points = []
    for i in range(num_points):
        theta2 = 2 * np.pi * i / num_points
        try:
            result = position_analysis(
                params, theta2, coupler_point_ratio, coupler_angle_offset
            )
            curve_points.append(result.coupler_point)
        except ValueError:
            # Skip points where the mechanism cannot be assembled
            continue

    return np.array(curve_points)
