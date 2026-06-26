"""Tests for dynamic analysis module."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest
from src.dynamic_analysis import DynamicAnalyzer, SystemParameters
from src.motion_laws import MotionLaw, MotionLawCalculator
from src.cam_profile import CamProfileGenerator, FollowerType, FollowerMotion


class TestDynamicAnalyzer:
    """Tests for DynamicAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DynamicAnalyzer()

    def test_inertia_force_calculation(self):
        """Test inertia force is calculated correctly."""
        # F = ma, with m=0.1kg, a=1000mm/s^2 = 1m/s^2
        force = self.analyzer.calculate_inertia_force(acceleration=1000.0, mass=0.1)
        assert abs(force - 0.1) < 0.01

    def test_inertia_force_with_zero_acceleration(self):
        """Test inertia force with zero acceleration."""
        force = self.analyzer.calculate_inertia_force(acceleration=0.0)
        assert abs(force) < 0.001

    def test_natural_frequency(self):
        """Test natural frequency calculation."""
        # f_n = (1/2pi) * sqrt(k/m)
        # k = 500 N/mm = 500000 N/m, m = 0.1 kg
        freq = self.analyzer.calculate_natural_frequency(mass=0.1, stiffness=500.0)
        expected = np.sqrt(500000.0 / 0.1) / (2 * np.pi)
        assert abs(freq - expected) < 0.1

    def test_dynamic_amplification_at_low_speed(self):
        """Test dynamic amplification at low speed (should be ~1)."""
        omega_n = 100.0 * 2 * np.pi  # High natural frequency
        D = self.analyzer.calculate_dynamic_amplification(
            omega=1.0, natural_freq=100.0
        )
        assert D < 1.1  # Should be close to 1 at low speed ratio

    def test_dynamic_amplification_at_resonance(self):
        """Test dynamic amplification near resonance (should be > 1)."""
        D = self.analyzer.calculate_dynamic_amplification(
            omega=60.0, natural_freq=10.0
        )
        # At resonance (r = 1), amplification should be significant
        assert D > 1.0

    def test_contact_loss_check(self):
        """Test contact loss detection."""
        generator = CamProfileGenerator(30.0, 8.0)
        profile = generator.generate_profile(
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
        
        # With adequate spring, no contact loss
        params = SystemParameters(
            follower_mass=0.1,
            spring_stiffness=500.0,
            spring_preload=100.0  # High preload
        )
        contact_status, has_loss = self.analyzer.check_contact_loss(profile, params, 10.0)
        assert has_loss == False

    def test_dynamic_force_analysis(self):
        """Test dynamic force analysis produces valid results."""
        generator = CamProfileGenerator(30.0, 8.0)
        profile = generator.generate_profile(
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
        
        params = SystemParameters(
            follower_mass=0.1,
            spring_stiffness=500.0,
            spring_preload=10.0
        )
        
        result = self.analyzer.analyze_dynamic_forces(profile, params)
        
        assert len(result.inertia_force) == 360
        assert len(result.spring_force) == 360
        assert len(result.total_force) == 360
        assert result.natural_frequency > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
