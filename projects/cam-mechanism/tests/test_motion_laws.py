"""Tests for motion laws module."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest
from src.motion_laws import MotionLaw, MotionLawCalculator, MotionResult


class TestMotionLawCalculator:
    """Tests for MotionLawCalculator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calc = MotionLawCalculator(lift=20.0, omega=10.0)

    def test_uniform_motion_displacement(self):
        """Test that uniform motion displacement increases linearly."""
        result = self.calc.calculate(MotionLaw.UNIFORM, 180.0, 90.0)
        # At midpoint, displacement should be half the lift
        assert abs(result.displacement - 10.0) < 0.1

    def test_uniform_motion_at_start(self):
        """Test uniform motion at start (theta=0)."""
        result = self.calc.calculate(MotionLaw.UNIFORM, 180.0, 0.0)
        assert result.displacement == pytest.approx(0.0, abs=0.01)

    def test_uniform_motion_at_end(self):
        """Test uniform motion at end (theta=phi)."""
        result = self.calc.calculate(MotionLaw.UNIFORM, 180.0, 180.0)
        assert result.displacement == pytest.approx(20.0, abs=0.1)

    def test_parabolic_motion(self):
        """Test parabolic motion has correct midpoint displacement."""
        result = self.calc.calculate(MotionLaw.PARABOLIC, 180.0, 90.0)
        # At midpoint of parabolic motion, displacement should be half
        assert abs(result.displacement - 10.0) < 0.1

    def test_cycloidal_motion(self):
        """Test cycloidal motion at midpoint."""
        result = self.calc.calculate(MotionLaw.CYCLOIDAL, 180.0, 90.0)
        # At midpoint, cycloidal displacement should be half the lift
        assert abs(result.displacement - 10.0) < 0.1

    def test_polynomial_motion_endpoints(self):
        """Test polynomial motions have zero velocity at boundaries."""
        for law in [MotionLaw.POLYNOMIAL_3, MotionLaw.POLYNOMIAL_4, MotionLaw.POLYNOMIAL_5]:
            result_start = self.calc.calculate(law, 180.0, 0.0)
            result_end = self.calc.calculate(law, 180.0, 180.0)
            # Velocity should be zero at boundaries for polynomial motions
            assert abs(result_start.velocity) < 1.0
            assert abs(result_end.velocity) < 1.0

    def test_sinusoidal_motion(self):
        """Test sinusoidal motion."""
        result = self.calc.calculate(MotionLaw.SINUSOIDAL, 180.0, 90.0)
        assert abs(result.displacement - 10.0) < 0.1

    def test_motion_result_type(self):
        """Test that MotionResult has correct fields."""
        result = MotionResult(displacement=10.0, velocity=5.0, acceleration=2.0, jerk=1.0)
        assert result.displacement == 10.0
        assert result.velocity == 5.0
        assert result.acceleration == 2.0
        assert result.jerk == 1.0

    def test_velocity_scaling_with_omega(self):
        """Test that velocity scales linearly with omega."""
        calc1 = MotionLawCalculator(lift=20.0, omega=10.0)
        calc2 = MotionLawCalculator(lift=20.0, omega=20.0)
        
        result1 = calc1.calculate(MotionLaw.UNIFORM, 180.0, 90.0)
        result2 = calc2.calculate(MotionLaw.UNIFORM, 180.0, 90.0)
        
        # Velocity should double when omega doubles
        assert abs(result2.velocity - 2 * result1.velocity) < 0.1

    def test_acceleration_scaling_with_omega(self):
        """Test that acceleration scales with omega squared."""
        calc1 = MotionLawCalculator(lift=20.0, omega=10.0)
        calc2 = MotionLawCalculator(lift=20.0, omega=20.0)
        
        result1 = calc1.calculate(MotionLaw.CYCLOIDAL, 180.0, 45.0)
        result2 = calc2.calculate(MotionLaw.CYCLOIDAL, 180.0, 45.0)
        
        # Acceleration should quadruple when omega doubles
        assert abs(result2.acceleration - 4 * result1.acceleration) / abs(result1.acceleration) < 0.01

    def test_motion_law_info(self):
        """Test that motion law info is available."""
        info = self.calc.get_motion_law_info(MotionLaw.CYCLOIDAL)
        assert 'name' in info
        assert 'smoothness' in info
        assert 'speed_range' in info
        assert 'peak_acc_factor' in info
        assert 'description' in info

    def test_clipping(self):
        """Test that theta is clipped to [0, phase_angle]."""
        result = self.calc.calculate(MotionLaw.UNIFORM, 180.0, 200.0)
        assert result.displacement == pytest.approx(20.0, abs=0.1)

        result = self.calc.calculate(MotionLaw.UNIFORM, 180.0, -10.0)
        assert result.displacement == pytest.approx(0.0, abs=0.01)

    def test_all_motion_laws_produce_valid_results(self):
        """Test all motion laws produce valid numerical results."""
        for law in MotionLaw:
            result = self.calc.calculate(law, 180.0, 90.0)
            assert isinstance(result, MotionResult)
            assert isinstance(result.displacement, float)
            assert isinstance(result.velocity, float)
            assert isinstance(result.acceleration, float)
            assert isinstance(result.jerk, float)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
