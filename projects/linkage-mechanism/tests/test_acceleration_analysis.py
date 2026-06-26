"""Tests for acceleration analysis module."""

import pytest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.position_analysis import FourBarParams
from src.acceleration_analysis import (
    acceleration_analysis,
    compute_linear_acceleration,
)


class TestAccelerationAnalysis:
    """Test acceleration analysis."""

    def test_acceleration_crank_rocker(self):
        """Acceleration analysis for crank-rocker mechanism."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        omega2 = 1.0
        alpha3, alpha4 = acceleration_analysis(params, np.pi/4, omega2, 0.0)
        assert not np.isnan(alpha3)
        assert not np.isnan(alpha4)

    def test_acceleration_at_multiple_angles(self):
        """Acceleration should be computed at multiple crank angles."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        omega2 = 1.0
        for i in range(360):
            theta2 = 2 * np.pi * i / 360
            alpha3, alpha4 = acceleration_analysis(params, theta2, omega2, 0.0)
            assert not np.isnan(alpha3)
            assert not np.isnan(alpha4)

    def test_acceleration_with_input_acceleration(self):
        """Non-zero input acceleration should affect output."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        omega2 = 1.0

        alpha3_a, alpha4_a = acceleration_analysis(params, np.pi/4, omega2, 0.0)
        alpha3_b, alpha4_b = acceleration_analysis(params, np.pi/4, omega2, 5.0)

        # Different input accelerations should give different results
        assert abs(alpha3_a - alpha3_b) > 0.01 or abs(alpha4_a - alpha4_b) > 0.01

    def test_linear_acceleration(self):
        """Linear acceleration should return valid results."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        accelerations = compute_linear_acceleration(params, np.pi/4, 1.0, 0.0)
        assert 'A' in accelerations
        assert 'B' in accelerations
        assert 'C' in accelerations
        assert 'alpha3' in accelerations
        assert 'alpha4' in accelerations
        assert not np.isnan(accelerations['A'][0])
        assert not np.isnan(accelerations['B'][0])
        assert not np.isnan(accelerations['C'][0])

    def test_acceleration_units(self):
        """Acceleration should scale correctly with input velocity."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        omega2_1 = 1.0
        omega2_2 = 2.0

        alpha3_1, alpha4_1 = acceleration_analysis(params, np.pi/4, omega2_1, 0.0)
        alpha3_2, alpha4_2 = acceleration_analysis(params, np.pi/4, omega2_2, 0.0)

        # With double velocity, centripetal terms double quadratically
        # So acceleration should increase
        assert abs(alpha3_2) > abs(alpha3_1) or abs(alpha4_2) > abs(alpha4_1)
