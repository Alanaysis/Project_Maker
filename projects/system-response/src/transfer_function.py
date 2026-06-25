"""Transfer function representation for linear time-invariant systems."""

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np
from numpy.polynomial import polynomial as P


@dataclass
class TransferFunction:
    r"""Represents a continuous-time transfer function G(s) = num(s) / den(s).

    Coefficients are stored in descending power order (scipy convention):
        num = [b_m, b_{m-1}, ..., b_0]  ->  b_m s^m + ... + b_0
        den = [a_n, a_{n-1}, ..., a_0]  ->  a_n s^n + ... + a_0

    Parameters
    ----------
    num : array-like
        Numerator coefficients in descending power order.
    den : array-like
        Denominator coefficients in descending power order.
    name : str, optional
        Label for this transfer function.
    """

    num: np.ndarray
    den: np.ndarray
    name: str = "G"

    def __post_init__(self) -> None:
        self.num = np.atleast_1d(np.asarray(self.num, dtype=float))
        self.den = np.atleast_1d(np.asarray(self.den, dtype=float))
        # Normalise so leading denominator coefficient is 1
        lead = self.den[0]
        if lead != 0:
            self.num = self.num / lead
            self.den = self.den / lead

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def order(self) -> int:
        """Order of the system (degree of denominator)."""
        return len(self.den) - 1

    @property
    def num_order(self) -> int:
        """Degree of the numerator."""
        return len(self.num) - 1

    @property
    def is_proper(self) -> bool:
        """True if the system is proper (num order <= den order)."""
        return self.num_order <= self.order

    @property
    def dc_gain(self) -> float:
        """DC gain G(0)."""
        return float(self.num[-1] / self.den[-1])

    # ------------------------------------------------------------------
    # Poles / Zeros
    # ------------------------------------------------------------------

    def poles(self) -> np.ndarray:
        """Return the poles of the transfer function."""
        return np.roots(self.den)

    def zeros(self) -> np.ndarray:
        """Return the zeros of the transfer function."""
        if self.num_order == 0 and self.num[0] == 0:
            return np.array([])
        return np.roots(self.num)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def __call__(self, s: complex | np.ndarray) -> complex | np.ndarray:
        """Evaluate G(s) at the given complex frequency."""
        s = np.asarray(s, dtype=complex)
        num_val = np.polyval(self.num, s)
        den_val = np.polyval(self.den, s)
        return num_val / den_val

    def eval_freq(self, omega: np.ndarray) -> np.ndarray:
        """Evaluate G(jw) for a real frequency array omega.

        Parameters
        ----------
        omega : array-like
            Frequencies in rad/s.

        Returns
        -------
        np.ndarray
            Complex frequency response values.
        """
        omega = np.asarray(omega, dtype=float)
        s = 1j * omega
        return self(s)

    # ------------------------------------------------------------------
    # Arithmetic
    # ------------------------------------------------------------------

    def __mul__(self, other: TransferFunction) -> TransferFunction:
        """Series interconnection: G1 * G2."""
        if not isinstance(other, TransferFunction):
            return NotImplemented
        num = np.polymul(self.num, other.num)
        den = np.polymul(self.den, other.den)
        return TransferFunction(num, den, name=f"({self.name}*{other.name})")

    def __rmul__(self, scalar: float) -> TransferFunction:
        """Multiply by a scalar gain."""
        if isinstance(scalar, (int, float)):
            return TransferFunction(
                self.num * scalar, self.den, name=f"({scalar}*{self.name})"
            )
        return NotImplemented

    def __add__(self, other: TransferFunction) -> TransferFunction:
        """Parallel interconnection: G1 + G2."""
        if not isinstance(other, TransferFunction):
            return NotImplemented
        num = np.polyadd(
            np.polymul(self.num, other.den),
            np.polymul(other.num, self.den),
        )
        den = np.polymul(self.den, other.den)
        return TransferFunction(num, den, name=f"({self.name}+{other.name})")

    def __neg__(self) -> TransferFunction:
        return TransferFunction(-self.num, self.den, name=f"-{self.name}")

    def feedback(self, other: TransferFunction | None = None, sign: int = 1) -> TransferFunction:
        """Closed-loop feedback: G / (1 + sign * G * H).

        Parameters
        ----------
        other : TransferFunction, optional
            Feedback transfer function H(s). Defaults to unity (1).
        sign : int
            -1 for positive feedback, +1 for negative feedback (default).
            Convention: error = R - sign * Y*H, so default sign=1 gives
            standard negative feedback: G/(1+G*H).
        """
        if other is None:
            other = TransferFunction([1], [1], name="1")
        num_loop = np.polymul(self.num, other.num)
        den_loop = np.polymul(self.den, other.den)
        den_closed = np.polyadd(den_loop, sign * num_loop)
        return TransferFunction(
            np.polymul(self.num, other.den),
            den_closed,
            name=f"({self.name}/(1+{self.name}*{other.name}))",
        )

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"TransferFunction(name='{self.name}', num={self.num}, den={self.den})"

    def to_scipy(self):
        """Return (num, den) tuple compatible with scipy.signal."""
        return self.num.tolist(), self.den.tolist()

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @classmethod
    def from_poles_zeros(cls, poles: list, zeros: list, gain: float = 1.0, name: str = "G") -> TransferFunction:
        """Create a transfer function from poles, zeros and gain.

        G(s) = gain * (s - z_1) * ... * (s - z_m) / ((s - p_1) * ... * (s - p_n))
        """
        num = gain * np.poly(zeros) if zeros else np.array([gain])
        den = np.poly(poles) if poles else np.array([1.0])
        return cls(num, den, name=name)

    @classmethod
    def first_order(cls, gain: float = 1.0, tau: float = 1.0, name: str = "G1") -> TransferFunction:
        """First-order system: K / (tau*s + 1)."""
        return cls([gain], [tau, 1.0], name=name)

    @classmethod
    def second_order(cls, gain: float = 1.0, omega_n: float = 1.0, zeta: float = 0.5, name: str = "G2") -> TransferFunction:
        """Second-order system: K * omega_n^2 / (s^2 + 2*zeta*omega_n*s + omega_n^2)."""
        num = [gain * omega_n**2]
        den = [1.0, 2 * zeta * omega_n, omega_n**2]
        return cls(num, den, name=name)

    @classmethod
    def integrator(cls, gain: float = 1.0, name: str = "1/s") -> TransferFunction:
        """Integrator: K / s."""
        return cls([gain], [1.0, 0.0], name=name)

    @classmethod
    def delay(cls, T: float, order: int = 3, name: str = "delay") -> TransferFunction:
        """Pade approximation of a time delay e^{-sT}.

        Parameters
        ----------
        T : float
            Delay time in seconds.
        order : int
            Order of the Pade approximation.
        """
        from math import factorial

        a = np.zeros(order + 1)
        for k in range(order + 1):
            a[k] = (
                factorial(2 * order - k) * factorial(order)
                / (factorial(2 * order) * factorial(k) * factorial(order - k))
            )
        # Numerator: sum a_k (-sT)^k -> coefficients of s^k get (-T)^k * a_k
        # Denominator: sum a_k (sT)^k -> coefficients of s^k get T^k * a_k
        # Descending power order
        num_coeffs = np.array([a[k] * (-T) ** k for k in range(order + 1)])[::-1]
        den_coeffs = np.array([a[k] * T ** k for k in range(order + 1)])[::-1]
        return cls(num_coeffs, den_coeffs, name=name)


