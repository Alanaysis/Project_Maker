"""
Plant Models - Simulate physical systems for PID controller testing.

A "plant" is the system being controlled. This module provides three common
plant models used in control systems:

1. First-order plant: G(s) = K / (τs + 1)
   - K: static gain (steady-state output per unit input)
   - τ: time constant (how fast the system responds)
   - Examples: heating a room, filling a tank

2. Second-order plant: G(s) = K / (s² + 2ζωn*s + ωn²)
   - K: static gain
   - ζ (zeta): damping ratio (0=undamped, 1=critically damped, >1=overdamped)
   - ωn: natural frequency
   - Examples: spring-mass-damper, RLC circuit, robot arm

3. Delay system: G(s) = K * e^(-Ls) / (τs + 1)
   - First-order system with transport delay
   - L: dead time (delay before response begins)
   - Examples: pipeline flow, chemical process, network control
"""

import numpy as np
from typing import Optional


class FirstOrderPlant:
    """A first-order linear time-invariant (LTI) system.

    Transfer function: G(s) = K / (τs + 1)

    In the time domain: τ * dy/dt + y = K * u

    This is the simplest dynamic system. It has:
    - No overshoot (for step input)
    - Exponential approach to steady state
    - Time constant τ determines speed of response

    The discrete-time update (using Euler method):
        y(t+dt) = y(t) + (dt/τ) * (K*u(t) - y(t))

    Parameters:
        K: Static gain. Output at steady state per unit input. Default: 1.0
        tau: Time constant (seconds). Larger = slower response. Default: 1.0
        dt: Time step for simulation. Default: 0.01
        initial_output: Starting output value. Default: 0.0
    """

    def __init__(
        self,
        K: float = 1.0,
        tau: float = 1.0,
        dt: float = 0.01,
        initial_output: float = 0.0,
    ):
        if tau <= 0:
            raise ValueError("tau must be positive")
        if dt <= 0:
            raise ValueError("dt must be positive")

        self.K = K
        self.tau = tau
        self.dt = dt

        # Internal state
        self._output = initial_output
        self._initial_output = initial_output

    def reset(self) -> None:
        """Reset plant to initial state."""
        self._output = self._initial_output

    def update(self, control_input: float) -> float:
        """Advance the plant by one time step.

        Uses forward Euler discretization:
            y(t+dt) = y(t) + (dt/τ) * (K*u(t) - y(t))

        Args:
            control_input: The control signal applied to the plant.

        Returns:
            The new output value after one time step.
        """
        # Euler method: dy/dt = (K*u - y) / τ
        dy_dt = (self.K * control_input - self._output) / self.tau
        self._output += dy_dt * self.dt

        return self._output

    @property
    def output(self) -> float:
        """Current output value."""
        return self._output

    def __repr__(self) -> str:
        return f"FirstOrderPlant(K={self.K}, tau={self.tau})"


class SecondOrderPlant:
    """A second-order linear time-invariant system.

    Transfer function: G(s) = K*ωn² / (s² + 2ζωn*s + ωn²)

    In the time domain: d²y/dt² + 2ζωn*dy/dt + ωn²*y = K*ωn²*u

    This system can exhibit:
    - Overshoot (when ζ < 1, underdamped)
    - Oscillation (when ζ < 1)
    - No overshoot (when ζ >= 1, critically damped or overdamped)

    State-space representation (used for simulation):
        x1 = y (position)
        x2 = dy/dt (velocity)
        dx1/dt = x2
        dx2/dt = -ωn²*x1 - 2ζωn*x2 + K*ωn²*u

    Parameters:
        K: Static gain. Default: 1.0
        omega_n: Natural frequency (rad/s). Default: 1.0
        zeta: Damping ratio. Default: 0.7
            - 0: undamped (perpetual oscillation)
            - 0 < ζ < 1: underdamped (oscillation with decay)
            - 1: critically damped (fastest without overshoot)
            - > 1: overdamped (slow, no overshoot)
        dt: Time step for simulation. Default: 0.01
        initial_position: Starting position. Default: 0.0
        initial_velocity: Starting velocity. Default: 0.0
    """

    def __init__(
        self,
        K: float = 1.0,
        omega_n: float = 1.0,
        zeta: float = 0.7,
        dt: float = 0.01,
        initial_position: float = 0.0,
        initial_velocity: float = 0.0,
    ):
        if omega_n <= 0:
            raise ValueError("omega_n must be positive")
        if zeta < 0:
            raise ValueError("zeta must be non-negative")
        if dt <= 0:
            raise ValueError("dt must be positive")

        self.K = K
        self.omega_n = omega_n
        self.zeta = zeta
        self.dt = dt

        # Internal state (position and velocity)
        self._x1 = initial_position  # position (output)
        self._x2 = initial_velocity  # velocity
        self._initial_position = initial_position
        self._initial_velocity = initial_velocity

    def reset(self) -> None:
        """Reset plant to initial state."""
        self._x1 = self._initial_position
        self._x2 = self._initial_velocity

    def update(self, control_input: float) -> float:
        """Advance the plant by one time step.

        Uses 4th-order Runge-Kutta for better accuracy than Euler.

        State equations:
            dx1/dt = x2
            dx2/dt = -ωn²*x1 - 2ζωn*x2 + K*ωn²*u

        Args:
            control_input: The control signal applied to the plant.

        Returns:
            The new output (position) value after one time step.
        """
        wn2 = self.omega_n ** 2
        two_zeta_wn = 2.0 * self.zeta * self.omega_n

        def derivatives(x1, x2, u):
            dx1 = x2
            dx2 = -wn2 * x1 - two_zeta_wn * x2 + self.K * wn2 * u
            return dx1, dx2

        # Runge-Kutta 4th order
        dt = self.dt
        u = control_input

        k1_x1, k1_x2 = derivatives(self._x1, self._x2, u)
        k2_x1, k2_x2 = derivatives(
            self._x1 + 0.5 * dt * k1_x1,
            self._x2 + 0.5 * dt * k1_x2,
            u,
        )
        k3_x1, k3_x2 = derivatives(
            self._x1 + 0.5 * dt * k2_x1,
            self._x2 + 0.5 * dt * k2_x2,
            u,
        )
        k4_x1, k4_x2 = derivatives(
            self._x1 + dt * k3_x1,
            self._x2 + dt * k3_x2,
            u,
        )

        self._x1 += (dt / 6.0) * (k1_x1 + 2 * k2_x1 + 2 * k3_x1 + k4_x1)
        self._x2 += (dt / 6.0) * (k1_x2 + 2 * k2_x2 + 2 * k3_x2 + k4_x2)

        return self._x1

    @property
    def output(self) -> float:
        """Current output (position) value."""
        return self._x1

    @property
    def velocity(self) -> float:
        """Current velocity value."""
        return self._x2

    def __repr__(self) -> str:
        return (
            f"SecondOrderPlant(K={self.K}, omega_n={self.omega_n}, "
            f"zeta={self.zeta})"
        )


