"""
PID Tuner - Automatic parameter tuning methods.

This module implements classical PID tuning rules that determine PID gains
from system characteristics (like ultimate gain and period).

Methods implemented:
1. Ziegler-Nichols (Closed-Loop / Ultimate Cycle Method)
2. Cohen-Coon (Process Reaction Curve Method)
3. Tyreus-Luyben (modified Ziegler-Nichols for less overshoot)
4. Manual tuning guidance

The Ziegler-Nichols method:
    1. Set Ki=0, Kd=0
    2. Gradually increase Kp until the system oscillates with constant amplitude
    3. Record this Kp as Ku (ultimate gain) and oscillation period as Tu (ultimate period)
    4. Calculate PID gains from Ku and Tu using tuning rules

The Cohen-Coon method:
    1. Apply a step input to the open-loop system
    2. Record the reaction curve (S-shaped step response)
    3. Find the dead time (L), time constant (τ), and gain (K)
    4. Calculate PID gains from these parameters
"""

import numpy as np
from typing import Dict, Optional, Tuple, Callable
from .pid_controller import PIDController
from .plant import FirstOrderPlant, SecondOrderPlant


class PIDTuner:
    """Automatic PID parameter tuning.

    Supports multiple tuning methods:

    1. **Ziegler-Nichols** (classic method):
       - Finds ultimate gain Ku and ultimate period Tu by increasing Kp
       - Applies empirical formulas to compute Kp, Ki, Kd
       - Usually gives aggressive tuning (fast but overshooty)

    2. **Cohen-Coon** (process reaction curve):
       - Uses step response of open-loop system
       - Better for processes with significant dead time
       - Generally gives less aggressive tuning than Z-N

    3. **Tyreus-Luyben** (conservative Z-N):
       - Same method as Z-N to find Ku and Tu
       - Different formulas for less overshoot
       - Better for processes where stability is critical

    Parameters:
        dt: Time step for simulation. Default: 0.01
    """

    def __init__(self, dt: float = 0.01):
        self.dt = dt

    def ziegler_nichols(
        self,
        plant_update_fn: Callable[[float], float],
        setpoint: float = 1.0,
        initial_kp: float = 0.1,
        kp_increment: float = 0.1,
        max_kp: float = 100.0,
        oscillation_threshold: float = 0.01,
        min_oscillation_periods: int = 5,
        max_steps: int = 50000,
    ) -> Dict[str, float]:
        """Tune PID using Ziegler-Nichols closed-loop method.

        The algorithm:
            1. Start with only P control (Ki=0, Kd=0)
            2. Gradually increase Kp
            3. At each Kp, run a simulation and check for sustained oscillation
            4. When oscillation is detected, record Ku (ultimate gain) and
               Tu (ultimate period)
            5. Calculate PID gains using Ziegler-Nichols formulas

        Ziegler-Nichols tuning rules:
            Controller | Kp      | Ki        | Kd
            P          | 0.5*Ku  | -         | -
            PI         | 0.45*Ku | 0.54*Ku/Tu| -
            PID        | 0.6*Ku  | 1.2*Ku/Tu | 0.075*Ku*Tu

        Args:
            plant_update_fn: Function that takes control input and returns plant output.
            setpoint: Target value for the simulation.
            initial_kp: Starting Kp value. Default: 0.1
            kp_increment: How much to increase Kp each step. Default: 0.1
            max_kp: Maximum Kp to try before giving up. Default: 100.0
            oscillation_threshold: Minimum amplitude for oscillation detection.
            min_oscillation_periods: Minimum oscillation periods to confirm. Default: 5
            max_steps: Maximum simulation steps per Kp trial. Default: 50000

        Returns:
            Dictionary with keys:
                - 'Kp', 'Ki', 'Kd': Tuned PID gains
                - 'Ku': Ultimate gain
                - 'Tu': Ultimate period
                - 'method': 'ziegler_nichols'

        Raises:
            RuntimeError: If no oscillation is found up to max_kp.
        """
        kp = initial_kp

        while kp <= max_kp:
            # Reset plant for each trial
            # We need to create a fresh closure for each trial
            ku, tu = self._find_oscillation(
                plant_update_fn, setpoint, kp, max_steps,
                oscillation_threshold, min_oscillation_periods
            )

            if ku is not None and tu is not None:
                # Apply Ziegler-Nichols PID tuning rules
                tuned_kp = 0.6 * ku
                tuned_ki = 1.2 * ku / tu
                tuned_kd = 0.075 * ku * tu

                return {
                    "Kp": tuned_kp,
                    "Ki": tuned_ki,
                    "Kd": tuned_kd,
                    "Ku": ku,
                    "Tu": tu,
                    "method": "ziegler_nichols",
                }

            kp += kp_increment

        raise RuntimeError(
            f"No sustained oscillation found up to Kp={max_kp}. "
            "The system may be inherently stable or the Kp range is insufficient."
        )

    def cohen_coon(
        self,
        plant_update_fn: Callable[[float], float],
        step_magnitude: float = 1.0,
        max_steps: int = 10000,
    ) -> Dict[str, float]:
        """Tune PID using Cohen-Coon process reaction curve method.

        The algorithm:
            1. Apply a step input to the open-loop plant
            2. Record the step response
            3. Identify process parameters:
               - K: steady-state gain (Δoutput / Δinput)
               - L: dead time (time until response begins)
               - τ: time constant (from the exponential part)
            4. Calculate PID gains using Cohen-Coon formulas

        Cohen-Coon tuning rules:
            Kp = (1/K) * (τ/L + 1/3)
            Ki = Kp / (L * (32 + 6*L/τ) / (13 + 8*L/τ))
            Kd = Kp * L * 4 / (11 + 2*L/τ)

        Args:
            plant_update_fn: Function that takes control input and returns plant output.
            step_magnitude: Size of step input. Default: 1.0
            max_steps: Maximum simulation steps. Default: 10000

        Returns:
            Dictionary with keys:
                - 'Kp', 'Ki', 'Kd': Tuned PID gains
                - 'K': Process gain
                - 'L': Dead time
                - 'tau': Time constant
                - 'method': 'cohen_coon'
        """
        # Run open-loop step response
        outputs = []
        for _ in range(max_steps):
            y = plant_update_fn(step_magnitude)
            outputs.append(y)

        outputs = np.array(outputs)
        t = np.arange(len(outputs)) * self.dt

        # Find process parameters
        K, L, tau = self._identify_first_order(outputs, step_magnitude)

        # Cohen-Coon formulas
        if L == 0:
            L = self.dt  # Avoid division by zero

        r = L / tau  # Dead time ratio

        kp = (1.0 / K) * (tau / L + 1.0 / 3.0)
        ti = L * (32.0 + 6.0 * r) / (13.0 + 8.0 * r)
        td = L * 4.0 / (11.0 + 2.0 * r)

        ki = kp / ti
        kd = kp * td

        return {
            "Kp": kp,
            "Ki": ki,
            "Kd": kd,
            "K": K,
            "L": L,
            "tau": tau,
            "method": "cohen_coon",
        }

    def tyreus_luyben(
        self,
        plant_update_fn: Callable[[float], float],
        setpoint: float = 1.0,
        initial_kp: float = 0.1,
        kp_increment: float = 0.1,
        max_kp: float = 100.0,
        oscillation_threshold: float = 0.01,
        min_oscillation_periods: int = 5,
        max_steps: int = 50000,
    ) -> Dict[str, float]:
        """Tune PID using Tyreus-Luyben method.

        This is a modification of Ziegler-Nichols that produces less
        aggressive tuning with less overshoot. Same method to find Ku and Tu,
        but different formulas:

        Tyreus-Luyben tuning rules:
            Kp = 0.45 * Ku
            Ki = 0.45 * Ku / (2.2 * Tu)
            Kd = 0.45 * Ku * (Tu / 6.3)

        Args:
            plant_update_fn: Function that takes control input and returns plant output.
            setpoint: Target value. Default: 1.0
            initial_kp: Starting Kp. Default: 0.1
            kp_increment: Kp increment. Default: 0.1
            max_kp: Maximum Kp. Default: 100.0
            oscillation_threshold: Minimum amplitude. Default: 0.01
            min_oscillation_periods: Minimum periods. Default: 5
            max_steps: Maximum steps per trial. Default: 50000

        Returns:
            Dictionary with keys:
                - 'Kp', 'Ki', 'Kd': Tuned PID gains
                - 'Ku': Ultimate gain
                - 'Tu': Ultimate period
                - 'method': 'tyreus_luyben'

        Raises:
            RuntimeError: If no oscillation is found.
        """
        kp = initial_kp

        while kp <= max_kp:
            ku, tu = self._find_oscillation(
                plant_update_fn, setpoint, kp, max_steps,
                oscillation_threshold, min_oscillation_periods
            )

            if ku is not None and tu is not None:
                # Tyreus-Luyben formulas
                tuned_kp = 0.45 * ku
                tuned_ki = 0.45 * ku / (2.2 * tu)
                tuned_kd = 0.45 * ku * (tu / 6.3)

                return {
                    "Kp": tuned_kp,
                    "Ki": tuned_ki,
                    "Kd": tuned_kd,
                    "Ku": ku,
                    "Tu": tu,
                    "method": "tyreus_luyben",
                }

            kp += kp_increment

        raise RuntimeError(
            f"No sustained oscillation found up to Kp={max_kp}."
        )

    def _find_oscillation(
        self,
        plant_update_fn: Callable[[float], float],
        setpoint: float,
        kp: float,
        max_steps: int,
        threshold: float,
        min_periods: int,
    ) -> Tuple[Optional[float], Optional[float]]:
        """Run a P-only control loop and detect sustained oscillation.

        Returns (Ku, Tu) if oscillation is detected, (None, None) otherwise.
        """
        integral = 0.0
        prev_output = 0.0
        outputs = []

        for step in range(max_steps):
            # P-only control
            error = setpoint - prev_output
            control = kp * error
            output = plant_update_fn(control)
            outputs.append(output)
            prev_output = output

        outputs = np.array(outputs)

        # Check for oscillation in the second half of the simulation
        half = len(outputs) // 2
        segment = outputs[half:]

        if len(segment) < 100:
            return None, None

        # Find zero crossings of the derivative (peaks and troughs)
        diff = np.diff(segment)
        crossings = np.where(np.diff(np.sign(diff)))[0]

        if len(crossings) < min_periods * 2:
            return None, None

        # Calculate oscillation amplitude
        peak_values = segment[crossings]
        amplitude = (np.max(peak_values) - np.min(peak_values)) / 2.0

        if amplitude < threshold:
            return None, None

        # Calculate period from zero crossings
        crossing_times = crossings * self.dt
        if len(crossing_times) >= 2:
            # Half-periods between consecutive crossings
            half_periods = np.diff(crossing_times)
            period = 2.0 * np.mean(half_periods)
        else:
            return None, None

        # The current Kp that caused oscillation is the ultimate gain
        return kp, period

    def _identify_first_order(
        self, outputs: np.ndarray, step_magnitude: float
    ) -> Tuple[float, float, float]:
        """Identify first-order process parameters from step response.

        Finds:
            K: steady-state gain
            L: dead time (time to first reaching 5% of final value)
            tau: time constant (time to reach 63.2% of final value)
        """
        final_value = outputs[-1]
        K = final_value / step_magnitude

        # Dead time: when output first reaches 5% of final value
        threshold_5pct = 0.05 * final_value
        L_indices = np.where(outputs > threshold_5pct)[0]
        L = L_indices[0] * self.dt if len(L_indices) > 0 else 0.0

        # Time constant: when output reaches 63.2% of final value
        threshold_63pct = 0.632 * final_value
        tau_indices = np.where(outputs > threshold_63pct)[0]
        tau = tau_indices[0] * self.dt if len(tau_indices) > 0 else self.dt

        # tau is measured from start, but should be from end of dead time
        tau = max(tau - L, self.dt)

        return K, L, tau

    def manual_tune(
        self,
        plant_update_fn: Callable[[float], float],
        setpoint: float = 1.0,
        initial_params: Optional[Dict[str, float]] = None,
        duration: float = 10.0,
        max_iterations: int = 10,
    ) -> Dict[str, float]:
        """Manual tuning with iterative guidance.

        This method provides a structured approach to manual tuning by
        running simulations and suggesting parameter adjustments based
        on the step response characteristics.

        The algorithm:
            1. Start with initial parameters (or defaults)
            2. Run a closed-loop simulation
            3. Analyze performance metrics
            4. Suggest adjustments based on rules of thumb
            5. Repeat until satisfactory or max iterations reached

        Args:
            plant_update_fn: Function that takes control input and returns plant output.
            setpoint: Target value. Default: 1.0
            initial_params: Starting PID parameters. Default: {"Kp": 1.0, "Ki": 0.0, "Kd": 0.0}
            duration: Simulation duration per iteration. Default: 10.0
            max_iterations: Maximum tuning iterations. Default: 10

        Returns:
            Dictionary with keys:
                - 'Kp', 'Ki', 'Kd': Tuned PID gains
                - 'iterations': Number of iterations performed
                - 'method': 'manual'
        """
        if initial_params is None:
            params = {"Kp": 1.0, "Ki": 0.0, "Kd": 0.0}
        else:
            params = dict(initial_params)

        for iteration in range(max_iterations):
            # Run simulation with current parameters
            controller = PIDController(
                Kp=params.get("Kp", 1.0),
                Ki=params.get("Ki", 0.0),
                Kd=params.get("Kd", 0.0),
                dt=self.dt,
            )

            # We need a fresh plant for each iteration
            # Since we only have plant_update_fn, we simulate manually
            num_steps = int(duration / self.dt)
            outputs = []
            controller.reset()

            prev_output = 0.0
            for _ in range(num_steps):
                control = controller.update(setpoint, prev_output, 0.0)
                prev_output = plant_update_fn(control)
                outputs.append(prev_output)

            outputs = np.array(outputs)

            # Analyze performance
            final_value = outputs[-1]
            max_value = np.max(outputs)

            # Calculate metrics
            if setpoint != 0:
                overshoot = max(0.0, (max_value - setpoint) / abs(setpoint) * 100.0)
                ss_error = abs(final_value - setpoint) / abs(setpoint)
            else:
                overshoot = 0.0
                ss_error = abs(final_value)

            # Find settling time (2% band)
            band = 0.02 * abs(setpoint) if setpoint != 0 else 0.02
            outside_band = np.abs(outputs - setpoint) > band
            if np.any(outside_band):
                settling_idx = np.where(outside_band)[0][-1]
                settling_time = settling_idx * self.dt
            else:
                settling_time = 0.0

            # Apply tuning rules
            kp = params.get("Kp", 1.0)
            ki = params.get("Ki", 0.0)
            kd = params.get("Kd", 0.0)

            # Rule-based adjustments
            if overshoot > 20:
                # Too much overshoot: reduce Kp, increase Kd
                kp *= 0.8
                kd = max(kd, kp * settling_time / 8.0)
            elif overshoot > 10:
                # Moderate overshoot: slight adjustment
                kp *= 0.9
                kd = max(kd, kp * settling_time / 10.0)

            if ss_error > 0.05:
                # Steady-state error too high: increase Ki
                ki = max(ki, kp / (2.0 * max(settling_time, 1.0)))
            elif ss_error > 0.02:
                # Moderate steady-state error: slight increase
                ki = max(ki, kp / (4.0 * max(settling_time, 1.0)))

            if settling_time > duration * 0.8:
                # Too slow: increase Kp
                kp *= 1.2

            params = {"Kp": kp, "Ki": ki, "Kd": kd}

        return {
            "Kp": params["Kp"],
            "Ki": params["Ki"],
            "Kd": params["Kd"],
            "iterations": max_iterations,
            "method": "manual",
        }

    @staticmethod
    def get_tuning_guide() -> str:
        """Return a text guide for manual PID tuning.

        Returns:
            Multi-line string with tuning guidance.
        """
        return """
=== PID Manual Tuning Guide ===

Step 1: P-only tuning (find starting Kp)
  - Set Ki=0, Kd=0
  - Increase Kp until the system oscillates
  - This gives you a feel for the system's response

Step 2: Add Integral (eliminate steady-state error)
  - Start with Ki = Kp / (2 * expected_settling_time)
  - Increase Ki if steady-state error is too slow to eliminate
  - Decrease Ki if oscillation occurs

Step 3: Add Derivative (reduce overshoot)
  - Start with Kd = Kp * (expected_settling_time / 8)
  - Increase Kd to reduce overshoot and settling time
  - Decrease Kd if the output becomes noisy

Common issues:
  - Oscillation: Kp too high, or Ki too high
  - Slow response: Kp too low
  - Steady-state error: Ki too low (or = 0)
  - Noisy output: Kd too high
  - Overshoot: Kp or Kd too high

Rules of thumb:
  - Kp: Controls speed of response
  - Ki: Eliminates steady-state error
  - Kd: Provides damping (reduces overshoot)

Improved PID variants:
  - Integral separation: Disable integral when error is large
  - Derivative on measurement: Avoid derivative kick on setpoint changes
  - Incomplete derivative: Additional filtering for noisy systems
  - Dead zone: Ignore small errors (for systems with friction)
"""
