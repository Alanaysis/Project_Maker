"""Tests for cam profile generation module."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest
from src.cam_profile import (
    CamProfileGenerator, CamGeometry, FollowerType, FollowerMotion
)
from src.motion_laws import MotionLaw


class TestCamProfileGenerator:
    """Tests for CamProfileGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = CamProfileGenerator(base_radius=30.0, roller_radius=8.0)
        
        self.base_params = dict(
            lift=20.0,
            rise_angle=120.0,
            rise_dwell_angle=60.0,
            return_angle=120.0,
            return_dwell_angle=60.0,
            omega=10.0,
            motion_law=MotionLaw.CYCLOIDAL
        )

    def test_translating_roller_profile_generation(self):
        """Test generating profile for translating roller follower."""
        profile = self.generator.generate_profile(
            follower_type=FollowerType.ROLLER,
            follower_motion=FollowerMotion.TRANSLATING,
            **self.base_params
        )
        
        assert isinstance(profile, CamGeometry)
        assert profile.base_radius == 30.0
        assert profile.lift == 20.0
        assert len(profile.profile_x) == len(profile.profile_y)
        assert profile.roller_radius == 8.0

    def test_translating_flat_foot_profile(self):
        """Test generating profile for flat-foot follower."""
        profile = self.generator.generate_profile(
            follower_type=FollowerType.FLAT_FOOT,
            follower_motion=FollowerMotion.TRANSLATING,
            **self.base_params
        )
        
        assert isinstance(profile, CamGeometry)
        assert len(profile.profile_x) > 0

    def test_translating_pin_profile(self):
        """Test generating profile for pin follower."""
        profile = self.generator.generate_profile(
            follower_type=FollowerType.PIN,
            follower_motion=FollowerMotion.TRANSLATING,
            **self.base_params
        )
        
        assert isinstance(profile, CamGeometry)
        assert len(profile.profile_x) == 360

    def test_offset_translating_profile(self):
        """Test generating profile for offset translating follower."""
        profile = self.generator.generate_profile(
            follower_type=FollowerType.ROLLER,
            follower_motion=FollowerMotion.OFFSET_TRANSLATING,
            offset=10.0,
            **self.base_params
        )
        
        assert isinstance(profile, CamGeometry)
        assert profile.offset == 10.0

    def test_oscillating_profile(self):
        """Test generating profile for oscillating follower."""
        profile = self.generator.generate_profile(
            follower_type=FollowerType.ROLLER,
            follower_motion=FollowerMotion.OSCILLATING,
            link_length=100.0,
            oscillation_angle=20.0,
            **self.base_params
        )
        
        assert isinstance(profile, CamGeometry)
        assert profile.link_length == 100.0

    def test_profile_is_closed_curve(self):
        """Test that the profile forms a closed curve."""
        profile = self.generator.generate_profile(
            follower_type=FollowerType.ROLLER,
            follower_motion=FollowerMotion.TRANSLATING,
            **self.base_params
        )
        
        # The first and last points should be close (closed curve)
        dx = profile.profile_x[0] - profile.profile_x[-1]
        dy = profile.profile_y[0] - profile.profile_y[-1]
        distance = np.sqrt(dx**2 + dy**2)
        assert distance < 1.0  # Should be essentially zero

    def test_base_circle_is_respected(self):
        """Test that the pitch curve is outside the base circle."""
        profile = self.generator.generate_profile(
            follower_type=FollowerType.ROLLER,
            follower_motion=FollowerMotion.TRANSLATING,
            **self.base_params
        )
        
        # For roller follower, pitch curve = profile + roller_radius
        for i in range(len(profile.profile_x)):
            r = np.sqrt(profile.profile_x[i]**2 + profile.profile_y[i]**2)
            pitch_r = r + self.generator.roller_radius
            assert pitch_r >= profile.base_radius - 0.1

    def test_different_motion_laws_produce_different_profiles(self):
        """Test that different motion laws produce different profiles."""
        profiles = []
        for law in [MotionLaw.CYCLOIDAL, MotionLaw.PARABOLIC, MotionLaw.POLYNOMIAL_5]:
            profile = self.generator.generate_profile(
                follower_type=FollowerType.ROLLER,
                follower_motion=FollowerMotion.TRANSLATING,
                motion_law=law,
                **{k: v for k, v in self.base_params.items() if k != 'motion_law'}
            )
            profiles.append(profile)
        
        # Profiles should be different
        for i in range(len(profiles)):
            for j in range(i + 1, len(profiles)):
                dx = profiles[i].profile_x - profiles[j].profile_x
                dy = profiles[i].profile_y - profiles[j].profile_y
                diff = np.sqrt(dx**2 + dy**2)
                assert np.max(diff) > 0.1  # Should be noticeably different


class TestPressureAngleCalculation:
    """Tests for pressure angle calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = CamProfileGenerator(base_radius=30.0, roller_radius=8.0)

    def test_pressure_angle_calculation(self):
        """Test that pressure angle calculation works."""
        profile = self.generator.generate_profile(
            follower_type=FollowerType.ROLLER,
            follower_motion=FollowerMotion.TRANSLATING,
            motion_law=MotionLaw.CYCLOIDAL,
            lift=20.0,
            rise_angle=120.0,
            rise_dwell_angle=60.0,
            return_angle=120.0,
            return_dwell_angle=60.0,
            omega=10.0
        )
        
        angles, pressure_angles = self.generator.calculate_pressure_angle(profile)
        
        assert len(angles) == len(pressure_angles)
        assert np.all(pressure_angles >= -90)  # Pressure angle should be reasonable
        assert np.all(pressure_angles <= 90)


class TestCurvatureCalculation:
    """Tests for curvature calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = CamProfileGenerator(base_radius=30.0, roller_radius=8.0)

    def test_curvature_calculation(self):
        """Test that curvature calculation works."""
        profile = self.generator.generate_profile(
            follower_type=FollowerType.ROLLER,
            follower_motion=FollowerMotion.TRANSLATING,
            motion_law=MotionLaw.CYCLOIDAL,
            lift=20.0,
            rise_angle=120.0,
            rise_dwell_angle=60.0,
            return_angle=120.0,
            return_dwell_angle=60.0,
            omega=10.0
        )
        
        curvature_radius, cx, cy = self.generator.calculate_curvature(profile)
        
        assert len(curvature_radius) == len(profile.profile_x)
        assert len(cx) == len(profile.profile_x)
        assert len(cy) == len(profile.profile_x)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
