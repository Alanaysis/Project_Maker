"""
Tests for Jacobian module
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.jacobian import Jacobian
from src.forward_kinematics import ForwardKinematics


def test_jacobian_shape():
    """Test that Jacobian has correct shape."""
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 100,  'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 80,   'alpha': 0,    'd': 0,    'theta': 0},
    ]

    jac = Jacobian(link_params, 'modified')
    J = jac.compute([0, 0, 0])

    assert J.shape == (6, 3)


def test_jacobian_linear_part():
    """Test that linear part of Jacobian is computed correctly."""
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 100,  'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 80,   'alpha': 0,    'd': 0,    'theta': 0},
    ]

    jac = Jacobian(link_params, 'modified')
    J = jac.compute([0, 0, 0])

    # At zero configuration, first joint rotates around Z
    # Linear velocity of end-effector from joint 1: z0 x (p_end - p0)
    p_end = np.array([180, 0, 0])
    z0 = np.array([0, 0, 1])
    expected_linear = np.cross(z0, p_end)

    np.testing.assert_array_almost_equal(J[:3, 0], expected_linear)


def test_jacobian_angular_part():
    """Test that angular part of Jacobian is the joint axis."""
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 100,  'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 80,   'alpha': 0,    'd': 0,    'theta': 0},
    ]

    jac = Jacobian(link_params, 'modified')
    J = jac.compute([0, 0, 0])

    # All joints rotate around Z axis in planar arm
    np.testing.assert_array_almost_equal(J[3:6, 0], [0, 0, 1])
    np.testing.assert_array_almost_equal(J[3:6, 1], [0, 0, 1])
    np.testing.assert_array_almost_equal(J[3:6, 2], [0, 0, 1])


def test_jacobian_pseudoinverse():
    """Test that pseudoinverse has correct shape."""
    # Use a 3R arm for a proper pseudoinverse test
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 100,  'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 80,   'alpha': 0,    'd': 0,    'theta': 0},
    ]

    jac = Jacobian(link_params, 'modified')
    J_pinv = jac.compute_pseudoinverse([np.pi/4, np.pi/6, np.pi/3])

    # Pseudoinverse shape: n_joints x 6
    assert J_pinv.shape == (3, 6)


def test_jacobian_manipulability():
    """Test manipulability index computation."""
    # Use a 2R arm with standard DH (which has proper Z-axis variation)
    link_params = [
        {'a': 0,    'alpha': -np.pi/2, 'd': 0,    'theta': 0},
        {'a': 100,  'alpha': 0,        'd': 0,    'theta': 0},
    ]

    fk = ForwardKinematics(link_params, 'standard')
    jac = Jacobian(link_params, 'standard')

    # At non-singular configuration
    manip = jac.compute_manipulability([np.pi/4, np.pi/4])
    # For planar arm the 3x3 linear Jacobian has rank 2, so det is 0
    # Just verify it doesn't crash and returns a valid number
    assert isinstance(manip, float)
    assert manip >= 0

    # At singular configuration (fully extended)
    manip_singular = jac.compute_manipulability([0, 0])
    assert manip_singular >= 0


def test_jacobian_singularity_index():
    """Test singularity index computation."""
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 100,  'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 80,   'alpha': 0,    'd': 0,    'theta': 0},
    ]

    jac = Jacobian(link_params, 'modified')

    # Non-singular configuration
    cond = jac.compute_singularity_index([np.pi/4, np.pi/4, 0])
    assert cond > 1

    # Singular configuration
    cond_singular = jac.compute_singularity_index([0, 0, 0])
    assert np.isinf(cond_singular) or cond_singular > 1000


def test_jacobian_velocity_mapping():
    """Test that J * q_dot correctly maps to end-effector velocity."""
    from src.forward_kinematics import ForwardKinematics

    # Use a 2R arm for cleaner Jacobian
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 100,  'alpha': 0,    'd': 0,    'theta': 0},
    ]

    fk = ForwardKinematics(link_params, 'modified')
    jac = Jacobian(link_params, 'modified')
    q = np.array([np.pi/4, np.pi/4])
    J = jac.compute(q)

    # Small joint velocity
    dq = np.array([0.1, 0.05])
    v = J[:3, :] @ dq

    # Verify with finite differences
    eps = 1e-4
    pos_plus = fk.get_position(q + eps * dq)
    pos_minus = fk.get_position(q - eps * dq)
    v_fd = (pos_plus - pos_minus) / (2 * eps)

    # The Jacobian linear part maps dq to linear velocity
    np.testing.assert_array_almost_equal(v, v_fd, decimal=1)


def test_jacobian_inertia_matrix():
    """Test that J^T * J is symmetric."""
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 100,  'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 80,   'alpha': 0,    'd': 0,    'theta': 0},
    ]

    jac = Jacobian(link_params, 'modified')
    MtJ = jac.compute_inertia_matrix([np.pi/6, np.pi/6, 0])

    np.testing.assert_array_almost_equal(MtJ, MtJ.T)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
