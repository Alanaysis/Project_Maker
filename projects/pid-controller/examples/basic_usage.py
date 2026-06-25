"""
Basic PID Controller Usage Example.

This example demonstrates:
1. Creating a PID controller with specific gains
2. Simulating a first-order system
3. Analyzing the step response
4. Comparing P, PI, and PID controllers
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src import PIDController, FirstOrderPlant, Simulator
from src.simulator import run_comparison


def example_single_pid():
    """Run a single PID controller simulation."""
    print("=" * 60)
    print("Example 1: Single PID Controller")
    print("=" * 60)

    # Create PID controller with moderate tuning
    controller = PIDController(
        Kp=2.0,       # Proportional gain
        Ki=0.5,       # Integral gain
        Kd=0.3,       # Derivative gain
        output_min=-10,  # Minimum control output
        output_max=10,   # Maximum control output
        dt=0.01,         # Time step
    )

    # Create a first-order plant (like a room heater)
    # K=1.0 means steady-state output equals input
    # tau=2.0 means 2-second time constant
    plant = FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)

    # Create simulator and run
    sim = Simulator(controller, plant, dt=0.01)
    result = sim.run(setpoint=1.0, duration=15.0)

    # Print results
    print(f"  Controller: {controller}")
    print(f"  Plant: {plant}")
    print(f"  Results:")
    for key, value in result.summary().items():
        print(f"    {key}: {value:.4f}")
    print()


def example_p_pi_pid_comparison():
    """Compare P, PI, and PID controllers on the same plant."""
    print("=" * 60)
    print("Example 2: P vs PI vs PID Comparison")
    print("=" * 60)

    # Define different controller configurations
    configs = {
        "P only": {"Kp": 3.0, "Ki": 0.0, "Kd": 0.0},
        "PI": {"Kp": 2.0, "Ki": 0.5, "Kd": 0.0},
        "PID": {"Kp": 2.0, "Ki": 0.5, "Kd": 0.3},
    }

    # All use the same plant
    def make_plant():
        return FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)

    # Run comparison
    results = run_comparison(
        configs, make_plant, setpoint=1.0, duration=15.0, dt=0.01
    )

    # Print comparison table
    print(f"  {'Controller':<12} {'Overshoot%':<12} {'Settle(s)':<12} "
          f"{'Rise(s)':<12} {'SS Error':<12}")
    print(f"  {'-'*12} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")

    for name, result in results.items():
        m = result.summary()
        print(f"  {name:<12} {m['overshoot_pct']:<12.2f} "
              f"{m['settling_time_s']:<12.2f} {m['rise_time_s']:<12.2f} "
              f"{m['steady_state_error']:<12.4f}")
    print()

    # Key observations
    print("  Key observations:")
    print("  - P only: Has steady-state error (cannot reach setpoint exactly)")
    print("  - PI: Eliminates steady-state error, may have some overshoot")
    print("  - PID: Best balance of speed, overshoot, and zero steady-state error")
    print()


def example_different_gains():
    """Show effect of different PID gains."""
    print("=" * 60)
    print("Example 3: Effect of Different Gains")
    print("=" * 60)

    configs = {
        "Low Kp": {"Kp": 1.0, "Ki": 0.5, "Kd": 0.1},
        "High Kp": {"Kp": 5.0, "Ki": 0.5, "Kd": 0.1},
        "Low Ki": {"Kp": 2.0, "Ki": 0.1, "Kd": 0.1},
        "High Ki": {"Kp": 2.0, "Ki": 2.0, "Kd": 0.1},
        "Low Kd": {"Kp": 2.0, "Ki": 0.5, "Kd": 0.05},
        "High Kd": {"Kp": 2.0, "Ki": 0.5, "Kd": 1.0},
    }

    def make_plant():
        return FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)

    results = run_comparison(
        configs, make_plant, setpoint=1.0, duration=15.0, dt=0.01
    )

    print(f"  {'Config':<12} {'Overshoot%':<12} {'Settle(s)':<12} "
          f"{'Rise(s)':<12} {'SS Error':<12}")
    print(f"  {'-'*12} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")

    for name, result in results.items():
        m = result.summary()
        print(f"  {name:<12} {m['overshoot_pct']:<12.2f} "
              f"{m['settling_time_s']:<12.2f} {m['rise_time_s']:<12.2f} "
              f"{m['steady_state_error']:<12.4f}")
    print()


def example_setpoint_tracking():
    """Demonstrate tracking a time-varying setpoint."""
    print("=" * 60)
    print("Example 4: Time-Varying Setpoint Tracking")
    print("=" * 60)

    controller = PIDController(Kp=2.0, Ki=0.5, Kd=0.3, dt=0.01)
    plant = FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)
    sim = Simulator(controller, plant, dt=0.01)

    # Square wave setpoint: alternates between 1.0 and 0.0
    def square_wave(t):
        return 1.0 if (t % 4.0) < 2.0 else 0.0

    result = sim.run(setpoint_fn=square_wave, duration=20.0)

    # Track final values at different time points
    print("  Setpoint: Square wave (1.0 for 2s, 0.0 for 2s)")
    print(f"  Final measurement at t=20s: {result.measurement[-1]:.4f}")
    print(f"  Final error: {result.error[-1]:.4f}")
    print()


if __name__ == "__main__":
    print("\nPID Controller - Basic Usage Examples\n")
    example_single_pid()
    example_p_pi_pid_comparison()
    example_different_gains()
    example_setpoint_tracking()
    print("All examples completed successfully!")
