"""Tests for multi-bit operations."""

import unittest
from src.multi_bit import (
    bit_to_list,
    list_to_bit,
    bitwise_and,
    bitwise_or,
    bitwise_xor,
    bitwise_not,
    shift_left,
    shift_right,
)


class TestBitConversion(unittest.TestCase):
    """Test bit conversion utilities."""

    def test_bit_to_list(self):
        self.assertEqual(bit_to_list(5, 4), [1, 0, 1, 0])
        self.assertEqual(bit_to_list(0, 4), [0, 0, 0, 0])
        self.assertEqual(bit_to_list(15, 4), [1, 1, 1, 1])
        self.assertEqual(bit_to_list(1, 4), [0, 0, 0, 1])

    def test_list_to_bit(self):
        self.assertEqual(list_to_bit([1, 0, 1, 0]), 5)
        self.assertEqual(list_to_bit([0, 0, 0, 0]), 0)
        self.assertEqual(list_to_bit([1, 1, 1, 1]), 15)
        self.assertEqual(list_to_bit([0, 0, 0, 1]), 1)

    def test_roundtrip(self):
        """Convert to list and back should preserve value."""
        for val in range(16):
            bits = bit_to_list(val, 4)
            self.assertEqual(list_to_bit(bits), val)


class TestBitwiseOperations(unittest.TestCase):
    """Test multi-bit gate operations."""

    def test_bitwise_and(self):
        self.assertEqual(bitwise_and(5, 3, 4), 1)   # 0101 & 0011 = 0001
        self.assertEqual(bitwise_and(15, 10, 4), 10)  # 1111 & 1010 = 1010
        self.assertEqual(bitwise_and(0, 0, 4), 0)
        self.assertEqual(bitwise_and(15, 15, 4), 15)

    def test_bitwise_or(self):
        self.assertEqual(bitwise_or(5, 3, 4), 7)    # 0101 | 0011 = 0111
        self.assertEqual(bitwise_or(10, 5, 4), 15)   # 1010 | 0101 = 1111
        self.assertEqual(bitwise_or(0, 0, 4), 0)
        self.assertEqual(bitwise_or(15, 0, 4), 15)

    def test_bitwise_xor(self):
        self.assertEqual(bitwise_xor(5, 3, 4), 6)    # 0101 ^ 0011 = 0110
        self.assertEqual(bitwise_xor(10, 5, 4), 15)   # 1010 ^ 0101 = 1111
        self.assertEqual(bitwise_xor(0, 0, 4), 0)
        self.assertEqual(bitwise_xor(15, 15, 4), 0)

    def test_bitwise_not(self):
        self.assertEqual(bitwise_not(0, 4), 15)      # ~0000 = 1111
        self.assertEqual(bitwise_not(15, 4), 0)       # ~1111 = 0000
        self.assertEqual(bitwise_not(5, 4), 10)       # ~0101 = 1010
        self.assertEqual(bitwise_not(1, 4), 14)       # ~0001 = 1110


class TestShiftOperations(unittest.TestCase):
    """Test shift operations."""

    def test_shift_left(self):
        self.assertEqual(shift_left(1, 4, 1), 2)     # 0001 << 1 = 0010
        self.assertEqual(shift_left(1, 4, 2), 4)     # 0001 << 2 = 0100
        self.assertEqual(shift_left(8, 4, 1), 0)     # 1000 << 1 = 0000 (overflow)

    def test_shift_right(self):
        self.assertEqual(shift_right(4, 4, 1), 2)    # 0100 >> 1 = 0010
        self.assertEqual(shift_right(8, 4, 2), 2)    # 1000 >> 2 = 0010
        self.assertEqual(shift_right(1, 4, 1), 0)    # 0001 >> 1 = 0000


if __name__ == "__main__":
    unittest.main()
