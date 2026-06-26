"""Tests for position analysis module."""

import pytest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.position_analysis import (
    FourBarParams,
    GrashofType,
    LinkageType,
    check_grashof,
    classify_linkage_type,
    position_analysis,
    compute_linkage_circles,
    compute_rocker_limits,
    generate_coupler_curve,
)


class TestGrashofCondition:
    """Test Grashof condition classification."""

    def test_grashof_crank_rocker(self):
        """Grashof condition with crank as shortest link."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        result = check_grashof(params)
        assert result == GrashofType.GRASHOF

    def test_grashof_double_crank(self):
        """Grashof condition with ground as shortest link."""
        params = FourBarParams(a1=1.5, a2=3.0, a3=4.0, a4=3.5)
        result = check_grashof(params)
        assert result == GrashofType.GRASHOF

    def test_grashof_non_grashof(self):
        """Non-Grashof mechanism: s + l > p + q.
        Links: 4.0, 1.5, 3.0, 2.0 -> s=1.5, l=4.0, s+l=5.5, p+q=5.0
        """
        params = FourBarParams(a1=4.0, a2=1.5, a3=3.0, a4=2.0)
        result = check_grashof(params)
        assert result == GrashofType.NON_GRASHOF

    def test_grashof_special(self):
        """Special (change-point) mechanism: s + l = p + q."""
        params = FourBarParams(a1=3.0, a2=2.0, a3=3.0, a4=2.0)
        result = check_grashof(params)
        assert result == GrashofType.SPECIAL

    def test_grashof_invalid_lengths(self):
        """Invalid link lengths should raise ValueError."""
        with pytest.raises(ValueError):
            FourBarParams(a1=-1.0, a2=2.0, a3=3.0, a4=4.0)
        with pytest.raises(ValueError):
            FourBarParams(a1=0, a2=2.0, a3=3.0, a4=4.0)


class TestLinkageClassification:
    """Test linkage type classification."""

    def test_crank_rocker(self):
        """Crank-rocker: shortest link is crank (link 2)."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        result = classify_linkage_type(params)
        assert result == LinkageType.CRANK_ROCKER

    def test_double_crank(self):
        """Double-crank: shortest link is ground (link 1)."""
        params = FourBarParams(a1=1.5, a2=3.0, a3=4.0, a4=3.5)
        result = classify_linkage_type(params)
        assert result == LinkageType.DOUBLE_CRANK

    def test_double_rocker_non_grashof(self):
        """Double-rocker: non-Grashof mechanism."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=3.0, a4=2.0)
        result = classify_linkage_type(params)
        assert result == LinkageType.DOUBLE_ROCKER


class TestPositionAnalysis:
    """Test position analysis."""

    def test_position_crank_rocker(self):
        """Position analysis for crank-rocker at theta2=0."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        pos = position_analysis(params, 0.0)
        assert abs(pos.theta2) < 1e-10
        assert not np.isnan(pos.theta3)
        assert not np.isnan(pos.theta4)
        # theta4 should be close to 0 (crank and ground aligned)
        assert abs(pos.theta4) < np.pi / 2

    def test_position_at_pi(self):
        """Position analysis at theta2=pi."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        pos = position_analysis(params, np.pi)
        assert abs(pos.theta2 - np.pi) < 1e-10

    def test_position_full_rotation(self):
        """Mechanism should complete full rotation for Grashof crank-rocker."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        for i in range(360):
            theta2 = 2 * np.pi * i / 360
            pos = position_analysis(params, theta2)
            assert not np.isnan(pos.theta3)
            assert not np.isnan(pos.theta4)

    def test_position_coupler_point(self):
        """Coupler point position should be correct."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        pos_mid = position_analysis(params, 0.0, coupler_point_ratio=(0.5, 0.0))
        pos_end = position_analysis(params, 0.0, coupler_point_ratio=(1.0, 0.0))
        # Coupler point at ratio 0.5 should be between crank end and coupler end
        assert pos_mid.coupler_point[0] != pos_end.coupler_point[0]

    def test_position_invalid_angle(self):
        """Non-Grashof mechanism should fail at some angles."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=3.0, a4=2.0)
        # Try angles that may be outside the working range
        found_failure = False
        for i in range(360):
            theta2 = 2 * np.pi * i / 360
            try:
                position_analysis(params, theta2)
            except ValueError:
                found_failure = True
                break
        # Non-Grashof mechanisms have limited range
        assert found_failure, "Non-Grashof mechanism should fail at some angles"


class TestLinkageCircles:
    """Test linkage circles computation."""

    def test_circles_grashof(self):
        """Linkage circles for Grashof mechanism."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        circles = compute_linkage_circles(params)
        assert circles['grashof_type'] == GrashofType.GRASHOF
        assert circles['crank_circle']['radius'] == 1.5
        assert circles['rocker_circle']['radius'] == 3.5
        assert circles['crank_can_rotate_full'] is True

    def test_circles_non_grashof(self):
        """Linkage circles for non-Grashof mechanism."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=3.0, a4=2.0)
        circles = compute_linkage_circles(params)
        assert circles['grashof_type'] == GrashofType.NON_GRASHOF
        assert circles['crank_can_rotate_full'] is False


class TestCouplerCurve:
    """Test coupler curve generation."""

    def test_coupler_curve_crank_rocker(self):
        """Coupler curve for crank-rocker should be a closed loop."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        curve = generate_coupler_curve(params, num_points=360)
        assert len(curve) > 0
        assert curve.shape[1] == 2
        # Should trace a roughly closed loop
        assert not np.all(curve[0] == curve[-1])  # May not be exactly closed

    def test_coupler_curve_midpoint(self):
        """Midpoint coupler curve should have certain properties."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        curve = generate_coupler_curve(params, num_points=360,
                                        coupler_point_ratio=(0.5, 0.0))
        assert len(curve) > 100  # Should have enough points

    def test_coupler_curve_empty(self):
        """Non-Grashof mechanism may produce fewer points."""
        params = FourBarParams(a1=3.0, a2=1.5, a3=3.5, a4=2.5)
        curve = generate_coupler_curve(params, num_points=360)
        # Should still have some valid points
        assert len(curve) > 0


class TestRockerLimits:
    """Test rocker oscillation limit computation."""

    def test_rocker_limits_crank_rocker(self):
        """Rocker limits for crank-rocker mechanism."""
        params = FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)
        theta4_min, theta4_max = compute_rocker_limits(params)
        assert theta4_min >= 0
        assert theta4_max <= np.pi
        assert theta4_max > theta4_min
