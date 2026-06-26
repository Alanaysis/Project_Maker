"""Tests for velocity analysis module."""

import pytest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.position_analysis import FourBarParams
from src.velocity_analysis import (
    velocity_analysis,
    compute_linear_velocity,
    compute_transmission_angle,
)


class TestVelocityAnalysis:
    """Test velocity analysis."""

    def test_velocity_crank_rocker(self):
        """Velocity analysis for crank-rocker mechanism."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        omega2 = 1.0  # rad/s
        omega3, omega4 = velocity_analysis(params, 0.0, omega2)
        assert not np.isnan(omega3)
        assert not np.isnan(omega4)

    def test_velocity_at_multiple_angles(self):
        """Velocity should be computed at multiple crank angles."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        omega2 = 1.0
        for i in range(360):
            theta2 = 2 * np.pi * i / 360
            omega3, omega4 = velocity_analysis(params, theta2, omega2)
            assert not np.isnan(omega3)
            assert not np.isnan(omega4)

    def test_velocity_zero_input(self):
        """Zero input velocity should give zero output velocities."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        omega3, omega4 = velocity_analysis(params, np.pi/4, 0.0)
        assert abs(omega3) < 1e-10
        assert abs(omega4) < 1e-10

    def test_linear_velocity(self):
        """Linear velocity computation should return valid results."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        velocities = compute_linear_velocity(params, np.pi/4, 1.0)
        assert 'A' in velocities
        assert 'B' in velocities
        assert 'C' in velocities
        assert 'omega3' in velocities
        assert 'omega4' in velocities
        assert not np.isnan(velocities['A'][0])
        assert not np.isnan(velocities['B'][0])
        assert not np.isnan(velocities['C'][0])


class TestTransmissionAngle:
    """Test transmission angle computation."""

    def test_transmission_angle_range(self):
        """Transmission angle should be between 0 and pi/2."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        for i in range(360):
            theta2 = 2 * np.pi * i / 360
            mu = compute_transmission_angle(params, theta2)
            assert 0 <= mu <= np.pi / 2 + 1e-10

    def test_transmission_angle_at_extreme(self):
        """Transmission angle at theta2=0 and theta2=pi."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        mu_0 = compute_transmission_angle(params, 0.0)
        mu_pi = compute_transmission_angle(params, np.pi)
        assert not np.isnan(mu_0)
        assert not np.isnan(mu_pi)

    def test_transmission_angle_quality(self):
        """Transmission angle should be acceptable for good mechanism design."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        min_mu = float('inf')
        for i in range(720):
            theta2 = 2 * np.pi * i / 720
            mu = compute_transmission_angle(params, theta2)
            min_mu = min(min_mu, mu)
        # Minimum should be above 0
        assert min_mu > 0
