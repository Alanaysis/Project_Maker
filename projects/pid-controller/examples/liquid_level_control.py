"""
Liquid Level Control Example - PID controller for a tank system.

This example simulates a liquid level control system, such as:
- Water tank level control
- Chemical mixing tank
- Boiler drum level control

The system model:
- First-order (tank with inlet and outlet)
- Setpoint: target liquid level
- Disturbance: outlet flow changes
- Actuator: inlet valve position

Key concepts demonstrated:
- Nonlinear system (valve characteristics)
- Disturbance rejection (outlet flow changes)
- Cascade control concept
- Anti-windup for valve saturation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src import PIDController, FirstOrderPlant, Simulator


class TankPlant:
    """Simulate a liquid level control system.

    Model: first-order system with nonlinear valve
    - A: tank cross-sectional area (m^2)
    - R: outlet flow resistance
    - valve_flow: max flow through valve (m^3/s)
    - outlet_flow: constant outlet flow (m^3/s)

    Mass balance: A * dh/dt = Qin - Qout
    Where:
    - h: liquid level (m)
    - Qin: inlet flow (controlled by valve)
    - Qout: outlet flow (depends on level)
    """

    def __init__(
        self,
        A: float = 1.0,           # Tank area (m^2)
        R: float = 10.0,          # Outlet resistance
        valve_flow: float = 0.1,  # Max valve flow (m^3/s)
        outlet_flow: float = 0.05,  # Base outlet flow (m^3/s)
        dt: float = 0.1,
        initial_level: float = 0.0,
    ):
        self.A = A
        self.R = R
        self.valve_flow = valve_flow
        self.outlet_flow = outlet_flow
        self.dt = dt

        # Internal state
        self._level = initial_level
        self._initial_level = initial_level

        # Disturbance
        self._outlet_disturbance = 0.0

    def reset(self):
        self._level = self._initial_level
        self._outlet_disturbance = 0.0

    def set_outlet_disturbance(self, disturbance: float):
        """Set outlet flow disturbance."""
        self._outlet_disturbance = disturbance

    def update(self, control_input: float) -> float:
        """Update liquid level with valve input.

        The model includes:
        1. Inlet flow from valve (proportional to control input)
        2. Outlet flow (depends on level and disturbance)
        3. Tank dynamics (mass balance)
        """
        # Inlet flow (valve characteristic: linear)
        # control_input is 0-100% valve opening
        valve_opening = np.clip(control_input, 0.0, 100.0) / 100.0
        Qin = self.valve_flow * valve_opening

        # Outlet flow (depends on level: sqrt relationship)
        # Qout = sqrt(h/R) + base_flow + disturbance
        if self._level > 0:
            Qout = np.sqrt(self._level / self.R) + self.outlet_flow + self._outlet_disturbance
        else:
            Qout = self.outlet_flow + self._outlet_disturbance

        # Mass balance: A * dh/dt = Qin - Qout
        dh_dt = (Qin - Qout) / self.A

        # Update level (Euler integration)
        self._level += dh_dt * self.dt

        # Level cannot be negative
        self._level = max(0.0, self._level)

        return self._level

    @property
    def output(self) -> float:
        return self._level


def run_level_control():
    """Run liquid level control simulation."""
    print("=" * 60)
    print("Liquid Level Control System - PID Controller")
    print("=" * 60)

    # Create tank plant
    # valve_flow=5.0: at 100% opening, Qin = 5.0 m³/s
    # outlet_flow=0.1: base outlet flow
    # At steady state with 100% valve: 5.0 = sqrt(h/10) + 0.1 => h ~ 240m
    # So 2.0m is easily achievable
    plant = TankPlant(
        A=1.0,              # Tank area
        R=10.0,             # Outlet resistance
        valve_flow=5.0,     # Max valve flow (m³/s)
        outlet_flow=0.1,    # Base outlet flow (m³/s)
        dt=0.1,
        initial_level=0.0,
    )

    # Target level: 2.0 meters
    setpoint = 2.0

    # Create PID controller with anti-windup
    # (important for valve saturation)
    controller = PIDController(
        Kp=50.0,
        Ki=2.0,
        Kd=10.0,
        output_min=0.0,      # Valve can only open
        output_max=100.0,    # Max valve opening
        integral_min=-50.0,  # Anti-windup limits
        integral_max=50.0,
        dt=0.1,
    )

    # Run simulation
    sim = Simulator(controller, plant, dt=0.1)
    result = sim.run(setpoint=setpoint, duration=100.0)

    # Print results
    print(f"\nSetpoint: {setpoint} meters")
    print(f"Initial level: 0.0 meters")
    print(f"\nPerformance Metrics:")
    print(f"  Overshoot: {result.overshoot:.1f}%")
    print(f"  Rise time: {result.rise_time:.1f}s")
    print(f"  Settling time (2%): {result.settling_time:.1f}s")
    print(f"  Settling time (5%): {result.settling_time_5pct:.1f}s")
    print(f"  Steady-state error: {result.steady_state_error:.3f} meters")

    # Show level at key times
    print(f"\nLevel Profile:")
    for t in [0, 5, 10, 20, 40, 60, 80, 100]:
        idx = min(int(t / 0.1), len(result.measurement) - 1)
        level = result.measurement[idx]
        print(f"  t={t:3d}s: {level:.2f} meters")

    return result


def run_disturbance_rejection():
    """Demonstrate disturbance rejection for outlet flow changes."""
    print("\n" + "=" * 60)
    print("Disturbance Rejection - Outlet Flow Change")
    print("=" * 60)

    # Create tank plant
    plant = TankPlant(
        A=1.0, R=10.0, valve_flow=5.0, outlet_flow=0.1,
        dt=0.1, initial_level=2.0,
    )

    # Controller
    controller = PIDController(
        Kp=50.0, Ki=2.0, Kd=10.0,
        output_min=0.0, output_max=100.0,
        integral_min=-50.0, integral_max=50.0,
        dt=0.1,
    )

    # Setpoint: constant at 2.0 meters
    setpoint = 2.0

    # Run simulation with manual loop to inject disturbance
    controller.reset()
    plant.reset()

    num_steps = int(200.0 / 0.1)
    levels = []
    times = []

    for step in range(num_steps):
        t = step * 0.1

        # Inject disturbance at t=50: outlet flow increases
        if t >= 50.0:
            plant.set_outlet_disturbance(0.02)  # 20% increase in outlet flow

        measurement = plant.output
        control = controller.update(setpoint, measurement, t)
        plant.update(control)

        levels.append(measurement)
        times.append(t)

    print(f"\nSetpoint: {setpoint} meters")
    print(f"Disturbance: outlet flow +20% at t=50s")

    # Show results
    print(f"\nLevel at key times:")
    for t in [0, 30, 49, 50, 60, 80, 100, 150, 200]:
        idx = min(int(t / 0.1), len(levels) - 1)
        print(f"  t={t:3d}s: {levels[idx]:.3f} meters")

    # Find minimum level after disturbance
    post_disturbance = levels[500:]  # After t=50s
    min_level = min(post_disturbance)
    print(f"\nMinimum level after disturbance: {min_level:.3f} meters")
    print(f"Maximum deviation from setpoint: {setpoint - min_level:.3f} meters")


def run_setpoint_tracking():
    """Demonstrate level tracking with varying setpoints."""
    print("\n" + "=" * 60)
    print("Level Tracking - Varying Setpoints")
    print("=" * 60)

    # Create tank plant
    plant = TankPlant(
        A=1.0, R=10.0, valve_flow=5.0, outlet_flow=0.1,
        dt=0.1, initial_level=0.0,
    )

    # Controller
    controller = PIDController(
        Kp=50.0, Ki=2.0, Kd=10.0,
        output_min=0.0, output_max=100.0,
        integral_min=-50.0, integral_max=50.0,
        dt=0.1,
    )

    # Setpoint function: step changes
    def setpoint_fn(t):
        if t < 30:
            return 2.0    # 2 meters
        elif t < 60:
            return 1.0    # 1 meter
        elif t < 90:
            return 3.0    # 3 meters
        else:
            return 2.0    # Back to 2 meters

    # Run simulation
    sim = Simulator(controller, plant, dt=0.1)
    result = sim.run(setpoint_fn=setpoint_fn, duration=120.0)

    print(f"\nSetpoint changes:")
    print(f"  t=0-30s: 2.0 meters")
    print(f"  t=30-60s: 1.0 meters")
    print(f"  t=60-90s: 3.0 meters")
    print(f"  t=90-120s: 2.0 meters")

    # Show level at key times
    print(f"\nLevel at key times:")
    for t in [0, 15, 30, 45, 60, 75, 90, 105, 120]:
        idx = min(int(t / 0.1), len(result.measurement) - 1)
        level = result.measurement[idx]
        sp = setpoint_fn(t)
        print(f"  t={t:3d}s: level={level:.2f}m, setpoint={sp:.1f}m")


if __name__ == "__main__":
    run_level_control()
    run_disturbance_rejection()
    run_setpoint_tracking()
