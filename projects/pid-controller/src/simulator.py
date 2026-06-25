"""
Simulator - Run closed-loop PID control simulations.

This module ties together the PID controller and plant models to run
complete closed-loop simulations. It provides:

1. Simple simulation: Run a single PID + plant simulation
2. Multi-scenario: Compare different PID tunings
3. Step response analysis: Compute performance metrics
4. Data collection: Record all signals for plotting
"""

import numpy as np
from typing import Dict, List, Optional, Callable, Any
from .pid_controller import PIDController
from .plant import FirstOrderPlant, SecondOrderPlant


class SimulationResult:
    """Container for simulation results.

    Stores all time-series data and computed performance metrics
    for analysis and plotting.

    Attributes:
        time: Time array (seconds).
        setpoint: Setpoint array.
        measurement: Plant output array.
        error: Error (setpoint - measurement) array.
        control: Control output array.
        p_term: Proportional term array.
        i_term: Integral term array.
        d_term: Derivative term array.
        overshoot: Maximum overshoot percentage.
        settling_time: Time to settle within 2% of setpoint.
        rise_time: Time to go from 10% to 90% of setpoint.
        steady_state_error: Final error value.
        settling_time_5pct: Time to settle within 5% of setpoint.
    """

    def __init__(self, history: Dict[str, np.ndarray]):
        self.time = history["time"]
        self.setpoint = history["setpoint"]
        self.measurement = history["measurement"]
        self.error = history["error"]
        self.control = history["output"]
        self.p_term = history["p_term"]
        self.i_term = history["i_term"]
        self.d_term = history["d_term"]

        # Compute performance metrics
        self._compute_metrics()

    def _compute_metrics(self) -> None:
        """Compute step response performance metrics."""
        if len(self.setpoint) == 0:
            self.overshoot = 0.0
            self.settling_time = float("inf")
            self.settling_time_5pct = float("inf")
            self.rise_time = float("inf")
            self.steady_state_error = float("inf")
            return

        target = self.setpoint[-1]
        if target == 0:
            self.overshoot = 0.0
            self.settling_time = self.time[-1]
            self.settling_time_5pct = self.time[-1]
            self.rise_time = self.time[-1]
            self.steady_state_error = abs(self.error[-1])
            return

        # Overshoot: maximum percentage above setpoint
        max_output = np.max(self.measurement)
        if target > 0:
            self.overshoot = max(0.0, (max_output - target) / abs(target) * 100.0)
        else:
            self.overshoot = max(0.0, (target - max_output) / abs(target) * 100.0)

        # Rise time: time from 10% to 90% of setpoint
        self.rise_time = self._find_rise_time(0.1, 0.9)

        # Settling time: last time the error exceeds 2% of setpoint
        self.settling_time = self._find_settling_time(0.02)

        # Settling time (5% band)
        self.settling_time_5pct = self._find_settling_time(0.05)

        # Steady-state error
        self.steady_state_error = abs(self.error[-1])

    def _find_rise_time(self, low_pct: float, high_pct: float) -> float:
        """Find time to go from low_pct to high_pct of setpoint."""
        target = self.setpoint[-1]
        if target == 0:
            return self.time[-1]

        low_val = low_pct * target
        high_val = high_pct * target

        # Find first crossing of low threshold
        low_idx = np.where(self.measurement >= low_val)[0]
        if len(low_idx) == 0:
            return float("inf")

        # Find first crossing of high threshold after low
        high_idx = np.where(self.measurement[low_idx[0]:] >= high_val)[0]
        if len(high_idx) == 0:
            return float("inf")

        t_low = self.time[low_idx[0]]
        t_high = self.time[low_idx[0] + high_idx[0]]

        return t_high - t_low

    def _find_settling_time(self, band_pct: float) -> float:
        """Find the last time error exceeds band_pct of setpoint."""
        target = self.setpoint[-1]
        if target == 0:
            return self.time[-1]

        band = band_pct * abs(target)

        # Find indices where error is outside the band
        outside_band = np.abs(self.error) > band

        if not np.any(outside_band):
            return 0.0

        # Last index where error was outside band
        last_outside = np.where(outside_band)[0][-1]

        return self.time[last_outside]

    def summary(self) -> Dict[str, float]:
        """Return performance metrics as a dictionary.

        Returns:
            Dictionary with overshoot, settling_time, rise_time,
            steady_state_error, settling_time_5pct.
        """
        return {
            "overshoot_pct": self.overshoot,
            "settling_time_s": self.settling_time,
            "settling_time_5pct_s": self.settling_time_5pct,
            "rise_time_s": self.rise_time,
            "steady_state_error": self.steady_state_error,
        }

    def __repr__(self) -> str:
        return (
            f"SimulationResult(overshoot={self.overshoot:.1f}%, "
            f"settling_time={self.settling_time:.2f}s, "
            f"rise_time={self.rise_time:.2f}s, "
            f"ss_error={self.steady_state_error:.4f})"
        )


