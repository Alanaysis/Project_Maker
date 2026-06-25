"""
Temperature Control Example - PID controller for a heating system.

This example simulates a temperature control system, such as:
- Oven temperature control
- Room thermostat
- Chemical reactor temperature

The system model:
- First-order with delay (heating element has thermal inertia)
- Setpoint: target temperature
- Disturbance: ambient temperature changes
- Actuator: heater power (0-100%)

Key concepts demonstrated:
- PID tuning for temperature control
- Dealing with transport delay
- Disturbance rejection
- Integral separation for large setpoint changes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src import PIDController, DelaySystem, Simulator


def run_temperature_control():
    """Run temperature control simulation."""
    print("=" * 60)
    print("Temperature Control System - PID Controller")
    print("=" * 60)

    # Create temperature plant using DelaySystem
    # G(s) = K * e^(-Ls) / (tau*s + 1)
    # K=1.0, tau=10s, delay=2s
    # At steady state with unit input: output = K = 1.0
    plant = DelaySystem(
        K=1.0,           # Steady-state gain
        tau=10.0,        # Thermal time constant
        delay=2.0,       # Transport delay
        dt=0.1,
        initial_output=0.0,
    )

    # Target temperature: normalized to 1.0
    setpoint = 1.0

    # Create PID controller with integral separation
    # Conservative tuning for delay system
    controller = PIDController(
        Kp=1.5,
        Ki=0.1,
        Kd=3.0,
        output_min=0.0,      # Heater can only add heat
        output_max=5.0,      # Max heater power
        integral_separation=True,
        integral_separation_threshold=0.5,  # Disable integral when error > 0.5
        dt=0.1,
    )

    # Run simulation
    sim = Simulator(controller, plant, dt=0.1)
    result = sim.run(setpoint=setpoint, duration=100.0)

    # Print results
    print(f"\nSetpoint: {setpoint}")
    print(f"Initial temperature: 0.0")
    print(f"\nPerformance Metrics:")
    print(f"  Overshoot: {result.overshoot:.1f}%")
    print(f"  Rise time: {result.rise_time:.1f}s")
    print(f"  Settling time (2%): {result.settling_time:.1f}s")
    print(f"  Settling time (5%): {result.settling_time_5pct:.1f}s")
    print(f"  Steady-state error: {result.steady_state_error:.4f}")

    # Show temperature at key times
    print(f"\nTemperature Profile:")
    for t in [0, 5, 10, 20, 30, 50, 70, 100]:
        idx = min(int(t / 0.1), len(result.measurement) - 1)
        temp = result.measurement[idx]
        print(f"  t={t:3d}s: {temp:.3f}")

    return result


def run_disturbance_rejection():
    """Demonstrate disturbance rejection in temperature control."""
    print("\n" + "=" * 60)
    print("Disturbance Rejection - Ambient Temperature Change")
    print("=" * 60)

    # Create plant
    plant = DelaySystem(
        K=1.0, tau=10.0, delay=2.0, dt=0.1, initial_output=0.0
    )

    # Controller
    controller = PIDController(
        Kp=1.5, Ki=0.1, Kd=3.0,
        output_min=0.0, output_max=5.0,
        integral_separation=True,
        integral_separation_threshold=0.5,
        dt=0.1,
    )

    # Setpoint: constant at 1.0
    setpoint = 1.0

    # Run simulation with manual loop to inject disturbance
    controller.reset()
    plant.reset()

    num_steps = int(100.0 / 0.1)
    temps = []
    times = []

    for step in range(num_steps):
        t = step * 0.1

        measurement = plant.output

        # Inject disturbance at t=50: add 0.2 to output (simulating ambient change)
        if t >= 50.0:
            control = controller.update(setpoint, measurement + 0.2, t)
        else:
            control = controller.update(setpoint, measurement, t)

        plant.update(control)
        temps.append(measurement)
        times.append(t)

    print(f"\nSetpoint: {setpoint}")
    print(f"Disturbance: +0.2 added to measurement at t=50s")

    # Show results
    print(f"\nTemperature at key times:")
    for t in [0, 20, 49, 50, 60, 80, 100]:
        idx = min(int(t / 0.1), len(temps) - 1)
        print(f"  t={t:3d}s: {temps[idx]:.3f}")

    # Find minimum temperature after disturbance
    post_disturbance = temps[500:]  # After t=50s
    if post_disturbance:
        min_temp = min(post_disturbance)
        print(f"\nMinimum temperature after disturbance: {min_temp:.3f}")
        print(f"Maximum deviation from setpoint: {setpoint - min_temp:.3f}")


if __name__ == "__main__":
    run_temperature_control()
    run_disturbance_rejection()
