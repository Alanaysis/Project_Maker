"""
DH Parameters Module / DH参数模块

Denavit-Hartenberg (DH) parameters are a standard convention for modeling
robot kinematics. They define the relationship between adjacent links using
four parameters:

Standard DH Parameters (a_i, alpha_i, d_i, theta_i):
- a_i: Link length (distance along x_i from z_{i-1} to z_i)
- alpha_i: Link twist (angle around x_i from z_{i-1} to z_i)
- d_i: Link offset (distance along z_i from x_{i-1} to x_i)
- theta_i: Joint angle (angle around z_i from x_{i-1} to x_i)

Modified DH Parameters (alpha_{i-1}, a_{i-1}, d_i, theta_i):
- alpha_{i-1}: Link twist (angle around x_{i-1} from z_{i-1} to z_i)
- a_{i-1}: Link length (distance along x_{i-1} from z_{i-1} to z_i)
- d_i: Link offset (distance along z_i from x_{i-1} to x_i)
- theta_i: Joint angle (angle around z_i from x_{i-1} to x_i)

The key difference: Standard DH uses the common normal between two consecutive
z-axes as the x-axis, while Modified DH places the x-axis at the base of
the z-axis (simpler for serial manipulators).
"""

import numpy as np


def standard_dh_transform(a, alpha, d, theta):
    """
    Compute homogeneous transformation matrix using Standard DH parameters.

    The standard DH transformation matrix T_i^{i-1} transforms coordinates
    from frame i to frame i-1:

        T = [cos(theta)   -sin(theta)*cos(alpha)   sin(theta)*sin(alpha)   a*cos(theta) ]
            [sin(theta)    cos(theta)*cos(alpha)  -cos(theta)*sin(alpha)  a*sin(theta) ]
            [0             sin(alpha)              cos(alpha)               d           ]
            [0             0                       0                        1           ]

    Args:
        a: Link length (mm)
        alpha: Link twist angle (radians)
        d: Link offset (mm)
        theta: Joint angle (radians)

    Returns:
        4x4 homogeneous transformation matrix
    """
    ct = np.cos(theta)
    st = np.sin(theta)
    ca = np.cos(alpha)
    sa = np.sin(alpha)

    T = np.array([
        [ct,    -st * ca,  st * sa,  a * ct],
        [st,     ct * ca, -ct * sa,  a * st],
        [0,      sa,       ca,        d     ],
        [0,      0,        0,         1     ]
    ])
    return T


def modified_dh_transform(alpha, a, d, theta):
    """
    Compute homogeneous transformation matrix using Modified DH parameters.

    The modified DH transformation matrix T_i^{i-1} transforms coordinates
    from frame i to frame i-1:

        T = [cos(theta)  -sin(theta)  0   a]
            [sin(theta)*cos(alpha)  cos(theta)*cos(alpha)  -sin(alpha)  -d*sin(alpha)]
            [sin(theta)*sin(alpha)  cos(theta)*sin(alpha)   cos(alpha)  d*cos(alpha)]
            [0                      0                      0              1        ]

    Modified DH is often preferred for robot arms because:
    - Revolute joint axes are parallel to z_i
    - Each x_i is along the common normal between z_{i-1} and z_i
    - Simpler for serial manipulators with revolute joints

    Args:
        alpha: Link twist angle (radians)
        a: Link length (mm)
        d: Link offset (mm)
        theta: Joint angle (radians)

    Returns:
        4x4 homogeneous transformation matrix
    """
    ct = np.cos(theta)
    st = np.sin(theta)
    ca = np.cos(alpha)
    sa = np.sin(alpha)

    T = np.array([
        [ct, -st,    0, a],
        [st * ca, ct * ca, -sa, -d * sa],
        [st * sa, ct * sa,  ca, d * ca],
        [0,       0,       0,  1        ]
    ])
    return T


def compute_forward_dh(link_params, convention='standard'):
    """
    Compute forward transformation by multiplying individual DH matrices.

    The overall transformation from base to end-effector is:
        T_0^n = T_0^1 * T_1^2 * ... * T_{n-1}^n

    Each T_i^{i+1} is computed from the DH parameters of joint i+1.

    Args:
        link_params: List of dicts with keys 'a', 'alpha', 'd', 'theta'
                     (joint angles must be provided as 'theta')
        convention: 'standard' or 'modified'

    Returns:
        Overall homogeneous transformation matrix T_0^n
    """
    if convention == 'standard':
        transform_fn = standard_dh_transform
    else:
        transform_fn = modified_dh_transform

    T = np.eye(4)
    for params in link_params:
        T = T @ transform_fn(**params)
    return T


def compute_all_transforms(link_params, convention='standard'):
    """
    Compute all intermediate transformation matrices.

    Returns a list where result[i] is the transformation from base to frame i+1.

    Args:
        link_params: List of dicts with DH parameters
        convention: 'standard' or 'modified'

    Returns:
        List of homogeneous transformation matrices
    """
    if convention == 'standard':
        transform_fn = standard_dh_transform
    else:
        transform_fn = modified_dh_transform

    transforms = []
    T = np.eye(4)
    for params in link_params:
        T = T @ transform_fn(**params)
        transforms.append(T.copy())
    return transforms


def dh_to_link_description(dh_params, convention='standard'):
    """
    Convert DH parameters to a human-readable link description.

    Args:
        dh_params: List of dicts with DH parameters
        convention: 'standard' or 'modified'

    Returns:
        List of strings describing each link
    """
    links = []
    for i, params in enumerate(dh_params):
        theta_deg = np.degrees(params['theta'])
        alpha_deg = np.degrees(params['alpha'])
        link_desc = (
            f"Link {i}: theta={theta_deg:7.2f}°, "
            f"d={params['d']:8.2f}mm, "
            f"a={params['a']:8.2f}mm, "
            f"alpha={alpha_deg:8.2f}°"
        )
        links.append(link_desc)
    return links
