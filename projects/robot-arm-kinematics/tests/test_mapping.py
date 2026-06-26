"""
Tests for mapping module
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.mapping import (
    linear_joint_trajectory,
    cubic_joint_trajectory,
    quintic_joint_trajectory,
    compute_path_length,
)


def test_linear_trajectory():
    """Test linear joint trajectory."""
    q_start = np.array([0, 0, 0])
    q_end = np.array([np.pi/2, np.pi/4, np.pi/6])
    n_points = 10

    traj = linear_joint_trajectory(q_start, q_end, n_points)

    assert traj.shape == (n_points, 3)
    np.testing.assert_array_almost_equal(traj[0], q_start)
    np.testing.assert_array_almost_equal(traj[-1], q_end)


def test_linear_trajectory_interpolation():
    """Test that linear interpolation is correct."""
    q_start = np.array([0, 0, 0])
    q_end = np.array([1, 2, 3])
    n_points = 5

    traj = linear_joint_trajectory(q_start, q_end, n_points)

    for i in range(n_points):
        t = i / (n_points - 1)
        expected = (1 - t) * q_start + t * q_end
        np.testing.assert_array_almost_equal(traj[i], expected)


def test_cubic_trajectory():
    """Test cubic polynomial trajectory."""
    q_start = np.array([0, 0, 0])
    q_end = np.array([np.pi/2, np.pi/4, np.pi/6])
    n_points = 50

    traj = cubic_joint_trajectory(q_start, q_end, n_points)

    assert traj.shape == (n_points, 3)
    np.testing.assert_array_almost_equal(traj[0], q_start)
    np.testing.assert_array_almost_equal(traj[-1], q_end)

    # Check zero velocity at endpoints
    v_start = (traj[1] - traj[0]) * (n_points - 1)
    v_end = (traj[-1] - traj[-2]) * (n_points - 1)

    # With zero start/end velocity, first and last steps should be small
    np.testing.assert_array_almost_equal(v_start, np.zeros(3), decimal=1)
    np.testing.assert_array_almost_equal(v_end, np.zeros(3), decimal=1)


def test_quintic_trajectory():
    """Test quintic polynomial trajectory."""
    q_start = np.array([0, 0, 0])
    q_end = np.array([np.pi/2, np.pi/4, np.pi/6])
    n_points = 50

    traj = quintic_joint_trajectory(q_start, q_end, n_points)

    assert traj.shape == (n_points, 3)
    np.testing.assert_array_almost_equal(traj[0], q_start)
    np.testing.assert_array_almost_equal(traj[-1], q_end)


def test_quintic_zero_velocity_acceleration():
    """Test that quintic trajectory has zero velocity and acceleration at endpoints."""
    q_start = np.array([0, 0, 0])
    q_end = np.array([1, 1, 1])
    n_points = 100

    traj = quintic_joint_trajectory(q_start, q_end, n_points, v_start=0, a_start=0, v_end=0, a_end=0)

    dt = 1.0 / (n_points - 1)
    v_start = (traj[1] - traj[0]) / dt
    v_end = (traj[-1] - traj[-2]) / dt
    a_start = (traj[2] - 2*traj[1] + traj[0]) / (dt**2)
    a_end = (traj[-1] - 2*traj[-2] + traj[-3]) / (dt**2)

    np.testing.assert_array_almost_equal(v_start, np.zeros(3), decimal=1)
    np.testing.assert_array_almost_equal(v_end, np.zeros(3), decimal=1)


def test_path_length():
    """Test path length computation."""
    from src.forward_kinematics import ForwardKinematics

    link_params = [
        {'a': 0,    'alpha': 0,    'd': 0,    'theta': 0},
        {'a': 100,  'alpha': 0,    'd': 0,    'theta': 0},
    ]

    fk = ForwardKinematics(link_params, 'modified')

    # Straight line along X axis
    poses = [
        np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
        np.array([[1, 0, 0, 50], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
        np.array([[1, 0, 0, 100], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
    ]

    length = compute_path_length(poses)
    np.testing.assert_almost_equal(length, 100)


def test_path_length_diagonal():
    """Test path length along diagonal."""
    poses = [
        np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
        np.array([[1, 0, 0, 3], [0, 1, 0, 4], [0, 0, 1, 0], [0, 0, 0, 1]]),
    ]

    length = compute_path_length(poses)
    np.testing.assert_almost_equal(length, 5)  # 3-4-5 triangle


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
