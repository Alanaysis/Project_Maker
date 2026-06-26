"""Velocity analysis for four-bar linkages.

四连杆机构的速度分析模块。

Velocity analysis computes the angular velocities of the coupler and
rocker links given the input crank angular velocity.

The velocity analysis is derived by differentiating the position
vector loop equation with respect to time.
"""

from typing import Tuple

import numpy as np

from .position_analysis import FourBarParams, PositionResult, position_analysis


def velocity_analysis(params: FourBarParams, theta2: float,
                      omega2: float) -> Tuple[float, float]:
    """Compute angular velocities of coupler and rocker links.

    Differentiating the vector loop equation:
        a2*e^(i*theta2) + a3*e^(i*theta3) = a1 + a4*e^(i*theta4)

    With respect to time:
        i*a2*omega2*e^(i*theta2) + i*a3*omega3*e^(i*theta3) = i*a4*omega4*e^(i*theta4)

    This gives two scalar equations:
        -a2*omega2*sin(theta2) - a3*omega3*sin(theta3) = -a4*omega4*sin(theta4)
         a2*omega2*cos(theta2) + a3*omega3*cos(theta3) = a4*omega4*cos(theta4)

    Solving the 2x2 system for omega3 and omega4:
        [a3*sin(theta3)   -a4*sin(theta4)] [omega3]   [a2*omega2*sin(theta2)]
        [-a3*cos(theta3)   a4*cos(theta4)] [omega4] = [-a2*omega2*cos(theta2)]

    Args:
        params: Four-bar linkage parameters.
        theta2: Input crank angle in radians.
        omega2: Input crank angular velocity (rad/s).

    Returns:
        Tuple of (omega3, omega4): angular velocities of coupler and rocker.

    Raises:
        ValueError: If the mechanism is at a singularity.
    """
    a1, a2, a3, a4 = params.a1, params.a2, params.a3, params.a4

    # First get the position solution
    pos = position_analysis(params, theta2)
    theta3, theta4 = pos.theta3, pos.theta4

    # Coefficient matrix for [omega3, omega4]
    # Row 1: a3*sin(theta3) * omega3 - a4*sin(theta4) * omega4 = a2*omega2*sin(theta2)
    # Row 2: -a3*cos(theta3) * omega3 + a4*cos(theta4) * omega4 = -a2*omega2*cos(theta2)

    M = np.array([
        [a3 * np.sin(theta3), -a4 * np.sin(theta4)],
        [-a3 * np.cos(theta3), a4 * np.cos(theta4)],
    ])

    # Right-hand side
    b = np.array([
        a2 * omega2 * np.sin(theta2),
        -a2 * omega2 * np.cos(theta2),
    ])

    # Check determinant (singularity)
    det = np.linalg.det(M)
    if abs(det) < 1e-10:
        raise ValueError(
            f"Singularity detected at theta2={theta2:.4f} rad. "
            f"Determinant = {det:.2e}. "
            f"The mechanism is at a dead point."
        )

    # Solve for [omega3, omega4]
    omega3, omega4 = np.linalg.solve(M, b)

    return float(omega3), float(omega4)


def compute_linear_velocity(params: FourBarParams, theta2: float,
                            omega2: float) -> dict:
    """Compute linear velocities of key points.

    Args:
        params: Four-bar linkage parameters.
        theta2: Input crank angle in radians.
        omega2: Input crank angular velocity (rad/s).

    Returns:
        dict with linear velocities of points A, B, and C:
            'A': velocity of crank-coupler joint (tuple)
            'B': velocity of coupler-rocker joint (tuple)
            'C': velocity of coupler point midpoint (tuple)
    """
    a1, a2, a3, a4 = params.a1, params.a2, params.a3, params.a4
    o2, o4 = params.o2, params.o4

    # Get position solution
    pos = position_analysis(params, theta2)

    # Point A: end of crank (crank-coupler joint)
    Ax = a2 * np.cos(theta2) + o2[0]
    Ay = a2 * np.sin(theta2) + o2[1]
    # VA = omega2 x r_O2A
    VAx = -omega2 * a2 * np.sin(theta2)
    VAy = omega2 * a2 * np.cos(theta2)

    # Point B: end of coupler (coupler-rocker joint)
    Bx = Ax + a3 * np.cos(pos.theta3)
    By = Ay + a3 * np.sin(pos.theta3)

    # VB = VA + omega3 x r_AB
    omega3, omega4 = velocity_analysis(params, theta2, omega2)
    VBx = VAx - omega3 * a3 * np.sin(pos.theta3)
    VBy = VAy + omega3 * a3 * np.cos(pos.theta3)

    # Point C: end of rocker
    Cx = o4[0] + a4 * np.cos(pos.theta4)
    Cy = o4[1] + a4 * np.sin(pos.theta4)

    # VC = omega4 x r_O4C
    VCx = -omega4 * a4 * np.sin(pos.theta4)
    VCy = omega4 * a4 * np.cos(pos.theta4)

    return {
        'A': (VAx, VAy),
        'B': (VBx, VBy),
        'C': (VCx, VCy),
        'omega3': omega3,
        'omega4': omega4,
    }


def compute_transmission_angle(params: FourBarParams, theta2: float) -> float:
    """Compute the transmission angle.

    The transmission angle (mu) is the angle between the coupler link
    and the rocker link. It measures the mechanical advantage of the
    mechanism.

    mu = angle between link 3 (coupler) and link 4 (rocker)

    A good transmission angle is close to 90 degrees.
    Values outside [40, 140] degrees may cause poor force transmission.

    Args:
        params: Four-bar linkage parameters.
        theta2: Input crank angle in radians.

    Returns:
        Transmission angle in radians.
    """
    pos = position_analysis(params, theta2)

    # Vector from B to C (coupler direction)
    a1, a2, a3, a4 = params.a1, params.a2, params.a3, params.a4
    o2, o4 = params.o2, params.o4

    Bx = o2[0] + a2 * np.cos(pos.theta2)
    By = o2[1] + a2 * np.sin(pos.theta2)
    Cx = o4[0] + a4 * np.cos(pos.theta4)
    Cy = o4[1] + a4 * np.sin(pos.theta4)

    # Vector BC (coupler)
    BC = np.array([Cx - Bx, Cy - By])
    # Vector from C to O4 (rocker, pointing toward ground)
    CO4 = np.array([o4[0] - Cx, o4[1] - Cy])

    # cos(mu) = |BC . CO4| / (|BC| * |CO4|)
    dot_product = np.abs(np.dot(BC, CO4))
    mag_BC = np.linalg.norm(BC)
    mag_CO4 = np.linalg.norm(CO4)

    if mag_BC < 1e-10 or mag_CO4 < 1e-10:
        return np.pi / 2  # Default to 90 degrees

    cos_mu = dot_product / (mag_BC * mag_CO4)
    cos_mu = np.clip(cos_mu, -1.0, 1.0)
    mu = np.arccos(cos_mu)

    return mu
