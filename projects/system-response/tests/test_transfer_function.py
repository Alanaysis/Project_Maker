"""Tests for TransferFunction."""

import numpy as np
import pytest

from src.transfer_function import TransferFunction


class TestTransferFunction:
    """Test basic transfer function operations."""

    def test_creation(self):
        tf = TransferFunction([1], [1, 1], name="first_order")
        assert tf.order == 1
        assert tf.name == "first_order"

    def test_normalization(self):
        tf = TransferFunction([2], [2, 2])
        np.testing.assert_allclose(tf.num, [1.0])
        np.testing.assert_allclose(tf.den, [1.0, 1.0])

    def test_dc_gain(self):
        tf = TransferFunction([5], [1, 1])
        assert abs(tf.dc_gain - 5.0) < 1e-10

    def test_poles(self):
        tf = TransferFunction([1], [1, 3, 2])  # (s+1)(s+2)
        poles = tf.poles()
        poles_sorted = np.sort(poles.real)
        np.testing.assert_allclose(poles_sorted, [-2, -1], atol=1e-10)

    def test_zeros(self):
        tf = TransferFunction([1, 2], [1, 1])  # zero at s=-2
        zeros = tf.zeros()
        np.testing.assert_allclose(zeros.real, [-2], atol=1e-10)

    def test_eval(self):
        # G(s) = 1/(s+1), G(0) = 1
        tf = TransferFunction([1], [1, 1])
        val = tf(0)
        assert abs(val - 1.0) < 1e-10

    def test_eval_freq(self):
        # G(s) = 1/(s+1), G(j*1) = 1/(j+1) = 0.5 - 0.5j
        tf = TransferFunction([1], [1, 1])
        val = tf.eval_freq(np.array([1.0]))
        expected = 1.0 / (1j + 1)
        assert abs(val[0] - expected) < 1e-10

    def test_is_proper(self):
        proper = TransferFunction([1], [1, 1])
        assert proper.is_proper

        # Strictly proper
        strict = TransferFunction([1], [1, 1, 1])
        assert strict.is_proper

    def test_series(self):
        g1 = TransferFunction([1], [1, 1], name="G1")
        g2 = TransferFunction([1], [1, 2], name="G2")
        g_series = g1 * g2
        assert g_series.order == 2

    def test_parallel(self):
        g1 = TransferFunction([1], [1, 1], name="G1")
        g2 = TransferFunction([1], [1, 2], name="G2")
        g_parallel = g1 + g2
        # DC gain should be sum of DC gains
        np.testing.assert_allclose(g_parallel.dc_gain, g1.dc_gain + g2.dc_gain, atol=1e-10)

    def test_scalar_multiply(self):
        tf = TransferFunction([1], [1, 1])
        scaled = 3.0 * tf
        np.testing.assert_allclose(scaled.dc_gain, 3.0, atol=1e-10)

    def test_feedback_unity(self):
        # G/(1+G) with G=1/(s+1)
        g = TransferFunction([1], [1, 1])
        cl = g.feedback()
        # Closed-loop: 1/(s+2), DC = 0.5
        np.testing.assert_allclose(cl.dc_gain, 0.5, atol=1e-10)

    def test_from_poles_zeros(self):
        tf = TransferFunction.from_poles_zeros(poles=[-1, -2], zeros=[-3], gain=2)
        poles = np.sort(tf.poles().real)
        np.testing.assert_allclose(poles, [-2, -1], atol=1e-10)
        assert abs(tf.dc_gain - 2 * 3 / (1 * 2)) < 1e-10

    def test_first_order_factory(self):
        tf = TransferFunction.first_order(gain=5, tau=2)
        assert tf.order == 1
        np.testing.assert_allclose(tf.dc_gain, 5.0, atol=1e-10)

    def test_second_order_factory(self):
        tf = TransferFunction.second_order(gain=1, omega_n=2, zeta=0.5)
        assert tf.order == 2

    def test_integrator(self):
        tf = TransferFunction.integrator()
        assert tf.order == 1
        # DC gain should be infinite
        assert abs(tf.den[-1]) < 1e-15

    def test_to_scipy(self):
        tf = TransferFunction([1, 2], [1, 3, 2])
        num, den = tf.to_scipy()
        assert isinstance(num, list)
        assert isinstance(den, list)

    def test_repr(self):
        tf = TransferFunction([1], [1, 1], name="G")
        r = repr(tf)
        assert "TransferFunction" in r
        assert "G" in r
