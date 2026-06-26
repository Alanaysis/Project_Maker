"""
Jacobian Matrix Module / 雅可比矩阵模块

The Jacobian matrix J relates joint velocities to end-effector velocities:

    v = J(q) * q_dot

where:
- v = [v_x, v_y, v_z, omega_x, omega_y, omega_z]^T is the twist
  (linear velocity + angular velocity)
- q_dot is the vector of joint velocities
- J is a 6 x n matrix (n = number of joints)

The Jacobian is fundamental for:
1. Velocity control: Convert desired end-effector velocity to joint velocities
2. Force/torque mapping: tau = J^T * F (joint torques from end-effector forces)
3. Singularity analysis: det(J^T * J) = 0 at singularities
4. Inverse kinematics: Numerical IK uses J^-1 or J^+ (pseudoinverse)

For a revolute joint j:
    J_linear_j = z_{j-1} x (p_end - p_j)
    J_angular_j = z_{j-1}

where z_{j-1} is the joint axis, p_j is joint j position, and p_end is end-effector position.
"""

import numpy as np
from .forward_kinematics import ForwardKinematics


class Jacobian:
    """
    Compute and analyze the Jacobian matrix for a serial manipulator.

    Attributes:
        link_params: Base DH parameters
        dh_convention: 'standard' or 'modified'
        fk: ForwardKinematics instance
    """

    def __init__(self, link_params, dh_convention='modified'):
        """
        Initialize Jacobian calculator.

        Args:
            link_params: List of dicts with base DH parameters
            dh_convention: DH convention to use
        """
        self.link_params = link_params
        self.dh_convention = dh_convention
        self.fk = ForwardKinematics(link_params, dh_convention)

    def compute(self, joint_angles):
        """
        Compute the geometric Jacobian matrix.

        For each joint j, the j-th column of J contains:
        - Linear velocity component: z_{j-1} x (p_end - p_j)
        - Angular velocity component: z_{j-1}

        Args:
            joint_angles: Array of joint angles in radians

        Returns:
            6 x n Jacobian matrix
        """
        joint_angles = np.asarray(joint_angles)
        n_joints = len(joint_angles)
        J = np.zeros((6, n_joints))

        # Get all link frames
        transforms = self.fk.get_all_transforms(joint_angles)

        # End-effector position
        p_end = self.fk.get_position(joint_angles)

        for j in range(n_joints):
            # Get the z-axis of frame j (joint j axis direction)
            if j == 0:
                # First joint axis in base frame
                z_j = np.array([0, 0, 1])
                p_j = np.array([0, 0, 0])
            else:
                # Transform local z-axis to base frame
                z_j = transforms[j][:3, 2]
                p_j = transforms[j][:3, 3]

            # Linear velocity component: z_j x (p_end - p_j)
            J[:3, j] = np.cross(z_j, p_end - p_j)

            # Angular velocity component: z_j
            J[3:6, j] = z_j

        return J

    def compute_pseudoinverse(self, joint_angles):
        """
        Compute the Moore-Penrose pseudoinverse of the Jacobian.

        J^+ = J^T * (J * J^T)^-1

        Used for:
        - Resolved motion rate control: q_dot = J^+ * v_desired
        - Null space projection: q_dot = J^+ * v + (I - J^+ * J) * q_null

        Args:
            joint_angles: Array of joint angles in radians

        Returns:
            n x 6 pseudoinverse Jacobian
        """
        J = self.compute(joint_angles)
        # Use thin SVD for numerical stability: J = U @ diag(S) @ Vt
        U, S, Vt = np.linalg.svd(J, full_matrices=False)
        k = len(S)

        # Compute pseudoinverse with singularity handling
        S_inv = np.zeros(k)
        for i, s in enumerate(S):
            if s > 1e-6:
                S_inv[i] = 1.0 / s

        # J^+ = V @ diag(S_inv) @ U^T  ->  (n, m)
        J_pinv = Vt.T @ np.diag(S_inv) @ U.T
        return J_pinv

    def compute_manipulability(self, joint_angles):
        """
        Compute manipulability index (Yoshikawa manipulability).

        w = sqrt(det(J * J^T))

        This measures how "far" the robot is from a singularity.
        - w = 0: singular configuration
        - w large: good dexterity

        Alternative: m = sqrt(trace(J * J^T)) = sum of singular values

        Args:
            joint_angles: Array of joint angles in radians

        Returns:
            Manipulability index (scalar)
        """
        J = self.compute(joint_angles)
        M = J[:3, :] @ J[:3, :].T  # Linear manipulability
        return np.sqrt(max(0, np.linalg.det(M)))

    def compute_singularity_index(self, joint_angles):
        """
        Compute condition number of the linear Jacobian.

        kappa = sigma_max / sigma_min

        - kappa = inf: singular
        - kappa close to 1: well-conditioned

        Args:
            joint_angles: Array of joint angles in radians

        Returns:
            Condition number of the linear Jacobian
        """
        J = self.compute(joint_angles)[:3, :]
        singular_values = np.linalg.svd(J, compute_uv=False)
        if singular_values[-1] < 1e-10:
            return np.inf
        return singular_values[0] / singular_values[-1]

    def compute_inertia_matrix(self, joint_angles):
        """
        Compute the inertia matrix approximation.

        For a simplified analysis, we compute J^T * J which relates to
        the manipulability ellipsoid.

        The manipulability ellipsoid has axes aligned with the eigenvectors
        of (J * J^T) and lengths proportional to the singular values.

        Args:
            joint_angles: Array of joint angles in radians

        Returns:
            6x6 matrix J^T * J
        """
        J = self.compute(joint_angles)
        return J.T @ J

    def get_manipulability_ellipsoid(self, joint_angles, n_points=50):
        """
        Compute points on the manipulability ellipsoid.

        The manipulability ellipsoid shows the achievable instantaneous
        end-effector velocities for unit joint velocities.

        Args:
            joint_angles: Array of joint angles in radians
            n_points: Number of points on ellipsoid surface

        Returns:
            Array of points on the ellipsoid surface
        """
        J = self.compute(joint_angles)
        U, S, Vt = np.linalg.svd(J)

        # Generate points on unit sphere
        theta = np.linspace(0, 2 * np.pi, n_points)
        phi = np.linspace(0, np.pi, n_points // 2)
        theta_grid, phi_grid = np.meshgrid(theta, phi)

        # Unit sphere points
        sphere_pts = np.array([
            np.sin(phi_grid) * np.cos(theta_grid),
            np.sin(phi_grid) * np.sin(theta_grid),
            np.cos(phi_grid)
        ]).reshape(3, -1)

        # Transform by J
        ellipsoid_pts = U @ S[:3, np.newaxis] * sphere_pts
        return ellipsoid_pts.T