class Simulator:
    """Run closed-loop PID control simulations.

    This class connects a PID controller to a plant and runs the
    closed-loop simulation for a specified duration.

    Usage:
        # Create components
        controller = PIDController(Kp=1.0, Ki=0.5, Kd=0.1)
        plant = FirstOrderPlant(K=1.0, tau=2.0)

        # Create simulator and run
        sim = Simulator(controller, plant)
        result = sim.run(setpoint=1.0, duration=10.0)

        # Analyze results
        print(result.summary())
    """

    def __init__(
        self,
        controller: PIDController,
        plant: Any,
        dt: Optional[float] = None,
    ):
        """Initialize simulator.

        Args:
            controller: PIDController instance.
            plant: Plant instance (FirstOrderPlant or SecondOrderPlant).
            dt: Time step. If None, uses controller's dt.
        """
        self.controller = controller
        self.plant = plant
        self.dt = dt or controller.dt

    def run(
        self,
        setpoint: float = 1.0,
        duration: float = 10.0,
        setpoint_fn: Optional[Callable[[float], float]] = None,
    ) -> SimulationResult:
        """Run a closed-loop simulation.

        The control loop at each step:
            1. Read plant output (measurement)
            2. Compute PID control output
            3. Apply control output to plant
            4. Record all signals

        Args:
            setpoint: Constant setpoint value. Default: 1.0
            duration: Simulation duration in seconds. Default: 10.0
            setpoint_fn: Optional function(t) -> setpoint for time-varying
                setpoints. Overrides the constant setpoint parameter.

        Returns:
            SimulationResult with all time-series data and metrics.
        """
        # Reset controller and plant
        self.controller.reset()
        self.plant.reset()

        num_steps = int(duration / self.dt)

        for step in range(num_steps):
            t = step * self.dt

            # Determine setpoint
            if setpoint_fn is not None:
                current_setpoint = setpoint_fn(t)
            else:
                current_setpoint = setpoint

            # Read measurement from plant
            measurement = self.plant.output

            # Compute PID output
            control = self.controller.update(current_setpoint, measurement, t)

            # Apply to plant
            self.plant.update(control)

        # Final step
        t = num_steps * self.dt
        measurement = self.plant.output
        if setpoint_fn is not None:
            current_setpoint = setpoint_fn(t)
        else:
            current_setpoint = setpoint
        self.controller.update(current_setpoint, measurement, t)

        # Return results
        return SimulationResult(self.controller.history)


def run_comparison(
    controller_configs: Dict[str, Dict[str, float]],
    plant_factory: Callable[[], Any],
    setpoint: float = 1.0,
    duration: float = 10.0,
    dt: float = 0.01,
) -> Dict[str, SimulationResult]:
    """Compare multiple PID configurations on the same plant.

    Useful for comparing different tuning methods or parameters.

    Args:
        controller_configs: Dictionary mapping name -> PID parameters.
            Example: {"Aggressive": {"Kp": 2.0, "Ki": 1.0, "Kd": 0.5}}
        plant_factory: Callable that creates a fresh plant instance.
        setpoint: Setpoint value. Default: 1.0
        duration: Simulation duration. Default: 10.0
        dt: Time step. Default: 0.01

    Returns:
        Dictionary mapping name -> SimulationResult.
    """
    results = {}

    for name, params in controller_configs.items():
        controller = PIDController(dt=dt, **params)
        plant = plant_factory()
        sim = Simulator(controller, plant, dt=dt)
        results[name] = sim.run(setpoint=setpoint, duration=duration)

    return results
