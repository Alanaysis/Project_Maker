"""Time-domain response analysis for LTI systems."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy import signal

from .transfer_function import TransferFunction


@dataclass
class TimeResponseData:
    """Container for time-domain response data.

    Attributes
    ----------
    t : np.ndarray
        Time vector.
    y : np.ndarray
        Output response.
    u : np.ndarray | None
        Input signal (if applicable).
    """

    t: np.ndarray
    y: np.ndarray
    u: np.ndarray | None = None


class TimeResponse:
    """Compute time-domain responses of LTI systems.

    Parameters
    ----------
    tf : TransferFunction
        The system transfer function.
    """

    def __init__(self, tf: TransferFunction) -> None:
        self.tf = tf
        self._sys = signal.lti(tf.num, tf.den)

    # ------------------------------------------------------------------
    # Step response
    # ------------------------------------------------------------------

    def step(self, T: np.ndarray | None = None, t_final: float | None = None) -> TimeResponseData:
        """Compute the step response.

        Parameters
        ----------
        T : array-like, optional
            Time points at which to evaluate. If None, automatically chosen.
        t_final : float, optional
            Final time when T is not given.
        """
        if T is None:
            if t_final is None:
                t_final = self._auto_tfinal()
            T = np.linspace(0, t_final, 1000)
        t, y = signal.step(self._sys, T=T)
        u = np.ones_like(t)
        return TimeResponseData(t=t, y=y, u=u)

    # ------------------------------------------------------------------
    # Impulse response
    # ------------------------------------------------------------------

    def impulse(self, T: np.ndarray | None = None, t_final: float | None = None) -> TimeResponseData:
        """Compute the impulse response."""
        if T is None:
            if t_final is None:
                t_final = self._auto_tfinal()
            T = np.linspace(0, t_final, 1000)
        t, y = signal.impulse(self._sys, T=T)
        return TimeResponseData(t=t, y=y)

    # ------------------------------------------------------------------
    # Ramp response
    # ------------------------------------------------------------------

    def ramp(self, T: np.ndarray | None = None, t_final: float | None = None) -> TimeResponseData:
        """Compute the ramp response (input r(t) = t).

        Implemented as the step response of s*G(s) integrated, or equivalently
        convolving the impulse response with a ramp.
        """
        if T is None:
            if t_final is None:
                t_final = self._auto_tfinal()
            T = np.linspace(0, t_final, 1000)

        dt = T[1] - T[0]
        # Ramp input
        u = T.copy()
        # Compute response to arbitrary input via lsim
        t, y, _ = signal.lsim(self._sys, u, T)
        return TimeResponseData(t=t, y=y, u=u)

    # ------------------------------------------------------------------
    # General input response
    # ------------------------------------------------------------------

    def lsim(self, u: np.ndarray, T: np.ndarray) -> TimeResponseData:
        """Compute the response to an arbitrary input.

        Parameters
        ----------
        u : np.ndarray
            Input signal values.
        T : np.ndarray
            Time points.
        """
        t, y, _ = signal.lsim(self._sys, u, T)
        return TimeResponseData(t=t, y=y, u=u)

    # ------------------------------------------------------------------
    # Initial condition response
    # ------------------------------------------------------------------

    def initial(self, x0: np.ndarray, T: np.ndarray | None = None, t_final: float | None = None) -> TimeResponseData:
        """Compute the zero-input response for given initial conditions.

        Parameters
        ----------
        x0 : array-like
            Initial state vector.
        T : array-like, optional
            Time points.
        t_final : float, optional
            Final time when T is not given.
        """
        if T is None:
            if t_final is None:
                t_final = self._auto_tfinal()
            T = np.linspace(0, t_final, 1000)
        # Use state-space representation for initial response
        A, B, C, D = signal.tf2ss(self.tf.num, self.tf.den)
        from scipy.integrate import solve_ivp
        x0 = np.atleast_1d(np.asarray(x0, dtype=float))

        def state_deriv(t, x):
            return A @ x

        sol = solve_ivp(state_deriv, [T[0], T[-1]], x0, t_eval=T, rtol=1e-10, atol=1e-12)
        t = sol.t
        y = (C @ sol.y).flatten()
        return TimeResponseData(t=t, y=y)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _auto_tfinal(self) -> float:
        """Estimate a reasonable final time based on dominant pole."""
        poles = self.tf.poles()
        real_poles = poles[np.isreal(poles)].real
        real_poles = real_poles[real_poles < 0]
        if len(real_poles) == 0:
            return 10.0
        dominant = np.min(np.abs(real_poles))
        if dominant == 0:
            return 10.0
        # Settle in about 5 time constants
        return min(5.0 / dominant, 100.0)
