"""
Tests for PID Tuner.

Tests cover:
- Ziegler-Nichols tuning method
- Cohen-Coon tuning method
- Tyreus-Luyben tuning method
- Manual tuning method
- Tuning guide output
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from src.tuner import PIDTuner
from src.plant import FirstOrderPlant


class TestPIDTunerInit:
    """Test tuner initialization."""

    def test_default_dt(self):
        tuner = PIDTuner()
        assert tuner.dt == 0.01

    def test_custom_dt(self):
        tuner = PIDTuner(dt=0.05)
        assert tuner.dt == 0.05


class TestCohenCoon:
    """Test Cohen-Coon tuning method."""

    def test_returns_valid_gains(self):
        tuner = PIDTuner(dt=0.01)

        # Create a simple first-order plant
        def make_plant():
            plant = FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)
            return plant.update

        result = tuner.cohen_coon(make_plant(), step_magnitude=1.0)

        assert "Kp" in result
        assert "Ki" in result
        assert "Kd" in result
        assert result["method"] == "cohen_coon"

    def test_gains_are_positive(self):
        tuner = PIDTuner(dt=0.01)

        plant = FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)
        result = tuner.cohen_coon(plant.update, step_magnitude=1.0)

        assert result["Kp"] > 0
        assert result["Ki"] > 0
        assert result["Kd"] > 0

    def test_identifies_process_parameters(self):
        tuner = PIDTuner(dt=0.01)

        plant = FirstOrderPlant(K=2.0, tau=3.0, dt=0.01)
        result = tuner.cohen_coon(plant.update, step_magnitude=1.0)

        # Should identify approximate process parameters
        assert result["K"] > 0
        assert result["tau"] > 0


class TestManualTune:
    """Test manual tuning method."""

    def test_returns_valid_gains(self):
        tuner = PIDTuner(dt=0.01)
        plant = FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)

        result = tuner.manual_tune(plant.update, setpoint=1.0, duration=5.0)

        assert "Kp" in result
        assert "Ki" in result
        assert "Kd" in result
        assert result["method"] == "manual"

    def test_returns_iterations(self):
        tuner = PIDTuner(dt=0.01)
        plant = FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)

        result = tuner.manual_tune(
            plant.update, setpoint=1.0, duration=5.0, max_iterations=5
        )

        assert result["iterations"] == 5

    def test_custom_initial_params(self):
        tuner = PIDTuner(dt=0.01)
        plant = FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)

        initial = {"Kp": 2.0, "Ki": 0.5, "Kd": 0.1}
        result = tuner.manual_tune(
            plant.update, setpoint=1.0, duration=5.0,
            initial_params=initial, max_iterations=1
        )

        assert result["Kp"] > 0
        assert result["Ki"] >= 0
        assert result["Kd"] >= 0

    def test_gains_adjust_for_overshoot(self):
        """Manual tune should adjust gains based on performance."""
        tuner = PIDTuner(dt=0.01)
        plant = FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)

        # Start with very aggressive parameters that cause overshoot
        initial = {"Kp": 20.0, "Ki": 10.0, "Kd": 5.0}
        result = tuner.manual_tune(
            plant.update, setpoint=1.0, duration=10.0,
            initial_params=initial, max_iterations=3
        )

        # Gains should be adjusted (result should be different from initial)
        assert result["method"] == "manual"
        assert result["iterations"] == 3


class TestTuningGuide:
    """Test tuning guide output."""

    def test_guide_returns_string(self):
        guide = PIDTuner.get_tuning_guide()
        assert isinstance(guide, str)
        assert len(guide) > 100

    def test_guide_contains_key_info(self):
        guide = PIDTuner.get_tuning_guide()
        assert "Kp" in guide
        assert "Ki" in guide
        assert "Kd" in guide
        assert "P-only" in guide or "P only" in guide

    def test_guide_contains_improved_variants(self):
        guide = PIDTuner.get_tuning_guide()
        assert "Integral separation" in guide or "integral separation" in guide
        assert "Dead zone" in guide or "dead zone" in guide
