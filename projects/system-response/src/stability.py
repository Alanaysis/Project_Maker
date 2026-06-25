"""Stability analysis: Routh criterion and root locus."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from numpy.polynomial import polynomial as P

from .transfer_function import TransferFunction


@dataclass
class RouthTable:
    """Result of a Routh stability analysis.

    Attributes
    ----------
    table : np.ndarray
        The Routh table as a 2D array.
    is_stable : bool
        True if all roots have negative real parts.
    sign_changes : int
        Number of sign changes in the first column (number of RHP poles).
    first_column : np.ndarray
        First column of the Routh table.
    """

    table: np.ndarray
    is_stable: bool
    sign_changes: int
    first_column: np.ndarray


@dataclass
class RootLocusData:
    """Root locus plot data.

    Attributes
    ----------
    gains : np.ndarray
        Array of gain values K.
    roots : np.ndarray
        Array of shape (n_gains, n_poles) containing closed-loop poles for each gain.
    """

    gains: np.ndarray
    roots: np.ndarray


class StabilityAnalyzer:
    """Stability analysis tools.

    Parameters
    ----------
    tf : TransferFunction
        The open-loop transfer function.
    """

    def __init__(self, tf: TransferFunction) -> None:
        self.tf = tf

    # ------------------------------------------------------------------
    # Routh criterion
    # ------------------------------------------------------------------

    def routh(self, den: np.ndarray | None = None) -> RouthTable:
        """Build the Routh table for the given characteristic polynomial.

        Parameters
        ----------
        den : array-like, optional
            Denominator coefficients (descending powers of s).
            If None, uses self.tf.den.

        Returns
        -------
        RouthTable
        """
        if den is None:
            den = self.tf.den
        den = np.asarray(den, dtype=float)

        n = len(den)
        if n < 2:
            return RouthTable(
                table=np.array([[den[0]]]),
                is_stable=True,
                sign_changes=0,
                first_column=np.array([den[0]]),
            )

        # Number of rows = order + 1
        rows = n
        cols = (n + 1) // 2
        table = np.zeros((rows, cols))

        # Fill first two rows
        row0 = den[0::2]  # even-indexed coefficients
        row1 = den[1::2]  # odd-indexed coefficients
        table[0, :len(row0)] = row0
        table[1, :len(row1)] = row1

        # Fill remaining rows
        for i in range(2, rows):
            if table[i - 1, 0] == 0:
                # Special case: entire row is zero -> auxiliary polynomial
                # Replace with derivative of previous row
                # Find the row above that has non-zero first element
                prev_row = table[i - 1]
                if np.all(prev_row == 0):
                    # Auxiliary polynomial from row i-2
                    aux_order = rows - i
                    aux_coeffs = table[i - 2]
                    # Derivative: multiply by descending powers
                    deriv = np.zeros_like(aux_coeffs)
                    for j in range(len(aux_coeffs)):
                        power = len(aux_coeffs) - 1 - j
                        if power > 0:
                            deriv[j] = aux_coeffs[j] * power
                    table[i - 1, :len(deriv)] = deriv
                else:
                    # Replace zero with small epsilon to continue
                    table[i - 1, 0] = 1e-10

            for j in range(cols):
                a = table[i - 1, 0]
                if a == 0:
                    a = 1e-10
                c1 = table[i - 2, 0]
                c2 = table[i - 2, j + 1] if j + 1 < cols else 0
                d1 = table[i - 1, j + 1] if j + 1 < cols else 0
                table[i, j] = (table[i - 1, 0] * c2 - c1 * d1) / a

        # First column analysis
        first_col = table[:, 0]
        sign_changes = 0
        for i in range(1, len(first_col)):
            if first_col[i - 1] * first_col[i] < 0:
                sign_changes += 1

        return RouthTable(
            table=table,
            is_stable=(sign_changes == 0),
            sign_changes=sign_changes,
            first_column=first_col,
        )

    # ------------------------------------------------------------------
    # Root locus
    # ------------------------------------------------------------------

    def root_locus(self, k_range: np.ndarray | None = None, n_points: int = 500) -> RootLocusData:
        """Compute root locus data.

        Parameters
        ----------
        k_range : array-like, optional
            Gain values. If None, auto-generated.
        n_points : int
            Number of gain values.

        Returns
        -------
        RootLocusData
        """
        poles = self.tf.poles()
        zeros = self.tf.zeros()

        if k_range is None:
            # Auto range from 0 to a reasonable max
            max_gain = self._estimate_max_gain(poles, zeros)
            k_range = np.linspace(0, max_gain, n_points)

        # For each gain K, compute closed-loop poles: 1 + K*N(s)/D(s) = 0
        # -> D(s) + K*N(s) = 0
        roots_list = []
        for k in k_range:
            char_poly = np.polyadd(self.tf.den, k * self.tf.num)
            r = np.roots(char_poly)
            # Sort by real part for consistent tracking
            r = r[np.argsort(r.real)]
            roots_list.append(r)

        return RootLocusData(
            gains=np.asarray(k_range),
            roots=np.array(roots_list),
        )

    def _estimate_max_gain(self, poles: np.ndarray, zeros: np.ndarray) -> float:
        """Estimate maximum gain for root locus."""
        # Use a heuristic based on pole/zero locations
        max_pole = np.max(np.abs(poles)) if len(poles) > 0 else 1
        max_zero = np.max(np.abs(zeros)) if len(zeros) > 0 else 0
        return max(10 * max_pole, 10 * max_zero, 100)

    # ------------------------------------------------------------------
    # Marginal stability (gain at imaginary axis crossing)
    # ------------------------------------------------------------------

    def marginal_gain(self) -> float | None:
        """Find the gain K at which closed-loop poles cross the imaginary axis.

        Uses the Routh table to find the critical gain.

        Returns
        -------
        float or None
            The critical gain, or None if the system is unconditionally stable.
        """
        den = self.tf.den
        num = self.tf.num
        n = len(den)

        # Build Routh table symbolically is complex; use numerical search
        # Binary search on gain to find where poles become unstable
        k_low, k_high = 0, 1000
        for _ in range(100):
            k_mid = (k_low + k_high) / 2
            char_poly = np.polyadd(den, k_mid * num)
            poles = np.roots(char_poly)
            if np.any(poles.real > 0):
                k_high = k_mid
            else:
                k_low = k_mid
            if k_high - k_low < 1e-6:
                break

        if k_high < 999:
            return float(k_high)
        return None

    # ------------------------------------------------------------------
    # Pole analysis
    # ------------------------------------------------------------------

    def closed_loop_poles(self, k: float = 1.0) -> np.ndarray:
        """Compute closed-loop poles for unity feedback with gain K.

        Parameters
        ----------
        k : float
            Loop gain.

        Returns
        -------
        np.ndarray
            Closed-loop pole locations.
        """
        char_poly = np.polyadd(self.tf.den, k * self.tf.num)
        return np.roots(char_poly)

    def is_stable(self, k: float = 1.0) -> bool:
        """Check if closed-loop system is stable for given gain."""
        poles = self.closed_loop_poles(k)
        return bool(np.all(poles.real < 0))

    def stability_margins_robust(self) -> dict:
        """Compute robust stability information.

        Returns
        -------
        dict
            Keys: 'open_loop_stable', 'closed_loop_stable', 'poles', 'marginal_gain'.
        """
        ol_poles = self.tf.poles()
        cl_poles = self.closed_loop_poles(k=1.0)
        mg = self.marginal_gain()
        return {
            "open_loop_stable": bool(np.all(ol_poles.real < 0)),
            "closed_loop_stable": bool(np.all(cl_poles.real < 0)),
            "open_loop_poles": ol_poles,
            "closed_loop_poles": cl_poles,
            "marginal_gain": mg,
        }
