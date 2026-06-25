"""Controller design: PID, lead/lag compensators."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy import optimize

from .transfer_function import TransferFunction


@dataclass
class PIDParams:
    """PID controller parameters.

    Attributes
    ----------
    Kp : float
        Proportional gain.
    Ki : float
        Integral gain.
    Kd : float
        Derivative gain.
    Tf : float
        Derivative filter time constant.
    """

    Kp: float
    Ki: float
    Kd: float
    Tf: float = 0.01


class ControllerDesigner:
    """Design controllers for LTI systems.

    Parameters
    ----------
    plant : TransferFunction
        The plant transfer function.
    """

    def __init__(self, plant: TransferFunction) -> None:
        self.plant = plant

    # ------------------------------------------------------------------
    # PID tuning
    # ------------------------------------------------------------------

    def pid_ziegler_nichols(self, method: str = "step") -> PIDParams:
        """Ziegler-Nichols PID tuning.

        Parameters
        ----------
        method : str
            'step' for step-response method, 'ultimate' for ultimate-gain method.

        Returns
        -------
        PIDParams
        """
        if method == "step":
            return self._zn_step_method()
        elif method == "ultimate":
            return self._zn_ultimate_method()
        else:
            raise ValueError(f"Unknown method: {method}")

    def _zn_step_method(self) -> PIDParams:
        """Ziegler-Nichols step response method.

        Uses the reaction curve to determine K, L, T parameters.
        """
        from .time_response import TimeResponse

        tr = TimeResponse(self.plant)
        data = tr.step()
        t, y = data.t, data.y
        final_val = y[-1]

        # Find inflection point (maximum slope)
        dy = np.gradient(y, t)
        infl_idx = np.argmax(dy)

        # Tangent line parameters
        slope = dy[infl_idx]
        t_infl = t[infl_idx]
        y_infl = y[infl_idx]

        # Dead time L: where tangent line crosses zero
        if slope > 1e-12:
            L = max(t_infl - y_infl / slope, 1e-3)
        else:
            L = 0.1

        # Time constant T: where tangent line reaches final value
        if slope > 1e-12:
            T = max((final_val - y_infl) / slope + t_infl - L, 1e-3)
        else:
            T = 1.0

        K = final_val  # Process gain
        a = K * L / T if T > 0 else 0.1

        # Ziegler-Nichols PID rules
        Kp = 1.2 / a
        Ti = 2 * L
        Td = 0.5 * L

        Ki = Kp / Ti if Ti > 0 else 0
        Kd = Kp * Td

        return PIDParams(Kp=Kp, Ki=Ki, Kd=Kd)

    def _zn_ultimate_method(self) -> PIDParams:
        """Ziegler-Nichols ultimate gain method.

        Finds the critical gain Ku and critical period Tu.
        """
        Ku = self._find_ultimate_gain()
        if Ku is None:
            # Fallback to step method
            return self._zn_step_method()

        Tu = self._find_ultimate_period(Ku)

        # Ziegler-Nichols rules
        Kp = 0.6 * Ku
        Ti = 0.5 * Tu
        Td = 0.125 * Tu

        Ki = Kp / Ti if Ti > 0 else 0
        Kd = Kp * Td

        return PIDParams(Kp=Kp, Ki=Ki, Kd=Kd)

    def _find_ultimate_gain(self) -> float | None:
        """Find the ultimate gain using binary search."""
        from .stability import StabilityAnalyzer

        sa = StabilityAnalyzer(self.plant)
        k_low, k_high = 0.01, 1000.0

        for _ in range(100):
            k_mid = (k_low + k_high) / 2
            if sa.is_stable(k_mid):
                k_low = k_mid
            else:
                k_high = k_mid
            if k_high - k_low < 1e-4:
                break

        if k_high < 999:
            return float(k_high)
        return None

    def _find_ultimate_period(self, Ku: float) -> float:
        """Find the oscillation period at ultimate gain."""
        poles = np.roots(np.polyadd(self.plant.den, Ku * self.plant.num))
        imag_poles = poles[np.abs(poles.real) < 1e-6]
        if len(imag_poles) > 0:
            omega = np.max(np.abs(imag_poles.imag))
            if omega > 0:
                return 2 * np.pi / omega
        return 1.0

    # ------------------------------------------------------------------
    # PID controller transfer function
    # ------------------------------------------------------------------

    @staticmethod
    def pid_transfer_function(params: PIDParams) -> TransferFunction:
        """Create a PID controller transfer function.

        C(s) = Kp + Ki/s + Kd*s/(Tf*s + 1)

        Parameters
        ----------
        params : PIDParams

        Returns
        -------
        TransferFunction
        """
        Kp, Ki, Kd, Tf = params.Kp, params.Ki, params.Kd, params.Tf

        # PID with filtered derivative
        # C(s) = (Kd*s^2 + Kp*s + Ki) / (s*(Tf*s + 1))
        num = [Kd, Kp, Ki]
        den = [Tf, 1.0, 0.0]
        return TransferFunction(num, den, name="PID")

    # ------------------------------------------------------------------
    # Lead compensator
    # ------------------------------------------------------------------

    def design_lead(
        self,
        phase_boost_deg: float,
        omega_cross: float,
        alpha: float | None = None,
    ) -> TransferFunction:
        """Design a lead compensator.

        C(s) = K * (s + z) / (s + p)  where z < p (zero is closer to origin)

        Parameters
        ----------
        phase_boost_deg : float
            Desired phase boost at crossover frequency (degrees).
        omega_cross : float
            Desired crossover frequency (rad/s).
        alpha : float, optional
            Ratio z/p. If None, computed from phase boost.

        Returns
        -------
        TransferFunction
        """
        phase_boost_rad = np.radians(phase_boost_deg)

        if alpha is None:
            # Compute alpha from phase boost
            # Max phase boost: sin(phi_m) = (alpha - 1)/(alpha + 1)
            sin_phi = np.sin(phase_boost_rad)
            alpha = (1 + sin_phi) / (1 - sin_phi)
            alpha = max(alpha, 1.01)

        # Place zero and pole
        z = omega_cross / np.sqrt(alpha)
        p = omega_cross * np.sqrt(alpha)

        # Gain to set |C(jw)*G(jw)| = 1 at omega_cross
        G_jw = self.plant.eval_freq(np.array([omega_cross]))[0]
        C_mag_target = 1.0 / abs(G_jw)

        # |C(jw)| = K * |jw + z| / |jw + p|
        num_mag = np.sqrt(omega_cross**2 + z**2)
        den_mag = np.sqrt(omega_cross**2 + p**2)
        K = C_mag_target * den_mag / num_mag

        return TransferFunction([K, K * z], [1.0, p], name="Lead")

    # ------------------------------------------------------------------
    # Lag compensator
    # ------------------------------------------------------------------

    def design_lag(
        self,
        low_freq_gain_boost: float,
        omega_cross: float,
        separation_factor: float = 10.0,
    ) -> TransferFunction:
        """Design a lag compensator.

        C(s) = K * (s + z) / (s + p)  where z > p (zero is farther from origin)

        Parameters
        ----------
        low_freq_gain_boost : float
            Desired gain increase at low frequencies (linear scale).
        omega_cross : float
            Crossover frequency (rad/s).
        separation_factor : float
            Ratio z/p for pole-zero separation.

        Returns
        -------
        TransferFunction
        """
        # Place pole and zero well below crossover
        p = omega_cross / (separation_factor * 10)
        z = p * separation_factor

        # K to maintain crossover frequency
        G_jw = self.plant.eval_freq(np.array([omega_cross]))[0]
        C_mag_target = 1.0 / abs(G_jw)

        num_mag = np.sqrt(omega_cross**2 + z**2)
        den_mag = np.sqrt(omega_cross**2 + p**2)
        K = C_mag_target * den_mag / num_mag

        return TransferFunction([K, K * z], [1.0, p], name="Lag")

    # ------------------------------------------------------------------
    # Lead-Lag compensator
    # ------------------------------------------------------------------

    def design_lead_lag(
        self,
        phase_boost_deg: float,
        omega_cross: float,
        low_freq_boost: float = 10.0,
    ) -> tuple[TransferFunction, TransferFunction]:
        """Design combined lead-lag compensator.

        Parameters
        ----------
        phase_boost_deg : float
            Phase boost from lead portion.
        omega_cross : float
            Crossover frequency.
        low_freq_boost : float
            Low-frequency gain boost from lag portion.

        Returns
        -------
        tuple[TransferFunction, TransferFunction]
            (lead_compensator, lag_compensator)
        """
        lead = self.design_lead(phase_boost_deg, omega_cross)
        lag = self.design_lag(low_freq_boost, omega_cross)
        return lead, lag

    # ------------------------------------------------------------------
    # Root locus based design
    # ------------------------------------------------------------------

    def design_from_poles(
        self,
        desired_poles: list[complex],
    ) -> TransferFunction:
        """Design a controller to place closed-loop poles at desired locations.

        Uses pole placement for a proper system.

        Parameters
        ----------
        desired_poles : list[complex]
            Desired closed-loop pole locations.

        Returns
        -------
        TransferFunction
            Controller transfer function.
        """
        desired_poles = np.array(desired_poles, dtype=complex)
        desired_char = np.poly(desired_poles)

        # Current characteristic polynomial: den(s)
        # Need controller C(s) such that: den(s) + C(s)*num(s) = desired_char(s)
        # C(s)*num(s) = desired_char(s) - den(s)
        target_num = np.polyadd(desired_char, -self.plant.den)

        # Pad to same length
        max_len = max(len(target_num), len(self.plant.num))
        target_num_padded = np.zeros(max_len)
        target_num_padded[max_len - len(target_num):] = target_num
        num_padded = np.zeros(max_len)
        num_padded[max_len - len(self.plant.num):] = self.plant.num

        # Controller numerator = target_num / plant_num (polynomial division)
        # Use deconvolution
        controller_num, remainder = np.polydiv(target_num_padded, num_padded)

        # Remove leading zeros
        controller_num = np.trim_zeros(controller_num, 'f')
        if len(controller_num) == 0:
            controller_num = np.array([1.0])

        # Controller denominator: use same order for properness
        controller_den = np.ones(len(controller_num))

        return TransferFunction(controller_num, controller_den, name="C")
