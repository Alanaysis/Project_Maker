"""Frequency-domain response analysis (Bode, Nyquist, stability margins)."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy import signal

from .transfer_function import TransferFunction


@dataclass
class BodeData:
    """Container for Bode plot data.

    Attributes
    ----------
    omega : np.ndarray
        Frequency vector (rad/s).
    magnitude_db : np.ndarray
        Magnitude in decibels.
    phase_deg : np.ndarray
        Phase in degrees.
    """

    omega: np.ndarray
    magnitude_db: np.ndarray
    phase_deg: np.ndarray


@dataclass
class NyquistData:
    """Container for Nyquist plot data.

    Attributes
    ----------
    real : np.ndarray
        Real part of G(jw).
    imag : np.ndarray
        Imaginary part of G(jw).
    omega : np.ndarray
        Frequency vector.
    """

    real: np.ndarray
    imag: np.ndarray
    omega: np.ndarray


@dataclass
class StabilityMargins:
    """Gain and phase margins.

    Attributes
    ----------
    gain_margin_db : float | None
        Gain margin in dB (None if infinite).
    gain_margin_freq : float
        Frequency at which gain margin is measured (rad/s).
    phase_margin_deg : float | None
        Phase margin in degrees (None if infinite).
    phase_margin_freq : float
        Frequency at which phase margin is measured (rad/s).
    """

    gain_margin_db: float | None
    gain_margin_freq: float
    phase_margin_deg: float | None
    phase_margin_freq: float


class FrequencyResponse:
    """Frequency-domain analysis for LTI systems.

    Parameters
    ----------
    tf : TransferFunction
        The system transfer function.
    """

    def __init__(self, tf: TransferFunction) -> None:
        self.tf = tf
        self._sys = signal.lti(tf.num, tf.den)

    # ------------------------------------------------------------------
    # Bode plot data
    # ------------------------------------------------------------------

    def bode(self, omega: np.ndarray | None = None, n_points: int = 1000) -> BodeData:
        """Compute Bode plot data.

        Parameters
        ----------
        omega : array-like, optional
            Frequency vector in rad/s. If None, automatically generated.
        n_points : int
            Number of frequency points when omega is auto-generated.

        Returns
        -------
        BodeData
        """
        if omega is None:
            omega = np.logspace(-2, 2, n_points)
        w, mag, phase = signal.bode(self._sys, omega)
        return BodeData(omega=w, magnitude_db=mag, phase_deg=phase)

    # ------------------------------------------------------------------
    # Nyquist plot data
    # ------------------------------------------------------------------

    def nyquist(self, omega: np.ndarray | None = None, n_points: int = 1000) -> NyquistData:
        """Compute Nyquist plot data.

        Parameters
        ----------
        omega : array-like, optional
            Frequency vector in rad/s.
        n_points : int
            Number of frequency points.

        Returns
        -------
        NyquistData
        """
        if omega is None:
            omega = np.logspace(-2, 3, n_points)
        resp = self.tf.eval_freq(omega)
        return NyquistData(real=resp.real, imag=resp.imag, omega=omega)

    # ------------------------------------------------------------------
    # Stability margins
    # ------------------------------------------------------------------

    def margins(self) -> StabilityMargins:
        """Compute gain and phase margins.

        Returns
        -------
        StabilityMargins
        """
        omega = np.logspace(-3, 3, 10000)
        resp = self.tf.eval_freq(omega)
        mag = np.abs(resp)
        phase_deg = np.degrees(np.angle(resp))

        # Gain margin: at phase crossover (phase = -180 deg)
        # Find where phase crosses -180
        phase_unwrapped = np.unwrap(np.radians(phase_deg))
        phase_180_crossings = np.where(np.diff(np.sign(phase_deg + 180)))[0]

        gm_db = None
        wgm = 0.0
        if len(phase_180_crossings) > 0:
            idx = phase_180_crossings[0]
            # Interpolate
            w1, w2 = omega[idx], omega[idx + 1]
            p1, p2 = phase_deg[idx], phase_deg[idx + 1]
            frac = (-180 - p1) / (p2 - p1) if p2 != p1 else 0.5
            wgm = w1 + frac * (w2 - w1)
            # Gain at crossover frequency
            mag_at_wgm = np.interp(wgm, omega, mag)
            if mag_at_wgm > 0:
                gm_db = float(20 * np.log10(1.0 / mag_at_wgm))

        # Phase margin: at gain crossover (|G(jw)| = 1, i.e., 0 dB)
        mag_db = 20 * np.log10(mag + 1e-30)
        gain_0db_crossings = np.where(np.diff(np.sign(mag_db)))[0]

        pm_deg = None
        wpm = 0.0
        if len(gain_0db_crossings) > 0:
            idx = gain_0db_crossings[0]
            w1, w2 = omega[idx], omega[idx + 1]
            m1, m2 = mag_db[idx], mag_db[idx + 1]
            frac = (0 - m1) / (m2 - m1) if m2 != m1 else 0.5
            wpm = w1 + frac * (w2 - w1)
            phase_at_wpm = np.interp(wpm, omega, phase_deg)
            pm_deg = float(180 + phase_at_wpm)

        return StabilityMargins(
            gain_margin_db=gm_db,
            gain_margin_freq=float(wgm),
            phase_margin_deg=pm_deg,
            phase_margin_freq=float(wpm),
        )

    # ------------------------------------------------------------------
    # Frequency response at specific omega
    # ------------------------------------------------------------------

    def eval(self, omega: float) -> complex:
        """Evaluate G(j*omega)."""
        return complex(self.tf.eval_freq(np.array([omega]))[0])

    def magnitude(self, omega: float) -> float:
        """Magnitude |G(jw)| in dB."""
        return 20 * np.log10(abs(self.eval(omega)))

    def phase(self, omega: float) -> float:
        """Phase of G(jw) in degrees."""
        return np.degrees(np.angle(self.eval(omega)))

    # ------------------------------------------------------------------
    # Resonance peak
    # ------------------------------------------------------------------

    def resonance_peak(self, omega_range: tuple[float, float] = (0.01, 100)) -> dict:
        """Find the resonance peak (maximum magnitude).

        Returns
        -------
        dict
            Keys: 'peak_db', 'peak_freq', 'peak_linear'.
        """
        omega = np.logspace(np.log10(omega_range[0]), np.log10(omega_range[1]), 5000)
        resp = self.tf.eval_freq(omega)
        mag_db = 20 * np.log10(np.abs(resp))
        idx = np.argmax(mag_db)
        return {
            "peak_db": float(mag_db[idx]),
            "peak_freq": float(omega[idx]),
            "peak_linear": float(np.abs(resp[idx])),
        }

    # ------------------------------------------------------------------
    # Bandwidth
    # ------------------------------------------------------------------

    def bandwidth(self, db_drop: float = -3.0) -> float:
        """Find the bandwidth (frequency where magnitude drops by db_drop from DC).

        Parameters
        ----------
        db_drop : float
            Drop in dB from DC gain (default -3 dB).

        Returns
        -------
        float
            Bandwidth in rad/s.
        """
        omega = np.logspace(-3, 3, 10000)
        resp = self.tf.eval_freq(omega)
        mag_db = 20 * np.log10(np.abs(resp))
        dc_db = mag_db[0]
        target = dc_db + db_drop
        # Find first crossing
        crossings = np.where(np.diff(np.sign(mag_db - target)))[0]
        if len(crossings) == 0:
            return float("inf")
        idx = crossings[0]
        # Linear interpolation
        w1, w2 = omega[idx], omega[idx + 1]
        m1, m2 = mag_db[idx], mag_db[idx + 1]
        frac = (target - m1) / (m2 - m1) if m2 != m1 else 0.5
        return float(w1 + frac * (w2 - w1))
