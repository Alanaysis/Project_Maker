"""
Joint Space to Cartesian Space Mapping Module / 关节空间到笛卡尔空间映射

This module provides tools for mapping between joint space and Cartesian space:

1. Trajectory generation in joint space
2. Linear interpolation in Cartesian space
3. Path planning between waypoints
4. Velocity and acceleration profiles

Key concepts:
- Joint space: Configuration space where each dimension is a joint angle
- Cartesian space: Task space where position/orientation are defined
- Mapping between spaces requires IK (Cartesian -> Joint) or FK (Joint -> Cartesian)
"""

import numpy as np
from .forward_kinematics import ForwardKinematics
from .inverse_kinematics import ik_numerical
from .jacobian import Jacobian


def linear_joint_trajectory(q_start, q_end, n_points):
    """
    Generate linear interpolation in joint space.

    Simple straight-line path in joint configuration space.
    Each joint moves independently from start to end.

    Args:
        q_start: Start joint angles (array)
        q_end: End joint angles (array)
        n_points: Number of interpolation points

    Returns:
        Array of shape (n_points, n_joints) with trajectory
    """
    q_start = np.asarray(q_start)
    q_end = np.asarray(q_end)
    t = np.linspace(0, 1, n_points)
    trajectory = np.outer(1 - t, q_start) + np.outer(t, q_end)
    return trajectory


def cubic_joint_trajectory(q_start, q_end, n_points, v_start=0, v_end=0):
    """
    Generate cubic polynomial trajectory in joint space.

    Uses a 3rd order polynomial: q(t) = a0 + a1*t + a2*t^2 + a3*t^3

    Boundary conditions:
    - q(0) = q_start, q(1) = q_end
    - v(0) = v_start, v(1) = v_end

    This ensures smooth start and stop with continuous velocity.

    Args:
        q_start: Start joint angles (array)
        q_end: End joint angles (array)
        n_points: Number of interpolation points
        v_start: Start velocity (default: 0)
        v_end: End velocity (default: 0)

    Returns:
        Array of shape (n_points, n_joints) with trajectory
    """
    q_start = np.asarray(q_start)
    q_end = np.asarray(q_end)

    # Coefficients for cubic polynomial with zero velocity at endpoints
    # q(t) = (2t^3 - 3t^2 + 1)*q_start + (t^3 - 2t^2 + t)*v_start +
    #        (-2t^3 + 3t^2)*q_end + (t^3 - t^2)*v_end
    t = np.linspace(0, 1, n_points).reshape(-1, 1)

    h00 = 2 * t**3 - 3 * t**2 + 1
    h10 = t**3 - 2 * t**2 + t
    h01 = -2 * t**3 + 3 * t**2
    h11 = t**3 - t**2

    trajectory = h00 * q_start + h10 * v_start + h01 * q_end + h11 * v_end
    return trajectory


def quintic_joint_trajectory(q_start, q_end, n_points, v_start=0, a_start=0, v_end=0, a_end=0):
    """
    Generate quintic polynomial trajectory in joint space.

    Uses a 5th order polynomial ensuring continuity of position,
    velocity, AND acceleration at both endpoints.

    q(t) = a0 + a1*t + a2*t^2 + a3*t^3 + a4*t^4 + a5*t^5

    Args:
        q_start: Start joint angles (array)
        q_end: End joint angles (array)
        n_points: Number of interpolation points
        v_start, a_start: Start velocity and acceleration
        v_end, a_end: End velocity and acceleration

    Returns:
        Array of shape (n_points, n_joints) with trajectory
    """
    q_start = np.asarray(q_start)
    q_end = np.asarray(q_end)

    t = np.linspace(0, 1, n_points).reshape(-1, 1)

    # Quintic polynomial: q(t) = c0 + c1*t + c2*t^2 + c3*t^3 + c4*t^4 + c5*t^5
    # Boundary conditions: q(0)=q0, q'(0)=v0, q''(0)=a0
    #                      q(1)=qf, q'(1)=vf, q''(1)=af
    # Coefficients derived from boundary conditions:
    c0 = q_start
    c1 = v_start
    c2 = a_start / 2.0
    c3 = 10 * q_end - 10 * q_start - 5 * v_start - v_end - a_start / 2.0
    c4 = 15 * q_start - 15 * q_end + 7 * v_start + 3 * v_end + a_start / 2.0
    c5 = -6 * q_start + 6 * q_end - 3 * v_start - 3 * v_end - a_start / 2.0

    trajectory = (c0 + c1 * t + c2 * t**2 + c3 * t**3 + c4 * t**4 + c5 * t**5)
    return trajectory


