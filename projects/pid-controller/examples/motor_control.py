"""
Motor Control Example - PID controller for DC motor speed control.

This example simulates a DC motor speed control system, such as:
- Conveyor belt speed control
- Fan speed regulation
- Robot wheel speed control

The system model:
- Second-order (motor + load inertia)
- Setpoint: target RPM
- Disturbance: load torque changes
- Actuator: motor voltage

Key concepts demonstrated:
- Second-order system control
- Dead zone for motor friction
- Derivative filtering for noise rejection
- Speed tracking with varying setpoints
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src import PIDController, SecondOrderPlant, Simulator


class DCMotorPlant:
    """Simulate a DC motor speed control system.

    Model: second-order system with friction
    - J: motor + load inertia (kg*m^2)
    - b: viscous friction coefficient
    - Kt: motor torque constant
    - Ke: back-EMF constant
    - R: motor resistance

    Transfer function: G(s) = Kt / (J*s + b + Kt*Ke/R)
    """

    def __init__(
        self,
        J: float = 0.01,      # Inertia
        b: float = 0.1,       # Viscous friction
        Kt: float = 1.0,      # Torque constant
        Ke: float = 0.01,     # Back-EMF constant
        R: float = 1.0,       # Resistance
        dt: float = 0.001,
        friction_deadzone: float = 0.5,  # Coulomb friction threshold
    ):
        self.J = J
        self.b = b
        self.Kt = Kt
        self.Ke = Ke
        self.R = R
        self.dt = dt
        self.friction_deadzone = friction_deadzone

        # Internal state
        self._speed = 0.0      # Motor speed (rad/s)
        self._position = 0.0   # Motor position (rad)

    def reset(self):
        self._speed = 0.0
        self._position = 0.0

    def update(self, control_input: float) -> float:
        """Update motor speed with voltage input.

        The model includes:
        1. Electromagnetic torque from voltage
        2. Back-EMF opposing motion
        3. Viscous friction
        4. Coulomb friction (dead zone)
        """
        # Electromagnetic torque
        torque_em = self.Kt * control_input / self.R

        # Back-EMF torque (opposing motion)
        torque_bemf = self.Kt * self.Ke * self._speed / self.R

        # Viscous friction
        torque_viscous = self.b * self._speed

        # Coulomb friction (dead zone)
        if abs(self._speed) < 0.01:
            # Static friction
            if abs(torque_em - torque_bemf) < self.friction_deadzone:
                torque_friction = torque_em - torque_bemf
            else:
                torque_friction = self.friction_deadzone * np.sign(torque_em - torque_bemf)
        else:
            # Dynamic friction
            torque_friction = self.friction_deadzone * np.sign(self._speed)

        # Net torque
        torque_net = torque_em - torque_bemf - torque_viscous - torque_friction

        # Acceleration
        acceleration = torque_net / self.J

        # Update speed (Euler integration)
        self._speed += acceleration * self.dt

        # Update position
        self._position += self._speed * self.dt

        return self._speed

    @property
    def output(self) -> float:
        return self._speed

    @property
    def position(self) -> float:
        return self._position


def run_speed_control():
    """Run motor speed control simulation."""
    print("=" * 60)
    print("DC Motor Speed Control - PID Controller")
    print("=" * 60)

    # Create motor plant
    plant = DCMotorPlant(
        J=0.01,          # Inertia
        b=0.1,           # Viscous friction
        Kt=1.0,          # Torque constant
        Ke=0.01,         # Back-EMF constant
        R=1.0,           # Resistance
        dt=0.001,
        friction_deadzone=0.5,
    )

    # Target speed: 100 rad/s
    setpoint = 100.0

    # Create PID controller with dead zone
    # (helps with friction - don't try to correct small errors)
    controller = PIDController(
        Kp=0.5,
        Ki=2.0,
        Kd=0.01,
        output_min=-24.0,    # Motor voltage limits
        output_max=24.0,
        dead_zone=0.5,       # Ignore small speed errors
        derivative_filter_coeff=0.2,  # Filter noise
        dt=0.001,
    )

    # Run simulation
    sim = Simulator(controller, plant, dt=0.001)
    result = sim.run(setpoint=setpoint, duration=2.0)

    # Print results
    print(f"\nSetpoint: {setpoint} rad/s")
    print(f"\nPerformance Metrics:")
    print(f"  Overshoot: {result.overshoot:.1f}%")
    print(f"  Rise time: {result.rise_time:.3f}s")
    print(f"  Settling time (2%): {result.settling_time:.3f}s")
    print(f"  Steady-state error: {result.steady_state_error:.2f} rad/s")

    # Show speed at key times
    print(f"\nSpeed Profile:")
    for t in [0, 0.1, 0.3, 0.5, 1.0, 1.5, 2.0]:
        idx = min(int(t / 0.001), len(result.measurement) - 1)
        speed = result.measurement[idx]
        print(f"  t={t:.1f}s: {speed:.1f} rad/s")

    return result


def run_speed_tracking():
    """Demonstrate speed tracking with varying setpoints."""
    print("\n" + "=" * 60)
    print("Speed Tracking - Varying Setpoints")
    print("=" * 60)

    # Create motor plant
    plant = DCMotorPlant(
        J=0.01, b=0.1, Kt=1.0, Ke=0.01, R=1.0,
        dt=0.001, friction_deadzone=0.5,
    )

    # Controller (without dead zone for tracking)
    controller = PIDController(
        Kp=0.5, Ki=2.0, Kd=0.01,
        output_min=-24.0, output_max=24.0,
        derivative_filter_coeff=0.2,
        dt=0.001,
    )

    # Setpoint function: step changes
    def setpoint_fn(t):
        if t < 0.5:
            return 100.0    # 100 rad/s
        elif t < 1.0:
            return 50.0     # 50 rad/s
        elif t < 1.5:
            return 150.0    # 150 rad/s
        else:
            return 100.0    # Back to 100 rad/s

    # Run simulation
    sim = Simulator(controller, plant, dt=0.001)
    result = sim.run(setpoint_fn=setpoint_fn, duration=2.0)

    print(f"\nSetpoint changes:")
    print(f"  t=0.0-0.5s: 100 rad/s")
    print(f"  t=0.5-1.0s: 50 rad/s")
    print(f"  t=1.0-1.5s: 150 rad/s")
    print(f"  t=1.5-2.0s: 100 rad/s")

    # Show speed at key times
    print(f"\nSpeed at key times:")
    for t in [0, 0.3, 0.5, 0.8, 1.0, 1.3, 1.5, 1.8, 2.0]:
        idx = min(int(t / 0.001), len(result.measurement) - 1)
        speed = result.measurement[idx]
        sp = setpoint_fn(t)
        print(f"  t={t:.1f}s: speed={speed:.1f} rad/s, setpoint={sp:.1f} rad/s")


def run_friction_comparison():
    """Compare control with and without dead zone."""
    print("\n" + "=" * 60)
    print("Friction Compensation Comparison")
    print("=" * 60)

    setpoint = 100.0

    # Without dead zone
    plant1 = DCMotorPlant(dt=0.001, friction_deadzone=0.5)
    controller1 = PIDController(
        Kp=0.5, Ki=2.0, Kd=0.01,
        output_min=-24.0, output_max=24.0,
        dt=0.001,
    )
    sim1 = Simulator(controller1, plant1, dt=0.001)
    result1 = sim1.run(setpoint=setpoint, duration=2.0)

    # With dead zone
    plant2 = DCMotorPlant(dt=0.001, friction_deadzone=0.5)
    controller2 = PIDController(
        Kp=0.5, Ki=2.0, Kd=0.01,
        output_min=-24.0, output_max=24.0,
        dead_zone=0.5,
        dt=0.001,
    )
    sim2 = Simulator(controller2, plant2, dt=0.001)
    result2 = sim2.run(setpoint=setpoint, duration=2.0)

    print(f"\nWithout dead zone:")
    print(f"  Overshoot: {result1.overshoot:.1f}%")
    print(f"  Settling time: {result1.settling_time:.3f}s")
    print(f"  Steady-state error: {result1.steady_state_error:.2f} rad/s")

    print(f"\nWith dead zone (0.5):")
    print(f"  Overshoot: {result2.overshoot:.1f}%")
    print(f"  Settling time: {result2.settling_time:.3f}s")
    print(f"  Steady-state error: {result2.steady_state_error:.2f} rad/s")


if __name__ == "__main__":
    run_speed_control()
    run_speed_tracking()
    run_friction_comparison()
