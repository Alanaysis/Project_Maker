"""
Tests for inverse kinematics module
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.inverse_kinematics import (
    ik_2r_planar,
    ik_2r_planar_all_solutions,
    ik_numerical,
)
from src.forward_kinematics import fk_2r_arm


def test_ik_2r_elbow_up():
    """Test IK solution for elbow_up configuration."""
    l1, l2 = 100, 80

    # Target position
    target_x, target_y = 120, 60

    theta1, theta2 = ik_2r_planar(target_x, target_y, l1, l2, 'elbow_up')

    # Verify by forward kinematics
    vx, vy = fk_2r_arm(theta1, theta2, l1, l2)
    np.testing.assert_almost_equal(vx, target_x, decimal=4)
    np.testing.assert_almost_equal(vy, target_y, decimal=4)

    # Elbow up means theta2 > 0 (or close to 0)
    assert theta2 >= -1e-6


def test_ik_2r_elbow_down():
    """Test IK solution for elbow_down configuration."""
    l1, l2 = 100, 80

    target_x, target_y = 120, 60

    theta1, theta2 = ik_2r_planar(target_x, target_y, l1, l2, 'elbow_down')

    # Verify by forward kinematics
    vx, vy = fk_2r_arm(theta1, theta2, l1, l2)
    np.testing.assert_almost_equal(vx, target_x, decimal=4)
    np.testing.assert_almost_equal(vy, target_y, decimal=4)

    # Elbow down means theta2 < 0
    assert theta2 <= 1e-6


def test_ik_2r_all_solutions():
    """Test that all IK solutions are returned."""
    l1, l2 = 100, 80
    target_x, target_y = 120, 60

    solutions = ik_2r_planar_all_solutions(target_x, target_y, l1, l2)

    assert len(solutions) == 2

    # Verify each solution
    for theta1, theta2 in solutions:
        vx, vy = fk_2r_arm(theta1, theta2, l1, l2)
        np.testing.assert_almost_equal(vx, target_x, decimal=4)
        np.testing.assert_almost_equal(vy, target_y, decimal=4)


def test_ik_2r_boundary():
    """Test IK at workspace boundaries."""
    l1, l2 = 100, 80

    # At max reach
    theta1, theta2 = ik_2r_planar(l1 + l2, 0, l1, l2)
    np.testing.assert_almost_equal(theta2, 0)

    # At min reach (if l1 != l2)
    if l1 > l2:
        theta1, theta2 = ik_2r_planar(l1 - l2, 0, l1, l2, 'elbow_up')
        np.testing.assert_almost_equal(theta2, np.pi)


def test_ik_2r_outside_workspace():
    """Test that IK raises error for unreachable targets."""
    l1, l2 = 100, 80

    try:
        ik_2r_planar(200, 100, l1, l2)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_ik_2r_near_origin():
    """Test IK when target is near the inner boundary."""
    l1, l2 = 100, 80

    # Target at inner boundary (l1 - l2 = 20)
    theta1, theta2 = ik_2r_planar(20, 0, l1, l2)
    vx, vy = fk_2r_arm(theta1, theta2, l1, l2)
    np.testing.assert_almost_equal(vx, 20, decimal=4)
    np.testing.assert_almost_equal(vy, 0, decimal=4)


def test_ik_numerical_basic():
    """Test numerical IK solver."""
    # Use a simple 2R arm where orientation can be matched
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 100,  'alpha': 0,    'd': 0,    'theta': 0},
    ]

    # Target at (100, 100) with identity orientation
    target = np.eye(4)
    target[0, 3] = 100 * np.sqrt(2) / 2
    target[1, 3] = 100 * np.sqrt(2) / 2

    q = ik_numerical(link_params, target, 'modified', max_iter=200)

    assert q is not None
    assert len(q) == 2

    # Verify
    from src.forward_kinematics import ForwardKinematics
    fk = ForwardKinematics(link_params, 'modified')
    T = fk.compute(q)
    np.testing.assert_array_almost_equal(T[:3, 3], target[:3, 3], decimal=3)


def test_ik_numerical_with_guess():
    """Test numerical IK with initial guess."""
    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 100,  'alpha': 0,    'd': 0,    'theta': 0},
    ]

    target = np.array([
        [1, 0, 0, 100],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ])

    q = ik_numerical(link_params, target, 'modified', initial_guess=[0, 0])

    assert q is not None
    np.testing.assert_almost_equal(q[0], 0, decimal=3)
    np.testing.assert_almost_equal(q[1], 0, decimal=3)


def test_ik_2r_symmetry():
    """Test IK symmetry: two solutions should give same position."""
    l1, l2 = 100, 80
    target_x, target_y = 120, 60

    solutions = ik_2r_planar_all_solutions(target_x, target_y, l1, l2)

    # Both should reach the same target
    for theta1, theta2 in solutions:
        vx, vy = fk_2r_arm(theta1, theta2, l1, l2)
        np.testing.assert_almost_equal(vx, target_x, decimal=4)
        np.testing.assert_almost_equal(vy, target_y, decimal=4)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