def cartesian_linear_path(fk, q_start, q_end, n_points):
    """
    Generate a straight-line path in Cartesian space.

    Interpolates linearly in position and SLERP (spherical linear
    interpolation) in orientation between start and end poses.

    Args:
        fk: ForwardKinematics instance
        q_start: Start joint angles
        q_end: End joint angles
        n_points: Number of interpolation points

    Returns:
        (q_trajectory, pose_trajectory): Joint space and Cartesian space paths
    """
    T_start = fk.compute(q_start)
    T_end = fk.compute(q_end)

    # Linear position interpolation
    positions = np.linspace(T_start[:3, 3], T_end[:3, 3], n_points)

    # SLERP for orientation
    R_start = T_start[:3, :3]
    R_end = T_end[:3, :3]
    rotations = slerp(R_start, R_end, n_points)

    # Build target poses
    target_poses = [np.eye(4) for _ in range(n_points)]
    for i in range(n_points):
        target_poses[i][:3, :3] = rotations[i]
        target_poses[i][:3, 3] = positions[i]

    # Solve IK for each target pose
    q_trajectory = []
    prev_q = q_start.copy()
    for T in target_poses:
        q = ik_numerical(fk.link_params, T, fk.dh_convention,
                         initial_guess=prev_q)
        if q is not None:
            q_trajectory.append(q)
            prev_q = q
        else:
            # Fall back to previous solution
            q_trajectory.append(prev_q)

    return np.array(q_trajectory), target_poses


def slerp(R_start, R_end, n_points):
    """
    Spherical linear interpolation between rotation matrices.

    Uses the matrix logarithm/exponential for geodesic interpolation
    on SO(3).

    R(t) = R_start * exp(log(R_start^T * R_end) * t)

    Args:
        R_start: Start 3x3 rotation matrix
        R_end: End 3x3 rotation matrix
        n_points: Number of interpolation points

    Returns:
        Array of shape (n_points, 3, 3) with interpolated rotations
    """
    R = np.zeros((n_points, 3, 3))

    # Relative rotation
    R_rel = R_start.T @ R_end

    # Convert to axis-angle
    cos_angle = (np.trace(R_rel) - 1) / 2
    cos_angle = np.clip(cos_angle, -1, 1)
    angle = np.arccos(cos_angle)

    if angle < 1e-6:
        # No rotation needed
        for i in range(n_points):
            R[i] = R_start
        return R

    # Axis-angle to rotation matrix
    axis = np.array([
        R_rel[2, 1] - R_rel[1, 2],
        R_rel[0, 2] - R_rel[2, 0],
        R_rel[1, 0] - R_rel[0, 1]
    ]) / (2 * np.sin(angle))

    # Generate interpolated rotations
    for i in range(n_points):
        t = i / (n_points - 1)
        R_rel_t = _axis_angle_to_matrix(axis * t * angle)
        R[i] = R_start @ R_rel_t

    return R


def _axis_angle_to_matrix(axis, angle=None):
    """
    Convert axis-angle to rotation matrix using Rodrigues' formula.

    R = I + sin(theta)*K + (1-cos(theta))*K^2

    where K is the skew-symmetric matrix of the axis.

    Args:
        axis: 3-element rotation axis (normalized)
        angle: Rotation angle in radians (if None, extracted from axis)

    Returns:
        3x3 rotation matrix
    """
    if angle is None:
        angle = np.linalg.norm(axis)
        axis = axis / angle

    K = np.array([
        [0, -axis[2], axis[1]],
        [axis[2], 0, -axis[0]],
        [-axis[1], axis[0], 0]
    ])

    R = np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * K @ K
    return R


def generate_waypoint_path(fk, waypoints, n_points_per_segment=50):
    """
    Generate a path through multiple waypoints.

    Each segment uses Cartesian linear interpolation with IK solving.

    Args:
        fk: ForwardKinematics instance
        waypoints: List of target poses (4x4 matrices) or joint angle arrays
        n_points_per_segment: Points per segment

    Returns:
        Full trajectory as array of joint configurations
    """
    trajectory = []
    prev_q = None

    for i in range(len(waypoints) - 1):
        wp_start = waypoints[i]
        wp_end = waypoints[i + 1]

        # Convert poses to joint angles if needed
        if wp_start.shape == (4, 4):
            if prev_q is not None:
                q_start = ik_numerical(fk.link_params, wp_start, fk.dh_convention,
                                       initial_guess=prev_q)
            else:
                q_start = np.zeros(len(fk.link_params))
        else:
            q_start = wp_start

        if wp_end.shape == (4, 4):
            q_end = ik_numerical(fk.link_params, wp_end, fk.dh_convention,
                                 initial_guess=q_start)
        else:
            q_end = wp_end

        if q_start is None or q_end is None:
            continue

        # Linear interpolation in joint space for this segment
        segment = linear_joint_trajectory(q_start, q_end, n_points_per_segment)
        trajectory.append(segment[:-1])  # Avoid duplicate waypoint
        prev_q = q_end

    return np.vstack(trajectory) if trajectory else np.array([])


def compute_path_length(cartesian_path):
    """
    Compute the arc length of a Cartesian path.

    Args:
        cartesian_path: Array of 4x4 pose matrices

    Returns:
        Total path length in mm
    """
    total_length = 0
    for i in range(1, len(cartesian_path)):
        dx = cartesian_path[i][:3, 3] - cartesian_path[i-1][:3, 3]
        total_length += np.linalg.norm(dx)
    return total_length
