"""Tests for circuit composition (adders)."""

import unittest
from src.circuits import (
    HalfAdder,
    FullAdder,
    add_n_bit,
    build_n_bit_adder,
)
from src.circuits import Wire


class TestHalfAdder(unittest.TestCase):
    """Test half adder circuit."""

    def test_all_inputs(self):
        ha = HalfAdder()
        test_cases = [
            (0, 0, 0, 0),
            (0, 1, 1, 0),
            (1, 0, 1, 0),
            (1, 1, 0, 1),
        ]
        for a, b, exp_sum, exp_carry in test_cases:
            w_a = Wire("A", a)
            w_b = Wire("B", b)
            ha.set_inputs(w_a, w_b)
            ha.evaluate()
            s, c = ha.get_result()
            self.assertEqual(s, exp_sum)
            self.assertEqual(c, exp_carry)

    def test_sum_formula(self):
        """Sum should equal A XOR B."""
        ha = HalfAdder()
        for a in [0, 1]:
            for b in [0, 1]:
                w_a = Wire("A", a)
                w_b = Wire("B", b)
                ha.set_inputs(w_a, w_b)
                ha.evaluate()
                s, _ = ha.get_result()
                from src.gates import XOR
                self.assertEqual(s, XOR(a, b))

    def test_carry_formula(self):
        """Carry should equal A AND B."""
        ha = HalfAdder()
        for a in [0, 1]:
            for b in [0, 1]:
                w_a = Wire("A", a)
                w_b = Wire("B", b)
                ha.set_inputs(w_a, w_b)
                ha.evaluate()
                _, c = ha.get_result()
                from src.gates import AND
                self.assertEqual(c, AND(a, b))


class TestFullAdder(unittest.TestCase):
    """Test full adder circuit."""

    def test_all_inputs(self):
        fa = FullAdder()
        test_cases = [
            (0, 0, 0, 0, 0),
            (0, 1, 0, 1, 0),
            (1, 0, 0, 1, 0),
            (1, 1, 0, 0, 1),
            (0, 0, 1, 1, 0),
            (0, 1, 1, 0, 1),
            (1, 0, 1, 0, 1),
            (1, 1, 1, 1, 1),
        ]
        for a, b, cin, exp_sum, exp_cout in test_cases:
            w_a = Wire("A", a)
            w_b = Wire("B", b)
            w_cin = Wire("Cin", cin)
            fa.set_inputs(w_a, w_b, w_cin)
            fa.evaluate()
            s, cout = fa.get_result()
            self.assertEqual(s, exp_sum)
            self.assertEqual(cout, exp_cout)

    def test_addition_property(self):
        """Sum + 2*Cout should equal A + B + Cin (mod 2)."""
        fa = FullAdder()
        for a in [0, 1]:
            for b in [0, 1]:
                for cin in [0, 1]:
                    w_a = Wire("A", a)
                    w_b = Wire("B", b)
                    w_cin = Wire("Cin", cin)
                    fa.set_inputs(w_a, w_b, w_cin)
                    fa.evaluate()
                    s, cout = fa.get_result()
                    total = a + b + cin
                    self.assertEqual(s + 2 * cout, total)


class TestNBitAdder(unittest.TestCase):
    """Test n-bit ripple carry adder."""

    def test_4bit_all_zero(self):
        result, carry = add_n_bit(0, 0, 4)
        self.assertEqual(result, 0)
        self.assertEqual(carry, 0)

    def test_4bit_overflow(self):
        result, carry = add_n_bit(15, 1, 4)
        self.assertEqual(result, 0)
        self.assertEqual(carry, 1)

    def test_4bit_mixed(self):
        result, carry = add_n_bit(5, 3, 4)
        self.assertEqual(result, 8)
        self.assertEqual(carry, 0)

    def test_4bit_comprehensive(self):
        """Verify all 4-bit addition results."""
        n = 4
        for a in range(1 << n):
            for b in range(1 << n):
                expected = (a + b) & ((1 << n) - 1)
                expected_carry = 1 if (a + b) >= (1 << n) else 0
                result, carry = add_n_bit(a, b, n)
                self.assertEqual(result, expected)
                self.assertEqual(carry, expected_carry)

    def test_2bit_addition(self):
        """Test 2-bit adder."""
        n = 2
        self.assertEqual(add_n_bit(1, 1, n), (0, 0))
        self.assertEqual(add_n_bit(3, 0, n), (3, 0))
        self.assertEqual(add_n_bit(3, 1, n), (0, 1))

    def test_build_n_bit_adder(self):
        adders = build_n_bit_adder(4)
        self.assertEqual(len(adders), 4)
        for adder in adders:
            self.assertIsInstance(adder, FullAdder)


if __name__ == "__main__":
    unittest.main()
