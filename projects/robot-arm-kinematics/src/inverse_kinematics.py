"""
Inverse Kinematics Module / 逆向运动学模块

Inverse kinematics (IK) computes the joint angles required to place
the end-effector at a desired position and orientation.

    q = IK(T_desired)

IK is much harder than forward kinematics because:
1. Multiple solutions may exist (arm up/down, left/right configurations)
2. No closed-form solution for most robots
3. Some positions may be outside the reachable workspace
4. Singularities can cause numerical instability

Two main approaches:
- Analytical (closed-form): Exact solutions for specific robot geometries
- Numerical (iterative): General-purpose but computationally expensive
"""

import numpy as np
from scipy.optimize import fsolve
from .forward_kinematics import ForwardKinematics


def ik_2r_planar(x, y, l1, l2, config='elbow_up'):
    """
    Analytical inverse kinematics for a 2R planar arm.

    Given a target position (x, y), find the two joint angles.

    Solution derivation:
    Using the law of cosines on the triangle formed by the two links:

        cos(theta2) = (x^2 + y^2 - l1^2 - l2^2) / (2*l1*l2)

    Then:
        theta1 = atan2(y, x) - atan2(k2, k1)
        theta2 = atan2(sin_theta2, cos_theta2)

    where:
        k1 = l1 + l2*cos(theta2)
        k2 = l2*sin(theta2)

    Two configurations exist:
    - 'elbow_up': theta2 > 0 (elbow points up)
    - 'elbow_down': theta2 < 0 (elbow points down)

    Args:
        x: Target x position (mm)
        y: Target y position (mm)
        l1: Length of first link (mm)
        l2: Length of second link (mm)
        config: 'elbow_up' or 'elbow_down'

    Returns:
        (theta1, theta2) joint angles in radians

    Raises:
        ValueError: If target is outside reachable workspace
    """
    # Check reachability
    d = np.sqrt(x**2 + y**2)
    max_reach = l1 + l2
    min_reach = abs(l1 - l2)

    if d > max_reach or d < min_reach:
        raise ValueError(
            f"Target ({x:.2f}, {y:.2f}) is outside reachable workspace. "
            f"Reach: [{min_reach:.2f}, {max_reach:.2f}], "
            f"Distance: {d:.2f}"
        )

    # Law of cosines for theta2
    cos_theta2 = (x**2 + y**2 - l1**2 - l2**2) / (2 * l1 * l2)
    # Clamp to [-1, 1] to handle floating point errors
    cos_theta2 = np.clip(cos_theta2, -1, 1)
    sin_theta2 = np.sqrt(1 - cos_theta2**2)

    if config == 'elbow_down':
        sin_theta2 = -sin_theta2

    theta2 = np.arctan2(sin_theta2, cos_theta2)

    # Solve for theta1
    k1 = l1 + l2 * cos_theta2
    k2 = l2 * sin_theta2
    theta1 = np.arctan2(y, x) - np.arctan2(k2, k1)

    return theta1, theta2


def ik_2r_planar_all_solutions(x, y, l1, l2):
    """
    Find all valid IK solutions for a 2R planar arm.

    Returns both elbow_up and elbow_down configurations if they exist.

    Args:
        x: Target x position (mm)
        y: Target y position (mm)
        l1: Length of first link (mm)
        l2: Length of second link (mm)

    Returns:
        List of (theta1, theta2) tuples for each valid solution
    """
    solutions = []
    for config in ['elbow_up', 'elbow_down']:
        try:
            theta1, theta2 = ik_2r_planar(x, y, l1, l2, config)
            solutions.append((theta1, theta2))
        except ValueError:
            pass
    return solutions


def ik_numerical(link_params, target_pose, dh_convention='modified',
                 initial_guess=None, max_iter=100, tol=1e-6):
    """
    Numerical inverse kinematics using Newton-Raphson method.

    This is a general-purpose IK solver that works for any robot geometry.
    It iteratively minimizes the error between current and target pose.

    Algorithm:
        1. Compute current end-effector pose T_current = FK(q)
        2. Compute error: delta = log(T_current^-1 * T_target)
        3. Update: q_new = q_old + J^-1 * delta
        4. Repeat until convergence

    Args:
        link_params: List of dicts with base DH parameters
        target_pose: 4x4 target homogeneous transformation matrix
        dh_convention: 'standard' or 'modified'
        initial_guess: Initial joint angle guess (default: zeros)
        max_iter: Maximum number of iterations
        tol: Convergence tolerance

    Returns:
        Array of joint angles, or None if no convergence
    """
    fk = ForwardKinematics(link_params, dh_convention)
    n_joints = len(link_params)

    if initial_guess is None:
        q = np.zeros(n_joints)
    else:
        q = np.asarray(initial_guess).copy()

    for iteration in range(max_iter):
        T_current = fk.compute(q)

        # Compute pose error (position + orientation)
        pos_error = target_pose[:3, 3] - T_current[:3, 3]

        # Orientation error using rotation matrix logarithm
        R_err = T_current[:3, :3].T @ target_pose[:3, :3]
        ori_error = _rotation_matrix_to_axis_angle(R_err)

        # Combine position and orientation errors
        error = np.concatenate([pos_error, ori_error])

        # Check convergence
        if np.linalg.norm(error) < tol:
            return q

        # Compute Jacobian
        J = _compute_jacobian_numerical(fk, q)

        # Solve for delta_q
        try:
            delta_q = np.linalg.lstsq(J, error, rcond=None)[0]
        except np.linalg.LinAlgError:
            return None

        # Update joint angles
        q = q + delta_q

        # Check if change is small enough
        if np.linalg.norm(delta_q) < tol:
            return q

    return None


