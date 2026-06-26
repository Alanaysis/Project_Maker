"""Tests for contact stress module."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest
from src.contact_stress import ContactStressAnalyzer, ContactStressResult
from src.cam_profile import FollowerType


class TestContactStressAnalyzer:
    """Tests for ContactStressAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ContactStressAnalyzer()

    def test_contact_stress_calculation(self):
        """Test Hertz contact stress calculation."""
        result = self.analyzer.calculate_contact_stress(
            normal_force=100.0,      # 100 N
            roller_radius=8.0,        # 8 mm
            cam_radius=30.0,          # 30 mm
            follower_width=10.0,      # 10 mm
            follower_type=FollowerType.ROLLER
        )
        
        assert isinstance(result, ContactStressResult)
        assert result.max_hertz_stress > 0
        assert result.contact_half_width > 0
        assert result.is_safe == True  # 100 MPa should be safe for hardened steel

    def test_contact_stress_with_zero_force(self):
        """Test with zero normal force."""
        result = self.analyzer.calculate_contact_stress(
            normal_force=0.0,
            roller_radius=8.0,
            cam_radius=30.0
        )
        
        assert result.max_hertz_stress == 0.0
        assert result.is_safe is True

    def test_contact_stress_with_large_force(self):
        """Test with large normal force."""
        result = self.analyzer.calculate_contact_stress(
            normal_force=10000.0,     # Large force
            roller_radius=8.0,
            cam_radius=30.0,
            follower_width=10.0
        )
        
        assert result.max_hertz_stress > 0
        # Check if it exceeds allowable stress
        if result.max_hertz_stress > self.analyzer.allowable_stress:
            assert not result.is_safe

    def test_dynamic_force_calculation(self):
        """Test dynamic force calculation."""
        # F = F_spring + m*a + m*g
        force = self.analyzer.calculate_dynamic_force(
            follower_mass=0.1,
            acceleration=1000.0,  # 1000 mm/s^2 = 1 m/s^2
            spring_force=10.0
        )
        
        expected = 10.0 + 0.1 * 1.0 + 0.1 * 9.81
        assert abs(force - expected) < 0.01

    def test_dynamic_force_no_acceleration(self):
        """Test dynamic force with no acceleration."""
        force = self.analyzer.calculate_dynamic_force(
            follower_mass=0.1,
            acceleration=0.0,
            spring_force=10.0
        )
        
        # Should be approximately spring_force + gravity
        expected = 10.0 + 0.1 * 9.81
        assert abs(force - expected) < 0.01

    def test_stress_info(self):
        """Test that stress info is available."""
        info = self.analyzer.get_stress_info()
        assert 'hertz_theory' in info
        assert 'max_stress_location' in info
        assert 'failure_modes' in info
        assert 'mitigation' in info


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
