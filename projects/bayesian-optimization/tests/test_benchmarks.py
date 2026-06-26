"""Tests for benchmark functions."""

import numpy as np
import pytest
from src.benchmarks import (
    branin, branin_bounds, branin_true_minimum,
    hartmann, hartmann_bounds, hartmann_true_minimum,
    booth, booth_bounds,
    rastrigin, rastrigin_bounds,
    ackley, ackley_bounds,
    get_benchmark,
)


class TestBranin:
    """Test suite for Branin benchmark function."""

    def test_branin_at_minimum(self):
        """Branin should be near minimum at known minimizers."""
        f_min, x_opt = branin_true_minimum()
        for x in x_opt:
            val = branin(x)
            assert abs(val - f_min) < 0.01, f"Branin at {x} should be ~{f_min}"

    def test_branin_bounds(self):
        """Branin bounds should be 2D."""
        bounds = branin_bounds()
        assert bounds.shape == (2, 2)
        assert bounds[0, 0] == -5.0
        assert bounds[0, 1] == 10.0

    def test_branin_output_type(self):
        """Branin should return a float."""
        result = branin(np.array([0.0, 0.0]))
        assert isinstance(result, float)

    def test_branin_continuous(self):
        """Branin should be continuous (small input change -> small output change)."""
        x1 = np.array([1.0, 2.0])
        x2 = np.array([1.0 + 1e-6, 2.0 + 1e-6])
        assert abs(branin(x1) - branin(x2)) < 1e-3


class TestHartmann:
    """Test suite for Hartmann benchmark function."""

    def test_hartmann_6d(self):
        """Hartmann 6D should return finite value."""
        x = np.array([20.169, 15.001, 47.687, 27.533, 31.165, 65.730])
        val = hartmann(x)
        assert np.isfinite(val)
        assert val < 0  # Should be negative (minimization target)

    def test_hartmann_bounds(self):
        """Hartmann bounds should be [0, 1] for each dimension."""
        bounds = hartmann_bounds(6)
        assert bounds.shape == (6, 2)
        assert np.all(bounds[:, 0] == 0.0)
        assert np.all(bounds[:, 1] == 1.0)

    def test_hartmann_positive_input(self):
        """Hartmann expects inputs in [0, 100]."""
        x = np.array([50.0] * 6)  # center of [0, 100]
        val = hartmann(x)
        assert np.isfinite(val)

    def test_hartmann_2d(self):
        """Hartmann should work for d=2."""
        x = np.array([20.169, 15.001])
        # For d=2, use the 2D Hartmann function (different coefficients)
        val = hartmann(x, n=2)
        assert np.isfinite(val)


class TestBooth:
    """Test suite for Booth benchmark function."""

    def test_booth_at_minimum(self):
        """Booth should be 0 at its minimum."""
        val = booth(np.array([1.0, 3.0]))
        assert abs(val) < 1e-6

    def test_booth_bounds(self):
        """Booth bounds should be [-10, 10] for each dimension."""
        bounds = booth_bounds()
        assert bounds.shape == (2, 2)
        assert np.all(bounds[:, 0] == -10.0)
        assert np.all(bounds[:, 1] == 10.0)


class TestRastrigin:
    """Test suite for Rastrigin benchmark function."""

    def test_rastrigin_at_minimum(self):
        """Rastrigin should be 0 at origin."""
        val = rastrigin(np.zeros(2))
        assert abs(val) < 1e-6

    def test_rastrigin_multimodal(self):
        """Rastrigin should have multiple local minima."""
        val0 = rastrigin(np.zeros(2))
        val1 = rastrigin(np.array([1.0, 0.0]))
        val2 = rastrigin(np.array([2.0, 2.0]))
        assert val1 > val0 or val2 > val0  # Should not always be 0

    def test_rastrigin_bounds(self):
        """Rastrigin bounds should be [-5.12, 5.12]."""
        bounds = rastrigin_bounds(3)
        assert bounds.shape == (3, 2)
        assert np.allclose(bounds[:, 0], -5.12)
        assert np.allclose(bounds[:, 1], 5.12)


class TestAckley:
    """Test suite for Ackley benchmark function."""

    def test_ackley_at_minimum(self):
        """Ackley should be 0 at origin."""
        val = ackley(np.zeros(2))
        assert abs(val) < 1e-6

    def test_ackley_bounds(self):
        """Ackley bounds should be [-32.768, 32.768]."""
        bounds = ackley_bounds(3)
        assert bounds.shape == (3, 2)
        assert np.allclose(bounds[:, 0], -32.768)
        assert np.allclose(bounds[:, 1], 32.768)


class TestGetBenchmark:
    """Test benchmark factory function."""

    def test_get_branin(self):
        """Should get Branin benchmark."""
        fn, bounds, min_val, min_pt = get_benchmark("branin")
        assert callable(fn)
        assert bounds.shape == (2, 2)
        assert min_val == pytest.approx(0.397887, abs=0.001)

    def test_get_hartmann(self):
        """Should get Hartmann benchmark."""
        fn, bounds, min_val, min_pt = get_benchmark("hartmann", d=6)
        assert callable(fn)
        assert bounds.shape == (6, 2)
        assert min_val == pytest.approx(-3.322371, abs=0.001)

    def test_get_unknown_raises(self):
        """Should raise ValueError for unknown benchmark."""
        with pytest.raises(ValueError, match="Unknown benchmark"):
            get_benchmark("unknown_function")
