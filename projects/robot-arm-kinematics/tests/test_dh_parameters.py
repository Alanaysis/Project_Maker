"""
Tests for DH parameters module
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.dh_parameters import (
    standard_dh_transform,
    modified_dh_transform,
    compute_forward_dh,
    compute_all_transforms,
    dh_to_link_description,
)


def test_standard_dh_identity():
    """DH parameters with zero angles and offsets should give identity."""
    T = standard_dh_transform(a=0, alpha=0, d=0, theta=0)
    expected = np.eye(4)
    np.testing.assert_array_almost_equal(T, expected)


def test_standard_dh_translation():
    """Pure translation in z should only affect d parameter."""
    d = 10
    T = standard_dh_transform(a=0, alpha=0, d=d, theta=0)
    np.testing.assert_almost_equal(T[2, 3], d)
    np.testing.assert_array_almost_equal(T[:3, :3], np.eye(3))


def test_standard_dh_rotation():
    """Pure rotation should only affect rotation matrix."""
    theta = np.pi / 2
    T = standard_dh_transform(a=0, alpha=0, d=0, theta=theta)
    expected_rot = np.array([
        [0, -1, 0],
        [1, 0, 0],
        [0, 0, 1],
    ])
    np.testing.assert_array_almost_equal(T[:3, :3], expected_rot)


def test_modified_dh_identity():
    """Modified DH with zero parameters should give identity."""
    T = modified_dh_transform(alpha=0, a=0, d=0, theta=0)
    expected = np.eye(4)
    np.testing.assert_array_almost_equal(T, expected)


def test_modified_dh_translation():
    """Pure translation in x should only affect a parameter."""
    a = 10
    T = modified_dh_transform(alpha=0, a=a, d=0, theta=0)
    np.testing.assert_almost_equal(T[0, 3], a)
    np.testing.assert_array_almost_equal(T[:3, :3], np.eye(3))


def test_forward_dh_composition():
    """Composing two DH transforms should match manual multiplication."""
    params1 = [{'a': 0, 'alpha': -np.pi/2, 'd': 0, 'theta': 0}]
    params2 = [{'a': 100, 'alpha': 0, 'd': 0, 'theta': 0}]

    T = compute_forward_dh(params1 + params2, 'modified')

    # Position should be at (100, 0, 0) after the two transforms
    np.testing.assert_almost_equal(T[0, 3], 100)
    np.testing.assert_almost_equal(T[1, 3], 0)
    np.testing.assert_almost_equal(T[2, 3], 0)


def test_all_transforms_consistency():
    """All transforms should be consistent with forward computation."""
    params = [
        {'a': 0,    'alpha': -np.pi/2, 'd': 0,     'theta': 0},
        {'a': 100,  'alpha': 0,        'd': 0,     'theta': np.pi/4},
        {'a': 80,   'alpha': 0,        'd': 0,     'theta': np.pi/3},
    ]

    all_T = compute_all_transforms(params, 'modified')
    T_total = compute_forward_dh(params, 'modified')

    # Last transform should equal total
    np.testing.assert_array_almost_equal(all_T[-1], T_total)


def test_link_description():
    """Link description should contain expected strings."""
    params = [
        {'a': 0, 'alpha': -np.pi/2, 'd': 0, 'theta': 0},
        {'a': 100, 'alpha': 0, 'd': 0, 'theta': np.pi/4},
    ]
    links = dh_to_link_description(params)
    assert len(links) == 2
    assert 'Link 0' in links[0]
    assert 'Link 1' in links[1]
    assert '-90.00' in links[0]  # alpha = -pi/2 in degrees


def test_homogeneous_matrix_properties():
    """Homogeneous transformation matrix should have valid properties."""
    T = standard_dh_transform(a=10, alpha=np.pi/4, d=5, theta=np.pi/6)

    # Bottom row should be [0, 0, 0, 1]
    np.testing.assert_array_almost_equal(T[3], [0, 0, 0, 1])

    # Rotation part should be orthonormal
    R = T[:3, :3]
    np.testing.assert_array_almost_equal(R @ R.T, np.eye(3))
    np.testing.assert_almost_equal(np.linalg.det(R), 1)


def test_standard_vs_modified_dh():
    """Test that both conventions produce valid transformation matrices."""
    params_std = {'a': 10, 'alpha': np.pi/3, 'd': 5, 'theta': np.pi/6}
    params_mod = {'a': 10, 'alpha': np.pi/3, 'd': 5, 'theta': np.pi/6}

    T_std = standard_dh_transform(**params_std)
    T_mod = modified_dh_transform(**params_mod)

    # Both should be valid homogeneous transformations
    np.testing.assert_array_almost_equal(T_std[3], [0, 0, 0, 1])
    np.testing.assert_array_almost_equal(T_mod[3], [0, 0, 0, 1])


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
