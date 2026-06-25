"""
PID Controller - Core implementation of the PID control algorithm.

The PID controller computes a control output based on three terms:
- Proportional (P): Reacts to current error
- Integral (I): Eliminates steady-state error by accumulating past errors
- Derivative (D): Predicts future error by looking at rate of change

Control output: u(t) = Kp*e(t) + Ki*∫e(t)dt + Kd*de(t)/dt

Key features:
- Anti-windup: Prevents integral term from growing unbounded
- Output clamping: Limits control output to valid range
- Derivative filtering: Low-pass filter on derivative to reduce noise
- Bumpless transfer: Smooth transition when switching modes
- Integral separation: Disable integral when error is large
- Dead zone: Ignore small errors within a threshold
- Incomplete derivative: Additional first-order filtering on derivative
"""

import numpy as np
from typing import Optional, Dict, List, Tuple


class PIDController:
    """A PID (Proportional-Integral-Derivative) controller.

    This implements the discrete-time PID algorithm with several practical
    enhancements used in real control systems:

    1. **Proportional term**: Output proportional to current error
       - Larger Kp -> faster response, but more overshoot
       - Cannot eliminate steady-state error alone

    2. **Integral term**: Output proportional to accumulated error
       - Eliminates steady-state error
       - Can cause overshoot and oscillation
       - Anti-windup prevents excessive accumulation

    3. **Derivative term**: Output proportional to rate of error change
       - Provides damping, reduces overshoot
       - Sensitive to noise (filtered with low-pass filter)
       - Only acts on process variable changes (not setpoint changes)

    Improved variants:
    - **Integral separation**: Disables integral accumulation when error is
      large (|error| > separation_threshold). Prevents integral windup during
      large transients while still eliminating steady-state error near setpoint.
    - **Derivative on measurement**: Derivative acts on measurement changes
      rather than error changes, avoiding "derivative kick" on setpoint changes.
    - **Incomplete derivative**: Adds an additional first-order low-pass filter
      to the derivative term, further reducing high-frequency noise sensitivity.
    - **Dead zone**: When |error| < dead_zone, the controller output is zero.
      Useful for systems with friction or backlash where small corrections
      are ineffective.

    Parameters:
        Kp: Proportional gain. Default: 1.0
        Ki: Integral gain. Default: 0.0
        Kd: Derivative gain. Default: 0.0
        output_min: Minimum output value. Default: -inf
        output_max: Maximum output value. Default: +inf
        integral_min: Minimum integral accumulator (anti-windup). Default: -inf
        integral_max: Maximum integral accumulator (anti-windup). Default: +inf
        derivative_filter_coeff: Low-pass filter coefficient for derivative (0-1).
            Lower values = more filtering. Default: 0.1
        dt: Time step for discrete integration. Default: 0.01
        integral_separation: If True, enable integral separation. Default: False
        integral_separation_threshold: Error threshold for integral separation.
            When |error| > threshold, integral accumulation is paused. Default: 1.0
        incomplete_derivative: If True, enable incomplete derivative (additional
            first-order filter on derivative term). Default: False
        incomplete_derivative_coeff: Filter coefficient for incomplete derivative
            (0-1). Lower = more filtering. Default: 0.5
        dead_zone: Dead zone width. When |error| < dead_zone, output is 0.
            Default: 0.0 (disabled)
    """

    def __init__(
        self,
        Kp: float = 1.0,
        Ki: float = 0.0,
        Kd: float = 0.0,
        output_min: float = -float("inf"),
        output_max: float = float("inf"),
        integral_min: float = -float("inf"),
        integral_max: float = float("inf"),
        derivative_filter_coeff: float = 0.1,
        dt: float = 0.01,
        integral_separation: bool = False,
        integral_separation_threshold: float = 1.0,
        incomplete_derivative: bool = False,
        incomplete_derivative_coeff: float = 0.5,
        dead_zone: float = 0.0,
    ):
        if dt <= 0:
            raise ValueError("dt must be positive")
        if not 0 < derivative_filter_coeff <= 1:
            raise ValueError("derivative_filter_coeff must be in (0, 1]")
        if integral_separation_threshold < 0:
            raise ValueError("integral_separation_threshold must be non-negative")
        if not 0 < incomplete_derivative_coeff <= 1:
            raise ValueError("incomplete_derivative_coeff must be in (0, 1]")
        if dead_zone < 0:
            raise ValueError("dead_zone must be non-negative")

        # Controller gains
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd

        # Output limits
        self.output_min = output_min
        self.output_max = output_max

        # Anti-windup limits for integral accumulator
        self.integral_min = integral_min
        self.integral_max = integral_max

        # Derivative low-pass filter coefficient
        self.derivative_filter_coeff = derivative_filter_coeff

        # Time step
        self.dt = dt

        # Improved variant parameters
        self.integral_separation = integral_separation
        self.integral_separation_threshold = integral_separation_threshold
        self.incomplete_derivative = incomplete_derivative
        self.incomplete_derivative_coeff = incomplete_derivative_coeff
        self.dead_zone = dead_zone

        # Internal state
        self._integral: float = 0.0
        self._prev_error: float = 0.0
        self._prev_derivative: float = 0.0
        self._prev_measurement: float = 0.0
        self._prev_incomplete_d: float = 0.0
        self._first_update: bool = True

        # History for analysis
        self._history: Dict[str, List[float]] = {
            "time": [],
            "setpoint": [],
            "measurement": [],
            "error": [],
            "p_term": [],
            "i_term": [],
            "d_term": [],
            "output": [],
        }

    def reset(self) -> None:
        """Reset controller state.

        Clears all internal state (integral accumulator, previous errors,
        derivative filter state) and history. Use this when starting a
        new simulation or when the controller needs to be re-initialized.
        """
        self._integral = 0.0
        self._prev_error = 0.0
        self._prev_derivative = 0.0
        self._prev_measurement = 0.0
        self._prev_incomplete_d = 0.0
        self._first_update = True

        for key in self._history:
            self._history[key] = []

    def update(self, setpoint: float, measurement: float, t: float = 0.0) -> float:
        """Compute one step of PID control.

        This is the core algorithm. Given the desired value (setpoint) and
        the current measured value (measurement), compute the control output.

        The algorithm:
            1. Calculate error: e = setpoint - measurement
            2. Dead zone check: if |e| < dead_zone, output = 0
            3. P term: Kp * e
            4. I term: Ki * ∫e dt (with integral separation and anti-windup)
            5. D term: Kd * de/dt (with low-pass filtering, on measurement only,
               optional incomplete derivative)
            6. Sum all terms and clamp to output limits

        Args:
            setpoint: The desired value.
            measurement: The current measured value.
            t: Current time (for history tracking). Default: 0.0

        Returns:
            Control output value, clamped to [output_min, output_max].
        """
        # Calculate error
        error = setpoint - measurement

        # --- Dead zone ---
        if self.dead_zone > 0 and abs(error) < self.dead_zone:
            # Inside dead zone: no control action
            self._history["time"].append(t)
            self._history["setpoint"].append(setpoint)
            self._history["measurement"].append(measurement)
            self._history["error"].append(error)
            self._history["p_term"].append(0.0)
            self._history["i_term"].append(0.0)
            self._history["d_term"].append(0.0)
            self._history["output"].append(0.0)
            self._prev_error = error
            self._prev_measurement = measurement
            self._first_update = False
            return 0.0

        # --- Proportional term ---
        p_term = self.Kp * error

        # --- Integral term (with integral separation) ---
        # Integral separation: only accumulate integral when error is small
        # This prevents integral windup during large transients
        if self.integral_separation and abs(error) > self.integral_separation_threshold:
            # Error is large: skip integral accumulation
            pass
        else:
            # Trapezoidal integration for better accuracy
            if self._first_update:
                self._integral += error * self.dt
            else:
                self._integral += (self._prev_error + error) / 2.0 * self.dt

        # Anti-windup: clamp integral accumulator
        self._integral = np.clip(self._integral, self.integral_min, self.integral_max)
        i_term = self.Ki * self._integral

        # --- Derivative term ---
        # Derivative on measurement (not error) to avoid derivative kick
        # when setpoint changes abruptly
        if self._first_update:
            raw_derivative = 0.0
        else:
            raw_derivative = -(measurement - self._prev_measurement) / self.dt

        # Low-pass filter on derivative
        alpha = self.derivative_filter_coeff
        filtered_derivative = (
            alpha * raw_derivative + (1 - alpha) * self._prev_derivative
        )

        # Incomplete derivative: additional first-order filter
        # This further reduces high-frequency noise at the cost of
        # slightly delayed derivative response
        if self.incomplete_derivative:
            beta = self.incomplete_derivative_coeff
            d_filtered = beta * filtered_derivative + (1 - beta) * self._prev_incomplete_d
            self._prev_incomplete_d = d_filtered
        else:
            d_filtered = filtered_derivative

        d_term = self.Kd * d_filtered

        # --- Compute total output ---
        output = p_term + i_term + d_term

        # Clamp output
        output_clamped = np.clip(output, self.output_min, self.output_max)

        # Anti-windup back-calculation: if output is saturated, prevent
        # integral from growing further in the direction of saturation
        if output != output_clamped and self.Ki != 0:
            # Back-calculate the excess
            excess = output - output_clamped
            self._integral -= excess / self.Ki
            self._integral = np.clip(
                self._integral, self.integral_min, self.integral_max
            )
            i_term = self.Ki * self._integral
            output_clamped = np.clip(p_term + i_term + d_term, self.output_min, self.output_max)

        # --- Update internal state ---
        self._prev_error = error
        self._prev_derivative = filtered_derivative
        self._prev_measurement = measurement
        self._first_update = False

        # --- Record history ---
        self._history["time"].append(t)
        self._history["setpoint"].append(setpoint)
        self._history["measurement"].append(measurement)
        self._history["error"].append(error)
        self._history["p_term"].append(p_term)
        self._history["i_term"].append(i_term)
        self._history["d_term"].append(d_term)
        self._history["output"].append(output_clamped)

        return output_clamped

    @property
    def history(self) -> Dict[str, np.ndarray]:
        """Return history as numpy arrays for analysis and plotting.

        Returns:
            Dictionary with keys: time, setpoint, measurement, error,
            p_term, i_term, d_term, output.
        """
        return {k: np.array(v) for k, v in self._history.items()}

    @property
    def gains(self) -> Tuple[float, float, float]:
        """Return current PID gains as (Kp, Ki, Kd) tuple."""
        return (self.Kp, self.Ki, self.Kd)

    @gains.setter
    def gains(self, value: Tuple[float, float, float]) -> None:
        """Set PID gains from a (Kp, Ki, Kd) tuple."""
        self.Kp, self.Ki, self.Kd = value

    def get_tuning_params(self) -> Dict[str, float]:
        """Return current tuning parameters as a dictionary.

        Useful for parameter tuning algorithms.
        """
        return {
            "Kp": self.Kp,
            "Ki": self.Ki,
            "Kd": self.Kd,
        }

    def set_tuning_params(self, params: Dict[str, float]) -> None:
        """Set tuning parameters from a dictionary.

        Args:
            params: Dictionary with keys 'Kp', 'Ki', 'Kd'.
        """
        if "Kp" in params:
            self.Kp = params["Kp"]
        if "Ki" in params:
            self.Ki = params["Ki"]
        if "Kd" in params:
            self.Kd = params["Kd"]

    def __repr__(self) -> str:
        return (
            f"PIDController(Kp={self.Kp}, Ki={self.Ki}, Kd={self.Kd}, "
            f"output_range=[{self.output_min}, {self.output_max}])"
        )
