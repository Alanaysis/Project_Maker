"""
Tests for forward kinematics module
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.forward_kinematics import fk_2r_arm, ForwardKinematics


def test_fk_2r_zero_angles():
    """2R arm with zero angles should be fully extended along X axis."""
    l1, l2 = 100, 80
    x, y = fk_2r_arm(0, 0, l1, l2)
    np.testing.assert_almost_equal(x, l1 + l2)
    np.testing.assert_almost_equal(y, 0)


def test_fk_2r_90_degrees():
    """2R arm with theta1=90 should point along Y axis."""
    l1, l2 = 100, 80
    x, y = fk_2r_arm(np.pi/2, 0, l1, l2)
    np.testing.assert_almost_equal(x, 0)
    np.testing.assert_almost_equal(y, l1 + l2)


def test_fk_2r_bent():
    """2R arm with both joints at 90 degrees."""
    l1, l2 = 100, 80
    x, y = fk_2r_arm(np.pi/2, np.pi/2, l1, l2)
    np.testing.assert_almost_equal(x, -l2)
    np.testing.assert_almost_equal(y, l1)


def test_fk_2r_full_circle():
    """Test 2R arm at various angles."""
    l1, l2 = 100, 80
    for theta1 in np.linspace(0, 2*np.pi, 10):
        for theta2 in np.linspace(-np.pi, np.pi, 10):
            x, y = fk_2r_arm(theta1, theta2, l1, l2)
            distance = np.sqrt(x**2 + y**2)
            assert abs(l1 - l2) - 1e-6 <= distance <= l1 + l2 + 1e-6


def test_forward_kinematics_class():
    """Test ForwardKinematics class."""
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 100,  'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 80,   'alpha': 0,    'd': 0,    'theta': 0},
    ]
    fk = ForwardKinematics(link_params, 'modified')

    # Zero angles: fully extended
    pos = fk.get_position([0, 0, 0])
    np.testing.assert_almost_equal(pos[0], 180)
    np.testing.assert_almost_equal(pos[1], 0)
    np.testing.assert_almost_equal(pos[2], 0)


def test_forward_kinematics_orientation():
    """Test that orientation is computed correctly."""
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 100,  'alpha': 0,    'd': 0,    'theta': 0},
    ]
    fk = ForwardKinematics(link_params, 'modified')

    R = fk.get_orientation([np.pi/2, 0])
    # Should be rotated 90 degrees around Z
    np.testing.assert_array_almost_equal(R, np.array([
        [0, -1, 0],
        [1, 0, 0],
        [0, 0, 1],
    ]))


def test_forward_kinematics_transform_matrix():
    """Test that transformation matrix is valid."""
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 100,  'alpha': 0,    'd': 0,    'theta': 0},
    ]
    fk = ForwardKinematics(link_params, 'modified')

    T = fk.compute([0, 0])

    # Bottom row
    np.testing.assert_array_almost_equal(T[3], [0, 0, 0, 1])

    # Rotation is orthonormal
    R = T[:3, :3]
    np.testing.assert_array_almost_equal(R @ R.T, np.eye(3))

    # Position
    np.testing.assert_almost_equal(T[0, 3], 100)
    np.testing.assert_almost_equal(T[1, 3], 0)


def test_forward_kinematics_all_transforms():
    """Test that all intermediate transforms are consistent."""
    link_params = [
        {'a': 0,    'alpha': -np.pi/2, 'd': 0,    'theta': 0},
        {'a': 100,  'alpha': 0,        'd': 0,    'theta': 0},
        {'a': 80,   'alpha': 0,        'd': 0,    'theta': 0},
    ]
    fk = ForwardKinematics(link_params, 'modified')

    transforms = fk.get_all_transforms([0, 0, 0])
    assert len(transforms) == 3

    # First transform should be rotation by -pi/2 around Z
    np.testing.assert_array_almost_equal(transforms[0][2, 3], 0)

    # Total should match last transform
    T_total = fk.compute([0, 0, 0])
    np.testing.assert_array_almost_equal(transforms[-1], T_total)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
