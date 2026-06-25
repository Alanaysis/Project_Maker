"""
Tests for Simulator and SimulationResult.

Tests cover:
- Basic simulation run
- Performance metrics computation
- Comparison utility
- Time-varying setpoints
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from src.pid_controller import PIDController
from src.plant import FirstOrderPlant, SecondOrderPlant
from src.simulator import Simulator, SimulationResult, run_comparison


class TestSimulator:
    """Test simulator functionality."""

    def test_basic_simulation(self):
        controller = PIDController(Kp=2.0, Ki=0.5, Kd=0.1, dt=0.01)
        plant = FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)
        sim = Simulator(controller, plant, dt=0.01)

        result = sim.run(setpoint=1.0, duration=5.0)

        assert isinstance(result, SimulationResult)
        assert len(result.time) > 0
        assert len(result.measurement) > 0

    def test_simulation_converges(self):
        """PID should drive plant to setpoint."""
        controller = PIDController(Kp=2.0, Ki=0.5, Kd=0.3, dt=0.01)
        plant = FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)
        sim = Simulator(controller, plant, dt=0.01)

        result = sim.run(setpoint=1.0, duration=15.0)

        # Final measurement should be close to setpoint
        assert abs(result.measurement[-1] - 1.0) < 0.05

    def test_time_varying_setpoint(self):
        controller = PIDController(Kp=2.0, Ki=0.5, Kd=0.1, dt=0.01)
        plant = FirstOrderPlant(K=1.0, tau=1.0, dt=0.01)
        sim = Simulator(controller, plant, dt=0.01)

        # Step setpoint
        def step_setpoint(t):
            return 2.0 if t > 5.0 else 1.0

        result = sim.run(setpoint_fn=step_setpoint, duration=15.0)

        # Should track the setpoint changes
        assert len(result.time) > 0

    def test_custom_dt(self):
        controller = PIDController(Kp=1.0, Ki=0, Kd=0, dt=0.05)
        plant = FirstOrderPlant(K=1.0, tau=1.0, dt=0.05)
        sim = Simulator(controller, plant, dt=0.05)

        result = sim.run(setpoint=1.0, duration=5.0)

        # Check that time steps are correct
        assert len(result.time) == int(5.0 / 0.05) + 1  # +1 for final step


class TestSimulationResult:
    """Test simulation result metrics."""

    def test_summary_returns_dict(self):
        controller = PIDController(Kp=2.0, Ki=0.5, Kd=0.3, dt=0.01)
        plant = FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)
        sim = Simulator(controller, plant, dt=0.01)

        result = sim.run(setpoint=1.0, duration=10.0)
        summary = result.summary()

        assert isinstance(summary, dict)
        assert "overshoot_pct" in summary
        assert "settling_time_s" in summary
        assert "rise_time_s" in summary
        assert "steady_state_error" in summary

    def test_metrics_reasonable_values(self):
        controller = PIDController(Kp=2.0, Ki=0.5, Kd=0.3, dt=0.01)
        plant = FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)
        sim = Simulator(controller, plant, dt=0.01)

        result = sim.run(setpoint=1.0, duration=15.0)

        assert result.overshoot >= 0
        assert result.settling_time >= 0
        assert result.rise_time >= 0
        assert result.steady_state_error >= 0

    def test_repr(self):
        controller = PIDController(Kp=2.0, Ki=0.5, Kd=0.3, dt=0.01)
        plant = FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)
        sim = Simulator(controller, plant, dt=0.01)

        result = sim.run(setpoint=1.0, duration=10.0)
        repr_str = repr(result)

        assert "SimulationResult" in repr_str
        assert "overshoot" in repr_str


class TestRunComparison:
    """Test comparison utility."""

    def test_returns_multiple_results(self):
        configs = {
            "P": {"Kp": 3.0, "Ki": 0.0, "Kd": 0.0},
            "PI": {"Kp": 2.0, "Ki": 0.5, "Kd": 0.0},
        }

        def make_plant():
            return FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)

        results = run_comparison(
            configs, make_plant, setpoint=1.0, duration=10.0, dt=0.01
        )

        assert len(results) == 2
        assert "P" in results
        assert "PI" in results
        assert all(isinstance(r, SimulationResult) for r in results.values())

    def test_each_result_has_metrics(self):
        configs = {
            "Conservative": {"Kp": 1.0, "Ki": 0.1, "Kd": 0.05},
            "Aggressive": {"Kp": 5.0, "Ki": 2.0, "Kd": 1.0},
        }

        def make_plant():
            return FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)

        results = run_comparison(
            configs, make_plant, setpoint=1.0, duration=15.0, dt=0.01
        )

        for name, result in results.items():
            summary = result.summary()
            assert "overshoot_pct" in summary
            assert summary["settling_time_s"] >= 0
