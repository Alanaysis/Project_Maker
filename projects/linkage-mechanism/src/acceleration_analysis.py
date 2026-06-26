"""Acceleration analysis for four-bar linkages.

四连杆机构的加速度分析模块。

Acceleration analysis computes the angular accelerations of the coupler
and rocker links, as well as linear accelerations of key points,
given the input crank angular acceleration.

The acceleration analysis is derived by differentiating the velocity
vector loop equation with respect to time.
"""

from typing import Tuple

import numpy as np

from .position_analysis import FourBarParams, position_analysis
from .velocity_analysis import velocity_analysis


def acceleration_analysis(params: FourBarParams, theta2: float,
                          omega2: float, alpha2: float = 0.0) -> Tuple[float, float]:
    """Compute angular accelerations of coupler and rocker links.

    Differentiating the velocity equation with respect to time:
        i*a2*alpha2*e^(i*theta2) - a2*omega2^2*e^(i*theta2) +
        i*a3*alpha3*e^(i*theta3) - a3*omega3^2*e^(i*theta3) =
        i*a4*alpha4*e^(i*theta4) - a4*omega4^2*e^(i*theta4)

    This gives two scalar equations:
        -a2*alpha2*sin(theta2) - a2*omega2^2*cos(theta2) -
         a3*alpha3*sin(theta3) - a3*omega3^2*cos(theta3) =
         -a4*alpha4*sin(theta4) - a4*omega4^2*cos(theta4)

         a2*alpha2*cos(theta2) - a2*omega2^2*sin(theta2) +
         a3*alpha3*cos(theta3) - a3*omega3^2*sin(theta3) =
         a4*alpha4*cos(theta4) - a4*omega4^2*sin(theta4)

    Solving the 2x2 system for alpha3 and alpha4.

    Args:
        params: Four-bar linkage parameters.
        theta2: Input crank angle in radians.
        omega2: Input crank angular velocity (rad/s).
        alpha2: Input crank angular acceleration (rad/s^2). Default 0.0.

    Returns:
        Tuple of (alpha3, alpha4): angular accelerations of coupler and rocker.

    Raises:
        ValueError: If the mechanism is at a singularity.
    """
    a1, a2, a3, a4 = params.a1, params.a2, params.a3, params.a4

    # Get position and velocity solutions
    pos = position_analysis(params, theta2)
    theta3, theta4 = pos.theta3, pos.theta4
    omega3, omega4 = velocity_analysis(params, theta2, omega2)

    # Coefficient matrix for [alpha3, alpha4]
    M = np.array([
        [a3 * np.sin(theta3), -a4 * np.sin(theta4)],
        [-a3 * np.cos(theta3), a4 * np.cos(theta4)],
    ])

    # Right-hand side (includes centripetal terms)
    b = np.array([
        a2 * alpha2 * np.sin(theta2) + a2 * omega2**2 * np.cos(theta2) +
        a3 * omega3**2 * np.cos(theta3),
        -a2 * alpha2 * np.cos(theta2) + a2 * omega2**2 * np.sin(theta2) +
        a3 * omega3**2 * np.sin(theta3),
    ])

    # Check determinant (singularity)
    det = np.linalg.det(M)
    if abs(det) < 1e-10:
        raise ValueError(
            f"Singularity detected at theta2={theta2:.4f} rad. "
            f"Determinant = {det:.2e}."
        )

    # Solve for [alpha3, alpha4]
    alpha3, alpha4 = np.linalg.solve(M, b)

    return float(alpha3), float(alpha4)


def compute_linear_acceleration(params: FourBarParams, theta2: float,
                                omega2: float, alpha2: float = 0.0) -> dict:
    """Compute linear accelerations of key points.

    Args:
        params: Four-bar linkage parameters.
        theta2: Input crank angle in radians.
        omega2: Input crank angular velocity (rad/s).
        alpha2: Input crank angular acceleration (rad/s^2). Default 0.0.

    Returns:
        dict with linear accelerations of points A, B, and C:
            'A': acceleration of crank end point
            'B': acceleration of coupler-crank joint
            'C': acceleration of coupler-rocker joint
    """
    a1, a2, a3, a4 = params.a1, params.a2, params.a3, params.a4
    o2, o4 = params.o2, params.o4

    # Get position, velocity, and angular acceleration solutions
    pos = position_analysis(params, theta2)
    omega3, omega4 = velocity_analysis(params, theta2, omega2)
    alpha3, alpha4 = acceleration_analysis(params, theta2, omega2, alpha2)

    # Point A: end of crank
    Ax = o2[0] + a2 * np.cos(pos.theta2)
    Ay = o2[1] + a2 * np.sin(pos.theta2)
    # AA = alpha2 x r_O2A - omega2^2 * r_O2A
    AAx = -alpha2 * a2 * np.sin(pos.theta2) - omega2**2 * a2 * np.cos(pos.theta2)
    AAy = alpha2 * a2 * np.cos(pos.theta2) - omega2**2 * a2 * np.sin(pos.theta2)

    # Point B: end of coupler
    Bx = Ax + a3 * np.cos(pos.theta3)
    By = Ay + a3 * np.sin(pos.theta3)
    # AB = alpha3 x r_AB - omega3^2 * r_AB
    ABx = -alpha3 * a3 * np.sin(pos.theta3) - omega3**2 * a3 * np.cos(pos.theta3)
    ABy = alpha3 * a3 * np.cos(pos.theta3) - omega3**2 * a3 * np.sin(pos.theta3)

    # Point C: end of rocker
    Cx = o4[0] + a4 * np.cos(pos.theta4)
    Cy = o4[1] + a4 * np.sin(pos.theta4)
    # AC = alpha4 x r_O4C - omega4^2 * r_O4C
    ACx = -alpha4 * a4 * np.sin(pos.theta4) - omega4**2 * a4 * np.cos(pos.theta4)
    ACy = alpha4 * a4 * np.cos(pos.theta4) - omega4**2 * a4 * np.sin(pos.theta4)

    return {
        'A': (AAx, AAy),
        'B': (ABx, ABy),
        'C': (ACx, ACy),
        'alpha3': alpha3,
        'alpha4': alpha4,
    }
