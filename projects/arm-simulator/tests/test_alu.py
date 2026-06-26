"""
Tests for ARM ALU
==================

Tests for the ALU class in alu.py.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.alu import ALU


class TestALUAddition:
    """Test cases for ALU addition operations"""

    def setup_method(self):
        self.alu = ALU()

    def test_add_basic(self):
        """Test basic addition"""
        result, n, z, c, v = self.alu.add(10, 20)
        assert result == 30
        assert z == False

    def test_add_zero(self):
        """Test addition with zero"""
        result, n, z, c, v = self.alu.add(0, 0)
        assert result == 0
        assert z == True

    def test_add_overflow(self):
        """Test addition overflow (unsigned)"""
        result, n, z, c, v = self.alu.add(0xFFFFFFFF, 1)
        assert result == 0
        assert c == True  # Carry should be set

    def test_add_with_carry(self):
        """Test addition with carry input"""
        result, n, z, c, v = self.alu.add(0xFFFFFFFF, 1, carry=1)
        assert result == 1
        assert c == True

    def test_add_negative_result(self):
        """Test addition resulting in negative (signed)"""
        result, n, z, c, v = self.alu.add(0x80000000, 0x80000000)
        assert n == True  # Negative result


class TestALUSubtraction:
    """Test cases for ALU subtraction operations"""

    def setup_method(self):
        self.alu = ALU()

    def test_subtract_basic(self):
        """Test basic subtraction"""
        result, n, z, c, v = self.alu.subtract(20, 10)
        assert result == 10
        assert z == False

    def test_subtract_zero(self):
        """Test subtraction resulting in zero"""
        result, n, z, c, v = self.alu.subtract(10, 10)
        assert result == 0
        assert z == True

    def test_subtract_borrow(self):
        """Test subtraction with borrow"""
        result, n, z, c, v = self.alu.subtract(5, 10)
        assert c == False  # No carry = borrow occurred

    def test_subtract_no_borrow(self):
        """Test subtraction without borrow"""
        result, n, z, c, v = self.alu.subtract(10, 5)
        assert c == True  # No borrow


class TestALULogical:
    """Test cases for ALU logical operations"""

    def setup_method(self):
        self.alu = ALU()

    def test_and(self):
        """Test AND operation"""
        result, n, z, c, v = self.alu.logical_and(0xFF, 0xF0)
        assert result == 0xF0
        assert z == False

    def test_and_zero_result(self):
        """Test AND resulting in zero"""
        result, n, z, c, v = self.alu.logical_and(0xFF, 0x00)
        assert result == 0
        assert z == True

    def test_orr(self):
        """Test ORR operation"""
        result, n, z, c, v = self.alu.logical_orr(0xF0, 0x0F)
        assert result == 0xFF
        assert z == False

    def test_eor(self):
        """Test EOR (XOR) operation"""
        result, n, z, c, v = self.alu.logical_eor(0xF0, 0x0F)
        assert result == 0xFF
        assert z == False

    def test_eor_same_values(self):
        """Test EOR with same values (result = 0)"""
        result, n, z, c, v = self.alu.logical_eor(0xFF, 0xFF)
        assert result == 0
        assert z == True

    def test_bic(self):
        """Test BIC (bit clear) operation"""
        result, n, z, c, v = self.alu.logical_bic(0xFF, 0xF0)
        assert result == 0x0F  # Clear bits that are set in second operand

    def test_bic_all_clear(self):
        """Test BIC clearing all bits"""
        result, n, z, c, v = self.alu.logical_bic(0xFF, 0xFF)
        assert result == 0
        assert z == True


class TestALUMove:
    """Test cases for ALU move operations"""

    def setup_method(self):
        self.alu = ALU()

    def test_move(self):
        """Test MOV operation"""
        result, n, z, c, v = self.alu.move(0x12345678)
        assert result == 0x12345678
        assert n == True  # MSB is 1
        assert z == False

    def test_move_zero(self):
        """Test MOV of zero"""
        result, n, z, c, v = self.alu.move(0)
        assert result == 0
        assert z == True

    def test_move_not(self):
        """Test MVN operation"""
        result, n, z, c, v = self.alu.move_not(0x000000FF)
        assert result == 0xFFFFFF00

    def test_move_does_not_update_c_v(self):
        """Test that MOV does not update C and V flags"""
        result, n, z, c, v = self.alu.move(0x12345678)
        assert c == 0  # C should be 0 (not updated)
        assert v == 0  # V should be 0 (not updated)


class TestALUCompare:
    """Test cases for ALU compare operations"""

    def setup_method(self):
        self.alu = ALU()

    def test_compare_equal(self):
        """Test CMP with equal values"""
        result, n, z, c, v = self.alu.compare(10, 10)
        assert z == True  # Zero flag set

    def test_compare_greater(self):
        """Test CMP with first > second"""
        result, n, z, c, v = self.alu.compare(20, 10)
        assert n == False  # Positive result

    def test_compare_less(self):
        """Test CMP with first < second"""
        result, n, z, c, v = self.alu.compare(10, 20)
        assert n == True  # Negative result


class TestALUTest:
    """Test cases for ALU test operations"""

    def setup_method(self):
        self.alu = ALU()

    def test_test(self):
        """Test TST operation"""
        n, z = self.alu.test(0xFF, 0xF0)
        assert n == True  # MSB set
        assert z == False

    def test_test_zero(self):
        """Test TST with zero result"""
        n, z = self.alu.test(0xFF, 0x00)
        assert z == True

    def test_test_equal(self):
        """Test TEQ operation"""
        n, z = self.alu.test_equal(10, 10)
        assert z == True  # Equal values

    def test_test_not_equal(self):
        """Test TEQ with non-equal values"""
        n, z = self.alu.test_equal(10, 20)
        assert z == False


class TestALUShift:
    """Test cases for ALU shift operations"""

    def setup_method(self):
        self.alu = ALU()

    def test_lsl(self):
        """Test logical shift left"""
        result, c_out = self.alu.shift_left(1, 4)
        assert result == 16  # 1 << 4 = 16
        assert c_out == 0

    def test_lsl_carry(self):
        """Test LSR carry out"""
        result, c_out = self.alu.shift_left(0x80000000, 1)
        assert c_out == 1  # MSB shifted out

    def test_lsr(self):
        """Test logical shift right"""
        result, c_out = self.alu.shift_right_logical(256, 4)
        assert result == 16  # 256 >> 4 = 16

    def test_asr(self):
        """Test arithmetic shift right"""
        result, c_out = self.alu.shift_right_arithmetic(256, 4)
        assert result == 16

    def test_asr_negative(self):
        """Test arithmetic shift right with negative number"""
        result, c_out = self.alu.shift_right_arithmetic(0x80000000, 1)
        assert result == 0xC0000000  # Sign bit preserved


class TestALUMultiply:
    """Test cases for ALU multiply operations"""

    def setup_method(self):
        self.alu = ALU()

    def test_multiply(self):
        """Test MUL operation"""
        result = self.alu.multiply(6, 7)
        assert result == 42

    def test_multiply_by_zero(self):
        """Test multiplication by zero"""
        result = self.alu.multiply(100, 0)
        assert result == 0

    def test_multiply_accumulate(self):
        """Test MLA operation"""
        result = self.alu.multiply_accumulate(6, 7, 10)
        assert result == 52  # 6*7 + 10 = 52

    def test_unsigned_multiply_long(self):
        """Test UMULL operation"""
        low, high = self.alu.unsigned_multiply_long(0x00000001, 0x00000002)
        assert low == 2
        assert high == 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
