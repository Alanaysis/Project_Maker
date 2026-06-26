"""
Tests for ARM Register File
=============================

Tests for the CPSR and RegisterFile classes in registers.py.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.registers import RegisterFile, CPSR


class TestCPSR:
    """Test cases for CPSR (Current Program Status Register)"""

    def test_initial_state(self):
        """Test that CPSR starts in a valid initial state"""
        cpsr = CPSR()
        assert cpsr.mode == 0x10  # USER mode
        assert cpsr.n == False
        assert cpsr.z == False
        assert cpsr.c == False
        assert cpsr.v == False

    def test_n_flag(self):
        """Test negative flag setting"""
        cpsr = CPSR()
        cpsr.set_flags_from_result(0x80000000)  # Negative number
        assert cpsr.n == True

        cpsr.set_flags_from_result(0x7FFFFFFF)  # Positive number
        assert cpsr.n == False

    def test_z_flag(self):
        """Test zero flag setting"""
        cpsr = CPSR()
        cpsr.set_flags_from_result(0)
        assert cpsr.z == True

        cpsr.set_flags_from_result(1)
        assert cpsr.z == False

    def test_c_flag_addition(self):
        """Test carry flag for addition"""
        cpsr = CPSR()
        # Addition that overflows 32 bits
        cpsr.set_flags_from_result(0xFFFFFFFF + 1)  # Results in 0x100000000
        assert cpsr.c == True

        cpsr.set_flags_from_result(1 + 1)
        assert cpsr.c == False

    def test_c_flag_subtraction(self):
        """Test carry flag for subtraction (borrow)"""
        cpsr = CPSR()
        # Subtraction: 5 - 10 = borrow
        cpsr.set_flags_from_result(5 - 10, is_subtraction=True)
        assert cpsr.c == False  # No carry = borrow detected

        cpsr.set_flags_from_result(10 - 5, is_subtraction=True)
        assert cpsr.c == True  # No borrow

    def test_condition_check_eq(self):
        """Test EQ condition (Z flag)"""
        cpsr = CPSR()
        cpsr.set_flags_from_result(0)  # Set Z flag
        assert cpsr.check_condition("EQ") == True
        assert cpsr.check_condition("NE") == False

    def test_condition_check_ne(self):
        """Test NE condition (not Z flag)"""
        cpsr = CPSR()
        cpsr.set_flags_from_result(1)  # Clear Z flag
        assert cpsr.check_condition("NE") == True
        assert cpsr.check_condition("EQ") == False

    def test_condition_check_gt(self):
        """Test GT condition (signed greater than)"""
        cpsr = CPSR()
        cpsr.set_flags_from_result(5 - 3)  # Positive result
        assert cpsr.check_condition("GT") == True

        cpsr.set_flags_from_result(3 - 5)  # Negative result
        assert cpsr.check_condition("GT") == False

    def test_condition_check_lt(self):
        """Test LT condition (signed less than)"""
        cpsr = CPSR()
        cpsr.set_flags_from_result(3 - 5)  # Negative result
        assert cpsr.check_condition("LT") == True

        cpsr.set_flags_from_result(5 - 3)  # Positive result
        assert cpsr.check_condition("LT") == False

    def test_condition_check_always(self):
        """Test AL (always) condition"""
        cpsr = CPSR()
        assert cpsr.check_condition("AL") == True

    def test_cpsr_repr(self):
        """Test CPSR string representation"""
        cpsr = CPSR()
        repr_str = repr(cpsr)
        assert "CPSR" in repr_str

    def test_save_restore_spsr(self):
        """Test saving and restoring SPSR"""
        cpsr = CPSR()
        cpsr.set_flags_from_result(0xFFFFFFFF)

        saved = cpsr.save_to_spsr()
        assert saved == 0xFFFFFFFF

        cpsr.value = 0
        cpsr.restore_from_spsr(saved)
        assert (cpsr.value & 0xFFFFFFFF) == saved


class TestRegisterFile:
    """Test cases for RegisterFile"""

    def test_initial_state(self):
        """Test that register file starts in a valid initial state"""
        rf = RegisterFile()
        assert rf.regs == [0] * 16
        assert rf.cpsr is not None

    def test_write_read_registers(self):
        """Test writing and reading registers"""
        rf = RegisterFile()
        rf.write_reg(0, 42)
        assert rf.read_reg(0) == 42

        rf.write_reg(15, 0x1000)
        assert rf.read_reg(15) == 0x1000

    def test_register_overflow_protection(self):
        """Test that register values are masked to 32 bits"""
        rf = RegisterFile()
        rf.write_reg(0, 0x1FFFFFFFF)  # More than 32 bits
        assert rf.read_reg(0) == 0xFFFFFFFF

        rf.write_reg(0, -1)  # Negative value
        assert rf.read_reg(0) == 0xFFFFFFFF

    def test_register_out_of_range(self):
        """Test that out-of-range register access raises error"""
        rf = RegisterFile()
        try:
            rf.write_reg(16, 42)
            assert False, "Should have raised IndexError"
        except IndexError:
            pass

        try:
            rf.read_reg(-1)
            assert False, "Should have raised IndexError"
        except IndexError:
            pass

    def test_sp_accessor(self):
        """Test SP (R13) accessor methods"""
        rf = RegisterFile()
        rf.set_sp(0x2000)
        assert rf.get_sp() == 0x2000

    def test_lr_accessor(self):
        """Test LR (R14) accessor methods"""
        rf = RegisterFile()
        rf.set_lr(0x1234)
        assert rf.get_lr() == 0x1234

    def test_pc_accessor(self):
        """Test PC (R15) accessor methods"""
        rf = RegisterFile()
        rf.set_pc(0x5000)
        assert rf.get_pc() == 0x5000

    def test_pc_thumb_bit(self):
        """Test PC thumb bit handling"""
        rf = RegisterFile()
        rf.set_pc_thumb(0x5000)
        assert rf.get_pc() == 0x5001  # Thumb bit set

    def test_dump(self):
        """Test register dump output"""
        rf = RegisterFile()
        rf.write_reg(0, 42)
        dump = rf.dump()
        assert "R0" in dump
        assert "42" in dump or "0x0000002A" in dump

    def test_spsr_save_restore(self):
        """Test SPSR save and restore"""
        rf = RegisterFile()
        rf.cpsr.set_flags_from_result(0x12345678)
        rf.save_spsr("SVC")
        rf.cpsr.value = 0
        rf.restore_spsr("SVC")
        assert (rf.cpsr.value & 0xFFFFFFFF) == 0x12345678


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
