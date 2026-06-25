"""
PID Controller Visualization Example.

This example demonstrates how to visualize PID controller behavior:
1. Step response with PID components
2. Comparison of different tunings
3. Effect of disturbances
4. Tuning method results

Requires: matplotlib
    pip install matplotlib
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("matplotlib not installed. Install with: pip install matplotlib")
    print("Running in text-only mode.\n")

from src import PIDController, FirstOrderPlant, SecondOrderPlant, Simulator
from src.simulator import run_comparison


def plot_step_response():
    """Plot a complete step response with PID term decomposition."""
    if not HAS_MATPLOTLIB:
        return

    controller = PIDController(Kp=2.0, Ki=0.5, Kd=0.3, dt=0.01)
    plant = FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)
    sim = Simulator(controller, plant, dt=0.01)
    result = sim.run(setpoint=1.0, duration=15.0)

    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    # Plot 1: Setpoint vs Measurement
    axes[0].plot(result.time, result.setpoint, 'b--', label='Setpoint', linewidth=2)
    axes[0].plot(result.time, result.measurement, 'r-', label='Measurement', linewidth=1.5)
    axes[0].set_ylabel('Value')
    axes[0].set_title('PID Step Response (Kp=2.0, Ki=0.5, Kd=0.3)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Plot 2: Error
    axes[1].plot(result.time, result.error, 'g-', label='Error', linewidth=1.5)
    axes[1].axhline(y=0, color='k', linestyle='-', linewidth=0.5)
    axes[1].set_ylabel('Error')
    axes[1].set_title('Error Signal')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Plot 3: PID terms
    axes[2].plot(result.time, result.p_term, 'b-', label='P term', alpha=0.7)
    axes[2].plot(result.time, result.i_term, 'r-', label='I term', alpha=0.7)
    axes[2].plot(result.time, result.d_term, 'g-', label='D term', alpha=0.7)
    axes[2].plot(result.time, result.control, 'k-', label='Total output', linewidth=2)
    axes[2].set_xlabel('Time (s)')
    axes[2].set_ylabel('Control Signal')
    axes[2].set_title('PID Term Contributions')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/pid-controller/examples/step_response.png', dpi=150)
    print("  Saved: examples/step_response.png")


def plot_comparison():
    """Plot comparison of different PID tunings."""
    if not HAS_MATPLOTLIB:
        return

    configs = {
        "P only": {"Kp": 3.0, "Ki": 0.0, "Kd": 0.0},
        "PI": {"Kp": 2.0, "Ki": 0.5, "Kd": 0.0},
        "PID": {"Kp": 2.0, "Ki": 0.5, "Kd": 0.3},
        "Aggressive": {"Kp": 4.0, "Ki": 2.0, "Kd": 0.5},
    }

    def make_plant():
        return FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)

    results = run_comparison(
        configs, make_plant, setpoint=1.0, duration=15.0, dt=0.01
    )

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    # Plot responses
    for name, result in results.items():
        axes[0].plot(result.time, result.measurement, label=name, linewidth=1.5)

    axes[0].axhline(y=1.0, color='k', linestyle='--', label='Setpoint', alpha=0.5)
    axes[0].set_ylabel('Output')
    axes[0].set_title('Comparison of PID Tunings')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Plot control signals
    for name, result in results.items():
        axes[1].plot(result.time, result.control, label=name, linewidth=1.5)

    axes[1].set_xlabel('Time (s)')
    axes[1].set_ylabel('Control Output')
    axes[1].set_title('Control Signals')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/pid-controller/examples/comparison.png', dpi=150)
    print("  Saved: examples/comparison.png")


def plot_disturbance_rejection():
    """Show PID controller handling disturbances."""
    if not HAS_MATPLOTLIB:
        return

    controller = PIDController(Kp=2.0, Ki=0.5, Kd=0.3, dt=0.01)
    plant = FirstOrderPlant(K=1.0, tau=2.0, dt=0.01)
    sim = Simulator(controller, plant, dt=0.01)

    # Run with disturbance: constant setpoint but plant has a step disturbance
    controller.reset()
    plant.reset()

    num_steps = 2000
    time_arr = np.zeros(num_steps)
    setpoint_arr = np.ones(num_steps)
    measurement_arr = np.zeros(num_steps)
    output_arr = np.zeros(num_steps)

    for i in range(num_steps):
        t = i * 0.01
        time_arr[i] = t

        measurement = plant.output
        measurement_arr[i] = measurement

        control = controller.update(1.0, measurement, t)
        output_arr[i] = control

        # Add disturbance at t=10s (simulates a load change)
        disturbance = 0.5 if t >= 10.0 else 0.0
        plant.update(control + disturbance)

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    axes[0].plot(time_arr, setpoint_arr, 'b--', label='Setpoint', linewidth=2)
    axes[0].plot(time_arr, measurement_arr, 'r-', label='Measurement', linewidth=1.5)
    axes[0].axvline(x=10.0, color='gray', linestyle=':', label='Disturbance applied')
    axes[0].set_ylabel('Output')
    axes[0].set_title('Disturbance Rejection (disturbance at t=10s)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(time_arr, output_arr, 'g-', label='Control', linewidth=1.5)
    axes[1].axvline(x=10.0, color='gray', linestyle=':', label='Disturbance applied')
    axes[1].set_xlabel('Time (s)')
    axes[1].set_ylabel('Control Output')
    axes[1].set_title('Control Signal')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/pid-controller/examples/disturbance.png', dpi=150)
    print("  Saved: examples/disturbance.png")


def plot_second_order():
    """Show PID control of a second-order (oscillatory) system."""
    if not HAS_MATPLOTLIB:
        return

    configs = {
        "Underdamped (z=0.3)": {"Kp": 2.0, "Ki": 0.5, "Kd": 0.5},
        "Critical (z=1.0)": {"Kp": 2.0, "Ki": 0.5, "Kd": 0.3},
        "Overdamped (z=2.0)": {"Kp": 2.0, "Ki": 0.5, "Kd": 0.2},
    }

    plants = {
        "Underdamped (z=0.3)": lambda: SecondOrderPlant(K=1.0, omega_n=2.0, zeta=0.3, dt=0.01),
        "Critical (z=1.0)": lambda: SecondOrderPlant(K=1.0, omega_n=2.0, zeta=1.0, dt=0.01),
        "Overdamped (z=2.0)": lambda: SecondOrderPlant(K=1.0, omega_n=2.0, zeta=2.0, dt=0.01),
    }

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    for name in configs:
        controller = PIDController(dt=0.01, **configs[name])
        plant = plants[name]()
        sim = Simulator(controller, plant, dt=0.01)
        result = sim.run(setpoint=1.0, duration=15.0)

        axes[0].plot(result.time, result.measurement, label=name, linewidth=1.5)

    axes[0].axhline(y=1.0, color='k', linestyle='--', label='Setpoint', alpha=0.5)
    axes[0].set_ylabel('Output')
    axes[0].set_title('PID Control of Second-Order Systems')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    for name in configs:
        controller = PIDController(dt=0.01, **configs[name])
        plant = plants[name]()
        sim = Simulator(controller, plant, dt=0.01)
        result = sim.run(setpoint=1.0, duration=15.0)

        axes[1].plot(result.time, result.control, label=name, linewidth=1.5)

    axes[1].set_xlabel('Time (s)')
    axes[1].set_ylabel('Control Output')
    axes[1].set_title('Control Signals')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/home/siok/project_copyninja/projects/pid-controller/examples/second_order.png', dpi=150)
    print("  Saved: examples/second_order.png")


if __name__ == "__main__":
    print("\nPID Controller - Visualization Examples\n")
    plot_step_response()
    plot_comparison()
    plot_disturbance_rejection()
    plot_second_order()

    if HAS_MATPLOTLIB:
        print("\nAll plots saved to examples/ directory.")
        print("Open them with any image viewer.")
    else:
        print("\nmatplotlib not available. Install with: pip install matplotlib")
