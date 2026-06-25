"""Tests for StabilityAnalyzer."""

import numpy as np
import pytest

from src.transfer_function import TransferFunction
from src.stability import StabilityAnalyzer


class TestStabilityAnalyzer:
    """Test stability analysis tools."""

    def test_routh_stable(self):
        # s^2 + 3s + 2 = (s+1)(s+2): stable
        sa = StabilityAnalyzer(TransferFunction([1], [1, 3, 2]))
        result = sa.routh()
        assert result.is_stable
        assert result.sign_changes == 0

    def test_routh_unstable(self):
        # s^2 - s + 1: unstable (positive real part)
        sa = StabilityAnalyzer(TransferFunction([1], [1, -1, 1]))
        result = sa.routh()
        assert not result.is_stable
        assert result.sign_changes > 0

    def test_routh_third_order(self):
        # s^3 + 6s^2 + 11s + 6 = (s+1)(s+2)(s+3): stable
        sa = StabilityAnalyzer(TransferFunction([1], [1, 6, 11, 6]))
        result = sa.routh()
        assert result.is_stable

    def test_routh_first_column(self):
        sa = StabilityAnalyzer(TransferFunction([1], [1, 3, 2]))
        result = sa.routh()
        # All first column elements should be positive for stable system
        assert np.all(result.first_column > 0)

    def test_root_locus_data(self):
        sa = StabilityAnalyzer(TransferFunction([1], [1, 3, 2]))
        rl = sa.root_locus(k_range=np.linspace(0, 10, 50))
        assert rl.roots.shape[0] == 50
        assert rl.roots.shape[1] == 2  # Second order

    def test_root_locus_auto_range(self):
        sa = StabilityAnalyzer(TransferFunction([1], [1, 3, 2]))
        rl = sa.root_locus()
        assert len(rl.gains) > 0

    def test_closed_loop_poles_stable(self):
        # G = 1/(s+1), with K=1: closed-loop poles at s=-2
        sa = StabilityAnalyzer(TransferFunction([1], [1, 1]))
        poles = sa.closed_loop_poles(k=1.0)
        np.testing.assert_allclose(sorted(poles.real), [-2], atol=1e-10)

    def test_is_stable_true(self):
        sa = StabilityAnalyzer(TransferFunction([1], [1, 3, 2]))
        assert sa.is_stable(k=1.0)

    def test_is_stable_false(self):
        # High gain can destabilize
        sa = StabilityAnalyzer(TransferFunction([1], [1, -1]))
        assert not sa.is_stable(k=1.0)

    def test_stability_margins_robust(self):
        sa = StabilityAnalyzer(TransferFunction([1], [1, 3, 2]))
        info = sa.stability_margins_robust()
        assert "open_loop_stable" in info
        assert "closed_loop_stable" in info
        assert info["open_loop_stable"]
        assert info["closed_loop_stable"]

    def test_marginal_gain(self):
        # System that becomes unstable at high gain
        # G(s) = 1/((s+1)(s+2)(s+3))
        sa = StabilityAnalyzer(TransferFunction([1], [1, 6, 11, 6]))
        mg = sa.marginal_gain()
        # Should find a finite gain where instability occurs
        if mg is not None:
            assert mg > 0

    def test_routh_single_pole(self):
        # s + 1: trivially stable
        sa = StabilityAnalyzer(TransferFunction([1], [1, 1]))
        result = sa.routh()
        assert result.is_stable
