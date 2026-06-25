"""System identification from input-output data."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy import signal, optimize

from .transfer_function import TransferFunction


@dataclass
class IdentificationResult:
    """Result of system identification.

    Attributes
    ----------
    tf : TransferFunction
        Identified transfer function.
    order : int
        Model order (numerator, denominator).
    residual : float
        Fit residual (lower is better).
    """

    tf: TransferFunction
    order: tuple[int, int]
    residual: float


class SystemIdentifier:
    """Identify a transfer function model from time-domain data.

    Uses least-squares and optimization methods to fit transfer function
    parameters to measured input-output data.
    """

    # ------------------------------------------------------------------
    # Step response identification
    # ------------------------------------------------------------------

    @staticmethod
    def from_step_response(
        t: np.ndarray, y: np.ndarray, model_order: int = 1
    ) -> IdentificationResult:
        """Identify a transfer function from step response data.

        Parameters
        ----------
        t : np.ndarray
            Time vector.
        y : np.ndarray
            Output response to a step input.
        model_order : int
            Order of the model (1 or 2).

        Returns
        -------
        IdentificationResult
        """
        t = np.asarray(t, dtype=float)
        y = np.asarray(y, dtype=float)
        final_val = y[-1]

        if model_order == 1:
            # First-order: y(t) = K*(1 - e^{-t/tau})
            # Find tau: time to reach 63.2% of final value
            target = 0.632 * final_val
            idx = np.argmin(np.abs(y - target))
            tau = t[idx] if t[idx] > 0 else 1.0
            K = final_val

            tf = TransferFunction.first_order(gain=K, tau=tau, name="G_id")

        elif model_order == 2:
            # Second-order: use overshoot and settling time
            peak_idx = np.argmax(y)
            peak_val = y[peak_idx]
            peak_time = t[peak_idx]

            if abs(final_val) > 1e-12:
                os = (peak_val - final_val) / abs(final_val)
            else:
                os = 0.0

            K = final_val

            if os > 0 and os < 1:
                # Underdamped
                zeta = -np.log(os) / np.sqrt(np.pi**2 + np.log(os)**2)
                wd = np.pi / peak_time if peak_time > 0 else 1.0
                omega_n = wd / np.sqrt(1 - zeta**2)
            else:
                # Critically damped or overdamped
                zeta = 1.0
                # Estimate from 10-90% rise time
                t10 = t[np.argmin(np.abs(y - 0.1 * final_val))]
                t90 = t[np.argmin(np.abs(y - 0.9 * final_val))]
                rise = t90 - t10
                omega_n = 1.67 / rise if rise > 0 else 1.0

            tf = TransferFunction.second_order(gain=K, omega_n=omega_n, zeta=zeta, name="G_id")
        else:
            raise ValueError(f"Unsupported model order: {model_order}")

        # Compute residual
        sys_id = signal.lti(tf.num, tf.den)
        _, y_fit = signal.step(sys_id, T=t)
        residual = float(np.sqrt(np.mean((y - y_fit) ** 2)))

        return IdentificationResult(tf=tf, order=(model_order, model_order), residual=residual)

    # ------------------------------------------------------------------
    # Frequency response identification
    # ------------------------------------------------------------------

    @staticmethod
    def from_frequency_response(
        omega: np.ndarray,
        mag_db: np.ndarray,
        phase_deg: np.ndarray,
        order: int = 2,
    ) -> IdentificationResult:
        """Identify a transfer function from frequency response data.

        Parameters
        ----------
        omega : np.ndarray
            Frequency vector (rad/s).
        mag_db : np.ndarray
            Magnitude in dB.
        phase_deg : np.ndarray
            Phase in degrees.
        order : int
            Model order.

        Returns
        -------
        IdentificationResult
        """
        omega = np.asarray(omega, dtype=float)
        mag_db = np.asarray(mag_db, dtype=float)
        phase_deg = np.asarray(phase_deg, dtype=float)

        mag_linear = 10 ** (mag_db / 20)
        phase_rad = np.radians(phase_deg)
        target_complex = mag_linear * np.exp(1j * phase_rad)

        def error_fn(params):
            num_coeffs = params[: order + 1]
            den_coeffs = np.concatenate([[1.0], params[order + 1 :]])
            tf_temp = TransferFunction(num_coeffs, den_coeffs)
            resp = tf_temp.eval_freq(omega)
            return np.sum(np.abs(resp - target_complex) ** 2)

        # Initial guess: simple poles at -1
        x0 = np.ones(2 * order + 1)
        x0[order + 1 :] = np.arange(1, order + 1)  # Denominator coefficients

        result = optimize.minimize(error_fn, x0, method="Nelder-Mead", options={"maxiter": 10000})
        opt_params = result.x

        num_coeffs = opt_params[: order + 1]
        den_coeffs = np.concatenate([[1.0], opt_params[order + 1 :]])
        tf = TransferFunction(num_coeffs, den_coeffs, name="G_id")

        return IdentificationResult(
            tf=tf, order=(order, order), residual=float(result.fun)
        )

    # ------------------------------------------------------------------
    # Pole-zero identification from impulse response
    # ------------------------------------------------------------------

    @staticmethod
    def from_impulse_response(
        t: np.ndarray, y: np.ndarray, n_poles: int = 2, n_zeros: int = 0
    ) -> IdentificationResult:
        """Identify poles and zeros from impulse response using Prony's method.

        Parameters
        ----------
        t : np.ndarray
            Time vector.
        y : np.ndarray
            Impulse response.
        n_poles : int
            Number of poles to estimate.
        n_zeros : int
            Number of zeros to estimate.

        Returns
        -------
        IdentificationResult
        """
        t = np.asarray(t, dtype=float)
        y = np.asarray(y, dtype=float)
        dt = t[1] - t[0]
        n = len(y)

        # Prony's method: fit sum of exponentials
        # y(t) = sum A_i * exp(p_i * t)
        order = n_poles

        # Build Hankel matrix
        L = n // 2
        H = np.zeros((L, order + 1))
        for i in range(L):
            for j in range(order + 1):
                if i + j < n:
                    H[i, j] = y[i + j]

        # Solve using SVD
        H_shifted = H[:, :-1]
        target = H[:, -1]

        # Least squares
        coeffs, _, _, _ = np.linalg.lstsq(-H_shifted, target, rcond=None)
        # Characteristic polynomial coefficients
        char_coeffs = np.concatenate([[1.0], coeffs])

        # Find roots (poles in z-domain)
        z_roots = np.roots(char_coeffs)
        # Convert to s-domain: s = ln(z)/dt
        s_poles = np.log(z_roots + 1e-30) / dt

        # Build transfer function
        den = np.poly(s_poles.real)  # Use real parts for stability
        gain = np.sum(y) * dt  # Approximate gain
        num = np.array([gain])
        tf = TransferFunction(num, den, name="G_id")

        # Compute residual
        sys_id = signal.lti(tf.num, tf.den)
        _, y_fit = signal.impulse(sys_id, T=t)
        residual = float(np.sqrt(np.mean((y - y_fit) ** 2)))

        return IdentificationResult(tf=tf, order=(0, n_poles), residual=residual)
