"""Performance metrics: rise time, overshoot, settling time, steady-state error."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy import signal

from .transfer_function import TransferFunction


@dataclass
class PerformanceData:
    """Container for step-response performance metrics.

    Attributes
    ----------
    rise_time : float
        Time to go from 10% to 90% of final value (seconds).
    overshoot_pct : float
        Percentage overshoot (%).
    settling_time : float
        2% settling time (seconds).
    steady_state_error : float
        Steady-state error for a unit step input.
    peak_value : float
        Maximum output value.
    peak_time : float
        Time at which peak occurs.
    final_value : float
        Final (steady-state) value.
    """

    rise_time: float
    overshoot_pct: float
    settling_time: float
    steady_state_error: float
    peak_value: float
    peak_time: float
    final_value: float


class PerformanceMetrics:
    """Compute step-response performance metrics.

    Parameters
    ----------
    tf : TransferFunction
        The system transfer function.
    """

    def __init__(self, tf: TransferFunction) -> None:
        self.tf = tf
        self._sys = signal.lti(tf.num, tf.den)

    def step_metrics(self, T: np.ndarray | None = None, t_final: float | None = None) -> PerformanceData:
        """Compute all step-response performance metrics.

        Parameters
        ----------
        T : array-like, optional
            Time points. If None, auto-generated.
        t_final : float, optional
            Final time when T is None.

        Returns
        -------
        PerformanceData
        """
        if T is None:
            if t_final is None:
                t_final = self._auto_tfinal()
            T = np.linspace(0, t_final, 10000)

        t, y = signal.step(self._sys, T=T)
        final_val = y[-1]

        # Rise time: 10% to 90%
        rt = self._rise_time(t, y, final_val)

        # Overshoot
        peak_val = np.max(y)
        peak_time = float(t[np.argmax(y)])
        if abs(final_val) > 1e-12:
            os_pct = max(0, (peak_val - final_val) / abs(final_val) * 100)
        else:
            os_pct = 0.0

        # Settling time (2% criterion)
        st = self._settling_time(t, y, final_val, tol=0.02)

        # Steady-state error
        sse = 1.0 - final_val

        return PerformanceData(
            rise_time=rt,
            overshoot_pct=float(os_pct),
            settling_time=st,
            steady_state_error=float(sse),
            peak_value=float(peak_val),
            peak_time=peak_time,
            final_value=float(final_val),
        )

    def _rise_time(self, t: np.ndarray, y: np.ndarray, final_val: float) -> float:
        """Compute 10%-90% rise time."""
        val_10 = 0.1 * final_val
        val_90 = 0.9 * final_val

        t_10 = self._crossing_time(t, y, val_10)
        t_90 = self._crossing_time(t, y, val_90)

        if t_10 is None or t_90 is None:
            return float("inf")
        return float(t_90 - t_10)

    def _settling_time(self, t: np.ndarray, y: np.ndarray, final_val: float, tol: float = 0.02) -> float:
        """Compute settling time within tolerance band."""
        band = tol * abs(final_val) if abs(final_val) > 1e-12 else tol
        # Walk backwards from the end
        for i in range(len(t) - 1, -1, -1):
            if abs(y[i] - final_val) > band:
                if i < len(t) - 1:
                    return float(t[i + 1])
                return float("inf")
        return float(t[0])

    def _crossing_time(self, t: np.ndarray, y: np.ndarray, level: float) -> float | None:
        """Find time when y first crosses a given level."""
        for i in range(len(y) - 1):
            if (y[i] - level) * (y[i + 1] - level) <= 0 and y[i] != y[i + 1]:
                # Linear interpolation
                frac = (level - y[i]) / (y[i + 1] - y[i])
                return float(t[i] + frac * (t[i + 1] - t[i]))
        return None

    # ------------------------------------------------------------------
    # Analytical formulas for standard systems
    # ------------------------------------------------------------------

    @staticmethod
    def second_order_metrics(omega_n: float, zeta: float) -> PerformanceData:
        """Analytical performance metrics for a standard second-order system.

        G(s) = omega_n^2 / (s^2 + 2*zeta*omega_n*s + omega_n^2)

        Parameters
        ----------
        omega_n : float
            Natural frequency (rad/s).
        zeta : float
            Damping ratio.

        Returns
        -------
        PerformanceData
        """
        if zeta < 0 or zeta >= 1:
            raise ValueError("Analytical formulas require 0 <= zeta < 1")

        # Rise time (approximate)
        theta = np.arccos(zeta)
        wd = omega_n * np.sqrt(1 - zeta**2)
        rt = (np.pi - theta) / wd

        # Overshoot
        os_pct = np.exp(-zeta * np.pi / np.sqrt(1 - zeta**2)) * 100

        # Settling time (2%)
        st = 4.0 / (zeta * omega_n)

        # Peak time
        pt = np.pi / wd

        # Peak value
        pv = 1.0 + os_pct / 100

        return PerformanceData(
            rise_time=rt,
            overshoot_pct=os_pct,
            settling_time=st,
            steady_state_error=0.0,
            peak_value=pv,
            peak_time=pt,
            final_value=1.0,
        )

    # ------------------------------------------------------------------
    # Steady-state error analysis
    # ------------------------------------------------------------------

    def steady_state_error(self, input_type: str = "step") -> float:
        """Compute steady-state error for standard inputs using final value theorem.

        Parameters
        ----------
        input_type : str
            One of 'step', 'ramp', 'parabolic'.

        Returns
        -------
        float
            Steady-state error.
        """
        s = 1e-10  # Small s for evaluation
        Gs = self.tf(np.array([s]))[0]

        if input_type == "step":
            return float(np.real(1.0 / (1.0 + Gs)))
        elif input_type == "ramp":
            # e_ss = 1/Kv where Kv = lim s->0 s*G(s)
            Kv = s * Gs
            if abs(Kv) < 1e-15:
                return float("inf")
            return float(np.real(1.0 / Kv))
        elif input_type == "parabolic":
            # e_ss = 1/Ka where Ka = lim s->0 s^2*G(s)
            Ka = s**2 * Gs
            if abs(Ka) < 1e-15:
                return float("inf")
            return float(np.real(1.0 / Ka))
        else:
            raise ValueError(f"Unknown input type: {input_type}")

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _auto_tfinal(self) -> float:
        """Estimate a reasonable final time."""
        poles = self.tf.poles()
        real_poles = poles[np.isreal(poles)].real
        real_poles = real_poles[real_poles < 0]
        if len(real_poles) == 0:
            return 10.0
        dominant = np.min(np.abs(real_poles))
        if dominant == 0:
            return 10.0
        return min(5.0 / dominant, 100.0)
