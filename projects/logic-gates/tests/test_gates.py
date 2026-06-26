"""Tests for basic logic gates."""

import unittest
from src.gates import AND, OR, NOT, NAND, NOR, XOR, XNOR


class TestAND(unittest.TestCase):
    """Test AND gate truth table."""

    def test_all_combinations(self):
        self.assertEqual(AND(0, 0), 0)
        self.assertEqual(AND(0, 1), 0)
        self.assertEqual(AND(1, 0), 0)
        self.assertEqual(AND(1, 1), 1)

    def test_idempotent(self):
        self.assertEqual(AND(1, 1), 1)
        self.assertEqual(AND(0, 0), 0)


class TestOR(unittest.TestCase):
    """Test OR gate truth table."""

    def test_all_combinations(self):
        self.assertEqual(OR(0, 0), 0)
        self.assertEqual(OR(0, 1), 1)
        self.assertEqual(OR(1, 0), 1)
        self.assertEqual(OR(1, 1), 1)


class TestNOT(unittest.TestCase):
    """Test NOT gate truth table."""

    def test_inversion(self):
        self.assertEqual(NOT(0), 1)
        self.assertEqual(NOT(1), 0)

    def test_double_not(self):
        self.assertEqual(NOT(NOT(0)), 0)
        self.assertEqual(NOT(NOT(1)), 1)


class TestNAND(unittest.TestCase):
    """Test NAND gate truth table."""

    def test_all_combinations(self):
        self.assertEqual(NAND(0, 0), 1)
        self.assertEqual(NAND(0, 1), 1)
        self.assertEqual(NAND(1, 0), 1)
        self.assertEqual(NAND(1, 1), 0)

    def test_is_not_and(self):
        """NAND should be the inverse of AND."""
        for a in [0, 1]:
            for b in [0, 1]:
                self.assertEqual(NAND(a, b), NOT(AND(a, b)))


class TestNOR(unittest.TestCase):
    """Test NOR gate truth table."""

    def test_all_combinations(self):
        self.assertEqual(NOR(0, 0), 1)
        self.assertEqual(NOR(0, 1), 0)
        self.assertEqual(NOR(1, 0), 0)
        self.assertEqual(NOR(1, 1), 0)

    def test_is_not_or(self):
        """NOR should be the inverse of OR."""
        for a in [0, 1]:
            for b in [0, 1]:
                self.assertEqual(NOR(a, b), NOT(OR(a, b)))


class TestXOR(unittest.TestCase):
    """Test XOR gate truth table."""

    def test_all_combinations(self):
        self.assertEqual(XOR(0, 0), 0)
        self.assertEqual(XOR(0, 1), 1)
        self.assertEqual(XOR(1, 0), 1)
        self.assertEqual(XOR(1, 1), 0)

    def test_different_inputs(self):
        """XOR should return 1 when inputs differ."""
        self.assertEqual(XOR(0, 1), 1)
        self.assertEqual(XOR(1, 0), 1)

    def test_same_inputs(self):
        """XOR should return 0 when inputs are same."""
        self.assertEqual(XOR(0, 0), 0)
        self.assertEqual(XOR(1, 1), 0)


class TestXNOR(unittest.TestCase):
    """Test XNOR gate truth table."""

    def test_all_combinations(self):
        self.assertEqual(XNOR(0, 0), 1)
        self.assertEqual(XNOR(0, 1), 0)
        self.assertEqual(XNOR(1, 0), 0)
        self.assertEqual(XNOR(1, 1), 1)

    def test_is_not_xor(self):
        """XNOR should be the inverse of XOR."""
        for a in [0, 1]:
            for b in [0, 1]:
                self.assertEqual(XNOR(a, b), NOT(XOR(a, b)))


if __name__ == "__main__":
    unittest.main()