class DelaySystem:
    """A first-order system with transport delay (dead time).

    Transfer function: G(s) = K * e^(-Ls) / (τs + 1)

    This models systems where there is a time delay between applying
    the control input and observing the effect. Common in:
    - Pipeline flow control (fluid takes time to travel)
    - Chemical processes (reaction delay)
    - Network control systems (communication delay)
    - Temperature control with long sensor placement

    The delay is implemented using a circular buffer that stores
    past control inputs. The plant responds to the input that was
    applied L seconds ago.

    Parameters:
        K: Static gain. Default: 1.0
        tau: Time constant (seconds). Default: 1.0
        delay: Dead time (seconds). Default: 1.0
        dt: Time step for simulation. Default: 0.01
        initial_output: Starting output value. Default: 0.0
    """

    def __init__(
        self,
        K: float = 1.0,
        tau: float = 1.0,
        delay: float = 1.0,
        dt: float = 0.01,
        initial_output: float = 0.0,
    ):
        if tau <= 0:
            raise ValueError("tau must be positive")
        if delay < 0:
            raise ValueError("delay must be non-negative")
        if dt <= 0:
            raise ValueError("dt must be positive")

        self.K = K
        self.tau = tau
        self.delay = delay
        self.dt = dt

        # Internal state
        self._output = initial_output
        self._initial_output = initial_output

        # Delay buffer: stores past control inputs
        # Number of delay steps
        self._delay_steps = max(1, int(round(delay / dt)))
        self._buffer = [0.0] * self._delay_steps
        self._buffer_idx = 0

    def reset(self) -> None:
        """Reset plant to initial state."""
        self._output = self._initial_output
        self._buffer = [0.0] * self._delay_steps
        self._buffer_idx = 0

    def update(self, control_input: float) -> float:
        """Advance the plant by one time step.

        The control input is first stored in a delay buffer. The plant
        responds to the input that was applied `delay` seconds ago.

        Discrete-time update:
            1. Store current input in buffer
            2. Retrieve delayed input from buffer
            3. Apply first-order dynamics: y(t+dt) = y(t) + (dt/tau) * (K*u_delayed - y)

        Args:
            control_input: The control signal applied to the plant.

        Returns:
            The new output value after one time step.
        """
        # Store current input in delay buffer
        self._buffer[self._buffer_idx] = control_input

        # Get delayed input (the input from delay_steps ago)
        delayed_idx = (self._buffer_idx + 1) % self._delay_steps
        delayed_input = self._buffer[delayed_idx]

        # Advance buffer index
        self._buffer_idx = delayed_idx

        # First-order dynamics with delayed input
        dy_dt = (self.K * delayed_input - self._output) / self.tau
        self._output += dy_dt * self.dt

        return self._output

    @property
    def output(self) -> float:
        """Current output value."""
        return self._output

    def __repr__(self) -> str:
        return (
            f"DelaySystem(K={self.K}, tau={self.tau}, delay={self.delay})"
        )