def ik_puma560(x, y, z, phi, theta, psi):
    """
    Analytical IK for PUMA 560 robot arm.

    Uses wrist-center decomposition:
    1. Find wrist center position from target pose
    2. Solve first 3 joints for wrist center (3R arm in space)
    3. Solve last 3 joints for wrist orientation (spherical wrist)

    Args:
        x, y, z: Target end-effector position (mm)
        phi, theta, psi: Euler angles (roll, pitch, yaw) in radians

    Returns:
        Array of 6 joint angles, or None if no solution
    """
    # PUMA 560 DH parameters (modified)
    d2 = 0.432  # mm
    d3 = 0.149  # mm
    a3 = 0.020  # mm
    d4 = 0.433  # mm

    # Convert target position to mm
    x_mm = x * 1000
    y_mm = y * 1000
    z_mm = z * 1000

    # Wrist center position (subtract last link offset along z axis of frame 6)
    # The last link goes along the approach vector
    wz = x_mm - d4 * np.cos(theta) * np.cos(phi)
    wy = y_mm - d4 * np.cos(theta) * np.sin(phi)
    wx = z_mm - d4 * np.sin(theta)

    # First three joints: position the wrist center
    # Joint 1: angle in XY plane
    r = np.sqrt(wx**2 + wy**2)
    if r < 1e-6:
        return None
    theta1 = np.arctan2(wy, wx)

    # Joints 2 and 3: solve for wrist center in XZ plane (after rotating by theta1)
    # After joint 1, the wrist center projects to:
    x_prime = r
    z_prime = wx  # Actually z_mm after transformation

    # Using geometry of links 2 and 3
    # d2 is along Z1, a3 is along X3, d3 is offset
    # Distance from joint 2 to wrist center:
    dx = x_prime
    dz = z_prime - d2

    # Law of cosines for joint 3
    cos_theta3 = (dx**2 + dz**2 - d2**2 - d3**2 - a3**2) / (2 * a3 * np.sqrt(dx**2 + dz**2))
    # This is simplified; actual PUMA 560 has more complex geometry

    # For simplicity, use numerical approach for full PUMA 560 IK
    # This is a placeholder showing the decomposition concept
    return None


def _rotation_matrix_to_axis_angle(R):
    """
    Convert rotation matrix to axis-angle representation.

    Uses the matrix logarithm to extract the rotation vector.

    Args:
        R: 3x3 rotation matrix

    Returns:
        3-element axis-angle vector
    """
    # Handle special cases
    if np.allclose(R, np.eye(3)):
        return np.zeros(3)

    # Rotation vector from Rodrigues' formula inversion
    cos_angle = (np.trace(R) - 1) / 2
    cos_angle = np.clip(cos_angle, -1, 1)
    angle = np.arccos(cos_angle)

    if angle < 1e-6:
        return np.zeros(3)

    axis = np.array([
        R[2, 1] - R[1, 2],
        R[0, 2] - R[2, 0],
        R[1, 0] - R[0, 1]
    ]) / (2 * np.sin(angle))

    return axis * angle


def _compute_jacobian_numerical(fk, joint_angles, eps=1e-5):
    """
    Compute Jacobian using finite differences.

    J[i,j] = d(T)/d(theta_j) evaluated at joint_angles

    Args:
        fk: ForwardKinematics instance
        joint_angles: Current joint angles
        eps: Perturbation size

    Returns:
        6xN Jacobian matrix (6 = 3 pos + 3 ori, N = number of joints)
    """
    n_joints = len(joint_angles)
    J = np.zeros((6, n_joints))

    for j in range(n_joints):
        # Perturb joint j
        dq = np.zeros(n_joints)
        dq[j] = eps

        T_plus = fk.compute(joint_angles + dq)
        T_minus = fk.compute(joint_angles - dq)

        # Position part
        J[:3, j] = (T_plus[:3, 3] - T_minus[:3, 3]) / (2 * eps)

        # Orientation part (using rotation matrix difference)
        R_plus = T_plus[:3, :3]
        R_minus = T_minus[:3, :3]
        R_diff = R_plus - R_minus

        # Extract angular velocity components
        J[3, j] = (R_diff[2, 1]) / (2 * eps)
        J[4, j] = (R_diff[0, 2]) / (2 * eps)
        J[5, j] = (R_diff[1, 0]) / (2 * eps)

    return J
