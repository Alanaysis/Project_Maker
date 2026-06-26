"""
Forward Kinematics Module / 正向运动学模块

Forward kinematics computes the end-effector pose (position and orientation)
given the joint angles. This is the direct problem of robot kinematics.

For a serial manipulator with n joints:
    q = [theta_1, theta_2, ..., theta_n]
    T_base_to_end = f(q)

The result is a 4x4 homogeneous transformation matrix that describes
the end-effector frame relative to the base frame.

Key concepts:
- Homogeneous transformation matrix combines rotation and translation
- T = [R | p]
-     [0 | 1]
  where R is 3x3 rotation matrix and p is 3x1 position vector
- Composition of transformations: T_total = T_0^1 * T_1^2 * ... * T_{n-1}^n
"""

import numpy as np
from .dh_parameters import compute_forward_dh, compute_all_transforms, standard_dh_transform, modified_dh_transform


class ForwardKinematics:
    """
    Forward kinematics solver for serial manipulators.

    Uses DH parameters to compute the end-effector pose from joint angles.

    Attributes:
        dh_convention: 'standard' or 'modified'
        link_params: Base DH parameters (without joint angles)
        n_joints: Number of revolute joints
    """

    def __init__(self, link_params, dh_convention='modified'):
        """
        Initialize forward kinematics solver.

        Args:
            link_params: List of dicts with base DH parameters.
                         For revolute joints, 'theta' will be overridden by joint angles.
                         Example: {'a': 0.3, 'alpha': -np.pi/2, 'd': 0, 'theta': 0}
            dh_convention: DH convention to use ('standard' or 'modified')
        """
        self.dh_convention = dh_convention
        self.link_params = link_params
        self.n_joints = len(link_params)

    def compute(self, joint_angles):
        """
        Compute end-effector pose from joint angles.

        Args:
            joint_angles: Array of joint angles in radians [theta_1, theta_2, ...]

        Returns:
            4x4 homogeneous transformation matrix (base to end-effector)
        """
        joint_angles = np.asarray(joint_angles)
        params = []
        for i, base_param in enumerate(self.link_params):
            param = base_param.copy()
            param['theta'] = joint_angles[i]
            params.append(param)

        return compute_forward_dh(params, self.dh_convention)

    def get_position(self, joint_angles):
        """
        Extract end-effector position from forward kinematics result.

        Args:
            joint_angles: Array of joint angles in radians

        Returns:
            3-element array [x, y, z] in base frame coordinates
        """
        T = self.compute(joint_angles)
        return T[:3, 3]

    def get_orientation(self, joint_angles):
        """
        Extract end-effector orientation as a 3x3 rotation matrix.

        Args:
            joint_angles: Array of joint angles in radians

        Returns:
            3x3 rotation matrix
        """
        T = self.compute(joint_angles)
        return T[:3, :3]

    def get_all_transforms(self, joint_angles):
        """
        Get all intermediate link frames.

        Args:
            joint_angles: Array of joint angles in radians

        Returns:
            List of 4x4 transformation matrices for each link frame
        """
        joint_angles = np.asarray(joint_angles)
        params = []
        for i, base_param in enumerate(self.link_params):
            param = base_param.copy()
            param['theta'] = joint_angles[i]
            params.append(param)

        return compute_all_transforms(params, self.dh_convention)

    def compute_jacobian(self, joint_angles):
        """
        Compute Jacobian using forward kinematics finite differences.
        See jacobian module for analytical computation.
        """
        from .jacobian import Jacobian
        return Jacobian(self.link_params, self.dh_convention).compute(joint_angles)


def fk_2r_arm(theta1, theta2, l1, l2):
    """
    Closed-form forward kinematics for a 2R planar arm.

    A 2R arm has two revolute joints in the XY plane.
    Given link lengths l1, l2 and joint angles theta1, theta2:

        x = l1*cos(theta1) + l2*cos(theta1 + theta2)
        y = l1*sin(theta1) + l2*sin(theta1 + theta2)

    This is the simplest non-trivial example and serves as a great
    starting point for understanding robot kinematics.

    Args:
        theta1: Angle of first joint (radians)
        theta2: Angle of second joint relative to first (radians)
        l1: Length of first link (mm)
        l2: Length of second link (mm)

    Returns:
        (x, y) end-effector position
    """
    x = l1 * np.cos(theta1) + l2 * np.cos(theta1 + theta2)
    y = l1 * np.sin(theta1) + l2 * np.sin(theta1 + theta2)
    return x, y


def fk_puma560(joint_angles):
    """
    Forward kinematics for PUMA 560 robot arm.

    The PUMA 560 is a classic 6-DOF industrial robot. This function
    uses modified DH parameters.

    DH Parameters for PUMA 560 (modified convention):
    | Joint | theta       | d (mm) | a (mm) | alpha (rad) |
    |-------|-------------|--------|--------|-------------|
    | 1     | theta1      | 0      | 0      | -pi/2       |
    | 2     | theta2      | 0      | 0.432  | 0           |
    | 3     | theta3      | 0.149  | 0.020  | -pi/2       |
    | 4     | theta4      | 0.433  | 0      | -pi/2       |
    | 5     | theta5      | 0      | 0      | pi/2        |
    | 6     | theta6      | 0      | 0      | 0           |

    Args:
        joint_angles: Array of 6 joint angles in radians

    Returns:
        4x4 homogeneous transformation matrix
    """
    link_params = [
        {'a': 0,    'alpha': -np.pi/2, 'd': 0,     'theta': 0},
        {'a': 0.432, 'alpha': 0,       'd': 0,     'theta': 0},
        {'a': 0.020, 'alpha': -np.pi/2, 'd': 0.149, 'theta': 0},
        {'a': 0,     'alpha': -np.pi/2, 'd': 0.433, 'theta': 0},
        {'a': 0,     'alpha': np.pi/2,  'd': 0,     'theta': 0},
        {'a': 0,     'alpha': 0,        'd': 0,     'theta': 0},
    ]
    fk = ForwardKinematics(link_params, 'modified')
    return fk.compute(joint_angles)
